"""Base protocol interfaces for A2A communication."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of protocol messages."""
    HEARTBEAT = "heartbeat"
    DISCOVERY = "discovery"
    TASK = "task"
    RESULT = "result"
    COORDINATION = "coordination"
    CONSENSUS = "consensus"
    ERROR = "error"
    STATUS = "status"
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"


class NodeStatus(Enum):
    """Status of a protocol node."""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class ProtocolMessage:
    """Base message for A2A protocols."""
    id: UUID = field(default_factory=uuid4)
    type: MessageType = MessageType.TASK
    sender: str = ""
    target: Optional[str] = None
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "type": self.type.value,
            "sender": self.sender,
            "target": self.target,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtocolMessage":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            type=MessageType(data["type"]),
            sender=data.get("sender", ""),
            target=data.get("target"),
            content=data.get("content", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            metadata=data.get("metadata", {})
        )


@dataclass
class ProtocolNode:
    """Represents a node in the protocol network."""
    node_id: str
    capabilities: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.IDLE
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata
        }
    
    def is_active(self) -> bool:
        """Check if node is active."""
        return self.status == NodeStatus.ACTIVE
    
    def has_capability(self, capability: str) -> bool:
        """Check if node has a specific capability."""
        return capability in self.capabilities


class Protocol(ABC):
    """Abstract base class for A2A protocols."""
    
    def __init__(self, node_id: str):
        """Initialize protocol.
        
        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id
        self.nodes: Dict[str, ProtocolNode] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._running = False
        self._message_queue: asyncio.Queue = asyncio.Queue()
        
        # Add self as a node
        self.nodes[node_id] = ProtocolNode(
            node_id=node_id,
            status=NodeStatus.ACTIVE
        )
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers."""
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.DISCOVERY, self._handle_discovery)
        self.register_handler(MessageType.STATUS, self._handle_status)
    
    @abstractmethod
    async def start(self):
        """Start the protocol."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the protocol."""
        pass
    
    @abstractmethod
    async def send_message(self, message: ProtocolMessage) -> Any:
        """Send a message through the protocol."""
        pass
    
    @abstractmethod
    async def broadcast(self, message: ProtocolMessage):
        """Broadcast a message to all nodes."""
        pass
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Async function to handle the message
        """
        self.message_handlers[message_type] = handler
    
    async def handle_message(self, message: ProtocolMessage):
        """Handle an incoming message.
        
        Args:
            message: The message to handle
        """
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error handling message {message.type}: {e}")
        else:
            logger.warning(f"No handler for message type: {message.type}")
    
    async def _handle_heartbeat(self, message: ProtocolMessage):
        """Handle heartbeat message."""
        node_id = message.sender
        if node_id in self.nodes:
            self.nodes[node_id].last_heartbeat = message.timestamp
            self.nodes[node_id].status = NodeStatus(message.content.get("status", "active"))
        else:
            # New node discovered
            self.nodes[node_id] = ProtocolNode(
                node_id=node_id,
                capabilities=message.content.get("capabilities", []),
                status=NodeStatus(message.content.get("status", "active")),
                last_heartbeat=message.timestamp
            )
    
    async def _handle_discovery(self, message: ProtocolMessage):
        """Handle discovery message."""
        # Respond with our node info
        response = ProtocolMessage(
            type=MessageType.DISCOVERY,
            sender=self.node_id,
            target=message.sender,
            content={
                "capabilities": self.nodes[self.node_id].capabilities,
                "status": self.nodes[self.node_id].status.value
            }
        )
        await self.send_message(response)
    
    async def _handle_status(self, message: ProtocolMessage):
        """Handle status update message."""
        node_id = message.sender
        if node_id in self.nodes:
            self.nodes[node_id].status = NodeStatus(message.content.get("status", "active"))
    
    def get_active_nodes(self) -> List[str]:
        """Get list of active nodes."""
        return [
            node_id for node_id, node in self.nodes.items()
            if node.is_active() and node_id != self.node_id
        ]
    
    def get_nodes_with_capability(self, capability: str) -> List[str]:
        """Get nodes with a specific capability."""
        return [
            node_id for node_id, node in self.nodes.items()
            if node.has_capability(capability) and node.is_active()
        ]
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status."""
        return {
            "node_id": self.node_id,
            "total_nodes": len(self.nodes),
            "active_nodes": len(self.get_active_nodes()) + 1,  # +1 for self
            "capabilities": list(set(
                cap for node in self.nodes.values()
                for cap in node.capabilities
            )),
            "status": self.nodes[self.node_id].status.value
        }
    
    def register_capability(self, capability: str):
        """Register a capability for this node."""
        if capability not in self.nodes[self.node_id].capabilities:
            self.nodes[self.node_id].capabilities.append(capability)
    
    def unregister_capability(self, capability: str):
        """Unregister a capability for this node."""
        if capability in self.nodes[self.node_id].capabilities:
            self.nodes[self.node_id].capabilities.remove(capability)
    
    def update_status(self, status: NodeStatus):
        """Update this node's status."""
        self.nodes[self.node_id].status = status
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(node_id='{self.node_id}', nodes={len(self.nodes)})"


# Alias for backward compatibility
Message = ProtocolMessage


@dataclass
class A2AMessage:
    """A2A-specific message format."""
    id: str
    source: str
    target: Optional[str] = None
    type: MessageType = MessageType.TASK
    payload: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type.value if isinstance(self.type, Enum) else str(self.type),
            "payload": self.payload,
            "metadata": self.metadata
        }


# Additional alias for A2A protocol
A2AMessageType = MessageType


# Alias NodeInfo to ProtocolNode for compatibility
NodeInfo = ProtocolNode


class ProtocolError(Exception):
    """Base exception for protocol errors."""
    pass
