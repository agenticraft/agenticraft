# MCP (Model Context Protocol) in AgentiCraft - Practical Guide

## Quick Start

### 1. Installation

```bash
# Install AgentiCraft with MCP support
pip install agenticraft[mcp]

# Additional dependencies
pip install websockets  # For WebSocket transport
pip install uvicorn    # For HTTP transport
```

### 2. Creating Your First MCP Server

```python
#!/usr/bin/env python3
from agenticraft import tool
from agenticraft.protocols.mcp import MCPServer, mcp_tool
import asyncio

# Define a simple tool
@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

# Define an MCP-specific tool with schema
@mcp_tool(
    returns={"type": "integer"},
    examples=[{"input": {"x": 5}, "output": 25}]
)
def square(x: int) -> int:
    """Square a number."""
    return x * x

async def main():
    # Create server
    server = MCPServer(
        name="My First MCP Server",
        version="1.0.0"
    )
    
    # Register tools
    server.register_tools([greet, square])
    
    # Start server
    print("Starting MCP server on ws://localhost:3000")
    await server.start_websocket_server("localhost", 3000)

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Using MCP Tools in an Agent

```python
#!/usr/bin/env python3
from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient
import asyncio

async def main():
    # Connect to MCP server
    async with MCPClient("ws://localhost:3000") as mcp:
        # Create agent with MCP tools
        agent = Agent(
            name="Assistant",
            instructions="You are a helpful assistant with MCP tools.",
            tools=mcp.get_tools()
        )
        
        # Use the agent
        response = await agent.arun("Please greet Alice and tell me what 7 squared is.")
        print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Patterns

### Pattern 1: Service Gateway

Expose multiple external services through a single MCP server:

```python
from agenticraft.protocols.mcp import MCPServer, mcp_tool
import httpx

@mcp_tool(returns={"type": "object"})
async def get_weather(city: str) -> dict:
    """Get weather for a city."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city}")
        return response.json()

@mcp_tool(returns={"type": "object"})
async def search_news(query: str) -> dict:
    """Search for news articles."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.news.com/search?q={query}")
        return response.json()

# Create gateway server
server = MCPServer(name="API Gateway")
server.register_tools([get_weather, search_news])
```

### Pattern 2: Tool Wrapping

Convert existing functions to MCP tools:

```python
from agenticraft.protocols.mcp import wrap_function_as_mcp_tool

# Existing function
def calculate_tax(income: float, tax_rate: float = 0.2) -> dict:
    tax = income * tax_rate
    return {"income": income, "tax": tax, "net": income - tax}

# Wrap as MCP tool
mcp_calculate_tax = wrap_function_as_mcp_tool(
    calculate_tax,
    name="tax_calculator",
    description="Calculate income tax",
    returns={
        "type": "object",
        "properties": {
            "income": {"type": "number"},
            "tax": {"type": "number"},
            "net": {"type": "number"}
        }
    }
)
```

### Pattern 3: Tool Registry

Organize and manage tools with the registry:

```python
from agenticraft.protocols.mcp import get_global_registry

registry = get_global_registry()

# Register tools by category
registry.register_agenticraft_tool(weather_tool, category="apis")
registry.register_agenticraft_tool(database_tool, category="data")
registry.register_agenticraft_tool(email_tool, category="communication")

# Search tools
math_tools = registry.search_tools("calculate")
api_tools = registry.list_tools("apis")

# Export/import tool sets
tool_config = registry.export_tools()
# Save to file or database...

# Later, restore tools
registry.import_tools(tool_config)
```

## Testing MCP Implementations

### Unit Testing Tools

```python
import pytest
from agenticraft.protocols.mcp import mcp_tool

@mcp_tool(returns={"type": "string"})
def reverse_string(text: str) -> str:
    return text[::-1]

async def test_reverse_string():
    # Test the tool directly
    result = reverse_string("hello")
    assert result == "olleh"
    
    # Test MCP metadata
    mcp_tool_obj = reverse_string.get_mcp_tool()
    assert mcp_tool_obj.name == "reverse_string"
    assert len(mcp_tool_obj.parameters) == 1
```

### Integration Testing

