"""
Protocol adapter implementations for the unified fabric.

This module contains adapters for all supported protocols.
"""
import asyncio
import json
import logging
import uuid
import aiohttp
from typing import Any, Dict, List, Optional

from agenticraft.core.exceptions import ToolError
from agenticraft.protocols.mcp import MCPClient, MCPServer, MCPTool
from agenticraft.protocols.a2a import ProtocolClient as A2AClient, ProtocolServer as A2AServer

from .protocol_types import (
    IProtocolAdapter,
    ProtocolType,
    ProtocolCapability,
    UnifiedTool
)

logger = logging.getLogger(__name__)


class MCPAdapter(IProtocolAdapter):
    """Adapter for MCP (Model Context Protocol)."""
    
    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.server: Optional[MCPServer] = None
        self._tools: Dict[str, UnifiedTool] = {}
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.MCP
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to MCP server."""
        url = config.get("url")
        if not url:
            raise ValueError("MCP adapter requires 'url' in config")
        
        self.client = MCPClient(url, **config.get("options", {}))
        await self.client.connect()
        
        # Discover and cache tools
        await self.discover_tools()
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.client:
            await self.client.disconnect()
            self.client = None
        self._tools.clear()
    
    async def discover_tools(self) -> List[UnifiedTool]:
        """Discover MCP tools."""
        if not self.client:
            return []
        
        tools = []
        mcp_tools = self.client.get_tools()
        
        for tool in mcp_tools:
            unified = UnifiedTool(
                name=tool.name,
                description=tool.description,
                protocol=ProtocolType.MCP,
                original_tool=tool,
                parameters=tool.get_definition().model_dump()
            )
            self._tools[tool.name] = unified
            tools.append(unified)
        
        return tools
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute MCP tool."""
        if not self.client:
            raise ToolError("MCP client not connected")
        
        return await self.client.call_tool(tool_name, kwargs)
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get MCP capabilities."""
        if not self.client or not self.client.server_info:
            return []
        
        capabilities = []
        
        # Tool execution capability
        capabilities.append(ProtocolCapability(
            name="tool_execution",
            description="Execute tools via MCP protocol",
            protocol=ProtocolType.MCP,
            metadata={
                "server_name": self.client.server_info.name,
                "server_version": self.client.server_info.version,
                "tool_count": len(self._tools)
            }
        ))
        
        # Resource access (if supported)
        if hasattr(self.client.server_info, 'capabilities'):
            caps = self.client.server_info.capabilities
            if caps.get('resources'):
                capabilities.append(ProtocolCapability(
                    name="resource_access",
                    description="Access resources via MCP",
                    protocol=ProtocolType.MCP
                ))
        
        return capabilities
    
    def supports_feature(self, feature: str) -> bool:
        """Check if adapter supports a specific feature."""
        # MCP supports tools and resources
        supported_features = ["tool_execution", "resource_access"]
        return feature in supported_features


class A2AAdapter(IProtocolAdapter):
    """Adapter for A2A (Agent-to-Agent) Protocol."""
    
    def __init__(self):
        self.client: Optional[A2AClient] = None
        self.server: Optional[A2AServer] = None
        self._agents: Dict[str, Any] = {}
        self._tools: Dict[str, UnifiedTool] = {}
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.A2A
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to A2A network."""
        # A2A can work with multiple connection methods
        connection_type = config.get("connection_type", "http")
        
        if connection_type == "http":
            url = config.get("url")
            if url:
                self.client = A2AClient(url, **config.get("options", {}))
                await self.client.connect()
        elif connection_type == "mesh":
            # Connect to A2A mesh network
            mesh_config = config.get("mesh_config", {})
            # Implementation depends on A2A mesh specifics
            pass
        
        # Discover agents and their capabilities
        await self._discover_agents()
    
    async def disconnect(self) -> None:
        """Disconnect from A2A network."""
        if self.client:
            await self.client.disconnect()
            self.client = None
        self._agents.clear()
        self._tools.clear()
    
    async def _discover_agents(self) -> None:
        """Discover agents in the A2A network."""
        if not self.client:
            return
        
        # Get agent cards from A2A network
        # This is based on A2A protocol specification
        try:
            agents = await self.client.discover_agents()
            for agent_card in agents:
                self._agents[agent_card.id] = agent_card
                
                # Convert agent skills to unified tools
                for skill in agent_card.skills:
                    tool = UnifiedTool(
                        name=f"{agent_card.id}.{skill.name}",
                        description=skill.description,
                        protocol=ProtocolType.A2A,
                        original_tool=skill,
                        parameters=skill.parameters
                    )
                    self._tools[tool.name] = tool
        except Exception as e:
            logger.error(f"Failed to discover A2A agents: {e}")
    
    async def discover_tools(self) -> List[UnifiedTool]:
        """Discover A2A tools (agent skills)."""
        return list(self._tools.values())
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute A2A tool (delegate to agent)."""
        if not self.client:
            raise ToolError("A2A client not connected")
        
        # Parse agent_id.skill_name format
        parts = tool_name.split(".", 1)
        if len(parts) != 2:
            raise ToolError(f"Invalid A2A tool name format: {tool_name}")
        
        agent_id, skill_name = parts
        
        # Send task to agent
        return await self.client.send_task(agent_id, skill_name, kwargs)
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get A2A capabilities."""
        capabilities = []
        
        # Agent collaboration
        capabilities.append(ProtocolCapability(
            name="agent_collaboration",
            description="Collaborate with other agents via A2A",
            protocol=ProtocolType.A2A,
            metadata={
                "agent_count": len(self._agents),
                "skill_count": len(self._tools)
            }
        ))
        
        # Bidirectional communication
        capabilities.append(ProtocolCapability(
            name="bidirectional_communication",
            description="Support for ongoing agent conversations",
            protocol=ProtocolType.A2A
        ))
        
        # Discovery
        capabilities.append(ProtocolCapability(
            name="agent_discovery",
            description="Discover agents and their capabilities",
            protocol=ProtocolType.A2A
        ))
        
        return capabilities


