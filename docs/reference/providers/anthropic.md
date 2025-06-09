# Anthropic Provider Reference

The Anthropic provider supports Claude 3 models including Opus, Sonnet, and Haiku.

## Configuration

### Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Initialization

```python
from agenticraft import Agent

# IMPORTANT: Always specify model when using Anthropic provider
agent = Agent(
    name="Claude",
    provider="anthropic",
    model="claude-3-opus-20240229"  # Required!
)
```

## Supported Models

| Model | Description | Context Window | Best For |
|-------|-------------|----------------|----------|
| `claude-3-opus-20240229` | Most capable | 200K tokens | Complex analysis, reasoning |
| `claude-3-sonnet-20240229` | Balanced performance | 200K tokens | General tasks |
| `claude-3-haiku-20240307` | Fast and efficient | 200K tokens | High-volume, simple tasks |

## ⚠️ Important: Parameter Configuration

**AgentiCraft currently does not support passing parameters in `run()` or `arun()` calls.** All parameters must be set during Agent initialization:

```python
# ❌ This will NOT work - causes "multiple values" error
agent = Agent(provider="anthropic", model="claude-3-opus-20240229")
response = await agent.arun("Hello", temperature=0.5)  # Error!

# ✅ This works - set parameters during initialization
agent = Agent(
    provider="anthropic",
    model="claude-3-opus-20240229",
    temperature=0.5,
    max_tokens=100
)
response = await agent.arun("Hello")  # Success!
```

## ⚠️ Model Specification Required

Unlike OpenAI, the Anthropic provider requires explicit model specification:

```python
# ❌ This will fail with "model: gpt-4" error
agent = Agent(
    provider="anthropic"
    # No model specified - defaults to gpt-4!
)

# ✅ Always specify a Claude model
agent = Agent(
    provider="anthropic",
    model="claude-3-haiku-20240307"
)
```

## Provider-Specific Features

### Constitutional AI

Claude models are trained with Constitutional AI for helpful, harmless, and honest responses:

```python
agent = Agent(
    name="SafeAssistant",
    provider="anthropic",
    model="claude-3-opus-20240229",
    instructions="You are a helpful, harmless, and honest assistant."
)
```

### Large Context Window

Claude excels at processing long documents (up to 200K tokens):

```python
agent = Agent(
    name="DocumentAnalyzer",
    provider="anthropic", 
    model="claude-3-opus-20240229",
    timeout=120  # Increase timeout for long documents
)

# Process a long document
with open("long_document.txt", "r") as f:
    document = f.read()

response = await agent.arun(f"Analyze this document:\n\n{document}")
```

### XML Tags Support

Claude works exceptionally well with structured prompts using XML tags:

```python
prompt = """
<document>
{document_content}
</document>

<instructions>
1. Summarize the key points
2. Identify any risks
3. Suggest next steps
</instructions>

Please analyze the document according to the instructions.
"""

response = await agent.arun(prompt)
```

### Tool Usage with WorkflowAgent

For reliable tool usage, use the WorkflowAgent pattern:

```python
from agenticraft.agents import WorkflowAgent

# Create workflow agent
agent = WorkflowAgent(
    name="ClaudeTools",
    provider="anthropic",
    model="claude-3-haiku-20240307",  # Fast model for tools
    temperature=0.3
)

# Define handlers
def calculate_handler(agent, step, context):
    expr = context.get("expression", "")
    try:
        result = eval(expr, {"__builtins__": {}})
        context["result"] = result
        return f"Calculated: {result}"
    except Exception as e:
        return f"Error: {e}"

agent.register_handler("calc", calculate_handler)

# Use in workflow
workflow = agent.create_workflow("math")
workflow.add_step(name="calculate", handler="calc")
context = {"expression": "850 * 0.15"}
result = await agent.execute_workflow(workflow, context=context)
```

## Configuration Options

```python
# All parameters must be set during initialization
agent = Agent(
    name="ConfiguredClaude",
    provider="anthropic",
    model="claude-3-opus-20240229",  # Always required
    
    # Anthropic-specific options
    temperature=0.7,        # 0.0-1.0
    max_tokens=4000,       # Max response length
    top_p=0.9,            # Nucleus sampling
    top_k=0,              # Top-k sampling (0 = disabled)
    stop=["\n\nHuman:"],  # Stop sequences
    
    # Connection settings
    timeout=60,           # Increase for complex tasks
    max_retries=3        # Retry attempts
)
```

## Error Handling

```python
from agenticraft import Agent
from agenticraft.core.exceptions import ProviderError

try:
    agent = Agent(
        name="Claude",
        provider="anthropic",
        model="claude-3-opus-20240229"
    )
    response = await agent.arun("Hello")
except ProviderError as e:
    error_msg = str(e)
    if "rate_limit" in error_msg:
        print("Rate limit reached")
    elif "not_found_error" in error_msg and "model" in error_msg:
        print("Model specification error - check model name")
    elif "invalid_api_key" in error_msg:
        print("Check your Anthropic API key")
    elif "Request timed out" in error_msg:
        print("Timeout - try increasing timeout parameter")
    else:
        print(f"Anthropic error: {e}")
```

## Common Issues and Solutions

### Issue: "model: gpt-4" error

