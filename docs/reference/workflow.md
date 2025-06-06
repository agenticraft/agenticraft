# Workflow API Reference

The Workflow system enables complex multi-step processes with dependencies, parallel execution, and error handling.

## WorkflowAgent

The primary class for executing workflows.

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(
    name="Processor",
    model="gpt-4",
    parallel=True  # Enable parallel step execution
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Agent name |
| `model` | `str` | `"gpt-4"` | LLM model |
| `parallel` | `bool` | `False` | Enable parallel execution |
| `max_workers` | `int` | `4` | Max parallel workers |
| `timeout` | `float` | `300` | Step timeout in seconds |

### Methods

#### run_workflow(prompt: str, workflow: List[Step]) -> WorkflowResponse

Execute a workflow with the given prompt.

```python
workflow = [
    Step("step1", "Do first task"),
    Step("step2", "Do second task", depends_on=["step1"])
]

result = agent.run_workflow("Process data", workflow)
```

## Step

Define individual workflow steps.

```python
from agenticraft import Step

step = Step(
    name="process_data",
    description="Process the input data",
    depends_on=["previous_step"],
    condition="if data exists",
    retry_count=3,
    timeout=60
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Unique step identifier |
| `description` | `str` | required | What the step does |
| `depends_on` | `List[str]` | `[]` | Steps that must complete first |
| `condition` | `str` | `None` | Condition for execution |
| `retry_count` | `int` | `0` | Number of retries on failure |
| `timeout` | `float` | `None` | Step timeout override |
| `parallel` | `bool` | `True` | Can run in parallel |
| `fallback` | `str` | `None` | Fallback step on failure |

## Workflow Patterns

### Sequential Workflow

```python
sequential_workflow = [
    Step("fetch", "Fetch data from source"),
    Step("validate", "Validate data", depends_on=["fetch"]),
    Step("transform", "Transform data", depends_on=["validate"]),
    Step("save", "Save results", depends_on=["transform"])
]
```

### Parallel Workflow

```python
parallel_workflow = [
    # These run in parallel
    Step("fetch_users", "Get user data"),
    Step("fetch_orders", "Get order data"),
    Step("fetch_products", "Get product data"),
    
    # This waits for all three
    Step("combine", "Combine all data",
         depends_on=["fetch_users", "fetch_orders", "fetch_products"])
]
```

### Conditional Workflow

```python
conditional_workflow = [
    Step("check_cache", "Check if data is cached"),
    Step("fetch_remote", "Fetch from API",
         condition="if not cached"),
    Step("process", "Process the data",
         depends_on=["check_cache", "fetch_remote"])
]
```

### Error Handling Workflow

```python
resilient_workflow = [
    Step("risky_operation", "Perform risky operation",
         retry_count=3,
         fallback="safe_operation"),
    Step("safe_operation", "Fallback operation",
         skip_by_default=True),
    Step("continue", "Continue processing",
         depends_on=["risky_operation", "safe_operation"])
]
```

## WorkflowResponse

The response from workflow execution.

```python
@dataclass
class WorkflowResponse:
    content: str  # Final result
    steps: Dict[str, StepResult]  # Results by step name
    duration: float  # Total execution time
    success: bool  # Overall success status
```

### StepResult

```python
@dataclass
class StepResult:
    name: str  # Step name
    status: str  # "success", "failed", "skipped"
    output: str  # Step output
    error: Optional[str]  # Error message if failed
    duration: float  # Execution time
    retries: int  # Number of retries used
```

## Advanced Features

### Custom Step Handlers

```python
def custom_handler(context: Dict[str, Any]) -> str:
    """Custom step implementation."""
    previous_output = context.get("previous_step_output")
    # Custom logic
    return "Custom result"

agent.set_step_handler("custom_step", custom_handler)
```

### Progress Callbacks

```python
def on_step_complete(step_name: str, result: StepResult):
    print(f"Completed {step_name}: {result.status}")

agent.on_step_complete = on_step_complete
```

### Workflow Templates

```python
class DataPipelineTemplate:
    @staticmethod
    def create(source: str, destination: str) -> List[Step]:
        return [
            Step("extract", f"Extract from {source}"),
            Step("transform", "Clean and transform"),
            Step("load", f"Load to {destination}"),
            Step("verify", "Verify data integrity")
        ]

# Use template
workflow = DataPipelineTemplate.create("database", "warehouse")
result = agent.run_workflow("Run ETL", workflow)
```

### Dynamic Workflows

```python
def build_workflow(task_count: int) -> List[Step]:
    """Build workflow dynamically based on input."""
    workflow = []
    
    # Create parallel tasks
    for i in range(task_count):
        workflow.append(
            Step(f"task_{i}", f"Process chunk {i}")
        )
    
    # Add aggregation step
    task_names = [f"task_{i}" for i in range(task_count)]
    workflow.append(
        Step("aggregate", "Combine results",
             depends_on=task_names)
    )
    
    return workflow

# Use dynamic workflow
dynamic = build_workflow(5)
result = agent.run_workflow("Process in parallel", dynamic)
```

## Best Practices

1. **Step Granularity**: Keep steps focused on single tasks
2. **Clear Dependencies**: Explicitly define step relationships
3. **Error Handling**: Use retries and fallbacks for reliability
4. **Timeouts**: Set appropriate timeouts for long-running steps
5. **Logging**: Enable detailed logging for debugging

## Complete Example

```python
from agenticraft import WorkflowAgent, Step
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class ReportGenerator:
    def __init__(self):
        self.agent = WorkflowAgent(
            name="ReportGen",
            model="gpt-4",
            parallel=True,
            max_workers=3
        )
    
    def generate_report(self, company: str, quarter: str):
        """Generate quarterly report."""
        
        workflow = [
            # Data collection (parallel)
            Step("financial_data", 
                 f"Get financial data for {company} Q{quarter}"),
            Step("market_data",
                 f"Get market analysis for Q{quarter}"),
            Step("competitor_data",
                 f"Get competitor analysis"),
            
            # Analysis (depends on data)
            Step("financial_analysis",
                 "Analyze financial performance",
                 depends_on=["financial_data"]),
            Step("market_position",
                 "Analyze market position",
                 depends_on=["market_data", "competitor_data"]),
            
            # Report sections (parallel after analysis)
            Step("executive_summary",
                 "Write executive summary",
                 depends_on=["financial_analysis", "market_position"]),
            Step("detailed_analysis",
                 "Write detailed analysis",
                 depends_on=["financial_analysis", "market_position"]),
            Step("recommendations",
                 "Generate recommendations",
                 depends_on=["financial_analysis", "market_position"]),
            
            # Final assembly
            Step("assemble_report",
                 "Combine all sections into final report",
                 depends_on=["executive_summary", 
                           "detailed_analysis", 
                           "recommendations"]),
            
            # Quality check
            Step("quality_check",
                 "Review and polish report",
                 depends_on=["assemble_report"],
                 retry_count=2)
        ]
        
        # Set up progress tracking
        self.agent.on_step_complete = self._log_progress
        
        # Run workflow
        result = self.agent.run_workflow(
            f"Generate Q{quarter} report for {company}",
            workflow
        )
        
        return {
            "report": result.steps["assemble_report"].output,
            "summary": result.steps["executive_summary"].output,
            "duration": result.duration,
            "success": result.success
        }
    
    def _log_progress(self, step_name: str, result: StepResult):
        """Log step progress."""
        status_emoji = "✅" if result.status == "success" else "❌"
        logging.info(
            f"{status_emoji} {step_name}: "
            f"{result.duration:.2f}s"
        )

# Usage
generator = ReportGenerator()
report = generator.generate_report("TechCorp", "4")
print(report["summary"])
print(f"Generated in {report['duration']:.2f} seconds")
```

## See Also

- [WorkflowAgent](agent.md#workflowagent) - WorkflowAgent class details
- [Workflow Concepts](../concepts/workflows.md) - Understanding workflows
- [Advanced Examples](../examples/advanced-agents.md) - Complex workflow examples
