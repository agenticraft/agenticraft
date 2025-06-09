# Streaming Responses Guide

## Overview

AgentiCraft v0.2.0 introduces streaming responses, allowing you to receive AI responses token-by-token in real-time. This provides a more responsive user experience, especially for long-form content generation.

## Features

- **Real-time Output**: See responses as they're generated
- **Provider Support**: Works with OpenAI, Anthropic, and Ollama
- **Error Handling**: Graceful handling of stream interruptions
- **Performance Metrics**: Track streaming duration and chunk counts
- **Tool Integration**: Seamlessly works with tools during streaming

## Quick Start

```python
from agenticraft import Agent
import asyncio

async def main():
    agent = Agent(
        name="StreamingAgent",
        model="gpt-4o-mini"
    )
    
    # Stream a response
    async for chunk in agent.stream("Tell me a story"):
        print(chunk.content, end="", flush=True)

asyncio.run(main())
```

## Basic Usage

### Simple Streaming

The most basic use case is streaming text responses:

```python
async for chunk in agent.stream("Explain quantum computing"):
    print(chunk.content, end="", flush=True)
```

### Collecting Complete Response

You can collect the entire streamed response:

```python
from agenticraft.core.streaming import StreamingResponse

response = StreamingResponse()
async for chunk in agent.stream("List the planets"):
    response.add_chunk(chunk)
    print(".", end="", flush=True)  # Progress indicator

print(f"\nComplete response: {response.complete_text}")
print(f"Duration: {response.duration:.2f} seconds")
print(f"Chunks received: {response.chunk_count}")
```

### Checking Provider Support

Not all providers support streaming. Always check first:

```python
info = agent.get_provider_info()
if info['supports_streaming']:
    async for chunk in agent.stream(prompt):
        # Process chunks
else:
    # Fall back to regular completion
    response = await agent.arun(prompt)
```

## Advanced Usage

### Stream Interruption

Handle stream interruptions gracefully:

```python
from agenticraft.core.streaming import StreamInterruptedError

try:
    char_count = 0
    async for chunk in agent.stream("Write a long essay"):
        print(chunk.content, end="", flush=True)
        char_count += len(chunk.content)
        
        # Interrupt after 100 characters
        if char_count > 100:
            break
            
except StreamInterruptedError as e:
    print(f"Stream interrupted: {e}")
    if e.partial_response:
        print(f"Partial response: {e.partial_response}")
```

### Streaming with Parameters

Pass additional parameters to control generation:

```python
async for chunk in agent.stream(
    "Write a creative story",
    temperature=0.9,
    max_tokens=500,
    top_p=0.95
):
    print(chunk.content, end="", flush=True)
```

### Progress Tracking

Track streaming progress in real-time:

```python
import time

start_time = time.time()
token_count = 0

async for chunk in agent.stream("Explain machine learning"):
    print(chunk.content, end="", flush=True)
    token_count += len(chunk.content.split())
    
    # Show progress
    elapsed = time.time() - start_time
    tokens_per_second = token_count / elapsed if elapsed > 0 else 0
    print(f"\r[{token_count} tokens, {tokens_per_second:.1f} tok/s]", 
          end="", flush=True)
```

### Streaming with Tools

**Important**: When using tools with WorkflowAgent and streaming, you must use the handler pattern instead of the `@tool` decorator for reliable operation.

#### The Handler Pattern (Recommended)

The proper way to integrate tools with streaming in WorkflowAgent:

```python
from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.core.streaming import create_mock_stream

# 1. Define tool as regular function (no @tool decorator)
def calculate(expression: str) -> float:
    """Calculate a mathematical expression."""
    result = eval(expression, {"__builtins__": {}}, {})
    return float(result)

# 2. Create streaming handler
async def calc_handler(agent, step, context):
    """Handler that performs calculation with streaming."""
    params = context.get("calc_params", {})
    
    # Stream status
    async for chunk in create_mock_stream(f"Calculating {params}...\n", chunk_size=5):
        print(chunk.content, end="", flush=True)
    
    # Execute tool
    result = calculate(**params)
    context["calc_result"] = result
    
    # Stream result
    async for chunk in create_mock_stream(f"Result: {result}\n", chunk_size=5):
        print(chunk.content, end="", flush=True)
    
    return str(result)

# 3. Register handler with workflow
agent = WorkflowAgent(name="Calculator")
agent.register_handler("calculate", calc_handler)

workflow = agent.create_workflow("math_workflow")
workflow.add_step(
    name="calculate",
    handler="calculate",
    action="Performing calculation..."
)

context = {"calc_params": {"expression": "15 * 2500 / 100"}}
result = await agent.execute_workflow(workflow, context=context)
```

#### Tool Wrapper Pattern

For reusable tool integration, use a wrapper class:

