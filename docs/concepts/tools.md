# Tools

!!! warning "Important: Use Handlers Instead"
    The `@tool` decorator has compatibility issues with OpenAI and other providers due to message formatting requirements.
    **We strongly recommend using handlers instead.** See [Handlers](handlers.md) for the recommended approach.

## Current Status

The `@tool` decorator was designed to provide a simple way to extend agent capabilities. However, it currently has several limitations:

1. **Message Ordering Issues** - Tool response messages must immediately follow tool calls
2. **Missing Required Fields** - The `type` field is not properly set in tool calls  
3. **Schema Generation Problems** - Array parameters don't generate correct OpenAI schemas

These issues affect OpenAI and potentially other providers.

## Recommended Solution: Handlers

Handlers provide all the functionality of tools without the compatibility issues:

```python
# Instead of this (unreliable):
@tool
def calculate(expression: str) -> float:
    """Calculate a math expression."""
    return eval(expression)

agent = Agent(tools=[calculate])

# Use this (reliable):
def calculate_handler(agent, step, context):
    """Calculate a math expression."""
    expression = context.get("expression", "")
    result = eval(expression, {"__builtins__": {}}, {})
    context["result"] = result
    return f"Calculated: {result}"

agent = WorkflowAgent()
agent.register_handler("calculate", calculate_handler)
```

## Benefits of Handlers

- ✅ **Work with all providers** - No compatibility issues
- ✅ **Full control** - Direct access to context and workflow state
- ✅ **Better error handling** - Explicit error management
- ✅ **Composable** - Easy to combine and reuse
- ✅ **Production ready** - Battle-tested pattern

## Migration Guide

### Simple Tool
```python
# Old
@tool
def get_weather(city: str) -> dict:
    return {"temp": 72, "conditions": "sunny"}

# New  
def weather_handler(agent, step, context):
    city = context.get("city", "San Francisco")
    weather = {"temp": 72, "conditions": "sunny"}
    context["weather"] = weather
    return f"Weather in {city}: {weather['temp']}°F"
```

### Tool with Multiple Parameters
```python
# Old
@tool
def search(query: str, limit: int = 10) -> list:
    return perform_search(query, limit)

# New
def search_handler(agent, step, context):
    query = context.get("query", "")
    limit = context.get("limit", 10)
    results = perform_search(query, limit)
    context["search_results"] = results
    return f"Found {len(results)} results"
```

### Async Tool
```python
# Old
@tool
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# New
async def fetch_handler(agent, step, context):
    url = context.get("url")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            context["fetched_data"] = data
            return f"Fetched {len(data)} items"
```

## Using Handlers in Workflows

```python
# Create agent
agent = WorkflowAgent(name="Assistant")

# Register handlers
agent.register_handler("weather", weather_handler)
agent.register_handler("search", search_handler)

# Create workflow
workflow = agent.create_workflow("research")
workflow.add_step(name="get_weather", handler="weather")
workflow.add_step(name="search_info", handler="search", depends_on=["get_weather"])

# Execute with context
context = {
    "city": "New York",
    "query": "tourist attractions"
}
result = await agent.execute_workflow(workflow, context=context)
```

## Next Steps

- **[Read the Handlers Guide](handlers.md)** - Complete documentation on handlers
- **[See Examples](../examples/)** - Working examples using handlers
- **[Workflow Patterns](workflows.md)** - How handlers integrate with workflows

## Future Plans

We're working on fixing the underlying issues with the `@tool` decorator. Once resolved, both patterns will be supported. For now, handlers are the recommended approach for production use.