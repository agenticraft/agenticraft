# Reasoning Patterns Migration Guide

This guide helps you migrate to the new reasoning patterns introduced in AgentiCraft v0.2.0-alpha.

## Overview

AgentiCraft v0.2.0-alpha introduces three powerful reasoning patterns:
- **Chain of Thought (CoT)** - Step-by-step reasoning
- **Tree of Thoughts (ToT)** - Multi-path exploration
- **ReAct** - Reasoning with tool actions

## Migration Steps

### 1. Update Your Imports

**Before (v0.1.x):**
```python
from agenticraft import Agent
```

**After (v0.2.0-alpha):**
```python
from agenticraft.agents.reasoning import ReasoningAgent
```

### 2. Update Agent Creation

**Before:**
```python
agent = Agent(
    name="Assistant",
    instructions="Help with tasks"
)
```

**After:**
```python
agent = ReasoningAgent(
    name="Assistant",
    instructions="Help with tasks",
    reasoning_pattern="chain_of_thought"  # or "tree_of_thoughts", "react", "auto"
)
```

### 3. Access Reasoning Traces

The new `ReasoningAgent` provides transparent access to the reasoning process:

```python
response = await agent.think_and_act("Solve a complex problem")

# Access reasoning steps
for step in response.reasoning_steps:
    print(f"{step.number}. {step.description}")
    print(f"   Confidence: {step.confidence:.0%}")
    if step.alternatives:
        print(f"   Alternatives considered: {len(step.alternatives)}")
```

### 4. Pattern Selection

You can let the agent automatically select the best reasoning pattern:

```python
agent = ReasoningAgent(
    name="AutoReasoner",
    reasoning_pattern="auto"  # Automatically selects based on query
)
```

## Pattern-Specific Migration

### Chain of Thought (CoT)

Best for: Mathematical problems, logical deduction, step-by-step analysis

```python
from agenticraft.reasoning.patterns import ChainOfThoughtPattern

# Direct pattern usage
pattern = ChainOfThoughtPattern()
result = await pattern.reason(
    query="If a train travels 120 miles in 2 hours...",
    context={}
)
```

### Tree of Thoughts (ToT)

Best for: Creative solutions, exploring multiple approaches

```python
from agenticraft.reasoning.patterns import TreeOfThoughtsPattern

pattern = TreeOfThoughtsPattern(
    max_branches=3,
    exploration_depth=3
)
```

### ReAct Pattern

Best for: Tasks requiring tool usage with reasoning

```python
from agenticraft.reasoning.patterns import ReactPattern
from agenticraft import tool

@tool
def calculator(expression: str) -> float:
    """Evaluate a mathematical expression"""
    return eval(expression)

agent = ReasoningAgent(
    name="MathAssistant",
    reasoning_pattern="react",
    tools=[calculator]
)
```

## Breaking Changes

1. **Response Format**: The response now includes a `reasoning_steps` attribute
2. **Async by Default**: All reasoning operations are async
3. **Pattern Configuration**: Each pattern has specific configuration options

## Backward Compatibility

To maintain backward compatibility, you can still use the base `Agent` class:

```python
from agenticraft import Agent

# This still works but without reasoning traces
agent = Agent(name="Assistant")
```

## Examples

See the [reasoning examples](../examples/reasoning.md) for complete working code:
- [Chain of Thought Demo](https://github.com/agenticraft/agenticraft/blob/main/examples/reasoning/chain_of_thought.py)
- [Tree of Thoughts Demo](https://github.com/agenticraft/agenticraft/blob/main/examples/reasoning/tree_of_thoughts.py)
- [ReAct Pattern Demo](https://github.com/agenticraft/agenticraft/blob/main/examples/reasoning/react.py)

## Need Help?

- Check the [API Reference](../api/reasoning/index.md)
- Join our [Discord community](https://discord.gg/agenticraft)
- Open an [issue on GitHub](https://github.com/agenticraft/agenticraft/issues)
