import pytest
from unittest.mock import patch, MagicMock
from src.services.base_client import BaseLLMClient
from src.core.exceptions import ExternalServiceException


def test_base_client_initialization_success(mock_llm):
    with patch(
        "src.services.base_client.ChatGoogleGenerativeAI", return_value=mock_llm
    ):
        client = BaseLLMClient("TestService")
        assert client.service_name == "TestService"
        assert client.llm == mock_llm


def test_base_client_initialization_failure():
    with patch(
        "src.services.base_client.ChatGoogleGenerativeAI",
        side_effect=Exception("API Error"),
    ):
        with pytest.raises(ExternalServiceException) as exc_info:
            BaseLLMClient("TestService")
        assert "Failed to initialize testservice" in str(exc_info.value)
        assert exc_info.value.service_name == "TestService"


def test_base_client_llm_invocation(mock_llm):
    with patch(
        "src.services.base_client.ChatGoogleGenerativeAI", return_value=mock_llm
    ):
        client = BaseLLMClient("TestService")
        mock_llm.invoke.return_value = MagicMock(content="Test response")

        messages = [{"role": "user", "content": "Test message"}]
        response = client.llm.invoke(messages)

        assert response.content == "Test response"
        mock_llm.invoke.assert_called_once_with(messages)
