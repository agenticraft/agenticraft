# Workflow Handler Pattern

This guide explains the handler pattern for using tools with workflows in AgentiCraft.

## Overview

The handler pattern is the recommended approach for integrating tools with WorkflowAgent. It provides a clean separation between tool operations and AI operations while avoiding common issues with message formatting.

## The Handler Pattern

### Basic Structure

```python
# 1. Define handler function
def my_handler(agent, step, context):
    """
    Handler function for workflow step.
    
    Args:
        agent: The WorkflowAgent instance
        step: The current WorkflowStep
        context: Shared workflow context (dict)
    
    Returns:
        str: Status message for the step
    """
    # Get input from context
    input_data = context.get("input_key")
    
    # Process data
    result = process_data(input_data)
    
    # Store result in context for other steps
    context["output_key"] = result
    
    # Return status message
    return f"Processed: {result}"

# 2. Register handler with agent
agent.register_handler("my_handler", my_handler)

# 3. Use in workflow step
workflow.add_step(
    name="process_step",
    handler="my_handler",  # Reference by name
    action="Processing data"  # Description for logs
)
```

### Async Handlers

Handlers can be synchronous or asynchronous:

```python
async def async_handler(agent, step, context):
    """Async handler for operations that need await."""
    result = await some_async_operation()
    context["async_result"] = result
    return "Async operation completed"
```

## Complete Example

```python
from agenticraft.agents.workflow import WorkflowAgent, StepStatus

# Create agent
agent = WorkflowAgent(
    name="DataProcessor",
    instructions="Process and analyze data"
)

# Define handlers
def extract_handler(agent, step, context):
    """Extract keywords from text."""
    text = context.get("input_text", "")
    keywords = extract_keywords(text)
    context["keywords"] = keywords
    return f"Extracted {len(keywords)} keywords"

def save_handler(agent, step, context):
    """Save results to file."""
    data = context.get("final_data", {})
    filename = save_to_file(data)
    context["saved_file"] = filename
    return f"Saved to {filename}"

# Register handlers
agent.register_handler("extract", extract_handler)
agent.register_handler("save", save_handler)

# Create workflow
workflow = agent.create_workflow("data_pipeline")

# Add steps
workflow.add_step(
    name="extract",
    handler="extract",
    action="Extracting keywords"
)

workflow.add_step(
    name="analyze",
    action="Analyze these keywords and provide insights",
    depends_on=["extract"]
)

workflow.add_step(
    name="save",
    handler="save", 
    action="Saving results",
    depends_on=["analyze"]
)

# Execute
context = {"input_text": "Your text here"}
result = await agent.execute_workflow(workflow, context=context)
```

## Mixing Handlers and AI Steps

The handler pattern works seamlessly with AI steps:

- **Handler steps**: Use the `handler` parameter for tool/data operations
- **AI steps**: Use only the `action` parameter for AI prompts

```python
# Tool operation with handler
workflow.add_step(
    name="load_data",
    handler="load_handler",
    action="Loading data from database"
)

# AI operation without handler
workflow.add_step(
    name="analyze",
    action="Analyze this data and identify key patterns",
    depends_on=["load_data"]
)
```

## Benefits

1. **No Message Format Issues**: Avoids "messages with role 'tool'" errors
2. **Clear Separation**: Tool operations vs AI operations are distinct
3. **Context Management**: Full control over data flow between steps
4. **Debugging**: Easier to debug with explicit context passing
5. **Flexibility**: Mix Python logic with AI capabilities
6. **Reliability**: Works consistently with streaming and all providers

## Best Practices

1. **Keep handlers focused**: Each handler should do one thing well
2. **Use context wisely**: Store only necessary data in context
3. **Return meaningful messages**: Help with debugging and monitoring
4. **Handle errors**: Add try/except blocks in handlers
5. **Document context keys**: Make it clear what data handlers expect/produce

## Common Patterns

### Data Processing Pipeline
```python
def load_handler(agent, step, context):
    data = load_from_source()
    context["raw_data"] = data
    return f"Loaded {len(data)} records"

def transform_handler(agent, step, context):
    raw = context.get("raw_data", [])
    transformed = transform_data(raw)
    context["clean_data"] = transformed
    return "Data transformed"

def save_handler(agent, step, context):
    data = context.get("final_report", "")
    path = save_report(data)
    return f"Saved to {path}"
```

### Multi-Agent Coordination
```python
def coordinator_handler(agent, step, context):
    """Coordinate results from multiple AI agents."""
    results = []
    for key in ["agent1_result", "agent2_result", "agent3_result"]:
        if key in context:
            results.append(context[key])
    
    context["combined_results"] = combine_results(results)
    return f"Combined {len(results)} agent outputs"
```

### Conditional Processing
```python
def quality_check_handler(agent, step, context):
    """Check quality and set condition for next steps."""
    data = context.get("processed_data", {})
    score = calculate_quality_score(data)
    
    context["quality_score"] = score
    context["needs_review"] = score < 0.8
    
    return f"Quality score: {score:.2f}"
```

## Migration from @tool Decorator

If you have existing code using the `@tool` decorator:

```python
# Old approach with @tool
@tool
def my_tool(param: str) -> str:
    return process(param)

# New approach with handler
def my_handler(agent, step, context):
    param = context.get("param", "")
    result = process(param)
    context["result"] = result
    return f"Processed: {result}"
```

## Related Examples

- `examples/agents/workflow_with_handlers.py` - Complete handler pattern example
- `examples/workflows/simple_workflow.py` - Basic workflow with handlers
- `examples/workflows/research_workflow.py` - Complex multi-step workflow
- `examples/streaming/streaming_with_handlers.py` - Streaming with handlers

## When to Use Each Pattern

### Use WorkflowAgent with Handlers When:
- You need multi-step processes
- Data must flow between steps
- You want explicit control over execution
- Building data pipelines or complex workflows

### Use Basic Agent When:
- Simple question-answer interactions
- Natural language analysis is sufficient
- Single-step operations
- Conversational interfaces

### Basic Agent Pattern

For simple operations, Basic Agent relies on instructions and natural language:

```python
from agenticraft import Agent

# Create agent with clear instructions
agent = Agent(
    name="DataAnalyzer",
    instructions="""You are a data analysis assistant.
    
    When asked to analyze numbers:
    - Calculate basic statistics (mean, min, max)
    - Identify patterns
    - Provide clear explanations
    """,
    model="gpt-4o-mini"
)

# Use natural language for analysis
response = await agent.arun(
    "Analyze these numbers: 10, 20, 30, 40, 50. "
    "Calculate the average and tell me if there's a pattern."
)
```

## Telemetry Integration

Both agent types are fully instrumented for telemetry:

- **Basic Agent**: Telemetry captures all `arun()` calls automatically
- **WorkflowAgent**: Telemetry captures handler executions and workflow steps

No additional instrumentation code needed! Enable telemetry and all operations are tracked:

```python
from agenticraft.telemetry.integration import TelemetryConfig

# Enable telemetry
telemetry = TelemetryConfig(enabled=True)
telemetry.initialize()

# Use agents normally - telemetry is automatic
```

## Summary

The handler pattern provides a robust, reliable way to integrate tools with WorkflowAgent. It separates concerns, provides full control over data flow, and works consistently across all scenarios including streaming and multi-provider setups.

Choose WorkflowAgent with handlers for complex operations requiring explicit control, and use Basic Agent for simpler conversational tasks. Both patterns are fully supported with automatic telemetry integration.
