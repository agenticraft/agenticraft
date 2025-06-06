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

# Explicit provider required for Anthropic
agent = Agent(
    name="Claude",
    provider="anthropic",
    model="claude-3-opus-20240229"
)
```

## Supported Models

| Model | Description | Context Window | Best For |
|-------|-------------|----------------|----------|
| `claude-3-opus-20240229` | Most capable | 200K tokens | Complex analysis, reasoning |
| `claude-3-sonnet-20240229` | Balanced performance | 200K tokens | General tasks |
| `claude-3-haiku-20240307` | Fast and efficient | 200K tokens | High-volume, simple tasks |
| `claude-2.1` | Previous generation | 100K tokens | Legacy support |
| `claude-instant-1.2` | Fastest | 100K tokens | Real-time applications |

## Provider-Specific Features

### Constitutional AI

Claude models are trained with Constitutional AI for helpful, harmless, and honest responses:

```python
agent = Agent(
    name="SafeAssistant",
    provider="anthropic",
    model="claude-3-opus-20240229",
    system_prompt="You are a helpful, harmless, and honest assistant."
)
```

### Large Context Window

Claude excels at processing long documents:

```python
agent = Agent(
    name="DocumentAnalyzer",
    provider="anthropic", 
    model="claude-3-opus-20240229"
)

# Process a long document (up to 200K tokens)
with open("long_document.txt", "r") as f:
    document = f.read()

response = agent.run(f"Analyze this document:\n\n{document}")
```

### XML Tags Support

Claude works well with structured prompts using XML tags:

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

response = agent.run(prompt)
```

### Vision Capabilities

Claude 3 models support image analysis:

```python
agent = Agent(
    name="VisionClaude",
    provider="anthropic",
    model="claude-3-opus-20240229"
)

response = agent.run(
    prompt="Describe this image in detail",
    images=["path/to/image.jpg"]
)
```

## Configuration Options

```python
agent = Agent(
    name="ConfiguredClaude",
    provider="anthropic",
    model="claude-3-opus-20240229",
    
    # Anthropic-specific options
    temperature=0.7,        # 0.0-1.0
    max_tokens=4000,       # Max response length
    top_p=0.9,            # Nucleus sampling
    top_k=0,              # Top-k sampling (0 = disabled)
    
    # Safety settings
    stop_sequences=["\n\nHuman:"],
    
    # Retry configuration
    max_retries=3,
    timeout=60  # Claude can take longer for complex tasks
)
```

## Tool Usage

Claude supports tool use through a specific format:

```python
from agenticraft import Agent, tool

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression, {"__builtins__": {}}))

@tool 
def search(query: str) -> str:
    """Search for information."""
    return f"Search results for: {query}"

agent = Agent(
    name="ClaudeWithTools",
    provider="anthropic",
    model="claude-3-opus-20240229",
    tools=[calculate, search]
)

# Claude will use tools when appropriate
response = agent.run("What's 15% of 2500? Also search for tax rates.")
```

## Error Handling

```python
from agenticraft import Agent, ProviderError

try:
    agent = Agent(
        name="Claude",
        provider="anthropic",
        model="claude-3-opus-20240229"
    )
    response = agent.run("Hello")
except ProviderError as e:
    if "rate_limit" in str(e):
        print("Rate limit reached")
    elif "invalid_api_key" in str(e):
        print("Check your Anthropic API key")
    else:
        print(f"Anthropic error: {e}")
```

## Cost Optimization

### Model Selection Strategy

```python
class AnthropicOptimizer:
    def __init__(self):
        self.agent = Agent(
            name="Optimizer",
            provider="anthropic",
            model="claude-3-haiku-20240307"  # Start with cheapest
        )
    
    def process(self, task: str, requirements: dict):
        # Determine model based on requirements
        if requirements.get("complexity") == "high":
            model = "claude-3-opus-20240229"
        elif requirements.get("speed") == "fast":
            model = "claude-3-haiku-20240307"
        else:
            model = "claude-3-sonnet-20240229"
        
        self.agent.model = model
        return self.agent.run(task)
```

### Token Estimation

