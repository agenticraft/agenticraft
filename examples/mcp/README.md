# MCP (Model Context Protocol) - Examples and Production Implementation

This directory contains both example implementations and references to the production-ready MCP files in the AgentiCraft root.

## 📁 MCP File Organization

### Production Files (in project root)
- **`mcp_server_production.py`** - Production MCP server with WebSocket support
- **`mcp_client_production.py`** - Production client with compatibility fixes
- **`mcp_websocket_compatibility.py`** - WebSocket compatibility utilities
- **`mcp_basic_demo.py`** - Basic MCP demonstration
- **`mcp_advanced_demo.py`** - Advanced features demo

### Example Files (in this directory)
- **`basic_server.py`** - Simple example server
- **`basic_client.py`** - Simple example client
- **`advanced_mcp_example.py`** - Advanced patterns
- **`external_services_example.py`** - Service gateway patterns
- **`test_*.py`** - Test implementations

### Documentation
- **`docs/mcp/practical_guide.md`** - Real-world usage patterns
- **`docs/mcp/tools_handlers_guide.md`** - Integration approaches
- **`docs/mcp/examples_summary.md`** - Detailed examples documentation

## 🚀 Quick Start

### Using Production Files

1. **Start the Production MCP Server**
   ```bash
   # From AgentiCraft root directory
   python mcp_server_production.py
   ```
   
   This starts a WebSocket server on `ws://localhost:3000` with 4 built-in tools:
   - `calculate` - Evaluate mathematical expressions
   - `reverse_text` - Reverse text with metadata
   - `get_time` - Get current time in specified timezone
   - `list_files` - List files in allowed directories

2. **Test with Production Client**
   ```bash
   # In another terminal
   python mcp_client_production.py
   ```

3. **Run the Review Tool**
   ```bash
   python tools/mcp_review_tool.py
   ```

### Using Example Files

```bash
# From this directory (examples/mcp/)
# Terminal 1: Start example server
python basic_server.py

# Terminal 2: Run example client
python basic_client.py
```

## 🛠️ Production Implementation Details

### `mcp_server_production.py`
Production-ready MCP server featuring:
- WebSocket transport with compatibility fixes
- Comprehensive error handling and logging
- 4 example tools demonstrating different patterns
- Clean, extensible architecture

Example usage:
```python
from agenticraft.protocols.mcp import MCPServer, mcp_tool

# Create and configure server
server = MCPServer(name="Production Server")
server.register_tools([calculate, reverse_text, get_time, list_files])

# Start server
await server.start_websocket_server("localhost", 3000)
```

### `mcp_client_production.py`
Production client featuring:
- WebSocket compatibility fixes for older versions
- Tool discovery and testing
- Integration with AgentiCraft agents
- Comprehensive error handling

Example usage:
```python
from agenticraft.protocols.mcp import MCPClient
from agenticraft import Agent

async with MCPClient("ws://localhost:3000") as client:
    # Use tools directly
    result = await client.call_tool("calculate", {"expression": "10 + 5"})
    
    # Or with an agent
    agent = Agent(name="Assistant", tools=client.get_tools())
    response = await agent.say("Calculate 10 + 5")
```

## 🔧 Available Tools in Production Server

```python
# 1. Calculator
result = await client.call_tool("calculate", {"expression": "10 + 5 * 2"})
# Returns: 20.0

# 2. Text Reverser  
result = await client.call_tool("reverse_text", {"text": "hello"})
# Returns: {"original": "hello", "reversed": "olleh", "length": 5}

# 3. Time Service
result = await client.call_tool("get_time", {"timezone": "UTC"})
# Returns: "2024-12-08T10:30:00Z"

# 4. File Lister
result = await client.call_tool("list_files", {"directory": "."})
# Returns: ["file1.py", "file2.txt", ...]
```

## 📚 Example Files Overview

### Basic Examples

#### `basic_server.py`
A simple MCP server that exposes basic tools like calculator, text manipulation, and file listing.

```bash
# Run WebSocket server (default)
python basic_server.py

# Run HTTP server
python basic_server.py http
```

#### `basic_client.py`
A client that connects to MCP servers, discovers tools, and uses them with AgentiCraft agents.

