# AgentiCraft Documentation

Welcome to the AgentiCraft documentation! AgentiCraft is a production-ready framework for building AI agents with transparent reasoning, streaming capabilities, and comprehensive observability.

## 🎯 What's New in v0.2.0

### Advanced Reasoning Patterns
Three sophisticated reasoning patterns that make agent thinking transparent and structured:
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

[Learn more →](./features/reasoning_patterns.md)

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

### Dynamic Provider Switching (v0.1.1)
Switch between OpenAI, Anthropic, and Ollama at runtime:

```python
agent.set_provider("anthropic", model="claude-3-opus-20240229")
response = await agent.run("Complex task requiring powerful model")

agent.set_provider("ollama", model="llama2")
response = await agent.run("Simple task that can use local model")
```

[Learn more →](./features/provider_switching.md)

### Advanced Reasoning (v0.2.0)
Make agent thinking transparent with structured reasoning patterns.

[Learn more →](./features/reasoning_patterns.md)

### Coming Soon
- Streaming responses for real-time output
- MCP protocol for standardized tool interactions
- Enhanced workflows with visual builders
- Production telemetry and observability

## 📖 Start Here

New to AgentiCraft? Start with these resources:

1. [Quick Start Guide](./quickstart.md) - Get up and running in 5 minutes
2. [Reasoning Patterns Guide](./features/reasoning_patterns.md) - Learn about transparent reasoning
3. [Examples](./examples/index.md) - See AgentiCraft in action

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

We welcome contributions! See our [Contributing Guide](../CONTRIBUTING.md) to get started.

---

*AgentiCraft - Dead simple AI agents with reasoning traces*
