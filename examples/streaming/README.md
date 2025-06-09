# Streaming Examples for AgentiCraft

This directory contains comprehensive examples demonstrating AgentiCraft's streaming capabilities, including the proper patterns for using streaming with WorkflowAgent and tools.

## 🚀 Quick Start

### Interactive Runner (Recommended)
```bash
# Run the interactive example selector
python run_examples.py
```

### Direct Execution (No API Key Required)
```bash
# Basic streaming demonstration
python simple_streaming_demo.py

# WorkflowAgent streaming demo
python workflow_streaming_demo.py
```

### With API Keys
```bash
# Set your API key
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"

# Run real streaming examples
python basic_streaming.py
python advanced_streaming_handlers.py
```

## 📝 Example Files

### Core Examples

#### `simple_streaming_demo.py`
- **No API key required** (has mock mode)
- Basic streaming concepts
- Mock streaming demonstration
- Real API streaming (if keys available)
- Progress visualization
- Comparison of streaming vs non-streaming

#### `basic_streaming.py`
- Introduction to streaming with real APIs
- Provider comparison
- Stream collection patterns
- Error handling basics

#### `workflow_streaming_demo.py`
- Simple WorkflowAgent streaming example
- Shows workflow creation and execution
- Parallel workflow demonstration
- **No API key required** (uses mock streaming)

### Advanced Examples

#### `streaming_with_handlers.py` ⭐ **RECOMMENDED**
- **Proper handler pattern for tools with WorkflowAgent**
- StreamingToolWrapper implementation
- How to avoid @tool decorator issues
- Context-based data flow
- Best practices demonstration

#### `advanced_streaming_handlers.py`
- Advanced features with handler pattern
- Progress tracking with visual feedback
- Retry logic with streaming
- Tool execution history
- Interruption handling

#### `practical_streaming.py`
- Real-world use cases
- Interactive chat interface
- Document processing with progress
- Multi-step task execution

### Specialized Examples

#### `visual_streaming.py`
- Visual streaming demonstrations
- Progress bars and indicators
- Terminal UI examples

#### `multi_provider_stream.py`
- Compare streaming across providers
- Provider-specific features
- Performance comparison

#### `run_examples.py`
- Interactive example runner
- Checks for API keys automatically
- Menu-driven example selection
- Runs all examples in sequence option
- Helpful for exploring examples without remembering filenames

## 🔑 Key Concepts

### 1. Basic Streaming
```python
async for chunk in agent.stream("Your prompt"):
    print(chunk.content, end="", flush=True)
```

### 2. Handler Pattern for WorkflowAgent (IMPORTANT!)
```python
# ✅ CORRECT: Use handlers for tools with WorkflowAgent
async def tool_handler(agent, step, context):
    params = context.get("params", {})
    result = my_tool_function(**params)
    context["result"] = result
    return str(result)

agent.register_handler("my_handler", tool_handler)
workflow.add_step(name="step", handler="my_handler")

# ❌ WRONG: Don't use @tool decorator with streaming
@tool
def my_tool():  # This causes API errors
    pass
```

### 3. Collecting Streams
```python
from agenticraft.core.streaming import StreamingResponse

response = StreamingResponse()
async for chunk in agent.stream("Your prompt"):
    response.add_chunk(chunk)
print(response.complete_text)
```

### 4. Error Handling
```python
from agenticraft.core.streaming import StreamInterruptedError

try:
    async for chunk in agent.stream("Your prompt"):
        process_chunk(chunk)
except StreamInterruptedError as e:
    print(f"Partial response: {e.partial_response}")
```

## 🎓 Recommended Learning Path

1. **Start with the Interactive Runner**
   ```bash
   python run_examples.py
   ```
   - Automatically checks for API keys
   - Guides you through examples in order
   - Shows which examples work without API keys

2. **Follow this progression:**
   - `simple_streaming_demo.py` - Learn basic streaming concepts (no API key)
   - `workflow_streaming_demo.py` - See WorkflowAgent streaming (no API key)
   - `basic_streaming.py` - Real API streaming fundamentals
   - `streaming_with_handlers.py` - **Critical**: Learn the handler pattern
   - `advanced_streaming_handlers.py` - Production-ready patterns
   - `practical_streaming.py` - Real-world applications

3. **Study the handler pattern carefully**
   - The handler pattern in `streaming_with_handlers.py` is essential
   - This pattern avoids common streaming + tool errors
   - Use it as the template for your own implementations

## 🎯 When to Use Each Pattern

### Use Basic Streaming When:
- Working with simple Agent (not WorkflowAgent)
- No tool integration needed
- Direct prompt-response interaction

### Use Handler Pattern When:
- Working with WorkflowAgent
- Integrating tools into workflows
- Need control over data flow
- Building production applications

### Use Mock Streaming When:
- Testing without API costs
- Developing UI/UX
- Learning streaming concepts

## 🏗️ Architecture Overview

```
┌─────────────────┐
│     Agent       │ → Basic streaming for simple use cases
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WorkflowAgent   │ → Requires handler pattern for tools
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Handler      │ → Registered functions that execute tools
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tool Function  │ → Regular functions (no @tool decorator)
└─────────────────┘
```

## 🧪 Testing Approach

1. **Start with Mock**: Use `simple_streaming_demo.py` to understand concepts
2. **Learn Handlers**: Study `streaming_with_handlers.py` for proper patterns
3. **Try Real APIs**: Run examples with API keys set
4. **Build Your Own**: Use the patterns in your applications

## 📊 Performance Tips

- **Chunk Size**: Smaller chunks = more responsive UI
- **Buffer Management**: Process chunks immediately for memory efficiency
- **Parallel Streams**: Use asyncio.gather() for multiple streams
- **Progress Tracking**: Update UI every N chunks, not every chunk

## 🐛 Common Issues and Solutions

### Tool Streaming Errors
**Problem**: `Invalid parameter: messages with role 'tool'` error  
**Solution**: Use handler pattern instead of @tool decorator (see `streaming_with_handlers.py`)

### No Streaming Output
**Problem**: Nothing appears during streaming  
**Solution**: Use `flush=True` in print statements: `print(chunk.content, end="", flush=True)`

### Incomplete Responses
**Problem**: Stream cuts off unexpectedly  
**Solution**: Handle the `is_final` flag and check for interruptions

### Slow Streaming
**Solutions**:
- Use a faster model (e.g., gpt-3.5-turbo instead of gpt-4)
- Check network latency
- Reduce max_tokens if appropriate

## 📚 Related Documentation

- **Handler Pattern**: See `examples/agents/workflow_with_handlers.py`
- **Tool Wrappers**: See `examples/agents/workflow_with_wrappers.py`
- **API Reference**: See `docs/features/streaming.md`
- **Best Practices**: Handler pattern section in streaming docs

## 🚀 Next Steps

1. Run `simple_streaming_demo.py` to see basic streaming
2. Study `streaming_with_handlers.py` to learn the handler pattern
3. Explore `advanced_streaming_handlers.py` for production patterns
4. Read the [streaming documentation](../../docs/features/streaming.md)

---

*Remember: Always use the handler pattern when combining WorkflowAgent with tools and streaming!*
