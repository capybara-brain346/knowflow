from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.auth import get_current_admin
from src.services.admin_service import AdminService
from src.models.database import User
from src.models.request import DocumentMetadataRequest, DocumentIndexRequest
from src.models.response import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentIndexResponse,
)

router = APIRouter()


def get_admin_service():
    return AdminService()


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    current_admin: Annotated[User, Depends(get_current_admin)],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    background_tasks: BackgroundTasks,
):
    doc_id = await admin_service.upload_document(file)
    background_tasks.add_task(admin_service.index_document, doc_id)
    return DocumentUploadResponse(
        doc_id=doc_id,
        status="processing",
        message="Document uploaded and queued for processing",
    )


@router.post("/documents/{doc_id}/index", response_model=DocumentIndexResponse)
async def index_document(
    request: Optional[DocumentIndexRequest],
    doc_id: str,
    current_admin: Annotated[User, Depends(get_current_admin)],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
):
    result = await admin_service.index_document(
        doc_id, force_reindex=request.force_reindex if request else False
    )
    return DocumentIndexResponse(**result)


@router.get("/documents")
async def list_documents(
    current_admin: Annotated[User, Depends(get_current_admin)],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    status: Optional[str] = Query(None, description="Filter by document status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
):
    documents = await admin_service.list_documents(
        status=status, page=page, page_size=page_size
    )
    return [doc for doc in documents]


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    current_admin: Annotated[User, Depends(get_current_admin)],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
):
    document = await admin_service.get_document(doc_id)
    return document
