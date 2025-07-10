from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
import mimetypes
from datetime import datetime, timezone

from src.core.database import get_db
from src.models.database import Document, DocumentStatus
from src.services.s3_service import S3Service


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

    def __init__(self, db: Session = next(get_db())):
        self.db = db
        self.storage_service = S3Service()

    async def upload_document(self, file: UploadFile) -> str:
        if file.content_type not in self.SUPPORTED_MIMETYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}",
            )

        doc_id = str(uuid4())
        extension = self.SUPPORTED_MIMETYPES[file.content_type]
        file_key = f"documents/{doc_id}{extension}"

        document = Document(
            doc_id=doc_id,
            title=file.filename,
            content_type=file.content_type,
            status=DocumentStatus.PENDING,
            doc_metadata={"original_filename": file.filename},
        )
        self.db.add(document)

        try:
            await self.storage_service.upload_file(file_key, file)
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

        if document.status == DocumentStatus.INDEXED and not force_reindex:
            return {
                "doc_id": doc_id,
                "status": document.status.value,
                "message": "Document already indexed",
            }

        try:
            document.status = DocumentStatus.PROCESSING
            self.db.commit()

            document.status = DocumentStatus.INDEXED
            document.indexed_at = datetime.now(timezone.utc)
            self.db.commit()

            return {
                "doc_id": doc_id,
                "status": document.status.value,
                "message": "Document indexed successfully",
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
