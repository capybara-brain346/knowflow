from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.database import ChatSession, Message, User


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: int, title: Optional[str] = None) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            title=title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        return self.db.query(ChatSession).filter(ChatSession.user_id == user_id).all()

    def get_session(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )

    def add_message(
        self,
        session_id: int,
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

    def get_session_messages(self, session_id: int) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.chat_session_id == session_id)
            .order_by(Message.created_at)
            .all()
        )
