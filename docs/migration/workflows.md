# Migrating to Enhanced Workflows

This guide helps you migrate from basic workflows to AgentiCraft's Enhanced Workflows introduced in v0.2.0.

## What's Changed

### Before (v0.1.x)
```python
# Basic workflow as list of tuples
workflow = [
    ("fetch_data", "Get data from API"),
    ("process", "Process the data"),
    ("save", "Save results")
]

agent = WorkflowAgent(name="Processor")
result = agent.run_workflow("Execute pipeline", workflow)
```

### After (v0.2.0)
```python
# Rich workflow with full features
from agenticraft.core.workflow import Workflow, Step

workflow = Workflow(
    name="data_pipeline",
    steps=[
        Step("fetch_data", "Get data from API", retry_count=3),
        Step("process", "Process the data", depends_on=["fetch_data"]),
        Step("save", "Save results", depends_on=["process"])
    ]
)

agent = WorkflowAgent(
    name="Processor",
    enable_checkpoints=True,
    enable_visualization=True
)

# Visualize before execution
print(visualize_workflow(workflow))

# Execute with progress tracking
async for progress in agent.stream_workflow("Execute pipeline", workflow):
    print(f"{progress.percentage:.0f}%: {progress.current_step}")
```

## Migration Steps

### 1. Update Your Imports

```python
# Old
from agenticraft import WorkflowAgent

# New
from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.core.workflow import Workflow, Step
from agenticraft.workflows import visualize_workflow
from agenticraft.workflows.patterns import WorkflowPatterns
from agenticraft.workflows.templates import WorkflowTemplates
```

### 2. Convert Workflow Definitions

#### Simple Sequential Workflow
```python
# Old
workflow = [
    ("step1", "First step"),
    ("step2", "Second step"),
    ("step3", "Third step")
]

# New - Basic conversion
workflow = Workflow(
    name="my_workflow",
    steps=[
        Step("step1", "First step"),
        Step("step2", "Second step"),
        Step("step3", "Third step")
    ]
)

# New - With enhancements
workflow = Workflow(
    name="my_workflow",
    description="My enhanced workflow",
    steps=[
        Step("step1", "First step", timeout=60),
        Step("step2", "Second step", retry_count=2),
        Step("step3", "Third step", checkpoint=True)
    ]
)
```

#### Workflow with Dependencies
```python
# Old - No native dependency support
workflow = [
    ("fetch_users", "Get users"),
    ("fetch_orders", "Get orders"),
    ("merge", "Merge data"),  # Had to handle deps manually
    ("analyze", "Analyze")
]

# New - Explicit dependencies
workflow = Workflow(
    name="data_analysis",
    steps=[
        Step("fetch_users", "Get users"),
        Step("fetch_orders", "Get orders"),
        Step("merge", "Merge data", depends_on=["fetch_users", "fetch_orders"]),
        Step("analyze", "Analyze", depends_on=["merge"])
    ]
)
```

### 3. Update Agent Creation

```python
# Old
agent = WorkflowAgent(name="MyAgent")

# New - With enhanced features
agent = WorkflowAgent(
    name="MyAgent",
    enable_checkpoints=True,      # Save progress
    enable_visualization=True,    # Visualize workflows
    enable_streaming=True,        # Stream progress
    max_parallel_steps=5,         # Parallel execution
    retry_failed_steps=True       # Auto-retry failures
)
```

### 4. Update Execution Code

#### Synchronous to Asynchronous
```python
# Old - Synchronous
result = agent.run_workflow("Task", workflow)
print(result)

# New - Asynchronous with more options
result = await agent.run_workflow(
    task="Task",
    workflow=workflow,
    checkpoint_id="task_001",  # Enable resume
    context={"user_id": 123}   # Pass context
)

# Access detailed results
for step_name, step_result in result.steps.items():
    print(f"{step_name}: {step_result.status}")
    if step_result.output:
        print(f"  Output: {step_result.output}")
```

#### Add Progress Tracking
```python
# Old - No progress visibility
result = agent.run_workflow("Long task", workflow)

# New - Real-time progress
async for progress in agent.stream_workflow("Long task", workflow):
    print(f"Step: {progress.current_step}")
    print(f"Status: {progress.status}")
    print(f"Progress: {progress.percentage:.1f}%")
    
    # Update UI
    update_progress_bar(progress.percentage)
```

### 5. Leverage New Features

#### Workflow Visualization
```python
# Visualize before execution
visualization = visualize_workflow(workflow, format="mermaid")
print(visualization)

# Or as ASCII for terminals
ascii_viz = visualize_workflow(workflow, format="ascii")
print(ascii_viz)

# Interactive HTML
html_viz = visualize_workflow(workflow, format="html", interactive=True)
save_to_file("workflow.html", html_viz)
```

