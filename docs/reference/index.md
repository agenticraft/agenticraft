# API Reference

Welcome to the AgentiCraft API Reference. This documentation covers all public APIs in v0.1.1.

## Quick Links

- [Complete API Reference v0.1.1](api-v0.1.1.md) - Detailed API documentation
- [Core Classes](#core-classes) - Agent, ReasoningAgent, WorkflowAgent
- [Tools](#tools) - Tool decorators and base classes
- [Providers](#providers) - LLM provider configuration
- [Memory](#memory) - Memory implementations
- [Workflows](#workflows) - Workflow system

## Core Classes

### Agents
- [`Agent`](api-v0.1.1.md#agent) - Base agent class
- [`ReasoningAgent`](api-v0.1.1.md#reasoningagent-new-in-v011) - Step-by-step reasoning (v0.1.1)
- [`WorkflowAgent`](api-v0.1.1.md#workflowagent-new-in-v011) - Multi-step workflows (v0.1.1)

### Tools
- [`@tool`](api-v0.1.1.md#tool-decorator) - Tool decorator
- [`BaseTool`](api-v0.1.1.md#basetool) - Base tool class

### Workflows
- [`Workflow`](api-v0.1.1.md#workflow) - Workflow definition
- [`WorkflowStep`](api-v0.1.1.md#workflowstep-v011) - Step configuration

### Memory
- [`ConversationMemory`](api-v0.1.1.md#conversationmemory) - Short-term memory
- [`KnowledgeMemory`](api-v0.1.1.md#knowledgememory) - Long-term storage

### Providers
- [Provider Configuration](api-v0.1.1.md#provider-configuration) - Setup guide
- [Provider Factory](api-v0.1.1.md#provider-factory-v011) - Dynamic provider creation

## What's New in v0.1.1

- **Dynamic Provider Switching** - Change providers at runtime with `agent.set_provider()`
- **ReasoningAgent** - New agent type for transparent reasoning
- **WorkflowAgent** - New agent type for complex workflows
- **Anthropic Provider** - Full Claude 3 support
- **Ollama Provider** - Local model support
- **Provider Auto-detection** - Automatic provider selection from model names

## Getting Started

```python
from agenticraft import Agent, ReasoningAgent, WorkflowAgent

# Basic agent
agent = Agent(name="Assistant", model="gpt-4")

# Reasoning agent
reasoner = ReasoningAgent(name="ProblemSolver")

# Workflow agent
workflow_agent = WorkflowAgent(name="Processor")
```

For more examples, see the [Examples Directory](../../examples/).
