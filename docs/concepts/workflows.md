# Workflows

Workflows enable agents to execute complex, multi-step processes with clear structure and error handling.

## Enhanced in v0.2.0 🚀

Workflows now include powerful new capabilities:
- **Visual Planning & Execution** - See workflows before and during execution
- **Dynamic Modification** - Adapt workflows on the fly
- **Checkpoint/Resume** - Never lose progress
- **Progress Streaming** - Real-time execution updates
- **Rich Patterns** - Pre-built patterns for common scenarios
- **Production Templates** - Ready-to-use business workflows

For detailed documentation, see:
- [Enhanced Workflows Feature Guide](../features/enhanced_workflows.md)
- [Workflows API Reference](../api/workflows/index.md)
- [Migration Guide](../migration/workflows.md)

## Understanding Workflows

A workflow breaks down complex tasks into manageable steps that can be executed sequentially or in parallel.

```python
from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.core.workflow import Workflow, Step

agent = WorkflowAgent(
    name="DataProcessor", 
    model="gpt-4",
    enable_checkpoints=True,  # New in v0.2.0
    enable_visualization=True  # New in v0.2.0
)

workflow = Workflow(
    name="data_pipeline",
    steps=[
        Step("extract", "Extract data from the source", retry_count=3),
        Step("transform", "Clean and transform the data", depends_on=["extract"]),
        Step("analyze", "Perform analysis", depends_on=["transform"]),
        Step("report", "Generate a report", depends_on=["analyze"])
    ]
)

# Visualize before execution (New in v0.2.0)
from agenticraft.workflows import visualize_workflow
print(visualize_workflow(workflow, format="mermaid"))

# Execute with progress streaming (New in v0.2.0)
async for progress in agent.stream_workflow("Process our Q4 sales data", workflow):
    print(f"{progress.current_step}: {progress.percentage:.0f}%")
```

## Workflow Benefits

1. **Clarity**: Break complex tasks into clear steps
2. **Debugging**: See exactly where issues occur
3. **Reusability**: Save and reuse workflow patterns
4. **Progress Tracking**: Monitor execution progress
5. **Error Recovery**: Handle failures gracefully

## Visual Representation (New in v0.2.0)

Visualize workflows in multiple formats:

```python
# Mermaid diagram for documentation
mermaid = visualize_workflow(workflow, format="mermaid")

# ASCII for terminal output
ascii = visualize_workflow(workflow, format="ascii")

# Interactive HTML
html = visualize_workflow(workflow, format="html", interactive=True)

# JSON for programmatic use
json_repr = visualize_workflow(workflow, format="json")
```

## Workflow Patterns (New in v0.2.0)

Use pre-built patterns for common scenarios:

```python
from agenticraft.workflows.patterns import WorkflowPatterns

# Parallel execution
parallel = WorkflowPatterns.parallel_tasks(
    name="data_fetching",
    tasks=[fetch_users, fetch_orders, fetch_products],
    max_concurrent=3
)

# Conditional branching
approval = WorkflowPatterns.conditional_branch(
    name="approval_flow",
    condition="risk_score < 0.5",
    if_branch=[auto_approve],
    else_branch=[manual_review]
)

# Retry with backoff
resilient = WorkflowPatterns.retry_loop(
    name="api_call",
    task=external_api_step,
    max_retries=3,
    backoff_factor=2.0
)
```

## Production Templates (New in v0.2.0)

Ready-to-use workflow templates:

```python
from agenticraft.workflows.templates import WorkflowTemplates

# Research workflow
research = WorkflowTemplates.research_workflow(
    topic="Market Analysis",
    sources=["academic", "news", "industry"],
    depth="comprehensive"
)

# Content pipeline
content = WorkflowTemplates.content_pipeline(
    content_type="blog_post",
    target_audience="developers",
    seo_optimized=True
)

# Data processing
etl = WorkflowTemplates.data_processing(
    input_format="csv",
    output_format="parquet",
    transformations=["clean", "validate", "aggregate"]
)
```

## Step Dependencies

Define relationships between steps:

```python
workflow = Workflow(
    name="data_analysis",
    steps=[
        Step("fetch_data", "Fetch data from API"),
        Step("validate", "Validate data", depends_on=["fetch_data"]),
        Step("process", "Process data", depends_on=["validate"]),
        Step("save", "Save results", depends_on=["process"])
    ]
)
```

