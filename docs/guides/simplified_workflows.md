# Simplified Workflow Approach

This guide explains the simplified approach to creating workflows in AgentiCraft that prioritizes reliability and ease of use.

## Overview

After extensive testing, we've identified a simplified pattern that makes workflows more reliable and easier to understand. This approach removes complex features in favor of straightforward, predictable behavior.

## Key Principles

### 1. Direct Values Over Variable Substitution

**Avoid**: Complex variable substitution with `$variable` syntax
```python
# This can be unreliable
workflow.add_step(
    name="analyze",
    action="Analyze $previous_result",
    inputs={"data": "$extracted_data"}
)
```

**Prefer**: Direct values in prompts
```python
# More reliable
workflow.add_step(
    name="analyze", 
    action="Analyze the extracted keywords from the previous step",
    depends_on=["extract"]
)
```

### 2. Clear Separation of Concerns

- **Handlers**: For data operations, file I/O, API calls
- **AI Steps**: For natural language processing, analysis, generation

```python
# Data operation with handler
workflow.add_step(
    name="load_data",
    handler="load_handler",
    action="Loading data"
)

# AI operation without handler  
workflow.add_step(
    name="analyze",
    action="Analyze the loaded data and provide insights",
    depends_on=["load_data"]
)
```

### 3. Linear or Simple Branching Flows

Keep workflows simple and easy to follow:

```python
# Good: Clear linear flow
step1 → step2 → step3 → step4

# Good: Simple branching
step1 → step2a ↘
              → step4
step1 → step2b ↗

# Avoid: Complex interdependencies
step1 ↔ step2 ↔ step3
  ↓       ↓      ↓
step4 ← step5 → step6
```

## The Working Pattern

Here's the reliable pattern for creating workflows:

```python
# 1. Create WorkflowAgent
agent = WorkflowAgent(
    name="MyAgent",
    instructions="Clear instructions for the agent"
)

# 2. Define handlers for data operations
def data_handler(agent, step, context):
    """Process data and update context."""
    input_data = context.get("input", "")
    result = process_data(input_data)
    context["processed"] = result
    return f"Processed {len(result)} items"

# 3. Register handlers
agent.register_handler("process", data_handler)

# 4. Create workflow
workflow = agent.create_workflow(
    "my_workflow",
    "Simple workflow description"
)

# 5. Add steps in order
# Data step
workflow.add_step(
    name="process",
    handler="process",
    action="Processing input data"
)

# AI step
workflow.add_step(
    name="analyze",
    action="Analyze the processed data and identify patterns",
    depends_on=["process"]
)

# Another data step
workflow.add_step(
    name="save",
    handler="save_handler",
    action="Saving results",
    depends_on=["analyze"]
)

# 6. Execute with context
context = {"input": "your data"}
result = await agent.execute_workflow(workflow, context=context)

# 7. Post-process if needed
if result.status == StepStatus.COMPLETED:
    # Access specific step results
    analysis = result.step_results.get("analyze")
    if analysis and analysis.result:
        context["final_analysis"] = analysis.result
```

## Practical Examples

### Example 1: Simple Data Pipeline

```python
# Extract → Transform → Load pattern
def extract_handler(agent, step, context):
    data = fetch_from_source()
    context["raw_data"] = data
    return f"Extracted {len(data)} records"

def transform_handler(agent, step, context):
    raw = context.get("raw_data", [])
    clean = [clean_record(r) for r in raw]
    context["clean_data"] = clean
    return f"Transformed {len(clean)} records"

def load_handler(agent, step, context):
    data = context.get("clean_data", [])
    save_to_database(data)
    return "Data loaded successfully"

# Register all handlers
agent.register_handler("extract", extract_handler)
agent.register_handler("transform", transform_handler)
agent.register_handler("load", load_handler)

# Create simple ETL workflow
workflow.add_step("extract", handler="extract")
workflow.add_step("transform", handler="transform", depends_on=["extract"])
workflow.add_step("load", handler="load", depends_on=["transform"])
```

### Example 2: AI Analysis Pipeline

```python
# Research → Analyze → Report pattern
workflow.add_step(
    name="research",
    action="Research the topic of quantum computing applications"
)

workflow.add_step(
    name="analyze",
    action="Analyze the research and identify key trends",
    depends_on=["research"]
)

workflow.add_step(
    name="report",
    action="Write a concise report on the findings",
    depends_on=["analyze"]
)
```

## Tips for Success

### 1. Keep It Simple
- Start with 3-5 steps maximum
- Add complexity only when needed
- Test each step individually first

### 2. Use Handlers for Data
- File operations
- API calls
- Database queries
- Data transformations

### 3. Use Action for AI
- Analysis and insights
- Content generation
- Decision making
- Natural language tasks

### 4. Store Results in Context
```python
# After workflow completes
if result.status == StepStatus.COMPLETED:
    # Get AI-generated content
    report = result.step_results.get("generate_report")
    if report and report.result:
        context["final_report"] = report.result
        
    # Use it in subsequent operations
    save_report(context["final_report"])
```

### 5. Test Incrementally
1. Test handlers independently
2. Test single-step workflows
3. Add steps one at a time
4. Verify context updates

## Common Issues and Solutions

### Issue 1: "No data available"
**Cause**: Trying to access context data that doesn't exist
**Solution**: Always use `.get()` with defaults
```python
data = context.get("key", default_value)
```

### Issue 2: Variable substitution failures
**Cause**: Using `$variable` syntax
**Solution**: Use explicit values in prompts

### Issue 3: Async handler issues
**Cause**: Mixing async/sync incorrectly
**Solution**: Keep handlers simple and synchronous when possible

### Issue 4: Complex dependencies
**Cause**: Circular or complex step dependencies
**Solution**: Use linear or simple branching flows

## Best Practices

1. **Name steps clearly**: Use descriptive names like `extract_keywords`, not `step1`
2. **Add logging**: Include print statements in handlers for debugging
3. **Handle errors**: Add try/except blocks in handlers
4. **Document context**: Comment what each handler expects and produces
5. **Keep handlers focused**: One handler, one responsibility

## Summary

The simplified approach prioritizes:
- **Reliability** over complex features
- **Clarity** over clever abstractions  
- **Predictability** over flexibility

This approach has proven to work consistently across all providers and scenarios, making it the recommended pattern for production workflows.

## Related Resources

- [Workflow Handler Pattern](./workflow_handler_pattern.md) - Detailed handler guide
- [Workflow API Reference](../api/workflows.md) - Complete API documentation
- [Examples](../../examples/workflows/) - Working examples using this approach
