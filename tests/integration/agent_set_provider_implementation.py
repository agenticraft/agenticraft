"""Example implementation of set_provider method for the Agent class.

This shows how the Agent class could be extended to support provider switching.
This would need to be added to the core/agent.py file.
"""

from typing import Any

from agenticraft.core.exceptions import ProviderError
from agenticraft.core.provider import ProviderFactory

# This method should be added to the Agent class in core/agent.py


def set_provider(
    self,
    provider_name: str,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
) -> None:
    """Switch the agent's LLM provider.

    This method allows dynamic switching between different LLM providers
    while preserving the agent's configuration, tools, memory, and state.

    Args:
        provider_name: Name of the provider ("openai", "anthropic", "ollama")
        model: Optional model override for the new provider
        api_key: Optional API key for the new provider
        base_url: Optional base URL (mainly for Ollama)
        **kwargs: Additional provider-specific parameters

    Raises:
        ProviderError: If the provider name is invalid or setup fails

    Example:
        Switching to Anthropic::

            agent.set_provider("anthropic", model="claude-3-opus-20240229")

        Switching to Ollama::

            agent.set_provider("ollama", model="llama2", base_url="http://localhost:11434")
    """
    # Map of provider names to their default models
    provider_defaults = {
        "openai": "gpt-4",
        "anthropic": "claude-3-opus-20240229",
        "ollama": "llama2",
    }

    # Validate provider name
    if provider_name not in provider_defaults:
        raise ProviderError(
            f"Unknown provider: {provider_name}. "
            f"Valid providers are: {', '.join(provider_defaults.keys())}"
        )

    # Determine model to use
    if model is None:
        # If no model specified, use provider default
        model = provider_defaults[provider_name]
    else:
        # For Ollama, strip "ollama/" prefix if present
        if provider_name == "ollama" and model.startswith("ollama/"):
            model = model[7:]  # Remove "ollama/" prefix

    # Store current provider in case we need to rollback
    old_provider = self._provider
    old_model = self.config.model

    try:
        # Update configuration
        self.config.model = model
        if api_key:
            self.config.api_key = api_key
        if base_url:
            self.config.base_url = base_url

        # Create new provider
        # ProviderFactory uses model name to determine provider,
        # so we need to ensure the model name is appropriate
        self._provider = ProviderFactory.create(
            model=model,
            api_key=api_key or self.config.api_key,
            base_url=base_url or self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            **kwargs,
        )

        # Log the switch
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Agent '{self.name}' switched from {old_model} to "
            f"{provider_name}/{model}"
        )

    except Exception as e:
        # Rollback on failure
        self._provider = old_provider
        self.config.model = old_model
        raise ProviderError(f"Failed to switch provider: {e}") from e


# Additional helper methods that could be useful:


def get_provider_info(self) -> dict[str, Any]:
    """Get information about the current provider.

    Returns:
        Dict containing provider name, model, and capabilities
    """
    return {
        "provider": self.provider.name,
        "model": self.config.model,
        "supports_streaming": hasattr(self.provider, "stream"),
        "supports_tools": True,  # All providers should support tools via adaptation
        "timeout": self.config.timeout,
        "max_retries": self.config.max_retries,
    }


def list_available_providers(self) -> list[str]:
    """List available LLM providers.

    Returns:
        List of provider names that can be used with set_provider
    """
    return ["openai", "anthropic", "ollama"]


# Example usage showing how these methods would work:

if __name__ == "__main__":
    from agenticraft import Agent, tool

    # Create an agent
    agent = Agent(
        name="FlexibleAgent",
        instructions="You are a helpful assistant that can work with any LLM.",
    )

    # Define a tool
    @tool
    def calculate(expression: str) -> float:
        """Evaluate a mathematical expression."""
        return eval(expression)

    agent.add_tool(calculate)

    # Start with OpenAI
    response = agent.run("Hello! What model are you?")
    print(f"OpenAI says: {response.content}")

    # Switch to Anthropic
    agent.set_provider("anthropic", model="claude-3-sonnet-20240229")
    response = agent.run("Hello! What model are you now?")
    print(f"Anthropic says: {response.content}")

    # Switch to Ollama for local inference
    agent.set_provider("ollama", model="llama2", base_url="http://localhost:11434")
    response = agent.run("Hello! What model are you running as?")
    print(f"Ollama says: {response.content}")

    # Tools still work after switching
    response = agent.run("Calculate 42 * 17 for me")
    print(f"Calculation result: {response.content}")

    # Get provider info
    info = agent.get_provider_info()
    print(f"Current provider info: {info}")
