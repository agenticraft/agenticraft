"""
Protocol gateway for external integrations.

This module provides a gateway that allows external systems
to interact with AgentiCraft protocols through a unified interface.
"""
import asyncio
import logging
from typing import Any, Dict, Optional, List, Set
from uuid import uuid4

from ..base import Protocol
from .base import ProtocolBridge
from ...core.registry import ServiceRegistry

logger = logging.getLogger(__name__)


class ProtocolGateway:
    """
    Gateway for protocol interactions.
    
    This gateway provides a unified interface for external systems
    to interact with multiple protocols and bridges.
    """
    
    def __init__(
        self,
        gateway_id: Optional[str] = None,
        registry: Optional[ServiceRegistry] = None
    ):
        """
        Initialize protocol gateway.
        
        Args:
            gateway_id: Gateway identifier
            registry: Service registry
        """
        self.gateway_id = gateway_id or str(uuid4())
        self.registry = registry
        
        # Protocol management
        self._protocols: Dict[str, Protocol] = {}
        self._bridges: List[ProtocolBridge] = []
        self._routes: Dict[str, str] = {}  # Protocol routing
        
        # Gateway state
        self._running = False
        
        logger.info(f"Created protocol gateway: {self.gateway_id}")
        
    def register_protocol(
        self,
        protocol_id: str,
        protocol: Protocol
    ) -> None:
        """
        Register a protocol with the gateway.
        
        Args:
            protocol_id: Protocol identifier
            protocol: Protocol instance
        """
        if protocol_id in self._protocols:
            raise ValueError(f"Protocol {protocol_id} already registered")
            
        self._protocols[protocol_id] = protocol
        logger.info(f"Registered protocol {protocol_id} with gateway")
        
    def register_bridge(self, bridge: ProtocolBridge) -> None:
        """
        Register a protocol bridge.
        
        Args:
            bridge: Protocol bridge
        """
        self._bridges.append(bridge)
        
        # Update routing table
        proto_a, proto_b = bridge.get_supported_protocols()
        self._routes[f"{proto_a}->{proto_b}"] = "bridge"
        self._routes[f"{proto_b}->{proto_a}"] = "bridge"
        
        logger.info(f"Registered bridge between {proto_a} and {proto_b}")
        
    async def start(self) -> None:
        """Start the gateway."""
        if self._running:
            return
            
        logger.info(f"Starting protocol gateway {self.gateway_id}")
        
        # Start all protocols
        for proto_id, protocol in self._protocols.items():
            if hasattr(protocol, 'start'):
                await protocol.start()
                logger.info(f"Started protocol {proto_id}")
                
        # Start all bridges
        for bridge in self._bridges:
            await bridge.start()
            
        # Register in service registry
        if self.registry:
            await self.registry.register(
                name=f"gateway:{self.gateway_id}",
                service_type="gateway",
                metadata={
                    "protocols": list(self._protocols.keys()),
                    "bridges": len(self._bridges)
                },
                tags={"gateway", "protocol-gateway"}
            )
            
        self._running = True
        logger.info(f"Protocol gateway {self.gateway_id} started")
        
    async def stop(self) -> None:
        """Stop the gateway."""
        if not self._running:
            return
            
        logger.info(f"Stopping protocol gateway {self.gateway_id}")
        
        # Unregister from service registry
        if self.registry:
            await self.registry.unregister(f"gateway:{self.gateway_id}")
            
        # Stop all bridges
        for bridge in self._bridges:
            await bridge.stop()
            
        # Stop all protocols
        for protocol in self._protocols.values():
            if hasattr(protocol, 'stop'):
                await protocol.stop()
                
        self._running = False
        logger.info(f"Protocol gateway {self.gateway_id} stopped")
        
    async def send(
        self,
        message: Any,
        source_protocol: str,
        target_protocol: str,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Send message between protocols.
        
        Args:
            message: Message to send
            source_protocol: Source protocol ID
            target_protocol: Target protocol ID
            target: Target identifier
            timeout: Operation timeout
            
        Returns:
            Response from target
        """
        # Direct send if same protocol
        if source_protocol == target_protocol:
            protocol = self._protocols.get(source_protocol)
            if not protocol:
                raise ValueError(f"Unknown protocol: {source_protocol}")
                
            return await protocol.send(message, target, timeout)
            
        # Check for bridge
        route_key = f"{source_protocol}->{target_protocol}"
        if route_key in self._routes:
            # Find appropriate bridge
            for bridge in self._bridges:
                proto_a, proto_b = bridge.get_supported_protocols()
                if (proto_a == source_protocol and proto_b == target_protocol) or \
                   (proto_a == target_protocol and proto_b == source_protocol):
                    return await bridge.bridge_message(
                        message,
                        source_protocol,
                        target
                    )
                    
        raise ValueError(
            f"No route from {source_protocol} to {target_protocol}"
        )
        
    async def broadcast(
        self,
        message: Any,
        source_protocol: str,
        exclude_protocols: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Broadcast message to all protocols.
        
        Args:
            message: Message to broadcast
            source_protocol: Source protocol ID
            exclude_protocols: Protocols to exclude
            
        Returns:
            Responses from all protocols
        """
        exclude = exclude_protocols or set()
        exclude.add(source_protocol)
        
        responses = {}
        tasks = []
        
        for proto_id in self._protocols:
            if proto_id not in exclude:
                task = asyncio.create_task(
                    self.send(
                        message,
                        source_protocol,
                        proto_id
                    )
                )
                tasks.append((proto_id, task))
                
        # Gather responses
        for proto_id, task in tasks:
            try:
                responses[proto_id] = await task
            except Exception as e:
                logger.error(f"Broadcast to {proto_id} failed: {e}")
                responses[proto_id] = {"error": str(e)}
                
        return responses
        
    def get_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Get protocol by ID."""
        return self._protocols.get(protocol_id)
        
    def list_protocols(self) -> List[str]:
        """List registered protocol IDs."""
        return list(self._protocols.keys())
        
    def list_bridges(self) -> List[Tuple[str, str]]:
        """List registered bridges."""
        bridges = []
        for bridge in self._bridges:
            bridges.append(bridge.get_supported_protocols())
        return bridges
        
    def get_routes(self) -> Dict[str, str]:
        """Get routing table."""
        return self._routes.copy()
        
    async def discover_services(
        self,
        service_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available services across all protocols.
        
        Args:
            service_type: Filter by service type
            
        Returns:
            List of discovered services
        """
        if not self.registry:
            return []
            
        services = await self.registry.discover(service_type=service_type)
        return [service.to_dict() for service in services]
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of gateway and all protocols.
        
        Returns:
            Health status information
        """
        health = {
            "gateway_id": self.gateway_id,
            "running": self._running,
            "protocols": {},
            "bridges": []
        }
        
        # Check protocol health
        for proto_id, protocol in self._protocols.items():
            if hasattr(protocol, 'health_check'):
                try:
                    health["protocols"][proto_id] = await protocol.health_check()
                except Exception as e:
                    health["protocols"][proto_id] = {
                        "error": str(e),
                        "status": "error"
                    }
                    
        # Check bridge health
        for bridge in self._bridges:
            proto_a, proto_b = bridge.get_supported_protocols()
            health["bridges"].append({
                "protocols": [proto_a, proto_b],
                "running": bridge.is_running
            })
            
        return health