```python
class StreamingToolWrapper:
    """Wrapper to make tools work with WorkflowAgent."""
    
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func
    
    def create_streaming_handler(self, step_name: str):
        """Create a streaming handler for workflow steps."""
        async def handler(agent, step, context):
            # Get parameters from context
            params = context.get(f"{step_name}_params", {})
            
            # Stream execution status
            async for chunk in create_mock_stream(f"Executing {self.name}...\n"):
                print(chunk.content, end="", flush=True)
            
            # Execute tool
            result = await self.execute(**params)
            
            # Store result in context
            context[f"{step_name}_result"] = result
            
            return str(result)
        
        return handler
    
    async def execute(self, *args, **kwargs):
        """Execute the wrapped function."""
        return self.func(*args, **kwargs)
```

#### Why the Handler Pattern?

1. **Reliability**: The `@tool` decorator can cause message structure errors with streaming APIs
2. **Control**: Full control over streaming behavior and data flow
3. **Context**: Natural integration with workflow context for data passing
4. **Testing**: Easier to test and mock

#### Basic Agent Tool Streaming

For simple agents (not WorkflowAgent), standard tool usage works:

```python
from agenticraft.tools import calculator_tool

agent = Agent()
agent.add_tool(calculator_tool)

# Note: This may have limitations with some providers
async for chunk in agent.stream("What's 15% of $2,500?"):
    print(chunk.content, end="", flush=True)
```

## Provider-Specific Features

### OpenAI

OpenAI streaming includes token usage metadata:

```python
async for chunk in agent.stream("Hello"):
    if chunk.metadata.get('usage'):
        print(f"Tokens used: {chunk.metadata['usage']}")
```

**Supported Models**:
- GPT-4 (all variants)
- GPT-3.5-turbo (all variants)

**Special Features**:
- Function calling during streaming
- Token usage tracking
- Stop reason in final chunk

### Anthropic

Anthropic uses event-based streaming:

```python
agent = Agent(provider="anthropic", model="claude-3-5-sonnet-latest")

async for chunk in agent.stream("Explain DNA"):
    # Anthropic includes thinking traces in metadata
    if chunk.metadata.get('event_type') == 'content_block_delta':
        print(chunk.content, end="", flush=True)
```

**Supported Models**:
- Claude 3.5 (Sonnet, Opus)
- Claude 3 (all variants)
- Claude 2.1

**Special Features**:
- Event-based streaming
- Thinking trace visibility
- Message stop sequences

### Ollama

Ollama provides efficient local model streaming:

```python
agent = Agent(provider="ollama", model="llama3.2")

async for chunk in agent.stream("Hello world"):
    # Ollama streams are typically faster with lower latency
    print(chunk.content, end="", flush=True)
```

**Supported Models**:
- All Ollama models
- Custom local models

**Special Features**:
- Low latency (local inference)
- Custom model parameters
- GPU acceleration info

## Error Handling

### Common Errors

```python
from agenticraft.core.streaming import StreamInterruptedError
from agenticraft.core.exceptions import ProviderError

try:
    async for chunk in agent.stream(prompt):
        process_chunk(chunk)
        
except StreamInterruptedError as e:
    # Handle interrupted streams
    print(f"Stream interrupted: {e}")
    
except ProviderError as e:
    # Handle provider errors
    print(f"Provider error: {e}")
    
except asyncio.TimeoutError:
    # Handle timeouts
    print("Stream timed out")
```

### Retry Logic

Implement retry logic for resilient streaming:

```python
async def stream_with_retry(agent, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            async for chunk in agent.stream(prompt):
                yield chunk
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retry {attempt + 1}/{max_retries}")
            await asyncio.sleep(1)
```

## Performance Optimization

### 1. Chunk Processing

Process chunks efficiently without blocking:

```python
async def process_stream(agent, prompt):
    buffer = []
    async for chunk in agent.stream(prompt):
        buffer.append(chunk.content)
        
        # Process in batches
        if len(buffer) >= 10:
            await process_batch(buffer)
            buffer.clear()
    
    # Process remaining
    if buffer:
        await process_batch(buffer)
```

### 2. Concurrent Streams

Handle multiple streams concurrently:

```python
async def multi_stream(agent, prompts):
    tasks = []
    for prompt in prompts:
        task = asyncio.create_task(
            collect_stream(agent.stream(prompt))
        )
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    return responses
```

### 3. Memory Efficiency

For long streams, process chunks without storing all:

```python
async def process_large_stream(agent, prompt):
    word_count = 0
    async for chunk in agent.stream(prompt):
        # Process chunk immediately
        word_count += len(chunk.content.split())
        
        # Don't store chunks in memory
        await send_to_user(chunk.content)
    
    return word_count
```

## Best Practices

### 1. Always Check Support

```python
if agent.get_provider_info()['supports_streaming']:
    # Use streaming
    async for chunk in agent.stream(prompt):
        ...
else:
    # Fall back to regular completion
    response = await agent.arun(prompt)
```

