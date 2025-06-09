# Working with Handlers

Handlers extend your agents' capabilities by allowing them to interact with external systems, APIs, and perform specialized tasks. They are the recommended way to add tool-like functionality to AgentiCraft agents.

## Understanding Handlers

Handlers are functions that agents can use within workflows to perform specific operations. They provide a clean, reliable way to extend agent capabilities without the compatibility issues of decorators.

## Creating Handlers

A handler is a function with a specific signature:

```python
def my_handler(agent, step, context):
    """Handler function for a specific task."""
    # Get inputs from context
    input_data = context.get("input_key", default_value)
    
    # Perform operations
    result = perform_some_operation(input_data)
    
    # Store results in context
    context["output_key"] = result
    
    # Return status message
    return f"Operation completed: {result}"
```

## Basic Example

```python
from agenticraft.agents import WorkflowAgent

# Define handlers
def weather_handler(agent, step, context):
    """Get weather for a location."""
    location = context.get("location", "San Francisco")
    # In real implementation, call weather API
    weather_data = {
        "location": location,
        "temperature": 72,
        "conditions": "Sunny"
    }
    context["weather"] = weather_data
    return f"Weather in {location}: {weather_data['temperature']}°F, {weather_data['conditions']}"

def calculate_handler(agent, step, context):
    """Perform calculations."""
    expression = context.get("expression", "")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        context["calc_result"] = result
        return f"Calculated: {result}"
    except Exception as e:
        return f"Calculation error: {e}"

# Create agent and register handlers
agent = WorkflowAgent(name="Assistant")
agent.register_handler("weather", weather_handler)
agent.register_handler("calculate", calculate_handler)

# Use in workflow
workflow = agent.create_workflow("demo")
workflow.add_step(name="get_weather", handler="weather")
workflow.add_step(name="do_math", handler="calculate")

# Execute
context = {
    "location": "New York",
    "expression": "42 * 17"
}
result = await agent.execute_workflow(workflow, context=context)
```

## Handler Best Practices

### 1. Clear Input/Output via Context

```python
def data_processor_handler(agent, step, context):
    """Process data with clear I/O."""
    # Clearly document expected inputs
    raw_data = context.get("raw_data", [])
    processing_config = context.get("config", {})
    
    # Process
    processed = process_data(raw_data, **processing_config)
    
    # Store with descriptive keys
    context["processed_data"] = processed
    context["processing_stats"] = {
        "input_count": len(raw_data),
        "output_count": len(processed),
        "timestamp": datetime.now()
    }
    
    return f"Processed {len(processed)} items"
```

### 2. Error Handling

```python
def safe_handler(agent, step, context):
    """Handler with proper error handling."""
    try:
        data = context["required_data"]  # Will raise if missing
        result = risky_operation(data)
        context["result"] = result
        context["success"] = True
        return f"Success: {result}"
    except KeyError as e:
        context["success"] = False
        context["error"] = f"Missing required data: {e}"
        return f"Error: Missing {e}"
    except Exception as e:
        context["success"] = False
        context["error"] = str(e)
        return f"Error: {e}"
```

### 3. Async Handlers

```python
async def async_api_handler(agent, step, context):
    """Async handler for API calls."""
    url = context.get("api_url")
    params = context.get("api_params", {})
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            context["api_response"] = data
            return f"API call successful: {len(data)} records"
```

## Advanced Patterns

### Handler Wrapper Class

For organizing multiple related handlers:

