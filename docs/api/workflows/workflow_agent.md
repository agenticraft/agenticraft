# Enhanced WorkflowAgent API Reference

## Overview

The Enhanced WorkflowAgent extends the base WorkflowAgent with advanced capabilities including visual planning, dynamic workflow modification, checkpoint/resume support, and real-time progress streaming.

## Class Reference

### WorkflowAgent

```python
class WorkflowAgent(Agent):
    """
    Advanced agent for executing complex workflows with enhanced features.
    
    Provides visual planning, dynamic modification, checkpointing,
    and progress streaming capabilities.
    """
```

#### Initialization

```python
from agenticraft.agents.workflow import WorkflowAgent

agent = WorkflowAgent(
    name: str = "WorkflowExecutor",
    model: str = "gpt-4",
    provider: Optional[str] = None,
    enable_checkpoints: bool = False,
    checkpoint_dir: Optional[str] = None,
    enable_visualization: bool = True,
    enable_streaming: bool = False,
    progress_callback: Optional[Callable] = None,
    max_parallel_steps: int = 5,
    step_timeout: Optional[float] = None,
    retry_failed_steps: bool = True,
    **kwargs
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | "WorkflowExecutor" | Agent name |
| `model` | str | "gpt-4" | LLM model to use |
| `provider` | Optional[str] | None | LLM provider |
| `enable_checkpoints` | bool | False | Enable checkpoint/resume |
| `checkpoint_dir` | Optional[str] | None | Directory for checkpoints |
| `enable_visualization` | bool | True | Enable workflow visualization |
| `enable_streaming` | bool | False | Enable progress streaming |
| `progress_callback` | Optional[Callable] | None | Progress update callback |
| `max_parallel_steps` | int | 5 | Maximum parallel executions |
| `step_timeout` | Optional[float] | None | Default step timeout |
| `retry_failed_steps` | bool | True | Retry failed steps |

#### Core Methods

##### run_workflow()

```python
async def run_workflow(
    self,
    task: str,
    workflow: Union[Workflow, List[Step], Dict],
    context: Optional[Dict[str, Any]] = None,
    checkpoint_id: Optional[str] = None,
    resume_from_checkpoint: bool = False,
    **kwargs
) -> WorkflowResult
```

Execute a workflow with optional checkpoint/resume.

**Parameters:**
- `task`: Task description
- `workflow`: Workflow to execute
- `context`: Execution context
- `checkpoint_id`: Unique checkpoint identifier
- `resume_from_checkpoint`: Resume from existing checkpoint

**Returns:**
- `WorkflowResult`: Execution results with step outputs

**Example:**

```python
# Execute with checkpointing
result = await agent.run_workflow(
    task="Process quarterly data",
    workflow=data_pipeline,
    checkpoint_id="q4_2024_processing",
    resume_from_checkpoint=True
)

# Access results
for step_name, step_result in result.steps.items():
    print(f"{step_name}: {step_result.status}")
    if step_result.output:
        print(f"  Output: {step_result.output}")