### Advanced Examples

#### `advanced_mcp_example.py`
Comprehensive example showing:
- Advanced MCP tools with metadata (returns, examples)
- Integration with AgentiCraft agents
- Streaming responses with MCP tools
- Server monitoring and metrics
- Global registry usage

#### `external_services_example.py`
Demonstrates exposing external services through MCP:
- Weather API integration
- Database queries
- Email service
- Service composition
- System health monitoring

### Testing Examples

#### `test_websocket_transport.py`
Tests WebSocket transport functionality including connection handling, concurrent clients, and error recovery.

#### `test_mcp_integration.py`
Comprehensive integration tests covering the type system, server/client communication, and tool adapters.

## 🎯 Key Concepts

### Creating MCP Tools

```python
from agenticraft.protocols.mcp import mcp_tool

@mcp_tool(
    returns={"type": "object", "properties": {...}},
    examples=[{"input": {...}, "output": {...}}]
)
def my_tool(param: str) -> dict:
    """Tool description."""
    return {"result": param.upper()}
```

### Starting an MCP Server

```python
from agenticraft.protocols.mcp import MCPServer

server = MCPServer(name="My Server", version="1.0.0")
server.register_tool(my_tool)

# WebSocket mode
await server.start_websocket_server("localhost", 3000)

# HTTP mode
app = server.create_fastapi_app()
```

### Connecting to MCP Servers

```python
from agenticraft.protocols.mcp import MCPClient

async with MCPClient("ws://localhost:3000") as client:
    # Discover tools
    tools = client.available_tools
    
    # Call a tool
    result = await client.call_tool("my_tool", {"param": "hello"})
    
    # Use with agent
    agent = Agent(name="Assistant", tools=client.get_tools())
```

## 🔌 Transport Options

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

## 📋 Best Practices

1. **Tool Design**
   - Keep tools focused and single-purpose
   - Provide clear descriptions and examples
   - Use type hints for parameters
   - Include return type schemas

2. **Error Handling**
   - Always wrap external service calls in try/except
   - Return meaningful error messages
   - Use appropriate MCP error codes
   - Implement retry logic for transient failures

3. **Performance**
   - Use async tools for I/O operations
   - Implement connection pooling for HTTP
   - Cache results when appropriate
   - Monitor tool execution times

4. **Security**
   - Validate all input parameters
   - Sanitize file paths and system commands
   - Use authentication for production servers
   - Limit resource access appropriately

## 🚧 Troubleshooting

### WebSocket Connection Issues
- Ensure no other service is using port 3000
- Check if `websockets` package is installed: `pip install websockets`
- Try the compatibility fixes in `mcp_websocket_compatibility.py`

### Tool Discovery Issues
- Verify tools are registered: Check server startup logs
- Ensure client is connecting to correct URL
- Use the review tool to diagnose: `python tools/mcp_review_tool.py`

### Import Errors
- Install MCP support: `pip install agenticraft[mcp]`
- Ensure you're in the AgentiCraft directory
- Check Python version (3.7+ required)

## 📦 Dependencies

```bash
# For WebSocket support
pip install websockets

# For HTTP server mode
pip install uvicorn

# For full MCP support
pip install agenticraft[mcp]
```

## 🎯 Next Steps

1. **For Production Use**: Start with the production files:
   ```bash
   python mcp_server_production.py  # Production server
   python mcp_client_production.py  # Test client
   ```

2. **For Learning**: Explore and modify these examples

3. **For Integration**: See the comprehensive guides in `docs/mcp/`

4. **For Testing**: Use `python tools/mcp_review_tool.py` to verify your setup

5. **Build Your Own**:
   - Extend the production server with custom tools
   - Create MCP gateways for external APIs
   - Deploy with proper monitoring and authentication
   - Use MCP tools in your agent workflows

## 📖 More Resources

- [Practical Guide](../../docs/mcp/practical_guide.md) - Real-world usage patterns
- [Tools & Handlers Guide](../../docs/mcp/tools_handlers_guide.md) - Integration approaches
- [Examples Summary](../../docs/mcp/examples_summary.md) - Detailed examples documentation