#### Use Workflow Patterns
```python
# Old - Manual parallel setup
# Complex manual implementation...

# New - Use patterns
parallel_workflow = WorkflowPatterns.parallel_tasks(
    name="parallel_processing",
    tasks=[
        Step("task1", "Process dataset 1"),
        Step("task2", "Process dataset 2"),
        Step("task3", "Process dataset 3")
    ],
    max_concurrent=3
)
```

#### Use Templates
```python
# Old - Build from scratch
workflow = [
    ("research", "Research topic"),
    ("outline", "Create outline"),
    ("draft", "Write draft"),
    # ... many more steps
]

# New - Use templates
content_workflow = WorkflowTemplates.content_pipeline(
    content_type="blog_post",
    target_audience="developers",
    tone="technical",
    seo_optimized=True
)
```

## Code Examples

### Example 1: Data Processing Pipeline

#### Before
```python
def process_data():
    agent = WorkflowAgent(name="DataProcessor")
    
    workflow = [
        ("extract", "Extract from database"),
        ("validate", "Validate data"),
        ("transform", "Transform format"),
        ("load", "Load to warehouse")
    ]
    
    result = agent.run_workflow("Process daily data", workflow)
    return result
```

#### After
```python
async def process_data():
    # Use template
    workflow = WorkflowTemplates.data_processing(
        input_format="database",
        output_format="warehouse",
        transformations=["validate", "clean", "transform"],
        validation_rules={
            "required_fields": ["id", "timestamp", "value"],
            "value_range": (0, 1000000)
        }
    )
    
    # Enhanced agent
    agent = WorkflowAgent(
        name="DataProcessor",
        enable_checkpoints=True,
        checkpoint_dir="./etl_checkpoints"
    )
    
    # Execute with monitoring
    result = await agent.run_workflow(
        "Process daily data",
        workflow,
        checkpoint_id=f"daily_{datetime.now().date()}"
    )
    
    # Check results
    if result.status == "completed":
        print(f"Processed in {result.total_duration:.2f}s")
    else:
        print(f"Failed at: {result.error}")
    
    return result
```

### Example 2: Multi-Step Analysis

#### Before
```python
class Analyzer:
    def __init__(self):
        self.agent = WorkflowAgent(name="Analyzer")
    
    def analyze(self, data):
        workflow = [
            ("preprocess", "Prepare data"),
            ("analyze", "Run analysis"),
            ("report", "Generate report")
        ]
        
        return self.agent.run_workflow(f"Analyze {data}", workflow)
```

#### After
```python
class Analyzer:
    def __init__(self):
        self.agent = WorkflowAgent(
            name="Analyzer",
            enable_visualization=True,
            enable_streaming=True
        )
    
    async def analyze(self, data):
        # Create workflow with patterns
        workflow = WorkflowPatterns.sequential_pipeline(
            name="analysis_pipeline",
            stages=[
                # Parallel preprocessing
                WorkflowPatterns.parallel_tasks(
                    name="preprocess",
                    tasks=[
                        Step("clean", "Clean data"),
                        Step("normalize", "Normalize values"),
                        Step("validate", "Validate integrity")
                    ]
                ),
                # Analysis with retries
                WorkflowPatterns.retry_loop(
                    name="analyze",
                    task=Step("ml_analysis", "Run ML analysis"),
                    max_retries=3
                ),
                # Conditional reporting
                WorkflowPatterns.conditional_branch(
                    name="report",
                    condition="confidence > 0.8",
                    if_branch=[Step("auto_report", "Generate report")],
                    else_branch=[Step("manual_review", "Flag for review")]
                )
            ],
            checkpoints=True
        )
        
        # Visualize the plan
        print(visualize_workflow(workflow))
        
        # Execute with progress
        async for progress in self.agent.stream_workflow(
            f"Analyze {data}",
            workflow
        ):
            yield progress  # Stream to UI
```

### Example 3: Conditional Workflow

#### Before
```python
# Manual condition handling
def approval_workflow(request):
    agent = WorkflowAgent(name="Approver")
    
    # Had to handle conditions in code
    if request.amount < 1000:
        workflow = [("auto_approve", "Automatic approval")]
    else:
        workflow = [
            ("review", "Manual review"),
            ("approve", "Approval decision")
        ]
    
    return agent.run_workflow("Approval", workflow)
```

