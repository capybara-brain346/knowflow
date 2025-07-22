import pytest
from unittest.mock import patch, MagicMock
from src.services.chat.query_decomposition import QueryDecompositionService
from langchain.schema import HumanMessage, SystemMessage


def test_decompose_query_simple(mock_llm):
    with patch(
        "src.services.chat.query_decomposition.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = QueryDecompositionService()
        mock_llm.invoke.return_value = MagicMock(
            content="What is the capital of France?"
        )

        result = service.decompose_query("What is the capital of France?")
        assert len(result) == 1
        assert result[0] == "What is the capital of France?"

        # Verify correct prompt construction
        mock_llm.invoke.assert_called_once()
        args = mock_llm.invoke.call_args[0][0]
        assert len(args) == 2
        assert isinstance(args[0], SystemMessage)
        assert isinstance(args[1], HumanMessage)
        assert "query decomposition assistant" in args[0].content.lower()


def test_decompose_query_complex(mock_llm):
    with patch(
        "src.services.chat.query_decomposition.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = QueryDecompositionService()
        mock_llm.invoke.return_value = MagicMock(
            content="1. What are the main features of the product?\n2. How much does it cost?\n3. What are the customer reviews?"
        )

        result = service.decompose_query(
            "Tell me about the product, its pricing and customer feedback"
        )
        assert len(result) == 3
        assert "main features" in result[0]
        assert "cost" in result[1]
        assert "reviews" in result[2]


def test_decompose_query_error_handling(mock_llm):
    with patch(
        "src.services.chat.query_decomposition.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = QueryDecompositionService()
        mock_llm.invoke.side_effect = Exception("API Error")

        query = "What is the meaning of life?"
        result = service.decompose_query(query)

        # Should return original query on error
        assert len(result) == 1
        assert result[0] == query


def test_decompose_query_empty_response(mock_llm):
    with patch(
        "src.services.chat.query_decomposition.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = QueryDecompositionService()
        mock_llm.invoke.return_value = MagicMock(content="\n\n  \n")

        query = "What is the weather?"
        result = service.decompose_query(query)

        # Should return original query for empty response
        assert len(result) == 1
        assert result[0] == query


def test_decompose_query_whitespace_handling(mock_llm):
    with patch(
        "src.services.chat.query_decomposition.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = QueryDecompositionService()
        mock_llm.invoke.return_value = MagicMock(
            content="  1. First question  \n\n2. Second question\n  3. Third question  "
        )

        result = service.decompose_query("Complex multi-part question")
        assert len(result) == 3
        assert all(not q.startswith(" ") and not q.endswith(" ") for q in result)
