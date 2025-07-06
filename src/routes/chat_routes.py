from fastapi import APIRouter, status
from typing import Dict
from pydantic import BaseModel

from src.services.chat_service import ChatService
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger

router = APIRouter()
chat_service = ChatService()


class ChatRequest(BaseModel):
    query: str


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> Dict[str, str]:
    try:
        logger.info(f"Processing chat query: {request.query[:50]}...")
        response = await chat_service.process_query(request.query)
        logger.info("Chat response generated successfully")
        return {"response": response}
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
