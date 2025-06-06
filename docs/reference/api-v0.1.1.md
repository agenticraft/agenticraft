# API Reference v0.1.1

## Core Classes

### Agent
The base agent class for all AgentiCraft agents.

```python
class Agent:
    def __init__(
        self,
        name: str,
        model: str = "gpt-4",
        provider: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        memory_enabled: bool = False,
        **kwargs
    )
```

### ReasoningAgent
Agent with transparent reasoning capabilities.

```python
class ReasoningAgent(Agent):
    def run(self, prompt: str) -> ReasoningResponse:
        """Returns response with reasoning trace."""
```

### WorkflowAgent
Agent optimized for multi-step workflows.

```python
class WorkflowAgent(Agent):
    def run_workflow(
        self, 
        prompt: str, 
        workflow: List[Step]
    ) -> WorkflowResponse:
        """Execute workflow and return step results."""
```

## Provider Management

### set_provider()
```python
agent.set_provider(
    provider: str,
    model: str,
    **kwargs
) -> None
```

Switch LLM provider at runtime.

### get_provider_info()
```python
agent.get_provider_info() -> Dict[str, Any]
```

Get current provider information.

### list_available_providers()
```python
agent.list_available_providers() -> List[str]
```

List all available providers.

## Tools

### @tool decorator
```python
@tool
def my_tool(param: str) -> str:
    """Tool description."""
    return result
```

### Tool class
```python
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
```

## Configuration

### AgentConfig
```python
@dataclass
class AgentConfig:
    name: str
    model: str = "gpt-4"
    provider: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    tools: List[Tool] = field(default_factory=list)
    memory_enabled: bool = False
```

## Responses

### Response
```python
@dataclass
class Response:
    content: str
    metadata: Dict[str, Any]
```

### ReasoningResponse
```python
@dataclass
class ReasoningResponse(Response):
    reasoning: List[str]
    confidence: float
```

### WorkflowResponse
```python
@dataclass
class WorkflowResponse(Response):
    steps: Dict[str, StepResult]
    duration: float
```

## Exceptions

### AgentiCraftError
Base exception for all AgentiCraft errors.

### ProviderError
Raised when provider operations fail.

### ToolError
Raised when tool execution fails.

## Full API Documentation

For complete API documentation with all parameters and examples, see:
- [Agent API](agent.md)
- [Tool API](tool.md)
- [Workflow API](workflow.md)
- Provider APIs:
  - [OpenAI](providers/openai.md)
  - [Anthropic](providers/anthropic.md)
  - [Ollama](providers/ollama.md)
