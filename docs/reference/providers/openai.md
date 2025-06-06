# OpenAI Provider Reference

The OpenAI provider supports GPT-4, GPT-3.5, and other OpenAI models.

## Configuration

### Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_ORG_ID="org-..."  # Optional
```

### Initialization

```python
from agenticraft import Agent

# Auto-detection from model name
agent = Agent(name="GPT", model="gpt-4")

# Explicit provider
agent = Agent(
    name="GPT",
    provider="openai",
    model="gpt-4",
    api_key="sk-..."  # Optional, uses env var if not provided
)
```

## Supported Models

| Model | Description | Context Window | Best For |
|-------|-------------|----------------|----------|
| `gpt-4` | Most capable model | 8K tokens | Complex reasoning, analysis |
| `gpt-4-32k` | Extended context | 32K tokens | Long documents |
| `gpt-4-turbo` | Faster, cheaper GPT-4 | 128K tokens | Balanced performance |
| `gpt-3.5-turbo` | Fast and efficient | 16K tokens | Simple tasks, high volume |
| `gpt-3.5-turbo-16k` | Extended context | 16K tokens | Longer conversations |

## Provider-Specific Features

### Function Calling

OpenAI models support native function calling:

```python
from agenticraft import Agent, tool

@tool
def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 72°F"

agent = Agent(
    name="Assistant",
    model="gpt-4",
    tools=[get_weather]
)

# OpenAI automatically handles function calling
response = agent.run("What's the weather in NYC?")
```

### Streaming Responses

```python
agent = Agent(
    name="Streamer",
    model="gpt-4",
    stream=True
)

for chunk in agent.run_stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

### Response Format

```python
# JSON mode
agent = Agent(
    name="JSONBot",
    model="gpt-4-turbo",
    response_format={"type": "json_object"}
)

response = agent.run("List 3 colors as JSON")
# Returns valid JSON
```

### Vision Capabilities

```python
# GPT-4 Vision
agent = Agent(
    name="VisionBot",
    model="gpt-4-vision-preview"
)

response = agent.run(
    prompt="What's in this image?",
    images=["path/to/image.jpg"]
)
```

## Configuration Options

```python
agent = Agent(
    name="Configured",
    provider="openai",
    model="gpt-4",
    
    # OpenAI-specific options
    temperature=0.7,        # 0.0-2.0
    max_tokens=2000,       # Max response length
    top_p=1.0,            # Nucleus sampling
    frequency_penalty=0.0, # -2.0 to 2.0
    presence_penalty=0.0,  # -2.0 to 2.0
    stop=["\n\n"],        # Stop sequences
    n=1,                  # Number of completions
    logprobs=True,        # Include log probabilities
    
    # Retry configuration
    max_retries=3,
    timeout=30
)
```

## Error Handling

```python
from agenticraft import Agent, ProviderError

try:
    agent = Agent(name="Bot", model="gpt-4")
    response = agent.run("Hello")
except ProviderError as e:
    if "rate_limit" in str(e):
        print("Rate limit reached, waiting...")
    elif "api_key" in str(e):
        print("Invalid API key")
    else:
        print(f"OpenAI error: {e}")
```

## Cost Optimization

### Model Selection by Task

```python
class SmartAssistant:
    def __init__(self):
        self.agent = Agent(name="Smart", model="gpt-3.5-turbo")
    
    def process(self, task: str, complexity: str):
        if complexity == "high":
            self.agent.model = "gpt-4"
        elif complexity == "medium":
            self.agent.model = "gpt-4-turbo"
        else:
            self.agent.model = "gpt-3.5-turbo"
        
        return self.agent.run(task)
```

### Token Usage Tracking

```python
response = agent.run("Generate a report")

# Access token usage
tokens = response.metadata.get("usage", {})
print(f"Prompt tokens: {tokens.get('prompt_tokens')}")
print(f"Completion tokens: {tokens.get('completion_tokens')}")
print(f"Total tokens: {tokens.get('total_tokens')}")
```

## Best Practices

1. **API Key Security**: Use environment variables, never hardcode keys
2. **Rate Limiting**: Implement exponential backoff for retries
3. **Context Management**: Monitor token usage to stay within limits
4. **Model Selection**: Use GPT-3.5-Turbo for simple tasks, GPT-4 for complex ones
5. **Error Handling**: Always handle API errors gracefully

## Complete Example

```python
import os
from agenticraft import Agent, tool
from typing import List

class OpenAIAssistant:
    def __init__(self):
        # Ensure API key is set
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")
        
        # Create agent with optimal settings
        self.agent = Agent(
            name="OpenAIAssistant",
            provider="openai",
            model="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            tools=self._create_tools()
        )
    
    def _create_tools(self) -> List:
        @tool
        def search_docs(query: str) -> str:
            """Search internal documentation."""
            # Implementation
            return f"Found docs about: {query}"
        
        @tool
        def calculate(expression: str) -> str:
            """Perform calculations."""
            try:
                result = eval(expression, {"__builtins__": {}})
                return str(result)
            except:
                return "Invalid expression"
        
        return [search_docs, calculate]
    
    def chat(self, message: str) -> str:
        """Process a chat message."""
        try:
            response = self.agent.run(message)
            
            # Track usage for cost monitoring
            usage = response.metadata.get("usage", {})
            self._log_usage(usage)
            
            return response.content
            
        except ProviderError as e:
            # Handle specific errors
            if "rate_limit" in str(e):
                # Switch to cached responses or queue
                return "I'm a bit busy right now, please try again in a moment."
            raise
    
    def _log_usage(self, usage: dict):
        """Log token usage for monitoring."""
        total = usage.get("total_tokens", 0)
        cost = self._estimate_cost(total)
        print(f"Tokens: {total}, Est. cost: ${cost:.4f}")
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on current pricing."""
        # GPT-4-Turbo pricing (example)
        return (tokens / 1000) * 0.01

# Usage
assistant = OpenAIAssistant()
response = assistant.chat("Help me analyze this data and create a chart")
print(response)
```

## See Also

- [Agent API](../agent.md) - Core agent functionality
- [Provider Switching](../../features/provider_switching.md) - Dynamic provider changes
- [OpenAI API Docs](https://platform.openai.com/docs) - Official OpenAI documentation
