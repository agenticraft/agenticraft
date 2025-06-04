"""Model Context Protocol (MCP) implementation for AgentiCraft.

The MCP module provides integration with the Model Context Protocol,
allowing AgentiCraft agents to discover and use tools from MCP servers.

Key components:
- Client: Connect to MCP servers and discover tools
- Server: Expose AgentiCraft tools via MCP
- Registry: Manage MCP tool registrations
- Adapters: Convert between AgentiCraft and MCP formats

Example:
    Using MCP tools with an agent::
    
        from agenticraft import Agent
        from agenticraft.protocols.mcp import MCPClient
        
        # Connect to MCP server
        mcp_client = MCPClient("ws://localhost:3000")
        await mcp_client.connect()
        
        # Create agent with MCP tools
        agent = Agent(
            name="MCPAgent",
            tools=mcp_client.get_tools()
        )
        
        # Use MCP tools transparently
        response = agent.run("Search for Python tutorials")
"""

from .client import MCPClient
from .server import MCPServer
from .registry import MCPRegistry
from .types import (
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPError,
    MCPCapability,
)
from .decorators import mcp_tool

__all__ = [
    "MCPClient",
    "MCPServer",
    "MCPRegistry",
    "MCPRequest",
    "MCPResponse",
    "MCPTool",
    "MCPError",
    "MCPCapability",
    "mcp_tool",
]
