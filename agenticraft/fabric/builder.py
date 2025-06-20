"""
Agent builder pattern for AgentiCraft.

This module provides a fluent builder interface for creating
agents with complex configurations.
"""
import logging
from typing import Optional, Dict, Any, List, Union

from .agent import UnifiedAgent
from ..core.transport import Transport, TransportConfig, HTTPTransport, WebSocketTransport
from ..core.auth import AuthConfig, AuthManager
from ..core.registry import ServiceRegistry, InMemoryRegistry
from ..protocols.base import Protocol

logger = logging.getLogger(__name__)


class AgentBuilder:
    """
    Fluent builder for creating agents.
    
    This builder provides a convenient way to create agents
    with complex configurations using method chaining.
    
    Example:
        agent = (AgentBuilder("my-agent")
            .with_mcp("http://localhost:8080")
            .with_a2a("mesh", ["peer1", "peer2"])
            .with_auth(AuthConfig.bearer("token"))
            .with_registry()
            .build())
    """
    
    def __init__(self, name: str):
        """
        Initialize agent builder.
        
        Args:
            name: Agent name
        """
        self.name = name
        self._protocols: List[Dict[str, Any]] = []
        self._registry: Optional[ServiceRegistry] = None
        self._config: Dict[str, Any] = {}
        self._primary_protocol: Optional[str] = None
        
    def with_mcp(
        self,
        url: str,
        auth: Optional[AuthConfig] = None,
        **kwargs
    ) -> "AgentBuilder":
        """
        Add MCP protocol support.
        
        Args:
            url: MCP server URL
            auth: Authentication configuration
            **kwargs: Additional MCP configuration
            
        Returns:
            Self for chaining
        """
        from ..protocols.mcp import MCPProtocol
        
        # Determine transport based on URL
        if url.startswith(("ws://", "wss://")):
            transport_class = WebSocketTransport
        else:
            transport_class = HTTPTransport
            
        self._protocols.append({
            "id": "mcp",
            "protocol_class": MCPProtocol,
            "transport_class": transport_class,
            "transport_config": TransportConfig(url=url, **kwargs),
            "auth_config": auth
        })
        
        if self._primary_protocol is None:
            self._primary_protocol = "mcp"
            
        return self
        
    def with_a2a(
        self,
        pattern: str = "mesh",
        peers: Optional[List[str]] = None,
        auth: Optional[AuthConfig] = None,
        **kwargs
    ) -> "AgentBuilder":
        """
        Add A2A protocol support.
        
        Args:
            pattern: A2A pattern (mesh, centralized, decentralized)
            peers: Initial peer addresses
            auth: Authentication configuration
            **kwargs: Additional A2A configuration
            
        Returns:
            Self for chaining
        """
        from ..protocols.a2a import A2AProtocol
        
        # A2A typically uses WebSocket
        url = kwargs.pop("url", f"ws://localhost:8000/{self.name}")
        
        self._protocols.append({
            "id": "a2a",
            "protocol_class": A2AProtocol,
            "protocol_kwargs": {
                "pattern": pattern,
                "peers": peers
            },
            "transport_class": WebSocketTransport,
            "transport_config": TransportConfig(
                url=url,
                extra={"auto_reconnect": True},
                **kwargs
            ),
            "auth_config": auth
        })
        
        if self._primary_protocol is None:
            self._primary_protocol = "a2a"
            
        return self
        
    def with_custom_protocol(
        self,
        protocol_id: str,
        protocol: Protocol,
        transport: Transport,
        auth: Optional[AuthConfig] = None
    ) -> "AgentBuilder":
        """
        Add custom protocol support.
        
        Args:
            protocol_id: Protocol identifier
            protocol: Protocol instance
            transport: Transport instance
            auth: Authentication configuration
            
        Returns:
            Self for chaining
        """
        self._protocols.append({
            "id": protocol_id,
            "protocol": protocol,
            "transport": transport,
            "auth_config": auth
        })
        
        if self._primary_protocol is None:
            self._primary_protocol = protocol_id
            
        return self
        
    def with_auth(
        self,
        auth_config: AuthConfig,
        protocol: Optional[str] = None
    ) -> "AgentBuilder":
        """
        Set authentication for protocols.
        
        Args:
            auth_config: Authentication configuration
            protocol: Specific protocol (None for all)
            
        Returns:
            Self for chaining
        """
        if protocol:
            # Set auth for specific protocol
            for proto in self._protocols:
                if proto["id"] == protocol:
                    proto["auth_config"] = auth_config
                    break
        else:
            # Set auth for all protocols
            for proto in self._protocols:
                proto["auth_config"] = auth_config
                
        return self
        
    def with_registry(
        self,
        registry: Optional[ServiceRegistry] = None
    ) -> "AgentBuilder":
        """
        Add service registry.
        
        Args:
            registry: Service registry (creates in-memory if None)
            
        Returns:
            Self for chaining
        """
        self._registry = registry or InMemoryRegistry()
        return self
        
    def with_config(self, **kwargs) -> "AgentBuilder":
        """
        Set additional configuration.
        
        Args:
            **kwargs: Configuration options
            
        Returns:
            Self for chaining
        """
        self._config.update(kwargs)
        return self
        
    def set_primary(self, protocol_id: str) -> "AgentBuilder":
        """
        Set primary protocol.
        
        Args:
            protocol_id: Protocol to set as primary
            
        Returns:
            Self for chaining
        """
        self._primary_protocol = protocol_id
        return self
        
    def build(self) -> UnifiedAgent:
        """
        Build the agent.
        
        Returns:
            Configured UnifiedAgent instance
        """
        # Create agent
        agent = UnifiedAgent(
            name=self.name,
            registry=self._registry,
            config=self._config
        )
        
        # Add protocols
        for proto_config in self._protocols:
            protocol_id = proto_config["id"]
            
            # Create protocol instance
            if "protocol" in proto_config:
                # Custom protocol provided
                protocol = proto_config["protocol"]
                transport = proto_config["transport"]
            else:
                # Create protocol and transport
                protocol_class = proto_config["protocol_class"]
                transport_class = proto_config["transport_class"]
                transport_config = proto_config["transport_config"]
                
                # Create transport
                transport = transport_class(transport_config)
                
                # Create protocol
                if "protocol_kwargs" in proto_config:
                    protocol = protocol_class(
                        transport=transport,
                        registry=self._registry,
                        **proto_config["protocol_kwargs"]
                    )
                else:
                    protocol = protocol_class(
                        transport=transport,
                        registry=self._registry
                    )
                    
            # Setup auth if configured
            auth = None
            if proto_config.get("auth_config"):
                auth = AuthManager()
                auth.set_auth(proto_config["auth_config"])
                
            # Add to agent
            agent.add_protocol(
                protocol_id,
                protocol,
                transport,
                auth,
                primary=(protocol_id == self._primary_protocol)
            )
            
        logger.info(f"Built agent '{self.name}' with {len(self._protocols)} protocols")
        
        return agent
        
    async def build_and_start(self) -> UnifiedAgent:
        """
        Build and start the agent.
        
        Returns:
            Started UnifiedAgent instance
        """
        agent = self.build()
        await agent.start()
        return agent


