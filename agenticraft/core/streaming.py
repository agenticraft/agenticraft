"""Streaming response support for AgentiCraft.

This module provides streaming capabilities for all LLM providers,
allowing token-by-token response streaming for better user experience.

Example:
    Basic streaming usage::

        from agenticraft import Agent

        agent = Agent(name="StreamBot")

        async for chunk in agent.stream("Tell me a story"):
            print(chunk.content, end="", flush=True)
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .exceptions import AgentError


@dataclass
class StreamChunk:
    """A single chunk in a streaming response.

    Attributes:
        content: The text content of this chunk
        token: Optional individual token (if available)
        metadata: Additional metadata about the chunk
        is_final: Whether this is the final chunk
        timestamp: When this chunk was created
    """

    content: str
    token: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_final: bool = False
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        """String representation returns the content."""
        return self.content


@dataclass
class StreamingResponse:
    """Container for a complete streaming response with metadata.

    This class accumulates chunks and provides access to the complete
    response once streaming is finished.

    Attributes:
        chunks: List of all chunks received
        complete_text: The accumulated complete text
        metadata: Response metadata
        start_time: When streaming started
        end_time: When streaming ended
        total_tokens: Total number of tokens (if available)
    """

    chunks: list[StreamChunk] = field(default_factory=list)
    complete_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    total_tokens: int | None = None
    stream_id: str = field(default_factory=lambda: str(uuid4()))

    def add_chunk(self, chunk: StreamChunk) -> None:
        """Add a chunk to the response.

        Args:
            chunk: The chunk to add
        """
        self.chunks.append(chunk)
        if chunk.content:
            self.complete_text += chunk.content

        if chunk.is_final:
            self.end_time = time.time()
            if "total_tokens" in chunk.metadata:
                self.total_tokens = chunk.metadata["total_tokens"]

    @property
    def duration(self) -> float | None:
        """Get the total streaming duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def chunk_count(self) -> int:
        """Get the total number of chunks."""
        return len(self.chunks)

    def __str__(self) -> str:
        """String representation returns the complete text."""
        return self.complete_text


class StreamingProvider(ABC):
    """Base interface for streaming-capable providers.

    All LLM providers that support streaming should implement this interface.
    """

    @abstractmethod
    async def stream(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        """Stream responses token by token.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional provider-specific parameters

        Yields:
            StreamChunk: Individual chunks of the response

        Raises:
            StreamInterruptedError: If the stream is interrupted
            ProviderError: If the provider encounters an error
        """
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming.

        Returns:
            bool: True if streaming is supported
        """
        pass


class StreamInterruptedError(AgentError):
    """Raised when a stream is interrupted before completion."""

    def __init__(
        self,
        message: str = "Stream was interrupted",
        partial_response: str | None = None,
    ):
        super().__init__(message)
        self.partial_response = partial_response


class StreamingManager:
    """Manages streaming operations with interruption handling.

    This class provides utilities for managing streaming operations,
    including timeout handling, interruption, and progress tracking.
    """

    def __init__(self, timeout: float | None = None):
        """Initialize the streaming manager.

        Args:
            timeout: Optional timeout in seconds for streaming operations
        """
        self.timeout = timeout
        self._active_streams: dict[str, asyncio.Task] = {}

    async def stream_with_timeout(
        self, stream_coro: AsyncIterator[StreamChunk], timeout: float | None = None
    ) -> AsyncIterator[StreamChunk]:
        """Stream with timeout protection.

        Args:
            stream_coro: The streaming coroutine
            timeout: Timeout in seconds (uses default if not specified)

        Yields:
            StreamChunk: Individual chunks

        Raises:
            asyncio.TimeoutError: If timeout is exceeded
        """
        timeout = timeout or self.timeout

        if timeout:
            try:
                async with asyncio.timeout(timeout):
                    async for chunk in stream_coro:
                        yield chunk
            except asyncio.TimeoutError:
                raise StreamInterruptedError(f"Stream timeout after {timeout} seconds")
        else:
            async for chunk in stream_coro:
                yield chunk

    def interrupt_stream(self, stream_id: str) -> bool:
        """Interrupt an active stream.

        Args:
            stream_id: The ID of the stream to interrupt

        Returns:
            bool: True if stream was interrupted, False if not found
        """
        if stream_id in self._active_streams:
            task = self._active_streams[stream_id]
            task.cancel()
            return True
        return False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cancel all active streams."""
        for task in self._active_streams.values():
            if not task.done():
                task.cancel()
        self._active_streams.clear()


# Utility functions for working with streams


async def collect_stream(stream: AsyncIterator[StreamChunk]) -> StreamingResponse:
    """Collect a complete stream into a StreamingResponse.

    Args:
        stream: The stream to collect

    Returns:
        StreamingResponse: The complete response
    """
    response = StreamingResponse()

    async for chunk in stream:
        response.add_chunk(chunk)

    return response


async def stream_to_string(stream: AsyncIterator[StreamChunk]) -> str:
    """Convert a stream directly to a string.

    Args:
        stream: The stream to convert

    Returns:
        str: The complete text from the stream
    """
    text = ""
    async for chunk in stream:
        text += chunk.content
    return text


def create_mock_stream(
    text: str, chunk_size: int = 10, delay: float = 0.1
) -> AsyncIterator[StreamChunk]:
    """Create a mock stream for testing.

    Args:
        text: The text to stream
        chunk_size: Size of each chunk
        delay: Delay between chunks in seconds

    Returns:
        AsyncIterator[StreamChunk]: Mock stream
    """

    async def _stream():
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i : i + chunk_size]
            is_final = i + chunk_size >= len(text)

            yield StreamChunk(
                content=chunk_text,
                is_final=is_final,
                metadata={"chunk_index": i // chunk_size},
            )

            if not is_final:
                await asyncio.sleep(delay)

    return _stream()
