"""Comprehensive tests for provider module to achieve >95% coverage."""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import pytest

from agenticraft.core.provider import (
    BaseProvider, ProviderFactory, OpenAIProvider, AnthropicProvider, OllamaProvider
)
from agenticraft.core.types import Message, MessageRole, CompletionResponse, ToolCall
from agenticraft.core.exceptions import ProviderError, ProviderAuthError, ProviderNotFoundError


class TestBaseProvider:
    """Test BaseProvider abstract class."""
    
    def test_cannot_instantiate_base_provider(self):
        """Test BaseProvider cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseProvider()
    
    def test_base_provider_init(self):
        """Test BaseProvider initialization through subclass."""
        class TestProvider(BaseProvider):
            async def complete(self, messages, **kwargs):
                return CompletionResponse(content="test")
            
            def validate_auth(self):
                pass
        
        provider = TestProvider(
            api_key="test-key",
            base_url="https://test.com",
            timeout=60,
            max_retries=5
        )
        
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://test.com"
        assert provider.timeout == 60
        assert provider.max_retries == 5
    
    @pytest.mark.asyncio
    async def test_base_provider_implementation(self):
        """Test implementing BaseProvider."""
        class TestProvider(BaseProvider):
            async def complete(
                self,
                messages: List[Dict[str, Any]],
                temperature: float = 0.7,
                max_tokens: Optional[int] = None,
                tools: Optional[List[Dict[str, Any]]] = None,
                **kwargs: Any
            ) -> CompletionResponse:
                return CompletionResponse(
                    content="Test response",
                    tool_calls=[],
                    finish_reason="stop",
                    usage={"prompt_tokens": 10, "completion_tokens": 20}
                )
            
            def validate_auth(self) -> None:
                if not self.api_key:
                    raise ProviderAuthError("test")
        
        provider = TestProvider(api_key="key")
        
        # Test complete
        response = await provider.complete([{"role": "user", "content": "Hi"}])
        assert response.content == "Test response"
        
        # Test validate_auth
        provider.validate_auth()  # Should not raise
        
        # Test auth failure
        provider2 = TestProvider()
        with pytest.raises(ProviderAuthError):
            provider2.validate_auth()


class TestOpenAIProvider:
    """Test OpenAIProvider implementation."""
    
    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client."""
        with patch("openai.AsyncOpenAI") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            yield mock_client
    
    def test_openai_provider_init_with_api_key(self, mock_openai):
        """Test OpenAI provider initialization with API key."""
        provider = OpenAIProvider(api_key="test-key-123")
        
        assert provider.api_key == "test-key-123"
        assert provider._client is None  # Client created lazily
        
        # Access client to trigger creation
        _ = provider.client
        
        # Check client was created with correct params
        from openai import AsyncOpenAI
        AsyncOpenAI.assert_called_once_with(
            api_key="test-key-123",
            base_url=provider.base_url,
            timeout=30,
            max_retries=3
        )
    
    def test_openai_provider_init_with_env_key(self):
        """Test OpenAI provider with environment key."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'}):
            provider = OpenAIProvider()
            assert provider.api_key == "env-key"
    
    def test_openai_provider_init_with_settings_key(self):
        """Test OpenAI provider with settings key."""
        with patch('agenticraft.core.provider.settings') as mock_settings:
            mock_settings.openai_api_key = "settings-key"
            provider = OpenAIProvider()
            assert provider.api_key == "settings-key"
    
    def test_openai_provider_init_no_api_key(self):
        """Test OpenAI provider fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('agenticraft.core.provider.settings') as mock_settings:
                mock_settings.openai_api_key = None
                with pytest.raises(ProviderAuthError, match="openai"):
                    OpenAIProvider()
    
    def test_openai_provider_validate_auth(self):
        """Test OpenAI auth validation."""
        # Valid key
        provider = OpenAIProvider(api_key="sk-test123")
        provider.validate_auth()  # Should not raise
        
        # Invalid key format
        provider2 = OpenAIProvider(api_key="invalid-key")
        with pytest.raises(ProviderAuthError):
            provider2.validate_auth()
        
        # Empty key
        provider3 = OpenAIProvider(api_key="")
        provider3.api_key = ""  # Force empty
        with pytest.raises(ProviderAuthError):
            provider3.validate_auth()
    
    @pytest.mark.asyncio
    async def test_complete_basic(self, mock_openai):
        """Test basic completion."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="Hello! How can I help?",
                    tool_calls=None
                ),
                finish_reason="stop"
            )
        ]
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            model_dump=lambda: {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        )
        
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Create provider and call complete
        provider = OpenAIProvider(api_key="sk-test")
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        response = await provider.complete(messages)
        
        assert response.content == "Hello! How can I help?"
        assert response.tool_calls == []
        assert response.finish_reason == "stop"
        assert response.usage == {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        assert response.metadata["model"] == "gpt-4"
        
        # Check API was called correctly
        mock_openai.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["messages"] == messages
        assert call_kwargs["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_complete_with_tools(self, mock_openai):
        """Test completion with tool calls."""
        # Mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"  # Set as attribute, not Mock parameter
        mock_tool_call.function.arguments = '{"city": "London"}'
        
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="I'll check the weather for you.",
                    tool_calls=[mock_tool_call]
                ),
                finish_reason="tool_calls"
            )
        ]
        mock_response.usage = None
        
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Create provider and call
        provider = OpenAIProvider(api_key="sk-test")
        
        tools = [{"type": "function", "function": {"name": "get_weather"}}]
        response = await provider.complete(
            [{"role": "user", "content": "What's the weather?"}],
            tools=tools
        )
        
        assert response.content == "I'll check the weather for you."
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].id == "call_123"
        assert response.tool_calls[0].name == "get_weather"
        assert response.tool_calls[0].arguments == {"city": "London"}  # Should be dict after validation
        assert response.finish_reason == "tool_calls"
        
        # Check tools were passed
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["tools"] == tools
        assert call_kwargs["tool_choice"] == "auto"
    
    @pytest.mark.asyncio
    async def test_complete_with_kwargs(self, mock_openai):
        """Test complete with additional kwargs."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test", tool_calls=None), finish_reason="stop")]
        mock_response.usage = None
        
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        provider = OpenAIProvider(api_key="sk-test")
        
        await provider.complete(
            [{"role": "user", "content": "Test"}],
            temperature=0.5,
            max_tokens=500,
            model="gpt-3.5-turbo",
            top_p=0.9,
            frequency_penalty=0.5
        )
        
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["model"] == "gpt-3.5-turbo"
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["frequency_penalty"] == 0.5
    
    @pytest.mark.asyncio
    async def test_complete_error_handling(self, mock_openai):
        """Test error handling in complete."""
        mock_openai.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        provider = OpenAIProvider(api_key="sk-test")
        
        with pytest.raises(ProviderError, match="OpenAI completion failed: API Error"):
            await provider.complete([{"role": "user", "content": "Test"}])
    
    @pytest.mark.asyncio
    async def test_complete_no_content(self, mock_openai):
        """Test completion with no content (e.g., only tool calls)."""
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=None,  # No content, only tool call
                    tool_calls=[Mock(id="123", function=Mock(name="test", arguments="{}"))]),
                finish_reason="tool_calls"
            )
        ]
        mock_response.usage = None
        
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        provider = OpenAIProvider(api_key="sk-test")
        response = await provider.complete([{"role": "user", "content": "Test"}])
        
        assert response.content == ""  # Empty string when None
        assert len(response.tool_calls) == 1


