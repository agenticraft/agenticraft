#!/usr/bin/env python3
"""Basic MCP server example.

This example demonstrates how to create an MCP server that exposes
AgentiCraft tools to MCP clients.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from agenticraft import tool
from agenticraft.protocols.mcp import MCPServer, mcp_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define some example tools
@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        The result of the calculation
    """
    try:
        # Safe eval with limited scope
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


@tool
def get_time(timezone: str = "UTC") -> str:
    """Get the current time in the specified timezone.

    Args:
        timezone: Timezone name (e.g., 'UTC', 'EST', 'PST')

    Returns:
        Current time as ISO format string
    """
    # Simple implementation - just return UTC time
    return datetime.utcnow().isoformat() + "Z"


@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "original": {"type": "string"},
            "reversed": {"type": "string"},
            "length": {"type": "integer"},
        },
    },
    examples=[
        {
            "input": {"text": "hello"},
            "output": {"original": "hello", "reversed": "olleh", "length": 5},
        }
    ],
)
def reverse_text(text: str) -> dict[str, Any]:
    """Reverse a text string and provide information about it.

    Args:
        text: Text to reverse

    Returns:
        Dictionary with original, reversed text and length
    """
    return {"original": text, "reversed": text[::-1], "length": len(text)}


@tool
def list_files(directory: str = ".") -> list[str]:
    """List files in a directory.

    Args:
        directory: Directory path (default: current directory)

    Returns:
        List of file names
    """
    import os

    try:
        # Limit to safe directories for security
        safe_dirs = [".", "./examples", "./examples/mcp"]
        if directory not in safe_dirs:
            raise ValueError(f"Access to directory '{directory}' not allowed")

        files = []
        for item in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, item)):
                files.append(item)
        return files
    except Exception as e:
        raise ValueError(f"Cannot list directory: {e}")


async def run_websocket_server():
    """Run MCP server in WebSocket mode."""
    print("🚀 Starting MCP WebSocket Server")
    print("=" * 50)

    # Create server
    server = MCPServer(
        name="AgentiCraft Example Server",
        version="1.0.0",
        description="Example MCP server with basic tools",
    )

    # Register tools
    tools = [calculate, get_time, reverse_text, list_files]
    server.register_tools(tools)

    print(f"📦 Registered {len(tools)} tools:")
    for t in tools:
        print(f"   - {t.name}: {t.description}")

    print("\n🌐 Starting WebSocket server on ws://localhost:3000")
    print("📝 To test: python examples/mcp/basic_client.py")
    print("\nPress Ctrl+C to stop the server")

    try:
        await server.start_websocket_server(host="localhost", port=3000)
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")


async def run_http_server():
    """Run MCP server in HTTP mode."""
    import uvicorn

    print("🚀 Starting MCP HTTP Server")
    print("=" * 50)

    # Create server
    server = MCPServer(
        name="AgentiCraft Example HTTP Server",
        version="1.0.0",
        description="Example MCP server with HTTP interface",
    )

    # Register tools
    tools = [calculate, get_time, reverse_text, list_files]
    server.register_tools(tools)

    print(f"📦 Registered {len(tools)} tools:")
    for t in tools:
        print(f"   - {t.name}: {t.description}")

    # Get FastAPI app
    app = server.create_fastapi_app()

    print("\n🌐 Starting HTTP server on http://localhost:8000")
    print("📝 Endpoints:")
    print("   - POST /rpc - MCP RPC endpoint")
    print("   - GET /health - Health check")
    print("\nTo test: python examples/mcp/basic_client.py")
    print("\nPress Ctrl+C to stop the server")

    # Run with uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Run the MCP server."""
    import sys

    # Check for mode argument
    mode = sys.argv[1] if len(sys.argv) > 1 else "websocket"

    if mode == "http":
        # Check if uvicorn is available
        try:
            import uvicorn

            await run_http_server()
        except ImportError:
            print("❌ HTTP mode requires uvicorn")
            print("   Install with: pip install uvicorn")
            print("\n🔄 Falling back to WebSocket mode...")
            await run_websocket_server()
    else:
        # Check if websockets is available
        try:
            import websockets

            await run_websocket_server()
        except ImportError:
            print("❌ WebSocket mode requires websockets")
            print("   Install with: pip install websockets")
            print("\nFor HTTP mode, run: python basic_server.py http")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
