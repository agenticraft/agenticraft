# Agents

Agents are the core building blocks of AgentiCraft. An agent is an AI-powered entity that can reason, use tools, and maintain memory.

## What is an Agent?

An agent in AgentiCraft consists of:

- **Identity**: Name and instructions that define its purpose
- **Reasoning**: Transparent thought processes
- **Tools**: Capabilities it can use
- **Memory**: Context it maintains
- **Provider**: The LLM that powers it

## Creating Agents

### Basic Agent

```python
from agenticraft import Agent

agent = Agent(
    name="Assistant",
    instructions="You are a helpful AI assistant."
)
```

### Agent with Tools

```python
from agenticraft import Agent, tool

@tool
def search(query: str) -> str:
    """Search for information."""
    # Implementation here
    return f"Results for: {query}"

agent = Agent(
    name="Researcher",
    instructions="You help with research tasks.",
    tools=[search]
)
```

### Agent with Memory

```python
from agenticraft import Agent, ConversationMemory

agent = Agent(
    name="ChatBot",
    instructions="You are a conversational assistant.",
    memory=[ConversationMemory(max_turns=10)]
)
```

## Agent Configuration

```python
agent = Agent(
    name="Advanced",
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000,
    timeout=30,
    max_retries=3
)
```

## Using Agents

### Synchronous Usage

```python
response = agent.run("Your prompt here")
print(response.content)
print(response.reasoning)
```

### Asynchronous Usage

```python
response = await agent.arun("Your prompt here")
```

## Understanding Agent Responses

Every agent response includes:

- `content`: The final response
- `reasoning`: The thought process
- `tool_calls`: Any tools used
- `usage`: Token usage information

## Best Practices

1. **Clear Instructions**: Be specific about the agent's role
2. **Appropriate Tools**: Only include necessary tools
3. **Memory Management**: Use memory judiciously
4. **Error Handling**: Always handle potential errors

## Next Steps

- Learn about [Tools](tools.md)
- Explore [Workflows](workflows.md)
- Understand [Memory](memory.md)
