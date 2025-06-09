# AgentiCraft Documentation

Welcome to the AgentiCraft documentation! AgentiCraft is a production-ready framework for building AI agents with transparent reasoning, streaming capabilities, and comprehensive observability.

## 🚀 What's New in v0.2.0-alpha

### 🌊 Streaming Support
Real-time token-by-token responses for all providers:
```python
async for chunk in agent.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

### 🧠 Advanced Reasoning Patterns
Three sophisticated reasoning patterns that make agent thinking transparent:
- **Chain of Thought**: Step-by-step reasoning with confidence tracking
- **Tree of Thoughts**: Multi-path exploration for creative solutions
- **ReAct**: Combines reasoning with tool actions

```python
from agenticraft.agents.reasoning import ReasoningAgent

agent = ReasoningAgent(reasoning_pattern="chain_of_thought")
response = await agent.think_and_act("Solve this complex problem")

# See the reasoning process
for step in response.reasoning_steps:
    print(f"{step.number}. {step.description} (confidence: {step.confidence:.0%})")
```

### 🔌 Model Context Protocol (MCP)
Seamless integration with Anthropic's MCP ecosystem:
```python
from agenticraft.protocols.mcp import MCPServer, MCPClient

# Use MCP tools in your agents
client = MCPClient("ws://localhost:8765")
agent = Agent(tools=[client.get_tool("calculator")])
```

### 📊 Production Telemetry
Built-in OpenTelemetry support with <1% overhead:
```python
from agenticraft.telemetry import setup_telemetry

setup_telemetry(
    service_name="my-agent-service",
    otlp_endpoint="http://localhost:4318",
    enable_metrics=True,
    enable_tracing=True
)
```

### 💾 Advanced Memory Systems
Vector and knowledge graph memory for intelligent context:
```python
from agenticraft.memory import VectorMemory, KnowledgeGraphMemory

# Semantic search across conversations
memory = VectorMemory()
relevant_context = await memory.search("previous discussions about AI")
```

[See all v0.2.0-alpha features →](./changelog.md)

## 📚 Documentation Structure

### Getting Started
- [Installation](./getting-started/installation.md)
- [Quick Start](./quickstart.md)
- [Core Concepts](./concepts/agents.md)

### Features
- [🔄 Provider Switching](./features/provider_switching.md) - Switch LLMs at runtime
- [👥 Advanced Agents](./features/advanced_agents.md) - ReasoningAgent and WorkflowAgent
- [🧠 Reasoning Patterns](./features/reasoning_patterns.md) - CoT, ToT, and ReAct patterns
- [🌊 Streaming Responses](./features/streaming.md) - Real-time token output
- [🔌 MCP Integration](./features/mcp_integration.md) - Model Context Protocol support
- [📊 Telemetry & Observability](./features/telemetry/index.md) - Production monitoring
- [💾 Memory Systems](./features/memory/README.md) - Vector and graph memory
- [🔧 Enhanced Workflows](./features/enhanced_workflows.md) - Visual workflow design
- [🛍️ Tool Marketplace](./features/marketplace/README.md) - Plugin ecosystem

### API Reference
- [Agent](./reference/agent.md)
- [Tool](./reference/tool.md)
- [Workflow](./reference/workflow.md)
- [Reasoning Patterns](./api/reasoning/index.md)
  - [Chain of Thought](./api/reasoning/chain_of_thought.md)
  - [Tree of Thoughts](./api/reasoning/tree_of_thoughts.md)
  - [ReAct](./api/reasoning/react.md)
- [Streaming](./api/streaming.md)
- [Providers](./reference/providers/openai.md)

### Migration Guides
- [Reasoning Patterns](./migration/reasoning.md)
- [Streaming](./migration/streaming.md)

### Quick Reference
- [Reasoning Patterns](./quick-reference/reasoning.md)
- [Streaming](./quick-reference/streaming.md)

### Examples
- [Hello World](./examples/hello-world.md)
- [Provider Switching](./examples/provider-switching.md)
- [Advanced Agents](./examples/advanced-agents.md)
- [Real-World Apps](./examples/real-world.md)
- [All Examples](./examples/index.md)

### Guides
- [Performance Tuning](./guides/performance-tuning.md)
- [Reasoning Integration](./guides/reasoning-integration.md)

## 🚀 Key Features

### Dynamic Provider Switching
Switch between OpenAI, Anthropic, and Ollama at runtime:

```python
agent.set_provider("anthropic", model="claude-3-opus-20240229")
response = await agent.run("Complex task requiring powerful model")

agent.set_provider("ollama", model="llama2")
response = await agent.run("Simple task that can use local model")
```

[Learn more →](./features/provider_switching.md)

### Streaming Responses
Real-time, token-by-token output with visual progress:

```python
# With progress bar
async for chunk in agent.stream_with_progress("Generate a report"):
    # Automatic progress visualization
    pass
```

[Learn more →](./features/streaming.md)

### Advanced Reasoning
Make agent thinking transparent with structured reasoning patterns:

```python
# Automatic pattern selection
agent = ReasoningAgent(reasoning_pattern="auto")
response = await agent.think_and_act(query)
```

[Learn more →](./features/reasoning_patterns.md)

### Production Observability
Built-in telemetry for monitoring, debugging, and optimization:

```python
# Automatic tracing of all operations
with tracer.start_as_current_span("complex_workflow"):
    response = await agent.run("Process customer request")
```

[Learn more →](./features/telemetry/index.md)

## 📖 Start Here

New to AgentiCraft? Start with these resources:

1. [Quick Start Guide](./quickstart.md) - Get up and running in 5 minutes
2. [Reasoning Patterns Guide](./features/reasoning_patterns.md) - Learn about transparent reasoning
3. [Streaming Guide](./features/streaming.md) - Real-time responses
4. [Examples](./examples/index.md) - 50+ working examples

### By Use Case

**Building a chatbot?**
- Start with [Streaming Responses](./features/streaming.md)
- Add [Memory Systems](./features/memory/README.md)
- Deploy with [Telemetry](./features/telemetry/index.md)

**Creating an autonomous agent?**
- Use [Advanced Reasoning](./features/reasoning_patterns.md)
- Design with [Enhanced Workflows](./features/enhanced_workflows.md)
- Monitor with [Observability](./features/telemetry/index.md)

**Building tool integrations?**
- Explore [MCP Protocol](./features/mcp_integration.md)
- Create [Custom Tools](./concepts/tools.md)
- Share via [Plugin Marketplace](./features/marketplace/README.md)

## 🔍 How to Use This Documentation

- **Feature Guides**: In-depth explanations of each feature with examples
- **API Reference**: Detailed technical documentation of all classes and methods
- **Migration Guides**: Step-by-step instructions for upgrading
- **Quick Reference**: Concise syntax and common patterns
- **Examples**: Working code you can run and modify

## 💡 Getting Help

- **Discord**: Join our [community Discord](https://discord.gg/agenticraft)
- **GitHub Issues**: Report bugs or request features
- **Stack Overflow**: Tag questions with `agenticraft`

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](./contributing.md) to get started.

---

*AgentiCraft - Dead simple AI agents with reasoning traces*
