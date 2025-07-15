from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.services.chat_service import ChatService
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.models.request import ChatRequest, FollowUpChatRequest, RenameChatRequest
from src.models.response import (
    ChatResponse,
    FollowUpChatResponse,
    RenameChatResponse,
    DeleteChatResponse,
)
from src.core.auth import get_current_user
from src.models.database import User
from src.core.database import get_db
from src.services.session_service import SessionService


router = APIRouter()
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    try:
        logger.info(f"Processing chat query: {request.query[:50]}...")

        chat_service = ChatService(db)
        session_service = SessionService(db)

        response = await chat_service.process_query(
            query=request.query,
            session_id=request.session_id,
            current_user_id=current_user.id,
        )

        if request.session_id:
            await session_service.add_message(
                session_id=request.session_id,
                sender="user",
                content=request.query,
            )

            await session_service.add_message(
                session_id=request.session_id,
                sender="assistant",
                content=response["message"],
                context_used=response.get("context_used"),
            )

        logger.info("Chat response generated and saved successfully")
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
    current_user: User = Depends(get_current_user),
) -> FollowUpChatResponse:
    chat_service = ChatService(db)
    session_service = SessionService(db)

    await session_service.add_message(
        session_id=session_id,
        sender="user",
        content=request.message,
    )

    response = await chat_service.follow_up_chat(
        session_id, request, current_user_id=current_user.id
    )

    await session_service.add_message(
        session_id=session_id,
        sender="assistant",
        content=response.response,
        context_used={"context_nodes": response.context_nodes},
    )

    return response


@router.put("/{session_id}/rename", response_model=RenameChatResponse)
async def rename_chat(
    session_id: str,
    request: RenameChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RenameChatResponse:
    try:
        chat_service = ChatService(db)
        response = await chat_service.rename_chat_session(
            session_id=session_id,
            new_title=request.new_title,
            current_user_id=current_user.id,
        )
        return RenameChatResponse(**response)
    except ExternalServiceException as e:
        logger.error(f"External service error during chat rename: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during chat rename: {str(e)}", exc_info=True)
        raise ExternalServiceException(
            message="Failed to rename chat session",
            service_name="ChatService",
            extra={"error": str(e)},
        )


@router.delete("/{session_id}", response_model=DeleteChatResponse)
async def delete_chat(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeleteChatResponse:
    try:
        chat_service = ChatService(db)
        response = await chat_service.delete_chat_session(
            session_id=session_id,
            current_user_id=current_user.id,
        )
        return DeleteChatResponse(**response)
    except ExternalServiceException as e:
        logger.error(f"External service error during chat deletion: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during chat deletion: {str(e)}", exc_info=True)
        raise ExternalServiceException(
            message="Failed to delete chat session",
            service_name="ChatService",
            extra={"error": str(e)},
        )