# Convenience functions for common configurations

def quick_mcp_agent(
    name: str,
    url: str,
    token: Optional[str] = None
) -> AgentBuilder:
    """
    Create a quick MCP agent builder.
    
    Args:
        name: Agent name
        url: MCP server URL
        token: Optional bearer token
        
    Returns:
        Configured builder
    """
    builder = AgentBuilder(name).with_mcp(url)
    
    if token:
        builder.with_auth(AuthConfig.bearer(token))
        
    return builder


def quick_a2a_agent(
    name: str,
    pattern: str = "mesh",
    peers: Optional[List[str]] = None
) -> AgentBuilder:
    """
    Create a quick A2A agent builder.
    
    Args:
        name: Agent name
        pattern: A2A pattern
        peers: Initial peers
        
    Returns:
        Configured builder
    """
    return AgentBuilder(name).with_a2a(pattern, peers)


def multi_protocol_agent(
    name: str,
    mcp_url: Optional[str] = None,
    a2a_pattern: Optional[str] = None
) -> AgentBuilder:
    """
    Create a multi-protocol agent builder.
    
    Args:
        name: Agent name
        mcp_url: MCP server URL
        a2a_pattern: A2A pattern
        
    Returns:
        Configured builder
    """
    builder = AgentBuilder(name).with_registry()
    
    if mcp_url:
        builder.with_mcp(mcp_url)
        
    if a2a_pattern:
        builder.with_a2a(a2a_pattern)
        
    return builder
