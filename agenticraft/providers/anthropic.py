"""Anthropic provider implementation for AgentiCraft."""

import os
from typing import Any, Dict, List, Optional, Union

from ..core.config import settings
from ..core.exceptions import ProviderError, ProviderAuthError
from ..core.provider import BaseProvider
from ..core.types import CompletionResponse, Message, ToolCall, ToolDefinition


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
        self.model = kwargs.pop('model', 'claude-3-opus-20240229')
        
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
        """Get completion from Anthropic.
        
        Reference: Simplified from agentic-framework patterns.
        """
        try:
            # Use provided model or default
            actual_model = model or self.model
            
            # Format messages - extract system message (Anthropic pattern)
            system_prompt, chat_messages = self._extract_system_message(messages)
            
            # Prepare request parameters
            request_params = {
                "model": actual_model,
                "messages": self._format_messages(chat_messages),
                "max_tokens": max_tokens or 4096,
                "temperature": temperature,
                **kwargs
            }
            
            # Add system prompt if present
            if system_prompt:
                request_params["system"] = system_prompt
            
            # Add tools if provided
            if tools:
                request_params["tools"] = self._convert_tools(tools)
                if tool_choice is not None:
                    request_params["tool_choice"] = self._format_tool_choice(tool_choice)
            
            # Make API call
            response = await self.client.messages.create(**request_params)
            
            # Parse response content
            content = ""
            tool_calls = []
            
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text
                elif hasattr(block, 'type') and block.type == 'tool_use':
                    # Extract tool call information
                    tool_calls.append(ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input
                    ))
            
            # Extract usage information
            usage_data = None
            if hasattr(response, 'usage'):
                usage_data = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            
            return CompletionResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=response.stop_reason,
                usage=usage_data,
                metadata={
                    "model": actual_model,
                    "stop_sequence": getattr(response, 'stop_sequence', None)
                },
                model=actual_model
            )
            
        except Exception as e:
            raise ProviderError(f"Anthropic completion failed: {e}") from e
    
    def _extract_system_message(self, messages: Union[List[Message], List[Dict[str, Any]]]) -> tuple:
        """Extract system message from messages list.
        
        Pattern from agentic-framework: Anthropic requires system message
        to be passed separately.
        """
        system_prompt = None
        chat_messages = []
        
        for msg in messages:
            # Handle both Message objects and dicts
            if isinstance(msg, Message):
                role = str(msg.role)
                content = msg.content
            else:
                role = msg.get("role")
                content = msg.get("content")
            
            if role == "system":
                system_prompt = content
            else:
                chat_messages.append(msg)
        
        return system_prompt, chat_messages
    
    def _format_messages(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Format messages for Anthropic API."""
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted.append(msg.to_dict())
            elif isinstance(msg, dict):
                formatted.append(msg)
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        return formatted
    
    def _convert_tools(self, tools: Union[List[ToolDefinition], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Convert tools to Anthropic format.
        
        Pattern from agentic-framework: Different tool schema format.
        """
        anthropic_tools = []
        
        for tool in tools:
            if isinstance(tool, ToolDefinition):
                # Convert from ToolDefinition
                schema = tool.to_openai_schema()
                func_def = schema["function"]
                anthropic_tools.append({
                    "name": func_def["name"],
                    "description": func_def["description"],
                    "input_schema": func_def["parameters"]
                })
            elif isinstance(tool, dict):
                # Already in dict format - convert to Anthropic format
                if "function" in tool:
                    # OpenAI format
                    func = tool["function"]
                    anthropic_tools.append({
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {})
                    })
                else:
                    # Assume it's already in Anthropic format
                    anthropic_tools.append(tool)
        
        return anthropic_tools
    
    def _format_tool_choice(self, tool_choice: Any) -> Dict[str, Any]:
        """Format tool choice for Anthropic API."""
        if isinstance(tool_choice, str):
            if tool_choice == "auto":
                return {"type": "auto"}
            elif tool_choice == "none":
                return {"type": "any"}
            else:
                # Specific tool name
                return {"type": "tool", "name": tool_choice}
        elif isinstance(tool_choice, dict):
            return tool_choice
        else:
            return {"type": "auto"}
    
    def validate_auth(self) -> None:
        """Validate Anthropic API key."""
        if not self.api_key:
            raise ProviderAuthError("anthropic")
        # Modern Anthropic keys may have different prefixes
        # Just ensure we have a non-empty key
