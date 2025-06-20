"""
Unified Protocol Fabric for AgentiCraft.

This module provides a unified interface for integrating multiple agent protocols
including Google's A2A (Agent-to-Agent) and Anthropic's MCP (Model Context Protocol).
"""

import asyncio
import json
import logging
import uuid
import aiohttp
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set, Type, Union, Callable
from urllib.parse import urlparse

from agenticraft.core import Agent, BaseTool
from agenticraft.core.exceptions import AgentError, ToolError

# Import protocol components with fallbacks
try:
    from agenticraft.protocols.mcp import MCPClient, MCPServer, MCPTool
except ImportError:
    # Use stubs if actual implementations not available
    from .protocol_stubs import MCPClient, MCPServer
    MCPTool = None

try:
    from agenticraft.protocols.a2a import A2AClient, A2AServer
except ImportError:
    # Use stubs if actual implementations not available  
    from .protocol_stubs import A2AClient, A2AServer

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Supported protocol types."""
    A2A = "a2a"       # Google's Agent-to-Agent Protocol
    MCP = "mcp"       # Anthropic's Model Context Protocol
    ACP = "acp"       # IBM's Agent Communication Protocol
    ANP = "anp"       # Agent Network Protocol (Decentralized)
    NATIVE = "native" # AgentiCraft native


@dataclass
class ProtocolCapability:
    """Represents a capability exposed by a protocol."""
    name: str
    description: str
    protocol: ProtocolType
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedTool:
    """Unified tool representation across all protocols."""
    name: str
    description: str
    protocol: ProtocolType
    original_tool: Any  # Original protocol-specific tool
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool through its native protocol."""
        if hasattr(self.original_tool, 'arun'):
            return await self.original_tool.arun(**kwargs)
        elif hasattr(self.original_tool, 'execute'):
            return await self.original_tool.execute(**kwargs)
        else:
            raise ToolError(f"Tool {self.name} has no executable method")


class IProtocolAdapter(ABC):
    """Interface for protocol adapters."""
    
    @property
    @abstractmethod
    def protocol_type(self) -> ProtocolType:
        """Get the protocol type."""
        pass
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to the protocol server/service."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the protocol."""
        pass
    
    @abstractmethod
    async def discover_tools(self) -> List[UnifiedTool]:
        """Discover available tools from the protocol."""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool through the protocol."""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get protocol capabilities."""
        pass


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


