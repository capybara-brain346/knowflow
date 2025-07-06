from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.auth import get_current_admin
from src.services.admin_service import AdminService
from src.models.database import User

router = APIRouter()


def get_admin_service():
    return AdminService()


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(get_current_admin)],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
):
    """
    Upload and process a document. Only accessible by admin users.
    The document will be processed and indexed in the background.
    """
    doc_id = await admin_service.upload_document(file)
    background_tasks.add_task(admin_service.index_document, doc_id)
    return {"doc_id": doc_id, "status": "processing"}
