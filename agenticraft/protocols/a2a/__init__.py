"""
A2A Protocol package.

This module provides the Agent-to-Agent protocol implementation
with support for multiple communication patterns.
"""

# Import protocol implementation
from .protocol import A2AProtocol

# Import base types
from .base import (
    Protocol,
    Message,
    MessageType,
    NodeInfo,
    ProtocolError
)

# Import patterns - fix the incorrect imports
from .centralized.task_router import TaskRouter
from .decentralized.consensus import ConsensusProtocol, ConsensusType
from .hybrid.mesh_network import MeshNetwork
from .hybrid import ProtocolBridge

# Import client-server
from .client_server import (
    ClientServerProtocol,
    ProtocolServer,
    ProtocolClient
)

# Import registry
from .registry import ProtocolRegistry, get_protocol, create_protocol, list_protocols

__all__ = [
    # Protocol
    "A2AProtocol",
    
    # Base types
    "Protocol",
    "Message",
    "MessageType", 
    "NodeInfo",
    "ProtocolError",
    
    # Patterns
    "TaskRouter",
    "ConsensusProtocol",
    "ConsensusType",
    "MeshNetwork",
    "ProtocolBridge",
    
    # Client-Server
    "ClientServerProtocol",
    "ProtocolServer",
    "ProtocolClient",
    
    # Registry
    "ProtocolRegistry",
    "get_protocol",
    "create_protocol",
    "list_protocols"
]
