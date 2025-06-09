# Enhanced Workflows

**Released in v0.2.0** - AgentiCraft's Enhanced Workflows provide powerful tools for creating, visualizing, and executing complex multi-step processes with unprecedented control and visibility.

## Overview

Enhanced Workflows transform how you build and manage complex AI-driven processes:

- **Visual Planning**: See your workflows before execution
- **Dynamic Modification**: Adapt workflows on the fly
- **Checkpoint/Resume**: Never lose progress on long-running tasks
- **Progress Streaming**: Real-time updates on execution status
- **Production Patterns**: Pre-built patterns for common scenarios
- **Rich Templates**: Ready-to-use workflows for business needs

## Key Features

### 🎨 Workflow Visualization

Visualize workflows in multiple formats for different needs:

```python
from agenticraft.workflows import visualize_workflow

# Create a workflow
workflow = Workflow(
    name="data_pipeline",
    steps=[
        Step("extract", "Extract data from sources"),
        Step("transform", "Clean and transform data"),
        Step("load", "Load into data warehouse")
    ]
)

# Visualize in different formats
mermaid = visualize_workflow(workflow, format="mermaid")
ascii = visualize_workflow(workflow, format="ascii")
html = visualize_workflow(workflow, format="html", interactive=True)
```

**Mermaid Output:**
```mermaid
graph TB
    start([Start])
    extract[Extract data from sources]
    transform[Clean and transform data]
    load[Load into data warehouse]
    end([End])
    
    start --> extract
    extract --> transform
    transform --> load
    load --> end
```

### 🔧 Workflow Patterns

Pre-built patterns for common workflow scenarios:

```python
from agenticraft.workflows.patterns import WorkflowPatterns

# Parallel execution pattern
parallel = WorkflowPatterns.parallel_tasks(
    name="multi_analysis",
    tasks=[
        {"name": "sentiment", "description": "Analyze sentiment"},
        {"name": "topics", "description": "Extract topics"},
        {"name": "entities", "description": "Identify entities"}
    ],
    max_concurrent=3
)

# Conditional branching
conditional = WorkflowPatterns.conditional_branch(
    name="quality_check",
    condition="score > 0.8",
    if_branch=[Step("approve", "Auto-approve")],
    else_branch=[Step("review", "Manual review")]
)

# Retry with backoff
resilient = WorkflowPatterns.retry_loop(
    name="api_call",
    task=Step("fetch", "Call external API"),
    max_retries=3,
    backoff_factor=2.0
)
```

### 📋 Workflow Templates

Production-ready templates for business scenarios:

```python
from agenticraft.workflows.templates import WorkflowTemplates

# Research workflow
research = WorkflowTemplates.research_workflow(
    topic="Competitive Analysis",
    sources=["web", "news", "academic"],
    depth="comprehensive",
    output_format="report"
)

# Content creation pipeline
content = WorkflowTemplates.content_pipeline(
    content_type="blog_post",
    target_audience="developers",
    stages=["research", "outline", "draft", "edit", "seo", "publish"]
)

# Data processing pipeline
etl = WorkflowTemplates.data_processing(
    input_format="csv",
    output_format="parquet",
    transformations=["clean", "validate", "enrich", "aggregate"]
)
```

### 🚀 Enhanced WorkflowAgent

The WorkflowAgent now includes powerful execution features:

```python
from agenticraft.agents.workflow import WorkflowAgent

agent = WorkflowAgent(
    name="DataProcessor",
    enable_checkpoints=True,
    enable_visualization=True,
    enable_streaming=True
)

# Visual planning with AI
planned = await agent.plan_workflow(
    "Create a customer churn analysis pipeline",
    requirements={"data_sources": ["crm", "support", "usage"]},
    output_format="workflow"
)

# Execute with checkpoints
result = await agent.run_workflow(
    "Q4 Churn Analysis",
    planned,
    checkpoint_id="churn_q4_2024",
    resume_from_checkpoint=True  # Resume if interrupted
)

# Stream progress
async for progress in agent.stream_workflow("Process", workflow):
    print(f"{progress.current_step}: {progress.percentage:.0f}%")
```

## Visual Planning

Let AI help you plan workflows visually:

```python
# AI-powered workflow planning
visual_plan = await agent.plan_workflow(
    task="Build a machine learning pipeline",
    requirements={
        "model_type": "classification",
        "data_size": "large",
        "deployment": "real-time"
    },
    constraints={
        "time_limit": "4 hours",
        "compute_budget": "$50"
    },
    output_format="mermaid"
)

print(visual_plan)
# Outputs a complete Mermaid diagram of the planned workflow
```

## Dynamic Modification

Modify workflows during execution:

```python
# Start with base workflow
workflow = WorkflowTemplates.data_processing(
    input_format="json",
    transformations=["validate", "transform"]
)

# Modify based on data characteristics
if data_quality_score < 0.7:
    workflow = agent.modify_workflow(
        workflow,
        modifications={
            "add_steps": [
                Step("clean_data", "Additional data cleaning"),
                Step("verify_quality", "Quality verification")
            ],
            "modify_steps": {
                "transform": {"retry_count": 3}
            }
        }
    )
```

