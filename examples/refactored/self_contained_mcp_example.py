"""
Self-contained MCP Agent Example

This example demonstrates the MCP agent functionality without
requiring an external server by creating a local server instance.
"""
import asyncio
import logging
from typing import Dict, Any

from agenticraft.fabric import create_mcp_agent
from agenticraft.core.auth import AuthConfig
from agenticraft.protocols.mcp import MCPServer, MCPTool, MCPToolParameter

# Enable logging
logging.basicConfig(level=logging.INFO)


# Create a simple calculator tool
def create_calculator_tool() -> MCPTool:
    """Create a calculator tool for demonstration."""
    return MCPTool(
        name="calculator",
        description="Simple calculator for basic math operations",
        parameters=[
            MCPToolParameter(
                name="operation",
                type="string",
                description="Math operation: add, subtract, multiply, divide",
                enum=["add", "subtract", "multiply", "divide"]
            ),
            MCPToolParameter(
                name="a",
                type="number",
                description="First number"
            ),
            MCPToolParameter(
                name="b", 
                type="number",
                description="Second number"
            )
        ]
    )


async def calculator_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle calculator tool calls."""
    operation = params.get("operation")
    a = params.get("a", 0)
    b = params.get("b", 0)
    
    result = None
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b != 0:
            result = a / b
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: Division by zero"
                }]
            }
    
    return {
        "content": [{
            "type": "text",
            "text": f"Result of {operation}({a}, {b}) = {result}"
        }]
    }


async def run_server():
    """Run MCP server in background."""
    # Create MCP server
    server = MCPServer(name="Example MCP Server")
    
    # Register calculator tool
    calc_tool = create_calculator_tool()
    server.register_tool(calc_tool)
    
    # Set up tool handler
    server.set_tool_handler("calculator", calculator_handler)
    
    # Start server
    await server.start(host="localhost", port=8080)
    
    print("MCP Server started on http://localhost:8080")
    
    # Keep server running
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        await server.stop()


async def run_client():
    """Run MCP client to interact with server."""
    # Wait a bit for server to start
    await asyncio.sleep(2)
    
    # Create agent with MCP protocol
    agent = create_mcp_agent(
        name="example-agent",
        url="http://localhost:8080",
        auth_config=AuthConfig.none()  # No auth for local demo
    )
    
    try:
        # Start the agent
        await agent.start()
        print(f"\\nAgent '{agent.name}' connected to server")
        
        # List available tools
        tools = await agent.call(
            method="tools/list",
            params={}
        )
        print(f"\\nAvailable tools: {tools}")
        
        # Call calculator tool
        print("\\nTesting calculator tool:")
        
        # Addition
        result = await agent.call(
            method="tools/call",
            params={
                "name": "calculator",
                "arguments": {
                    "operation": "add",
                    "a": 5,
                    "b": 3
                }
            }
        )
        print(f"  5 + 3 = {result}")
        
        # Multiplication
        result = await agent.call(
            method="tools/call",
            params={
                "name": "calculator",
                "arguments": {
                    "operation": "multiply",
                    "a": 7,
                    "b": 6
                }
            }
        )
        print(f"  7 × 6 = {result}")
        
        # Division
        result = await agent.call(
            method="tools/call",
            params={
                "name": "calculator",
                "arguments": {
                    "operation": "divide",
                    "a": 20,
                    "b": 4
                }
            }
        )
        print(f"  20 ÷ 4 = {result}")
        
        # Check agent health
        health = await agent.health_check()
        print(f"\\nAgent health: {health}")
        
    finally:
        await agent.stop()
        print(f"\\nAgent '{agent.name}' stopped")


async def main():
    """Run both server and client."""
    # Start server task
    server_task = asyncio.create_task(run_server())
    
    try:
        # Run client
        await run_client()
    finally:
        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
