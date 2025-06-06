# API Reference

Complete API documentation for AgentiCraft v0.1.1.

## Core APIs

### [Agent](agent.md)
The foundation of AgentiCraft - create intelligent agents with tools, memory, and provider flexibility.

```python
from agenticraft import Agent

agent = Agent(name="Assistant", model="gpt-4")
response = agent.run("Hello!")
```

### [ReasoningAgent](agent.md#reasoningagent)
Transparent reasoning with step-by-step thought processes.

```python
from agenticraft import ReasoningAgent

agent = ReasoningAgent(name="Thinker", model="gpt-4")
response = agent.run("Solve this problem...")
# Access reasoning: response.reasoning
```

### [WorkflowAgent](workflow.md#workflowagent)
Execute complex multi-step workflows with parallel processing.

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(name="Processor", model="gpt-4")
response = agent.run_workflow(prompt, workflow=[...])
```

## Provider APIs

### [OpenAI](providers/openai.md)
- GPT-4, GPT-3.5-Turbo
- Function calling
- Streaming support

### [Anthropic](providers/anthropic.md)
- Claude 3 (Opus, Sonnet, Haiku)
- Large context windows
- Constitutional AI

### [Ollama](providers/ollama.md)
- Local models (Llama2, Mistral, CodeLlama)
- Privacy-first
- No API costs

## Tool System

### [@tool Decorator](tool.md#tool-decorator)
Create tools with a simple decorator:

```python
@tool
def search(query: str) -> str:
    """Search the web."""
    return results
```

### [Tool Class](tool.md#tool-class)
Advanced tool configuration:

```python
tool = Tool(
    name="search",
    description="Search the web",
    function=search_function
)
```

## Configuration

### AgentConfig
Configure agents with type-safe dataclasses:

```python
config = AgentConfig(
    name="Bot",
    model="gpt-4",
    provider="openai",
    temperature=0.7
)
```

## Quick Reference

### Provider Switching
```python
# Runtime provider changes
agent.set_provider("anthropic", model="claude-3-opus-20240229")

# Get current provider
info = agent.get_provider_info()

# List available providers
providers = agent.list_available_providers()
```

### Memory
```python
# Enable conversation memory
agent = Agent(name="MemBot", memory_enabled=True)

# Access memory
history = agent.memory.get_history()
```

### Error Handling
```python
from agenticraft import ProviderError, ToolError

try:
    response = agent.run(prompt)
except ProviderError as e:
    # Handle provider issues
    agent.set_provider("ollama", model="llama2")
except ToolError as e:
    # Handle tool failures
    pass
```

## Complete Examples

See the [Examples](../examples/index.md) section for complete working code:
- [Basic usage](../examples/hello-world.md)
- [Provider switching](../examples/provider-switching.md)
- [Advanced agents](../examples/advanced-agents.md)

## API Versioning

This documentation covers AgentiCraft v0.1.1. For detailed changes, see the [Changelog](../changelog.md).
