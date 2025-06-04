"""Unit tests for provider module.

This module tests the LLM provider functionality including:
- Provider factory
- Different provider implementations
- Error handling and retries
- Tool calling
"""

import asyncio
import os
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from agenticraft.core.provider import (
    BaseProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    ProviderFactory,
)
from agenticraft.core.exceptions import (
    ProviderError,
    ProviderNotFoundError,
    ProviderAuthError,
)
from agenticraft.core.types import (
    CompletionResponse,
    ToolCall,
)


class TestBaseProvider:
    """Test BaseProvider abstract class."""
    
    def test_base_provider_cannot_be_instantiated(self):
        """Test that BaseProvider is abstract."""
        with pytest.raises(TypeError):
            BaseProvider()
    
    def test_provider_error_hierarchy(self):
        """Test ProviderError exception."""
        error = ProviderError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


# MockProvider tests removed - provider not implemented


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    def test_openai_provider_initialization(self):
        """Test OpenAI provider setup."""
        provider = OpenAIProvider(
            model="gpt-4",
            api_key="test-key",
            base_url="https://api.openai.com/v1"
        )
        
        assert provider.model == "gpt-4"
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.openai.com/v1"
    
    def test_openai_provider_requires_api_key(self):
        """Test OpenAI provider requires API key."""
        # Ensure no API key from environment or settings
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}, clear=True):
            with patch('agenticraft.core.provider.settings.openai_api_key', None):
                with pytest.raises(ValueError, match="API key required for OpenAI provider"):
                    OpenAIProvider(model="gpt-4", api_key=None)
    
    @pytest.mark.asyncio
    async def test_openai_provider_complete(self):
        """Test OpenAI completion with mocked client."""
        with patch("openai.AsyncOpenAI") as MockClient:
            # Setup mock
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(
                    message=MagicMock(
                        content="Test response",
                        tool_calls=None
                    ),
                    finish_reason="stop"
                )
            ]
            # Create a proper usage mock that returns a dict when model_dump is called
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 10
            mock_usage.completion_tokens = 5
            mock_usage.total_tokens = 15
            mock_usage.model_dump.return_value = {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
            mock_response.usage = mock_usage
            mock_response.model = "gpt-4"
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            # Test
            provider = OpenAIProvider(model="gpt-4", api_key="test-key")
            response = await provider.complete([
                {"role": "user", "content": "Hello"}
            ])
            
            assert response.content == "Test response"
            assert response.model == "gpt-4"
            assert response.usage["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_openai_provider_with_tools(self):
        """Test OpenAI provider with tool calling."""
        with patch("openai.AsyncOpenAI") as MockClient:
            # Setup mock
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            
            # Mock tool call
            mock_tool_call = MagicMock()
            mock_tool_call.id = "call_123"
            mock_tool_call.function.name = "search"
            mock_tool_call.function.arguments = '{"query": "weather"}'
            
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(
                    message=MagicMock(
                        content="I'll search for that.",
                        tool_calls=[mock_tool_call]
                    ),
                    finish_reason="tool_calls"
                )
            ]
            # Create a proper usage mock that returns a dict when model_dump is called
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 10
            mock_usage.completion_tokens = 5
            mock_usage.total_tokens = 15
            mock_usage.model_dump.return_value = {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
            mock_response.usage = mock_usage
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            # Test
            provider = OpenAIProvider(model="gpt-4", api_key="test-key")
            response = await provider.complete(
                messages=[{"role": "user", "content": "What's the weather?"}],
                tools=[{"type": "function", "function": {"name": "search"}}]
            )
            
            assert response.content == "I'll search for that."
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "search"
            assert response.tool_calls[0].arguments == {"query": "weather"}
    
    @pytest.mark.asyncio
    async def test_openai_provider_retry_on_error(self):
        """Test OpenAI provider retries on errors."""
        # Note: The OpenAI client handles retries internally
        # This test verifies that we properly configure max_retries
        with patch("openai.AsyncOpenAI") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            
            # Create provider with retries configured
            provider = OpenAIProvider(
                model="gpt-4",
                api_key="test-key",
                max_retries=2
            )
            
            # Access the client property to trigger lazy creation
            _ = provider.client
            
            # Verify the client was created with max_retries
            # Note: base_url comes from settings default
            MockClient.assert_called_once_with(
                api_key="test-key",
                base_url="https://api.openai.com/v1",  # Default from settings
                timeout=30,
                max_retries=2
            )
            
            # Now test that errors are properly raised
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("Network error")
            )
            
            with pytest.raises(ProviderError, match="OpenAI completion failed: Network error"):
                await provider.complete([
                    {"role": "user", "content": "Hello"}
                ])


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""
    
    def test_anthropic_provider_initialization(self):
        """Test Anthropic provider setup."""
        provider = AnthropicProvider(
            model="claude-3-opus",
            api_key="test-key"
        )
        
        assert provider.model == "claude-3-opus"
        assert provider.api_key == "test-key"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Anthropic module not installed")
    async def test_anthropic_provider_complete(self):
        """Test Anthropic completion with mocked client."""
        with patch("anthropic.AsyncAnthropic") as MockClient:
            # Setup mock
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    type="text",
                    text="Claude response"
                )
            ]
            mock_response.usage = MagicMock(
                input_tokens=10,
                output_tokens=5
            )
            mock_response.model = "claude-3-opus"
            
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            
            # Test
            provider = AnthropicProvider(model="claude-3-opus", api_key="test-key")
            response = await provider.complete([
                {"role": "user", "content": "Hello Claude"}
            ])
            
            assert response.content == "Claude response"
            assert response.model == "claude-3-opus"
            assert response.usage["total_tokens"] == 15


class TestProviderFactory:
    """Test ProviderFactory for creating providers."""
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        provider = ProviderFactory.create(
            model="gpt-4",
            api_key="test-key"
        )
        
        assert provider.__class__.__name__ == "OpenAIProvider"
        assert provider.model == "gpt-4"
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        provider = ProviderFactory.create(
            model="claude-3-opus",
            api_key="test-key"
        )
        
        assert isinstance(provider, AnthropicProvider)
        assert provider.model == "claude-3-opus"
    
    # Google provider not implemented yet
    
    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        provider = ProviderFactory.create(
            model="llama2:latest",
            base_url="http://localhost:11434"
        )
        
        assert isinstance(provider, OllamaProvider)
        assert provider.model == "llama2:latest"
    
    # Mock provider not implemented
    
    def test_create_with_provider_prefix(self):
        """Test creating provider with explicit prefix."""
        provider = ProviderFactory.create(
            model="openai:gpt-3.5-turbo",
            api_key="test-key"
        )
        
        assert provider.__class__.__name__ == "OpenAIProvider"
        assert provider.model == "gpt-3.5-turbo"
    
    def test_create_unknown_provider(self):
        """Test creating unknown provider raises error."""
        with pytest.raises(ValueError, match="Unknown provider: unknown"):
            ProviderFactory.create(model="unknown:model")
    
    def test_register_custom_provider(self):
        """Test registering custom provider."""
        class CustomProvider(BaseProvider):
            async def complete(self, messages, **kwargs):
                return CompletionResponse(
                    content="Custom response",
                    model="custom"
                )
        
        ProviderFactory.register("custom", CustomProvider)
        
        provider = ProviderFactory.create(model="custom:test")
        assert isinstance(provider, CustomProvider)
    
    # list_providers method not implemented in ProviderFactory