```

##### stream_workflow()

```python
async def stream_workflow(
    self,
    task: str,
    workflow: Union[Workflow, List[Step], Dict],
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AsyncIterator[WorkflowProgress]
```

Stream workflow execution progress in real-time.

**Parameters:**
- `task`: Task description
- `workflow`: Workflow to execute
- `context`: Execution context

**Yields:**
- `WorkflowProgress`: Progress updates during execution

**Example:**

```python
# Stream execution progress
async for progress in agent.stream_workflow(
    "Analyze customer feedback",
    feedback_workflow
):
    print(f"Step: {progress.current_step}")
    print(f"Status: {progress.status}")
    print(f"Progress: {progress.percentage:.1f}%")
    
    if progress.step_output:
        print(f"Output: {progress.step_output}")
```

##### plan_workflow()

```python
async def plan_workflow(
    self,
    task: str,
    requirements: Optional[Dict[str, Any]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    output_format: str = "workflow",
    visualize: bool = True
) -> Union[Workflow, str]
```

Use AI to plan a workflow based on task description.

**Parameters:**
- `task`: Task to plan workflow for
- `requirements`: Specific requirements
- `constraints`: Constraints (time, resources, etc.)
- `output_format`: Output format ("workflow", "mermaid", "json")
- `visualize`: Generate visualization

**Returns:**
- `Union[Workflow, str]`: Planned workflow or visualization

**Example:**

```python
# AI-powered workflow planning
planned_workflow = await agent.plan_workflow(
    task="Create a competitive analysis report",
    requirements={
        "sources": ["web", "industry_reports"],
        "depth": "comprehensive",
        "deliverables": ["report", "presentation"]
    },
    constraints={
        "time_limit": "2 hours",
        "budget": "$100"
    },
    output_format="workflow"
)

# Get visual plan
visual_plan = await agent.plan_workflow(
    task="Data migration pipeline",
    output_format="mermaid",
    visualize=True
)
print(visual_plan)  # Mermaid diagram
```

##### modify_workflow()

```python
def modify_workflow(
    self,
    workflow: Workflow,
    modifications: Dict[str, Any]
) -> Workflow
```

Dynamically modify a workflow structure.

**Parameters:**
- `workflow`: Workflow to modify
- `modifications`: Modifications to apply

**Returns:**
- `Workflow`: Modified workflow

**Modification Types:**
```python
modifications = {
    "add_steps": [Step(...)],
    "remove_steps": ["step_name"],
    "modify_steps": {
        "step_name": {"description": "New description"}
    },
    "reorder_steps": ["step1", "step3", "step2"],
    "add_dependencies": {
        "step_name": ["dependency1", "dependency2"]
    }
}
```

**Example:**

```python
# Add error handling step
modified = agent.modify_workflow(
    original_workflow,
    {
        "add_steps": [
            Step("error_handler", "Handle errors", 
                 condition="any_step_failed")
        ],
        "modify_steps": {
            "risky_step": {"retry_count": 3}
        }
    }
)
```

##### visualize_execution()

```python
def visualize_execution(
    self,
    workflow: Workflow,
    execution_result: Optional[WorkflowResult] = None,
    format: str = "mermaid",
    show_timing: bool = True,
    show_outputs: bool = False
) -> str
```

Visualize workflow with execution results.

**Parameters:**
- `workflow`: Workflow to visualize
- `execution_result`: Execution results to overlay
- `format`: Visualization format
- `show_timing`: Show execution times
- `show_outputs`: Show step outputs

**Returns:**
- `str`: Visualization with execution data

##### checkpoint_workflow()

```python
async def checkpoint_workflow(
    self,
    checkpoint_id: str,
    workflow: Workflow,
    current_state: Dict[str, Any],
    completed_steps: List[str],
    step_outputs: Dict[str, Any]
) -> bool
```

Save workflow checkpoint for resume capability.

**Parameters:**
- `checkpoint_id`: Unique checkpoint identifier
- `workflow`: Workflow being executed
- `current_state`: Current execution state
- `completed_steps`: List of completed step names
- `step_outputs`: Outputs from completed steps

**Returns:**
- `bool`: Success status

##### resume_from_checkpoint()

```python
async def resume_from_checkpoint(
    self,
    checkpoint_id: str
) -> Tuple[Workflow, Dict[str, Any], List[str], Dict[str, Any]]
```

Resume workflow from checkpoint.

**Returns:**
- `Tuple`: (workflow, state, completed_steps, outputs)

### WorkflowResult

```python
@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    
    workflow_id: str
    status: WorkflowStatus
    steps: Dict[str, StepResult]
    start_time: datetime
    end_time: Optional[datetime]
    total_duration: Optional[float]
    error: Optional[str]
    metadata: Dict[str, Any]
```

### WorkflowProgress

```python
@dataclass
class WorkflowProgress:
    """Real-time workflow progress update."""
    
    workflow_id: str
    current_step: str
    status: StepStatus
    percentage: float
    elapsed_time: float
    estimated_remaining: Optional[float]
    step_output: Optional[Any]
    message: Optional[str]
```

## Advanced Features

### Parallel Execution

```python
# Configure parallel execution
agent = WorkflowAgent(
    max_parallel_steps=10,
    parallel_strategy="adaptive"  # or "fixed", "resource_based"
)

# Define parallel workflow
parallel_workflow = Workflow(
    name="parallel_processing",
    steps=[
        Step("task1", "Process dataset 1", parallel_group="group1"),
        Step("task2", "Process dataset 2", parallel_group="group1"),
        Step("task3", "Process dataset 3", parallel_group="group1"),
        Step("merge", "Merge results", depends_on=["task1", "task2", "task3"])
    ]
)

result = await agent.run_workflow("Parallel processing", parallel_workflow)
```

### Dynamic Workflow Generation

```python
class DynamicWorkflowAgent(WorkflowAgent):
    """Agent that generates workflows dynamically."""
    
    async def generate_adaptive_workflow(
        self,
        task: str,
        initial_analysis: Dict[str, Any]
    ) -> Workflow:
        """Generate workflow based on initial analysis."""
        
        # Analyze task complexity
        complexity = await self.analyze_complexity(task)
        
        # Generate appropriate workflow
        if complexity > 0.8:
            return WorkflowPatterns.map_reduce(...)
        elif complexity > 0.5:
            return WorkflowPatterns.parallel_tasks(...)
        else:
            return WorkflowPatterns.sequential_pipeline(...)
```

### Progress Monitoring

```python
# With callback
def progress_handler(progress: WorkflowProgress):
    print(f"[{progress.percentage:.0f}%] {progress.current_step}: {progress.status}")
    
    if progress.estimated_remaining:
        print(f"  ETA: {progress.estimated_remaining:.0f}s")

agent = WorkflowAgent(
    progress_callback=progress_handler,
    progress_update_interval=1.0  # Update every second
)

# With async iteration
async for progress in agent.stream_workflow(task, workflow):
    await update_ui(progress)
    
    if progress.status == StepStatus.FAILED:
        await alert_user(progress.message)
```

### Workflow Optimization

```python
# Enable workflow optimization
agent = WorkflowAgent(
    enable_optimization=True,
    optimization_strategy="performance"  # or "cost", "balanced"
)

# Optimize existing workflow
optimized = await agent.optimize_workflow(
    workflow,
    constraints={
        "max_duration": 3600,
        "max_cost": 100,
        "required_quality": 0.9
    }
)

# Get optimization suggestions
suggestions = await agent.analyze_workflow(workflow)
print(suggestions)
# {
#     "parallel_opportunities": [...],
#     "redundant_steps": [...],
#     "optimization_potential": 0.35
# }
```

### Error Handling and Recovery

```python
# Configure error handling
agent = WorkflowAgent(
    retry_failed_steps=True,
    retry_strategy="exponential_backoff",
    max_retries=3,
    error_handlers={
        "network_error": lambda e: wait_and_retry(e),
        "validation_error": lambda e: fix_and_retry(e),
        "critical_error": lambda e: alert_and_stop(e)
    }
)

# Execute with error recovery
try:
    result = await agent.run_workflow(
        "Critical process",
        workflow,
        on_error="continue_with_defaults"  # or "stop", "skip"
    )
except WorkflowExecutionError as e:
    # Access partial results
    partial = e.partial_results
    failed_step = e.failed_at
    
    # Attempt recovery
    recovery_workflow = agent.create_recovery_workflow(
        original_workflow=workflow,
        failed_step=failed_step,
        partial_results=partial
    )
    
    result = await agent.run_workflow(
        "Recovery process",
        recovery_workflow
    )
```

## Integration Examples

### With Reasoning Patterns

```python
# Combine with reasoning for intelligent execution
reasoning_agent = ReasoningAgent(reasoning_pattern="chain_of_thought")
workflow_agent = WorkflowAgent()

# Plan with reasoning
reasoning_result = await reasoning_agent.think_and_act(
    "Plan the optimal workflow for data migration"
)

# Parse and execute
workflow = workflow_agent.parse_reasoning_to_workflow(reasoning_result)
result = await workflow_agent.run_workflow("Execute plan", workflow)
```

### With Streaming

```python
# Stream workflow execution with detailed updates
agent = WorkflowAgent(enable_streaming=True)

async def process_with_ui_updates():
    async for progress in agent.stream_workflow(task, workflow):
        # Update progress bar
        update_progress_bar(progress.percentage)
        
        # Show current step
        update_step_display(progress.current_step, progress.status)
        
        # Log outputs
        if progress.step_output:
            log_output(progress.step_output)
```

### With Templates

```python
# Use templates with enhanced execution
template = WorkflowTemplates.research_workflow(
    topic="Market Analysis",
    depth="comprehensive"
)

# Execute with enhancements
agent = WorkflowAgent(
    enable_checkpoints=True,
    enable_visualization=True
)

# Visualize before execution
preview = agent.visualize_execution(template)
display(preview)

# Execute with monitoring
result = await agent.run_workflow(
    "Q4 Market Analysis",
    template,
    checkpoint_id="market_analysis_q4"
)
```

## Performance Optimization

### Execution Strategies

```python
# Configure execution strategy
agent = WorkflowAgent(
    execution_strategy="adaptive",  # Dynamically adjust parallelism
    resource_limits={
        "max_memory": "4GB",
        "max_cpu": 4,
        "max_concurrent_api_calls": 10
    },
    performance_tracking=True
)

# Get performance metrics
metrics = agent.get_performance_metrics()
print(f"Average step duration: {metrics.avg_step_duration}s")
print(f"Parallelism efficiency: {metrics.parallelism_efficiency:.2%}")
```

### Caching

```python
# Enable caching
agent = WorkflowAgent(
    enable_caching=True,
    cache_strategy="content_based",  # Cache based on inputs
    cache_ttl=3600  # 1 hour
)

# Manual cache management
agent.cache_step_result("data_fetch", result_data)
cached = agent.get_cached_result("data_fetch")
```

## Best Practices

1. **Use Checkpoints for Long Workflows**: Enable for workflows > 5 minutes
2. **Monitor Progress**: Use callbacks or streaming for user feedback
3. **Plan Before Execution**: Use `plan_workflow()` for complex tasks
4. **Visualize Complex Workflows**: Always visualize before execution
5. **Handle Errors Gracefully**: Configure appropriate error handlers
6. **Optimize Parallel Execution**: Group independent steps
7. **Cache Expensive Operations**: Enable caching for repeated workflows

## See Also

- [Workflow Patterns](patterns.md) - Pre-built workflow patterns
- [Workflow Templates](templates.md) - Production-ready templates
- [Workflow Visualization](visualization.md) - Visualization options
- [Examples](../../examples/workflows/) - Complete examples
