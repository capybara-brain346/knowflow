from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
import PyPDF2
from io import BytesIO

from src.core.database import get_db
from src.models.database import Document, DocumentStatus, DocumentChunk, User
from src.services.s3_service import S3Service
from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument
from src.services.graph_service import GraphService


class DocumentService:
    SUPPORTED_MIMETYPES = {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "text/csv": ".csv",
        "text/plain": ".txt",
    }

    def __init__(
        self, db: Session = next(get_db()), current_user: Optional[User] = None
    ):
        self.db = db
        self.storage_service = S3Service()
        self.current_user = current_user
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )

            self.vector_store = PGVector(
                connection=settings.DATABASE_URL,
                embeddings=self.embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
            )

            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )

            self.graph_service = GraphService()

            logger.info("DocumentService initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize DocumentService: {str(e)}", exc_info=True
            )
            raise ExternalServiceException(
                message="Failed to initialize document service",
                service_name="DocumentService",
                extra={"error": str(e)},
            )

    async def upload_document(self, file: UploadFile) -> str:
        if file.content_type not in self.SUPPORTED_MIMETYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}",
            )

        doc_id = str(uuid4())
        extension = self.SUPPORTED_MIMETYPES[file.content_type]
        file_path = f"documents/{doc_id}{extension}"

        document = Document(
            doc_id=doc_id,
            title=file.filename,
            content_type=file.content_type,
            status=DocumentStatus.PENDING,
            doc_metadata={"original_filename": file.filename},
            user_id=self.current_user.id,
        )
        self.db.add(document)

        try:
            file_data = await file.read()
            self.storage_service.upload_file(
                user_id=self.current_user.id,
                file_path=file_path,
                file_data=file_data,
                content_type=file.content_type,
            )

            document.status = DocumentStatus.PROCESSING
            self.db.commit()
            return doc_id
        except Exception as e:
            self.db.rollback()
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload document",
            )

    async def index_document(
        self, doc_id: str, force_reindex: bool = False
    ) -> Dict[str, Any]:
        document = self.db.query(Document).filter(Document.doc_id == doc_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )

        if document.user_id != self.current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document",
            )

        if document.status == DocumentStatus.INDEXED and not force_reindex:
            return {
                "doc_id": doc_id,
                "status": document.status.value,
                "message": "Document already indexed",
            }

        try:
            document.status = DocumentStatus.PROCESSING
            self.db.commit()

            file_path = (
                f"documents/{doc_id}{self.SUPPORTED_MIMETYPES[document.content_type]}"
            )
            file_data = self.storage_service.get_file(
                user_id=document.user_id, file_path=file_path
            )

            if document.content_type == "text/plain":
                content = file_data.decode("utf-8")
            elif document.content_type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_data))
                content = "\n".join(page.extract_text() for page in pdf_reader.pages)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Indexing not supported for file type: {document.content_type}",
                )

            try:
                self.graph_service.store_graph_knowledge(doc_id, content)
                logger.info(
                    f"Successfully stored graph knowledge for document {doc_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to store graph knowledge: {str(e)}", exc_info=True
                )

            chunks = self.text_splitter.split_text(content)
            for i, chunk_content in enumerate(chunks):
                embedding = self.embeddings.embed_documents([chunk_content])[0]

                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_content,
                    chunk_metadata={"index": i},
                    embedding_vector=embedding,
                )
                self.db.add(chunk)

                self.vector_store.add_texts(
                    texts=[chunk_content],
                    metadatas=[
                        {
                            "document_id": document.id,
                            "doc_id": document.doc_id,
                            "chunk_index": i,
                            "user_id": document.user_id,
                        }
                    ],
                )

            document.status = DocumentStatus.INDEXED
            document.indexed_at = datetime.now(timezone.utc)
            self.db.commit()

            return {
                "doc_id": doc_id,
                "status": document.status.value,
                "message": "Document indexed successfully",
                "chunks_count": len(chunks),
            }
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to index document: {str(e)}",
            )

    async def list_documents(
        self, status: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> List[Document]:
        query = self.db.query(Document)

        if status:
            try:
                doc_status = DocumentStatus(status)
                query = query.filter(Document.status == doc_status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}",
                )

        offset = (page - 1) * page_size
        documents = query.offset(offset).limit(page_size).all()
        return documents

    async def get_document(self, doc_id: str) -> Document:
        document = self.db.query(Document).filter(Document.doc_id == doc_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )
        return document
