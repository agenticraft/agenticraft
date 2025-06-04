# Workflow Module Documentation

## Overview

The AgentiCraft workflow module provides a simple, step-based approach to chaining agents and tools together. Unlike complex graph-based workflow engines, AgentiCraft uses a straightforward dependency system that's easy to understand and debug.

## Key Concepts

### Steps
Steps are the building blocks of workflows. Each step:
- Has a unique name
- Executes with either an Agent or a Tool (not both)
- Can depend on other steps
- Supports retry logic and timeouts
- Passes outputs to dependent steps

### Workflows
Workflows orchestrate the execution of steps:
- Execute steps in dependency order (topological sort)
- Handle data passing between steps
- Provide error handling and retry logic
- Return comprehensive results

## Basic Usage

```python
from agenticraft import Workflow, Step, Agent, tool

# Create agents
researcher = Agent(name="Researcher", model="gpt-4")
writer = Agent(name="Writer", model="gpt-4")

# Create workflow
workflow = Workflow("content_pipeline")

# Add steps
workflow.add_steps([
    Step("research", agent=researcher, inputs={"topic": "AI safety"}),
    Step("outline", agent=writer, depends_on=["research"]),
    Step("write", agent=writer, depends_on=["outline"])
])

# Run workflow
result = await workflow.run()

# Access results
research_output = result["research"]
final_article = result["write"]
```

## Advanced Features

### Input References
Use `$` syntax to reference values from context:

```python
workflow.add_steps([
    Step("load", tool=load_data, inputs={"path": "$input_file"}),
    Step("process", agent=processor, inputs={"data": "$load"})
])

result = await workflow.run(input_file="data.csv")
```

### Error Handling & Retries
```python
Step(
    "api_call",
    tool=external_api,
    retry_count=3,      # Retry up to 3 times
    timeout=30          # 30 second timeout
)
```

### Workflow Visualization
```python
print(workflow.visualize())
# Output:
# Workflow: content_pipeline
# ========================
# 1. research (agent)
# 2. outline (agent) <- research
# 3. write (agent) <- outline
```

## Workflow Patterns

### Sequential Pipeline
```python
workflow.add_steps([
    Step("extract", tool=extract_data),
    Step("transform", agent=transformer, depends_on=["extract"]),
    Step("load", tool=save_data, depends_on=["transform"])
])
```

### Parallel Processing
```python
workflow.add_steps([
    Step("fetch_data", tool=fetch),
    Step("analyze_1", agent=analyst1, depends_on=["fetch_data"]),
    Step("analyze_2", agent=analyst2, depends_on=["fetch_data"]),
    Step("combine", agent=aggregator, depends_on=["analyze_1", "analyze_2"])
])
```

### Conditional Execution
```python
# Use agent logic to conditionally process
@tool
async def check_condition(data: dict) -> bool:
    return data.get("requires_processing", False)

workflow.add_steps([
    Step("check", tool=check_condition, inputs={"data": "$input"}),
    Step("process", agent=processor, depends_on=["check"])
])
```

## API Reference

### Workflow Class

#### Constructor
```python
Workflow(name: str, description: Optional[str] = None)
```

#### Methods
- `add_step(step: Step)` - Add a single step
- `add_steps(steps: List[Step])` - Add multiple steps
- `run(**inputs) -> WorkflowResult` - Execute the workflow
- `visualize() -> str` - Get text visualization

### Step Class

#### Constructor
```python
Step(
    name: str,
    agent: Optional[Agent] = None,
    tool: Optional[BaseTool] = None,
    inputs: Dict[str, Any] = {},
    depends_on: List[str] = [],
    retry_count: int = 0,
    timeout: Optional[int] = None
)
```

### WorkflowResult Class

#### Attributes
- `workflow_id: str` - Unique workflow execution ID
- `workflow_name: str` - Name of the workflow
- `success: bool` - Overall success status
- `steps: Dict[str, StepResult]` - Results from each step
- `started_at: datetime` - Workflow start time
- `completed_at: datetime` - Workflow completion time

#### Methods
- `result["step_name"]` - Get output from specific step

## Best Practices

1. **Keep Steps Focused**: Each step should do one thing well
2. **Use Clear Naming**: Step names should describe what they do
3. **Handle Errors Gracefully**: Use retry_count for unreliable operations
4. **Pass Minimal Data**: Large data should be referenced, not passed
5. **Document Dependencies**: Make it clear why steps depend on each other

## Common Pitfalls

1. **Circular Dependencies**: The workflow engine will detect and report these
2. **Missing Dependencies**: Referencing non-existent steps will fail validation
3. **Type Mismatches**: Ensure tool/agent inputs match expected types
4. **Timeout Issues**: Set appropriate timeouts for long-running operations

## Integration with Other Components

### With Tools
```python
@tool
def process_data(data: str) -> dict:
    return {"processed": data.upper()}

Step("process", tool=process_data)
```

### With Memory
```python
# Agents in workflows maintain their memory
agent = Agent(name="Assistant", memory=ConversationMemory())
Step("chat", agent=agent)
```

### With Plugins
```python
# Plugins enhance agents before workflow execution
registry.register(LoggingPlugin())
Step("logged_step", agent=enhanced_agent)
```

## Examples

See the `examples/workflows/` directory for complete examples:
- `simple_workflow.py` - Basic sequential workflow
- `research_workflow.py` - Multi-agent research pipeline
- `data_pipeline.py` - ETL workflow with tools
- `retry_workflow.py` - Error handling and retries
