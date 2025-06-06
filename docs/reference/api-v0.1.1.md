# AgentiCraft API Reference v0.1.1

## Core Classes

### `Agent`
The main agent class for creating AI agents.

```python
from agenticraft import Agent

agent = Agent(
    name: str = "Agent",
    instructions: str = "You are a helpful assistant",
    model: str = "gpt-3.5-turbo",
    provider: Optional[str] = None,  # "openai", "anthropic", "ollama"
    tools: Optional[List[Callable]] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
    memory: Optional[List[Memory]] = None,
    reasoning_pattern: Optional[ReasoningPattern] = None,
    telemetry: Optional[Telemetry] = None,
    plugins: Optional[List[Plugin]] = None,
)
```

**Methods:**
- `run(prompt: str) -> AgentResponse` - Execute a single interaction
- `arun(prompt: str) -> AgentResponse` - Async version of run
- `set_provider(provider: str, **kwargs)` - Switch LLM provider at runtime (v0.1.1)
- `get_provider_info() -> dict` - Get current provider information (v0.1.1)
- `list_available_providers() -> List[str]` - List all available providers (v0.1.1)
- `add_tool(tool: Callable)` - Add a tool to the agent
- `remove_tool(tool_name: str)` - Remove a tool from the agent
- `clear_memory()` - Clear agent's memory

### `ReasoningAgent` (New in v0.1.1)
Agent specialized for transparent step-by-step reasoning.

```python
from agenticraft import ReasoningAgent

agent = ReasoningAgent(
    name: str = "ReasoningAgent",
    max_reasoning_steps: int = 10,
    **kwargs  # All Agent parameters
)
```

**Methods:**
- `think_and_act(prompt: str) -> ReasoningResponse` - Process with reasoning steps
- `analyze(prompt: str) -> AnalysisResponse` - Detailed analysis with reasoning

### `WorkflowAgent` (New in v0.1.1)
Agent optimized for executing multi-step workflows.

```python
from agenticraft import WorkflowAgent

agent = WorkflowAgent(
    name: str = "WorkflowAgent",
    **kwargs  # All Agent parameters
)
```

**Methods:**
- `create_workflow(name: str, description: str = "") -> Workflow` - Create a new workflow
- `execute_workflow(workflow: Union[Workflow, str], context: dict = None, parallel: bool = True) -> WorkflowResult` - Execute workflow
- `register_handler(name: str, handler: Callable)` - Register custom step handler
- `get_workflow_status(workflow_id: str) -> dict` - Get running workflow status

## Tool System

### `@tool` Decorator
Create tools from Python functions.

```python
from agenticraft import tool

@tool
def my_tool(param1: str, param2: int = 10) -> dict:
    """Tool description for the agent.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    return {"result": param1, "count": param2}
```

### `BaseTool`
Base class for creating custom tools.

```python
from agenticraft import BaseTool

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "Description for the agent"
    
    def execute(self, **kwargs) -> Any:
        # Tool implementation
        return result
```

## Workflow System

### `Workflow`
Define multi-step processes.

```python
from agenticraft import Workflow, Step

workflow = Workflow(name="my_workflow")

# Add steps
workflow.add_step(
    name="step1",
    action="Do something",
    depends_on=[],  # No dependencies
)

workflow.add_step(
    name="step2", 
    action="Do something else",
    depends_on=["step1"],  # Depends on step1
    condition="step1_result == 'success'",  # Optional condition
    parallel=True,  # Can run in parallel with other parallel steps
    timeout=30.0,  # Step timeout in seconds
    max_retries=3,  # Retry failed steps
)
```

### `WorkflowStep` (v0.1.1)
Individual workflow step configuration.

```python
from agenticraft.agents.workflow import WorkflowStep

step = WorkflowStep(
    name: str,
    description: str = "",
    action: Optional[str] = None,
    handler: Optional[str] = None,
    depends_on: List[str] = [],
    condition: Optional[str] = None,
    parallel: bool = False,
    timeout: Optional[float] = None,
    max_retries: int = 3,
)
```

## Memory

### `ConversationMemory`
Short-term conversation history.

```python
from agenticraft.memory import ConversationMemory

memory = ConversationMemory(
    max_turns: int = 10,
    max_tokens: Optional[int] = None,
    summarize: bool = False,
)
```

### `KnowledgeMemory`
Long-term knowledge storage.

```python
from agenticraft.memory import KnowledgeMemory

memory = KnowledgeMemory(
    persist: bool = True,
    storage_path: Optional[str] = None,
    embedding_model: str = "text-embedding-ada-002",
)
```

