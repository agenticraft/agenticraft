# Configuration

AgentiCraft is designed to work out of the box with minimal configuration. However, understanding the configuration options will help you avoid common pitfalls.

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
    max_tokens=2000,
    timeout=60  # Important for avoiding timeouts!
)
agent = Agent(config=config)
```

## ⚠️ Important: Parameter Configuration

**AgentiCraft does not support passing parameters in `run()` or `arun()` method calls.** All parameters must be set during Agent initialization:

```python
# ❌ This will NOT work - causes "multiple values" error
agent = Agent(model="gpt-4")
response = await agent.arun("Hello", temperature=0.5)  # Error!

# ✅ This works - set parameters during initialization
agent = Agent(
    model="gpt-4",
    temperature=0.5
)
response = await agent.arun("Hello")  # Success!
```

## Environment Variables

Create a `.env` file in your project root:

```bash
# OpenAI
OPENAI_API_KEY="sk-..."

# Anthropic
ANTHROPIC_API_KEY="sk-ant-..."

# Ollama (local)
OLLAMA_HOST="http://localhost:11434"
```

Then load in your code:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Provider-Specific Configuration

### OpenAI
```python
agent = Agent(
    name="GPTAgent",
    provider="openai",  # Optional, auto-detected
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    timeout=30  # Default is usually fine
)
```

### Anthropic
```python
# ⚠️ Always specify model with Anthropic!
agent = Agent(
    name="ClaudeAgent", 
    provider="anthropic",
    model="claude-3-opus-20240229",  # Required!
    max_tokens=4000,
    temperature=0.7,
    timeout=60  # Increase for complex tasks
)
```

### Ollama (Local Models)
```python
# ⚠️ Always set timeout for Ollama!
agent = Agent(
    name="LocalAgent",
    provider="ollama",
    model="llama2",  # or "llama2:latest"
    temperature=0.8,
    max_tokens=200,  # Limit for faster responses
    timeout=180      # Essential for CPU inference!
)
```

## Common Configuration Patterns

### Different Agents for Different Tasks

```python
# Fast agent for simple queries
fast_agent = Agent(
    name="QuickBot",
    model="gpt-3.5-turbo",  # or "claude-3-haiku-20240307"
    temperature=0.3,
    max_tokens=100,
    timeout=30
)

# Smart agent for complex tasks
smart_agent = Agent(
    name="DeepThinker",
    model="gpt-4",  # or "claude-3-opus-20240229"
    temperature=0.7,
    max_tokens=2000,
    timeout=60
)

# Local agent for privacy
local_agent = Agent(
    name="PrivateBot",
    provider="ollama",
    model="llama2",
    temperature=0.7,
    max_tokens=500,
    timeout=300  # Longer timeout for local models
)
```

### Timeout Configuration Guide

| Provider | Model Type | Recommended Timeout |
|----------|-----------|-------------------|
| OpenAI | GPT-3.5 | 30s (default) |
| OpenAI | GPT-4 | 60s |
| Anthropic | Haiku | 30s |
| Anthropic | Sonnet | 60s |
| Anthropic | Opus | 120s |
| Ollama | Any (CPU) | 180-300s |
| Ollama | Any (GPU) | 60-120s |

## Error Prevention

### 1. Anthropic Model Specification
```python
# ❌ Don't do this
agent = Agent(provider="anthropic")  # Uses default gpt-4!

# ✅ Do this
agent = Agent(
    provider="anthropic",
    model="claude-3-haiku-20240307"
)
```

### 2. Ollama Timeout Configuration
```python
# ❌ Don't do this
agent = Agent(provider="ollama", model="llama2")  # May timeout

# ✅ Do this
agent = Agent(
    provider="ollama",
    model="llama2",
    timeout=180,
    max_tokens=200
)
```

### 3. Parameter Setting
```python
# ❌ Don't do this
agent = Agent(model="gpt-4")
response = agent.run("Hello", temperature=0.5)  # Runtime params not supported

# ✅ Do this
agent = Agent(model="gpt-4", temperature=0.5)
response = agent.run("Hello")
```

## Configuration Best Practices

1. **Set parameters during initialization** - Never in `run()` calls
2. **Always specify model for Anthropic** - Don't rely on defaults
3. **Set appropriate timeouts** - Especially for Ollama and complex tasks
4. **Use environment variables** - For API keys and sensitive data
5. **Create task-specific agents** - Different configs for different needs

## Full Configuration Example

```python
import os
from dotenv import load_dotenv
from agenticraft import Agent

# Load environment variables
load_dotenv()

class AssistantConfig:
    """Centralized configuration for different agents"""
    
    @staticmethod
    def create_fast_agent():
        """Quick responses for simple tasks"""
        return Agent(
            name="FastAssistant",
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=150,
            timeout=30
        )
    
    @staticmethod
    def create_smart_agent():
        """Complex reasoning and analysis"""
        return Agent(
            name="SmartAssistant",
            provider="anthropic",
            model="claude-3-opus-20240229",
            temperature=0.7,
            max_tokens=4000,
            timeout=120
        )
    
    @staticmethod
    def create_local_agent():
        """Private, local processing"""
        return Agent(
            name="LocalAssistant",
            provider="ollama",
            model="llama2",
            temperature=0.7,
            max_tokens=300,
            timeout=240  # 4 minutes for CPU
        )
    
    @staticmethod
    def create_code_agent():
        """Specialized for code generation"""
        return Agent(
            name="CodeAssistant",
            model="gpt-4",
            temperature=0.2,
            max_tokens=2000,
            timeout=60,
            instructions="You are an expert programmer. Write clean, efficient code."
        )

# Usage
config = AssistantConfig()
fast = config.create_fast_agent()
smart = config.create_smart_agent()
local = config.create_local_agent()
coder = config.create_code_agent()
```

## Troubleshooting Configuration Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| "multiple values for keyword" | Error when calling `run()` | Set all params during Agent init |
| "model: gpt-4" with Anthropic | Wrong model error | Always specify Claude model |
| Timeout with Ollama | Request hangs | Increase timeout to 180-300s |
| Missing API key | Auth error | Check environment variables |

## Next Steps

- [Create your first agent](first-agent.md) - Build your first agent
- [Provider Reference](../reference/providers/) - Detailed provider docs
- [Best Practices](../guides/performance-tuning.md) - Optimization tips
