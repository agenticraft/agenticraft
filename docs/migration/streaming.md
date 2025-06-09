# Streaming Migration Guide

## Migrating to Streaming in v0.2.0

This guide helps you update your code to use the new streaming capabilities introduced in AgentiCraft v0.2.0.

## What's New

- **Real-time token-by-token output** from all major providers
- **Async-first API** for better performance
- **Provider-agnostic streaming interface**
- **Advanced stream management** with interruption handling

## Basic Migration

### Before (v0.1.x)

```python
from agenticraft import Agent

# Synchronous API
agent = Agent(name="MyAgent", model="gpt-4")
response = agent.run("Tell me a story")
print(response.content)
```

### After (v0.2.0)

```python
from agenticraft import Agent
import asyncio

async def main():
    # Async API with streaming
    agent = Agent(name="MyAgent", model="gpt-4")
    
    # Option 1: Stream response
    async for chunk in agent.stream("Tell me a story"):
        print(chunk.content, end="", flush=True)
    
    # Option 2: Get complete response (async)
    response = await agent.arun("Tell me a story")
    print(response.content)

asyncio.run(main())
```

## Detailed Changes

### 1. Async API

All agent methods are now async:

```python
# Old
response = agent.run(prompt)
messages = agent.get_messages()

# New
response = await agent.arun(prompt)
messages = await agent.get_messages()
```

### 2. Streaming Support

New streaming method available:

```python
# Stream responses
async for chunk in agent.stream(prompt):
    # Process each chunk as it arrives
    print(chunk.content, end="")
```

### 3. Provider Compatibility

Check if your provider supports streaming:

```python
info = agent.get_provider_info()
if info['supports_streaming']:
    # Use streaming
    async for chunk in agent.stream(prompt):
        ...
else:
    # Fall back to regular completion
    response = await agent.arun(prompt)
```

## Common Patterns

### 1. Simple Script Migration

**Before:**
```python
from agenticraft import Agent

agent = Agent()
response = agent.run("Hello")
print(response.content)
```

**After:**
```python
from agenticraft import Agent
import asyncio

async def main():
    agent = Agent()
    
    # With streaming
    async for chunk in agent.stream("Hello"):
        print(chunk.content, end="")

# Run the async function
asyncio.run(main())
```

### 2. Web Application Migration

**Before (Flask):**
```python
from flask import Flask, jsonify
from agenticraft import Agent

app = Flask(__name__)
agent = Agent()

@app.route('/chat', methods=['POST'])
def chat():
    response = agent.run(request.json['prompt'])
    return jsonify({'response': response.content})
```

**After (FastAPI with streaming):**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agenticraft import Agent

app = FastAPI()
agent = Agent()

@app.post('/chat')
async def chat(prompt: str):
    async def generate():
        async for chunk in agent.stream(prompt):
            yield f"data: {chunk.content}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### 3. Error Handling Migration

**Before:**
```python
try:
    response = agent.run(prompt)
except Exception as e:
    print(f"Error: {e}")
```

**After:**
```python
from agenticraft.core.streaming import StreamInterruptedError

try:
    async for chunk in agent.stream(prompt):
        print(chunk.content, end="")
except StreamInterruptedError as e:
    print(f"Stream interrupted: {e}")
    if e.partial_response:
        print(f"Partial: {e.partial_response}")
except Exception as e:
    print(f"Error: {e}")
```

### 4. Progress Tracking Migration

**Before:**
```python
# No built-in progress tracking
response = agent.run(long_prompt)
print("Done!")
```

**After:**
```python
from agenticraft.core.streaming import StreamingResponse

response = StreamingResponse()
print("Generating", end="")

async for chunk in agent.stream(long_prompt):
    response.add_chunk(chunk)
    print(".", end="", flush=True)  # Progress dots

print(f"\nDone! Generated {response.chunk_count} chunks in {response.duration:.2f}s")
```

## Advanced Migration

### 1. Custom Providers

If you've implemented a custom provider:

**Before:**
```python
class MyProvider(BaseProvider):
    def complete(self, messages, **kwargs):
        # Synchronous completion
        return self.api_call(messages)
```

**After:**
```python
from agenticraft.core.streaming import StreamingProvider, StreamChunk

class MyProvider(BaseProvider, StreamingProvider):
    async def complete(self, messages, **kwargs):
        # Async completion
        return await self.api_call(messages)
    
    async def stream(self, messages, **kwargs):
        # Streaming support
        async for token in self.api_stream(messages):
            yield StreamChunk(content=token)
    
    def supports_streaming(self):
        return True
```