**Problem**: Not specifying a model defaults to GPT-4
```python
agent = Agent(provider="anthropic")  # Uses gpt-4 by default!
```

**Solution**: Always specify a Claude model
```python
agent = Agent(
    provider="anthropic",
    model="claude-3-haiku-20240307"
)
```

### Issue: Request timeouts

**Problem**: Default timeout too short for complex requests

**Solution**: Increase timeout and/or use faster model
```python
# For simple tasks - use Haiku with shorter timeout
simple_agent = Agent(
    provider="anthropic",
    model="claude-3-haiku-20240307",
    timeout=30
)

# For complex tasks - use Opus with longer timeout
complex_agent = Agent(
    provider="anthropic",
    model="claude-3-opus-20240229",
    timeout=120
)
```

### Issue: "multiple values for keyword argument"

**Problem**: Trying to pass parameters in `arun()` call

**Solution**: Set all parameters during initialization
```python
agent = Agent(
    provider="anthropic",
    model="claude-3-sonnet-20240229",
    temperature=0.5,
    max_tokens=1000
)
```

## Cost Optimization

### Model Selection Strategy

```python
# Use different models for different tasks
class ClaudeOptimizer:
    def __init__(self):
        # Haiku for simple/fast tasks
        self.fast_agent = Agent(
            provider="anthropic",
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=200,
            timeout=30
        )
        
        # Sonnet for balanced tasks
        self.balanced_agent = Agent(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            temperature=0.7,
            max_tokens=1000,
            timeout=60
        )
        
        # Opus for complex tasks
        self.smart_agent = Agent(
            provider="anthropic",
            model="claude-3-opus-20240229",
            temperature=0.7,
            max_tokens=4000,
            timeout=120
        )
    
    async def process(self, task: str, complexity: str):
        if complexity == "simple":
            return await self.fast_agent.arun(task)
        elif complexity == "medium":
            return await self.balanced_agent.arun(task)
        else:
            return await self.smart_agent.arun(task)
```

## Best Practices

1. **Always specify model**: Never rely on defaults with Anthropic provider
2. **Model selection**: Use Haiku for speed, Opus for quality, Sonnet for balance
3. **Timeout configuration**: Set appropriate timeouts (30-120 seconds)
4. **Parameter configuration**: Set all parameters during initialization
5. **XML tags**: Use XML tags for structured prompts with Claude
6. **Error handling**: Handle timeout and model specification errors

## Complete Working Example

```python
import os
import asyncio
from agenticraft import Agent
from agenticraft.agents import WorkflowAgent

class ClaudeAssistant:
    def __init__(self):
        # Ensure API key is set
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        # Create agents for different purposes
        self.chat_agent = Agent(
            name="ChatClaude",
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            temperature=0.7,
            max_tokens=1000,
            timeout=60
        )
        
        self.analyst_agent = Agent(
            name="AnalystClaude",
            provider="anthropic",
            model="claude-3-opus-20240229",
            temperature=0.3,
            max_tokens=4000,
            timeout=120,
            instructions="You are an expert analyst. Think step by step."
        )
        
        self.quick_agent = Agent(
            name="QuickClaude",
            provider="anthropic",
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=200,
            timeout=30
        )
    
    async def chat(self, message: str) -> str:
        """General conversation"""
        try:
            response = await self.chat_agent.arun(message)
            return response.content
        except Exception as e:
            return f"Chat error: {e}"
    
    async def analyze(self, document: str, instructions: str) -> str:
        """Complex document analysis"""
        prompt = f"""
        <document>
        {document}
        </document>
        
        <analysis_instructions>
        {instructions}
        </analysis_instructions>
        
        Please provide a thorough analysis following the instructions.
        """
        
        try:
            response = await self.analyst_agent.arun(prompt)
            return response.content
        except Exception as e:
            return f"Analysis error: {e}"
    
    async def quick_task(self, task: str) -> str:
        """Quick, simple tasks"""
        try:
            response = await self.quick_agent.arun(task)
            return response.content
        except Exception as e:
            return f"Quick task error: {e}"

# Usage example
async def main():
    assistant = ClaudeAssistant()
    
    # Quick task
    print("Quick task...")
    result = await assistant.quick_task("List 3 primary colors")
    print(f"Result: {result}\n")
    
    # Chat
    print("Chatting...")
    response = await assistant.chat("What's the weather like on Mars?")
    print(f"Chat: {response[:100]}...\n")
    
    # Analysis
    print("Analyzing...")
    doc = "AI technology is rapidly advancing..."
    analysis = await assistant.analyze(
        doc, 
        "Identify key trends and potential impacts"
    )
    print(f"Analysis: {analysis[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

## Performance Tips

1. **First request warm-up**: The first request might be slower
2. **Use appropriate timeouts**: 30s for Haiku, 60s for Sonnet, 120s for Opus
3. **Batch processing**: Process multiple items in one request when possible
4. **Model selection**: Use Haiku for high-volume simple tasks
5. **Prompt optimization**: Keep prompts concise but clear

## See Also

- [Agent API](../agent.md) - Core agent functionality
- [WorkflowAgent Guide](../../concepts/workflows.md) - Reliable tool usage
- [Provider Switching](../../features/provider_switching.md) - Dynamic provider changes
- [Anthropic Docs](https://docs.anthropic.com) - Official Anthropic documentation