## Providers

### Provider Configuration
Configure LLM providers.

```python
# OpenAI
agent = Agent(
    provider="openai",  # Optional, auto-detected from model
    model="gpt-4",
    api_key="sk-...",
    temperature=0.7,
    max_tokens=1000,
)

# Anthropic (v0.1.1)
agent = Agent(
    provider="anthropic",
    model="claude-3-opus-20240229",
    api_key="sk-ant-...",
    max_tokens=4096,
)

# Ollama (v0.1.1)
agent = Agent(
    provider="ollama",
    model="llama2:latest",
    base_url="http://localhost:11434",  # Optional, defaults to localhost
)
```

### Provider Factory (v0.1.1)
```python
from agenticraft.providers import ProviderFactory

# Get provider instance
provider = ProviderFactory.create(
    provider_name="anthropic",
    model="claude-3-sonnet-20240229",
    api_key="...",
)

# List available providers
providers = ProviderFactory.list_providers()
# Returns: ["openai", "anthropic", "ollama"]
```

## Reasoning Patterns

### `ChainOfThought`
Step-by-step reasoning pattern.

```python
from agenticraft.core.reasoning import ChainOfThought

agent = Agent(
    reasoning_pattern=ChainOfThought(
        max_steps=10,
        require_explicit_steps=True,
    )
)
```

## Telemetry

### `Telemetry`
OpenTelemetry integration.

```python
from agenticraft.telemetry import Telemetry

telemetry = Telemetry(
    service_name="my-agent-app",
    export_to="http://localhost:4317",  # OTLP endpoint
    console_export=False,  # Print to console
    sampling_rate=1.0,  # Sample all traces
)

agent = Agent(telemetry=telemetry)
```

## Response Types

### `AgentResponse`
Response from agent execution.

```python
response = agent.run("Hello")

response.content  # str: The agent's response
response.reasoning  # str: Reasoning process (if available)
response.tool_calls  # List[dict]: Tools called during execution
response.usage  # dict: Token usage information
response.metadata  # dict: Additional metadata
```

### `ReasoningResponse` (v0.1.1)
Response from ReasoningAgent.

```python
response = await reasoning_agent.think_and_act("Solve this problem")

response.content  # str: Final answer
response.reasoning_trace  # List[ReasoningStep]: All reasoning steps
response.total_steps  # int: Number of reasoning steps
response.conclusion  # str: Final conclusion
```

### `WorkflowResult` (v0.1.1)
Result from workflow execution.

```python
result = await workflow_agent.execute_workflow(workflow)

result.workflow_id  # str: Workflow ID
result.workflow_name  # str: Workflow name
result.status  # StepStatus: Overall status
result.duration  # float: Total duration in seconds
result.step_results  # Dict[str, StepResult]: Results per step
result.successful  # bool: Whether workflow succeeded
result.failed_steps  # List[str]: Names of failed steps
result.format_summary()  # str: Human-readable summary
```

## Exceptions

```python
from agenticraft import (
    AgenticraftError,  # Base exception
    AgentError,        # Agent-related errors
    ToolError,         # Tool execution errors
    WorkflowError,     # Workflow errors
    ProviderError,     # Provider errors (v0.1.1)
    MemoryError,       # Memory errors
)
```

## CLI Commands

```bash
# Create new project from template
agenticraft create [template] [name]

# Run an agent
agenticraft run [agent_file]

# List available templates
agenticraft templates

# Start MCP server
agenticraft mcp start [server_name]

# Plugin management (future)
agenticraft plugin install [plugin_name]
agenticraft plugin list
```

## Environment Variables

```bash
# API Keys
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# Provider URLs
OLLAMA_BASE_URL="http://localhost:11434"

# Telemetry
AGENTICRAFT_TELEMETRY_ENDPOINT="http://localhost:4317"
AGENTICRAFT_TELEMETRY_ENABLED="true"

# Logging
AGENTICRAFT_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

## Type Hints

AgentiCraft is fully typed. Common types:

```python
from typing import Any, Callable, Dict, List, Optional, Union
from agenticraft.types import (
    ToolFunction,
    ToolResult,
    Message,
    ModelConfig,
    ProviderConfig,
)
```

---

For more detailed documentation, see:
- [Quickstart Guide](../quickstart.md)
- [Examples](../examples/)
- [Provider Documentation](../providers/)
- [Feature Guides](../features/)