"""OpenAI provider implementation for AgentiCraft."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from ..core.config import settings
from ..core.exceptions import ProviderAuthError, ProviderError
from ..core.provider import BaseProvider
from ..core.streaming import StreamChunk, StreamingProvider, StreamInterruptedError
from ..core.types import CompletionResponse, Message, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider, StreamingProvider):
    """Provider for OpenAI models (GPT-4, GPT-3.5, etc.) with streaming support."""

    def __init__(self, **kwargs):
        """Initialize OpenAI provider."""
        # Get API key from kwargs, settings, or environment
        api_key = (
            kwargs.get("api_key")
            or settings.openai_api_key
            or os.getenv("OPENAI_API_KEY")
        )
        if not api_key:
            raise ValueError("API key required for OpenAI provider")

        kwargs["api_key"] = api_key
        kwargs.setdefault("base_url", settings.openai_base_url)

        # Store model if provided
        self.model = kwargs.pop("model", "gpt-4")

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
                    max_retries=self.max_retries,
                )
            except ImportError:
                raise ProviderError("OpenAI provider requires 'openai' package")
        return self._client

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
        """Get completion from OpenAI."""
        try:
            # Remove model from kwargs to avoid duplication
            kwargs.pop("model", None)

            # Use provided model or default
            actual_model = model or self.model

            # Format messages
            formatted_messages = self._format_messages(messages)

            # Prepare request parameters
            request_params = {
                "model": actual_model,
                "messages": formatted_messages,
                "temperature": temperature,
                **kwargs,
            }

            if max_tokens:
                request_params["max_tokens"] = max_tokens

            # Add tools if provided
            if tools:
                # Handle both ToolDefinition objects and raw dicts
                if tools and isinstance(tools[0], dict):
                    request_params["tools"] = tools
                else:
                    request_params["tools"] = [
                        tool.to_openai_schema() for tool in tools
                    ]
                request_params["tool_choice"] = (
                    tool_choice if tool_choice is not None else "auto"
                )

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
                    "total_tokens": response.usage.total_tokens,
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

                        tool_calls.append(
                            ToolCall(
                                id=str(tc.id), name=tc.function.name, arguments=args
                            )
                        )
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
                model=actual_model,
            )

        except Exception as e:
            raise ProviderError(f"OpenAI completion failed: {e}") from e

    def validate_auth(self) -> None:
        """Validate OpenAI API key."""
        if not self.api_key or not self.api_key.startswith("sk-"):
            raise ProviderAuthError("openai")

    def _format_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
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

    async def stream(
        self,
        messages: list[Message] | list[dict[str, Any]],
        model: str | None = None,
        tools: list[ToolDefinition] | list[dict[str, Any]] | None = None,
        tool_choice: Any | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from OpenAI.

        Args:
            messages: List of messages
            model: Model to use (defaults to instance model)
            tools: Optional tools for the model to use
            tool_choice: How to handle tool selection
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI-specific parameters

        Yields:
            StreamChunk: Individual chunks of the response

        Raises:
            StreamInterruptedError: If the stream is interrupted
            ProviderError: If the provider encounters an error
        """
        try:
            # Remove model from kwargs to avoid duplication
            kwargs.pop("model", None)

            # Use provided model or default
            actual_model = model or self.model

            # Format messages
            formatted_messages = self._format_messages(messages)

            # Prepare request parameters
            request_params = {
                "model": actual_model,
                "messages": formatted_messages,
                "temperature": temperature,
                "stream": True,  # Enable streaming
                **kwargs,
            }

            if max_tokens:
                request_params["max_tokens"] = max_tokens

            # Add tools if provided
            if tools:
                # Handle both ToolDefinition objects and raw dicts
                if tools and isinstance(tools[0], dict):
                    request_params["tools"] = tools
                else:
                    request_params["tools"] = [
                        tool.to_openai_schema() for tool in tools
                    ]
                request_params["tool_choice"] = (
                    tool_choice if tool_choice is not None else "auto"
                )

            # Make streaming request
            stream = await self.client.chat.completions.create(**request_params)

            # Process stream
            accumulated_content = ""
            accumulated_tool_calls = {}

            try:
                async for chunk in stream:
                    if not chunk.choices:
                        continue

                    choice = chunk.choices[0]

                    # Handle content chunks
                    if choice.delta and choice.delta.content:
                        content = choice.delta.content
                        accumulated_content += content

                        yield StreamChunk(
                            content=content,
                            token=content,  # For OpenAI, content is the token
                            metadata={"model": actual_model, "index": choice.index},
                        )

                    # Handle tool call chunks
                    if hasattr(choice.delta, "tool_calls") and choice.delta.tool_calls:
                        for tc in choice.delta.tool_calls:
                            # Skip if no ID
                            if not hasattr(tc, "id") or tc.id is None:
                                continue

                            if tc.id not in accumulated_tool_calls:
                                accumulated_tool_calls[tc.id] = {
                                    "id": tc.id,
                                    "name": (
                                        tc.function.name
                                        if hasattr(tc, "function")
                                        and tc.function
                                        and hasattr(tc.function, "name")
                                        else ""
                                    ),
                                    "arguments": "",
                                }

                            if (
                                hasattr(tc, "function")
                                and tc.function
                                and hasattr(tc.function, "arguments")
                                and tc.function.arguments
                            ):
                                accumulated_tool_calls[tc.id][
                                    "arguments"
                                ] += tc.function.arguments

                    # Check if this is the final chunk
                    if choice.finish_reason:
                        # Parse accumulated tool calls
                        tool_calls = []
                        for tc_data in accumulated_tool_calls.values():
                            try:
                                # Skip if missing required fields
                                if not tc_data.get("id") or not tc_data.get("name"):
                                    continue

                                args = (
                                    json.loads(tc_data["arguments"])
                                    if tc_data["arguments"]
                                    else {}
                                )
                                tool_calls.append(
                                    ToolCall(
                                        id=tc_data["id"],
                                        name=tc_data["name"],
                                        arguments=args,
                                    )
                                )
                            except json.JSONDecodeError:
                                logger.warning(
                                    f"Failed to parse tool arguments for {tc_data.get('name', 'unknown')}"
                                )

                        # Yield final chunk with metadata
                        yield StreamChunk(
                            content="",
                            is_final=True,
                            metadata={
                                "model": actual_model,
                                "finish_reason": choice.finish_reason,
                                "tool_calls": (
                                    [tc.model_dump() for tc in tool_calls]
                                    if tool_calls
                                    else None
                                ),
                                "total_content": accumulated_content,
                            },
                        )

            except asyncio.CancelledError:
                raise StreamInterruptedError(
                    "OpenAI stream was interrupted",
                    partial_response=accumulated_content,
                )

        except Exception as e:
            if isinstance(e, StreamInterruptedError):
                raise
            raise ProviderError(f"OpenAI streaming failed: {e}") from e

    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming.

        Returns:
            bool: True (OpenAI supports streaming)
        """
        return True