## Parallel Execution

Run independent steps simultaneously:

```python
workflow = Workflow(
    name="parallel_fetch",
    steps=[
        Step("fetch_users", "Get user data"),
        Step("fetch_orders", "Get order data"),
        Step("fetch_products", "Get product data"),
        Step("combine", "Combine all data", 
             depends_on=["fetch_users", "fetch_orders", "fetch_products"])
    ]
)

# The agent automatically executes independent steps in parallel
```

## Conditional Steps

Execute steps based on conditions:

```python
# Using patterns for conditional logic (v0.2.0)
from agenticraft.workflows.patterns import WorkflowPatterns

workflow = WorkflowPatterns.conditional_branch(
    name="data_processing",
    condition_step=Step("check_data", "Check if data exists"),
    condition="data_exists == True",
    if_branch=[
        Step("process", "Process existing data")
    ],
    else_branch=[
        Step("fetch_data", "Fetch from API"),
        Step("process", "Process the data")
    ]
)
```

## Error Handling

Built-in error recovery:

```python
# Using retry pattern (v0.2.0)
from agenticraft.workflows.patterns import WorkflowPatterns

workflow = WorkflowPatterns.retry_loop(
    name="resilient_operation",
    task=Step("risky_operation", "Perform operation"),
    max_retries=3,
    backoff_factor=2.0,
    fallback=Step("safe_operation", "Fallback operation")
)
```

## WorkflowAgent Features

The enhanced `WorkflowAgent` provides:
- **Visual Planning** - AI-powered workflow design
- **Checkpointing** - Save and resume execution
- **Progress Streaming** - Real-time updates
- **Dynamic Modification** - Adapt workflows during execution
- **Parallel Execution** - Automatic parallelization
- **Error Recovery** - Sophisticated error handling

```python
# Enhanced agent with v0.2.0 features
agent = WorkflowAgent(
    name="SmartProcessor",
    enable_checkpoints=True,
    enable_visualization=True,
    enable_streaming=True,
    max_parallel_steps=10
)

# AI-powered workflow planning
planned_workflow = await agent.plan_workflow(
    task="Analyze customer feedback and generate insights",
    requirements={"sources": ["surveys", "reviews", "support"]},
    output_format="workflow"
)

# Execute with checkpoint support
result = await agent.run_workflow(
    "Q4 Customer Analysis",
    planned_workflow,
    checkpoint_id="customer_analysis_q4",
    resume_from_checkpoint=True
)
```

## Example: Data Pipeline

```python
from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.workflows.templates import WorkflowTemplates

# Use a template
etl_workflow = WorkflowTemplates.data_processing(
    input_format="csv",
    output_format="parquet",
    transformations=[
        "remove_duplicates",
        "clean_missing",
        "normalize_dates",
        "calculate_metrics",
        "aggregate_by_region"
    ],
    validation_rules={
        "required_columns": ["id", "date", "amount"],
        "date_format": "YYYY-MM-DD",
        "amount_range": (0, 1000000)
    },
    parallel_processing=True
)

agent = WorkflowAgent(
    name="ETL",
    model="gpt-4",
    enable_checkpoints=True
)

# Stream execution progress
async for progress in agent.stream_workflow(
    "Run ETL for customer data",
    etl_workflow
):
    print(f"{progress.current_step}: {progress.status}")
    if progress.percentage:
        update_progress_bar(progress.percentage)
```

## Best Practices

1. **Visualize First**: Always visualize complex workflows before execution
2. **Use Patterns**: Leverage pre-built patterns for common scenarios
3. **Enable Checkpoints**: For workflows longer than 5 minutes
4. **Monitor Progress**: Use streaming for real-time visibility
5. **Use Templates**: Start with templates and customize
6. **Handle Failures**: Plan for error scenarios with retry patterns
7. **Test Steps Individually**: Ensure each step works in isolation
8. **Document Workflows**: Use clear descriptions and visualizations

## Next Steps

- [Explore Enhanced Workflows](../features/enhanced_workflows.md) - All new v0.2.0 features
- [Workflow API Reference](../api/workflows/index.md) - Detailed API documentation
- [Workflow Examples](../examples/workflows/) - Real-world examples
- [Migration Guide](../migration/workflows.md) - Upgrade from v0.1.x
