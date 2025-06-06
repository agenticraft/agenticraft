# Tool API Reference

Tools extend agent capabilities by providing functions they can call to interact with external systems.

## Creating Tools

### @tool Decorator

The simplest way to create a tool:

```python
from agenticraft import tool

@tool
def search(query: str) -> str:
    """Search the web for information."""
    # Implementation
    return f"Results for: {query}"
```

### Tool Function Requirements

1. **Type Hints**: Always include type hints for parameters and return values
2. **Docstring**: The docstring is used by the LLM to understand when to use the tool
3. **Return Values**: Tools should return strings or JSON-serializable data

### Advanced Tool Definition

```python
@tool
def complex_tool(
    required_param: str,
    optional_param: int = 10,
    another_param: bool = False
) -> dict:
    """
    A complex tool with multiple parameters.
    
    Args:
        required_param: This parameter is required
        optional_param: This one has a default value
        another_param: A boolean flag
        
    Returns:
        A dictionary with results
    """
    return {
        "result": required_param,
        "count": optional_param,
        "flag": another_param
    }
```

## Tool Class

For more control, use the Tool class directly:

```python
from agenticraft import Tool

class DatabaseTool(Tool):
    def __init__(self, connection_string: str):
        super().__init__(
            name="query_database",
            description="Execute SQL queries on the database",
            parameters={
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "limit": {
                    "type": "integer", 
                    "description": "Maximum rows to return",
                    "default": 100
                }
            }
        )
        self.conn = self._connect(connection_string)
    
    def execute(self, query: str, limit: int = 100) -> str:
        """Execute the tool logic."""
        results = self.conn.execute(query).fetchmany(limit)
        return str(results)
```

## Using Tools with Agents

### Basic Usage

```python
from agenticraft import Agent, tool

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Sunny, 72°F in {location}"

@tool
def set_reminder(task: str, time: str) -> str:
    """Set a reminder for a specific time."""
    return f"Reminder set: {task} at {time}"

# Create agent with tools
agent = Agent(
    name="Assistant",
    model="gpt-4",
    tools=[get_weather, set_reminder]
)

# Agent automatically uses tools when needed
response = agent.run("What's the weather in NYC and remind me to bring an umbrella at 3pm")
```

### Dynamic Tool Addition

```python
agent = Agent(name="Bot", model="gpt-4")

# Add tools after creation
agent.add_tool(my_tool)
agent.add_tools([tool1, tool2, tool3])

# Remove tools
agent.remove_tool("tool_name")
```

## Tool Patterns

### Error Handling

```python
@tool
def safe_tool(param: str) -> str:
    """A tool with error handling."""
    try:
        # Tool logic
        result = process(param)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### Async Tools

```python
@tool
async def async_tool(url: str) -> str:
    """An async tool for network operations."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

### Stateful Tools

```python
class StatefulTool(Tool):
    def __init__(self):
        super().__init__(
            name="counter",
            description="Increment and track a counter"
        )
        self.count = 0
    
    def execute(self) -> str:
        self.count += 1
        return f"Count is now: {self.count}"
```

### Composite Tools

```python
@tool
def research_and_summarize(topic: str) -> str:
    """Research a topic and provide a summary."""
    # Use other tools internally
    search_results = search_tool.execute(topic)
    summary = summarize_tool.execute(search_results)
    return summary
```

## Tool Configuration

### Tool Metadata

```python
@tool(
    name="custom_name",  # Override function name
    description="Custom description",
    tags=["search", "web"],
    version="1.0.0"
)
def my_tool(query: str) -> str:
    return "result"
```

### Tool Permissions

```python
@tool(
    requires_confirmation=True,  # Ask user before executing
    rate_limit=10,  # Max calls per minute
    cost=0.01  # Cost per call for tracking
)
def expensive_tool(data: str) -> str:
    return process_data(data)
```

## Built-in Tools

AgentiCraft provides several built-in tools:

```python
from agenticraft.tools import (
    web_search,
    read_file,
    write_file,
    execute_code,
    query_database
)

agent = Agent(
    name="PowerUser",
    model="gpt-4",
    tools=[web_search, read_file, write_file]
)
```

## Best Practices

1. **Clear Descriptions**: Write detailed docstrings that explain what the tool does
2. **Type Safety**: Always use type hints
3. **Error Handling**: Handle exceptions gracefully
4. **Idempotency**: Make tools idempotent when possible
5. **Security**: Validate inputs and sanitize outputs
6. **Performance**: Consider caching for expensive operations

## Examples

### Web Scraping Tool

```python
@tool
def scrape_website(url: str, selector: str = "body") -> str:
    """
    Scrape content from a website.
    
    Args:
        url: The URL to scrape
        selector: CSS selector for content (default: body)
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.select_one(selector)
    return content.text if content else "No content found"
```

### API Integration Tool

```python
@tool
def call_api(
    endpoint: str,
    method: str = "GET",
    data: dict = None
) -> str:
    """
    Make an API call.
    
    Args:
        endpoint: API endpoint URL
        method: HTTP method (GET, POST, etc.)
        data: Request data for POST/PUT
    """
    if method == "GET":
        response = requests.get(endpoint)
    elif method == "POST":
        response = requests.post(endpoint, json=data)
    
    return response.json()
```

### Data Processing Tool

```python
@tool
def analyze_csv(
    file_path: str,
    operation: str = "summary"
) -> str:
    """
    Analyze a CSV file.
    
    Args:
        file_path: Path to CSV file
        operation: Type of analysis (summary, stats, plot)
    """
    df = pd.read_csv(file_path)
    
    if operation == "summary":
        return df.describe().to_string()
    elif operation == "stats":
        return {
            "rows": len(df),
            "columns": list(df.columns),
            "missing": df.isnull().sum().to_dict()
        }
    elif operation == "plot":
        # Generate and save plot
        df.plot()
        plt.savefig("output.png")
        return "Plot saved to output.png"
```

## See Also

- [Agent API](agent.md) - Using tools with agents
- [MCP Integration](../features/mcp_integration.md) - Model Context Protocol tools
- [Creating Custom Tools](../concepts/tools.md) - Tool creation guide
