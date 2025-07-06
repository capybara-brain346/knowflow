from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.request import CreateSessionRequest, SendMessageRequest
from src.models.response import ChatSessionResponse, ChatSessionListResponse
from src.services.session_service import SessionService
from src.routes.auth_routes import get_current_user
from src.models.database import User

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=ChatSessionResponse)
def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SessionService(db)
    session = service.create_session(current_user.id, request.title)
    return session


@router.get("", response_model=List[ChatSessionListResponse])
def list_sessions(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = SessionService(db)
    sessions = service.get_user_sessions(current_user.id)
    return sessions


@router.get("/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/messages", response_model=ChatSessionResponse)
def send_message(
    session_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add user message
    service.add_message(
        session_id=session_id,
        sender="user",
        content=request.content,
        context_used=request.context_used,
    )

    # Here you would typically process the message and generate an AI response
    # For now, we'll just return the updated session
    return service.get_session(session_id, current_user.id)
