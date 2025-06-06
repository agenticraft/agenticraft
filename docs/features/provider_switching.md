# Provider Switching Guide

## Overview

AgentiCraft v0.1.1 introduces dynamic provider switching, allowing agents to seamlessly switch between different LLM providers (OpenAI, Anthropic, Ollama) at runtime. This feature enables:

- **Cost optimization** by using appropriate models for different tasks
- **Failover resilience** with automatic fallback to alternative providers
- **Model comparison** for evaluating different LLMs on the same task
- **Local/cloud flexibility** by switching between cloud APIs and local models

## Quick Start

```python
from agenticraft import Agent

# Create an agent
agent = Agent(name="FlexibleAgent")

# NEW in v0.1.1: Explicit provider specification
agent = Agent(
    name="ClaudeAgent",
    provider="anthropic",  # Explicit provider
    model="claude-3-opus-20240229"
)

# Switch to different providers
agent.set_provider("anthropic", model="claude-3-opus-20240229")
agent.set_provider("ollama", model="llama2")
agent.set_provider("openai", model="gpt-3.5-turbo")
```

## Available Providers

### OpenAI
- **Models**: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`, `o1-preview`, `o1-mini`
- **Features**: Function calling, JSON mode, streaming
- **Setup**: Requires `OPENAI_API_KEY` environment variable

### Anthropic
- **Models**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`
- **Features**: Large context window, constitutional AI
- **Setup**: Requires `ANTHROPIC_API_KEY` environment variable

### Ollama (Local)
- **Models**: `llama2`, `mistral`, `codellama`, `gemma`, `phi`, and more
- **Features**: Local inference, no API costs, privacy
- **Setup**: Requires Ollama running locally (`ollama serve`)

## Basic Usage

### Simple Provider Switching

```python
from agenticraft import Agent

# Method 1: Auto-detection from model name (backward compatible)
agent = Agent(
    name="Assistant",
    model="gpt-4",  # Auto-detects OpenAI
    instructions="You are a helpful AI assistant."
)

# Method 2: Explicit provider specification (NEW in v0.1.1)
agent = Agent(
    name="Assistant",
    provider="openai",  # Explicit provider
    model="gpt-4",
    instructions="You are a helpful AI assistant."
)

# Benefits of explicit provider:
# - No ambiguity about which provider is used
# - Works with custom model names
# - Better for configuration files
# - Clearer intent in code

# Get current provider info
info = agent.get_provider_info()
print(f"Current provider: {info['provider']}")
print(f"Model: {info['model']}")

# Switch to Anthropic
agent.set_provider("anthropic", model="claude-3-sonnet-20240229")

# Switch to local Ollama
agent.set_provider("ollama", model="llama2", base_url="http://localhost:11434")

# List available providers
providers = agent.list_available_providers()
print(f"Available providers: {providers}")
```

### With Error Handling

```python
from agenticraft.core.exceptions import ProviderError

try:
    agent.set_provider("anthropic", model="claude-3-opus-20240229")
except ProviderError as e:
    print(f"Failed to switch provider: {e}")
    # Fallback to another provider
    agent.set_provider("openai", model="gpt-3.5-turbo")
```

## Advanced Patterns

### Cost-Optimized Agent

Use different models based on task complexity:

```python
class SmartAgent:
    def __init__(self):
        self.agent = Agent(name="SmartAgent")
    
    def estimate_complexity(self, prompt: str) -> str:
        # Simple heuristic
        if len(prompt.split()) > 50 or "analyze" in prompt.lower():
            return "high"
        elif len(prompt.split()) < 10:
            return "low"
        return "medium"
    
    async def run(self, prompt: str) -> str:
        complexity = self.estimate_complexity(prompt)
        
        if complexity == "high":
            self.agent.set_provider("anthropic", model="claude-3-opus-20240229")
        elif complexity == "low":
            self.agent.set_provider("openai", model="gpt-3.5-turbo")
        else:
            self.agent.set_provider("openai", model="gpt-4")
        
        response = await self.agent.arun(prompt)
        return response.content
```

### Resilient Agent with Failover

Automatically failover to backup providers:

```python
class ResilientAgent:
    def __init__(self):
        self.agent = Agent(name="ResilientAgent")
        self.providers = [
            ("openai", "gpt-4"),
            ("anthropic", "claude-3-sonnet-20240229"),
            ("ollama", "llama2"),
        ]
    
    async def run(self, prompt: str) -> str:
        for provider, model in self.providers:
            try:
                self.agent.set_provider(provider, model=model)
                response = await self.agent.arun(prompt)
                return response.content
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                continue
        
        raise Exception("All providers failed")
```

### Model Comparison

Compare responses from different models:

```python
async def compare_models(prompt: str):
    agent = Agent(name="Comparator")
    models = [
        ("openai", "gpt-4"),
        ("anthropic", "claude-3-opus-20240229"),
        ("ollama", "llama2"),
    ]
    
    results = {}
    for provider, model in models:
        try:
            agent.set_provider(provider, model=model)
            response = await agent.arun(prompt)
            results[f"{provider}/{model}"] = response.content
        except Exception as e:
            results[f"{provider}/{model}"] = f"Error: {e}"
    
    return results
```

## Provider-Specific Features

### OpenAI

```python
# JSON response format
response = await agent.arun(
    "List 3 colors",
    response_format={"type": "json_object"}
)

# Streaming (when implemented)
async for chunk in agent.astream("Tell me a story"):
    print(chunk, end="")
```

