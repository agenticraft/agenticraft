"""Unit tests for Ollama provider.

Tests the Ollama provider implementation with mocked API responses.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from agenticraft.core.exceptions import ProviderError
from agenticraft.providers.ollama import OllamaProvider
from agenticraft.core.types import Message, MessageRole, ToolDefinition, ToolParameter


class TestOllamaProvider:
    """Test suite for Ollama provider."""
    
    @pytest.fixture
    def provider(self):
        """Create Ollama provider instance."""
        return OllamaProvider()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        response = MagicMock(spec=httpx.Response)
        response.raise_for_status = MagicMock()
        return response
    
    def test_initialization_defaults(self):
        """Test provider initialization with defaults."""
        provider = OllamaProvider()
        assert provider.api_key == "ollama"
        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "llama2"
        assert provider.timeout == 300
    
    def test_initialization_with_params(self):
        """Test provider initialization with custom parameters."""
        provider = OllamaProvider(
            base_url="http://192.168.1.100:11434",
            model="codellama",
            timeout=600
        )
        assert provider.base_url == "http://192.168.1.100:11434"
        assert provider.model == "codellama"
        assert provider.timeout == 600
    
    def test_initialization_strips_ollama_prefix(self):
        """Test that ollama/ prefix is stripped from model names."""
        provider = OllamaProvider(model="ollama/mistral")
        assert provider.model == "mistral"
    
    @pytest.mark.asyncio
    async def test_complete_basic(self, provider, mock_response):
        """Test basic completion without tools."""
        # Mock response data
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Hello! I'm running locally via Ollama."
            },
            "prompt_eval_count": 15,
            "eval_count": 25,
            "total_duration": 1000000000,  # 1 second in nanoseconds
        }
        
        # Mock HTTP client
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        response = await provider.complete(messages)
        
        assert response.content == "Hello! I'm running locally via Ollama."
        assert response.finish_reason == "stop"
        assert response.usage["prompt_tokens"] == 15
        assert response.usage["completion_tokens"] == 25
        assert response.usage["total_tokens"] == 40
        assert response.metadata["total_duration"] == 1000000000
        
        # Verify API call
        mock_client.post.assert_called_once_with(
            "/api/chat",
            json={
                "model": "llama2",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False,
                "options": {
                    "temperature": 0.7
                }
            }
        )
    
    @pytest.mark.asyncio
    async def test_complete_with_model_override(self, provider, mock_response):
        """Test completion with model override."""
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Response from CodeLlama"}
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Write code"}]
        
        await provider.complete(messages, model="codellama")
        
        # Verify correct model was used
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == "codellama"
    
    @pytest.mark.asyncio
    async def test_complete_with_ollama_prefix(self, provider, mock_response):
        """Test completion with ollama/ prefix in model name."""
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Response"}
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Test"}]
        
        await provider.complete(messages, model="ollama/phi")
        
        # Verify prefix was stripped
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == "phi"
    
    @pytest.mark.asyncio
    async def test_complete_with_message_objects(self, provider, mock_response):
        """Test completion with Message objects."""
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "I understand"}
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful"),
            Message(role=MessageRole.USER, content="Hello")
        ]
        
        await provider.complete(messages)
        
        # Verify messages were formatted correctly
        call_args = mock_client.post.call_args
        sent_messages = call_args[1]["json"]["messages"]
        assert sent_messages[0]["role"] == "system"
        assert sent_messages[0]["content"] == "You are helpful"
        assert sent_messages[1]["role"] == "user"
        assert sent_messages[1]["content"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_complete_with_parameters(self, provider, mock_response):
        """Test completion with custom parameters."""
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Response"}
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Test"}]
        
        await provider.complete(
            messages,
            temperature=0.2,
            max_tokens=100,
            top_p=0.9,
            seed=42
        )
        
        # Verify parameters were passed correctly
        call_args = mock_client.post.call_args
        options = call_args[1]["json"]["options"]
        assert options["temperature"] == 0.2
        assert options["num_predict"] == 100
        assert options["top_p"] == 0.9
        assert options["seed"] == 42
    
    @pytest.mark.asyncio
    async def test_complete_with_tools(self, provider, mock_response):
        """Test completion with tools (converted to text)."""
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "I'll use the calculator tool"}
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "What's 2+2?"}]
        tools = [{
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Perform calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    }
                }
            }
        }]
        
        await provider.complete(messages, tools=tools)
        
        # Verify tools were added to system message
        call_args = mock_client.post.call_args
        sent_messages = call_args[1]["json"]["messages"]
        assert len(sent_messages) == 2
        assert sent_messages[0]["role"] == "system"
        assert "Available tools:" in sent_messages[0]["content"]
        assert "calculator" in sent_messages[0]["content"]
    
    @pytest.mark.asyncio
    async def test_complete_http_404_error(self, provider):
        """Test handling of 404 error (model not found)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=None, response=mock_response)
        mock_client.post.side_effect = error
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.complete(messages, model="nonexistent")
        
        assert "not found" in str(exc_info.value).lower()
        assert "ollama pull" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_complete_http_500_error(self, provider):
        """Test handling of 500 error (server error)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=None, response=mock_response)
        mock_client.post.side_effect = error
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.complete(messages)
        
        assert "server error" in str(exc_info.value).lower()
        assert "ollama serve" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_complete_connection_error(self, provider):
        """Test handling of connection error."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.complete(messages)
        
        assert "cannot connect" in str(exc_info.value).lower()
        assert "ollama serve" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_complete_generic_error(self, provider):
        """Test handling of generic errors."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = RuntimeError("Something went wrong")
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.complete(messages)
        
        assert "completion failed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_list_models(self, provider, mock_response):
        """Test listing available models."""
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2", "size": 3825819519},
                {"name": "codellama", "size": 4804467907}
            ]
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        provider._client = mock_client
        
        models = await provider.list_models()
        
        assert len(models) == 2
        assert models[0]["name"] == "llama2"
        assert models[1]["name"] == "codellama"
        
        mock_client.get.assert_called_once_with("/api/tags")
    
    @pytest.mark.asyncio
    async def test_list_models_error(self, provider):
        """Test error handling in list_models."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network error")
        provider._client = mock_client
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.list_models()
        
        assert "failed to list" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_pull_model(self, provider, mock_response):
        """Test pulling a model."""
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        await provider.pull_model("llama2")
        
        mock_client.post.assert_called_once_with(
            "/api/pull",
            json={"name": "llama2"},
            timeout=None
        )
    
    @pytest.mark.asyncio
    async def test_pull_model_error(self, provider):
        """Test error handling in pull_model."""
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Download failed")
        provider._client = mock_client
        
        with pytest.raises(ProviderError) as exc_info:
            await provider.pull_model("llama2")
        
        assert "failed to pull" in str(exc_info.value).lower()
    
    def test_validate_auth_success(self, provider):
        """Test successful validation (connection check)."""
        with patch('httpx.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            provider.validate_auth()  # Should not raise
            
            mock_get.assert_called_once_with(
                "http://localhost:11434/api/tags",
                timeout=5
            )
    
    def test_validate_auth_connection_error(self, provider):
        """Test validation with connection error."""
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            with pytest.raises(ProviderError) as exc_info:
                provider.validate_auth()
            
            assert "cannot connect" in str(exc_info.value).lower()
            assert "ollama serve" in str(exc_info.value)
    
    def test_validate_auth_generic_error(self, provider):
        """Test validation with generic error."""
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = RuntimeError("Unexpected error")
            
            with pytest.raises(ProviderError) as exc_info:
                provider.validate_auth()
            
            assert "validation failed" in str(exc_info.value).lower()
    
    def test_format_messages(self, provider):
        """Test message formatting."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            {"role": "ASSISTANT", "content": "Hi!"},
            Message(role=MessageRole.SYSTEM, content="Be helpful")
        ]
        
        formatted = provider._format_messages(messages)
        
        assert len(formatted) == 3
        assert formatted[0] == {"role": "user", "content": "Hello"}
        assert formatted[1] == {"role": "assistant", "content": "Hi!"}
        assert formatted[2] == {"role": "system", "content": "Be helpful"}
    
    def test_format_messages_invalid_type(self, provider):
        """Test error handling for invalid message types."""
        messages = ["Invalid message type"]
        
        with pytest.raises(ValueError) as exc_info:
            provider._format_messages(messages)
        
        assert "invalid message type" in str(exc_info.value).lower()
    
    def test_format_tools_as_text(self, provider):
        """Test formatting tools as text description."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        }
                    }
                }
            },
            ToolDefinition(
                name="calculator",
                description="Do math",
                parameters=[
                    ToolParameter(name="expr", type="string", description="Expression")
                ]
            )
        ]
        
        text = provider._format_tools_as_text(tools)
        
        assert "Available tools:" in text
        assert "search: Search the web" in text
        assert "calculator: Do math" in text
        assert "TOOL_CALL:" in text
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with OllamaProvider() as provider:
            assert provider._client is not None
        
        # Client should be closed after context
        # (In real implementation, we'd check if aclose was called)
    
    @pytest.mark.asyncio
    async def test_complete_without_usage_data(self, provider, mock_response):
        """Test completion when Ollama doesn't return token counts."""
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Response without token data"
            }
            # No eval_count or prompt_eval_count
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        provider._client = mock_client
        
        messages = [{"role": "user", "content": "Test"}]
        response = await provider.complete(messages)
        
        assert response.content == "Response without token data"
        assert response.usage is None  # No usage data available
