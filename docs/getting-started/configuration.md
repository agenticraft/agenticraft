# Configuration

AgentiCraft is designed to work out of the box with minimal configuration.

## Basic Configuration

```python
from agenticraft import Agent, AgentConfig

# Simple configuration
agent = Agent(
    name="MyAgent",
    model="gpt-4",
    provider="openai"  # Optional - auto-detected from model
)

# Advanced configuration
config = AgentConfig(
    name="AdvancedAgent",
    model="claude-3-opus-20240229",
    provider="anthropic",
    temperature=0.7,
    max_tokens=2000
)
agent = Agent(config=config)
```

## Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"

# Anthropic
export ANTHROPIC_API_KEY="your-key-here"

# Ollama (local)
export OLLAMA_HOST="http://localhost:11434"
```

## Provider Configuration

Each provider has specific configuration options:

### OpenAI
```python
agent = Agent(
    name="GPTAgent",
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000
)
```

### Anthropic
```python
agent = Agent(
    name="ClaudeAgent", 
    provider="anthropic",
    model="claude-3-opus-20240229",
    max_tokens=4000
)
```

### Ollama
```python
agent = Agent(
    name="LocalAgent",
    provider="ollama",
    model="llama2",
    temperature=0.8
)
```

## Next Steps

- [Create your first agent](first-agent.md)
- [Learn about provider switching](../features/provider_switching.md)
