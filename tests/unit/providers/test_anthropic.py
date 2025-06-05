"""Unit tests for Anthropic provider.

Tests the Anthropic provider implementation with mocked API responses.
"""

import json
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agenticraft.core.exceptions import ProviderError, ProviderAuthError
from agenticraft.providers.anthropic import AnthropicProvider
from agenticraft.core.types import Message, MessageRole, ToolDefinition, ToolParameter


class TestAnthropicProvider:
    """Test suite for Anthropic provider."""
    
    @pytest.fixture
    def provider(self):
        """Create Anthropic provider instance."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            return AnthropicProvider()
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Anthropic client."""
        client = MagicMock()
        client.messages = MagicMock()
        client.messages.create = AsyncMock()
        return client
    
    def test_initialization_with_api_key(self):
        """Test provider initialization with API key."""
        provider = AnthropicProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-opus-20240229"
    
    def test_initialization_from_env(self):
        """Test provider initialization from environment."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'env-key'}):
            provider = AnthropicProvider()
            assert provider.api_key == "env-key"
    
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('agenticraft.core.config.settings.anthropic_api_key', None):
                with pytest.raises(ProviderAuthError):
                    AnthropicProvider()
    
    def test_validate_auth_success(self):
        """Test successful auth validation."""
        provider = AnthropicProvider(api_key="test-key")
        provider.validate_auth()  # Should not raise
    
    def test_validate_auth_failure(self):
        """Test auth validation with missing key."""
        provider = AnthropicProvider(api_key="test-key")
        provider.api_key = None
        with pytest.raises(ProviderAuthError):
            provider.validate_auth()
    
    @pytest.mark.asyncio
    async def test_complete_basic(self, provider, mock_client):
        """Test basic completion without tools."""
        # Mock response
        class MockTextBlock:
            def __init__(self, text):
                self.text = text
        
        mock_response = MagicMock()
        mock_response.content = [MockTextBlock("Hello! How can I help?")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_client.messages.create.return_value = mock_response
        
        # Patch client
        with patch.object(provider, '_client', mock_client):
            messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            response = await provider.complete(messages)
            
            assert response.content == "Hello! How can I help?"
            assert response.finish_reason == "end_turn"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 20
            assert response.usage["total_tokens"] == 30
    
    @pytest.mark.asyncio
    async def test_complete_with_system_message(self, provider, mock_client):
        """Test completion with system message extraction."""
        class MockTextBlock:
            def __init__(self, text):
                self.text = text
        
        mock_response = MagicMock()
        mock_response.content = [MockTextBlock("I understand.")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 5
        mock_client.messages.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hi"}
            ]
            
            await provider.complete(messages)
            
            # Verify system message was extracted
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["system"] == "You are helpful."
            assert len(call_args.kwargs["messages"]) == 1
            assert call_args.kwargs["messages"][0]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_complete_with_message_objects(self, provider, mock_client):
        """Test completion with Message objects."""
        class MockTextBlock:
            def __init__(self, text):
                self.text = text
        
        mock_response = MagicMock()
        mock_response.content = [MockTextBlock("Response")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 5
        mock_client.messages.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [
                Message(role=MessageRole.SYSTEM, content="System prompt"),
                Message(role=MessageRole.USER, content="User message")
            ]
            
            response = await provider.complete(messages)
            
            assert response.content == "Response"
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["system"] == "System prompt"
    
    @pytest.mark.asyncio
    async def test_complete_with_tools(self, provider, mock_client):
        """Test completion with tool calling."""
        # Mock response with tool use
        # Create simple mock objects instead of MagicMock
        class MockTextBlock:
            def __init__(self, text):
                self.text = text
        
        class MockToolBlock:
            def __init__(self):
                self.type = "tool_use"
                self.id = "tool_123"
                self.name = "calculator"
                self.input = {"a": 2, "b": 3}
        
        text_block = MockTextBlock("Let me calculate that.")
        tool_block = MockToolBlock()
        
        mock_response = MagicMock()
        mock_response.content = [
            text_block,
            tool_block
        ]
        mock_response.stop_reason = "tool_use"
        mock_response.usage.input_tokens = 30
        mock_response.usage.output_tokens = 40
        mock_client.messages.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "What's 2+3?"}]
            tools = [{
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Perform calculations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"}
                        }
                    }
                }
            }]
            
            response = await provider.complete(messages, tools=tools)
            
            assert response.content == "Let me calculate that."
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "calculator"
            assert response.tool_calls[0].arguments == {"a": 2, "b": 3}
            
            # Verify tools were converted to Anthropic format
            call_args = mock_client.messages.create.call_args
            assert "tools" in call_args.kwargs
            assert call_args.kwargs["tools"][0]["name"] == "calculator"
    
    @pytest.mark.asyncio
    async def test_complete_with_tool_choice(self, provider, mock_client):
        """Test completion with tool choice parameter."""
        class MockTextBlock:
            def __init__(self, text):
                self.text = text
        
        mock_response = MagicMock()
        mock_response.content = [MockTextBlock("Using tool")]
        mock_response.stop_reason = "tool_use"
        mock_client.messages.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Calculate"}]
            tools = [{"name": "calc", "description": "Calculator", "input_schema": {}}]
            
            # Test auto tool choice
            await provider.complete(messages, tools=tools, tool_choice="auto")
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["tool_choice"] == {"type": "auto"}
            
            # Test specific tool choice
            await provider.complete(messages, tools=tools, tool_choice="calc")
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["tool_choice"] == {"type": "tool", "name": "calc"}
    
    @pytest.mark.asyncio
    async def test_complete_with_parameters(self, provider, mock_client):
        """Test completion with various parameters."""
        class MockTextBlock:
            def __init__(self, text):
                self.text = text
        
        mock_response = MagicMock()
        mock_response.content = [MockTextBlock("Response")]
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 10
        mock_client.messages.create.return_value = mock_response
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Test"}]
            
            await provider.complete(
                messages,
                model="claude-3-sonnet-20240229",
                temperature=0.5,
                max_tokens=2000,
                top_p=0.9
            )
            
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["model"] == "claude-3-sonnet-20240229"
            assert call_args.kwargs["temperature"] == 0.5
            assert call_args.kwargs["max_tokens"] == 2000
            assert call_args.kwargs["top_p"] == 0.9
    
    @pytest.mark.asyncio
    async def test_complete_error_handling(self, provider, mock_client):
        """Test error handling in complete."""
        mock_client.messages.create.side_effect = Exception("API Error")
        
        with patch.object(provider, '_client', mock_client):
            messages = [{"role": "user", "content": "Test"}]
            
            with pytest.raises(ProviderError) as exc_info:
                await provider.complete(messages)
            
            assert "Anthropic completion failed" in str(exc_info.value)
    
    def test_extract_system_message(self, provider):
        """Test system message extraction."""
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        system, chat_messages = provider._extract_system_message(messages)
        
        assert system == "Be helpful"
        assert len(chat_messages) == 3
        assert all(msg.get("role") != "system" for msg in chat_messages)
    
    def test_format_messages(self, provider):
        """Test message formatting."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            {"role": "assistant", "content": "Hi!"}
        ]
        
        formatted = provider._format_messages(messages)
        
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["content"] == "Hi!"
    
    def test_convert_tools_openai_format(self, provider):
        """Test tool conversion from OpenAI format."""
        tools = [{
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search the web",
                "parameters": {"type": "object", "properties": {}}
            }
        }]
        
        converted = provider._convert_tools(tools)
        
        assert len(converted) == 1
        assert converted[0]["name"] == "search"
        assert converted[0]["description"] == "Search the web"
        assert converted[0]["input_schema"] == {"type": "object", "properties": {}}
    
    def test_convert_tools_tool_definition(self, provider):
        """Test tool conversion from ToolDefinition objects."""
        tools = [
            ToolDefinition(
                name="calculator",
                description="Perform math",
                parameters=[
                    ToolParameter(name="a", type="number", description="First number"),
                    ToolParameter(name="b", type="number", description="Second number")
                ]
            )
        ]
        
        converted = provider._convert_tools(tools)
        
        assert len(converted) == 1
        assert converted[0]["name"] == "calculator"
        assert converted[0]["description"] == "Perform math"
        assert "properties" in converted[0]["input_schema"]
    
    def test_format_tool_choice(self, provider):
        """Test tool choice formatting."""
        assert provider._format_tool_choice("auto") == {"type": "auto"}
        assert provider._format_tool_choice("none") == {"type": "any"}
        assert provider._format_tool_choice("search") == {"type": "tool", "name": "search"}
        assert provider._format_tool_choice({"type": "custom"}) == {"type": "custom"}
        assert provider._format_tool_choice(123) == {"type": "auto"}  # Invalid input
    
    @pytest.mark.asyncio
    async def test_client_creation(self, provider):
        """Test lazy client creation."""
        assert provider._client is None
        
        # Mock the AsyncAnthropic class
        mock_client_class = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        
        # Patch the import inside the client property
        with patch.dict('sys.modules', {'anthropic': MagicMock(AsyncAnthropic=mock_client_class)}):
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
        """Test handling of missing anthropic package."""
        with patch.dict('sys.modules', {'anthropic': None}):
            provider = AnthropicProvider(api_key="test-key")
            
            with pytest.raises(ProviderError) as exc_info:
                _ = provider.client
            
            assert "anthropic" in str(exc_info.value).lower()
            assert "package" in str(exc_info.value).lower()
