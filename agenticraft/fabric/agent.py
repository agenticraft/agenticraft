"""
Unified Agent Interface for AgentiCraft.

This module provides a single, clean agent interface that supports
multiple protocols through a unified abstraction layer.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, Type, List, Union, Set

from ..core.transport import Transport, TransportConfig
from ..core.auth import AuthManager, AuthConfig
from ..core.registry import ServiceRegistry, InMemoryRegistry
from ..protocols.base import Protocol

logger = logging.getLogger(__name__)


class UnifiedAgent:
    """
    Unified agent supporting multiple protocols.
    
    This class provides a single interface for creating agents that can
    communicate using different protocols (MCP, A2A, etc.) with automatic
    protocol selection and fallback capabilities.
    """
    
    def __init__(
        self,
        name: str,
        registry: Optional[ServiceRegistry] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize unified agent.
        
        Args:
            name: Agent name
            registry: Service registry (creates in-memory if None)
            config: Additional configuration
        """
        self.name = name
        self.registry = registry or InMemoryRegistry()
        self.config = config or {}
        
        # Protocol management
        self._protocols: Dict[str, Protocol] = {}
        self._transports: Dict[str, Transport] = {}
        self._auth_managers: Dict[str, AuthManager] = {}
        
        # Primary protocol for default operations
        self._primary_protocol: Optional[str] = None
        
        # Agent state
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        logger.info(f"Created unified agent: {name}")
        
    def add_protocol(
        self,
        protocol_id: str,
        protocol: Protocol,
        transport: Transport,
        auth: Optional[AuthManager] = None,
        primary: bool = False
    ) -> "UnifiedAgent":
        """
        Add a protocol to the agent.
        
        Args:
            protocol_id: Unique protocol identifier
            protocol: Protocol instance
            transport: Transport for the protocol
            auth: Optional auth manager
            primary: Set as primary protocol
            
        Returns:
            Self for chaining
        """
        if protocol_id in self._protocols:
            raise ValueError(f"Protocol {protocol_id} already registered")
            
        self._protocols[protocol_id] = protocol
        self._transports[protocol_id] = transport
        
        if auth:
            self._auth_managers[protocol_id] = auth
            
        if primary or self._primary_protocol is None:
            self._primary_protocol = protocol_id
            
        logger.info(f"Added protocol {protocol_id} to agent {self.name}")
        
        return self
        
    async def start(self, register: bool = True) -> None:
        """
        Start the agent and all protocols.
        
        Args:
            register: Whether to register in service registry
        """
        if self._running:
            logger.warning(f"Agent {self.name} already running")
            return
            
        logger.info(f"Starting agent {self.name}")
        
        # Start all transports
        for proto_id, transport in self._transports.items():
            try:
                await transport.connect()
                logger.info(f"Connected transport for protocol {proto_id}")
            except Exception as e:
                logger.error(f"Failed to connect transport for {proto_id}: {e}")
                raise
                
        # Start all protocols
        for proto_id, protocol in self._protocols.items():
            if hasattr(protocol, 'start'):
                try:
                    await protocol.start()
                    logger.info(f"Started protocol {proto_id}")
                except Exception as e:
                    logger.error(f"Failed to start protocol {proto_id}: {e}")
                    raise
                    
        # Register in service registry
        if register and self.registry:
            for proto_id in self._protocols:
                await self.registry.register(
                    name=f"{self.name}:{proto_id}",
                    service_type=proto_id,
                    endpoint=self._transports[proto_id].config.url,
                    metadata={
                        "agent": self.name,
                        "protocol": proto_id,
                        "primary": proto_id == self._primary_protocol
                    },
                    tags={self.name, proto_id}
                )
                
        self._running = True
        logger.info(f"Agent {self.name} started successfully")
        
    async def stop(self) -> None:
        """Stop the agent and all protocols."""
        if not self._running:
            return
            
        logger.info(f"Stopping agent {self.name}")
        
        # Cancel any running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
            
        # Unregister from service registry
        if self.registry:
            for proto_id in self._protocols:
                await self.registry.unregister(f"{self.name}:{proto_id}")
                
        # Stop all protocols
        for proto_id, protocol in self._protocols.items():
            if hasattr(protocol, 'stop'):
                try:
                    await protocol.stop()
                    logger.info(f"Stopped protocol {proto_id}")
                except Exception as e:
                    logger.error(f"Error stopping protocol {proto_id}: {e}")
                    
        # Disconnect all transports
        for proto_id, transport in self._transports.items():
            try:
                await transport.disconnect()
                logger.info(f"Disconnected transport for protocol {proto_id}")
            except Exception as e:
                logger.error(f"Error disconnecting transport for {proto_id}: {e}")
                
        self._running = False
        logger.info(f"Agent {self.name} stopped")
        
    async def send(
        self,
        message: Any,
        target: Optional[str] = None,
        protocol: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Send a message using specified or primary protocol.
        
        Args:
            message: Message to send
            target: Target agent/service
            protocol: Protocol to use (None for primary)
            timeout: Request timeout
            
        Returns:
            Response from target
        """
        proto_id = protocol or self._primary_protocol
        if not proto_id:
            raise ValueError("No protocol specified and no primary protocol set")
            
        if proto_id not in self._protocols:
            raise ValueError(f"Unknown protocol: {proto_id}")
            
        protocol_impl = self._protocols[proto_id]
        
        # Let protocol handle the message
        if hasattr(protocol_impl, 'send'):
            return await protocol_impl.send(message, target, timeout)
        else:
            raise NotImplementedError(
                f"Protocol {proto_id} does not support sending messages"
            )
            
    async def receive(
        self,
        protocol: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Receive a message from specified or primary protocol.
        
        Args:
            protocol: Protocol to receive from (None for primary)
            timeout: Receive timeout
            
        Returns:
            Received message
        """
        proto_id = protocol or self._primary_protocol
        if not proto_id:
            raise ValueError("No protocol specified and no primary protocol set")
            
        if proto_id not in self._protocols:
            raise ValueError(f"Unknown protocol: {proto_id}")
            
        protocol_impl = self._protocols[proto_id]
        
        # Let protocol handle receiving
        if hasattr(protocol_impl, 'receive'):
            if timeout:
                return await asyncio.wait_for(
                    protocol_impl.receive(),
                    timeout=timeout
                )
            else:
                return await protocol_impl.receive()
        else:
            raise NotImplementedError(
                f"Protocol {proto_id} does not support receiving messages"
            )
            
    async def call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
        protocol: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Make an RPC-style call.
        
        Args:
            method: Method name
            params: Method parameters
            target: Target service
            protocol: Protocol to use
            timeout: Call timeout
            
        Returns:
            Method result
        """
        message = {
            "method": method,
            "params": params or {}
        }
        
        return await self.send(message, target, protocol, timeout)
        
    async def discover_services(
        self,
        service_type: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available services.
        
        Args:
            service_type: Filter by service type
            tags: Filter by tags
            
        Returns:
            List of service information
        """
        if not self.registry:
            return []
            
        services = await self.registry.discover(
            service_type=service_type,
            tags=tags
        )
        
        return [service.to_dict() for service in services]
        
    def get_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Get protocol instance by ID."""
        return self._protocols.get(protocol_id)
        
    def get_transport(self, protocol_id: str) -> Optional[Transport]:
        """Get transport instance by protocol ID."""
        return self._transports.get(protocol_id)
        
    def list_protocols(self) -> List[str]:
        """List all registered protocol IDs."""
        return list(self._protocols.keys())
        
    def set_primary_protocol(self, protocol_id: str) -> None:
        """Set primary protocol for default operations."""
        if protocol_id not in self._protocols:
            raise ValueError(f"Unknown protocol: {protocol_id}")
            
        self._primary_protocol = protocol_id
        logger.info(f"Set primary protocol to {protocol_id}")
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all protocols and transports.
        
        Returns:
            Health status information
        """
        health = {
            "agent": self.name,
            "running": self._running,
            "protocols": {}
        }
        
        for proto_id in self._protocols:
            proto_health = {
                "connected": False,
                "error": None
            }
            
            # Check transport
            transport = self._transports.get(proto_id)
            if transport:
                proto_health["connected"] = transport.is_connected
                
            # Check protocol health if supported
            protocol = self._protocols.get(proto_id)
            if hasattr(protocol, 'health_check'):
                try:
                    proto_health["status"] = await protocol.health_check()
                except Exception as e:
                    proto_health["error"] = str(e)
                    
            health["protocols"][proto_id] = proto_health
            
        return health
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Factory functions for common agent configurations

def create_mcp_agent(
    name: str,
    url: str,
    auth_config: Optional[AuthConfig] = None,
    **kwargs
) -> UnifiedAgent:
    """
    Create an agent with MCP protocol.
    
    Args:
        name: Agent name
        url: MCP server URL
        auth_config: Authentication configuration
        **kwargs: Additional agent configuration
        
    Returns:
        Configured agent
    """
    from ..protocols.mcp import MCPProtocol
    from ..core.transport import HTTPTransport, WebSocketTransport
    
    agent = UnifiedAgent(name, **kwargs)
    
    # Determine transport based on URL
    if url.startswith(("ws://", "wss://")):
        transport = WebSocketTransport(TransportConfig(url=url))
    else:
        transport = HTTPTransport(TransportConfig(url=url))
        
    # Setup auth if provided
    auth = None
    if auth_config:
        from ..core.auth import get_auth_manager
        auth = get_auth_manager()
        auth.set_auth(auth_config)
        
    # Add MCP protocol
    protocol = MCPProtocol(transport=transport, auth=auth)
    agent.add_protocol(
        "mcp",
        protocol,
        transport,
        auth,
        primary=True
    )
    
    return agent


# Export main classes
__all__ = [
    "UnifiedAgent",
    "create_mcp_agent",
    "create_a2a_agent",
]


def create_a2a_agent(
    name: str,
    pattern: str = "mesh",
    peers: Optional[List[str]] = None,
    **kwargs
) -> UnifiedAgent:
    """
    Create an agent with A2A protocol.
    
    Args:
        name: Agent name
        pattern: A2A pattern (mesh, centralized, decentralized)
        peers: Initial peer addresses
        **kwargs: Additional agent configuration
        
    Returns:
        Configured agent
    """
    from ..protocols.a2a import A2AProtocol
    from ..core.transport import WebSocketTransport
    
    agent = UnifiedAgent(name, **kwargs)
    
    # A2A typically uses WebSocket
    transport = WebSocketTransport(
        TransportConfig(
            url=f"ws://localhost:8000/{name}",
            extra={"auto_reconnect": True}
        )
    )
    
    # Create A2A protocol with specified pattern
    protocol = A2AProtocol(pattern=pattern, peers=peers, transport=transport)
    
    # Add A2A protocol
    agent.add_protocol(
        "a2a",
        protocol,
        transport,
        primary=True
    )
    
    return agent
