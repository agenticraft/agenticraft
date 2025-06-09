# Workflow Patterns API Reference

## Overview

Workflow Patterns provide pre-built, reusable workflow structures for common scenarios. These patterns implement best practices and can be customized for specific use cases.

## Class Reference

### WorkflowPatterns

```python
class WorkflowPatterns:
    """
    Collection of common workflow patterns.
    
    Static methods that generate workflow structures for
    parallel execution, conditional logic, loops, and more.
    """
```

#### Pattern Methods

##### parallel_tasks()

```python
@staticmethod
def parallel_tasks(
    name: str,
    tasks: List[Union[Step, Dict[str, Any]]],
    max_concurrent: Optional[int] = None,
    timeout: Optional[float] = None,
    error_handling: str = "fail_fast"
) -> Workflow
```

Create a workflow that executes multiple tasks in parallel.

**Parameters:**
- `name`: Workflow name
- `tasks`: List of tasks to execute in parallel
- `max_concurrent`: Maximum concurrent executions (None = unlimited)
- `timeout`: Overall timeout in seconds
- `error_handling`: How to handle errors ("fail_fast", "continue", "collect")

**Returns:**
- `Workflow`: Configured parallel workflow

**Example:**

```python
from agenticraft.workflows.patterns import WorkflowPatterns

# Create parallel data fetching workflow
parallel_fetch = WorkflowPatterns.parallel_tasks(
    name="fetch_all_data",
    tasks=[
        {"name": "fetch_users", "description": "Get user data from API"},
        {"name": "fetch_orders", "description": "Get order data from API"},
        {"name": "fetch_products", "description": "Get product catalog"}
    ],
    max_concurrent=3,
    error_handling="continue"
)

# With Step objects
parallel_process = WorkflowPatterns.parallel_tasks(
    name="process_files",
    tasks=[
        Step("process_csv", "Process CSV files", tool=csv_processor),
        Step("process_json", "Process JSON files", tool=json_processor),
        Step("process_xml", "Process XML files", tool=xml_processor)
    ],
    timeout=300
)
```

##### conditional_branch()

```python
@staticmethod
def conditional_branch(
    name: str,
    condition: Union[str, Callable],
    if_branch: List[Step],
    else_branch: Optional[List[Step]] = None,
    condition_step: Optional[Step] = None
) -> Workflow
```

Create a workflow with conditional branching logic.

**Parameters:**
- `name`: Workflow name
- `condition`: Condition expression or callable
- `if_branch`: Steps to execute if condition is true
- `else_branch`: Steps to execute if condition is false
- `condition_step`: Optional step to evaluate condition

**Returns:**
- `Workflow`: Configured conditional workflow

**Example:**

```python
# Simple conditional
conditional_flow = WorkflowPatterns.conditional_branch(
    name="quality_check",
    condition="score > 0.8",
    if_branch=[
        Step("approve", "Approve the submission"),
        Step("publish", "Publish to production")
    ],
    else_branch=[
        Step("review", "Send for manual review"),
        Step("notify", "Notify reviewers")
    ]
)

# With condition evaluation step
validation_flow = WorkflowPatterns.conditional_branch(
    name="validate_data",
    condition_step=Step("validate", "Validate data quality"),
    condition=lambda result: result.get("is_valid", False),
    if_branch=[Step("process", "Process valid data")],
    else_branch=[Step("cleanup", "Clean invalid data")]
)
```

##### retry_loop()

```python
@staticmethod
def retry_loop(
    name: str,
    task: Union[Step, List[Step]],
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_conditions: Optional[List[str]] = None,
    fallback: Optional[Step] = None
) -> Workflow
```

Create a workflow with retry logic and exponential backoff.

**Parameters:**
- `name`: Workflow name
- `task`: Task(s) to retry
- `max_retries`: Maximum retry attempts
- `backoff_factor`: Exponential backoff multiplier
- `retry_conditions`: Conditions that trigger retry
- `fallback`: Fallback step if all retries fail

**Returns:**
- `Workflow`: Configured retry workflow

**Example:**

```python
# Simple retry
retry_api = WorkflowPatterns.retry_loop(
    name="api_call_with_retry",
    task=Step("call_api", "Call external API", tool=api_tool),
    max_retries=5,
    backoff_factor=2.0,
    retry_conditions=["timeout", "rate_limit", "500_error"]
)

# With fallback
resilient_fetch = WorkflowPatterns.retry_loop(
    name="fetch_with_fallback",
    task=[
        Step("fetch_primary", "Fetch from primary source"),
        Step("parse", "Parse response")
    ],
    max_retries=3,
    fallback=Step("fetch_cache", "Get from cache")
)
```

##### map_reduce()

```python
@staticmethod
def map_reduce(
    name: str,
    map_tasks: List[Step],
    reduce_task: Step,
    batch_size: Optional[int] = None,
    map_timeout: Optional[float] = None
) -> Workflow
```

Create a map-reduce pattern for data processing.

