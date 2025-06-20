# AgentiCraft Reasoning Module

This module provides advanced reasoning patterns for agents.

## Structure

```
reasoning/
├── __init__.py          # Main module exports
├── patterns/            # Reasoning pattern implementations
│   ├── __init__.py
│   ├── base.py          # Base classes (ReasoningPattern, ReasoningStep, etc.)
│   ├── chain_of_thought.py  # Chain of Thought reasoning
│   ├── tree_of_thoughts.py  # Tree of Thoughts reasoning
│   ├── react.py         # ReAct pattern
│   └── selector.py      # Pattern selection utilities
└── core/                # Core reasoning infrastructure
    └── reasoning.py     # Base reasoning functionality
```

## Usage

```python
from agenticraft.reasoning import ChainOfThoughtReasoning

# Create reasoning instance
cot = ChainOfThoughtReasoning()

# Use in async context
async def reason_about(problem: str):
    trace = await cot.think(problem)
    return trace.get_conclusion()
```

## Available Patterns

1. **Chain of Thought (CoT)** - Step-by-step reasoning
2. **Tree of Thoughts (ToT)** - Explore multiple reasoning paths
3. **ReAct** - Reasoning + Acting in interleaved fashion

## Import Notes

The module uses dynamic imports to handle cases where specific patterns might not be available. Always check if a pattern is available before using:

```python
from agenticraft.reasoning import ChainOfThoughtReasoning

if ChainOfThoughtReasoning:
    # Use the reasoning pattern
    cot = ChainOfThoughtReasoning()
else:
    # Fall back to basic reasoning
    print("ChainOfThoughtReasoning not available")
```