#### After
```python
async def approval_workflow(request):
    # Use conditional pattern
    workflow = WorkflowPatterns.conditional_branch(
        name="approval_flow",
        condition_step=Step("evaluate", "Evaluate request"),
        condition=f"amount < 1000",
        if_branch=[
            Step("auto_approve", "Automatic approval"),
            Step("notify", "Send notification")
        ],
        else_branch=[
            Step("assign_reviewer", "Assign to reviewer"),
            Step("review", "Manual review"),
            Step("decision", "Make decision"),
            Step("notify", "Send notification")
        ]
    )
    
    agent = WorkflowAgent(name="Approver")
    
    # Execute with context
    result = await agent.run_workflow(
        "Approval request",
        workflow,
        context={"amount": request.amount}
    )
    
    return result
```

## Async Considerations

### Converting Sync to Async

```python
# Old synchronous code
def run_workflow(task):
    agent = WorkflowAgent()
    result = agent.run_workflow(task, workflow)
    return result

# New async code
async def run_workflow(task):
    agent = WorkflowAgent()
    result = await agent.run_workflow(task, workflow)
    return result

# With streaming
async def run_workflow_with_updates(task):
    agent = WorkflowAgent(enable_streaming=True)
    
    results = []
    async for progress in agent.stream_workflow(task, workflow):
        print(f"Progress: {progress.percentage}%")
        results.append(progress)
    
    return results
```

### Integration with FastAPI

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/workflow/{workflow_id}")
async def workflow_progress(websocket: WebSocket, workflow_id: str):
    await websocket.accept()
    
    agent = WorkflowAgent(enable_streaming=True)
    workflow = get_workflow(workflow_id)
    
    try:
        async for progress in agent.stream_workflow("Execute", workflow):
            await websocket.send_json({
                "step": progress.current_step,
                "status": progress.status,
                "percentage": progress.percentage
            })
    except Exception as e:
        await websocket.send_json({"error": str(e)})
```

## Performance Improvements

### Old Performance Characteristics
- No parallel execution
- No caching
- No progress visibility
- No checkpoint/resume

### New Performance Features
```python
# Optimize for performance
agent = WorkflowAgent(
    max_parallel_steps=10,        # Parallel execution
    enable_caching=True,          # Cache step results
    cache_ttl=3600,              # 1 hour cache
    batch_size=1000,             # Batch processing
    resource_limits={
        "max_memory": "4GB",
        "max_concurrent_api_calls": 20
    }
)

# Monitor performance
result = await agent.run_workflow(task, workflow, collect_metrics=True)
print(f"Execution time: {result.metrics.total_duration}s")
print(f"Parallel efficiency: {result.metrics.parallelism_efficiency:.0%}")
```

## Rollback Plan

If you need to temporarily use old-style workflows:

```python
class LegacyWorkflowAdapter:
    """Adapter for old-style workflows."""
    
    @staticmethod
    def convert_legacy_workflow(legacy_workflow: List[Tuple[str, str]]) -> Workflow:
        """Convert old format to new."""
        steps = [
            Step(name=name, description=desc)
            for name, desc in legacy_workflow
        ]
        
        return Workflow(
            name="legacy_workflow",
            steps=steps
        )
    
    @staticmethod
    async def run_legacy_workflow(agent, task, legacy_workflow):
        """Run old-style workflow with new agent."""
        workflow = LegacyWorkflowAdapter.convert_legacy_workflow(legacy_workflow)
        return await agent.run_workflow(task, workflow)

# Use adapter
legacy_workflow = [("step1", "Do something"), ("step2", "Do more")]
result = await LegacyWorkflowAdapter.run_legacy_workflow(
    agent, "Task", legacy_workflow
)
```

## Common Issues and Solutions

### Issue: Workflow execution is now async
**Solution**: Update calling code to use `async/await` or use `asyncio.run()`

### Issue: Old workflows don't have dependencies
**Solution**: Add dependencies where needed or use sequential execution

### Issue: No progress visibility
**Solution**: Enable streaming and add progress handlers

### Issue: Complex manual workflows
**Solution**: Replace with patterns and templates

## Benefits of Migration

1. **Visualization**: See workflows before execution
2. **Reliability**: Checkpoints and retries
3. **Performance**: Parallel execution
4. **Monitoring**: Real-time progress
5. **Reusability**: Patterns and templates
6. **Maintainability**: Clear structure

## Next Steps

1. Start with simple workflow conversion
2. Add visualization to existing workflows
3. Enable checkpoints for long-running tasks
4. Explore patterns for complex scenarios
5. Use templates for common workflows

## Getting Help

- [API Documentation](../api/workflows/index.md)
- [Feature Guide](../features/enhanced_workflows.md)
- [Examples](../examples/workflows/)
- [Discord Community](https://discord.gg/agenticraft)

---

Enhanced Workflows provide significantly better control, visibility, and reliability. The migration is straightforward, and the benefits include visualization, checkpointing, progress tracking, and production-ready patterns.
