"""
AgentiCraft Protocols Package.

This module provides protocol implementations for agent communication,
including MCP (Model Context Protocol) and A2A (Agent-to-Agent) protocols.
"""

# Import base protocol
from .base import (
    Protocol,
    ProtocolConfig,
    RequestResponseProtocol,
    StreamingProtocol
)

# Import protocol implementations
from . import mcp
from . import a2a
from . import external
from . import bridges

__all__ = [
    # Base
    "Protocol",
    "ProtocolConfig", 
    "RequestResponseProtocol",
    "StreamingProtocol",
    
    # Protocol packages
    "mcp",
    "a2a",
    "external",
    "bridges"
]
