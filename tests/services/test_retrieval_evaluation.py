import pytest
from unittest.mock import patch, MagicMock
import json
from src.services.chat.retrieval_evaluation import RetrievalEvaluationService
from langchain.schema import HumanMessage, SystemMessage


@pytest.fixture
def sample_evaluation_response():
    return {
        "chunk_scores": [
            {
                "chunk": "text1",
                "relevance_score": 8,
                "reasoning": "Directly answers the query",
            },
            {"chunk": "text2", "relevance_score": 5, "reasoning": "Partially relevant"},
        ],
        "missing_aspects": ["technical details"],
        "redundant_information": ["repeated context"],
        "suggested_improvements": {
            "additional_info_needed": ["implementation steps"],
            "alternative_search_terms": [
                "technical specification",
                "implementation guide",
            ],
        },
        "overall_quality_score": 7,
        "quality_summary": "Good overall coverage but missing technical details",
    }


def test_evaluate_retrieval_quality_success(mock_llm, sample_evaluation_response):
    with patch(
        "src.services.chat.retrieval_evaluation.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = RetrievalEvaluationService()
        mock_llm.invoke.return_value = MagicMock(
            content=json.dumps(sample_evaluation_response)
        )

        result = service.evaluate_retrieval_quality(
            "How does the system work?", ["Text chunk 1", "Text chunk 2"]
        )

        assert result["overall_quality_score"] == 7
        assert len(result["chunk_scores"]) == 2
        assert "needs_improvement" in result
        assert result["needs_improvement"] == False  # Score >= 7

        # Verify prompt construction
        mock_llm.invoke.assert_called_once()
        args = mock_llm.invoke.call_args[0][0]
        assert len(args) == 2
        assert isinstance(args[0], SystemMessage)
        assert isinstance(args[1], HumanMessage)


def test_evaluate_retrieval_quality_low_score(mock_llm):
    with patch(
        "src.services.chat.retrieval_evaluation.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = RetrievalEvaluationService()
        low_score_response = {
            "chunk_scores": [
                {"chunk": "text", "relevance_score": 3, "reasoning": "Not relevant"}
            ],
            "missing_aspects": ["important context"],
            "overall_quality_score": 3,
        }
        mock_llm.invoke.return_value = MagicMock(content=json.dumps(low_score_response))

        result = service.evaluate_retrieval_quality("Query", ["Text"])
        assert result["needs_improvement"] == True
        assert result["overall_quality_score"] == 3


def test_evaluate_retrieval_quality_error_handling(mock_llm):
    with patch(
        "src.services.chat.retrieval_evaluation.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = RetrievalEvaluationService()
        mock_llm.invoke.side_effect = Exception("API Error")

        result = service.evaluate_retrieval_quality("Query", ["Text"])
        assert result["overall_quality_score"] == 0
        assert result["needs_improvement"] == True


def test_evaluate_retrieval_quality_invalid_json(mock_llm):
    with patch(
        "src.services.chat.retrieval_evaluation.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = RetrievalEvaluationService()
        mock_llm.invoke.return_value = MagicMock(content="Invalid JSON")

        result = service.evaluate_retrieval_quality("Query", ["Text"])
        assert result["overall_quality_score"] == 0
        assert result["needs_improvement"] == True


def test_improve_retrieval_suggestions(mock_llm, sample_evaluation_response):
    with patch(
        "src.services.chat.retrieval_evaluation.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = RetrievalEvaluationService()

        # Test when improvement is needed
        evaluation = {
            **sample_evaluation_response,
            "overall_quality_score": 5,
            "needs_improvement": True,
        }

        alternative_queries = service._improve_retrieval("Original query", evaluation)
        assert len(alternative_queries) > 0
        assert "technical specification" in alternative_queries
        assert "implementation guide" in alternative_queries


def test_improve_retrieval_no_improvement_needed(mock_llm):
    with patch(
        "src.services.chat.retrieval_evaluation.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = RetrievalEvaluationService()

        evaluation = {"overall_quality_score": 9, "needs_improvement": False}

        alternative_queries = service._improve_retrieval("Original query", evaluation)
        assert len(alternative_queries) == 0


def test_improve_retrieval_error_handling(mock_llm):
    with patch(
        "src.services.chat.retrieval_evaluation.ChatGoogleGenerativeAI",
        return_value=mock_llm,
    ):
        service = RetrievalEvaluationService()

        # Test with invalid evaluation data
        evaluation = {"invalid": "data"}
        alternative_queries = service._improve_retrieval("Original query", evaluation)
        assert len(alternative_queries) == 0