### Anthropic

```python
# Anthropic handles system messages differently
agent.config.instructions = "You are Claude, created by Anthropic."
agent.set_provider("anthropic")

# Larger context window
response = await agent.arun(very_long_prompt)  # Up to 200k tokens
```

### Ollama

```python
# Local model with custom parameters
agent.set_provider("ollama", model="llama2")

response = await agent.arun(
    "Generate text",
    temperature=0.9,
    seed=42,  # Reproducible generation
    num_predict=200  # Max tokens
)
```

## Configuration Options

### Using Provider Parameter

The `provider` parameter in AgentConfig allows explicit provider specification:

```python
# Explicit provider specification
agent = Agent(
    name="MyAgent",
    provider="anthropic",  # Explicit provider
    model="claude-3-opus-20240229"
)

# From configuration dictionary
config = {
    "name": "ConfigAgent",
    "provider": "ollama",
    "model": "llama2",
    "base_url": "http://localhost:11434",
    "temperature": 0.7
}
agent = Agent(**config)

# Provider validation
try:
    agent = Agent(provider="invalid_provider")  # Raises ValueError
except ValueError as e:
    print(f"Error: {e}")
```

### Environment-Based Configuration

```python
import os

# Read from environment
provider = os.getenv("AGENT_PROVIDER", "openai")
model = os.getenv("AGENT_MODEL", "gpt-4")

agent = Agent(
    name="EnvAgent",
    provider=provider,
    model=model
)
```

## What's Preserved When Switching

When you switch providers, the following are preserved:

- ✅ **Agent configuration**: name, instructions, temperature, max_tokens
- ✅ **Tools**: All registered tools remain available
- ✅ **Memory**: Conversation history and memory stores
- ✅ **Reasoning patterns**: The agent's reasoning approach
- ✅ **Agent ID**: The unique identifier remains the same

What changes:

- ❌ **Model**: Updates to the new provider's model
- ❌ **API credentials**: Uses the new provider's credentials
- ❌ **Provider client**: A new provider instance is created

## Performance Considerations

### Provider Latency

Typical response times (approximate):

- **OpenAI GPT-3.5**: 0.5-2 seconds
- **OpenAI GPT-4**: 2-10 seconds
- **Anthropic Claude**: 1-5 seconds
- **Ollama (local)**: 0.1-5 seconds (depends on hardware)

### Switching Overhead

Provider switching is lightweight:
- Creating new provider instance: ~1ms
- Validating credentials: ~10ms
- Total switch time: <50ms

### Best Practices

1. **Cache provider instances** if switching frequently:
   ```python
   # Future enhancement - provider pooling
   provider_pool = {
       "openai": OpenAIProvider(...),
       "anthropic": AnthropicProvider(...)
   }
   ```

2. **Use appropriate models** for tasks:
   - Simple queries: `gpt-3.5-turbo`, `claude-3-haiku`
   - Complex reasoning: `gpt-4`, `claude-3-opus`
   - Local/private: `ollama/llama2`, `ollama/mistral`

3. **Handle provider differences**:
   - Test tools with each provider
   - Be aware of token limits
   - Consider response format variations

## Troubleshooting

### Common Issues

**Provider not found:**
```python
ProviderError: Unknown provider: xyz
```
Solution: Check available providers with `agent.list_available_providers()`

**Authentication failed:**
```python
ProviderAuthError: Missing API key for anthropic
```
Solution: Set environment variable `ANTHROPIC_API_KEY`

**Ollama connection failed:**
```python
ProviderError: Cannot connect to Ollama
```
Solution: Ensure Ollama is running: `ollama serve`

**Model not available:**
```python
ProviderError: Model 'gpt-5' not found
```
Solution: Check supported models for each provider

### Debug Logging

Enable debug logging to troubleshoot:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now provider switches will be logged
agent.set_provider("anthropic")
# Logs: "Agent 'Assistant' switched to anthropic (model: claude-3-opus-20240229)"
```

## Future Enhancements

Planned improvements for future versions:

- **Provider pooling**: Reuse provider instances
- **Automatic model selection**: Choose optimal model based on task
- **Cost tracking**: Monitor spending across providers
- **Performance metrics**: Compare provider response times
- **Streaming support**: Unified streaming interface
- **Provider profiles**: Save and load provider configurations

## Examples

See the `examples/provider_switching/` directory for complete examples:

- `basic_switching.py`: Simple provider switching examples
- `cost_optimization.py`: Optimize costs with smart provider selection
- `provider_failover.py`: Build resilient agents with automatic failover

## API Reference

### Agent.set_provider()

```python
def set_provider(
    self, 
    provider_name: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Switch the agent's LLM provider dynamically.
    
    Args:
        provider_name: Name of the provider ("openai", "anthropic", "ollama")
        model: Optional model override for the new provider
        api_key: Optional API key for the new provider
        base_url: Optional base URL (mainly for Ollama)
        **kwargs: Additional provider-specific parameters
        
    Raises:
        ProviderError: If the provider name is invalid or setup fails
    """
```

### Agent.get_provider_info()

```python
def get_provider_info(self) -> Dict[str, Any]:
    """
    Get information about the current provider.
    
    Returns:
        Dict containing provider name, model, and capabilities
    """
```

### Agent.list_available_providers()

```python
def list_available_providers(self) -> List[str]:
    """
    List available LLM providers.
    
    Returns:
        List of provider names that can be used with set_provider
    """
```
