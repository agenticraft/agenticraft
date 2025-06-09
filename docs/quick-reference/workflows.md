# Workflows Quick Reference

## Basic Workflow Creation

```python
from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.core.workflow import Workflow, Step

# Simple workflow
workflow = Workflow(
    name="data_pipeline",
    steps=[
        Step("fetch", "Fetch data"),
        Step("process", "Process data"),
        Step("save", "Save results")
    ]
)

# With dependencies
workflow = Workflow(
    name="complex_pipeline",
    steps=[
        Step("fetch_a", "Fetch dataset A"),
        Step("fetch_b", "Fetch dataset B"),
        Step("merge", "Merge datasets", depends_on=["fetch_a", "fetch_b"]),
        Step("analyze", "Analyze merged data", depends_on=["merge"])
    ]
)
```

## Visualization

```python
from agenticraft.workflows import visualize_workflow

# Quick visualization
mermaid = visualize_workflow(workflow)  # Default: mermaid
ascii = visualize_workflow(workflow, format="ascii")
json = visualize_workflow(workflow, format="json")
html = visualize_workflow(workflow, format="html")

# With progress
viz = visualize_workflow(
    workflow,
    show_progress=True,
    progress_data=execution_result.progress
)
```

## Workflow Patterns

### Parallel Tasks
```python
from agenticraft.workflows.patterns import WorkflowPatterns

parallel = WorkflowPatterns.parallel_tasks(
    name="parallel_work",
    tasks=[task1, task2, task3],
    max_concurrent=3
)
```

### Conditional Branch
```python
conditional = WorkflowPatterns.conditional_branch(
    name="decision",
    condition="score > 0.8",
    if_branch=[approve_step],
    else_branch=[review_step]
)
```

### Retry Loop
```python
retry = WorkflowPatterns.retry_loop(
    name="resilient_task",
    task=risky_step,
    max_retries=3,
    backoff_factor=2.0
)
```

### Map-Reduce
```python
mapreduce = WorkflowPatterns.map_reduce(
    name="data_aggregation",
    map_tasks=[process1, process2, process3],
    reduce_task=aggregate_step
)
```

## Workflow Templates

### Research
```python
from agenticraft.workflows.templates import WorkflowTemplates

research = WorkflowTemplates.research_workflow(
    topic="AI Safety",
    sources=["academic", "news"],
    depth="comprehensive"
)
```

### Content Pipeline
```python
content = WorkflowTemplates.content_pipeline(
    content_type="blog_post",
    target_audience="developers",
    seo_optimized=True
)
```

### Data Processing
```python
etl = WorkflowTemplates.data_processing(
    input_format="csv",
    output_format="parquet",
    transformations=["clean", "validate", "aggregate"]
)
```

## Enhanced WorkflowAgent

### Basic Usage
```python
agent = WorkflowAgent(
    name="Processor",
    enable_checkpoints=True,
    enable_visualization=True
)

# Execute workflow
result = await agent.run_workflow(
    task="Process Q4 data",
    workflow=workflow
)
```

### With Checkpoints
```python
# Enable checkpointing
agent = WorkflowAgent(enable_checkpoints=True)

# Execute with checkpoint
result = await agent.run_workflow(
    "Long task",
    workflow,
    checkpoint_id="task_001",
    resume_from_checkpoint=True
)
```

### Streaming Progress
```python
# Stream execution progress
async for progress in agent.stream_workflow("Task", workflow):
    print(f"{progress.current_step}: {progress.percentage:.0f}%")
    
    if progress.status == "failed":
        print(f"Error: {progress.message}")
```

### Visual Planning
```python
# AI-powered planning
planned = await agent.plan_workflow(
    task="Create marketing campaign",
    requirements={"channels": ["email", "social"]},
    output_format="workflow"  # or "mermaid"
)
```

## Common Configurations

### High Reliability
```python
reliable_agent = WorkflowAgent(
    retry_failed_steps=True,
    max_retries=3,
    retry_strategy="exponential_backoff",
    enable_checkpoints=True,
    checkpoint_interval=300  # Every 5 minutes
)
```

