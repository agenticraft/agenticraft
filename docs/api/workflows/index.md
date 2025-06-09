# Workflows API Reference

## Overview

AgentiCraft's Enhanced Workflows provide a powerful system for creating, visualizing, and executing complex multi-step processes with built-in patterns, templates, and visualization capabilities.

## Core Components

### [Workflow Visualization](visualization.md)
Create visual representations of workflows in multiple formats including Mermaid, ASCII, JSON, and HTML.

### [Workflow Patterns](patterns.md)
Pre-built patterns for common workflow scenarios: parallel execution, conditional branching, retry loops, and more.

### [Workflow Templates](templates.md)
Production-ready templates for research, content creation, data processing, and multi-agent collaboration.

### [Enhanced WorkflowAgent](workflow_agent.md)
Advanced agent with visual planning, dynamic modification, checkpoints, and progress streaming.

## Quick Start

```python
from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.workflows import visualize_workflow
from agenticraft.workflows.patterns import WorkflowPatterns

# Create a workflow agent
agent = WorkflowAgent(name="DataProcessor")

# Define workflow using patterns
workflow = WorkflowPatterns.parallel_tasks(
    name="process_data",
    tasks=[
        {"name": "fetch", "description": "Fetch data from API"},
        {"name": "validate", "description": "Validate data format"},
        {"name": "transform", "description": "Transform to target schema"}
    ]
)

# Visualize the workflow
visualization = visualize_workflow(workflow, format="mermaid")
print(visualization)

# Execute with progress tracking
async for progress in agent.stream_workflow("Process customer data", workflow):
    print(f"Step {progress.current_step}: {progress.status}")
```

## Workflow Structure

### Basic Workflow Definition

```python
from agenticraft.core.workflow import Step, Workflow

# Simple sequential workflow
workflow = Workflow(
    name="data_pipeline",
    steps=[
        Step("extract", "Extract data from source"),
        Step("transform", "Transform data format"),
        Step("load", "Load into database")
    ]
)

# With dependencies
workflow = Workflow(
    name="complex_pipeline",
    steps=[
        Step("fetch_users", "Get user data"),
        Step("fetch_orders", "Get order data"),
        Step("merge", "Merge datasets", depends_on=["fetch_users", "fetch_orders"]),
        Step("analyze", "Analyze merged data", depends_on=["merge"])
    ]
)
```

### Step Configuration

```python
Step(
    name="process_data",
    description="Process the dataset",
    tool=data_processor_tool,  # Optional tool binding
    depends_on=["fetch_data"],  # Dependencies
    retry_count=3,              # Retry on failure
    timeout=300,                # Timeout in seconds
    condition="len(data) > 0",  # Conditional execution
    parallel=True,              # Allow parallel execution
    checkpoint=True             # Enable checkpointing
)
```

## Visualization

### Supported Formats

| Format | Use Case | Features |
|--------|----------|----------|
| `mermaid` | Documentation, web display | Interactive, colorful, standard |
| `ascii` | Terminal output, logs | Text-based, portable |
| `json` | Programmatic processing | Structured data, parseable |
| `html` | Standalone viewing | Self-contained, interactive |

### Visualization API

```python
from agenticraft.workflows import visualize_workflow

# Basic visualization
mermaid = visualize_workflow(workflow, format="mermaid")

# With execution progress
mermaid_with_progress = visualize_workflow(
    workflow, 
    format="mermaid",
    show_progress=True,
    progress_data=execution_result.progress
)

# ASCII for terminal
ascii_viz = visualize_workflow(workflow, format="ascii")
print(ascii_viz)
```

## Patterns

Pre-built workflow patterns for common scenarios:

```python
from agenticraft.workflows.patterns import WorkflowPatterns

# Parallel execution
parallel = WorkflowPatterns.parallel_tasks(
    name="multi_process",
    tasks=[...],
    max_concurrent=5
)

# Conditional branching
conditional = WorkflowPatterns.conditional_branch(
    name="decision_flow",
    condition="score > 0.8",
    if_branch=[...],
    else_branch=[...]
)

# Retry with backoff
retry = WorkflowPatterns.retry_loop(
    name="resilient_task",
    task=risky_step,
    max_retries=3,
    backoff_factor=2
)

# Map-reduce pattern
mapreduce = WorkflowPatterns.map_reduce(
    name="data_aggregation",
    map_tasks=[...],
    reduce_task=aggregate_step
)
```