**Parameters:**
- `name`: Workflow name
- `map_tasks`: Tasks to execute in parallel (map phase)
- `reduce_task`: Task to aggregate results (reduce phase)
- `batch_size`: Process maps in batches
- `map_timeout`: Timeout for each map task

**Returns:**
- `Workflow`: Configured map-reduce workflow

**Example:**

```python
# Data aggregation workflow
analytics = WorkflowPatterns.map_reduce(
    name="sales_analytics",
    map_tasks=[
        Step("analyze_north", "Analyze North region", tool=analyzer),
        Step("analyze_south", "Analyze South region", tool=analyzer),
        Step("analyze_east", "Analyze East region", tool=analyzer),
        Step("analyze_west", "Analyze West region", tool=analyzer)
    ],
    reduce_task=Step("aggregate", "Combine regional data", tool=aggregator),
    batch_size=2,
    map_timeout=300
)

# Document processing
doc_processor = WorkflowPatterns.map_reduce(
    name="process_documents",
    map_tasks=[Step(f"process_doc_{i}", f"Process document {i}") 
               for i in range(10)],
    reduce_task=Step("merge_results", "Merge all processed documents")
)
```

##### sequential_pipeline()

```python
@staticmethod
def sequential_pipeline(
    name: str,
    stages: List[Union[Step, List[Step]]],
    error_handling: str = "stop_on_error",
    checkpoints: bool = False
) -> Workflow
```

Create a sequential pipeline with optional stage grouping.

**Parameters:**
- `name`: Workflow name
- `stages`: List of stages (single step or step groups)
- `error_handling`: Error strategy ("stop_on_error", "skip_failed", "compensate")
- `checkpoints`: Enable checkpointing between stages

**Returns:**
- `Workflow`: Configured pipeline workflow

**Example:**

```python
# ETL pipeline
etl = WorkflowPatterns.sequential_pipeline(
    name="customer_etl",
    stages=[
        # Extract stage
        [
            Step("extract_db", "Extract from database"),
            Step("extract_api", "Extract from API")
        ],
        # Transform stage
        Step("transform", "Transform and clean data"),
        # Load stage
        [
            Step("load_warehouse", "Load to data warehouse"),
            Step("load_cache", "Update cache")
        ]
    ],
    checkpoints=True
)

# Simple pipeline
process_pipeline = WorkflowPatterns.sequential_pipeline(
    name="document_pipeline",
    stages=[
        Step("parse", "Parse document"),
        Step("analyze", "Analyze content"),
        Step("summarize", "Generate summary"),
        Step("store", "Store results")
    ],
    error_handling="compensate"
)
```

##### fan_out_fan_in()

```python
@staticmethod
def fan_out_fan_in(
    name: str,
    splitter: Step,
    processors: List[Step],
    combiner: Step,
    dynamic_processors: bool = False
) -> Workflow
```

Create a fan-out/fan-in pattern for dynamic parallelism.

**Parameters:**
- `name`: Workflow name
- `splitter`: Step that splits work into chunks
- `processors`: Steps that process chunks in parallel
- `combiner`: Step that combines results
- `dynamic_processors`: Allow dynamic number of processors

**Returns:**
- `Workflow`: Configured fan-out/fan-in workflow

**Example:**

```python
# Dynamic parallel processing
batch_processor = WorkflowPatterns.fan_out_fan_in(
    name="batch_processing",
    splitter=Step("split", "Split into batches", tool=splitter_tool),
    processors=[
        Step("process_batch", "Process a batch", tool=processor_tool)
    ],
    combiner=Step("combine", "Combine results", tool=combiner_tool),
    dynamic_processors=True
)
```

##### iterative_refinement()

```python
@staticmethod
def iterative_refinement(
    name: str,
    initial_step: Step,
    refinement_step: Step,
    evaluation_step: Step,
    max_iterations: int = 5,
    target_condition: Optional[str] = None
) -> Workflow
```

Create an iterative refinement pattern.

**Parameters:**
- `name`: Workflow name
- `initial_step`: Initial processing step
- `refinement_step`: Step that refines the result
- `evaluation_step`: Step that evaluates quality
- `max_iterations`: Maximum refinement iterations
- `target_condition`: Condition to meet for completion

**Returns:**
- `Workflow`: Configured iterative workflow

**Example:**

```python
# Content refinement
content_refiner = WorkflowPatterns.iterative_refinement(
    name="refine_content",
    initial_step=Step("draft", "Create initial draft"),
    refinement_step=Step("improve", "Improve content"),
    evaluation_step=Step("evaluate", "Evaluate quality"),
    max_iterations=3,
    target_condition="quality_score > 0.9"
)
```

## Pattern Combinations

### Nested Patterns

