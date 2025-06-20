# AgentiCraft MCP Examples

This directory contains examples demonstrating the refactored MCP (Model Context Protocol) implementation in AgentiCraft.

## Examples

### 1. mock_mcp_example.py
A self-contained example that demonstrates MCP functionality without requiring a real server. It uses a mock transport to simulate MCP protocol interactions.

**Features demonstrated:**
- Creating an MCP agent
- Protocol initialization
- Listing available tools
- Calling tools with parameters
- Mock transport implementation

**To run:**
```bash
python examples/refactored/mock_mcp_example.py
```

### 2. simple_mcp_agent.py
An example that connects to a real MCP server. Requires an MCP server to be running.

**Features demonstrated:**
- Connecting to an MCP server over HTTP
- Bearer token authentication
- Tool discovery and execution
- Resource reading
- Health checks

**To run:**
1. First, start an MCP server on localhost:8080
2. Then run:
```bash
python examples/refactored/simple_mcp_agent.py
```

## Running an MCP Server

To use the `simple_mcp_agent.py` example, you need an MCP server. Options include:

1. **Using AgentiCraft's built-in server:**
   ```python
   from agenticraft.protocols.mcp import MCPServer
   from agenticraft.core.tool import tool
   
   # Create server
   server = MCPServer(name="My MCP Server")
   
   # Add tools
   @tool
   def calculator(operation: str, a: float, b: float) -> float:
       '''Simple calculator tool'''
       if operation == "add":
           return a + b
       # ... etc
   
   server.register_tool(calculator)
   
   # Run with FastAPI
   app = server.create_fastapi_app()
   # Then run with: uvicorn app:app --port 8080
   ```

2. **Using any MCP-compatible server** that implements the Model Context Protocol specification.

## Architecture Overview

The refactored architecture separates concerns:

- **Transport Layer**: Handles network communication (HTTP, WebSocket)
- **Auth Layer**: Manages authentication (Bearer, API Key, etc.)
- **Protocol Layer**: Implements MCP protocol logic
- **Agent Layer**: Provides unified interface for multiple protocols

This separation allows for:
- Easy testing with mock transports
- Support for multiple transport types
- Pluggable authentication strategies
- Protocol-agnostic agent interface
