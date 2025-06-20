"""
A2A adapter for AgentiCraft fabric.

This module provides the adapter implementation for A2A protocol.
"""
import logging
from typing import Any, Dict, Optional, List, Set

from .base import ProtocolAdapter
from ...protocols.a2a import A2AProtocol

logger = logging.getLogger(__name__)


class A2AAdapter(ProtocolAdapter):
    """
    Adapter for A2A (Agent-to-Agent) Protocol.
    
    This adapter provides a unified interface for A2A protocol
    within the fabric layer.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize A2A adapter."""
        super().__init__(*args, **kwargs)
        
        # Ensure protocol is A2AProtocol
        if not isinstance(self.protocol, A2AProtocol):
            raise TypeError("A2AAdapter requires A2AProtocol instance")
            
    async def _initialize_protocol(self, config: Dict[str, Any]) -> None:
        """Initialize A2A protocol."""
        # Join network if bootstrap nodes provided
        bootstrap_nodes = config.get("bootstrap_nodes", [])
        if bootstrap_nodes:
            await self.protocol.join_network(bootstrap_nodes)
            
        # Start protocol
        await self.protocol.start()
        
    async def send_message(
        self,
        message: Any,
        target: Optional[str] = None
    ) -> Any:
        """Send message via A2A."""
        return await self.protocol.send(message, target)
        
    async def receive_message(self) -> Any:
        """Receive message from A2A."""
        return await self.protocol.receive()
        
    def get_protocol_name(self) -> str:
        """Get protocol name."""
        return "a2a"
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Get A2A capabilities."""
        return {
            "pattern": self.protocol.pattern,
            "node_id": self.protocol.node_id,
            "version": self.protocol.config.version,
            "features": {
                "broadcast": True,
                "routing": True,
                "discovery": True
            }
        }
        
    # A2A-specific methods
    
    async def broadcast(self, message: Any) -> None:
        """
        Broadcast message to all peers.
        
        Args:
            message: Message to broadcast
        """
        await self.protocol.broadcast(message)
        
    async def discover_peers(self) -> List[str]:
        """
        Discover network peers.
        
        Returns:
            List of peer node IDs
        """
        return list(self.protocol.peers)
        
    async def ping_peer(self, peer_id: str) -> bool:
        """
        Ping a specific peer.
        
        Args:
            peer_id: Peer to ping
            
        Returns:
            True if peer responded
        """
        try:
            response = await self.protocol.send(
                {"type": "ping"},
                target=peer_id,
                timeout=5.0
            )
            
            return response is not None and response.get("type") == "pong"
            
        except Exception:
            return False
            
    async def get_network_info(self) -> Dict[str, Any]:
        """
        Get network information.
        
        Returns:
            Network status and topology
        """
        return {
            "node_id": self.protocol.node_id,
            "pattern": self.protocol.pattern,
            "peers": list(self.protocol.peers),
            "peer_count": len(self.protocol.peers),
            "routing_table_size": len(self.protocol._routing_table)
        }
        
    async def join_network(self, bootstrap_nodes: List[str]) -> bool:
        """
        Join A2A network.
        
        Args:
            bootstrap_nodes: Nodes to connect through
            
        Returns:
            True if successfully joined
        """
        try:
            await self.protocol.join_network(bootstrap_nodes)
            return len(self.protocol.peers) > 0
        except Exception as e:
            logger.error(f"Failed to join network: {e}")
            return False
            
    async def leave_network(self) -> None:
        """Leave A2A network gracefully."""
        await self.protocol._leave_network()
        
    def add_peer(self, peer_id: str) -> None:
        """
        Add a peer to the network.
        
        Args:
            peer_id: Peer node ID
        """
        self.protocol.peers.add(peer_id)
        
    def remove_peer(self, peer_id: str) -> None:
        """
        Remove a peer from the network.
        
        Args:
            peer_id: Peer node ID
        """
        self.protocol.peers.discard(peer_id)
        
    async def update_routing(
        self,
        routes: Dict[str, str]
    ) -> None:
        """
        Update routing table.
        
        Args:
            routes: Routing updates
        """
        self.protocol._routing_table.update(routes)
        
        # Notify peers of routing update
        await self.protocol.broadcast({
            "type": "route",
            "routes": routes
        })
        
    async def discover_services(self) -> List[Dict[str, Any]]:
        """Discover services in the A2A network."""
        # Query all peers for their services
        services = []
        
        for peer in self.protocol.peers:
            try:
                response = await self.protocol.send(
                    {"type": "discover_services"},
                    target=peer,
                    timeout=5.0
                )
                
                if response and "services" in response:
                    services.extend(response["services"])
                    
            except Exception as e:
                logger.warning(f"Failed to discover services from {peer}: {e}")
                
        return services
        
    def get_pattern_info(self) -> Dict[str, Any]:
        """
        Get information about the communication pattern.
        
        Returns:
            Pattern-specific information
        """
        pattern_impl = self.protocol._pattern_impl
        info = {
            "pattern": self.protocol.pattern
        }
        
        # Add pattern-specific info
        if hasattr(pattern_impl, 'get_status'):
            info["status"] = pattern_impl.get_status()
            
        if hasattr(pattern_impl, 'get_topology'):
            info["topology"] = pattern_impl.get_topology()
            
        return info
