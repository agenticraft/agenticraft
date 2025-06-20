"""
Core communication patterns for AgentiCraft.

This module provides protocol-agnostic communication patterns
that can be used by any protocol implementation.
"""

from .client_server import ClientServerPattern, Server, Client
from .pubsub import PubSubPattern, Publisher, Subscriber, Topic
from .mesh import MeshPattern, MeshNode
from .consensus import ConsensusPattern, ConsensusNode

__all__ = [
    # Client-Server
    "ClientServerPattern",
    "Server",
    "Client",
    
    # Pub-Sub
    "PubSubPattern",
    "Publisher", 
    "Subscriber",
    "Topic",
    
    # Mesh
    "MeshPattern",
    "MeshNode",
    
    # Consensus
    "ConsensusPattern",
    "ConsensusNode"
]
