import uuid
import tempfile
import os
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    CSVLoader,
    TextLoader,
)

from src.core.config import settings
from src.core.exceptions import (
    ExternalServiceException,
    NotFoundException,
    ValidationException,
)
from src.core.logging import logger
from src.services.graph_service import GraphService
from src.services.storage_service import StorageService
from typing import Dict, Any, List, Optional


class AdminService:
    SUPPORTED_MIMETYPES = {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "text/csv": ".csv",
        "text/plain": ".txt",
    }

    def __init__(self):
        try:
            self.storage_service = StorageService()
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )

            logger.info("Initializing vector store...")
            self.vector_store = PGVector(
                connection=settings.DATABASE_URL,
                embeddings=self.embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
                pre_delete_collection=False,
                distance_strategy="cosine",
            )

            self.vector_store.create_vector_extension()
            self.vector_store.create_tables_if_not_exists()
            logger.info("Vector store initialized successfully")

            self.graph_service = GraphService()

            logger.info("AdminService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AdminService: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to initialize admin service",
                service_name="AdminService",
                extra={"error": str(e)},
            )

    def _get_document_loader(self, file_path: str, mime_type: str):
        try:
            loader_map = {
                "application/pdf": lambda path: PyPDFLoader(path),
                "application/msword": lambda path: UnstructuredWordDocumentLoader(path),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": lambda path: UnstructuredWordDocumentLoader(
                    path
                ),
                "application/vnd.ms-excel": lambda path: UnstructuredExcelLoader(path),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": lambda path: UnstructuredExcelLoader(
                    path
                ),
                "text/csv": lambda path: CSVLoader(path),
                "text/plain": lambda path: TextLoader(path),
            }

            if mime_type not in loader_map:
                raise ValidationException(f"Unsupported file type: {mime_type}")

            return loader_map[mime_type](file_path)
        except Exception as e:
            logger.error(f"Error creating document loader: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to create document loader",
                service_name="DocumentLoader",
                extra={"error": str(e), "mime_type": mime_type},
            )

    async def upload_document(self, file: UploadFile) -> str:
        if file.content_type not in self.SUPPORTED_MIMETYPES:
            raise ValidationException(
                f"Unsupported file type: {file.content_type}. Supported types: {', '.join(self.SUPPORTED_MIMETYPES.keys())}"
            )

        doc_id = str(uuid.uuid4())
        try:
            file_key = f"documents/{doc_id}/{file.filename}"

            logger.debug(f"Uploading file {file.filename} to S3 with doc_id: {doc_id}")
            self.storage_service.upload_file_obj(
                file_key=file_key, file_obj=file.file, content_type=file.content_type
            )
            logger.info(f"Successfully uploaded file to S3: {file.filename}")

            return doc_id
        except Exception as e:
            logger.error(
                f"Unexpected error during document upload: {str(e)}", exc_info=True
            )
            raise ExternalServiceException(
                message="Failed to process document upload",
                service_name="S3",
                extra={"error": str(e), "doc_id": doc_id},
            )

    async def index_document(self, doc_id: str) -> None:
        try:
            logger.debug(f"Retrieving document from S3: {doc_id}")
            files = self.storage_service.list_files(prefix=f"documents/{doc_id}/")

            if not files:
                logger.error(f"Document not found in S3: {doc_id}")
                raise NotFoundException(f"Document not found: {doc_id}")

            for file_info in files:
                logger.debug(f"Processing file for indexing: {file_info['key']}")

                file_metadata = self.storage_service.get_file_metadata(file_info["key"])
                content_type = file_metadata.get("ContentType", "text/plain")

                with tempfile.NamedTemporaryFile(
                    suffix=self.SUPPORTED_MIMETYPES.get(content_type, ".txt"),
                    delete=False,
                ) as temp_file:
                    file_obj = self.storage_service.download_file(file_info["key"])
                    temp_file.write(file_obj.read())
                    temp_file_path = temp_file.name

                try:
                    loader = self._get_document_loader(temp_file_path, content_type)
                    documents = loader.load()

                    logger.debug(f"Splitting document into chunks: {doc_id}")
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=settings.CHUNK_SIZE,
                        chunk_overlap=settings.CHUNK_OVERLAP,
                    )
                    chunks = text_splitter.split_documents(documents)
                    logger.info(f"Created {len(chunks)} chunks for document: {doc_id}")

                    for i, chunk in enumerate(chunks):
                        chunk.metadata.update(
                            {
                                "doc_id": doc_id,
                                "chunk_id": i,
                                "source": file_info["key"],
                                "content_type": content_type,
                            }
                        )

                    logger.debug(f"Adding document chunks to vector store: {doc_id}")
                    try:
                        self.vector_store.add_documents(chunks)
                        logger.info(
                            f"Successfully indexed document in vector store: {doc_id}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to add documents directly, trying alternative method: {str(e)}"
                        )
                        texts = [chunk.page_content for chunk in chunks]
                        metadatas = [chunk.metadata for chunk in chunks]
                        self.vector_store.add_texts(texts=texts, metadatas=metadatas)
                        logger.info(
                            f"Successfully indexed document using alternative method: {doc_id}"
                        )

                    logger.debug(f"Extracting graph knowledge: {doc_id}")
                    full_text = "\n\n".join([chunk.page_content for chunk in chunks])
                    self.graph_service.store_graph_knowledge(doc_id, full_text)
                    logger.info(f"Successfully stored graph knowledge: {doc_id}")

                finally:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during document indexing: {str(e)}", exc_info=True
            )
            raise ExternalServiceException(
                message="Failed to index document",
                service_name="Vector Store",
                extra={"error": str(e), "doc_id": doc_id},
            )

    async def list_documents(
        self, status: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            all_files = self.storage_service.list_files(prefix="documents/")

            documents = {}
            for file in all_files:
                parts = file["key"].split("/")
                if len(parts) >= 3:
                    doc_id = parts[1]
                    if doc_id not in documents:
                        file_metadata = self.storage_service.get_file_metadata(
                            file["key"]
                        )
                        documents[doc_id] = {
                            "doc_id": doc_id,
                            "filename": parts[2],
                            "size": file["size"],
                            "last_modified": file["last_modified"],
                            "content_type": file_metadata.get(
                                "ContentType", "application/octet-stream"
                            ),
                            "status": "processed",
                        }

            document_list = list(documents.values())

            if status:
                document_list = [
                    doc for doc in document_list if doc["status"] == status
                ]

            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            return document_list[start_idx:end_idx]

        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to list documents",
                service_name="AdminService",
                extra={"error": str(e)},
            )

    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        try:
            files = self.storage_service.list_files(prefix=f"documents/{doc_id}/")

            if not files:
                raise NotFoundException(f"Document not found: {doc_id}")

            file_info = files[0]
            file_metadata = self.storage_service.get_file_metadata(file_info["key"])
            filename = file_info["key"].split("/")[-1]

            return {
                "doc_id": doc_id,
                "filename": filename,
                "size": file_info["size"],
                "last_modified": file_info["last_modified"],
                "content_type": file_metadata.get(
                    "ContentType", "application/octet-stream"
                ),
                "status": "processed",
            }

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to get document",
                service_name="AdminService",
                extra={"error": str(e), "doc_id": doc_id},
            )
