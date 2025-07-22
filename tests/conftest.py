import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from neo4j import GraphDatabase
from src.core.config import settings
from src.core.database import Base
from src.models.database import User, Document, DocumentChunk, ChatSession, Message


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_s3_client():
    return MagicMock()


@pytest.fixture
def mock_neo4j_driver():
    driver = MagicMock(spec=GraphDatabase.driver)
    session = MagicMock()
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    return driver


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="Test response")
    return llm


@pytest.fixture
def mock_embeddings():
    embeddings = MagicMock()
    embeddings.embed_documents.return_value = [[0.1] * 768]
    embeddings.embed_query.return_value = [0.1] * 768
    return embeddings


@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser", email="test@example.com", hashed_password="hashedpassword"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_document(db_session, test_user):
    doc = Document(
        doc_id="test_doc_id",
        title="Test Document",
        content_type="application/pdf",
        status="PENDING",
        user_id=test_user.id,
    )
    db_session.add(doc)
    db_session.commit()
    return doc


@pytest.fixture
def test_chat_session(db_session, test_user):
    session = ChatSession(
        id="test_session_id", user_id=test_user.id, title="Test Session"
    )
    db_session.add(session)
    db_session.commit()
    return session
