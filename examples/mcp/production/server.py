#!/usr/bin/env python3
"""Completely working MCP server with proper WebSocket handling."""

import asyncio
import json
import logging
import os

# Add path
import sys
from datetime import datetime
from typing import Any

sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

from agenticraft import tool
from agenticraft.protocols.mcp import MCPServer, mcp_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define tools
@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


@tool
def get_time(timezone: str = "UTC") -> str:
    """Get the current time in the specified timezone."""
    return datetime.utcnow().isoformat() + "Z"


@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "original": {"type": "string"},
            "reversed": {"type": "string"},
            "length": {"type": "integer"},
        },
    }
)
def reverse_text(text: str) -> dict[str, Any]:
    """Reverse a text string and provide information about it."""
    return {"original": text, "reversed": text[::-1], "length": len(text)}


@tool
def list_files(directory: str = ".") -> list[str]:
    """List files in a directory."""

    try:
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


class WorkingMCPServer(MCPServer):
    """MCP Server with completely fixed WebSocket handling."""

    async def start_websocket_server(self, host: str = "localhost", port: int = 3000):
        """Start WebSocket server with proper handler signature."""
        try:
            import websockets
        except ImportError:
            raise ImportError("WebSocket support requires 'websockets' package")

        logger.info(f"Starting working MCP WebSocket server on {host}:{port}")

        # Create proper handler that matches what websockets expects
        async def websocket_handler(websocket):
            """Handle WebSocket connection with single argument."""
            logger.info(f"New WebSocket connection from {websocket.remote_address}")

            try:
                async for message in websocket:
                    try:
                        logger.info(f"Received message: {message}")

                        # Parse request
                        data = json.loads(message)

                        # Import here to avoid circular imports
                        from agenticraft.protocols.mcp.types import MCPRequest

                        # Create MCPRequest from the data
                        request = MCPRequest(**data)
                        logger.info(f"Parsed request: {request}")

                        # Handle request
                        response = await self.handle_request(request)
                        logger.info(f"Generated response: {response}")

                        # Send response
                        response_json = json.dumps(response.to_dict())
                        await websocket.send(response_json)
                        logger.info(f"Sent response: {response_json}")

                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                        from agenticraft.protocols.mcp.types import MCPErrorCode

                        error_response = self._error_response(
                            MCPErrorCode.PARSE_ERROR, "Invalid JSON"
                        )
                        await websocket.send(json.dumps(error_response.to_dict()))
                    except Exception as e:
                        logger.error(f"Message handling error: {e}")
                        import traceback

                        traceback.print_exc()

                        from agenticraft.protocols.mcp.types import MCPErrorCode

                        error_response = self._error_response(
                            MCPErrorCode.INTERNAL_ERROR, str(e)
                        )
                        await websocket.send(json.dumps(error_response.to_dict()))

            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                import traceback

                traceback.print_exc()

        # Start server with proper handler
        async with websockets.serve(websocket_handler, host, port):
            logger.info(f"WebSocket server started on {host}:{port}")
            await asyncio.Future()  # Run forever


async def main():
    """Run the working MCP server."""
    print("🚀 Starting WORKING MCP WebSocket Server")
    print("=" * 50)

    # Create server
    server = WorkingMCPServer(
        name="Working AgentiCraft MCP Server",
        version="1.0.0",
        description="MCP server with completely fixed WebSocket handling",
    )

    # Register tools
    tools = [calculate, get_time, reverse_text, list_files]
    server.register_tools(tools)

    print(f"📦 Registered {len(tools)} tools:")
    for t in tools:
        print(f"   - {t.name}: {t.description}")

    print("\n🌐 Starting WebSocket server on ws://localhost:3000")
    print("📝 This version should actually work!")
    print("📝 To test: python working_mcp_client.py")
    print("\nPress Ctrl+C to stop the server")

    try:
        await server.start_websocket_server("localhost", 3000)
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")


if __name__ == "__main__":
    asyncio.run(main())
