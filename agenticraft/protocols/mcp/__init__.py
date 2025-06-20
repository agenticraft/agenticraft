"""
MCP Protocol package.

This module provides the Model Context Protocol implementation
with support for tools, resources, and prompts.
"""

# Import protocol implementation
from .protocol import MCPProtocol

# Import types
from .types import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPErrorCode,
    MCPTool,
    MCPToolParameter,
    MCPResource,
    MCPPrompt,
    MCPConnectionConfig
)

# Import server and client
from .server import MCPServer
from .client import MCPClient

# Import registry
from .registry import MCPRegistry, get_global_registry

# Import tools
from .tools import (
    create_mcp_tool,
    tool_to_mcp,
    mcp_to_tool
)

# Add temporary compatibility functions
def mcp_tool(**kwargs):
    """Temporary stub for mcp_tool decorator."""
    def decorator(func):
        # Just return the function as-is for now
        return func
    return decorator

def wrap_function_as_mcp_tool(func, **kwargs):
    """Temporary stub for wrap_function_as_mcp_tool."""
    from ...core.tool import FunctionTool
    return FunctionTool(func, name=kwargs.get('name', func.__name__), description=kwargs.get('description', ''))

__all__ = [
    # Protocol
    "MCPProtocol",
    
    # Types
    "MCPRequest",
    "MCPResponse",
    "MCPError",
    "MCPErrorCode",
    "MCPTool",
    "MCPToolParameter",
    "MCPResource",
    "MCPPrompt",
    "MCPConnectionConfig",
    
    # Server and Client
    "MCPServer",
    "MCPClient",
    
    # Registry
    "MCPRegistry",
    "get_global_registry",
    
    # Tools
    "create_mcp_tool",
    "tool_to_mcp",
    "mcp_to_tool",
    "mcp_tool",
    "wrap_function_as_mcp_tool"
]
