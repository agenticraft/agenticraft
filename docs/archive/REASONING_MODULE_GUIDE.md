# AgentiCraft Reasoning Module Structure

## Overview

AgentiCraft has two separate reasoning implementations that serve different purposes:

### 1. Core Reasoning (`agenticraft.core.reasoning`)
- **Location**: `/agenticraft/core/reasoning.py`
- **Purpose**: Basic reasoning functionality integrated with the core Agent class
- **Classes**:
  - `SimpleReasoning` - Basic step-by-step reasoning
  - `ChainOfThought` - Chain of thought reasoning
  - `ReflectiveReasoning` - Multi-perspective reasoning
  - `ReasoningTrace` - Trace container for all patterns
  - `ReasoningStep` - Individual reasoning steps

### 2. Advanced Reasoning Patterns (`agenticraft.reasoning`)
- **Location**: `/agenticraft/reasoning/`
- **Purpose**: Advanced, protocol-aware reasoning patterns
- **Structure**:
  ```
  reasoning/
  ├── __init__.py
  ├── patterns/
  │   ├── __init__.py
  │   ├── base.py           # Base classes
  │   ├── chain_of_thought.py
  │   ├── tree_of_thoughts.py
  │   ├── react.py
  │   └── selector.py
  ```

## Import Guide

### For Basic Reasoning (Integrated with Agent)
```python
from agenticraft import Agent
from agenticraft.core.reasoning import ChainOfThought

# The Agent class automatically uses reasoning
agent = Agent(name="MyAgent")
response = agent.run("Solve this problem")
```

### For Advanced Reasoning Patterns
```python
# Import from the reasoning module
from agenticraft.reasoning import (
    ChainOfThoughtReasoning,
    TreeOfThoughtsReasoning,
    ReActReasoning,
    PatternSelector
)

# Use with ReasoningAgent
from agenticraft.agents import ReasoningAgent

agent = ReasoningAgent(
    name="AdvancedReasoner",
    reasoning_pattern="chain_of_thought"
)
```

## Key Differences

### Core Reasoning
- Simple, synchronous implementation
- Tightly integrated with Agent class
- Automatic trace generation
- No external dependencies

### Advanced Reasoning Patterns
- Async-first design
- Protocol-aware (MCP, Fabric)
- Supports complex patterns (Tree of Thoughts)
- Extensible pattern system

## Common Issues and Solutions

### Issue 1: ImportError with ThoughtProcess
**Error**: `cannot import name 'ThoughtProcess' from 'agenticraft.core.reasoning'`

**Solution**: `ThoughtProcess` doesn't exist. Use the correct class names:
- Core: `SimpleReasoning`, `ChainOfThought`, `ReflectiveReasoning`
- Advanced: `ChainOfThoughtReasoning`, `TreeOfThoughtsReasoning`

### Issue 2: Circular Import Errors
**Error**: Import errors when using reasoning patterns

**Solution**: The issue has been fixed by removing circular dependencies. The advanced reasoning patterns no longer import from core.reasoning.

### Issue 3: Missing Modules
**Error**: `ImportError` when importing advanced patterns

**Solution**: Install with the appropriate extras:
```bash
# For advanced reasoning patterns
pip install agenticraft[reasoning]

# For all features
pip install agenticraft[all]
```

## Usage Examples

### Example 1: Basic Agent with Reasoning
```python
from agenticraft import Agent

agent = Agent(
    name="BasicReasoner",
    instructions="You are a helpful assistant that thinks step by step"
)

response = agent.run("What is 15% of 250?")
print(response.messages[-1].content)
```

### Example 2: Advanced Reasoning Agent
```python
from agenticraft.agents import ReasoningAgent

agent = ReasoningAgent(
    name="AdvancedReasoner",
    reasoning_pattern="tree_of_thoughts",
    instructions="Explore multiple solution paths"
)

result = await agent.reason("Design a sustainable city")
print(result.get_explanation())
```

### Example 3: Custom Reasoning Pattern
```python
from agenticraft.reasoning import ReasoningPattern, ReasoningResult, ReasoningStep

class MyCustomReasoning(ReasoningPattern):
    def __init__(self):
        super().__init__(name="custom")
    
    async def reason(self, problem: str, context=None, **kwargs):
        # Custom reasoning logic
        steps = []
        # ... implement reasoning ...
        return ReasoningResult(
            conclusion="My conclusion",
            confidence=0.9,
            steps=steps,
            total_duration=1.0,
            pattern_used=self.name
        )
```

## Best Practices

1. **Use Core Reasoning** for:
   - Simple agent interactions
   - Quick prototypes
   - Synchronous workflows

2. **Use Advanced Patterns** for:
   - Complex reasoning tasks
   - Multi-step problem solving
   - Protocol-aware applications
   - Production systems

3. **Avoid Mixing**: Don't import from both core.reasoning and reasoning modules in the same file to avoid confusion.

## Testing

Run the test suite to verify imports:
```bash
# Test core functionality
python test_minimal.py

# Test reasoning imports
python test_fixed_imports.py

# Run full test suite
pytest tests/
```

## Migration Guide

If you're upgrading from an older version:

1. Replace any imports of `ThoughtProcess` with appropriate classes
2. Update `from agenticraft.core.reasoning` to use the correct module
3. For advanced patterns, use `from agenticraft.reasoning`
4. Check that all reasoning-related imports are from one module or the other

## Support

If you encounter issues:
1. Check this documentation first
2. Run the diagnostic scripts
3. Check the [GitHub issues](https://github.com/agenticraft/agenticraft/issues)
4. Join our [Discord](https://discord.gg/agenticraft) for help
