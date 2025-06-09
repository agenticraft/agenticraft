"""LLM provider implementations for AgentiCraft.

This module contains implementations of various LLM providers.
Each provider is in its own file for better organization and maintainability.
"""

from .anthropic import AnthropicProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider


def list_providers():
    """List all available provider names."""
    return ["openai", "anthropic", "ollama"]


def get_provider(provider_name: str, **kwargs):
    """Get a provider instance by name.

    This is a convenience function that creates a provider instance
    based on the provider name.

    Args:
        provider_name: Name of the provider ("openai", "anthropic", "ollama")
        **kwargs: Additional arguments passed to the provider constructor

    Returns:
        Provider instance

    Raises:
        ValueError: If provider name is invalid
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }

    if provider_name not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Valid providers are: {', '.join(providers.keys())}"
        )

    return providers[provider_name](**kwargs)


__all__ = [
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "list_providers",
    "get_provider",
]
