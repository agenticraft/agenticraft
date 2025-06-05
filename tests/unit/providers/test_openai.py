"""Unit tests for OpenAI provider.

Tests the OpenAI provider implementation with mocked API responses.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agenticraft.core.exceptions import ProviderError, ProviderAuthError
from agenticraft.providers.openai import OpenAIProvider
from agenticraft.core.types import Message, MessageRole, ToolDefinition, ToolParameter


class TestOpenAIProvider:
    """Test suite for OpenAI provider."""
    
    @pytest.fixture
    def provider(self):
        """Create OpenAI provider instance."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key'}):
            return OpenAIProvider()
    
    @pytest.fixture
    def mock_client(self):
        """Create mock OpenAI client."""
        client = MagicMock()
        client.chat = MagicMock()
        client.chat.completions = MagicMock()
        client.chat.completions.create = AsyncMock()
        return client
    
    def test_initialization_with_api_key(self):
        """Test provider initialization with API key."""
        provider = OpenAIProvider(api_key="sk-test-key")
        assert provider.api_key == "sk-test-key"
        assert provider.model == "gpt-4"
    
    def test_initialization_from_env(self):
        """Test provider initialization from environment."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-env-key'}):
            provider = OpenAIProvider()
            assert provider.api_key == "sk-env-key"
    
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('agenticraft.core.config.settings.openai_api_key', None):
                with pytest.raises(ValueError) as exc_info:
                    OpenAIProvider()
                assert "API key required" in str(exc_info.value)
    
    def test_validate_auth_success(self):
        """Test successful auth validation."""
        provider = OpenAIProvider(api_key="sk-test-key")
        provider.validate_auth()  # Should not raise
    
    def test_validate_auth_failure_no_key(self):
        """Test auth validation with missing key."""
        provider = OpenAIProvider(api_key="sk-test-key")
        provider.api_key = None
        with pytest.raises(ProviderAuthError):
            provider.validate_auth()
    
    def test_validate_auth_failure_invalid_format(self):
        """Test auth validation with invalid key format."""
        provider = OpenAIProvider(api_key="sk-test-key")
        provider.api_key = "invalid-key-format"
        with pytest.raises(ProviderAuthError):
            provider.validate_auth()
    
    @pytest.mark.asyncio
    async def test_complete_basic(self, provider, mock_client):
        """Test basic completion without tools."""
        # Mock response
        mock_message = MagicMock()
        mock_message.content = "Hello! I'm GPT-4."
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Patch client
        with patch.object(provider, '_client', mock_client):
            messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            response = await provider.complete(messages)
            
            assert response.content == "Hello! I'm GPT-4."
            assert response.finish_reason == "stop"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 20
            assert response.usage["total_tokens"] == 30
            assert response.model == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_complete_with_message_objects(self, provider, mock_client):
        """Test completion with Message objects."""
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [
                Message(role=MessageRole.SYSTEM, content="You are helpful"),
                Message(role=MessageRole.USER, content="Hello")
            ]
            
            response = await provider.complete(messages)
            
            assert response.content == "Response"
            
            # Verify messages were formatted correctly
            call_args = mock_client.chat.completions.create.call_args
            sent_messages = call_args.kwargs["messages"]
            assert len(sent_messages) == 2
            assert sent_messages[0]["role"] == "system"
            assert sent_messages[0]["content"] == "You are helpful"
            assert sent_messages[1]["role"] == "user"
            assert sent_messages[1]["content"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_complete_with_tools(self, provider, mock_client):
        """Test completion with tool calling."""
        # Mock tool call
        mock_function = MagicMock()
        mock_function.name = "calculator"
        mock_function.arguments = '{"expression": "2+2"}'
        
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function
        
        mock_message = MagicMock()
        mock_message.content = "Let me calculate that."
        mock_message.tool_calls = [mock_tool_call]
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
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
            
            response = await provider.complete(messages, tools=tools)
            
            assert response.content == "Let me calculate that."
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].id == "call_123"
            assert response.tool_calls[0].name == "calculator"
            assert response.tool_calls[0].arguments == {"expression": "2+2"}
            
            # Verify tools were included in request
            call_args = mock_client.chat.completions.create.call_args
            assert "tools" in call_args.kwargs
            assert call_args.kwargs["tool_choice"] == "auto"
    
    @pytest.mark.asyncio
    async def test_complete_with_tool_definition_objects(self, provider, mock_client):
        """Test completion with ToolDefinition objects."""
        mock_message = MagicMock()
        mock_message.content = "Using tool"
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Search for Python"}]
            tools = [
                ToolDefinition(
                    name="search",
                    description="Search the web",
                    parameters=[
                        ToolParameter(name="query", type="string", description="Search query")
                    ]
                )
            ]
            
            await provider.complete(messages, tools=tools, tool_choice="search")
            
            # Verify tool was converted to OpenAI schema
            call_args = mock_client.chat.completions.create.call_args
            assert "tools" in call_args.kwargs
            assert call_args.kwargs["tools"][0]["type"] == "function"
            assert call_args.kwargs["tools"][0]["function"]["name"] == "search"
            assert call_args.kwargs["tool_choice"] == "search"
    
    @pytest.mark.asyncio
    async def test_complete_with_parameters(self, provider, mock_client):
        """Test completion with various parameters."""
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Test"}]
            
            await provider.complete(
                messages,
                model="gpt-3.5-turbo",
                temperature=0.5,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5
            )
            
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gpt-3.5-turbo"
            assert call_args.kwargs["temperature"] == 0.5
            assert call_args.kwargs["max_tokens"] == 1000
            assert call_args.kwargs["top_p"] == 0.9
            assert call_args.kwargs["frequency_penalty"] == 0.5
            assert call_args.kwargs["presence_penalty"] == 0.5
    
    @pytest.mark.asyncio
    async def test_complete_with_model_dump_usage(self, provider, mock_client):
        """Test handling of usage data with model_dump method."""
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        # Mock usage with direct attributes
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 15
        mock_usage.completion_tokens = 25
        mock_usage.total_tokens = 40
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Test"}]
            response = await provider.complete(messages)
            
            assert response.usage["prompt_tokens"] == 15
            assert response.usage["completion_tokens"] == 25
            assert response.usage["total_tokens"] == 40
    
    @pytest.mark.asyncio
    async def test_complete_tool_call_json_parsing_error(self, provider, mock_client):
        """Test graceful handling of tool call JSON parsing errors."""
        # Create tool calls with both valid and invalid JSON
        mock_function1 = MagicMock()
        mock_function1.name = "valid_tool"
        mock_function1.arguments = '{"valid": "json"}'
        
        mock_function2 = MagicMock()
        mock_function2.name = "invalid_tool"
        mock_function2.arguments = 'invalid json {{'
        
        mock_tool_call1 = MagicMock()
        mock_tool_call1.id = "call_1"
        mock_tool_call1.function = mock_function1
        
        mock_tool_call2 = MagicMock()
        mock_tool_call2.id = "call_2"
        mock_tool_call2.function = mock_function2
        
        mock_message = MagicMock()
        mock_message.content = "Using tools"
        mock_message.tool_calls = [mock_tool_call1, mock_tool_call2]
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Test"}]
            response = await provider.complete(messages)
            
            # Should only include the valid tool call
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "valid_tool"
            assert response.tool_calls[0].arguments == {"valid": "json"}
    
    @pytest.mark.asyncio
    async def test_complete_error_handling(self, provider, mock_client):
        """Test error handling in complete."""
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Test"}]
            
            with pytest.raises(ProviderError) as exc_info:
                await provider.complete(messages)
            
            assert "OpenAI completion failed" in str(exc_info.value)
    
    def test_format_messages(self, provider):
        """Test message formatting."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            {"role": "assistant", "content": "Hi!"},
            Message(role=MessageRole.SYSTEM, content="Be helpful")
        ]
        
        formatted = provider._format_messages(messages)
        
        assert len(formatted) == 3
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["content"] == "Hi!"
        assert formatted[2]["role"] == "system"
        assert formatted[2]["content"] == "Be helpful"
    
    def test_format_messages_invalid_type(self, provider):
        """Test error handling for invalid message types."""
        messages = ["Invalid message type"]
        
        with pytest.raises(ValueError) as exc_info:
            provider._format_messages(messages)
        
        assert "Invalid message type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_client_creation(self, provider):
        """Test lazy client creation."""
        assert provider._client is None
        
        # Mock the AsyncOpenAI class
        mock_client_class = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        
        # Patch the import inside the client property
        with patch.dict('sys.modules', {'openai': MagicMock(AsyncOpenAI=mock_client_class)}):
            client = provider.client
            
            mock_client_class.assert_called_once_with(
                api_key=provider.api_key,
                base_url=provider.base_url,
                timeout=provider.timeout,
                max_retries=provider.max_retries
            )
            assert client is mock_client_instance
            assert provider._client is mock_client_instance
    
    @pytest.mark.asyncio
    async def test_import_error_handling(self):
        """Test handling of missing openai package."""
        with patch.dict('sys.modules', {'openai': None}):
            provider = OpenAIProvider(api_key="sk-test-key")
            
            with pytest.raises(ProviderError) as exc_info:
                _ = provider.client
            
            assert "openai" in str(exc_info.value).lower()
            assert "package" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, provider, mock_client):
        """Test handling of empty content in response."""
        mock_message = MagicMock()
        mock_message.content = None  # OpenAI sometimes returns None
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Test"}]
            response = await provider.complete(messages)
            
            assert response.content == ""  # Should convert None to empty string
    
    def test_initialization_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            base_url="https://custom.openai-proxy.com/v1"
        )
        assert provider.base_url == "https://custom.openai-proxy.com/v1"
    
    def test_initialization_with_custom_model(self):
        """Test initialization with custom default model."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-3.5-turbo-16k"
        )
        assert provider.model == "gpt-3.5-turbo-16k"
