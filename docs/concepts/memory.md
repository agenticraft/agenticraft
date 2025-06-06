# Memory

AgentiCraft provides flexible memory systems that allow agents to maintain context and learn from interactions.

## Memory Types

### Conversation Memory
Short-term memory for maintaining context within a conversation:

```python
from agenticraft import Agent

# Enable conversation memory
agent = Agent(
    name="MemoryBot",
    model="gpt-4",
    memory_enabled=True
)

# The agent remembers context
agent.run("My name is Alice")
response = agent.run("What's my name?")  # Remembers "Alice"
```

### Knowledge Memory
Long-term storage for facts and information:

```python
from agenticraft import Agent, KnowledgeMemory

# Create agent with knowledge memory
knowledge = KnowledgeMemory()
agent = Agent(
    name="KnowledgeBot",
    model="gpt-4",
    knowledge_memory=knowledge
)

# Store facts
agent.remember("The speed of light is 299,792,458 m/s")
agent.remember("Water boils at 100°C at sea level")

# Retrieve later
response = agent.run("What's the speed of light?")
```

## Memory Features

### Context Window Management
Automatically manages conversation history to fit within model limits:

```python
agent = Agent(
    name="SmartBot",
    memory_enabled=True,
    memory_config={
        "max_messages": 20,
        "summarize_after": 15,
        "compression_model": "gpt-3.5-turbo"
    }
)
```

### Semantic Search
Find relevant memories based on meaning:

```python
# Store various facts
agent.remember("Python was created by Guido van Rossum")
agent.remember("JavaScript was created by Brendan Eich")

# Semantic search
facts = agent.recall("programming language creators")
# Returns relevant memories
```

### Memory Persistence
Save and load memory across sessions:

```python
# Save memory to disk
agent.save_memory("bot_memory.json")

# Load in a new session
new_agent = Agent(name="Bot", memory_enabled=True)
new_agent.load_memory("bot_memory.json")
```

## Advanced Memory Patterns

### Episodic Memory
Remember specific interactions:

```python
agent = Agent(
    name="EpisodicBot",
    memory_config={
        "type": "episodic",
        "remember_interactions": True,
        "interaction_limit": 100
    }
)
```

### Working Memory
Temporary storage for complex tasks:

```python
# Agent uses working memory during problem-solving
agent.run("Let's solve this step by step...")
# Automatically maintains intermediate results
```

## Memory Best Practices

1. **Choose the Right Type**: Use conversation memory for chat, knowledge memory for facts
2. **Set Appropriate Limits**: Balance memory size with performance
3. **Regular Cleanup**: Remove outdated or irrelevant memories
4. **Privacy Considerations**: Be mindful of what information is stored
5. **Backup Important Data**: Persist critical memories to disk

## Memory with Provider Switching

Memory persists across provider switches:

```python
agent = Agent(name="Bot", memory_enabled=True)

# Chat with GPT-4
agent.run("Remember that my favorite color is blue")

# Switch providers
agent.set_provider("anthropic", model="claude-3-opus-20240229")

# Memory persists
response = agent.run("What's my favorite color?")  # Still remembers "blue"
```

## Next Steps

- [Learn about agents](agents.md)
- [Explore reasoning systems](reasoning.md)
- [Build memory-enabled agents](../getting-started/first-agent.md)
