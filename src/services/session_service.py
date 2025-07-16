from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
import uuid

from src.models.database import ChatSession, Message, User


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    async def create_session(
        self, user_id: int, title: Optional[str] = None
    ) -> ChatSession:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
            or f"Chat {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    async def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        return self.db.query(ChatSession).filter(ChatSession.user_id == user_id).all()

    async def get_session(self, session_id: str, user_id: int) -> Optional[ChatSession]:
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .options(joinedload(ChatSession.messages))
            .first()
        )

    async def add_message(
        self,
        session_id: str,
        sender: str,
        content: str,
        context_used: Optional[dict] = None,
    ) -> Message:
        message = Message(
            chat_session_id=session_id,
            sender=sender,
            content=content,
            context_used=context_used or {},
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    async def delete_session(self, session_id: str, user_id: int) -> None:
        session = await self.get_session(session_id, user_id)
        if session:
            self.db.delete(session)
            self.db.commit()

    async def get_session_messages(self, session_id: str) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.chat_session_id == session_id)
            .order_by(Message.created_at)
            .all()
        )