```python
# Combine multiple patterns
complex_workflow = WorkflowPatterns.sequential_pipeline(
    name="complex_data_pipeline",
    stages=[
        # Parallel data fetching
        WorkflowPatterns.parallel_tasks(
            name="fetch_stage",
            tasks=[
                Step("fetch_a", "Fetch dataset A"),
                Step("fetch_b", "Fetch dataset B")
            ]
        ),
        
        # Conditional processing
        WorkflowPatterns.conditional_branch(
            name="process_stage",
            condition="len(data) > 1000",
            if_branch=[
                WorkflowPatterns.map_reduce(
                    name="large_data_process",
                    map_tasks=[...],
                    reduce_task=Step("aggregate", "Aggregate results")
                )
            ],
            else_branch=[
                Step("simple_process", "Process small dataset")
            ]
        ),
        
        # Retry for reliability
        WorkflowPatterns.retry_loop(
            name="save_stage",
            task=Step("save", "Save results"),
            max_retries=3
        )
    ]
)
```

### Pattern Factory

```python
class WorkflowFactory:
    """Factory for creating customized workflow patterns."""
    
    @staticmethod
    def create_data_pipeline(
        source_type: str,
        processing_type: str,
        destination_type: str,
        **options
    ) -> Workflow:
        """Create a data pipeline based on types."""
        
        # Select appropriate patterns
        if source_type == "multiple":
            extract = WorkflowPatterns.parallel_tasks(...)
        else:
            extract = Step("extract", f"Extract from {source_type}")
        
        if processing_type == "batch":
            process = WorkflowPatterns.map_reduce(...)
        elif processing_type == "stream":
            process = WorkflowPatterns.sequential_pipeline(...)
        else:
            process = Step("process", "Process data")
        
        # Combine into pipeline
        return WorkflowPatterns.sequential_pipeline(
            name="data_pipeline",
            stages=[extract, process, load],
            **options
        )
```

## Configuration Options

### Error Handling Strategies

```python
# Fail fast - stop on first error
fail_fast = WorkflowPatterns.parallel_tasks(
    name="critical_tasks",
    tasks=[...],
    error_handling="fail_fast"
)

# Continue on error - complete all possible tasks
continue_on_error = WorkflowPatterns.parallel_tasks(
    name="best_effort_tasks",
    tasks=[...],
    error_handling="continue"
)

# Collect errors - gather all errors for analysis
collect_errors = WorkflowPatterns.parallel_tasks(
    name="validation_tasks",
    tasks=[...],
    error_handling="collect"
)
```

### Timeout Configuration

```python
# Global timeout
timed_workflow = WorkflowPatterns.sequential_pipeline(
    name="timed_pipeline",
    stages=[...],
    timeout=3600  # 1 hour total
)

# Per-step timeout
steps_with_timeout = [
    Step("quick_task", "Fast operation", timeout=10),
    Step("slow_task", "Slow operation", timeout=300),
    Step("critical_task", "Important task", timeout=None)  # No timeout
]
```

### Checkpoint Options

```python
# Enable checkpoints
checkpointed = WorkflowPatterns.sequential_pipeline(
    name="long_running",
    stages=[...],
    checkpoints=True,
    checkpoint_options={
        "storage": "disk",
        "compression": "gzip",
        "retention": "7d"
    }
)
```

## Performance Considerations

### Pattern Performance Characteristics

| Pattern | Overhead | Best For | Avoid When |
|---------|----------|----------|------------|
| Parallel Tasks | Low | I/O bound tasks | Sequential dependencies |
| Conditional Branch | Minimal | Decision trees | Complex conditions |
| Retry Loop | Variable | Unreliable operations | Non-idempotent tasks |
| Map-Reduce | Medium | Data processing | Small datasets |
| Sequential Pipeline | Low | Step-by-step processes | Parallel opportunities |

### Optimization Tips

```python
# Optimize parallel execution
optimized_parallel = WorkflowPatterns.parallel_tasks(
    name="optimized",
    tasks=tasks,
    max_concurrent=os.cpu_count(),  # Match CPU cores
    error_handling="continue"  # Don't block on single failure
)

# Optimize map-reduce
optimized_mapreduce = WorkflowPatterns.map_reduce(
    name="optimized_mr",
    map_tasks=map_tasks,
    reduce_task=reduce_task,
    batch_size=100  # Process in batches to reduce overhead
)
```

## Error Handling

### Pattern-Specific Error Handling

```python
try:
    workflow = WorkflowPatterns.parallel_tasks(
        name="tasks",
        tasks=invalid_tasks
    )
except PatternValidationError as e:
    if e.pattern == "parallel_tasks":
        print(f"Invalid parallel configuration: {e.message}")
    # Handle specific pattern errors

# Runtime error handling
try:
    result = await agent.run_workflow("Execute", workflow)
except WorkflowExecutionError as e:
    if e.pattern == "retry_loop":
        print(f"All retries exhausted: {e.last_error}")
    elif e.pattern == "conditional_branch":
        print(f"Condition evaluation failed: {e.condition}")
```

## See Also

- [Workflow Visualization](visualization.md) - Visualizing patterns
- [Workflow Templates](templates.md) - Complete workflow templates
- [WorkflowAgent](workflow_agent.md) - Pattern execution
- [Examples](../../examples/workflows/patterns_example.py) - Pattern examples