### 2. Testing Migration

**Before:**
```python
def test_agent():
    agent = Agent()
    response = agent.run("test")
    assert response.content
```

**After:**
```python
import pytest

@pytest.mark.asyncio
async def test_agent_streaming():
    agent = Agent()
    
    # Test streaming
    chunks = []
    async for chunk in agent.stream("test"):
        chunks.append(chunk)
    
    assert chunks
    assert chunks[-1].is_final

# Or use mock streams for testing
from agenticraft.core.streaming import create_mock_stream

async def test_with_mock():
    mock_stream = create_mock_stream("Test response")
    chunks = [chunk async for chunk in mock_stream]
    assert len(chunks) == 2  # Based on default chunk_size
```

### 3. Tool Integration

Tools work seamlessly with streaming:

**Before:**
```python
agent.register_tool(my_tool)
response = agent.run("Use the tool")
```

**After:**
```python
agent.add_tool(my_tool)

# Tools are called automatically during streaming
async for chunk in agent.stream("Use the tool"):
    print(chunk.content, end="")
```

## Performance Considerations

### Memory Usage

Streaming uses less memory for long responses:

```python
# Old: Entire response in memory
response = agent.run(long_prompt)  # Could be many MB

# New: Process chunks as they arrive
async for chunk in agent.stream(long_prompt):
    await process_and_discard(chunk)  # Constant memory usage
```

### Latency

First token latency is much better with streaming:

```python
# Old: Wait for entire response
start = time.time()
response = agent.run(prompt)  # Wait 5-10 seconds
print(f"Time to first token: {time.time() - start}s")

# New: First token arrives quickly
start = time.time()
async for chunk in agent.stream(prompt):
    if not first_token_time:
        first_token_time = time.time() - start  # Usually <1s
    print(chunk.content, end="")
```

## Compatibility Mode

For gradual migration, you can create a wrapper:

```python
class LegacyAgent:
    """Wrapper for backward compatibility."""
    
    def __init__(self, **kwargs):
        self.agent = Agent(**kwargs)
    
    def run(self, prompt, **kwargs):
        """Synchronous run method."""
        import asyncio
        return asyncio.run(self.agent.arun(prompt, **kwargs))
    
    def stream_sync(self, prompt, **kwargs):
        """Synchronous streaming."""
        import asyncio
        
        async def _stream():
            async for chunk in self.agent.stream(prompt, **kwargs):
                yield chunk
        
        # Use asyncio in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            gen = _stream()
            while True:
                try:
                    chunk = loop.run_until_complete(gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

# Use like old API
legacy_agent = LegacyAgent()
response = legacy_agent.run("Hello")  # Works synchronously
```

## Troubleshooting

### Issue: `RuntimeError: asyncio.run() cannot be called from a running event loop`

**Solution**: You're already in an async context (like Jupyter)

```python
# Instead of asyncio.run(main())
# Use await directly
await main()

# Or create task
import asyncio
task = asyncio.create_task(main())
await task
```

### Issue: Provider doesn't support streaming

**Solution**: Check support and fall back

```python
if agent.get_provider_info()['supports_streaming']:
    async for chunk in agent.stream(prompt):
        print(chunk.content, end="")
else:
    response = await agent.arun(prompt)
    print(response.content)
```

### Issue: Existing code breaks with async

**Solution**: Create async wrappers

```python
# Wrap your main logic
async def async_main():
    agent = Agent()
    async for chunk in agent.stream("Hello"):
        print(chunk.content)

# Run from sync code
if __name__ == "__main__":
    asyncio.run(async_main())
```

## Best Practices

1. **Always use async/await** for agent operations
2. **Check streaming support** before using stream()
3. **Handle interruptions** for better UX
4. **Process chunks immediately** to save memory
5. **Provide progress feedback** to users
6. **Test with mock streams** for faster tests

## Summary

The key changes for streaming in v0.2.0:

- ✅ All methods are now async
- ✅ New `stream()` method for real-time output
- ✅ Provider-agnostic streaming interface
- ✅ Better error handling with StreamInterruptedError
- ✅ Performance improvements with streaming

Update your code to use async/await and enjoy real-time streaming responses!

## Need Help?

- Check the [Streaming Guide](../features/streaming.md)
- See [Examples](../../examples/streaming/)
- Join our [Discord](https://discord.gg/agenticraft) for support
