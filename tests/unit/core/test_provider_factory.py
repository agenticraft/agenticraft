"""Tests for ProviderFactory and BaseProvider abstract class."""

from typing import Any
from unittest.mock import patch

import pytest

from agenticraft.core.exceptions import ProviderAuthError, ProviderNotFoundError
from agenticraft.core.provider import BaseProvider, ProviderFactory
from agenticraft.core.types import CompletionResponse, Message


class TestBaseProvider:
    """Test BaseProvider abstract class."""

    def test_cannot_instantiate_base_provider(self):
        """Test BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseProvider()

    def test_base_provider_implementation(self):
        """Test implementing BaseProvider correctly."""

        class TestProvider(BaseProvider):
            async def complete(
                self,
                messages: list[Message] | list[dict[str, Any]],
                model: str | None = None,
                tools: Any | None = None,
                tool_choice: Any | None = None,
                temperature: float = 0.7,
                max_tokens: int | None = None,
                **kwargs: Any,
            ) -> CompletionResponse:
                return CompletionResponse(
                    content="Test response",
                    finish_reason="stop",
                    model=model or "test-model",
                )

            def validate_auth(self) -> None:
                if not self.api_key:
                    raise ProviderAuthError("test")

        # Test initialization
        provider = TestProvider(
            api_key="test-key", base_url="https://test.com", timeout=60, max_retries=5
        )

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://test.com"
        assert provider.timeout == 60
        assert provider.max_retries == 5

        # Test auth validation
        provider.validate_auth()  # Should not raise

        # Test auth failure
        provider_no_key = TestProvider()
        with pytest.raises(ProviderAuthError):
            provider_no_key.validate_auth()


class TestProviderFactory:
    """Test ProviderFactory functionality."""

    def test_lazy_load_providers(self):
        """Test providers are loaded lazily."""
        # Clear providers first
        ProviderFactory._providers = {}

        # Should be empty initially
        assert len(ProviderFactory._providers) == 0

        # Trigger lazy loading
        ProviderFactory._lazy_load_providers()

        # Should have providers now
        assert "openai" in ProviderFactory._providers
        assert "anthropic" in ProviderFactory._providers
        assert "ollama" in ProviderFactory._providers

    def test_create_openai_provider_by_model(self):
        """Test creating OpenAI provider by model name."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            # GPT models
            provider = ProviderFactory.create(model="gpt-4")
            assert provider.__class__.__name__ == "OpenAIProvider"

            provider = ProviderFactory.create(model="gpt-3.5-turbo")
            assert provider.__class__.__name__ == "OpenAIProvider"

            # OpenAI o1 models
            provider = ProviderFactory.create(model="o1-preview")
            assert provider.__class__.__name__ == "OpenAIProvider"

    def test_create_anthropic_provider_by_model(self):
        """Test creating Anthropic provider by model name."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            provider = ProviderFactory.create(model="claude-3-opus-20240229")
            assert provider.__class__.__name__ == "AnthropicProvider"

            provider = ProviderFactory.create(model="claude-3-sonnet-20240229")
            assert provider.__class__.__name__ == "AnthropicProvider"

    def test_create_ollama_provider_by_model(self):
        """Test creating Ollama provider by model name."""
        provider = ProviderFactory.create(model="ollama/llama2")
        assert provider.__class__.__name__ == "OllamaProvider"

        provider = ProviderFactory.create(model="ollama/codellama")
        assert provider.__class__.__name__ == "OllamaProvider"

    def test_create_with_explicit_provider_prefix(self):
        """Test creating provider with explicit prefix."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            provider = ProviderFactory.create(model="openai:gpt-4")
            assert provider.__class__.__name__ == "OpenAIProvider"

    def test_create_unknown_model_raises_error(self):
        """Test unknown model raises ProviderNotFoundError."""
        with pytest.raises(
            ProviderNotFoundError, match="No provider found for model: unknown-model"
        ):
            ProviderFactory.create(model="unknown-model")

    def test_create_unknown_provider_raises_error(self):
        """Test unknown provider prefix raises error."""
        with pytest.raises(ProviderNotFoundError, match="Unknown provider: unknown"):
            ProviderFactory.create(model="unknown:model")

    def test_create_with_custom_params(self):
        """Test creating provider with custom parameters."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            provider = ProviderFactory.create(
                model="gpt-4",
                api_key="custom-key",
                base_url="https://custom.com",
                timeout=60,
                max_retries=5,
            )

            assert provider.api_key == "custom-key"
            assert provider.base_url == "https://custom.com"
            assert provider.timeout == 60
            assert provider.max_retries == 5

    def test_register_custom_provider(self):
        """Test registering a custom provider."""

        class CustomProvider(BaseProvider):
            async def complete(self, messages, **kwargs):
                return CompletionResponse(content="custom response")

            def validate_auth(self):
                pass

        # Register the provider
        ProviderFactory.register("custom", CustomProvider)

        # Ensure providers are loaded
        ProviderFactory._lazy_load_providers()

        # Should be able to create it now
        assert "custom" in ProviderFactory._providers

        # Create with explicit prefix
        with pytest.raises(ProviderNotFoundError):
            # Still need to add model detection logic
            ProviderFactory.create(model="custom-model")

    def test_ollama_model_with_colon(self):
        """Test Ollama models with version tags (contain colons)."""
        # Ollama models can have format like "llama2:latest"
        provider = ProviderFactory.create(model="llama2:latest")
        assert provider.__class__.__name__ == "OllamaProvider"

        provider = ProviderFactory.create(model="codellama:7b")
        assert provider.__class__.__name__ == "OllamaProvider"