### High Performance
```python
fast_agent = WorkflowAgent(
    max_parallel_steps=20,
    enable_caching=True,
    cache_ttl=3600,
    batch_size=1000
)
```

### Development Mode
```python
dev_agent = WorkflowAgent(
    enable_visualization=True,
    enable_streaming=True,
    verbose_logging=True,
    step_timeout=60  # Quick timeout for testing
)
```

## Step Configuration

```python
# Full step configuration
step = Step(
    name="process_data",
    description="Process the dataset",
    tool=processor_tool,          # Optional tool
    depends_on=["fetch_data"],    # Dependencies
    retry_count=3,                # Retries on failure
    timeout=300,                  # 5 minute timeout
    condition="len(data) > 0",    # Conditional execution
    parallel=True,                # Allow parallel
    checkpoint=True,              # Checkpoint after
    on_error="continue",          # Error handling
    metadata={"priority": "high"} # Custom metadata
)
```

## Error Handling

```python
# Workflow-level error handling
try:
    result = await agent.run_workflow(task, workflow)
except WorkflowExecutionError as e:
    print(f"Failed at: {e.failed_step}")
    print(f"Completed: {list(e.partial_results.keys())}")
    
    # Get partial results
    for step, output in e.partial_results.items():
        if output.success:
            print(f"✓ {step}: {output.data}")

# Step-level error handling
workflow = Workflow(
    name="resilient",
    steps=[
        Step("risky", "Risky operation",
             on_error="retry",
             fallback="safe_operation"),
        Step("safe_operation", "Fallback",
             skip_by_default=True)
    ]
)
```

## Workflow Modification

```python
# Dynamic modification
modified = agent.modify_workflow(
    workflow,
    modifications={
        "add_steps": [
            Step("validate", "Validate results")
        ],
        "remove_steps": ["old_step"],
        "modify_steps": {
            "process": {"timeout": 600}
        },
        "reorder_steps": ["fetch", "validate", "process"]
    }
)
```

## Performance Tips

1. **Use Parallel Patterns** for independent tasks
2. **Enable Caching** for repeated workflows
3. **Set Resource Limits** to prevent overload
4. **Use Checkpoints** for long workflows
5. **Batch Operations** when possible

```python
# Optimized configuration
agent = WorkflowAgent(
    max_parallel_steps=os.cpu_count(),
    enable_caching=True,
    resource_limits={
        "max_memory": "4GB",
        "max_concurrent_api_calls": 10
    },
    batch_size=100
)
```

## Visualization Options

### Mermaid
```python
mermaid_options = {
    "theme": "dark",
    "direction": "LR",  # Left to right
    "show_progress": True
}
```

### ASCII
```python
ascii_options = {
    "width": 80,
    "box_style": "rounded",
    "show_status": True
}
```

### HTML
```python
html_options = {
    "interactive": True,
    "zoom_controls": True,
    "export_buttons": True
}
```

## Quick Patterns

### ETL Pipeline
```python
etl = WorkflowPatterns.sequential_pipeline(
    name="etl",
    stages=[
        [Step("extract_db", "From DB"), Step("extract_api", "From API")],
        Step("transform", "Transform data"),
        Step("load", "Load to warehouse")
    ]
)
```

### Approval Flow
```python
approval = WorkflowPatterns.conditional_branch(
    name="approval",
    condition_step=Step("evaluate", "Evaluate request"),
    condition="risk_level == 'low'",
    if_branch=[Step("auto_approve", "Approve")],
    else_branch=[Step("manual_review", "Review")]
)
```

### Batch Processing
```python
batch = WorkflowPatterns.map_reduce(
    name="batch_process",
    map_tasks=[Step(f"process_{i}", f"Process batch {i}") 
               for i in range(10)],
    reduce_task=Step("combine", "Combine results")
)
```

Need more details? See the [full documentation](../api/workflows/index.md).