## Templates

Ready-to-use workflow templates:

```python
from agenticraft.workflows.templates import WorkflowTemplates

# Research workflow
research = WorkflowTemplates.research_workflow(
    topic="AI Safety",
    sources=["academic", "news", "blogs"],
    output_format="report"
)

# Content pipeline
content = WorkflowTemplates.content_pipeline(
    content_type="blog_post",
    stages=["research", "outline", "draft", "edit", "publish"]
)

# Data processing
data_pipeline = WorkflowTemplates.data_processing(
    input_format="csv",
    transformations=["clean", "normalize", "aggregate"],
    output_format="parquet"
)
```

## Enhanced WorkflowAgent

The WorkflowAgent provides advanced workflow execution capabilities:

```python
from agenticraft.agents.workflow import WorkflowAgent

agent = WorkflowAgent(
    name="AdvancedProcessor",
    enable_checkpoints=True,
    enable_visualization=True,
    progress_callback=lambda p: print(f"Progress: {p}")
)

# Visual planning
visual_plan = await agent.plan_workflow(
    "Create a marketing campaign",
    output_format="mermaid"
)

# Execute with checkpoints
result = await agent.run_workflow(
    task="Process Q4 data",
    workflow=workflow,
    checkpoint_dir="./checkpoints",
    resume_from_checkpoint=True
)

# Stream progress
async for progress in agent.stream_workflow(task, workflow):
    print(f"{progress.current_step}: {progress.percentage}%")
```

## Error Handling

Comprehensive error handling throughout workflows:

```python
try:
    result = await agent.run_workflow(task, workflow)
except WorkflowExecutionError as e:
    print(f"Failed at step: {e.failed_step}")
    print(f"Error: {e.error_message}")
    
    # Get partial results
    partial = e.partial_results
    for step, result in partial.items():
        if result.success:
            print(f"✓ {step}: {result.output}")
        else:
            print(f"✗ {step}: {result.error}")
```

## Performance Considerations

| Feature | Impact | Optimization |
|---------|--------|--------------|
| Visualization | Low (~10ms) | Cache rendered diagrams |
| Checkpointing | Medium (~100ms/checkpoint) | Async writes, compression |
| Progress Streaming | Low (~5ms/update) | Batch updates |
| Parallel Execution | Improves throughput | Configure max_concurrent |

## Integration Examples

### With Reasoning Patterns

```python
# Combine workflows with reasoning
reasoning_agent = ReasoningAgent(reasoning_pattern="chain_of_thought")
workflow_agent = WorkflowAgent()

# Plan workflow with reasoning
plan = await reasoning_agent.think_and_act(
    "Design a workflow for analyzing customer feedback"
)

# Convert to workflow
workflow = workflow_agent.parse_workflow(plan.content)

# Execute
result = await workflow_agent.run_workflow("Analyze feedback", workflow)
```

### With Streaming

```python
# Stream workflow execution
agent = WorkflowAgent(enable_streaming=True)

async for chunk in agent.stream_workflow("Complex analysis", workflow):
    if chunk.type == "step_complete":
        print(f"✓ Completed: {chunk.step_name}")
    elif chunk.type == "step_output":
        print(f"  Output: {chunk.content}")
    elif chunk.type == "progress":
        print(f"  Progress: {chunk.percentage}%")
```

## Best Practices

1. **Use Patterns**: Start with pre-built patterns for common scenarios
2. **Visualize First**: Always visualize complex workflows before execution
3. **Enable Checkpoints**: For long-running workflows
4. **Handle Errors**: Plan for failure scenarios
5. **Monitor Progress**: Use progress callbacks or streaming
6. **Test Steps**: Validate individual steps before full workflow
7. **Document Workflows**: Use descriptions and visualization

## See Also

- [Visualization API](visualization.md) - Detailed visualization options
- [Patterns Reference](patterns.md) - All available patterns
- [Templates Guide](templates.md) - Template customization
- [WorkflowAgent](workflow_agent.md) - Agent capabilities
- [Examples](../../examples/workflows/) - Working examples
