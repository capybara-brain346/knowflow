import pytest
from datetime import datetime, timezone
from src.services.session_service import SessionService
from src.models.database import ChatSession, Message


@pytest.fixture
def session_service(db_session):
    return SessionService(db_session)


@pytest.mark.asyncio
async def test_create_session_with_title(session_service, test_user):
    title = "Test Chat Session"
    session = await session_service.create_session(test_user.id, title)

    assert session.id is not None
    assert session.user_id == test_user.id
    assert session.title == title

    # Verify session was saved to database
    db_session = (
        session_service.db.query(ChatSession)
        .filter(ChatSession.id == session.id)
        .first()
    )
    assert db_session is not None
    assert db_session.title == title


@pytest.mark.asyncio
async def test_create_session_without_title(session_service, test_user):
    session = await session_service.create_session(test_user.id)

    assert session.id is not None
    assert session.user_id == test_user.id
    assert "Chat" in session.title
    assert datetime.now(timezone.utc).strftime("%Y-%m-%d") in session.title


@pytest.mark.asyncio
async def test_get_user_sessions(session_service, test_user, test_chat_session):
    # Create additional session
    await session_service.create_session(test_user.id, "Second Session")

    sessions = await session_service.get_user_sessions(test_user.id)
    assert len(sessions) == 2
    assert all(s.user_id == test_user.id for s in sessions)


@pytest.mark.asyncio
async def test_get_session(session_service, test_user, test_chat_session):
    session = await session_service.get_session(test_chat_session.id, test_user.id)

    assert session is not None
    assert session.id == test_chat_session.id
    assert session.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_session_not_found(session_service, test_user):
    session = await session_service.get_session("nonexistent", test_user.id)
    assert session is None


@pytest.mark.asyncio
async def test_get_session_wrong_user(session_service, test_chat_session):
    wrong_user_id = test_chat_session.user_id + 1
    session = await session_service.get_session(test_chat_session.id, wrong_user_id)
    assert session is None


@pytest.mark.asyncio
async def test_add_message(session_service, test_chat_session):
    message = await session_service.add_message(
        session_id=test_chat_session.id,
        sender="user",
        content="Test message",
        context_used={"test": "context"},
    )

    assert message.chat_session_id == test_chat_session.id
    assert message.sender == "user"
    assert message.content == "Test message"
    assert message.context_used == {"test": "context"}

    # Verify message was saved to database
    db_message = (
        session_service.db.query(Message).filter(Message.id == message.id).first()
    )
    assert db_message is not None
    assert db_message.content == "Test message"


@pytest.mark.asyncio
async def test_add_message_without_context(session_service, test_chat_session):
    message = await session_service.add_message(
        session_id=test_chat_session.id, sender="user", content="Test message"
    )

    assert message.context_used == {}


@pytest.mark.asyncio
async def test_delete_session(session_service, test_user, test_chat_session):
    # Add a message to the session
    await session_service.add_message(test_chat_session.id, "user", "Test message")

    await session_service.delete_session(test_chat_session.id, test_user.id)

    # Verify session and messages were deleted
    session = (
        session_service.db.query(ChatSession)
        .filter(ChatSession.id == test_chat_session.id)
        .first()
    )
    assert session is None

    messages = (
        session_service.db.query(Message)
        .filter(Message.chat_session_id == test_chat_session.id)
        .all()
    )
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_delete_session_not_found(session_service, test_user):
    # Should not raise any exception
    await session_service.delete_session("nonexistent", test_user.id)


@pytest.mark.asyncio
async def test_get_session_messages(session_service, test_chat_session):
    # Add multiple messages
    message1 = await session_service.add_message(
        test_chat_session.id, "user", "Message 1"
    )
    message2 = await session_service.add_message(
        test_chat_session.id, "assistant", "Message 2"
    )

    messages = await session_service.get_session_messages(test_chat_session.id)

    assert len(messages) == 2
    assert messages[0].content == "Message 1"
    assert messages[1].content == "Message 2"
    assert messages[0].created_at <= messages[1].created_at
