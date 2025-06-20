"""
Mesh network communication pattern.

This module provides a protocol-agnostic mesh network pattern
that can be used by any protocol implementation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Set, Callable, Awaitable
import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class MeshNode:
    """Node in mesh network."""
    id: str
    address: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    neighbors: Set[str] = field(default_factory=set)
    active: bool = True


@dataclass
class MeshMessage:
    """Message in mesh network."""
    id: str
    source: str
    destination: Optional[str]  # None for broadcast
    payload: Any
    hops: List[str] = field(default_factory=list)
    ttl: int = 10


class MeshPattern(ABC):
    """Abstract mesh network pattern."""
    
    def __init__(self, node_id: str):
        """Initialize mesh node."""
        self.node_id = node_id
        self._nodes: Dict[str, MeshNode] = {}
        self._message_handlers: List[Callable[[MeshMessage], Awaitable[None]]] = []
        self._seen_messages: Set[str] = set()
        
    @abstractmethod
    async def connect(self, bootstrap_nodes: List[str]) -> None:
        """Connect to mesh network."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from mesh network."""
        pass
        
    @abstractmethod
    async def send(
        self,
        payload: Any,
        destination: Optional[str] = None
    ) -> None:
        """Send message through mesh."""
        pass
        
    def add_message_handler(
        self,
        handler: Callable[[MeshMessage], Awaitable[None]]
    ) -> None:
        """Add message handler."""
        self._message_handlers.append(handler)
        
    async def discover_nodes(self) -> List[MeshNode]:
        """Discover nodes in the mesh."""
        return list(self._nodes.values())
        
    async def get_route(self, destination: str) -> Optional[List[str]]:
        """Get route to destination node."""
        # Simple BFS implementation
        if destination not in self._nodes:
            return None
            
        visited = {self.node_id}
        queue = [(self.node_id, [self.node_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == destination:
                return path
                
            node = self._nodes.get(current)
            if node:
                for neighbor in node.neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
                        
        return None
