# Streaming API Reference

## Module: `agenticraft.core.streaming`

The streaming module provides real-time, token-by-token response generation capabilities for AgentiCraft agents.

### Classes

#### `StreamChunk`

A single chunk in a streaming response.

```python
@dataclass
class StreamChunk:
    content: str
    token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_final: bool = False
    timestamp: float = field(default_factory=time.time)
```

**Attributes:**

- `content` (str): The text content of this chunk
- `token` (Optional[str]): Individual token if available (provider-specific)
- `metadata` (Dict[str, Any]): Additional metadata about the chunk
  - OpenAI: May include `usage`, `finish_reason`
  - Anthropic: May include `event_type`, `index`
  - Ollama: May include `model`, `eval_duration`
- `is_final` (bool): Whether this is the final chunk in the stream
- `timestamp` (float): Unix timestamp when the chunk was created

**Methods:**

- `__str__() -> str`: Returns the content string

**Example:**

```python
chunk = StreamChunk(
    content="Hello",
    metadata={"model": "gpt-4"},
    is_final=False
)
print(chunk)  # Output: Hello
```

---

#### `StreamingResponse`

Container for accumulating a complete streaming response.

```python
@dataclass
class StreamingResponse:
    chunks: List[StreamChunk] = field(default_factory=list)
    complete_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_tokens: Optional[int] = None
    stream_id: str = field(default_factory=lambda: str(uuid4()))
```

**Attributes:**

- `chunks` (List[StreamChunk]): List of all chunks received
- `complete_text` (str): The accumulated complete text
- `metadata` (Dict[str, Any]): Response-level metadata
- `start_time` (float): When streaming started (Unix timestamp)
- `end_time` (Optional[float]): When streaming ended
- `total_tokens` (Optional[int]): Total token count if available
- `stream_id` (str): Unique identifier for this stream

**Properties:**

- `duration` (Optional[float]): Total streaming duration in seconds
- `chunk_count` (int): Total number of chunks received

**Methods:**

- `add_chunk(chunk: StreamChunk) -> None`: Add a chunk to the response
- `__str__() -> str`: Returns the complete text

**Example:**

```python
response = StreamingResponse()
async for chunk in agent.stream("Hello"):
    response.add_chunk(chunk)

print(f"Complete text: {response.complete_text}")
print(f"Duration: {response.duration:.2f}s")
print(f"Chunks: {response.chunk_count}")
```

---

#### `StreamingProvider`

Abstract base class for streaming-capable providers.

```python
class StreamingProvider(ABC):
    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        """Stream responses token by token."""
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming."""
        pass
```

**Methods:**

- `stream(messages, **kwargs)`: Async iterator yielding StreamChunk objects
- `supports_streaming()`: Returns True if provider supports streaming

**Implementation Example:**

```python
class MyProvider(StreamingProvider):
    async def stream(self, messages, **kwargs):
        # Implementation specific to provider
        for token in self._generate_tokens(messages):
            yield StreamChunk(content=token)
    
    def supports_streaming(self):
        return True
```

---

#### `StreamInterruptedError`

Exception raised when a stream is interrupted before completion.

```python
class StreamInterruptedError(AgentError):
    def __init__(
        self, 
        message: str = "Stream was interrupted", 
        partial_response: Optional[str] = None
    ):
        super().__init__(message)
        self.partial_response = partial_response
```

**Attributes:**

- `message` (str): Error message
- `partial_response` (Optional[str]): Any partial response received before interruption

**Example:**

```python
try:
    async for chunk in agent.stream(prompt):
        if should_stop():
            raise StreamInterruptedError(
                "User cancelled", 
                partial_response=collected_text
            )
except StreamInterruptedError as e:
    print(f"Interrupted: {e}")
    print(f"Partial: {e.partial_response}")
```

---

#### `StreamingManager`

Manages streaming operations with timeout and interruption handling.

```python
class StreamingManager:
    def __init__(self, timeout: Optional[float] = None):
        """Initialize with optional timeout in seconds."""
```

**Methods:**

- `stream_with_timeout(stream_coro, timeout=None)`: Stream with timeout protection
- `interrupt_stream(stream_id: str) -> bool`: Interrupt an active stream

**Context Manager:**

```python
async with StreamingManager(timeout=30) as manager:
    async for chunk in manager.stream_with_timeout(
        agent.stream(prompt)
    ):
        process_chunk(chunk)
```

---

### Functions

#### `collect_stream`

Collect a complete stream into a StreamingResponse.

```python
async def collect_stream(
    stream: AsyncIterator[StreamChunk]
) -> StreamingResponse:
    """Collect a complete stream into a StreamingResponse."""
```

**Example:**

```python
response = await collect_stream(agent.stream("Hello"))
print(f"Complete: {response.complete_text}")
```

---

#### `stream_to_string`

Convert a stream directly to a string.

```python
async def stream_to_string(
    stream: AsyncIterator[StreamChunk]
) -> str:
    """Convert a stream directly to a string."""
```

**Example:**

```python
text = await stream_to_string(agent.stream("Hello"))
print(text)
```

---

#### `create_mock_stream`

Create a mock stream for testing.

```python
def create_mock_stream(
    text: str, 
    chunk_size: int = 10, 
    delay: float = 0.1
) -> AsyncIterator[StreamChunk]:
    """Create a mock stream for testing."""
```

**Parameters:**

- `text` (str): The text to stream
- `chunk_size` (int): Size of each chunk in characters
- `delay` (float): Delay between chunks in seconds

