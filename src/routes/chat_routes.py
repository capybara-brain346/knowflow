from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.services.chat_service import ChatService
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.models.request import ChatRequest
from src.models.response import ChatResponse
from src.core.auth import get_current_user
from src.models.database import User
from src.models.request import FollowUpChatRequest
from src.models.response import FollowUpChatResponse
from src.core.database import get_db

router = APIRouter()
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        logger.info(f"Processing chat query: {request.query[:50]}...")
        response = await chat_service.process_query(
            query=request.query, session_id=request.session_id
        )
        logger.info("Chat response generated successfully")
        return ChatResponse(
            message=response.get("message", ""),
            context_used=response.get("context_used"),
            session_id=response.get("session_id"),
        )
    except ExternalServiceException as e:
        logger.error(f"External service error during chat: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during chat: {str(e)}", exc_info=True)
        raise ExternalServiceException(
            message="Failed to process chat query",
            service_name="ChatService",
            extra={"error": str(e)},
        )


@router.post("/followup/{session_id}", response_model=FollowUpChatResponse)
async def follow_up_chat(
    session_id: str,
    request: FollowUpChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> FollowUpChatResponse:
    chat_service = ChatService(db)
    return await chat_service.follow_up_chat(session_id, request)
