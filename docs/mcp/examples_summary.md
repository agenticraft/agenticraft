# MCP (Model Context Protocol) Examples Summary

## Overview

The MCP examples in AgentiCraft demonstrate how to create, expose, and consume tools through the Model Context Protocol. MCP provides a standardized way to make tools available to AI agents across different systems.

## Example Files Reviewed

### 1. **basic_server.py**
Creates a simple MCP server that exposes basic tools.

**Key Features:**
- Defines tools using `@tool` and `@mcp_tool` decorators
- Supports both WebSocket and HTTP transport modes
- Example tools: calculator, time service, text reverser, file lister

**Usage:**
```bash
# WebSocket mode (default)
python basic_server.py

# HTTP mode
python basic_server.py http
```

### 2. **basic_client.py**
Demonstrates connecting to MCP servers and using their tools.

**Key Features:**
- Auto-discovers available MCP servers
- Lists available tools from the server
- Integrates MCP tools with AgentiCraft agents
- Shows direct tool calling

**Example Code:**
```python
async with MCPClient("ws://localhost:3000") as mcp:
    # Use tools with an agent
    agent = Agent(
        name="MCPAssistant",
        tools=mcp.get_tools()
    )
    response = await agent.arun("Calculate 15 * 23")
```

### 3. **basic_client_clean.py**
A simplified mock implementation for demonstration without requiring a server.

**Key Features:**
- Self-contained example (no server needed)
- Shows the conceptual flow of MCP
- Good for understanding basics without infrastructure

### 4. **advanced_mcp_example.py**
Comprehensive example showing advanced MCP capabilities.

**Key Features:**
- Advanced tool schemas with return types and examples
- Server monitoring and metrics collection
- Streaming responses with MCP tools
- Global registry for tool management
- Error handling and recovery
- Integration with AgentiCraft agents

**Advanced Tool Example:**
```python
@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "result": {"type": "number"},
            "steps": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        }
    },
    examples=[
        {
            "input": {"problem": "What is 25% of 80?"},
            "output": {
                "result": 20,
                "steps": ["Convert 25% to decimal: 0.25", "Multiply: 0.25 × 80 = 20"],
                "confidence": 1.0
            }
        }
    ]
)
async def solve_math_problem(problem: str) -> Dict[str, Any]:
    """Solve a math word problem step by step."""
    # Implementation
```

### 5. **external_services_example.py**
Shows how to expose external services through MCP.

**Key Features:**
- Mock services for weather, database, and email
- Service composition (using multiple services together)
- System health monitoring
- Real-world integration patterns

**Services Demonstrated:**
- Weather API integration
- Database queries (users and tasks)
- Email service for notifications
- System status monitoring

## Key MCP Concepts

### 1. Creating MCP Tools

**Basic Tool:**
```python
@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    return eval(expression, {"__builtins__": {}}, {})
```

**Advanced MCP Tool:**
```python
@mcp_tool(
    returns={"type": "object", "properties": {...}},
    examples=[{"input": {...}, "output": {...}}]
)
def my_tool(param: str) -> dict:
    """Tool description."""
    return {"result": param.upper()}
```

### 2. MCP Server Setup

```python
# Create server
server = MCPServer(
    name="My Server",
    version="1.0.0",
    description="Example MCP server"
)

# Register tools
server.register_tools([tool1, tool2, tool3])

# Start server (WebSocket)
await server.start_websocket_server("localhost", 3000)

# Or create FastAPI app (HTTP)
app = server.create_fastapi_app()
```

### 3. MCP Client Usage

```python
# Connect to server
async with MCPClient("ws://localhost:3000") as client:
    # Discover tools
    tools = client.available_tools
    
    # Call a tool directly
    result = await client.call_tool("tool_name", {"param": "value"})
    
    # Use with agent
    agent = Agent(
        name="Assistant",
        tools=client.get_tools()
    )
```

## Transport Options

### WebSocket Transport
- Real-time bidirectional communication
- Lower latency for multiple calls
- Persistent connection
- Requires `websockets` package

### HTTP Transport
- Simple request/response model
- Works through firewalls/proxies
- Stateless communication
- Uses FastAPI/HTTPX

## Best Practices

1. **Tool Design**
   - Keep tools focused and single-purpose
   - Provide clear descriptions and examples
   - Use type hints for all parameters
   - Include detailed return type schemas

2. **Error Handling**
   - Wrap external service calls in try/except
   - Return meaningful error messages
   - Implement retry logic for transient failures
   - Use appropriate MCP error codes

3. **Performance**
   - Use async tools for I/O operations
   - Implement connection pooling
   - Cache results when appropriate
   - Monitor tool execution times

4. **Security**
   - Validate all input parameters
   - Sanitize file paths and commands
   - Use authentication for production
   - Limit resource access appropriately

## Testing Strategy

Based on the test files:

1. **Unit Tests** (test_mcp_integration.py)
   - Type system validation
   - Tool adapter functionality
   - Registry operations
   - Error handling

2. **Integration Tests** (test_websocket_transport.py)
   - Connection handling
   - Concurrent clients
   - Large payload handling
   - Performance benchmarks

## Common Patterns

### 1. Service Gateway Pattern
Expose multiple external services through a single MCP server:
```python
# Weather, database, email services all through one MCP gateway
server.register_tools([
    get_weather,
    query_database,
    send_email,
    get_system_status
])
```

### 2. Tool Composition
Use multiple tools together for complex operations:
```python
# Get users, check their tasks, send reminders
users = await client.call_tool("query_users", {})
for user in users:
    tasks = await client.call_tool("get_tasks", {"user_id": user.id})
    if tasks.pending > 0:
        await client.call_tool("send_reminder", {"user_id": user.id})
```

### 3. Monitoring and Metrics
Track tool usage and performance:
```python
class MonitoredMCPServer(MCPServer):
    def __init__(self):
        super().__init__()
        self.call_count = {}
        self.error_count = {}
```

## Next Steps

1. **Try the Examples:**
   ```bash
   # Terminal 1: Start server
   python examples/mcp/basic_server.py
   
   # Terminal 2: Run client
   python examples/mcp/basic_client.py
   ```

2. **Create Custom Tools:**
   - Modify examples to add your own tools
   - Experiment with different return schemas
   - Try both transport modes

3. **Build Production Services:**
   - Implement authentication
   - Add proper error handling
   - Set up monitoring and logging
   - Deploy with proper scaling

4. **Integrate with Existing Systems:**
   - Wrap existing APIs as MCP tools
   - Connect to databases
   - Integrate with message queues
   - Build service orchestration

## Dependencies

```bash
# Core MCP support
pip install agenticraft[mcp]

# WebSocket transport
pip install websockets

# HTTP server mode
pip install uvicorn

# Full installation
pip install agenticraft[mcp] websockets uvicorn
```

## Troubleshooting

1. **"No MCP server found"**
   - Ensure server is running before client
   - Check port availability
   - Verify WebSocket/HTTP URL format

2. **Import errors**
   - Install required dependencies
   - Check Python version (3.7+ required)
   - Verify agenticraft installation

3. **Tool not found**
   - Verify tool registration on server
   - Check for typos in tool names
   - Ensure server started successfully

## Conclusion

The MCP examples demonstrate a powerful pattern for exposing and consuming tools across different systems. By following these examples, you can:

- Create standardized tool interfaces
- Build scalable service gateways
- Integrate AI agents with external systems
- Monitor and manage tool usage

The examples progress from basic concepts to advanced patterns, providing a comprehensive guide to MCP integration in AgentiCraft.
