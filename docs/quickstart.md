# Quickstart Guide

Get up and running with AgentiCraft in 5 minutes!

## Installation

```bash
pip install agenticraft
```

## Your First Agent

```python
from agenticraft import Agent

# Create an agent
agent = Agent(name="Assistant")

# Run the agent
response = await agent.run("What is the capital of France?")
print(response)
```

## Adding Tools

```python
from agenticraft import Agent, Tool

# Create agent
agent = Agent("ToolAgent")

# Add built-in tools
agent.add_tool(Tool.Calculator())
agent.add_tool(Tool.WebSearch())

# Use tools
response = await agent.run("Calculate 15% tip on $85.50")
print(response)
```

## Creating Custom Tools

```python
from agenticraft import Tool

@Tool.create("weather")
async def get_weather(city: str) -> str:
    """Get weather for a city"""
    # Your implementation here
    return f"Sunny in {city}"

agent.add_tool(get_weather)
```

## Using Memory

```python
from agenticraft import ChatAgent

# Create chatbot with memory
chatbot = ChatAgent("MemoryBot", memory=True)

# Have a conversation
await chatbot.chat("My name is Alice")
await chatbot.chat("What's my name?")  # Will remember "Alice"
```

## Next Steps

- Explore [built-in tools](https://docs.agenticraft.ai/tools)
- Learn about [memory systems](https://docs.agenticraft.ai/memory)
- Build [custom plugins](https://docs.agenticraft.ai/plugins)
- Deploy to [production](https://docs.agenticraft.ai/deployment)