class UnifiedProtocolFabric:
    """
    Unified Protocol Fabric for seamless integration of multiple agent protocols.
    
    This class provides a single interface for:
    - Connecting to multiple protocols simultaneously
    - Discovering tools across all protocols
    - Executing tools with automatic protocol routing
    - Managing protocol-specific configurations
    """
    
    def __init__(self):
        self.adapters: Dict[ProtocolType, IProtocolAdapter] = {}
        self.unified_tools: Dict[str, UnifiedTool] = {}
        self.capabilities: Dict[ProtocolType, List[ProtocolCapability]] = {}
        self._initialized = False
        
        # Register default adapters
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register default protocol adapters."""
        self.register_adapter(ProtocolType.MCP, MCPAdapter)
        self.register_adapter(ProtocolType.A2A, A2AAdapter)
    
    def register_adapter(self, protocol_type: ProtocolType, adapter_class: Type[IProtocolAdapter]):
        """Register a protocol adapter."""
        if protocol_type in self.adapters:
            logger.warning(f"Overriding existing adapter for {protocol_type}")
        
        adapter = adapter_class()
        self.adapters[protocol_type] = adapter
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the unified fabric with protocol configurations.
        
        Args:
            config: Protocol configurations in format:
                {
                    "mcp": {
                        "servers": [
                            {"url": "http://localhost:3000", "options": {...}}
                        ]
                    },
                    "a2a": {
                        "connection_type": "mesh",
                        "mesh_config": {...}
                    }
                }
        """
        if self._initialized:
            logger.warning("Fabric already initialized")
            return
        
        config = config or {}
        
        # Connect to each configured protocol
        tasks = []
        for protocol_type, adapter in self.adapters.items():
            protocol_config = config.get(protocol_type.value, {})
            if protocol_config:
                tasks.append(self._connect_protocol(protocol_type, protocol_config))
        
        # Connect all protocols in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Discover all tools
        await self._discover_all_tools()
        
        # Get all capabilities
        await self._discover_all_capabilities()
        
        self._initialized = True
        logger.info(f"Unified Protocol Fabric initialized with {len(self.unified_tools)} tools")
    
    async def _connect_protocol(self, protocol_type: ProtocolType, config: Dict[str, Any]):
        """Connect to a specific protocol."""
        adapter = self.adapters.get(protocol_type)
        if not adapter:
            return
        
        try:
            # Handle multiple servers for protocols like MCP
            if "servers" in config:
                for server_config in config["servers"]:
                    await adapter.connect(server_config)
            else:
                await adapter.connect(config)
            
            logger.info(f"Connected to {protocol_type.value} protocol")
        except Exception as e:
            logger.error(f"Failed to connect to {protocol_type.value}: {e}")
    
    async def _discover_all_tools(self):
        """Discover tools from all connected protocols."""
        self.unified_tools.clear()
        
        for protocol_type, adapter in self.adapters.items():
            try:
                tools = await adapter.discover_tools()
                for tool in tools:
                    # Add protocol prefix to avoid naming conflicts
                    prefixed_name = f"{protocol_type.value}:{tool.name}"
                    tool.name = prefixed_name
                    self.unified_tools[prefixed_name] = tool
                
                logger.info(f"Discovered {len(tools)} tools from {protocol_type.value}")
            except Exception as e:
                logger.error(f"Failed to discover tools from {protocol_type.value}: {e}")
    
    async def _discover_all_capabilities(self):
        """Discover capabilities from all protocols."""
        self.capabilities.clear()
        
        for protocol_type, adapter in self.adapters.items():
            try:
                caps = await adapter.get_capabilities()
                self.capabilities[protocol_type] = caps
            except Exception as e:
                logger.error(f"Failed to get capabilities from {protocol_type.value}: {e}")
    
    def get_available_protocols(self) -> List[ProtocolType]:
        """Get list of available protocols."""
        return list(self.adapters.keys())
    
    def get_tools(self, protocol: Optional[ProtocolType] = None) -> List[UnifiedTool]:
        """
        Get available tools, optionally filtered by protocol.
        
        Args:
            protocol: Optional protocol filter
            
        Returns:
            List of unified tools
        """
        if protocol:
            prefix = f"{protocol.value}:"
            return [
                tool for name, tool in self.unified_tools.items()
                if name.startswith(prefix)
            ]
        return list(self.unified_tools.values())
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Tool name (can be prefixed with protocol)
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        # Handle both prefixed and unprefixed names
        tool = self.unified_tools.get(tool_name)
        
        if not tool and ":" not in tool_name:
            # Try to find tool without prefix
            for name, t in self.unified_tools.items():
                if name.endswith(f":{tool_name}"):
                    tool = t
                    break
        
        if not tool:
            raise ToolError(f"Tool not found: {tool_name}")
        
        # Execute through the appropriate adapter
        adapter = self.adapters.get(tool.protocol)
        if not adapter:
            raise ToolError(f"Protocol adapter not found: {tool.protocol}")
        
        # Remove protocol prefix for actual execution
        actual_name = tool.name.split(":", 1)[1] if ":" in tool.name else tool.name
        return await adapter.execute_tool(actual_name, **kwargs)
    
    def get_capabilities(self, protocol: Optional[ProtocolType] = None) -> Dict[ProtocolType, List[ProtocolCapability]]:
        """Get capabilities by protocol."""
        if protocol:
            return {protocol: self.capabilities.get(protocol, [])}
        return self.capabilities
    
    async def create_unified_agent(self, name: str, **kwargs) -> Agent:
        """
        Create an agent with access to all unified tools.
        
        Args:
            name: Agent name
            **kwargs: Additional agent configuration
            
        Returns:
            Agent with unified tool access
        """
        # Get all tools as BaseTool instances
        tools = []
        for unified_tool in self.unified_tools.values():
            # Create tool wrapper
            tool_wrapper = UnifiedToolWrapper(unified_tool, self)
            tools.append(tool_wrapper)
        
        # Create agent with all tools
        agent = Agent(
            name=name,
            tools=tools,
            **kwargs
        )
        
        return agent
    
    async def shutdown(self):
        """Shutdown all protocol connections."""
        tasks = []
        for adapter in self.adapters.values():
            tasks.append(adapter.disconnect())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.unified_tools.clear()
        self.capabilities.clear()
        self._initialized = False
        
        logger.info("Unified Protocol Fabric shutdown complete")


class UnifiedToolWrapper(BaseTool):
    """Wrapper to use unified tools as AgentiCraft tools."""
    
    def __init__(self, unified_tool: UnifiedTool, fabric: UnifiedProtocolFabric):
        super().__init__(
            name=unified_tool.name,
            description=unified_tool.description
        )
        self.unified_tool = unified_tool
        self.fabric = fabric
    
    async def arun(self, **kwargs) -> Any:
        """Execute the unified tool."""
        return await self.fabric.execute_tool(self.unified_tool.name, **kwargs)


# Convenience functions
_global_fabric: Optional[UnifiedProtocolFabric] = None


def get_global_fabric() -> UnifiedProtocolFabric:
    """Get the global unified protocol fabric instance."""
    global _global_fabric
    if _global_fabric is None:
        _global_fabric = UnifiedProtocolFabric()
    return _global_fabric


async def initialize_fabric(config: Dict[str, Any]) -> UnifiedProtocolFabric:
    """Initialize the global fabric with configuration."""
    fabric = get_global_fabric()
    await fabric.initialize(config)
    return fabric
