# MCP Integration Guide

The Model Context Protocol (MCP) allows AgentiCraft agents to use tools from any MCP-compatible server, and expose AgentiCraft tools to other MCP clients.

## What is MCP?

MCP is a standardized protocol for:
- Tool discovery and description
- Tool execution across different systems
- Interoperability between AI frameworks

## Using MCP Tools in AgentiCraft

### Connecting to an MCP Server

```python
from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient

# Connect to MCP server
async with MCPClient("ws://localhost:3000") as mcp:
    # Get available tools
    tools = mcp.get_tools()
    
    # Create agent with MCP tools
    agent = Agent(
        name="MCPAgent",
        tools=tools
    )
    
    # Use tools transparently
    response = await agent.arun("Search for Python tutorials")
```

### HTTP-based MCP Server

```python
# Connect via HTTP instead of WebSocket
mcp = MCPClient("http://localhost:3000/mcp")
await mcp.connect()

# Use the same way
agent = Agent(tools=mcp.get_tools())
```

### Discovering Available Tools

```python
# List tool names
print(mcp.available_tools)

# Get specific tool
search_tool = mcp.get_tool("web_search")

# Get server info
print(mcp.server_info)
```

## Exposing AgentiCraft Tools via MCP

### Creating an MCP Server

```python
from agenticraft.protocols.mcp import MCPServer
from agenticraft import tool

# Define tools
@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression, {"__builtins__": {}})

@tool
def get_time() -> str:
    """Get current time."""
    from datetime import datetime
    return datetime.now().isoformat()

# Create MCP server
server = MCPServer(
    name="My Tools Server",
    version="1.0.0"
)

# Register tools
server.register_tools([calculate, get_time])

# Start WebSocket server
await server.start_websocket_server(port=3000)
```

### HTTP Mode with FastAPI

```python
from fastapi import FastAPI
import uvicorn

# Create server
server = MCPServer()
server.register_tools([calculate, get_time])

# Get FastAPI app
app = server.create_fastapi_app()

# Run with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Advanced MCP Tools

### MCP-Specific Tool Metadata

```python
from agenticraft.protocols.mcp import mcp_tool

@mcp_tool(
    name="weather",
    returns={
        "type": "object",
        "properties": {
            "temperature": {"type": "number"},
            "conditions": {"type": "string"},
            "humidity": {"type": "number"}
        }
    },
    examples=[
        {
            "input": {"city": "New York"},
            "output": {
                "temperature": 72,
                "conditions": "sunny",
                "humidity": 65
            }
        }
    ]
)
def get_weather(city: str) -> dict:
    """Get weather information for a city."""
    # Implementation here
    return {
        "temperature": 72,
        "conditions": "sunny",
        "humidity": 65
    }
```

### Tool Categories

```python
from agenticraft.protocols.mcp import MCPRegistry

# Get global registry
registry = MCPRegistry()

# Register tools with categories
registry.register_agenticraft_tool(
    calculate,
    category="math"
)
registry.register_agenticraft_tool(
    get_weather,
    category="data"
)

# List by category
math_tools = registry.list_tools(category="math")
```

## MCP Client Configuration

### Authentication

```python
# With API key
mcp = MCPClient(
    "wss://api.example.com/mcp",
    headers={"Authorization": "Bearer YOUR_KEY"}
)

# With custom headers
mcp = MCPClient(
    "https://api.example.com",
    headers={
        "X-API-Key": "YOUR_KEY",
        "X-Client-ID": "agenticraft"
    }
)
```

### Timeout and Retries

```python
mcp = MCPClient(
    "ws://localhost:3000",
    timeout=60,  # 60 second timeout
    max_retries=5
)
```

## Error Handling

```python
from agenticraft.core.exceptions import ToolError

try:
    async with MCPClient("ws://localhost:3000") as mcp:
        result = await mcp.call_tool("search", {"query": "AI"})
except ToolError as e:
    print(f"Tool error: {e}")
except Exception as e:
    print(f"Connection error: {e}")
```

## Best Practices

### 1. Connection Management

Always use context managers:
```python
async with MCPClient(url) as mcp:
    # Use MCP
    pass
# Connection automatically closed
```

### 2. Tool Validation

Validate tools before use:
```python
# Check if tool exists
if "web_search" in mcp.available_tools:
    tool = mcp.get_tool("web_search")
```

### 3. Error Recovery

Implement retry logic:
```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def call_with_retry(mcp, tool_name, args):
    return await mcp.call_tool(tool_name, args)
```

### 4. Tool Documentation

Always provide clear descriptions:
```python
@mcp_tool(
    description="Search the web for information",
    examples=[{
        "input": {"query": "Python tutorials"},
        "output": ["Tutorial 1", "Tutorial 2"]
    }]
)
def search(query: str) -> list:
    pass
```

## Testing MCP Integration

### Mock MCP Server

```python
from agenticraft.protocols.mcp import MCPServer

# Create test server
test_server = MCPServer()

@tool
def test_tool(input: str) -> str:
    return f"Processed: {input}"

test_server.register_tool(test_tool)

# Test with client
async with MCPClient("ws://localhost:3001") as client:
    result = await client.call_tool("test_tool", {"input": "test"})
    assert result == "Processed: test"
```

### Integration Tests

```python
import pytest

@pytest.mark.asyncio
async def test_mcp_integration():
    # Start server
    server = MCPServer()
    server.register_tool(calculate)
    
    # In real test, run server in background
    # Here we test the handler directly
    
    # Create request
    from agenticraft.protocols.mcp import MCPRequest, MCPMethod
    
    request = MCPRequest(
        method=MCPMethod.LIST_TOOLS
    )
    
    response = await server.handle_request(request)
    assert not response.is_error
    assert len(response.result["tools"]) == 1
```

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Check if server is running
   - Verify URL format (ws:// or wss://)
   - Check firewall settings

2. **Tool not found**
   - Refresh tool list: `await mcp._discover_tools()`
   - Check tool name spelling
   - Verify server has tool registered

3. **Timeout errors**
   - Increase timeout: `MCPClient(url, timeout=120)`
   - Check network latency
   - Verify server processing time

### Debug Mode

Enable detailed logging:
```python
import logging

logging.getLogger("agenticraft.protocols.mcp").setLevel(logging.DEBUG)
```

## Next Steps

- Explore [available MCP servers](https://mcp.com/servers)
- Learn about [creating custom MCP tools](creating-tools.md)
- See [MCP examples](../examples/mcp/)
