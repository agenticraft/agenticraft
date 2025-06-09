"""Ollama provider implementation for AgentiCraft.

This provider enables the use of local models through Ollama, supporting
various open-source models like Llama, Mistral, and others.

Example:
    Using Ollama models locally::

        from agenticraft import Agent

        # Use default Ollama model
        agent = Agent(model="ollama/llama2")

        # Use specific model with custom base URL
        agent = Agent(
            model="ollama/codellama",
            base_url="http://localhost:11434"
        )
"""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from ..core.config import settings
from ..core.exceptions import ProviderError
from ..core.provider import BaseProvider
from ..core.streaming import StreamChunk, StreamingProvider, StreamInterruptedError
from ..core.types import CompletionResponse, Message, ToolDefinition


class OllamaProvider(BaseProvider, StreamingProvider):
    """Provider for local Ollama models with streaming support.

    Ollama allows running open-source LLMs locally. This provider
    supports all Ollama features including streaming, custom models,
    and model management.

    Note: Requires Ollama to be installed and running locally.
    See: https://ollama.ai for installation instructions.
    """

    def __init__(self, **kwargs):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name (default: llama2)
            timeout: Request timeout in seconds (default: 300 for long generations)
            **kwargs: Additional provider arguments
        """
        # Set defaults for Ollama
        # Handle None or missing base_url
        if kwargs.get("base_url") is None or "base_url" not in kwargs:
            default_url = "http://localhost:11434"
            if hasattr(settings, "ollama_base_url") and settings.ollama_base_url:
                default_url = settings.ollama_base_url
            kwargs["base_url"] = default_url

        kwargs.setdefault("timeout", 300)  # Ollama can be slow for first run
        kwargs["api_key"] = "ollama"  # Ollama doesn't need API key

        # Extract and store model
        self.model = kwargs.pop("model", "llama2")
        # Handle ollama/ prefix
        if self.model.startswith("ollama/"):
            self.model = self.model[7:]  # Remove 'ollama/' prefix

        super().__init__(**kwargs)

        # Create HTTP client
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

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
        """Get completion from Ollama.

        Args:
            messages: Conversation messages
            model: Optional model override
            tools: Tool definitions (Note: Tool support depends on model)
            tool_choice: Tool choice strategy (if tools supported)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters

        Returns:
            CompletionResponse with generated content

        Raises:
            ProviderError: If Ollama request fails
        """
        try:
            # Use provided model or default
            actual_model = model or self.model
            if actual_model.startswith("ollama/"):
                actual_model = actual_model[7:]

            # Format messages for Ollama
            formatted_messages = self._format_messages(messages)

            # Prepare request body
            request_body = {
                "model": actual_model,
                "messages": formatted_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            # Add max_tokens as num_predict in Ollama
            if max_tokens:
                request_body["options"]["num_predict"] = max_tokens

            # Add any additional options
            for key, value in kwargs.items():
                if key not in ["model", "messages", "stream"]:
                    request_body["options"][key] = value

            # Note: Ollama's tool support is model-dependent
            # For now, we'll include tools in the system prompt if provided
            if tools:
                tool_description = self._format_tools_as_text(tools)
                # Prepend tool description to first user message or add system message
                if formatted_messages and formatted_messages[0]["role"] == "system":
                    formatted_messages[0]["content"] += f"\n\n{tool_description}"
                else:
                    formatted_messages.insert(
                        0, {"role": "system", "content": tool_description}
                    )

            # Make request to Ollama
            response = await self._client.post("/api/chat", json=request_body)
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract message content
            message = data.get("message", {})
            content = message.get("content", "")

            # Calculate token usage (approximate if not provided)
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            usage_data = (
                {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                }
                if (prompt_tokens or completion_tokens)
                else None
            )

            # Extract metadata
            metadata = {
                "model": actual_model,
                "eval_duration": data.get("eval_duration"),
                "load_duration": data.get("load_duration"),
                "total_duration": data.get("total_duration"),
            }

            return CompletionResponse(
                content=content,
                tool_calls=[],  # Ollama doesn't have native tool calling yet
                finish_reason="stop",
                usage=usage_data,
                metadata=metadata,
                model=actual_model,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderError(
                    f"Model '{actual_model}' not found. "
                    f"Try: ollama pull {actual_model}"
                )
            elif e.response.status_code == 500:
                raise ProviderError(
                    "Ollama server error. Is Ollama running? "
                    "Start with: ollama serve"
                )
            else:
                raise ProviderError(f"Ollama HTTP error: {e}")
        except httpx.ConnectError:
            raise ProviderError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start with: ollama serve"
            )
        except Exception as e:
            raise ProviderError(f"Ollama completion failed: {e}") from e

    async def list_models(self) -> list[dict[str, Any]]:
        """List available Ollama models.

        Returns:
            List of model information dictionaries

        Raises:
            ProviderError: If request fails
        """
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            raise ProviderError(f"Failed to list Ollama models: {e}") from e

    async def pull_model(self, model_name: str) -> None:
        """Pull (download) a model from Ollama registry.

        Args:
            model_name: Name of model to pull (e.g., "llama2", "codellama")

        Raises:
            ProviderError: If pull fails
        """
        try:
            response = await self._client.post(
                "/api/pull",
                json={"name": model_name},
                timeout=None,  # Pulling can take a long time
            )
            response.raise_for_status()
        except Exception as e:
            raise ProviderError(f"Failed to pull model '{model_name}': {e}") from e

    def validate_auth(self) -> None:
        """Validate connection to Ollama.

        Ollama doesn't require authentication, but we check
        if the server is accessible.
        """
        # Check connection in a synchronous context
        try:
            import httpx

            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except httpx.ConnectError:
            raise ProviderError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start with: ollama serve"
            )
        except Exception as e:
            raise ProviderError(f"Ollama validation failed: {e}")

    def _format_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Format messages for Ollama API.

        Args:
            messages: List of Message objects or message dicts

        Returns:
            List of message dictionaries for Ollama
        """
        formatted = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted.append({"role": str(msg.role), "content": msg.content})
            elif isinstance(msg, dict):
                # Ensure role is lowercase for Ollama
                formatted.append(
                    {"role": msg["role"].lower(), "content": msg["content"]}
                )
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        return formatted

    def _format_tools_as_text(
        self, tools: list[ToolDefinition] | list[dict[str, Any]]
    ) -> str:
        """Format tools as text description for models without native tool support.

        Args:
            tools: List of tool definitions

        Returns:
            Text description of available tools
        """
        tool_descriptions = ["Available tools:"]

        for tool in tools:
            if isinstance(tool, ToolDefinition):
                name = tool.name
                description = tool.description
                params = tool.parameters
            elif isinstance(tool, dict) and "function" in tool:
                # OpenAI format
                func = tool["function"]
                name = func["name"]
                description = func.get("description", "")
                params = func.get("parameters", {}).get("properties", {})
            else:
                continue

            tool_descriptions.append(f"\n- {name}: {description}")
            if params:
                tool_descriptions.append(f"  Parameters: {params}")

        tool_descriptions.append(
            "\nTo use a tool, respond with: "
            'TOOL_CALL: {"name": "tool_name", "arguments": {...}}'
        )

        return "\n".join(tool_descriptions)

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
        """Stream completion from Ollama.

        Args:
            messages: List of messages
            model: Model to use (defaults to instance model)
            tools: Optional tools (included in prompt)
            tool_choice: Tool choice strategy (not used)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters

        Yields:
            StreamChunk: Individual chunks of the response

        Raises:
            StreamInterruptedError: If the stream is interrupted
            ProviderError: If the provider encounters an error
        """
        try:
            # Use provided model or default
            actual_model = model or self.model
            if actual_model.startswith("ollama/"):
                actual_model = actual_model[7:]

            # Format messages for Ollama
            formatted_messages = self._format_messages(messages)

            # Prepare request body
            request_body = {
                "model": actual_model,
                "messages": formatted_messages,
                "stream": True,  # Enable streaming
                "options": {
                    "temperature": temperature,
                },
            }

            # Add max_tokens as num_predict in Ollama
            if max_tokens:
                request_body["options"]["num_predict"] = max_tokens

            # Add any additional options
            for key, value in kwargs.items():
                if key not in ["model", "messages", "stream"]:
                    request_body["options"][key] = value

            # Include tools in system prompt if provided
            if tools:
                tool_description = self._format_tools_as_text(tools)
                if formatted_messages and formatted_messages[0]["role"] == "system":
                    formatted_messages[0]["content"] += f"\n\n{tool_description}"
                else:
                    formatted_messages.insert(
                        0, {"role": "system", "content": tool_description}
                    )

            # Make streaming request
            accumulated_content = ""

            try:
                async with self._client.stream(
                    "POST", "/api/chat", json=request_body
                ) as response:
                    response.raise_for_status()

                    # Process stream
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        try:
                            # Parse JSON response
                            data = json.loads(line)

                            # Extract message content
                            message = data.get("message", {})
                            content = message.get("content", "")

                            if content:
                                accumulated_content += content

                                # Yield content chunk
                                yield StreamChunk(
                                    content=content,
                                    token=content,
                                    metadata={
                                        "model": actual_model,
                                        "eval_count": data.get("eval_count"),
                                    },
                                )

                            # Check if this is the final message
                            if data.get("done", False):
                                # Extract final metadata
                                metadata = {
                                    "model": actual_model,
                                    "total_duration": data.get("total_duration"),
                                    "load_duration": data.get("load_duration"),
                                    "eval_duration": data.get("eval_duration"),
                                    "eval_count": data.get("eval_count"),
                                    "prompt_eval_count": data.get("prompt_eval_count"),
                                    "total_content": accumulated_content,
                                }

                                # Yield final chunk
                                yield StreamChunk(
                                    content="", is_final=True, metadata=metadata
                                )
                                break

                        except json.JSONDecodeError:
                            # Skip malformed JSON lines
                            continue

            except asyncio.CancelledError:
                raise StreamInterruptedError(
                    "Ollama stream was interrupted",
                    partial_response=accumulated_content,
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ProviderError(
                        f"Model '{actual_model}' not found. "
                        f"Try: ollama pull {actual_model}"
                    )
                else:
                    raise ProviderError(f"Ollama streaming error: {e}")
            except httpx.ConnectError:
                raise ProviderError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Is Ollama running? Start with: ollama serve"
                )

        except Exception as e:
            if isinstance(e, (StreamInterruptedError, ProviderError)):
                raise
            raise ProviderError(f"Ollama streaming failed: {e}") from e

    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming.

        Returns:
            bool: True (Ollama supports streaming)
        """
        return True

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client."""
        await self._client.aclose()
