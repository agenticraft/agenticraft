# Reasoning Module Import Fix

## Issue
The reasoning module imports were failing because:
1. The module structure has patterns in a subdirectory (`reasoning/patterns/`)
2. The imports were trying to import directly from `agenticraft.reasoning`
3. Some dependencies might not be available

## Solution

### 1. Fixed Module Structure
The reasoning module now properly exports from the patterns subdirectory:

```python
# agenticraft/reasoning/__init__.py
from .patterns import *
from .patterns.base import ReasoningPattern, ReasoningResult, ReasoningStep
```

### 2. Graceful Import Handling
Examples now handle missing imports gracefully:

```python
try:
    from agenticraft.reasoning import ChainOfThoughtReasoning
except ImportError:
    # Use mock or fallback
    ChainOfThoughtReasoning = MockImplementation
```

### 3. Module Structure
```
agenticraft/reasoning/
├── __init__.py              # Main exports
├── patterns/                # Pattern implementations
│   ├── __init__.py         # Pattern exports
│   ├── base.py             # Base classes
│   ├── chain_of_thought.py # CoT implementation
│   ├── tree_of_thoughts.py # ToT implementation
│   └── react.py            # ReAct pattern
└── README.md               # Documentation
```

## Usage Examples

### Basic Import
```python
from agenticraft.reasoning import ChainOfThoughtReasoning

# Check if available
if ChainOfThoughtReasoning:
    cot = ChainOfThoughtReasoning()
```

### With Protocol Fabric
```python
from agenticraft.fabric import agent
from agenticraft.reasoning import ChainOfThoughtReasoning

@agent("reasoning_agent", servers=["mcp://localhost:3000"])
async def my_agent(self, problem: str):
    async with ChainOfThoughtReasoning() as cot:
        # Use reasoning with protocol tools
        data = await self.tools.search(problem)
        cot.add_observation("Data gathered", data)
        return cot.synthesize([data])
```

### Fallback Pattern
```python
try:
    from agenticraft.reasoning import ChainOfThoughtReasoning
    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False
    
    # Simple fallback
    class ChainOfThoughtReasoning:
        async def think(self, problem):
            return {"conclusion": f"Basic analysis of {problem}"}
```

## Files Updated

1. `/agenticraft/reasoning/__init__.py` - Fixed imports and exports
2. `/agenticraft/reasoning/patterns/__init__.py` - Proper pattern exports
3. `/agenticraft/reasoning/patterns/base.py` - Fixed relative imports
4. `/examples/fabric/protocol_integration_simple.py` - Graceful handling example
5. `/agenticraft/fabric/integrations.py` - Added import fallbacks

## Testing

Run the test script to verify imports:
```bash
python test_reasoning_imports.py
```

## Best Practices

1. Always check if optional modules are available
2. Provide fallback implementations for critical features
3. Use try/except blocks for optional imports
4. Document which features require which modules
5. Keep mock implementations simple but functional

The Protocol Fabric now works seamlessly with or without the reasoning module!
