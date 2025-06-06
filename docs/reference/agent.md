# Agent API Reference

The Agent class is the core of AgentiCraft, providing intelligent AI capabilities with tool usage, memory, and provider flexibility.

## Agent

```python
from agenticraft import Agent

agent = Agent(
    name="MyAgent",
    model="gpt-4",
    provider="openai",  # Optional, auto-detected from model
    **kwargs
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Unique name for the agent |
| `model` | `str` | `"gpt-4"` | Model to use |
| `provider` | `str` | `None` | LLM provider (auto-detected if None) |
| `tools` | `List[Tool]` | `[]` | Tools available to the agent |
| `memory_enabled` | `bool` | `False` | Enable conversation memory |
| `system_prompt` | `str` | `None` | System instructions |
| `temperature` | `float` | `0.7` | Sampling temperature |
| `max_tokens` | `int` | `None` | Maximum response tokens |

### Methods

#### run(prompt: str) -> Response

Execute the agent with a prompt.

```python
response = agent.run("Hello, how are you?")
print(response.content)
```

#### set_provider(provider: str, model: str, **kwargs)

Switch to a different LLM provider at runtime.

```python
agent.set_provider("anthropic", model="claude-3-opus-20240229")
```

#### get_provider_info() -> Dict[str, Any]

Get information about the current provider.

```python
info = agent.get_provider_info()
# {'provider': 'openai', 'model': 'gpt-4', 'temperature': 0.7}
```

#### list_available_providers() -> List[str]

List all available providers.

```python
providers = agent.list_available_providers()
# ['openai', 'anthropic', 'ollama']
```

## ReasoningAgent

An agent that provides transparent reasoning traces.

```python
from agenticraft import ReasoningAgent

agent = ReasoningAgent(
    name="Thinker",
    model="gpt-4",
    reasoning_style="chain_of_thought"
)

response = agent.run("Analyze this problem...")
print(response.reasoning)  # List of reasoning steps
print(response.confidence)  # Confidence score
```

### Additional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reasoning_style` | `str` | `"chain_of_thought"` | Reasoning approach |
| `explore_branches` | `int` | `1` | Branches for tree_of_thought |
| `enable_self_critique` | `bool` | `False` | Enable self-reflection |

## WorkflowAgent

An agent optimized for multi-step workflows.

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(name="Processor", model="gpt-4")

workflow = [
    Step("analyze", "Analyze the data"),
    Step("process", "Process the results"),
    Step("report", "Generate report")
]

result = agent.run_workflow("Process sales data", workflow)
```

## Response Objects

### Response

Basic response from an agent.

```python
@dataclass
class Response:
    content: str  # The response text
    metadata: Dict[str, Any]  # Additional metadata
```

### ReasoningResponse

Response from a ReasoningAgent.

```python
@dataclass 
class ReasoningResponse(Response):
    reasoning: List[str]  # Reasoning steps
    confidence: float  # Confidence score (0-1)
    assumptions: List[str]  # Assumptions made
```

### WorkflowResponse

Response from a WorkflowAgent.

```python
@dataclass
class WorkflowResponse(Response):
    steps: Dict[str, StepResult]  # Results by step name
    duration: float  # Total execution time
```

## Examples

### Basic Usage

```python
from agenticraft import Agent

# Simple agent
agent = Agent(name="Assistant", model="gpt-4")
response = agent.run("Tell me a joke")
print(response.content)
```

### With Tools

```python
from agenticraft import Agent, tool

@tool
def calculate(expression: str) -> float:
    return eval(expression)

agent = Agent(name="MathBot", tools=[calculate])
response = agent.run("What's 15 * 23?")
```

### Provider Switching

```python
# Start with GPT-4
agent = Agent(name="Flex", model="gpt-4")
response = agent.run("Complex analysis...")

# Switch to cheaper model
agent.set_provider("ollama", model="llama2")
response = agent.run("Simple summary...")
```

### With Memory

```python
agent = Agent(name="MemBot", memory_enabled=True)

agent.run("My name is Alice")
response = agent.run("What's my name?")
# Agent remembers: "Your name is Alice"
```

## See Also

- [Tool API](tool.md) - Creating and using tools
- [Workflow API](workflow.md) - Building workflows
- [OpenAI Provider](providers/openai.md) - OpenAI-specific details
- [Anthropic Provider](providers/anthropic.md) - Anthropic-specific details
- [Ollama Provider](providers/ollama.md) - Ollama-specific details
