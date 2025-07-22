import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from fastapi import HTTPException
from src.services.chat.chat_service import ChatService
from src.models.database import ChatSession, Message, Document, DocumentStatus
from src.models.request import FollowUpChatRequest
from src.core.exceptions import ExternalServiceException


@pytest.fixture
def chat_service(db_session, mock_llm, mock_embeddings, mock_neo4j_driver):
    with (
        patch(
            "src.services.chat.chat_service.ChatGoogleGenerativeAI",
            return_value=mock_llm,
        ),
        patch(
            "src.services.chat.chat_service.GoogleGenerativeAIEmbeddings",
            return_value=mock_embeddings,
        ),
        patch(
            "src.services.chat.chat_service.GraphDatabase.driver",
            return_value=mock_neo4j_driver,
        ),
        patch("src.services.chat.chat_service.PGVector") as mock_pgvector,
    ):
        mock_pgvector.return_value = MagicMock()
        service = ChatService(db_session)
        return service


@pytest.mark.asyncio
async def test_process_query_simple(chat_service, mock_llm):
    query = "What is the meaning of life?"
    current_user_id = 1

    chat_service.vector_store.similarity_search_with_score_by_vector.return_value = [
        (MagicMock(page_content="Life is 42"), 0.9)
    ]
    chat_service.graph_service.query_graph.return_value = [
        {"type": "Concept", "properties": {"name": "Life", "content": "Meaning"}}
    ]

    mock_llm.invoke.return_value = MagicMock(content="The meaning of life is 42")

    result = await chat_service.process_query(query, "session_1", current_user_id)

    assert "message" in result
    assert result["message"] == "The meaning of life is 42"
    assert "context_used" in result
    assert len(result["context_used"]["vector_results"]) > 0
    assert len(result["context_used"]["graph_results"]) > 0


@pytest.mark.asyncio
async def test_process_query_with_decomposition(chat_service, mock_llm):
    query = "Tell me about the system architecture and performance"
    current_user_id = 1

    # Mock query decomposition
    chat_service._query_decomposition_service = MagicMock()
    chat_service._query_decomposition_service.decompose_query.return_value = [
        "What is the system architecture?",
        "How does the system perform?",
    ]

    # Mock vector and graph results for both sub-queries
    chat_service.vector_store.similarity_search_with_score_by_vector.return_value = [
        (MagicMock(page_content="Architecture details"), 0.9)
    ]
    chat_service.graph_service.query_graph.return_value = [
        {"type": "Document", "properties": {"content": "Performance metrics"}}
    ]

    mock_llm.invoke.return_value = MagicMock(
        content="Combined response about architecture and performance"
    )

    result = await chat_service.process_query(
        query, "session_1", current_user_id, use_query_decomposition=True
    )

    assert result["message"] == "Combined response about architecture and performance"
    assert "context_used" in result
    assert "sub_responses" in result["context_used"]


@pytest.mark.asyncio
async def test_process_query_with_retrieval_evaluation(chat_service, mock_llm):
    query = "How does authentication work?"
    current_user_id = 1

    chat_service.vector_store.similarity_search_with_score_by_vector.return_value = [
        (MagicMock(page_content="Auth process"), 0.8)
    ]

    chat_service._retrieval_evaluation_service = MagicMock()
    chat_service._retrieval_evaluation_service.evaluate_retrieval_quality.return_value = {
        "overall_quality_score": 6,
        "needs_improvement": True,
        "suggested_improvements": {
            "alternative_search_terms": ["user authentication", "login process"]
        },
    }

    result = await chat_service.process_query(
        query, "session_1", current_user_id, use_retrieval_evaluation=True
    )

    assert "message" in result
    assert "context_used" in result


@pytest.mark.asyncio
async def test_follow_up_chat(chat_service, test_user, test_chat_session):
    request = FollowUpChatRequest(
        message="Follow up question",
        referenced_node_ids=["node1", "node2"],
        context_window=2,
    )

    mock_session = chat_service.driver.session.return_value.__enter__.return_value
    mock_session.run.return_value = [
        {"related": {"id": "node1", "content": "Context 1"}},
        {"related": {"id": "node2", "content": "Context 2"}},
    ]

    response = await chat_service.follow_up_chat(
        test_chat_session.id, request, test_user.id
    )

    assert response.response == "Placeholder response"
    assert len(response.context_nodes) == 2
    assert response.referenced_entities == ["node1", "node2"]


def test_rename_chat_session(chat_service, test_user, test_chat_session):
    new_title = "New Session Title"
    result = chat_service.rename_chat_session(
        test_chat_session.id, new_title, test_user.id
    )

    assert result["session_id"] == test_chat_session.id
    assert result["title"] == new_title


def test_rename_chat_session_not_found(chat_service, test_user):
    with pytest.raises(HTTPException) as exc_info:
        chat_service.rename_chat_session("nonexistent", "New Title", test_user.id)
    assert exc_info.value.status_code == 404


def test_rename_chat_session_unauthorized(chat_service, test_chat_session):
    with pytest.raises(HTTPException) as exc_info:
        chat_service.rename_chat_session(test_chat_session.id, "New Title", 999)
    assert exc_info.value.status_code == 403


def test_delete_chat_session(chat_service, test_user, test_chat_session):
    result = chat_service.delete_chat_session(test_chat_session.id, test_user.id)

    assert result["session_id"] == test_chat_session.id
    assert result["status"] == "deleted"

    session = (
        chat_service.db.query(ChatSession)
        .filter(ChatSession.id == test_chat_session.id)
        .first()
    )
    assert session is None


def test_delete_chat_session_not_found(chat_service, test_user):
    with pytest.raises(HTTPException) as exc_info:
        chat_service.delete_chat_session("nonexistent", test_user.id)
    assert exc_info.value.status_code == 404


def test_delete_chat_session_unauthorized(chat_service, test_chat_session):
    with pytest.raises(HTTPException) as exc_info:
        chat_service.delete_chat_session(test_chat_session.id, 999)
    assert exc_info.value.status_code == 403


def test_merge_results(chat_service):
    vector_results = ["Vector result 1", "Vector result 2"]
    graph_results = [
        {
            "type": "Concept",
            "properties": {"name": "Test", "content": "Content"},
            "relationships": [{"type": "RELATED_TO"}],
        }
    ]

    merged = chat_service._merge_results(vector_results, graph_results)
    assert isinstance(merged, str)
    assert "Vector result" in merged
    assert "Type: Concept" in merged
    assert "RELATED_TO" in merged


def test_merge_results_error_handling(chat_service):
    with pytest.raises(ExternalServiceException) as exc_info:
        chat_service._merge_results(None, None)
    assert "Failed to merge results" in str(exc_info.value)
