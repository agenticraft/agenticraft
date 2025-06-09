# Streaming Quick Reference

## Basic Streaming

```python
from agenticraft import Agent
import asyncio

async def main():
    agent = Agent(name="StreamBot", model="gpt-4o-mini")
    
    # Stream response
    async for chunk in agent.stream("Tell me a joke"):
        print(chunk.content, end="", flush=True)

asyncio.run(main())
```

## Check Provider Support

```python
info = agent.get_provider_info()
if info['supports_streaming']:
    # Provider supports streaming
    async for chunk in agent.stream(prompt):
        ...
else:
    # Fall back to regular completion
    response = await agent.arun(prompt)
```

## Collect Complete Response

```python
from agenticraft.core.streaming import StreamingResponse

response = StreamingResponse()
async for chunk in agent.stream("List 3 facts"):
    response.add_chunk(chunk)

print(f"Complete: {response.complete_text}")
print(f"Duration: {response.duration:.2f}s")
print(f"Chunks: {response.chunk_count}")
```

## Error Handling

```python
from agenticraft.core.streaming import StreamInterruptedError

try:
    async for chunk in agent.stream(prompt):
        print(chunk.content, end="")
except StreamInterruptedError as e:
    print(f"Interrupted: {e}")
    if e.partial_response:
        print(f"Partial: {e.partial_response}")
```

## Progress Tracking

```python
chunk_count = 0
async for chunk in agent.stream(prompt):
    chunk_count += 1
    print(f"\r[Chunk {chunk_count}] {chunk.content}", end="")
```

## Streaming with Parameters

```python
async for chunk in agent.stream(
    "Write a haiku",
    temperature=0.9,
    max_tokens=50
):
    print(chunk.content, end="")
```

## Provider-Specific Features

### OpenAI
```python
# Supports: GPT-4, GPT-3.5-turbo
# Features: Token usage, function calling during stream
async for chunk in agent.stream(prompt):
    if chunk.metadata.get('usage'):
        print(f"Tokens: {chunk.metadata['usage']}")
```

### Anthropic
```python
# Supports: Claude 3.5, Claude 3, Claude 2.1
# Features: Event-based streaming, thinking traces
agent = Agent(provider="anthropic", model="claude-3-5-sonnet-latest")
async for chunk in agent.stream(prompt):
    if chunk.metadata.get('event_type') == 'content_block_delta':
        print(chunk.content, end="")
```

### Ollama
```python
# Supports: All Ollama models
# Features: Low latency, local inference
agent = Agent(provider="ollama", model="llama3.2")
async for chunk in agent.stream(prompt):
    print(chunk.content, end="")
```

## Web Application (FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/stream")
async def stream_endpoint(prompt: str):
    agent = Agent()
    
    async def generate():
        async for chunk in agent.stream(prompt):
            yield f"data: {chunk.content}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

## Testing with Mock Streams

```python
from agenticraft.core.streaming import create_mock_stream

# Create mock stream for testing
mock = create_mock_stream(
    "Test response text",
    chunk_size=5,
    delay=0.1
)

async for chunk in mock:
    print(chunk.content)  # "Test ", "respo", "nse t", "ext"
```

## Common Patterns

### Timeout Protection
```python
from agenticraft.core.streaming import StreamingManager

async with StreamingManager(timeout=30) as manager:
    async for chunk in manager.stream_with_timeout(agent.stream(prompt)):
        print(chunk.content, end="")
```

### Concurrent Streams
```python
async def multi_stream(prompts):
    tasks = []
    for prompt in prompts:
        task = collect_stream(agent.stream(prompt))
        tasks.append(task)
    
    return await asyncio.gather(*tasks)
```

### Memory-Efficient Processing
```python
word_count = 0
async for chunk in agent.stream(long_prompt):
    words = chunk.content.split()
    word_count += len(words)
    # Process and discard chunk
print(f"Total words: {word_count}")
```

## Key Classes

- `StreamChunk`: Individual chunk with content and metadata
- `StreamingResponse`: Accumulates chunks into complete response  
- `StreamInterruptedError`: Raised when stream is interrupted
- `StreamingManager`: Manages streams with timeout/interruption

## Best Practices

1. ✅ Always check `supports_streaming` before using
2. ✅ Handle `StreamInterruptedError` for robustness
3. ✅ Process chunks immediately to save memory
4. ✅ Provide visual feedback during streaming
5. ✅ Use mock streams for testing
6. ✅ Set appropriate timeouts for production

## Performance Metrics

- **First chunk latency**: <100ms target achieved
- **OpenAI**: 200-500ms typical
- **Anthropic**: 300-700ms typical  
- **Ollama**: 50-200ms (local)
- **Memory usage**: Constant regardless of response size

## See Also

- [Full Streaming Guide](../features/streaming.md)
- [API Reference](../api/streaming.md)
- [Migration Guide](../migration/streaming.md)
- [Examples](../../examples/streaming/)
