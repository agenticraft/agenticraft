# Tools

Tools extend your agents' capabilities by allowing them to interact with external systems, APIs, and perform specialized tasks.

## Creating Tools

The simplest way to create a tool is with the `@tool` decorator:

```python
from agenticraft import tool

@tool
def weather(location: str) -> str:
    """Get the current weather for a location."""
    # Implementation here
    return f"Sunny in {location}, 72°F"

# Use the tool
agent = Agent(name="WeatherBot", tools=[weather])
response = agent.run("What's the weather in San Francisco?")
```

## Tool Parameters

Tools support type hints and documentation:

```python
@tool
def calculate(
    expression: str,
    precision: int = 2
) -> float:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: The math expression to evaluate
        precision: Decimal places for the result
        
    Returns:
        The calculated result
    """
    result = eval(expression)
    return round(result, precision)
```

## Tool Best Practices

1. **Clear Descriptions**: The docstring is used by the LLM to understand when to use the tool
2. **Type Hints**: Always use type hints for better LLM understanding
3. **Error Handling**: Tools should handle errors gracefully
4. **Single Purpose**: Each tool should do one thing well

## Advanced Tools

For more complex tools, use the `Tool` class:

```python
from agenticraft import Tool

class DatabaseTool(Tool):
    def __init__(self, connection_string: str):
        super().__init__(
            name="database_query",
            description="Query the database",
            parameters={
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                }
            }
        )
        self.conn = connect(connection_string)
    
    def execute(self, query: str) -> str:
        # Execute query and return results
        pass
```

## Built-in Tools

AgentiCraft provides common tools out of the box:
- Web search
- File operations
- API calls
- Data processing

## Tool Composition

Combine multiple tools for complex workflows:

```python
@tool
def search(query: str) -> str:
    """Search the web."""
    # Implementation
    
@tool
def summarize(text: str) -> str:
    """Summarize text."""
    # Implementation

# Agent can use both tools together
agent = Agent(
    name="ResearchBot",
    tools=[search, summarize]
)

response = agent.run("Research and summarize recent AI developments")
# Agent will search, then summarize the results
```

## Next Steps

- [Create your first tool](../getting-started/first-agent.md)
- [Learn about workflows](workflows.md)
- [Explore MCP tools](../features/mcp_integration.md)
