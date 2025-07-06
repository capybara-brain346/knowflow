import uuid
import tempfile
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
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
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )

            self.vector_store = PGVector(
                connection=settings.DATABASE_URL,
                embeddings=self.embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
            )

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
            file_content = await file.read()

            logger.debug(f"Uploading file {file.filename} to S3 with doc_id: {doc_id}")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"documents/{doc_id}/{file.filename}",
                Body=file_content,
                ContentType=file.content_type,
            )
            logger.info(f"Successfully uploaded file to S3: {file.filename}")

            return doc_id
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 error during document upload: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to upload document to S3",
                service_name="S3",
                extra={"error": str(e), "doc_id": doc_id},
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during document upload: {str(e)}", exc_info=True
            )
            raise ExternalServiceException(
                message="Failed to process document upload",
                service_name="AdminService",
                extra={"error": str(e), "doc_id": doc_id},
            )

    async def index_document(self, doc_id: str) -> None:
        try:
            logger.debug(f"Retrieving document from S3: {doc_id}")
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"documents/{doc_id}/",
            )

            if not response.get("Contents"):
                logger.error(f"Document not found in S3: {doc_id}")
                raise NotFoundException(f"Document not found: {doc_id}")

            for obj in response.get("Contents", []):
                logger.debug(f"Processing file for indexing: {obj['Key']}")

                file_metadata = self.s3_client.head_object(
                    Bucket=self.bucket_name, Key=obj["Key"]
                )
                content_type = file_metadata.get("ContentType", "text/plain")

                with tempfile.NamedTemporaryFile(
                    suffix=self.SUPPORTED_MIMETYPES.get(content_type, ".txt"),
                    delete=False,
                ) as temp_file:
                    self.s3_client.download_fileobj(
                        Bucket=self.bucket_name, Key=obj["Key"], Fileobj=temp_file
                    )
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
                                "source": obj["Key"],
                                "content_type": content_type,
                            }
                        )

                    logger.debug(f"Adding document chunks to vector store: {doc_id}")
                    self.vector_store.add_documents(chunks)
                    logger.info(f"Successfully indexed document: {doc_id}")

                finally:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)

        except NotFoundException:
            raise
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 error during document indexing: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to retrieve document from S3",
                service_name="S3",
                extra={"error": str(e), "doc_id": doc_id},
            )
        except ValidationException:
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
