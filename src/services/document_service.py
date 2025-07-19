import os
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    UnstructuredFileLoader,
    CSVLoader,
    TextLoader,
    Docx2txtLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile

from src.core.database import get_db
from src.models.database import Document, DocumentStatus, DocumentChunk, User
from src.services.s3_service import S3Service
from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from src.services.graph_service import GraphService
from src.utils.utils import clean_whitespaes


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
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

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
                separators=["\n\n", "\n", " ", ""],
                keep_separator=True,
                is_separator_regex=False,
                length_function=len,
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

    async def upload_documents(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        results = []

        for file in files:
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

                results.append(
                    {
                        "doc_id": doc_id,
                        "title": file.filename,
                        "status": "success",
                        "message": "Document uploaded successfully",
                    }
                )

            except Exception as e:
                self.db.rollback()
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                self.db.commit()

                results.append(
                    {
                        "title": file.filename,
                        "status": "failed",
                        "message": f"Failed to upload document: {str(e)}",
                    }
                )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No files were uploaded"
            )

        return results

    async def index_document(
        self, doc_id: str, force_reindex: bool = False
    ) -> Dict[str, Any]:
        document = self._get_and_validate_document(doc_id)

        if document.status == DocumentStatus.INDEXED and not force_reindex:
            return {
                "doc_id": doc_id,
                "status": document.status.value,
                "message": "Document already indexed",
            }

        try:
            document.status = DocumentStatus.PROCESSING
            self.db.commit()

            file_data = self._get_document_file(document)
            temp_file_path = self._create_temp_file(document, file_data)

            try:
                content = self._extract_document_content(temp_file_path, document)
                self._store_graph_knowledge(document.doc_id, content)
                chunks = self.text_splitter.split_text(content)
                embeddings = await self._generate_embeddings(chunks)

                chunk_objects, vector_texts, vector_metadata = (
                    self._prepare_chunks_and_vectors(document, chunks, embeddings)
                )

                self._save_chunks_and_vectors(
                    chunk_objects, vector_texts, vector_metadata
                )
                self._update_document_status(document)

                return {
                    "doc_id": doc_id,
                    "status": document.status.value,
                    "message": "Document indexed successfully",
                    "chunks_count": len(chunks),
                }

            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        except Exception as e:
            self._handle_indexing_error(document, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to index document: {str(e)}",
            )

    async def list_documents(
        self, document_status: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> List[Document]:
        query = self.db.query(Document).filter(Document.user_id == self.current_user.id)

        if document_status:
            try:
                doc_status = DocumentStatus(document_status)
                query = query.filter(Document.status == doc_status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {document_status}",
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

    def _get_and_validate_document(self, doc_id: str) -> Document:
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

        return document

    def _get_document_file(self, document: Document) -> bytes:
        file_path = f"documents/{document.doc_id}{self.SUPPORTED_MIMETYPES[document.content_type]}"
        return self.storage_service.get_file(
            user_id=document.user_id, file_path=file_path
        )

    def _create_temp_file(self, document: Document, file_data: bytes) -> str:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=self.SUPPORTED_MIMETYPES[document.content_type]
        ) as temp_file:
            temp_file.write(file_data)
            return temp_file.name

    def _extract_document_content(self, temp_file_path: str, document: Document) -> str:
        loader = self._get_document_loader(temp_file_path, document.content_type)
        docs = loader.load()
        content = "\n\n".join(doc.page_content for doc in docs)
        return clean_whitespaes(content)

    def _store_graph_knowledge(self, doc_id: str, content: str) -> None:
        try:
            self.graph_service.store_graph_knowledge(doc_id, content)
            logger.info(f"Successfully stored graph knowledge for document {doc_id}")
        except Exception as e:
            logger.error(f"Failed to store graph knowledge: {str(e)}", exc_info=True)

    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embeddings.embed_documents, chunks)

    def _prepare_chunks_and_vectors(
        self, document: Document, chunks: List[str], embeddings: List[List[float]]
    ) -> tuple[List[DocumentChunk], List[str], List[Dict]]:
        chunk_objects = []
        vector_texts = []
        vector_metadata = []

        for i, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk_content,
                chunk_metadata={"index": i},
                embedding_vector=embedding,
            )
            chunk_objects.append(chunk)
            vector_texts.append(chunk_content)
            vector_metadata.append(
                {
                    "document_id": document.id,
                    "doc_id": document.doc_id,
                    "user_id": document.user_id,
                    "chunk_index": i,
                }
            )

        return chunk_objects, vector_texts, vector_metadata

    def _save_chunks_and_vectors(
        self,
        chunk_objects: List[DocumentChunk],
        vector_texts: List[str],
        vector_metadata: List[Dict],
    ) -> None:
        self.db.bulk_save_objects(chunk_objects)
        self.db.commit()
        self.vector_store.add_texts(texts=vector_texts, metadatas=vector_metadata)

    def _update_document_status(self, document: Document) -> None:
        document.status = DocumentStatus.INDEXED
        document.indexed_at = datetime.now(timezone.utc)
        self.db.commit()

    def _handle_indexing_error(self, document: Document, error: Exception) -> None:
        document.status = DocumentStatus.FAILED
        document.error_message = str(error)
        self.db.commit()

    def _get_document_loader(self, file_path: str, content_type: str):
        try:
            if content_type == "application/pdf":
                return PyMuPDFLoader(file_path)
            elif content_type in [
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]:
                return Docx2txtLoader(file_path)
            elif content_type in [
                "text/csv",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ]:
                return CSVLoader(file_path)
            elif content_type == "text/plain":
                return TextLoader(file_path)
            else:
                return UnstructuredFileLoader(file_path)
        except Exception as e:
            logger.error(f"Failed to initialize document loader: {str(e)}")
            raise ExternalServiceException(
                message=f"Failed to load document of type {content_type}",
                service_name="DocumentLoader",
                extra={"error": str(e)},
            )