**Example:**

```python
mock_stream = create_mock_stream(
    "Hello, world!", 
    chunk_size=2, 
    delay=0.05
)

async for chunk in mock_stream:
    print(chunk.content, end="")  # Output: He ll o,  w or ld !
```

---

### Agent Integration

The `Agent` class provides the `stream()` method for streaming responses:

```python
class Agent:
    async def stream(
        self,
        prompt: str,
        *,
        messages: Optional[List[Message]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
        tools: Optional[List[Tool]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        """Stream a response from the agent token by token."""
```

**Parameters:**

- `prompt` (str): The input prompt
- `messages` (Optional[List[Message]]): Override conversation history
- `temperature` (Optional[float]): Sampling temperature (0.0-2.0)
- `max_tokens` (Optional[int]): Maximum tokens to generate
- `top_p` (Optional[float]): Nucleus sampling parameter
- `frequency_penalty` (Optional[float]): Frequency penalty (-2.0 to 2.0)
- `presence_penalty` (Optional[float]): Presence penalty (-2.0 to 2.0)
- `stop` (Optional[List[str]]): Stop sequences
- `tools` (Optional[List[Tool]]): Override agent tools
- `tool_choice` (Optional[Union[str, Dict]]): Tool selection strategy
- `response_format` (Optional[Dict]): Response format constraints
- `seed` (Optional[int]): Random seed for deterministic output
- `**kwargs`: Additional provider-specific parameters

**Yields:**

`StreamChunk`: Individual chunks of the response

**Raises:**

- `ProviderError`: If the provider doesn't support streaming
- `StreamInterruptedError`: If the stream is interrupted
- `AgentError`: For other agent-related errors

---

### Provider Implementations

#### OpenAI Streaming

```python
# Internal implementation in providers/openai.py
async def stream(self, messages, **kwargs) -> AsyncIterator[StreamChunk]:
    stream = await self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        stream=True,
        **kwargs
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield StreamChunk(
                content=chunk.choices[0].delta.content,
                metadata={
                    "model": self.model,
                    "finish_reason": chunk.choices[0].finish_reason
                }
            )
```

#### Anthropic Streaming

```python
# Internal implementation in providers/anthropic.py
async def stream(self, messages, **kwargs) -> AsyncIterator[StreamChunk]:
    async with self.client.messages.stream(
        model=self.model,
        messages=messages,
        **kwargs
    ) as stream:
        async for event in stream:
            if event.type == "content_block_delta":
                yield StreamChunk(
                    content=event.delta.text,
                    metadata={"event_type": event.type}
                )
```

#### Ollama Streaming

```python
# Internal implementation in providers/ollama.py
async def stream(self, messages, **kwargs) -> AsyncIterator[StreamChunk]:
    async with self.client.chat(
        model=self.model,
        messages=messages,
        stream=True,
        **kwargs
    ) as response:
        async for line in response:
            if line.get("message", {}).get("content"):
                yield StreamChunk(
                    content=line["message"]["content"],
                    metadata={"model": line.get("model")}
                )
```

---

### Usage Patterns

#### Basic Streaming

```python
async for chunk in agent.stream("Tell me a joke"):
    print(chunk.content, end="", flush=True)
```

#### With Error Handling

```python
try:
    async for chunk in agent.stream(prompt):
        await process_chunk(chunk)
except StreamInterruptedError as e:
    handle_interruption(e.partial_response)
except ProviderError as e:
    handle_provider_error(e)
```

#### Collecting Metrics

```python
response = StreamingResponse()
async for chunk in agent.stream(prompt):
    response.add_chunk(chunk)
    await update_ui(chunk.content)

metrics = {
    "duration": response.duration,
    "chunks": response.chunk_count,
    "tokens": response.total_tokens,
    "chars_per_second": len(response.complete_text) / response.duration
}
```

#### Concurrent Streaming

```python
async def stream_multiple(agent, prompts):
    streams = [
        collect_stream(agent.stream(p)) 
        for p in prompts
    ]
    return await asyncio.gather(*streams)
```

---

### Performance Considerations

1. **Chunk Size**: Providers send chunks of varying sizes. OpenAI typically sends word-level chunks, while Anthropic may send larger phrase-level chunks.

2. **Latency**: First chunk latency varies by provider:
   - OpenAI: 200-500ms
   - Anthropic: 300-700ms
   - Ollama: 50-200ms (local)

3. **Memory**: Streaming uses less memory than full responses, as chunks can be processed and discarded.

4. **Network**: Streaming is more resilient to network issues, as partial responses can be recovered.

---

### Testing

Use the mock stream for testing:

```python
import pytest

async def test_stream_processing():
    mock_stream = create_mock_stream(
        "Test response", 
        chunk_size=4
    )
    
    chunks = []
    async for chunk in mock_stream:
        chunks.append(chunk)
    
    assert len(chunks) == 4
    assert chunks[-1].is_final
```

---

### Best Practices

1. **Always check provider support** before streaming
2. **Handle interruptions gracefully** with try/except
3. **Process chunks immediately** to minimize memory usage
4. **Provide user feedback** during streaming
5. **Set appropriate timeouts** for long-running streams
6. **Test with mock streams** before production

---

### See Also

- [Streaming Guide](../features/streaming.md) - User guide with examples
- [Provider Documentation](../providers/) - Provider-specific details
- [Examples](../../examples/streaming/) - Complete working examples
