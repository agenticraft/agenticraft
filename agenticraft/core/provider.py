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
import os
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel

from .config import settings
from .exceptions import ProviderError, ProviderNotFoundError, ProviderAuthError
from .types import CompletionResponse, Message, ToolCall, ToolDefinition


class BaseProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
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
        messages: Union[List[Message], List[Dict[str, Any]]],
        model: Optional[str] = None,
        tools: Optional[Union[List[ToolDefinition], List[Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
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


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI models (GPT-4, GPT-3.5, etc.)."""
    
    def __init__(self, **kwargs):
        """Initialize OpenAI provider."""
        # Get API key from kwargs, settings, or environment
        api_key = (
            kwargs.get("api_key") or 
            settings.openai_api_key or 
            os.getenv("OPENAI_API_KEY")
        )
        if not api_key:
            raise ValueError("API key required for OpenAI provider")
        
        kwargs["api_key"] = api_key
        kwargs.setdefault("base_url", settings.openai_base_url)
        
        # Store model if provided
        self.model = kwargs.pop('model', 'gpt-4')
        
        super().__init__(**kwargs)
        
        self._client = None
    
    @property
    def client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout,
                    max_retries=self.max_retries
                )
            except ImportError:
                raise ProviderError("OpenAI provider requires 'openai' package")
        return self._client
    
    async def complete(
        self,
        messages: Union[List[Message], List[Dict[str, Any]]],
        model: Optional[str] = None,
        tools: Optional[Union[List[ToolDefinition], List[Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> CompletionResponse:
        """Get completion from OpenAI."""
        try:
            # Remove model from kwargs to avoid duplication
            kwargs.pop('model', None)
            
            # Use provided model or default
            actual_model = model or getattr(self, 'model', 'gpt-4')
            
            # Format messages
            formatted_messages = self._format_messages(messages)
            
            # Prepare request parameters
            request_params = {
                "model": actual_model,
                "messages": formatted_messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # Add tools if provided
            if tools:
                # Handle both ToolDefinition objects and raw dicts
                if tools and isinstance(tools[0], dict):
                    request_params["tools"] = tools
                else:
                    request_params["tools"] = [tool.to_openai_schema() for tool in tools]
                request_params["tool_choice"] = tool_choice if tool_choice is not None else "auto"
            
            # Make request
            response = await self.client.chat.completions.create(**request_params)
            
            # Parse response
            choice = response.choices[0]
            
            # Extract usage - handle new OpenAI format
            usage_data = None
            if response.usage:
                usage_dict = response.usage.model_dump() if hasattr(response.usage, 'model_dump') else response.usage
                # Convert to simple format expected by CompletionResponse
                if isinstance(usage_dict, dict):
                    usage_data = {
                        "prompt_tokens": usage_dict.get("prompt_tokens", 0),
                        "completion_tokens": usage_dict.get("completion_tokens", 0),
                        "total_tokens": usage_dict.get("total_tokens", 0)
                    }
                else:
                    usage_data = {
                        "prompt_tokens": getattr(usage_dict, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage_dict, "completion_tokens", 0),
                        "total_tokens": getattr(usage_dict, "total_tokens", 0)
                    }
            
            # Extract tool calls if any
            tool_calls = []
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    try:
                        # Parse arguments - handle JSON strings
                        args = tc.function.arguments
                        if isinstance(args, str):
                            import json
                            args = json.loads(args)
                        
                        tool_calls.append(ToolCall(
                            id=str(tc.id),
                            name=tc.function.name,
                            arguments=args
                        ))
                    except Exception as e:
                        # Log the error in production but continue
                        # This ensures robustness
                        continue
            
            return CompletionResponse(
                content=choice.message.content or "",
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                usage=usage_data,
                metadata={"model": actual_model},
                model=actual_model
            )
            
        except Exception as e:
            raise ProviderError(f"OpenAI completion failed: {e}") from e
    
    def validate_auth(self) -> None:
        """Validate OpenAI API key."""
        if not self.api_key or not self.api_key.startswith("sk-"):
            raise ProviderAuthError("openai")
    
    def _format_messages(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Format messages for OpenAI API.
        
        Args:
            messages: List of Message objects or message dicts
            
        Returns:
            List of message dictionaries for OpenAI API
        """
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted.append(msg.to_dict())
            elif isinstance(msg, dict):
                formatted.append(msg)
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        return formatted


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic models (Claude)."""
    
    def __init__(self, **kwargs):
        """Initialize Anthropic provider."""
        # Get API key from kwargs, settings, or environment
        api_key = (
            kwargs.get("api_key") or 
            settings.anthropic_api_key or 
            os.getenv("ANTHROPIC_API_KEY")
        )
        if not api_key:
            raise ProviderAuthError("anthropic")
        
        kwargs["api_key"] = api_key
        kwargs.setdefault("base_url", settings.anthropic_base_url)
        
        # Store model if provided
        self.model = kwargs.pop('model', 'claude-3-opus')
        
        super().__init__(**kwargs)
        
        self._client = None
    
    @property
    def client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout,
                    max_retries=self.max_retries
                )
            except ImportError:
                raise ProviderError("Anthropic provider requires 'anthropic' package")
        return self._client
    
    async def complete(
        self,
        messages: Union[List[Message], List[Dict[str, Any]]],
        model: Optional[str] = None,
        tools: Optional[Union[List[ToolDefinition], List[Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> CompletionResponse:
        """Get completion from Anthropic."""
        raise NotImplementedError(
            "Anthropic provider coming next week in v0.1.1!\n"
            "For now, please use OpenAI provider: model='gpt-4'\n"
            "Track progress: https://github.com/agenticraft/agenticraft/issues"
        )
    
    def validate_auth(self) -> None:
        """Validate Anthropic API key."""
        if not self.api_key or not self.api_key.startswith("sk-ant-"):
            raise ProviderAuthError("anthropic")


class OllamaProvider(BaseProvider):
    """Provider for local Ollama models."""
    
    def __init__(self, **kwargs):
        """Initialize Ollama provider."""
        kwargs.setdefault("base_url", settings.ollama_base_url)
        kwargs["api_key"] = "ollama"  # Ollama doesn't need API key
        
        # Store model if provided
        self.model = kwargs.pop('model', 'llama2')
        
        super().__init__(**kwargs)
    
    async def complete(
        self,
        messages: Union[List[Message], List[Dict[str, Any]]],
        model: Optional[str] = None,
        tools: Optional[Union[List[ToolDefinition], List[Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> CompletionResponse:
        """Get completion from Ollama."""
        raise NotImplementedError(
            "Ollama provider coming next week in v0.1.1!\n"
            "For now, please use OpenAI provider: model='gpt-4'\n"
            "Want to help implement it? We'd love contributions!\n"
            "See: https://github.com/agenticraft/agenticraft/blob/main/CONTRIBUTING.md"
        )
    
    def validate_auth(self) -> None:
        """Ollama doesn't require authentication."""
        pass


class ProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[str, Type[BaseProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    
    @classmethod
    def create(
        cls,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any
    ) -> BaseProvider:
        """Create a provider based on model name.
        
        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus", "ollama/llama2")
            api_key: Optional API key
            base_url: Optional base URL
            **kwargs: Additional provider arguments
            
        Returns:
            Provider instance
            
        Raises:
            ProviderNotFoundError: If no provider found for model
        """
        # Handle explicit provider:model format first
        if ":" in model:
            parts = model.split(":", 1)
            if parts[0] in cls._providers:
                provider_name = parts[0]
                model = parts[1]
            else:
                # Models with colons might be Ollama format (e.g., llama2:latest)
                provider_name = "ollama"
        # Determine provider from model name
        elif model.startswith(("gpt-", "o1-", "davinci", "curie", "babbage", "ada")):
            provider_name = "openai"
        elif model.startswith("claude"):
            provider_name = "anthropic" 
        elif model.startswith("gemini"):
            provider_name = "google"
        elif model.startswith("ollama/"):
            provider_name = "ollama"
        else:
            # Default to OpenAI for now
            provider_name = "openai"
        
        # Get provider class
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Create instance
        return provider_class(
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs
        )
    
    @classmethod
    def register(cls, name: str, provider_class: Type[BaseProvider]) -> None:
        """Register a custom provider.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
