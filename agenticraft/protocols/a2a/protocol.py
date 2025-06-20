"""
A2A Protocol implementation using core abstractions.

This module provides the refactored A2A protocol that uses
the core transport, auth, and registry abstractions.
"""
import asyncio
import logging
from typing import Any, Dict, Optional, List, Set
from uuid import uuid4

from ..base import Protocol, ProtocolConfig
from ...core.transport import Transport, Message as TransportMessage, MessageType
from ...core.auth import AuthManager
from ...core.registry import ServiceRegistry
from ...core.patterns import (
    ClientServerPattern,
    PubSubPattern,
    MeshPattern,
    ConsensusPattern
)

from .base import MessageType as A2AMessageType, Message as A2AMessage

logger = logging.getLogger(__name__)


class A2AProtocol(Protocol):
    """
    A2A (Agent-to-Agent) Protocol implementation.
    
    This protocol provides flexible agent-to-agent communication
    with support for multiple patterns: mesh, centralized, decentralized.
    """
    
    def __init__(
        self,
        pattern: str = "mesh",
        node_id: Optional[str] = None,
        peers: Optional[List[str]] = None,
        transport: Optional[Transport] = None,
        auth: Optional[AuthManager] = None,
        registry: Optional[ServiceRegistry] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize A2A protocol.
        
        Args:
            pattern: Communication pattern (mesh, centralized, decentralized)
            node_id: Node identifier (generated if None)
            peers: Initial peer addresses
            transport: Transport layer
            auth: Authentication manager
            registry: Service registry
            config: Additional configuration
        """
        self.node_id = node_id or str(uuid4())
        self.pattern = pattern
        self.peers = set(peers or [])
        
        protocol_config = ProtocolConfig(
            name="a2a",
            version="1.0",
            metadata={
                "pattern": pattern,
                "node_id": self.node_id,
                **config
            } if config else {
                "pattern": pattern,
                "node_id": self.node_id
            }
        )
        
        super().__init__(
            config=protocol_config,
            transport=transport,
            auth=auth,
            registry=registry
        )
        
        # Pattern implementation
        self._pattern_impl = self._create_pattern_implementation()
        
        # Message routing
        self._routing_table: Dict[str, str] = {}
        self._message_cache: Set[str] = set()  # For deduplication
        
        # Setup handlers
        self._setup_handlers()
        
    def _create_pattern_implementation(self):
        """Create pattern-specific implementation."""
        if self.pattern == "mesh":
            return MeshPattern(self.node_id)
        elif self.pattern == "centralized":
            return ClientServerPattern()
        elif self.pattern == "decentralized":
            return ConsensusPattern()
        elif self.pattern == "pubsub":
            return PubSubPattern()
        else:
            raise ValueError(f"Unknown pattern: {self.pattern}")
            
    def _setup_handlers(self) -> None:
        """Setup A2A message handlers."""
        self.add_handler("ping", self._handle_ping)
        self.add_handler("discover", self._handle_discover)
        self.add_handler("join", self._handle_join)
        self.add_handler("leave", self._handle_leave)
        self.add_handler("route", self._handle_route)
        self.add_handler("broadcast", self._handle_broadcast)
        
    async def start(self) -> None:
        """Start A2A protocol."""
        if self._running:
            return
            
        # Connect transport if provided
        if self.transport:
            await self.transport.connect()
            self.transport.on_message(self._handle_transport_message)
            
        # Initialize pattern
        if hasattr(self._pattern_impl, 'connect'):
            await self._pattern_impl.connect(list(self.peers))
            
        # Register in service registry
        if self.registry:
            await self.registry.register(
                name=f"a2a:{self.node_id}",
                service_type="a2a",
                endpoint=self.transport.config.url if self.transport else None,
                metadata={
                    "pattern": self.pattern,
                    "node_id": self.node_id
                },
                tags={"a2a", self.pattern}
            )
            
        self._running = True
        logger.info(f"A2A protocol started (pattern: {self.pattern}, node: {self.node_id})")
        
    async def stop(self) -> None:
        """Stop A2A protocol."""
        if not self._running:
            return
            
        # Leave network
        await self._leave_network()
        
        # Unregister from service registry
        if self.registry:
            await self.registry.unregister(f"a2a:{self.node_id}")
            
        # Disconnect pattern
        if hasattr(self._pattern_impl, 'disconnect'):
            await self._pattern_impl.disconnect()
            
        # Disconnect transport
        if self.transport:
            await self.transport.disconnect()
            
        self._running = False
        logger.info(f"A2A protocol stopped (node: {self.node_id})")
        
    async def send(
        self,
        message: Any,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Send A2A message."""
        # Create A2A message
        a2a_message = self._create_message(message, target)
        
        # Send based on pattern
        if self.pattern == "mesh":
            return await self._send_mesh(a2a_message, target, timeout)
        elif self.pattern == "centralized":
            return await self._send_centralized(a2a_message, target, timeout)
        elif self.pattern == "decentralized":
            return await self._send_decentralized(a2a_message, target, timeout)
        elif self.pattern == "pubsub":
            return await self._send_pubsub(a2a_message, target, timeout)
            
    async def receive(self, timeout: Optional[float] = None) -> Any:
        """Receive A2A message."""
        if not self.transport:
            raise RuntimeError("No transport configured")
            
        transport_message = await self.transport.receive()
        a2a_message = self._parse_transport_message(transport_message)
        
        return a2a_message.payload
        
    async def broadcast(self, message: Any) -> None:
        """Broadcast message to all peers."""
        a2a_message = self._create_message(message, None)
        a2a_message.type = A2AMessageType.BROADCAST
        
        # Send to all known peers
        tasks = []
        for peer in self.peers:
            if peer != self.node_id:
                tasks.append(self._send_to_peer(a2a_message, peer))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def join_network(self, bootstrap_nodes: List[str]) -> None:
        """Join A2A network."""
        for node in bootstrap_nodes:
            try:
                # Send join request
                response = await self.send(
                    {"type": "join", "node_id": self.node_id},
                    target=node,
                    timeout=5.0
                )
                
                if response and response.get("accepted"):
                    # Add peers from response
                    new_peers = response.get("peers", [])
                    self.peers.update(new_peers)
                    
                    logger.info(f"Joined network via {node}, discovered {len(new_peers)} peers")
                    break
                    
            except Exception as e:
                logger.warning(f"Failed to join via {node}: {e}")
                
    async def _leave_network(self) -> None:
        """Leave A2A network gracefully."""
        # Notify peers
        await self.broadcast({"type": "leave", "node_id": self.node_id})
        
    def _create_message(self, payload: Any, target: Optional[str]) -> A2AMessage:
        """Create A2A message."""
        return A2AMessage(
            id=str(uuid4()),
            source=self.node_id,
            target=target,
            type=A2AMessageType.REQUEST if target else A2AMessageType.BROADCAST,
            payload=payload,
            metadata={
                "pattern": self.pattern,
                "timestamp": asyncio.get_event_loop().time()
            }
        )
        
    async def _handle_transport_message(self, message: TransportMessage) -> None:
        """Handle message from transport."""
        try:
            a2a_message = self._parse_transport_message(message)
            
            # Check for duplicates
            if a2a_message.id in self._message_cache:
                return
                
            self._message_cache.add(a2a_message.id)
            
            # Route message
            if a2a_message.target == self.node_id:
                # Message is for us
                await self._handle_message(a2a_message)
            elif a2a_message.target:
                # Forward to target
                await self._forward_message(a2a_message)
            else:
                # Broadcast message
                await self._handle_broadcast(a2a_message)
                
        except Exception as e:
            logger.error(f"Error handling transport message: {e}")
            
    def _parse_transport_message(self, message: TransportMessage) -> A2AMessage:
        """Parse transport message into A2A message."""
        payload = message.payload
        
        if isinstance(payload, dict) and "source" in payload:
            return A2AMessage(**payload)
        else:
            # Wrap in A2A message
            return A2AMessage(
                id=message.id or str(uuid4()),
                source="unknown",
                target=None,
                type=A2AMessageType.REQUEST,
                payload=payload
            )
            
    async def _handle_message(self, message: A2AMessage) -> None:
        """Handle incoming A2A message."""
        # Extract message type from payload
        if isinstance(message.payload, dict):
            msg_type = message.payload.get("type", "unknown")
        else:
            msg_type = "unknown"
            
        handler = self._handlers.get(msg_type)
        if handler:
            response = await handler(message.payload)
            
            # Send response if needed
            if message.type == A2AMessageType.REQUEST and response is not None:
                response_msg = A2AMessage(
                    id=str(uuid4()),
                    source=self.node_id,
                    target=message.source,
                    type=A2AMessageType.RESPONSE,
                    payload=response,
                    metadata={"in_reply_to": message.id}
                )
                
                await self._send_to_peer(response_msg, message.source)
                
    async def _forward_message(self, message: A2AMessage) -> None:
        """Forward message to target."""
        # Find route to target
        next_hop = self._routing_table.get(message.target)
        
        if next_hop:
            await self._send_to_peer(message, next_hop)
        else:
            logger.warning(f"No route to {message.target}")
            
    async def _send_to_peer(self, message: A2AMessage, peer: str) -> None:
        """Send message to specific peer."""
        if not self.transport:
            return
            
        transport_message = TransportMessage(
            id=message.id,
            type=MessageType.REQUEST if message.type == A2AMessageType.REQUEST else MessageType.NOTIFICATION,
            payload=message.to_dict()
        )
        
        await self.transport.send(transport_message)
        
    # Pattern-specific sending methods
    
    async def _send_mesh(
        self,
        message: A2AMessage,
        target: Optional[str],
        timeout: Optional[float]
    ) -> Any:
        """Send via mesh pattern."""
        if hasattr(self._pattern_impl, 'send'):
            return await self._pattern_impl.send(message.payload, target)
        else:
            # Direct send
            if target:
                await self._send_to_peer(message, target)
            else:
                await self.broadcast(message.payload)
                
    async def _send_centralized(
        self,
        message: A2AMessage,
        target: Optional[str],
        timeout: Optional[float]
    ) -> Any:
        """Send via centralized pattern."""
        # In centralized pattern, route through coordinator
        # Implementation would depend on role (client/server)
        pass
        
    async def _send_decentralized(
        self,
        message: A2AMessage,
        target: Optional[str],
        timeout: Optional[float]
    ) -> Any:
        """Send via decentralized pattern."""
        # In decentralized pattern, use consensus
        # Implementation would use consensus protocol
        pass
        
    async def _send_pubsub(
        self,
        message: A2AMessage,
        target: Optional[str],
        timeout: Optional[float]
    ) -> Any:
        """Send via pub-sub pattern."""
        if hasattr(self._pattern_impl, 'publish'):
            topic = target or "default"
            await self._pattern_impl.publish(topic, message.payload)
            
    # Default handlers
    
    async def _handle_ping(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request."""
        return {
            "type": "pong",
            "node_id": self.node_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    async def _handle_discover(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle discover request."""
        return {
            "type": "discover_response",
            "node_id": self.node_id,
            "pattern": self.pattern,
            "peers": list(self.peers)
        }
        
    async def _handle_join(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle join request."""
        new_node = payload.get("node_id")
        
        if new_node:
            self.peers.add(new_node)
            logger.info(f"Node {new_node} joined network")
            
        return {
            "type": "join_response",
            "accepted": True,
            "peers": list(self.peers)
        }
        
    async def _handle_leave(self, payload: Dict[str, Any]) -> None:
        """Handle leave notification."""
        leaving_node = payload.get("node_id")
        
        if leaving_node:
            self.peers.discard(leaving_node)
            self._routing_table.pop(leaving_node, None)
            logger.info(f"Node {leaving_node} left network")
            
    async def _handle_route(self, payload: Dict[str, Any]) -> None:
        """Handle route update."""
        updates = payload.get("routes", {})
        self._routing_table.update(updates)
        
    async def _handle_broadcast(self, payload: Dict[str, Any]) -> None:
        """Handle broadcast message."""
        # Process broadcast
        await self.handle_message(payload)
        
        # Forward to other peers
        # (Implementation would include loop prevention)
        pass