## Checkpoint and Resume

Never lose progress on long-running workflows:

```python
# Enable checkpointing
agent = WorkflowAgent(
    enable_checkpoints=True,
    checkpoint_dir="./workflow_checkpoints"
)

# Execute with checkpoints
try:
    result = await agent.run_workflow(
        "Long running analysis",
        complex_workflow,
        checkpoint_id="analysis_2024_06"
    )
except InterruptedError:
    # Resume from last checkpoint
    result = await agent.run_workflow(
        "Long running analysis",
        complex_workflow,
        checkpoint_id="analysis_2024_06",
        resume_from_checkpoint=True
    )
```

## Progress Streaming

Get real-time updates on workflow execution:

```python
# Stream workflow progress
async for progress in agent.stream_workflow("ETL Process", etl_workflow):
    # Update UI
    update_progress_bar(progress.percentage)
    
    # Show current step
    display_current_step(progress.current_step, progress.status)
    
    # Log important outputs
    if progress.step_output and progress.current_step == "validate":
        log_validation_results(progress.step_output)
    
    # Handle failures immediately
    if progress.status == "failed":
        alert_team(f"Step {progress.current_step} failed: {progress.message}")
```

## Visualization Formats

### Mermaid Diagrams
Perfect for documentation and web display:
- Interactive in supported viewers
- Rich styling options
- Export to PNG/SVG
- Progress overlay support

### ASCII Art
Ideal for terminals and logs:
```
┌─────────────────────┐
│   Data Pipeline     │
└─────────────────────┘
         │
         ▼
   ┌──────────┐
   │ Extract  │ ✓
   └──────────┘
         │
         ▼
   ┌──────────┐
   │Transform │ ⟳
   └──────────┘
         │
         ▼
   ┌──────────┐
   │  Load    │ ○
   └──────────┘

Legend: ✓ Complete  ⟳ Running  ○ Pending
```

### Interactive HTML
Self-contained visualization with:
- Zoom and pan controls
- Click for step details
- Execution playback
- Export capabilities

## Workflow Patterns

### Parallel Execution
Execute independent tasks simultaneously:
```python
parallel = WorkflowPatterns.parallel_tasks(
    name="multi_fetch",
    tasks=[fetch_users, fetch_orders, fetch_products],
    max_concurrent=5,
    error_handling="continue"  # Don't stop on single failure
)
```

### Conditional Branching
Make decisions within workflows:
```python
approval_flow = WorkflowPatterns.conditional_branch(
    name="approval_process",
    condition="risk_score < 0.3",
    if_branch=[auto_approve_steps],
    else_branch=[manual_review_steps]
)
```

### Retry Logic
Build resilient workflows:
```python
reliable_api = WorkflowPatterns.retry_loop(
    name="external_api_call",
    task=api_call_step,
    max_retries=5,
    backoff_factor=2.0,  # Exponential backoff
    retry_conditions=["timeout", "rate_limit"]
)
```

### Map-Reduce
Process data in parallel then aggregate:
```python
analytics = WorkflowPatterns.map_reduce(
    name="regional_analytics",
    map_tasks=[analyze_region(r) for r in regions],
    reduce_task=aggregate_results,
    batch_size=10
)
```

## Production Templates

### Research Workflow
Comprehensive research with multiple sources:
```python
research = WorkflowTemplates.research_workflow(
    topic="AI Market Trends 2025",
    sources=["academic", "news", "industry_reports", "social"],
    depth="comprehensive",
    quality_threshold=0.8,
    output_format="executive_report"
)
```

### Content Pipeline
End-to-end content creation:
```python
blog_pipeline = WorkflowTemplates.content_pipeline(
    content_type="technical_blog",
    target_audience="senior_developers",
    tone="authoritative",
    seo_optimized=True,
    review_loops=2
)
```

### Multi-Agent Collaboration
Coordinate multiple specialized agents:
```python
team_workflow = WorkflowTemplates.multi_agent_collaboration(
    task="Product launch campaign",
    agents=[
        {"name": "strategist", "role": "Define strategy"},
        {"name": "copywriter", "role": "Create content"},
        {"name": "designer", "role": "Design assets"},
        {"name": "coordinator", "role": "Manage timeline"}
    ],
    coordination_style="orchestrated"
)
```

## Performance Considerations

### Optimization Strategies

1. **Parallel Execution**: Group independent steps
2. **Caching**: Enable for repeated operations
3. **Batch Processing**: Process data in chunks
4. **Resource Limits**: Set appropriate constraints

```python
# Optimized configuration
agent = WorkflowAgent(
    max_parallel_steps=10,
    enable_caching=True,
    cache_ttl=3600,
    resource_limits={
        "max_memory": "4GB",
        "max_concurrent_api_calls": 20
    }
)
```

### Performance Metrics