### 2. Handle Interruptions Gracefully

```python
partial_response = ""
try:
    async for chunk in agent.stream(prompt):
        partial_response += chunk.content
        if should_stop():
            break
except StreamInterruptedError:
    # Use partial_response if needed
    pass
```

### 3. Provide User Feedback

```python
print("Generating response", end="", flush=True)
async for chunk in agent.stream(prompt):
    print(".", end="", flush=True)  # Progress dots
    # Or update a progress bar
```

### 4. Set Appropriate Timeouts

```python
from agenticraft.core.streaming import StreamingManager

manager = StreamingManager(timeout=30.0)
async for chunk in manager.stream_with_timeout(
    agent.stream(prompt)
):
    process_chunk(chunk)
```

## Integration Examples

### Web Application (FastAPI)

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

### CLI Application

```python
import click

@click.command()
@click.argument('prompt')
def stream_cli(prompt):
    async def run():
        agent = Agent()
        async for chunk in agent.stream(prompt):
            click.echo(chunk.content, nl=False)
    
    asyncio.run(run())
```

### Jupyter Notebook

```python
from IPython.display import display, HTML
import ipywidgets as widgets

output = widgets.Output()
display(output)

async for chunk in agent.stream("Tell me about AI"):
    with output:
        print(chunk.content, end="")
```

## Troubleshooting

### Issue: No streaming output

**Solution**: Check provider support
```python
print(agent.get_provider_info()['supports_streaming'])
```

### Issue: Slow streaming

**Solutions**:
- Use a faster model (e.g., gpt-3.5-turbo)
- Check network connection
- Reduce max_tokens parameter

### Issue: Incomplete responses

**Solution**: Handle the final chunk
```python
async for chunk in agent.stream(prompt):
    if chunk.is_final:
        # Process final metadata
        pass
```

## API Reference

### StreamChunk

```python
@dataclass
class StreamChunk:
    content: str                    # Text content
    token: Optional[str] = None     # Individual token
    metadata: Dict[str, Any] = {}   # Provider metadata
    is_final: bool = False          # Last chunk indicator
    timestamp: float                # Creation time
```

### StreamingResponse

```python
@dataclass
class StreamingResponse:
    chunks: List[StreamChunk]       # All chunks
    complete_text: str              # Full text
    metadata: Dict[str, Any]        # Response metadata
    start_time: float               # Start timestamp
    end_time: Optional[float]       # End timestamp
    total_tokens: Optional[int]     # Token count
    
    # Properties
    duration: Optional[float]       # Total duration
    chunk_count: int                # Number of chunks
```

### Agent.stream()

```python
async def stream(
    self,
    prompt: str,
    *,
    temperature: float = None,
    max_tokens: int = None,
    top_p: float = None,
    frequency_penalty: float = None,
    presence_penalty: float = None,
    stop: List[str] = None,
    **kwargs
) -> AsyncIterator[StreamChunk]:
    """Stream a response token by token."""
```

## Migration from v0.1.x

If you're upgrading from v0.1.x, here's what's new:

```python
# v0.1.x - No streaming
response = agent.run("Tell me a story")
print(response.content)

# v0.2.0 - With streaming
async for chunk in agent.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

Note that all methods are now async, so you'll need to update your code accordingly.

## Common Pitfalls and Solutions

### Using @tool with WorkflowAgent Streaming

**Problem**: Using `@tool` decorators with WorkflowAgent streaming causes API errors.

**Solution**: Use the handler pattern instead:

```python
# ❌ DON'T do this
@tool
def my_tool():
    pass

# ✅ DO this instead
def my_tool():
    pass

# Then create a handler
async def my_tool_handler(agent, step, context):
    result = my_tool(**context.get("params", {}))
    return result
```

### Data Flow in Workflows

**Problem**: Not passing data correctly between workflow steps.

**Solution**: Use context dictionary:

```python
# Store results in context
context["step1_result"] = result

# Access in next step
next_input = context.get("step1_result")
```

## Examples

Complete examples are available in `examples/streaming/`:

- `basic_streaming.py` - Introduction to streaming
- `multi_provider_stream.py` - Compare providers
- `advanced_streaming_handlers.py` - Advanced patterns with handler approach
- `streaming_with_handlers.py` - Tool integration using handlers
- `practical_streaming.py` - Real-world use cases

Reference implementations:
- `examples/agents/workflow_with_handlers.py` - Handler pattern reference
- `examples/agents/workflow_with_wrappers.py` - Tool wrapper pattern

## Next Steps

- Learn about [Advanced Reasoning Patterns](./reasoning_patterns.md)
- Explore [Model Context Protocol](./mcp_integration.md)
- Set up [Telemetry](./telemetry/index.md) for monitoring

---

*Streaming transforms the user experience by providing immediate feedback. Start using it today to make your agents more responsive!*