class TestAnthropicProvider:
    """Test AnthropicProvider implementation."""
    
    def test_anthropic_provider_init_with_api_key(self):
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider(api_key="sk-ant-test")
        assert provider.api_key == "sk-ant-test"
    
    def test_anthropic_provider_init_no_api_key(self):
        """Test Anthropic provider without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('agenticraft.core.provider.settings') as mock_settings:
                mock_settings.anthropic_api_key = None
                with pytest.raises(ProviderAuthError, match="anthropic"):
                    AnthropicProvider()
    
    def test_anthropic_provider_validate_auth(self):
        """Test Anthropic auth validation."""
        # Valid key
        provider = AnthropicProvider(api_key="sk-ant-test123")
        provider.validate_auth()  # Should not raise
        
        # Invalid key format
        provider2 = AnthropicProvider(api_key="invalid-key")
        provider2.api_key = "invalid-key"  # Force invalid
        with pytest.raises(ProviderAuthError):
            provider2.validate_auth()
    
    @pytest.mark.asyncio
    async def test_anthropic_not_implemented(self):
        """Test Anthropic completion not implemented."""
        provider = AnthropicProvider(api_key="sk-ant-test")
        
        with pytest.raises(NotImplementedError):
            await provider.complete([{"role": "user", "content": "Test"}])


class TestOllamaProvider:
    """Test OllamaProvider implementation."""
    
    def test_ollama_provider_init(self):
        """Test Ollama provider initialization."""
        provider = OllamaProvider()
        assert provider.api_key == "ollama"  # Dummy key
        assert provider.base_url  # Should have default URL
    
    def test_ollama_provider_validate_auth(self):
        """Test Ollama auth validation (always passes)."""
        provider = OllamaProvider()
        provider.validate_auth()  # Should not raise
    
    @pytest.mark.asyncio
    async def test_ollama_not_implemented(self):
        """Test Ollama completion not implemented."""
        provider = OllamaProvider()
        
        with pytest.raises(NotImplementedError):
            await provider.complete([{"role": "user", "content": "Test"}])


class TestProviderFactory:
    """Test ProviderFactory."""
    
    def test_create_openai_provider_by_model(self):
        """Test creating OpenAI provider by model name."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            # GPT models
            provider = ProviderFactory.create(model="gpt-4")
            assert isinstance(provider, OpenAIProvider)
            
            provider = ProviderFactory.create(model="gpt-3.5-turbo")
            assert isinstance(provider, OpenAIProvider)
            
            # Other OpenAI models
            provider = ProviderFactory.create(model="o1-preview")
            assert isinstance(provider, OpenAIProvider)
    
    def test_create_anthropic_provider_by_model(self):
        """Test creating Anthropic provider by model name."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            provider = ProviderFactory.create(model="claude-3-opus")
            assert isinstance(provider, AnthropicProvider)
            
            provider = ProviderFactory.create(model="claude-3-sonnet")
            assert isinstance(provider, AnthropicProvider)
    
    def test_create_ollama_provider_by_model(self):
        """Test creating Ollama provider by model name."""
        provider = ProviderFactory.create(model="ollama/llama2")
        assert isinstance(provider, OllamaProvider)
        
        provider = ProviderFactory.create(model="ollama/codellama")
        assert isinstance(provider, OllamaProvider)
    
    def test_create_default_provider(self):
        """Test creating default provider for unknown model."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = ProviderFactory.create(model="unknown-model")
            assert isinstance(provider, OpenAIProvider)
    
    def test_create_with_custom_params(self):
        """Test creating provider with custom parameters."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'}):
            provider = ProviderFactory.create(
                model="gpt-4",
                api_key="custom-key",
                base_url="https://custom.com",
                timeout=60,
                max_retries=5
            )
            
            assert provider.api_key == "custom-key"
            assert provider.base_url == "https://custom.com"
            assert provider.timeout == 60
            assert provider.max_retries == 5
    
    def test_register_custom_provider(self):
        """Test registering a custom provider."""
        class CustomProvider(BaseProvider):
            async def complete(self, messages, **kwargs):
                return CompletionResponse(content="custom")
            
            def validate_auth(self):
                pass
        
        ProviderFactory.register("custom", CustomProvider)
        
        # Should now be able to create it
        provider = ProviderFactory.create(model="custom-model")
        assert isinstance(provider, OpenAIProvider)  # Still defaults to OpenAI
        
        # But can explicitly use it
        ProviderFactory._providers["custom"] = CustomProvider
        provider = ProviderFactory.create(model="custom/model")
        # Would need to add logic to detect custom/ prefix


class TestProviderIntegration:
    """Integration tests for providers."""
    
    @pytest.mark.asyncio
    async def test_provider_with_messages(self):
        """Test provider with Message objects."""
        with patch("openai.AsyncOpenAI") as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value = mock_client
            
            # Setup response
            mock_response = Mock()
            mock_response.choices = [
                Mock(message=Mock(content="Response", tool_calls=None), finish_reason="stop")
            ]
            mock_response.usage = Mock(
                prompt_tokens=10,
                completion_tokens=5,
                model_dump=lambda: {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            )
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            # Create provider
            provider = OpenAIProvider(api_key="sk-test")
            
            # Use Message objects
            messages = [
                Message(role=MessageRole.SYSTEM, content="You are helpful"),
                Message(role=MessageRole.USER, content="Hello")
            ]
            
            # Convert to dicts
            message_dicts = [msg.to_dict() for msg in messages]
            
            response = await provider.complete(message_dicts)
            
            assert response.content == "Response"
            assert response.usage["total_tokens"] == 15
    
    def test_import_error_handling(self):
        """Test handling of missing dependencies."""
        with patch.dict('sys.modules', {'openai': None}):
            provider = OpenAIProvider(api_key="sk-test")
            
            with pytest.raises(ProviderError, match="OpenAI provider requires 'openai' package"):
                _ = provider.client