class ACPAdapter(IProtocolAdapter):
    """
    Adapter for IBM's Agent Communication Protocol (ACP).
    
    ACP is a REST-based protocol that supports:
    - MIME multipart messages
    - Session management
    - Asynchronous messaging
    - Standard HTTP methods
    """
    
    def __init__(self):
        self.base_url: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._agents: Dict[str, Any] = {}
        self._tools: Dict[str, UnifiedTool] = {}
        self._sessions: Dict[str, str] = {}  # agent_id -> session_id
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.ACP
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to ACP server."""
        self.base_url = config.get("url")
        if not self.base_url:
            raise ValueError("ACP adapter requires 'url' in config")
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Optional authentication
        auth = config.get("auth")
        if auth:
            self.session.headers.update({
                "Authorization": f"Bearer {auth.get('token')}"
            })
        
        # Discover available agents
        await self._discover_agents()
    
    async def disconnect(self) -> None:
        """Disconnect from ACP server."""
        # Close all active sessions
        for agent_id, session_id in self._sessions.items():
            try:
                await self._close_session(agent_id, session_id)
            except Exception as e:
                logger.error(f"Failed to close session {session_id}: {e}")
        
        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None
        
        self._agents.clear()
        self._tools.clear()
        self._sessions.clear()
    
    async def _discover_agents(self) -> None:
        """Discover agents via ACP registry."""
        if not self.session:
            return
        
        try:
            async with self.session.get(f"{self.base_url}/agents") as resp:
                if resp.status == 200:
                    agents = await resp.json()
                    for agent in agents:
                        self._agents[agent["id"]] = agent
                        
                        # Convert agent capabilities to tools
                        for capability in agent.get("capabilities", []):
                            tool = UnifiedTool(
                                name=f"{agent['id']}.{capability['name']}",
                                description=capability.get("description", ""),
                                protocol=ProtocolType.ACP,
                                original_tool=capability,
                                parameters=capability.get("parameters", {})
                            )
                            self._tools[tool.name] = tool
        except Exception as e:
            logger.error(f"Failed to discover ACP agents: {e}")
    
    async def discover_tools(self) -> List[UnifiedTool]:
        """Discover ACP tools."""
        return list(self._tools.values())
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute ACP tool via REST API."""
        if not self.session:
            raise ToolError("ACP session not connected")
        
        # Parse agent_id.capability_name format
        parts = tool_name.split(".", 1)
        if len(parts) != 2:
            raise ToolError(f"Invalid ACP tool name format: {tool_name}")
        
        agent_id, capability_name = parts
        
        # Get or create session
        session_id = await self._get_or_create_session(agent_id)
        
        # Build multipart message
        boundary = f"----AgentiCraft{uuid.uuid4().hex}"
        data = aiohttp.FormData()
        
        # Add capability request
        data.add_field(
            "request",
            json.dumps({
                "capability": capability_name,
                "parameters": kwargs,
                "session_id": session_id
            }),
            content_type="application/json"
        )
        
        # Execute capability
        try:
            async with self.session.post(
                f"{self.base_url}/agents/{agent_id}/execute",
                data=data,
                headers={"X-Session-ID": session_id}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error = await resp.text()
                    raise ToolError(f"ACP execution failed: {error}")
        except Exception as e:
            logger.error(f"Failed to execute ACP tool: {e}")
            raise
    
    async def _get_or_create_session(self, agent_id: str) -> str:
        """Get existing session or create new one."""
        if agent_id in self._sessions:
            return self._sessions[agent_id]
        
        # Create new session
        async with self.session.post(
            f"{self.base_url}/agents/{agent_id}/sessions"
        ) as resp:
            if resp.status == 201:
                result = await resp.json()
                session_id = result["session_id"]
                self._sessions[agent_id] = session_id
                return session_id
            else:
                raise ToolError(f"Failed to create ACP session: {resp.status}")
    
    async def _close_session(self, agent_id: str, session_id: str) -> None:
        """Close an ACP session."""
        async with self.session.delete(
            f"{self.base_url}/agents/{agent_id}/sessions/{session_id}"
        ) as resp:
            if resp.status != 204:
                logger.warning(f"Failed to close session {session_id}: {resp.status}")
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get ACP capabilities."""
        capabilities = []
        
        capabilities.append(ProtocolCapability(
            name="rest_communication",
            description="REST-based agent communication",
            protocol=ProtocolType.ACP,
            metadata={
                "agent_count": len(self._agents),
                "capability_count": len(self._tools)
            }
        ))
        
        capabilities.append(ProtocolCapability(
            name="session_management",
            description="Stateful session support",
            protocol=ProtocolType.ACP
        ))
        
        capabilities.append(ProtocolCapability(
            name="multipart_messages",
            description="MIME multipart message support",
            protocol=ProtocolType.ACP
        ))
        
        return capabilities


class ANPAdapter(IProtocolAdapter):
    """
    Adapter for Agent Network Protocol (ANP) - Decentralized Discovery.
    
    ANP enables:
    - DID-based agent identity
    - Decentralized discovery via IPFS/DHT
    - P2P agent communication
    - Trustless verification
    """
    
    def __init__(self):
        self.did_resolver: Optional[Any] = None
        self.ipfs_gateway: Optional[str] = None
        self._agents: Dict[str, Any] = {}
        self._tools: Dict[str, UnifiedTool] = {}
        self._local_did: Optional[str] = None
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.ANP
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to ANP network."""
        # IPFS gateway for decentralized storage
        self.ipfs_gateway = config.get("ipfs_gateway", "https://ipfs.io")
        
        # Initialize DID resolver
        did_method = config.get("did_method", "web")
        if did_method == "web":
            self.did_resolver = WebDIDResolver(config.get("resolver_url"))
        else:
            # Future: Support other DID methods (did:key, did:ion, etc.)
            raise ValueError(f"Unsupported DID method: {did_method}")
        
        # Create local agent DID if configured
        if config.get("create_did", False):
            self._local_did = await self._create_agent_did(config)
        
        # Discover agents from ANP network
        await self._discover_agents()
    
    async def disconnect(self) -> None:
        """Disconnect from ANP network."""
        self.did_resolver = None
        self._agents.clear()
        self._tools.clear()
        self._local_did = None
    
    async def _create_agent_did(self, config: Dict[str, Any]) -> str:
        """Create DID for local agent."""
        # Simplified DID creation
        agent_name = config.get("agent_name", f"agent-{uuid.uuid4().hex[:8]}")
        did = f"did:web:agenticraft.io:agents:{agent_name}"
        
        # Create DID document
        did_doc = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": did,
            "verificationMethod": [{
                "id": f"{did}#keys-1",
                "type": "Ed25519VerificationKey2020",
                "controller": did,
                "publicKeyMultibase": "placeholder"  # Would be actual key
            }],
            "service": [{
                "id": f"{did}#agent-service",
                "type": "AgentService",
                "serviceEndpoint": config.get("endpoint", "http://localhost:8000"),
                "description": "ANP Agent Service",
                "capabilities": config.get("capabilities", [])
            }]
        }
        
        # Store in IPFS (simulated)
        logger.info(f"Created ANP DID: {did}")
        return did
    
    async def _discover_agents(self) -> None:
        """Discover agents from ANP network."""
        # In a real implementation, this would:
        # 1. Query DHT for agent DIDs
        # 2. Resolve DIDs to get service endpoints
        # 3. Fetch agent capabilities
        
        # For now, simulate with known agents
        sample_agents = [
            {
                "did": "did:web:example.com:agents:researcher",
                "name": "researcher",
                "endpoint": "https://example.com/agents/researcher",
                "capabilities": [
                    {"name": "search", "description": "Search the web"},
                    {"name": "analyze", "description": "Analyze data"}
                ]
            }
        ]
        
        for agent in sample_agents:
            self._agents[agent["did"]] = agent
            
            # Convert capabilities to tools
            for cap in agent["capabilities"]:
                tool = UnifiedTool(
                    name=f"{agent['name']}.{cap['name']}",
                    description=cap["description"],
                    protocol=ProtocolType.ANP,
                    original_tool=cap,
                    parameters=cap.get("parameters", {})
                )
                self._tools[tool.name] = tool
    
    async def discover_tools(self) -> List[UnifiedTool]:
        """Discover ANP tools."""
        return list(self._tools.values())
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute ANP tool via DID service endpoint."""
        # Parse agent_name.capability format
        parts = tool_name.split(".", 1)
        if len(parts) != 2:
            raise ToolError(f"Invalid ANP tool name format: {tool_name}")
        
        agent_name, capability = parts
        
        # Find agent by name
        agent = None
        for did, agent_data in self._agents.items():
            if agent_data["name"] == agent_name:
                agent = agent_data
                break
        
        if not agent:
            raise ToolError(f"ANP agent not found: {agent_name}")
        
        # Execute via service endpoint
        # In real implementation, this would use the endpoint from DID doc
        logger.info(f"Executing ANP tool {capability} on agent {agent['did']}")
        
        # Simulated execution
        return {
            "status": "success",
            "agent": agent["did"],
            "capability": capability,
            "result": f"Executed {capability} with {kwargs}"
        }
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get ANP capabilities."""
        capabilities = []
        
        capabilities.append(ProtocolCapability(
            name="decentralized_discovery",
            description="Discover agents via decentralized network",
            protocol=ProtocolType.ANP,
            metadata={
                "did_method": "web",
                "agent_count": len(self._agents)
            }
        ))
        
        capabilities.append(ProtocolCapability(
            name="did_identity",
            description="W3C DID-based agent identity",
            protocol=ProtocolType.ANP
        ))
        
        capabilities.append(ProtocolCapability(
            name="trustless_verification",
            description="Cryptographic verification of agent identity",
            protocol=ProtocolType.ANP
        ))
        
        return capabilities


class WebDIDResolver:
    """Simple DID resolver for did:web method."""
    
    def __init__(self, resolver_url: Optional[str] = None):
        self.resolver_url = resolver_url or "https://dev.uniresolver.io"
    
    async def resolve(self, did: str) -> Dict[str, Any]:
        """Resolve DID to DID document."""
        # Simple mock resolution
        return {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": did,
            "verificationMethod": [],
            "service": []
        }
