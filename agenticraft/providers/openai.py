"""OpenAI provider implementation for AgentiCraft."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from ..core.config import settings
from ..core.exceptions import ProviderError, ProviderAuthError
from ..core.provider import BaseProvider
from ..core.types import CompletionResponse, Message, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


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
            actual_model = model or self.model
            
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
            
            # Extract usage - modern OpenAI SDK format
            usage_data = None
            if response.usage:
                usage_data = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            # Extract tool calls if any
            tool_calls = []
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    try:
                        # Parse arguments - handle JSON strings
                        args = tc.function.arguments
                        if isinstance(args, str):
                            args = json.loads(args)
                        
                        tool_calls.append(ToolCall(
                            id=str(tc.id),
                            name=tc.function.name,
                            arguments=args
                        ))
                    except json.JSONDecodeError as e:
                        # Skip malformed tool calls
                        logger.warning(f"Failed to parse tool arguments: {e}")
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
