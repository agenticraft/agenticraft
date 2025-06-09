# Reasoning Patterns API Reference

## Overview

AgentiCraft provides three advanced reasoning patterns that enable agents to solve complex problems with transparency and structured thinking.

## Available Patterns

### [Chain of Thought (CoT)](chain_of_thought.md)
Linear, step-by-step reasoning with confidence tracking and alternative generation.

### [Tree of Thoughts (ToT)](tree_of_thoughts.md)
Multi-path exploration with scoring, pruning, and optimal path selection.

### [ReAct](react.md)
Combines reasoning with actions, creating dynamic thought-action-observation cycles.

## Quick Start

```python
from agenticraft.agents.reasoning import ReasoningAgent

# Create agent with specific pattern
agent = ReasoningAgent(
    name="SmartAgent",
    reasoning_pattern="chain_of_thought",  # or "tree_of_thoughts", "react"
    pattern_config={
        # Pattern-specific configuration
    }
)

# Execute reasoning
response = await agent.think_and_act("Your problem here")

# Access results
print(response.content)  # Final answer
print(response.reasoning)  # Human-readable reasoning
for step in response.reasoning_steps:
    print(f"{step.number}: {step.description} (confidence: {step.confidence})")
```

## Pattern Selection

### Automatic Selection

```python
# Let the agent choose the best pattern
agent = ReasoningAgent(name="AutoAgent")
pattern = agent.select_best_pattern("Your problem")
```

### Manual Selection Guide

| Problem Type | Recommended Pattern | Example |
|--------------|-------------------|---------|
| Sequential analysis | Chain of Thought | "Explain how photosynthesis works" |
| Creative exploration | Tree of Thoughts | "Design a mobile app for seniors" |
| Research & tool use | ReAct | "Find the current GDP of Japan" |

## Common Types

### Base Types

```python
from agenticraft.reasoning.patterns.base import (
    ReasoningStep,
    ReasoningTrace,
    PatternConfig
)
```

### Pattern-Specific Types

```python
# Chain of Thought
from agenticraft.reasoning.patterns.chain_of_thought import ThoughtStep

# Tree of Thoughts
from agenticraft.reasoning.patterns.tree_of_thoughts import (
    TreeNode,
    NodeStatus,
    NodeType
)

# ReAct
from agenticraft.reasoning.patterns.react import (
    StepType,
    ReactStep
)
```

## Integration with Agents

All reasoning patterns integrate seamlessly with ReasoningAgent:

```python
# The agent handles pattern initialization and execution
agent = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "max_depth": 4,
        "beam_width": 3
    }
)

# Pattern is used automatically
response = await agent.think_and_act("Design a logo")
```

## Performance Metrics

| Pattern | Complexity | Time (simple) | Time (complex) | Memory |
|---------|-----------|---------------|----------------|--------|
| CoT | O(n) | ~50ms | ~150ms | Low |
| ToT | O(b^d) | ~200ms | ~500ms | High |
| ReAct | O(n) | ~100ms | ~300ms+ | Medium |

## See Also

- [Pattern Selector](selector.md) - Automatic pattern selection
- [Base Pattern](base.md) - Base classes and interfaces
- [Integration Guide](../../guides/reasoning-integration.md) - Using patterns in applications
