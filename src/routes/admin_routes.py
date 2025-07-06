from fastapi import APIRouter, status, UploadFile, File
from typing import Dict

from src.services.admin_service import AdminService
from src.core.exceptions import (
    ValidationException,
    ExternalServiceException,
    NotFoundException,
)
from src.core.logging import logger

router = APIRouter()
admin_service = AdminService()


@router.post("/upload-doc", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> Dict[str, str]:
    try:
        if not file.filename:
            raise ValidationException("No file provided")

        logger.info(f"Uploading document: {file.filename}")
        doc_id = await admin_service.upload_document(file)
        logger.info(f"Document uploaded successfully with ID: {doc_id}")

        return {"message": "Document uploaded successfully", "doc_id": doc_id}
    except ValidationException as e:
        logger.error(f"Validation error during document upload: {str(e)}")
        raise
    except ExternalServiceException as e:
        logger.error(f"External service error during document upload: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during document upload: {str(e)}", exc_info=True
        )
        raise ExternalServiceException(
            message="Failed to upload document",
            service_name="S3",
            extra={"error": str(e)},
        )


@router.post("/index-doc/{doc_id}", status_code=status.HTTP_200_OK)
async def index_document(doc_id: str) -> Dict[str, str]:
    try:
        logger.info(f"Starting document indexing for doc_id: {doc_id}")
        await admin_service.index_document(doc_id)
        logger.info(f"Document indexed successfully: {doc_id}")

        return {"message": "Document indexed successfully", "doc_id": doc_id}
    except NotFoundException as e:
        logger.error(f"Document not found during indexing: {str(e)}")
        raise
    except ExternalServiceException as e:
        logger.error(f"External service error during document indexing: {str(e)}")
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
