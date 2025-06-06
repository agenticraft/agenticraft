# MCP Integration

AgentiCraft seamlessly integrates with the Model Context Protocol (MCP) for enhanced tool capabilities.

## Overview

MCP enables agents to use tools from any MCP-compatible server, expanding capabilities without custom code.

## Basic Usage

```python
from agenticraft import Agent
from agenticraft.mcp import MCPClient

# Connect to MCP server
mcp = MCPClient("http://localhost:8080")

# Create agent with MCP tools
agent = Agent(
    name="MCPAgent",
    model="gpt-4",
    tools=mcp.get_tools()
)

# Use MCP tools naturally
response = agent.run("Search for the latest AI news")
```

## Available MCP Servers

### File System Tools
```python
mcp = MCPClient("mcp://filesystem")
agent = Agent(name="FileBot", tools=mcp.get_tools())

agent.run("List all Python files in the current directory")
agent.run("Read the README.md file")
```

### Database Tools
```python
mcp = MCPClient("mcp://postgres", 
    connection_string="postgresql://localhost/mydb"
)
agent = Agent(name="DataBot", tools=mcp.get_tools())

agent.run("Show me all users created this month")
```

### Web Tools
```python
mcp = MCPClient("mcp://web")
agent = Agent(name="WebBot", tools=mcp.get_tools())

agent.run("Search for AgentiCraft tutorials")
agent.run("Get the content of https://example.com")
```

## Custom MCP Servers

```python
from agenticraft.mcp import MCPServer, mcp_tool

class CustomMCPServer(MCPServer):
    @mcp_tool
    def get_weather(self, location: str) -> str:
        """Get weather for a location."""
        # Implementation
        return f"Sunny in {location}"

# Start server
server = CustomMCPServer()
server.start(port=8080)

# Use in agent
mcp = MCPClient("http://localhost:8080")
agent = Agent(name="WeatherBot", tools=mcp.get_tools())
```

## Best Practices

1. **Tool Discovery**
   ```python
   # List available tools
   tools = mcp.get_tools()
   for tool in tools:
       print(f"{tool.name}: {tool.description}")
   ```

2. **Error Handling**
   ```python
   try:
       mcp = MCPClient(server_url)
   except MCPConnectionError:
       # Fallback to local tools
       agent = Agent(name="LocalBot", tools=local_tools)
   ```

3. **Performance**
   - Use connection pooling for high-throughput
   - Cache tool definitions
   - Implement timeouts for reliability

## Next Steps

- [Tool examples](../examples/provider-switching.md)
- [Understanding tools](../concepts/tools.md)
- [Building MCP servers](../plugins/creating-plugins.md)
