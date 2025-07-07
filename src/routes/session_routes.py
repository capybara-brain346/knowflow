from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.request import CreateSessionRequest, SendMessageRequest
from src.models.response import (
    ChatSessionResponse,
    ChatSessionListResponse,
    MessageResponse,
)
from src.services.session_service import SessionService
from src.core.auth import get_current_user
from src.models.database import User

router = APIRouter()


@router.post(
    "", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.create_session(current_user.id, request.title)
    return ChatSessionResponse.model_validate(session)


@router.get("", response_model=List[ChatSessionListResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    sessions = service.get_user_sessions(current_user.id)
    return [ChatSessionListResponse.model_validate(session) for session in sessions]


@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return ChatSessionResponse.model_validate(session)


@router.post("/{session_id}/messages", response_model=ChatSessionResponse)
async def send_message(
    session_id: int,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    await service.add_message(
        session_id=session_id,
        sender="user",
        content=request.content,
        context_used=request.context_used,
    )

    updated_session = await service.get_session(session_id, current_user.id)
    return ChatSessionResponse.model_validate(updated_session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    await service.delete_session(session_id, current_user.id)