Monitor workflow performance:
```python
result = await agent.run_workflow(task, workflow, collect_metrics=True)

metrics = result.metrics
print(f"Total duration: {metrics.total_duration}s")
print(f"Parallelism efficiency: {metrics.parallelism_efficiency:.0%}")
print(f"Cache hit rate: {metrics.cache_hit_rate:.0%}")
print(f"Resource utilization: {metrics.resource_utilization}")
```

## Error Handling

Comprehensive error handling throughout:

```python
# Configure error strategies
agent = WorkflowAgent(
    retry_failed_steps=True,
    retry_strategy="exponential_backoff",
    error_handlers={
        "network_error": retry_with_backoff,
        "validation_error": log_and_continue,
        "critical_error": alert_and_stop
    }
)

# Handle partial failures
try:
    result = await agent.run_workflow(task, workflow)
except WorkflowExecutionError as e:
    # Access partial results
    completed = e.partial_results
    failed_step = e.failed_at
    
    # Create recovery workflow
    recovery = agent.create_recovery_workflow(
        original=workflow,
        completed_steps=completed,
        start_from=failed_step
    )
```

## Integration Examples

### With Reasoning Patterns
```python
# Use reasoning to plan workflows
reasoner = ReasoningAgent(reasoning_pattern="tree_of_thoughts")
plan = await reasoner.think_and_act("Design optimal data pipeline")

# Convert reasoning to workflow
workflow = agent.parse_reasoning_to_workflow(plan)
result = await agent.run_workflow("Execute plan", workflow)
```

### With Streaming
```python
# Combine workflow streaming with response streaming
async for progress in agent.stream_workflow(task, workflow):
    if progress.current_step == "generate_report":
        # Stream the report generation
        async for chunk in agent.stream(progress.step_context):
            yield chunk
```

## Best Practices

### Simplified Workflow Pattern (Recommended)

Based on extensive testing, we recommend keeping workflows simple and predictable:

#### 1. Use Handlers for Data Operations
```python
# Define handler for data/tool operations
def process_handler(agent, step, context):
    # Process data
    result = process_data(context.get("input"))
    context["output"] = result
    return "Data processed"

agent.register_handler("process", process_handler)

# Use in workflow
workflow.add_step(
    name="process",
    handler="process",
    action="Processing data"
)
```

#### 2. Use Action Parameter Directly for AI Operations
```python
# AI step without handler - put prompt directly in action
workflow.add_step(
    name="analyze",
    action="Analyze the processed data and provide insights",
    depends_on=["process"]
)
```

#### 3. Avoid Complex Variable Substitution
```python
# ❌ Avoid - Complex variable substitution can be unreliable
workflow.add_step(
    name="report",
    action="Generate report using $analysis_result and $metrics"
)

# ✅ Better - Direct prompts or use handlers
workflow.add_step(
    name="report",
    action="Generate a comprehensive report based on the analysis"
)
```

#### 4. Store Results in Context After Workflow
```python
# Execute workflow
result = await agent.execute_workflow(workflow, context=context)

# Post-process results if needed
if result.status == StepStatus.COMPLETED:
    # Access step results
    analyze_result = result.step_results.get("analyze")
    if analyze_result:
        context["analysis"] = analyze_result.result
```

### General Best Practices

1. **Visualize First**: Always visualize complex workflows before execution
2. **Use Templates**: Start with templates for common scenarios
3. **Keep It Simple**: Don't overcomplicate with too many steps or complex dependencies
4. **Enable Checkpoints**: For workflows longer than 5 minutes
5. **Monitor Progress**: Use callbacks or streaming for visibility
6. **Plan for Failure**: Configure appropriate error handling
7. **Test Steps**: Validate individual steps before full workflow
8. **Document Workflows**: Use descriptions and visualization
9. **Test Incrementally**: Add steps one at a time when debugging

## Migration Guide

If you're using basic workflows:

```python
# Old approach
workflow = [
    ("step1", "Do something"),
    ("step2", "Do something else")
]
result = agent.run(workflow)

# New approach with enhanced features
workflow = Workflow(
    name="enhanced_workflow",
    steps=[
        Step("step1", "Do something", retry_count=2),
        Step("step2", "Do something else", depends_on=["step1"])
    ]
)

# With all enhancements
agent = WorkflowAgent(
    enable_checkpoints=True,
    enable_visualization=True
)

# Visualize first
print(visualize_workflow(workflow))

# Execute with monitoring
async for progress in agent.stream_workflow("Task", workflow):
    print(f"Progress: {progress.percentage}%")
```

## What's Next

- Explore the [API Reference](../api/workflows/index.md) for detailed documentation
- Check out [Workflow Examples](../examples/workflows/)
- Learn about [Workflow Patterns](../api/workflows/patterns.md)
- Try [Workflow Templates](../api/workflows/templates.md)

---

Enhanced Workflows make complex multi-step processes manageable, visible, and reliable. Start with templates, customize with patterns, and execute with confidence.
