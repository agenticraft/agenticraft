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
| `gpt-4-turbo-preview` | Faster, cheaper GPT-4 | 128K tokens | Balanced performance |
| `gpt-3.5-turbo` | Fast and efficient | 16K tokens | Simple tasks, high volume |
| `gpt-3.5-turbo-16k` | Extended context | 16K tokens | Longer conversations |

## ⚠️ Important: Parameter Configuration

**AgentiCraft currently does not support passing parameters in `run()` or `arun()` calls.** All parameters must be set during Agent initialization:

```python
# ❌ This will NOT work - causes "multiple values" error
agent = Agent(model="gpt-4")
response = await agent.arun("Hello", temperature=0.5)  # Error!

# ✅ This works - set parameters during initialization
agent = Agent(
    model="gpt-4",
    temperature=0.5,
    max_tokens=100
)
response = await agent.arun("Hello")  # Success!
```

## Provider-Specific Features

### Function Calling

OpenAI models support native function calling (Note: AgentiCraft recommends using the WorkflowAgent pattern for reliable tool usage):

```python
from agenticraft.agents import WorkflowAgent

# Create workflow agent for reliable tool usage
agent = WorkflowAgent(
    name="ToolUser",
    provider="openai",
    model="gpt-3.5-turbo"
)

# Define and register handlers
def calculate_handler(agent, step, context):
    expression = context.get("expression", "")
    try:
        result = eval(expression, {"__builtins__": {}})
        context["result"] = result
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

agent.register_handler("calc", calculate_handler)

# Use in workflow
workflow = agent.create_workflow("math")
workflow.add_step(name="calculate", handler="calc")
context = {"expression": "144 ** 0.5"}
result = await agent.execute_workflow(workflow, context=context)
```

### Streaming Responses (Coming in v0.2.0)

```python
# Note: Streaming support is coming soon
# This is how it will work:
# async for chunk in agent.stream("Tell me a story"):
#     print(chunk, end="", flush=True)
```

### Response Format

```python
# JSON mode (only with newer models)
agent = Agent(
    name="JSONBot",
    model="gpt-4-turbo-preview",
    response_format={"type": "json_object"}
)

response = await agent.arun("List 3 colors as JSON")
# Returns valid JSON
```

## Configuration Options

```python
# All parameters must be set during initialization
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
    seed=42,              # For reproducible outputs
    
    # Connection settings
    timeout=30,           # Request timeout in seconds
    max_retries=3        # Retry attempts
)
```

## Error Handling

```python
from agenticraft import Agent
from agenticraft.core.exceptions import ProviderError

try:
    agent = Agent(name="Bot", model="gpt-4")
    response = await agent.arun("Hello")
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
# Create different agents for different complexity levels
simple_agent = Agent(
    name="Simple",
    model="gpt-3.5-turbo",
    temperature=0.3,
    max_tokens=100
)

complex_agent = Agent(
    name="Complex", 
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000
)

# Use simple agent for basic tasks
response = await simple_agent.arun("What's 2+2?")

# Use complex agent for advanced tasks
response = await complex_agent.arun("Explain quantum mechanics")
```

### Token Usage Tracking

```python
response = await agent.arun("Generate a report")

# Access token usage from metadata
if hasattr(response, 'metadata') and response.metadata:
    usage = response.metadata.get("usage", {})
    print(f"Prompt tokens: {usage.get('prompt_tokens', 0)}")
    print(f"Completion tokens: {usage.get('completion_tokens', 0)}")
    print(f"Total tokens: {usage.get('total_tokens', 0)}")
```

## Common Issues and Solutions

### Issue: "multiple values for keyword argument"

**Problem**: Trying to pass parameters in `arun()` call
```python
# This causes an error
response = await agent.arun("Hello", temperature=0.5)
```

**Solution**: Set all parameters during Agent initialization
```python
agent = Agent(model="gpt-4", temperature=0.5)
response = await agent.arun("Hello")
```

### Issue: Timeout errors

**Solution**: Increase timeout during initialization
```python
agent = Agent(
    model="gpt-4",
    timeout=60  # Increase from default 30 seconds
)
```

### Issue: API key not found

**Solution**: Check environment variable or pass explicitly
```python
# Option 1: Set environment variable
# export OPENAI_API_KEY="sk-..."

# Option 2: Pass in initialization
agent = Agent(
    model="gpt-4",
    api_key="sk-..."
)
```

## Best Practices

1. **API Key Security**: Use environment variables, never hardcode keys
2. **Parameter Configuration**: Set all parameters during Agent initialization
3. **Model Selection**: Use GPT-3.5-Turbo for simple tasks, GPT-4 for complex ones
4. **Error Handling**: Always handle API errors gracefully
5. **Cost Management**: Monitor token usage and use appropriate models

## Complete Working Example

```python
import os
import asyncio
from agenticraft import Agent
from agenticraft.agents import WorkflowAgent

class OpenAIAssistant:
    def __init__(self):
        # Ensure API key is set
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")
        
        # Create agents for different tasks
        self.fast_agent = Agent(
            name="FastAssistant",
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=150
        )
        
        self.smart_agent = Agent(
            name="SmartAssistant",
            provider="openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Create workflow agent for tool usage
        self.tool_agent = WorkflowAgent(
            name="ToolAssistant",
            provider="openai",
            model="gpt-3.5-turbo"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up tool handlers for the workflow agent"""
        def calc_handler(agent, step, context):
            expr = context.get("expression", "")
            try:
                result = eval(expr, {"__builtins__": {}})
                return f"Result: {result}"
            except:
                return "Invalid expression"
        
        self.tool_agent.register_handler("calculate", calc_handler)
    
    async def quick_answer(self, question: str) -> str:
        """Use fast model for simple questions"""
        response = await self.fast_agent.arun(question)
        return response.content
    
    async def detailed_analysis(self, topic: str) -> str:
        """Use smart model for complex analysis"""
        prompt = f"Provide a detailed analysis of: {topic}"
        response = await self.smart_agent.arun(prompt)
        return response.content
    
    async def calculate(self, expression: str) -> str:
        """Use workflow agent for calculations"""
        workflow = self.tool_agent.create_workflow("calc")
        workflow.add_step(name="calc", handler="calculate")
        
        context = {"expression": expression}
        await self.tool_agent.execute_workflow(workflow, context=context)
        
        return context.get("result", "No result")

# Usage
async def main():
    assistant = OpenAIAssistant()
    
    # Quick answer
    answer = await assistant.quick_answer("What's the capital of France?")
    print(f"Quick: {answer}")
    
    # Detailed analysis
    analysis = await assistant.detailed_analysis("impact of AI on society")
    print(f"Analysis: {analysis[:200]}...")
    
    # Calculation
    result = await assistant.calculate("(100 * 15) / 3")
    print(f"Calculation: {result}")

asyncio.run(main())
```

## See Also

- [Agent API](../agent.md) - Core agent functionality
- [WorkflowAgent Guide](../../concepts/workflows.md) - Reliable tool usage
- [Provider Switching](../../features/provider_switching.md) - Dynamic provider changes
- [OpenAI API Docs](https://platform.openai.com/docs) - Official OpenAI documentation