```python
def estimate_tokens(text: str) -> int:
    """Rough estimation of Claude tokens."""
    # Claude uses a similar tokenization to ~4 chars per token
    return len(text) // 4

def check_context_fit(text: str, model: str) -> bool:
    """Check if text fits in model context."""
    limits = {
        "claude-3-opus-20240229": 200000,
        "claude-3-sonnet-20240229": 200000,
        "claude-3-haiku-20240307": 200000,
        "claude-2.1": 100000
    }
    return estimate_tokens(text) < limits.get(model, 100000)
```

## Best Practices

1. **Prompt Engineering**: Use clear, structured prompts with Claude
2. **XML Tags**: Leverage XML tags for better organization
3. **Context Management**: Take advantage of large context windows
4. **Safety**: Claude is designed to be helpful, harmless, and honest
5. **Rate Limits**: Anthropic has strict rate limits - implement backoff

## Complete Example

```python
import os
from agenticraft import Agent, tool
from typing import Dict, List

class ClaudeAssistant:
    def __init__(self):
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.agent = Agent(
            name="ClaudeAssistant",
            provider="anthropic",
            model="claude-3-opus-20240229",
            temperature=0.7,
            max_tokens=4000,
            system_prompt="""You are Claude, a helpful AI assistant.
            You excel at analysis, writing, and reasoning.
            Always strive to be helpful, harmless, and honest."""
        )
        
        self._setup_tools()
    
    def _setup_tools(self):
        @tool
        def analyze_data(data: str) -> str:
            """Analyze provided data."""
            # Simulate data analysis
            return f"Analysis of data: {len(data)} characters processed"
        
        @tool
        def generate_report(topic: str, sections: List[str]) -> str:
            """Generate a structured report."""
            outline = "\n".join(f"- {s}" for s in sections)
            return f"Report outline for {topic}:\n{outline}"
        
        self.agent.tools = [analyze_data, generate_report]
    
    def analyze_document(self, document: str) -> Dict:
        """Analyze a document with structured output."""
        
        prompt = f"""
        <document>
        {document}
        </document>
        
        <task>
        Please analyze this document and provide:
        1. A brief summary (2-3 sentences)
        2. Key points (bullet list)
        3. Potential concerns or risks
        4. Recommended actions
        5. Confidence level in your analysis
        </task>
        
        Format your response with clear sections.
        """
        
        response = self.agent.run(prompt)
        
        # Parse structured response
        return {
            "analysis": response.content,
            "model": "claude-3-opus-20240229",
            "tokens": estimate_tokens(document + response.content)
        }
    
    def creative_writing(self, prompt: str, style: str = "professional"):
        """Generate creative content."""
        
        style_prompts = {
            "professional": "Write in a clear, professional tone",
            "casual": "Write in a friendly, conversational tone",
            "academic": "Write in a formal, academic style with citations",
            "creative": "Write creatively with vivid descriptions"
        }
        
        full_prompt = f"""
        {style_prompts.get(style, style_prompts['professional'])}
        
        Task: {prompt}
        
        Please create high-quality content that engages the reader.
        """
        
        # Use Sonnet for creative tasks (good balance)
        self.agent.model = "claude-3-sonnet-20240229"
        response = self.agent.run(full_prompt)
        
        # Switch back to Opus
        self.agent.model = "claude-3-opus-20240229"
        
        return response.content

# Usage
assistant = ClaudeAssistant()

# Document analysis
doc = "Your long document text here..."
analysis = assistant.analyze_document(doc)
print(analysis["analysis"])

# Creative writing
story = assistant.creative_writing(
    "Write a short story about AI and humanity",
    style="creative"
)
print(story)
```

## Anthropic-Specific Tips

1. **Prompt Structure**: Claude responds well to clear structure and formatting
2. **Chain of Thought**: Ask Claude to think step-by-step for complex problems  
3. **Constitutional AI**: Claude will refuse harmful requests by design
4. **Context Usage**: Don't hesitate to use the full 200K context when needed
5. **Model Selection**: Opus for complex tasks, Haiku for speed, Sonnet for balance

## See Also

- [Agent API](../agent.md) - Core agent functionality
- [Provider Switching](../../features/provider_switching.md) - Dynamic provider changes
- [Anthropic Docs](https://docs.anthropic.com) - Official Anthropic documentation
