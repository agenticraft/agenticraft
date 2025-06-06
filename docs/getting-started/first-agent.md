# Your First Agent

Let's create your first AI agent with AgentiCraft in just a few lines of code.

## Basic Agent

```python
from agenticraft import Agent

# Create an agent
agent = Agent(name="Assistant", model="gpt-4")

# Have a conversation
response = agent.run("Hello! What can you help me with today?")
print(response)
```

## Agent with Tools

```python
from agenticraft import Agent, tool

@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

# Create agent with tools
agent = Agent(
    name="MathBot",
    model="gpt-4",
    tools=[calculate]
)

response = agent.run("What's 42 * 17?")
print(response)
```

## Agent with Memory

```python
from agenticraft import Agent

# Agent with conversation memory
agent = Agent(
    name="MemoryBot",
    model="gpt-4",
    memory_enabled=True
)

# First interaction
agent.run("My name is Alice")

# Agent remembers context
response = agent.run("What's my name?")
print(response)  # Will remember "Alice"
```

## Provider Switching

```python
from agenticraft import Agent

# Start with GPT-4
agent = Agent(name="FlexBot", model="gpt-4")
response = agent.run("Write a haiku")

# Switch to Claude
agent.set_provider("anthropic", model="claude-3-opus-20240229")
response = agent.run("Write another haiku")

# Switch to local Ollama
agent.set_provider("ollama", model="llama2")
response = agent.run("One more haiku")
```

## Next Steps

- [Explore advanced agents](../features/advanced_agents.md)
- [Learn about tools](../concepts/tools.md)
- [Build workflows](../concepts/workflows.md)
