"""LLM provider interfaces for AgentiCraft.

This module provides the base classes and factory for integrating
various LLM providers (OpenAI, Anthropic, Google, etc.) with AgentiCraft.

Example:
    Using different providers::

        from agenticraft import Agent

        # OpenAI (default)
        agent = Agent(model="gpt-4")

        # Anthropic
        agent = Agent(model="claude-3-opus", api_key="...")

        # Local Ollama
        agent = Agent(model="ollama/llama2", base_url="http://localhost:11434")
"""

from abc import ABC, abstractmethod
from typing import Any

from .exceptions import ProviderNotFoundError
from .types import CompletionResponse, Message, ToolDefinition


class BaseProvider(ABC):
    """Base class for LLM providers."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize provider.

        Args:
            api_key: API key for authentication
            base_url: Optional base URL override
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def complete(
        self,
        messages: list[Message] | list[dict[str, Any]],
        model: str | None = None,
        tools: list[ToolDefinition] | list[dict[str, Any]] | None = None,
        tool_choice: Any | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Get completion from the LLM.

        Args:
            messages: Conversation messages
            model: Optional model override
            tools: Available tools
            tool_choice: Tool choice strategy
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific arguments

        Returns:
            CompletionResponse with generated content
        """
        pass

    @abstractmethod
    def validate_auth(self) -> None:
        """Validate authentication credentials.

        Raises:
            ProviderAuthError: If authentication fails
        """
        pass


class ProviderFactory:
    """Factory for creating LLM providers."""

    _providers: dict[str, type[BaseProvider]] = {}

    @classmethod
    def _lazy_load_providers(cls) -> None:
        """Lazily load provider implementations."""
        if not cls._providers:
            from ..providers.anthropic import AnthropicProvider
            from ..providers.ollama import OllamaProvider
            from ..providers.openai import OpenAIProvider

            cls._providers = {
                "openai": OpenAIProvider,
                "anthropic": AnthropicProvider,
                "ollama": OllamaProvider,
            }

    @classmethod
    def create(
        cls,
        model: str,
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> BaseProvider:
        """Create a provider based on model name.

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus", "ollama/llama2")
            provider: Optional explicit provider name (overrides auto-detection)
            api_key: Optional API key
            base_url: Optional base URL
            **kwargs: Additional provider arguments

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If no provider found for model
        """
        # If explicit provider specified, use it
        if provider:
            # Ensure providers are loaded
            cls._lazy_load_providers()

            provider_class = cls._providers.get(provider)
            if not provider_class:
                raise ProviderNotFoundError(f"Unknown provider: {provider}")

            return provider_class(
                api_key=api_key, base_url=base_url, model=model, **kwargs
            )

        # Otherwise, Common Ollama model prefixes
        ollama_models = (
            "llama",
            "llama2",
            "llama3",
            "codellama",
            "mistral",
            "mixtral",
            "gemma",
            "phi",
            "vicuna",
            "orca",
            "neural-chat",
            "starling",
            "deepseek",
            "qwen",
            "dolphin",
            "yi",
            "solar",
            "command-r",
        )

        # Handle explicit provider:model format first
        if ":" in model and not model.startswith("ollama/"):
            parts = model.split(":", 1)
            # Check if it's an Ollama model with version tag first
            if any(parts[0].startswith(ollama) for ollama in ollama_models):
                provider_name = "ollama"
            else:
                # Ensure providers are loaded before checking
                cls._lazy_load_providers()
                if parts[0] in cls._providers:
                    provider_name = parts[0]
                    model = parts[1]
                else:
                    # If using provider:model format, provider must be known
                    raise ProviderNotFoundError(f"Unknown provider: {parts[0]}")
        # Determine provider from model name
        elif model.startswith(("gpt-", "o1-", "davinci", "curie", "babbage", "ada")):
            provider_name = "openai"
        elif model.startswith("claude"):
            provider_name = "anthropic"
        elif model.startswith("gemini"):
            provider_name = "google"
        elif model.startswith("ollama/"):
            provider_name = "ollama"
        # Check if it's a known Ollama model
        elif any(model.startswith(ollama) for ollama in ollama_models):
            provider_name = "ollama"
        else:
            # Unknown model
            raise ProviderNotFoundError(f"No provider found for model: {model}")

        # Ensure providers are loaded (may have been called above already)
        if not cls._providers:
            cls._lazy_load_providers()

        # Get provider class
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ProviderNotFoundError(f"Unknown provider: {provider_name}")

        # Create instance
        return provider_class(api_key=api_key, base_url=base_url, model=model, **kwargs)

    @classmethod
    def register(cls, name: str, provider_class: type[BaseProvider]) -> None:
        """Register a custom provider.

        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class


__all__ = [
    "BaseProvider",
    "ProviderFactory",
]
