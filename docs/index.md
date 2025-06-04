# 🤖 Welcome to AgentiCraft

**Build AI agents as simple as writing Python**

[![PyPI version](https://badge.fury.io/py/agenticraft.svg)](https://badge.fury.io/py/agenticraft)
[![Documentation](https://img.shields.io/badge/docs-agenticraft.ai-blue.svg)](https://docs.agenticraft.ai)
[![License](https://img.shields.io/github/license/agenticraft/agenticraft.svg)](https://github.com/agenticraft/agenticraft/blob/main/LICENSE)


## Why AgentiCraft?

Building AI agents should be as simple as writing Python. No complex abstractions, no graph theory, no 500-page documentation. Just clean, simple code that works.

!!! tip "5-Minute Quickstart"
    
    Get your first agent running faster than making coffee. [Start here →](quickstart.md)

## Core Principles



- **🚀 Simple First**  
  If it's not simple, it's not in core. Every API designed for developer joy.

- **🧠 Transparent Reasoning**  
  See how your agents think, not just what they output. No black boxes.

- **🔌 MCP-Native**  
  First-class Model Context Protocol support. Use any MCP tool seamlessly.

- **📈 Production Ready**  
  Built-in observability, templates, and best practices from day one.

## Quick Example

```python
from agenticraft import Agent, tool

@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression, {"__builtins__": {}}, {})

agent = Agent(
    name="MathAssistant",
    instructions="You are a helpful math assistant.",
    tools=[calculate]
)

response = agent.run("What's 42 * 17 + 238?")
print(response.content)
# Output: "Let me calculate that for you: 42 * 17 + 238 = 952"

# See the reasoning process
print(response.reasoning)
# Output: "I need to calculate the expression 42 * 17 + 238..."
```

## What Makes AgentiCraft Different?

| Feature | AgentiCraft | Others |
|---------|-------------|---------|
| **Setup Time** | 1 minute | 5-30 minutes |
| **Core Size** | <2,000 lines | 50,000+ lines |
| **Time to First Agent** | 5 minutes | 30+ minutes |
| **Documentation** | 100% coverage | Variable |
| **Reasoning Visibility** | Built-in | Often hidden |
| **Production Templates** | Included | DIY |

## Features at a Glance

### 🎯 Simple Agent Creation
```python
agent = Agent(name="assistant")
```
That's it. No configuration files, no complex setup.

### 🧠 Transparent Reasoning
```python
response = agent.run("Complex question")
print(response.reasoning)  # See the thought process
```

### 🔧 Easy Tool Integration
```python
@tool
def my_tool(param: str) -> str:
    return f"Processed: {param}"
    
agent = Agent(tools=[my_tool])
```

### 🔄 Simple Workflows
```python
workflow = Workflow(name="pipeline")
workflow.add_steps([
    Step("research", agent=researcher),
    Step("write", agent=writer, depends_on=["research"])
])
```

### 📊 Built-in Observability
```python
from agenticraft import Telemetry

telemetry = Telemetry(export_to="http://localhost:4317")
agent = Agent(telemetry=telemetry)
```

## Getting Started

- **[5-Minute Quickstart](quickstart.md)**  
  Build your first agent faster than making coffee

- **[Core Concepts](concepts/agents.md)**  
  Understand the fundamentals

- **[API Reference](reference/index.md)**  
  Detailed documentation for every feature

- **[Examples](examples/index.md)**  
  Learn from real-world implementations

## Community

Join our growing community of developers building with AgentiCraft:

- **[Discord](https://discord.gg/agenticraft)** - Get help and share ideas
- **[GitHub](https://github.com/agenticraft/agenticraft)** - Contribute and star the project
- **[Blog](https://blog.agenticraft.ai)** - Latest updates and tutorials

## Ready to Build?

**[Get Started →](quickstart.md)** | **[View Examples →](examples/index.md)**
