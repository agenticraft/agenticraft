# API Reference

Complete API documentation for AgentiCraft.

## Core Components

### [Agent](agent.md)
The main Agent class and related functionality.

### [Tool](tool.md)
Tool decorators and tool management.

### [Workflow](workflow.md)
Workflow and Step classes for multi-agent systems.

### [Memory](memory.md)
Memory interfaces and implementations.

### [Providers](providers.md)
LLM provider integrations.

## Quick Reference

### Creating an Agent

```python
from agenticraft import Agent

agent = Agent(
    name="MyAgent",
    instructions="Agent instructions",
    model="gpt-4",
    tools=[...],
    memory=[...]
)
```

### Defining Tools

```python
from agenticraft import tool

@tool
def my_tool(param: str) -> str:
    """Tool description."""
    return result
```

### Building Workflows

```python
from agenticraft import Workflow, Step

workflow = Workflow(name="pipeline")
workflow.add_steps([
    Step("step1", agent=agent1),
    Step("step2", agent=agent2, depends_on=["step1"])
])
```

## Type Reference

All types are available from:

```python
from agenticraft.core.types import (
    AgentResponse,
    ToolCall,
    Message,
    # ... more types
)
```

## Exception Reference

All exceptions are available from:

```python
from agenticraft.core.exceptions import (
    AgentError,
    ToolError,
    WorkflowError,
    # ... more exceptions
)
```
