# Workflows

Workflows enable agents to execute complex, multi-step processes with clear structure and error handling.

## Understanding Workflows

A workflow breaks down complex tasks into manageable steps that can be executed sequentially or in parallel.

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(name="DataProcessor", model="gpt-4")

workflow = [
    Step("extract", "Extract data from the source"),
    Step("transform", "Clean and transform the data"),
    Step("analyze", "Perform analysis"),
    Step("report", "Generate a report")
]

result = agent.run_workflow("Process our Q4 sales data", workflow)
```

## Workflow Benefits

1. **Clarity**: Break complex tasks into clear steps
2. **Debugging**: See exactly where issues occur
3. **Reusability**: Save and reuse workflow patterns
4. **Progress Tracking**: Monitor execution progress
5. **Error Recovery**: Handle failures gracefully

## Step Dependencies

Define relationships between steps:

```python
workflow = [
    Step("fetch_data", "Fetch data from API"),
    Step("validate", "Validate data", depends_on=["fetch_data"]),
    Step("process", "Process data", depends_on=["validate"]),
    Step("save", "Save results", depends_on=["process"])
]
```

## Parallel Execution

Run independent steps simultaneously:

```python
workflow = [
    Step("fetch_users", "Get user data"),
    Step("fetch_orders", "Get order data"),
    Step("fetch_products", "Get product data"),
    Step("combine", "Combine all data", 
         depends_on=["fetch_users", "fetch_orders", "fetch_products"])
]
```

## Conditional Steps

Execute steps based on conditions:

```python
workflow = [
    Step("check_data", "Check if data exists"),
    Step("fetch_data", "Fetch from API", 
         condition="if no data found"),
    Step("process", "Process the data")
]
```

## Error Handling

Built-in error recovery:

```python
workflow = [
    Step("risky_operation", "Perform operation",
         retry_count=3,
         fallback="safe_operation"),
    Step("safe_operation", "Fallback operation", 
         skip_by_default=True)
]
```

## WorkflowAgent Features

The `WorkflowAgent` provides:
- Automatic step orchestration
- Progress callbacks
- Result aggregation
- Error propagation
- Step timing and metrics

## Example: Data Pipeline

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(name="ETL", model="gpt-4")

etl_workflow = [
    # Extract
    Step("extract_csv", "Read data from CSV files"),
    Step("extract_api", "Fetch data from APIs"),
    
    # Transform
    Step("merge", "Merge data sources",
         depends_on=["extract_csv", "extract_api"]),
    Step("clean", "Clean and validate data",
         depends_on=["merge"]),
    Step("enrich", "Enrich with additional data",
         depends_on=["clean"]),
    
    # Load
    Step("load", "Load into database",
         depends_on=["enrich"]),
    Step("verify", "Verify data integrity",
         depends_on=["load"])
]

result = agent.run_workflow(
    "Run ETL for customer data",
    workflow=etl_workflow
)

# Access results
for step_name, step_result in result.steps.items():
    print(f"{step_name}: {step_result.status}")
```

## Best Practices

1. **Keep Steps Focused**: Each step should have a single, clear purpose
2. **Use Descriptive Names**: Step names should indicate their function
3. **Handle Failures**: Plan for error scenarios
4. **Log Progress**: Enable debugging and monitoring
5. **Test Steps Individually**: Ensure each step works in isolation

## Next Steps

- [Learn about WorkflowAgent](../features/advanced_agents.md#workflowagent)
- [See workflow examples](../examples/provider-switching.md)
- [Build complex workflows](../getting-started/first-agent.md)
