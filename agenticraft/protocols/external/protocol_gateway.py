"""
Protocol Gateway - Unified management of A2A and MCP protocols.

This module provides a single entry point for:
1. Managing multiple protocol connections
2. Routing between internal and external agents
3. Protocol translation and adaptation
4. Service discovery and registration
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union
from enum import Enum

from agenticraft.protocols.a2a.base import Protocol
from agenticraft.protocols.a2a import MeshNetwork
from agenticraft.fabric.adapters.adapter_factory import AdapterFactory, SDKPreference
from agenticraft.fabric.protocol_types import ProtocolType
from agenticraft.core.agent import Agent

from .a2a_bridge import A2ABridge, A2AServer
from .mcp_server_builder import MCPServerBuilder, create_agent_mcp_server

logger = logging.getLogger(__name__)


class ExternalProtocol(Enum):
    """External protocol types."""
    GOOGLE_A2A = "google_a2a"
    MCP = "mcp"
    CUSTOM = "custom"


@dataclass
class ServiceRegistration:
    """Registration info for an exposed service."""
    agent_name: str
    protocol: ExternalProtocol
    endpoint: str
    port: int
    capabilities: List[str]
    metadata: Dict[str, Any]


class ProtocolGateway:
    """
    Unified gateway for managing all protocol connections.
    
    Features:
    - Single point of management for all protocols
    - Automatic service discovery
    - Protocol translation
    - Load balancing and failover
    - Monitoring and metrics
    """
    
    def __init__(self, internal_mesh: Optional[MeshNetwork] = None):
        # Internal coordination
        self.internal_mesh = internal_mesh or MeshNetwork("gateway")
        
        # External protocol bridges
        self.a2a_bridge = A2ABridge(self.internal_mesh)
        
        # MCP connections
        self.mcp_clients: Dict[str, Any] = {}
        self.mcp_servers: Dict[str, MCPServerBuilder] = {}
        
        # Service registry
        self.services: Dict[str, ServiceRegistration] = {}
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "active_connections": 0
        }
    
    async def start(self):
        """Start the gateway."""
        # Start internal mesh if not running
        if not self.internal_mesh._running:
            await self.internal_mesh.start()
        
        logger.info("Protocol Gateway started")
    
    async def stop(self):
        """Stop the gateway."""
        # Stop all MCP servers
        # Note: In production, you'd properly shutdown servers
        
        # Disconnect external clients
        for client in self.mcp_clients.values():
            if hasattr(client, 'disconnect'):
                await client.disconnect()
        
        # Stop internal mesh
        await self.internal_mesh.stop()
        
        logger.info("Protocol Gateway stopped")
    
    # ===== Agent Exposure =====
    
    async def expose_agent(
        self,
        agent: Agent,
        protocols: List[ExternalProtocol],
        base_port: int = 8080
    ) -> Dict[ExternalProtocol, ServiceRegistration]:
        """
        Expose an agent through multiple protocols.
        
        Args:
            agent: AgentiCraft agent to expose
            protocols: List of protocols to expose through
            base_port: Starting port number
            
        Returns:
            Dictionary of protocol -> service registration
        """
        registrations = {}
        
        for i, protocol in enumerate(protocols):
            port = base_port + i
            
            if protocol == ExternalProtocol.GOOGLE_A2A:
                # Create A2A server
                server = await self.a2a_bridge.expose_agent(agent, port)
                
                # Create registration
                registration = ServiceRegistration(
                    agent_name=agent.name,
                    protocol=protocol,
                    endpoint=f"http://localhost:{port}",
                    port=port,
                    capabilities=server.agent_card.capabilities,
                    metadata={"agent_card": server.agent_card.to_dict()}
                )
                
                # Start server in background
                asyncio.create_task(self._run_a2a_server(server))
                
            elif protocol == ExternalProtocol.MCP:
                # Create MCP server
                builder = create_agent_mcp_server(agent, port)
                self.mcp_servers[agent.name] = builder
                
                # Create registration
                registration = ServiceRegistration(
                    agent_name=agent.name,
                    protocol=protocol,
                    endpoint=f"http://localhost:{port}",
                    port=port,
                    capabilities=[f"tool:{t}" for t in builder._tools],
                    metadata={
                        "resources": builder._resources,
                        "prompts": builder._prompts
                    }
                )
                
                # Start server in background
                asyncio.create_task(self._run_mcp_server(builder, port))
            
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")
            
            registrations[protocol] = registration
            self.services[f"{agent.name}:{protocol.value}"] = registration
        
        # Register capabilities in internal mesh
        for reg in registrations.values():
            for cap in reg.capabilities:
                self.internal_mesh.register_capability(
                    f"gateway:{reg.protocol.value}:{cap}"
                )
        
        return registrations
    
    async def _run_a2a_server(self, server: A2AServer):
        """Run A2A server in background."""
        try:
            server.run()
        except Exception as e:
            logger.error(f"A2A server error: {e}")
    
    async def _run_mcp_server(self, builder: MCPServerBuilder, port: int):
        """Run MCP server in background."""
        try:
            builder.run_sse(port=port)
        except Exception as e:
            logger.error(f"MCP server error: {e}")
    
    # ===== External Connections =====
    
    async def connect_external_a2a(self, agent_url: str) -> Dict[str, Any]:
        """Connect to an external A2A agent."""
        agent_card = await self.a2a_bridge.connect_external_agent(agent_url)
        
        # Register in services
        registration = ServiceRegistration(
            agent_name=agent_card["name"],
            protocol=ExternalProtocol.GOOGLE_A2A,
            endpoint=agent_url,
            port=0,  # External, no local port
            capabilities=agent_card["capabilities"],
            metadata={"agent_card": agent_card}
        )
        
        self.services[f"{agent_card['name']}:external_a2a"] = registration
        self.metrics["active_connections"] += 1
        
        return agent_card
    
    async def connect_mcp_server(
        self,
        name: str,
        config: Dict[str, Any],
        preference: SDKPreference = SDKPreference.AUTO
    ) -> List[Dict[str, Any]]:
        """Connect to an MCP server."""
        # Create MCP client adapter
        adapter = AdapterFactory.create_adapter(
            ProtocolType.MCP,
            preference=preference
        )
        
        await adapter.connect(config)
        self.mcp_clients[name] = adapter
        
        # Discover tools
        tools = await adapter.discover_tools()
        
        # Register in services
        registration = ServiceRegistration(
            agent_name=name,
            protocol=ExternalProtocol.MCP,
            endpoint=config.get("url", config.get("command", "stdio")),
            port=0,  # External
            capabilities=[f"tool:{t.name}" for t in tools],
            metadata={"transport": config.get("transport", "stdio")}
        )
        
        self.services[f"{name}:external_mcp"] = registration
        self.metrics["active_connections"] += 1
        
        return [{"name": t.name, "description": t.description} for t in tools]
    
    # ===== Unified Execution =====
    
    async def execute(
        self,
        task: str,
        capability: Optional[str] = None,
        prefer_external: bool = False
    ) -> Any:
        """
        Execute a task using the best available agent/tool.
        
        Args:
            task: Task description
            capability: Required capability (optional)
            prefer_external: Prefer external services
            
        Returns:
            Task result
        """
        self.metrics["total_requests"] += 1
        
        try:
            # Find capable services
            capable_services = self._find_capable_services(capability)
            
            if not capable_services:
                raise RuntimeError(f"No service found with capability: {capability}")
            
            # Select service based on preference
            service = self._select_service(capable_services, prefer_external)
            
            # Route to appropriate handler
            if service.protocol == ExternalProtocol.GOOGLE_A2A:
                result = await self.a2a_bridge.route_task(task, capability or "any")
            
            elif service.protocol == ExternalProtocol.MCP:
                # Extract tool name from capability
                tool_name = capability.split(":", 1)[1] if ":" in capability else capability
                adapter = self.mcp_clients.get(service.agent_name)
                
                if adapter:
                    result = await adapter.execute_tool(tool_name, {"task": task})
                else:
                    raise RuntimeError(f"MCP client not found: {service.agent_name}")
            
            else:
                # Internal routing
                result = await self.internal_mesh.execute_distributed(
                    task=task,
                    capability_required=capability or "any",
                    strategy="auto"
                )
            
            self.metrics["successful_requests"] += 1
            return result
            
        except Exception as e:
            self.metrics["failed_requests"] += 1
            logger.error(f"Execution failed: {e}")
            raise
    
    def _find_capable_services(
        self,
        capability: Optional[str]
    ) -> List[ServiceRegistration]:
        """Find services with the required capability."""
        if not capability:
            return list(self.services.values())
        
        capable = []
        for service in self.services.values():
            if capability in service.capabilities:
                capable.append(service)
            # Check partial match
            elif any(cap.endswith(capability) for cap in service.capabilities):
                capable.append(service)
        
        return capable
    
    def _select_service(
        self,
        services: List[ServiceRegistration],
        prefer_external: bool
    ) -> ServiceRegistration:
        """Select best service based on preferences."""
        if prefer_external:
            # Prefer external services
            external = [s for s in services if s.port == 0]
            if external:
                return external[0]
        
        # Default: prefer internal
        internal = [s for s in services if s.port != 0]
        if internal:
            return internal[0]
        
        # Fallback to any available
        return services[0]
    
    # ===== Discovery and Management =====
    
    def list_services(self) -> List[Dict[str, Any]]:
        """List all registered services."""
        return [
            {
                "name": service.agent_name,
                "protocol": service.protocol.value,
                "endpoint": service.endpoint,
                "capabilities": service.capabilities,
                "type": "internal" if service.port > 0 else "external"
            }
            for service in self.services.values()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics."""
        return {
            **self.metrics,
            "total_services": len(self.services),
            "internal_services": len([s for s in self.services.values() if s.port > 0]),
            "external_services": len([s for s in self.services.values() if s.port == 0]),
            "protocols": {
                "a2a": len([s for s in self.services.values() if s.protocol == ExternalProtocol.GOOGLE_A2A]),
                "mcp": len([s for s in self.services.values() if s.protocol == ExternalProtocol.MCP])
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all connections."""
        health = {
            "status": "healthy",
            "services": {},
            "issues": []
        }
        
        for name, service in self.services.items():
            try:
                if service.protocol == ExternalProtocol.MCP and service.port == 0:
                    # Check MCP client
                    adapter = self.mcp_clients.get(service.agent_name)
                    if adapter and hasattr(adapter, 'discover_tools'):
                        await adapter.discover_tools()
                        health["services"][name] = "healthy"
                    else:
                        health["services"][name] = "disconnected"
                        health["issues"].append(f"{name}: MCP client disconnected")
                else:
                    # Assume internal services are healthy if registered
                    health["services"][name] = "healthy"
                    
            except Exception as e:
                health["services"][name] = "error"
                health["issues"].append(f"{name}: {str(e)}")
                health["status"] = "degraded"
        
        return health


# Convenience functions

async def create_unified_gateway(
    agents: List[Agent],
    expose_protocols: List[ExternalProtocol] = [ExternalProtocol.GOOGLE_A2A, ExternalProtocol.MCP],
    base_port: int = 8080
) -> ProtocolGateway:
    """Create a gateway with multiple agents exposed through various protocols."""
    gateway = ProtocolGateway()
    await gateway.start()
    
    # Expose all agents
    port = base_port
    for agent in agents:
        await gateway.expose_agent(agent, expose_protocols, port)
        port += len(expose_protocols)
    
    return gateway