```python
class DataToolkit:
    """Collection of data processing handlers."""
    
    @staticmethod
    def load_handler(agent, step, context):
        """Load data from source."""
        source = context.get("source")
        data = load_from_source(source)
        context["loaded_data"] = data
        return f"Loaded {len(data)} records"
    
    @staticmethod
    def transform_handler(agent, step, context):
        """Transform loaded data."""
        data = context.get("loaded_data", [])
        transformed = apply_transformations(data)
        context["transformed_data"] = transformed
        return f"Transformed {len(transformed)} records"
    
    @staticmethod
    def save_handler(agent, step, context):
        """Save processed data."""
        data = context.get("transformed_data", [])
        destination = context.get("destination")
        save_to_destination(data, destination)
        return f"Saved {len(data)} records to {destination}"

# Register all handlers
toolkit = DataToolkit()
agent.register_handler("load", toolkit.load_handler)
agent.register_handler("transform", toolkit.transform_handler)
agent.register_handler("save", toolkit.save_handler)
```

### Conditional Handlers

```python
def conditional_handler(agent, step, context):
    """Handler with conditional logic."""
    data_size = len(context.get("data", []))
    
    if data_size > 1000:
        # Large dataset - use batch processing
        result = batch_process(context["data"])
        context["processing_method"] = "batch"
    else:
        # Small dataset - process individually
        result = individual_process(context["data"])
        context["processing_method"] = "individual"
    
    context["result"] = result
    return f"Processed using {context['processing_method']} method"
```

### Handler Composition

```python
def composite_handler(agent, step, context):
    """Handler that uses other handlers."""
    # Call other handlers programmatically
    weather_handler(agent, step, context)
    
    # Use weather data for calculation
    temp = context["weather"]["temperature"]
    context["expression"] = f"{temp} * 9/5 + 32"  # C to F
    calculate_handler(agent, step, context)
    
    return f"Temperature conversion complete: {context['calc_result']}°F"
```

## Workflow Integration

Handlers are designed to work seamlessly with workflows:

```python
# Create a data processing pipeline
workflow = agent.create_workflow("data_pipeline")

# Sequential processing
workflow.add_step(name="load", handler="load_handler")
workflow.add_step(name="validate", handler="validate_handler", depends_on=["load"])
workflow.add_step(name="transform", handler="transform_handler", depends_on=["validate"])
workflow.add_step(name="save", handler="save_handler", depends_on=["transform"])

# Parallel processing
workflow.add_step(name="analyze1", handler="analyze_type1", depends_on=["load"], parallel=True)
workflow.add_step(name="analyze2", handler="analyze_type2", depends_on=["load"], parallel=True)
workflow.add_step(name="combine", handler="combine_analyses", depends_on=["analyze1", "analyze2"])

# Execute with context
context = {
    "source": "database",
    "destination": "data_warehouse",
    "validation_rules": {...}
}
result = await agent.execute_workflow(workflow, context=context)
```

## Built-in Handler Patterns

Common patterns you can adapt:

### API Integration
```python
def api_handler(agent, step, context):
    endpoint = context["endpoint"]
    response = requests.get(endpoint)
    context["api_data"] = response.json()
    return f"Fetched {len(context['api_data'])} items"
```

### File Operations
```python
def file_handler(agent, step, context):
    filepath = context["filepath"]
    with open(filepath, 'r') as f:
        data = json.load(f)
    context["file_data"] = data
    return f"Loaded data from {filepath}"
```

### Data Processing
```python
def process_handler(agent, step, context):
    data = context["raw_data"]
    processed = [transform(item) for item in data]
    context["processed"] = processed
    return f"Processed {len(processed)} items"
```

## Migration from Tools

If you have existing code using tools, here's how to migrate:

```python
# Old approach (doesn't work with OpenAI)
@tool
def calculate(expression: str) -> float:
    return eval(expression)

# New approach (works reliably)
def calculate_handler(agent, step, context):
    expression = context.get("expression", "")
    result = eval(expression, {"__builtins__": {}}, {})
    context["result"] = result
    return f"Calculated: {result}"

# Register and use
agent.register_handler("calculate", calculate_handler)
```

## Next Steps

- [Create your first handler](../getting-started/first-agent.md)
- [Learn about workflows](workflows.md)
- [Explore the examples](../examples/)