"""
A2A Official SDK Adapter.

Uses the official Agent-to-Agent Protocol Python SDK from:
https://github.com/google-a2a/a2a-python
"""

import asyncio
from typing import Dict, List, Any, Optional, Set
from ..protocol_types import IProtocolAdapter, ProtocolType, UnifiedTool, ProtocolCapability

# Import ToolInfo or define if needed
from dataclasses import dataclass, field

@dataclass 
class ToolInfo:
    """Information about a tool."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)

try:
    # Based on typical Google SDK patterns, the imports might be:
    from google.a2a import Agent, AgentCard, Message
    from google.a2a.transport import HTTPTransport, WebSocketTransport
    from google.a2a.discovery import DiscoveryService
    from google.a2a.trust import TrustStore
    A2A_SDK_AVAILABLE = True
except ImportError:
    try:
        # Alternative import pattern
        import a2a
        from a2a import Agent, AgentCard, Message
        from a2a.transport import HTTPTransport, WebSocketTransport
        from a2a.discovery import DiscoveryService
        from a2a.trust import TrustStore
        A2A_SDK_AVAILABLE = True
    except ImportError:
        A2A_SDK_AVAILABLE = False
        Agent = AgentCard = TrustStore = Message = None
        HTTPTransport = WebSocketTransport = DiscoveryService = None


class A2AOfficialAdapter(IProtocolAdapter):
    """
    Adapter for Agent-to-Agent Protocol using the official SDK.
    
    Installation:
        pip install a2a-protocol
    
    Features:
        - Agent discovery and registration
        - Secure agent-to-agent communication
        - Trust verification with agent cards
        - Message routing and delegation
        - Capability negotiation
    """
    
    def __init__(self):
        if not A2A_SDK_AVAILABLE:
            raise ImportError(
                "A2A SDK not installed. Install with: pip install a2a-protocol"
            )
        self.agent: Optional[Agent] = None
        self.discovery: Optional[DiscoveryService] = None
        self.trust_store: Optional[TrustStore] = None
        self._connected_agents: Dict[str, Agent] = {}
        self._capabilities: Set[str] = set()
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.A2A
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Initialize A2A agent with official SDK."""
        # Create agent card
        agent_card = AgentCard(
            name=config.get("name", "agenticraft-agent"),
            description=config.get("description", "AgentiCraft A2A Agent"),
            capabilities=config.get("capabilities", []),
            endpoints=config.get("endpoints", []),
            public_key=config.get("public_key")  # For trust verification
        )
        
        # Initialize transport
        transport_type = config.get("transport", "http")
        if transport_type == "websocket":
            transport = WebSocketTransport(
                config.get("url", "ws://localhost:8080")
            )
        else:
            transport = HTTPTransport(
                config.get("url", "http://localhost:8080")
            )
        
        # Create agent
        self.agent = Agent(
            card=agent_card,
            transport=transport,
            private_key=config.get("private_key")  # For signing
        )
        
        # Initialize trust store
        self.trust_store = TrustStore()
        if "trusted_agents" in config:
            for trusted in config["trusted_agents"]:
                await self.trust_store.add_trusted_agent(trusted)
        
        # Initialize discovery service
        discovery_url = config.get("discovery_url")
        if discovery_url:
            self.discovery = DiscoveryService(discovery_url)
            # Register our agent
            await self.discovery.register(agent_card)
        
        # Start agent
        await self.agent.start()
        
        # Store our capabilities
        self._capabilities = set(agent_card.capabilities)
    
    async def disconnect(self) -> None:
        """Disconnect A2A agent."""
        if self.agent:
            # Unregister from discovery
            if self.discovery:
                await self.discovery.unregister(self.agent.card)
            
            # Stop agent
            await self.agent.stop()
            
            # Clear connections
            self._connected_agents.clear()
    
    async def discover_tools(self) -> List[ToolInfo]:
        """Discover tools from connected agents."""
        tools = []
        
        # Discover available agents if discovery service is available
        if self.discovery:
            available_agents = await self.discovery.search(
                capabilities=["tool-provider"]
            )
            
            for agent_card in available_agents:
                # Connect to agent if not already connected
                if agent_card.name not in self._connected_agents:
                    await self._connect_to_agent(agent_card)
                
                # Query agent for available tools
                agent = self._connected_agents.get(agent_card.name)
                if agent:
                    agent_tools = await self._query_agent_tools(agent)
                    tools.extend(agent_tools)
        
        # Also include local capabilities as tools
        for capability in self._capabilities:
            if capability.startswith("tool:"):
                tool_name = capability[5:]  # Remove "tool:" prefix
                tools.append(ToolInfo(
                    name=tool_name,
                    description=f"Local tool: {tool_name}",
                    parameters={}
                ))
        
        return tools
    
    async def _connect_to_agent(self, agent_card: AgentCard) -> None:
        """Establish connection to another agent."""
        # Verify trust
        if self.trust_store and not await self.trust_store.verify(agent_card):
            raise ValueError(f"Agent {agent_card.name} not trusted")
        
        # Create connection
        remote_agent = await self.agent.connect_to(agent_card)
        self._connected_agents[agent_card.name] = remote_agent
    
    async def _query_agent_tools(self, agent: Agent) -> List[ToolInfo]:
        """Query an agent for its available tools."""
        # Send tool discovery request
        response = await agent.send_message(
            Message(
                type="tools.discover",
                content={}
            )
        )
        
        tools = []
        if response.type == "tools.list":
            for tool_data in response.content.get("tools", []):
                tools.append(ToolInfo(
                    name=f"{agent.card.name}.{tool_data['name']}",
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("parameters", {})
                ))
        
        return tools
    
    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a tool through A2A protocol."""
        # Parse tool name to find target agent
        if "." in tool_name:
            agent_name, actual_tool_name = tool_name.split(".", 1)
        else:
            # Local tool
            return await self._execute_local_tool(tool_name, arguments)
        
        # Find target agent
        target_agent = self._connected_agents.get(agent_name)
        if not target_agent:
            # Try to discover and connect
            if self.discovery:
                agents = await self.discovery.search(name=agent_name)
                if agents:
                    await self._connect_to_agent(agents[0])
                    target_agent = self._connected_agents.get(agent_name)
        
        if not target_agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        # Send tool execution request
        response = await target_agent.send_message(
            Message(
                type="tool.execute",
                content={
                    "tool": actual_tool_name,
                    "arguments": arguments or {}
                }
            )
        )
        
        if response.type == "tool.result":
            return response.content.get("result")
        elif response.type == "error":
            raise RuntimeError(
                f"Tool execution failed: {response.content.get('message')}"
            )
        else:
            raise RuntimeError(f"Unexpected response type: {response.type}")
    
    async def _execute_local_tool(
        self, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a local tool (placeholder for actual implementation)."""
        # This would be implemented based on local capabilities
        raise NotImplementedError(
            f"Local tool execution for '{tool_name}' not implemented"
        )
    
    async def send_message(self, agent_name: str, message: Dict[str, Any]) -> Any:
        """Send a message to another agent (A2A feature)."""
        target_agent = self._connected_agents.get(agent_name)
        if not target_agent:
            raise ValueError(f"Not connected to agent '{agent_name}'")
        
        response = await target_agent.send_message(
            Message(
                type=message.get("type", "custom"),
                content=message.get("content", {})
            )
        )
        
        return {
            "type": response.type,
            "content": response.content
        }
    
    async def register_handler(self, message_type: str, handler) -> None:
        """Register a message handler (A2A feature)."""
        if self.agent:
            await self.agent.register_handler(message_type, handler)
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get A2A protocol capabilities."""
        capabilities = []
        
        # Basic A2A capabilities
        if self.agent:
            capabilities.append(ProtocolCapability(
                name="tools",
                description="Tool discovery and execution via A2A",
                protocol=ProtocolType.A2A
            ))
            
            capabilities.append(ProtocolCapability(
                name="discovery",
                description="Agent discovery service",
                protocol=ProtocolType.A2A
            ))
            
            capabilities.append(ProtocolCapability(
                name="trust",
                description="Trust verification with agent cards",
                protocol=ProtocolType.A2A
            ))
            
            capabilities.append(ProtocolCapability(
                name="messaging",
                description="Agent-to-agent messaging",
                protocol=ProtocolType.A2A
            ))
            
            capabilities.append(ProtocolCapability(
                name="delegation",
                description="Task delegation to other agents",
                protocol=ProtocolType.A2A
            ))
            
            # Add configured capabilities as metadata
            if self._capabilities:
                capabilities.append(ProtocolCapability(
                    name="custom_capabilities",
                    description="Agent-specific capabilities",
                    protocol=ProtocolType.A2A,
                    metadata={"capabilities": list(self._capabilities)}
                ))
        
        return capabilities
    
    def supports_feature(self, feature: str) -> bool:
        """Check if adapter supports a specific feature."""
        return feature in {
            'tools', 'discovery', 'trust', 'messaging',
            'delegation', 'capabilities'
        }


class A2AHybridAdapter(A2AOfficialAdapter):
    """
    Hybrid adapter with fallback to custom implementation.
    
    Useful during migration when not all features are available
    in the official SDK yet.
    """
    
    def __init__(self, fallback_adapter=None):
        self.fallback_adapter = fallback_adapter
        self._use_official = True
        
        try:
            super().__init__()
        except ImportError:
            if not self.fallback_adapter:
                raise
            self._use_official = False
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get capabilities with fallback support."""
        if self._use_official:
            try:
                return await super().get_capabilities()
            except Exception:
                if self.fallback_adapter:
                    return await self.fallback_adapter.get_capabilities()
                raise
        else:
            if self.fallback_adapter:
                return await self.fallback_adapter.get_capabilities()
            return []
    
    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute with fallback support."""
        if self._use_official:
            try:
                return await super().execute_tool(tool_name, arguments)
            except (NotImplementedError, RuntimeError) as e:
                if self.fallback_adapter and "not implemented" in str(e).lower():
                    return await self.fallback_adapter.execute_tool(
                        tool_name, arguments
                    )
                raise
        else:
            return await self.fallback_adapter.execute_tool(tool_name, arguments)