```python
async def test_mcp_integration():
    # Start test server
    server = MCPServer()
    server.register_tool(my_tool)
    
    server_task = asyncio.create_task(
        server.start_websocket_server("localhost", 3999)
    )
    
    try:
        # Test with client
        async with MCPClient("ws://localhost:3999") as client:
            result = await client.call_tool("my_tool", {"param": "value"})
            assert result == expected_result
    finally:
        server_task.cancel()
```

## Best Practices

### 1. Tool Design

```python
@mcp_tool(
    # Always provide return schema
    returns={
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "data": {"type": "array"}
        }
    },
    # Include examples for clarity
    examples=[
        {
            "input": {"query": "example"},
            "output": {"status": "success", "data": ["result1", "result2"]}
        }
    ]
)
async def good_tool_design(query: str) -> dict:
    """Clear description of what the tool does.
    
    Args:
        query: What to search for
        
    Returns:
        Status and results
    """
    # Implementation
```

### 2. Error Handling

```python
@mcp_tool
async def robust_tool(param: str) -> dict:
    """Tool with proper error handling."""
    try:
        # Validate input
        if not param:
            raise ValueError("Parameter cannot be empty")
        
        # Do work
        result = await external_api_call(param)
        
        return {"success": True, "data": result}
        
    except ValueError as e:
        # Return error in structured format
        return {"success": False, "error": str(e)}
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": "Internal error"}
```

### 3. Performance Optimization

```python
from functools import lru_cache

@mcp_tool
@lru_cache(maxsize=100)
def cached_tool(query: str) -> dict:
    """Tool with caching for repeated queries."""
    # Expensive operation
    return expensive_computation(query)

# For async tools
from aiocache import cached

@mcp_tool
@cached(ttl=300)  # Cache for 5 minutes
async def async_cached_tool(query: str) -> dict:
    """Async tool with caching."""
    return await expensive_async_operation(query)
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expose port for MCP server
EXPOSE 3000

CMD ["python", "mcp_server.py"]
```

### Production Configuration

```python
import os
from agenticraft.protocols.mcp import MCPServer

# Production server setup
server = MCPServer(
    name=os.getenv("MCP_SERVER_NAME", "Production MCP Server"),
    version=os.getenv("MCP_VERSION", "1.0.0")
)

# Configure based on environment
if os.getenv("ENV") == "production":
    host = "0.0.0.0"
    port = int(os.getenv("MCP_PORT", 3000))
    
    # Add authentication middleware
    server.add_middleware(AuthenticationMiddleware())
    
    # Add rate limiting
    server.add_middleware(RateLimitMiddleware(requests_per_minute=100))
else:
    host = "localhost"
    port = 3000
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   ```python
   # Check if server is running
   # Verify firewall settings
   # Try different port
   ```

2. **Tool Not Found**
   ```python
   # Verify tool registration
   server.register_tool(my_tool)  # Don't forget this!
   
   # Check tool name matches
   print(server.list_tools())  # Debug registered tools
   ```

3. **Parameter Validation Errors**
   ```python
   # Ensure parameters match schema
   @mcp_tool
   def my_tool(required_param: str, optional_param: int = 0):
       # Both params will be in schema
   ```

## Next Steps

1. **Run the Production Examples**
   ```bash
   # Terminal 1: Start production server
   python mcp_server_production.py
   
   # Terminal 2: Test with production client
   python mcp_client_production.py
   ```
   
   Or try the basic examples:
   ```bash
   cd examples/mcp
   python basic_server.py  # Terminal 1
   python basic_client.py  # Terminal 2
   ```

2. **Build Your Own Tools**
   - Start with simple tools
   - Add schemas and examples
   - Test with the client

3. **Integrate with Your Stack**
   - Wrap existing APIs
   - Connect to databases
   - Add to your agent workflows

4. **Scale Up**
   - Use the registry for tool management
   - Implement caching and optimization
   - Deploy with proper monitoring

## Resources

- [MCP Examples & Guide](../../examples/mcp/README.md) - Complete MCP documentation
- [Examples Summary](examples_summary.md) - Detailed examples documentation
- [Tools & Handlers Guide](tools_handlers_guide.md) - Integration approaches
- [Example Code](../../examples/mcp/) - All MCP examples
- Production Files (in root):
  - `mcp_server_production.py` - Production server
  - `mcp_client_production.py` - Production client

Remember: MCP is about making tools accessible across systems. Start simple, test thoroughly, and scale as needed!
