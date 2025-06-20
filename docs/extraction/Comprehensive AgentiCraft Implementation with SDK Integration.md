# Comprehensive AgentiCraft Implementation with SDK Integration

## Project Structure

```
/agenticraft/
├── fabric/                    # Protocol SDK integration
│   ├── __init__.py
│   ├── unified.py            # Unified protocol fabric
│   ├── adapters/             # SDK adapters
│   │   ├── __init__.py
│   │   ├── a2a.py
│   │   ├── mcp.py
│   │   └── anp.py
│   └── decorators.py         # Fast-agent inspired decorators
├── orchestration/            # LangGraph-inspired patterns
│   ├── __init__.py
│   ├── state.py              # State management
│   ├── graph.py              # Graph-based orchestration
│   ├── workflow.py           # Stateful workflows
│   └── checkpoint.py         # Checkpointing system
├── tools/                    # Minimal tool layer
│   ├── __init__.py
│   ├── base.py               # Simplified tool interface
│   ├── registry.py           # Unified tool registry
│   └── adapters.py           # SDK tool adapters
└── config/                   # Configuration
    ├── __init__.py
    └── agenticraft.yaml      # Unified configuration
```

## 1. Unified Protocol Fabric with SDK Integration

### `/agenticraft/fabric/unified.py`

```python
"""Unified Protocol Fabric using official SDKs with AgentiCraft enhancements."""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

# Official SDKs (installed separately)
try:
    from a2a import Agent as A2AAgent, AgentCard, Client as A2AClient
    HAS_A2A = True
except ImportError:
    HAS_A2A = False
    A2AAgent = None

try:
    from mcp import Server as MCPServer, Client as MCPClient, Tool
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    MCPServer = None

try:
    from agentconnect import AgentConnect, DIDAgent
    HAS_ANP = True
except ImportError:
    HAS_ANP = False
    AgentConnect = None

# AgentiCraft imports
from ..core.agent import Agent as AgentiCraftAgent
from ..protocols.a2a.hybrid.mesh_network import MeshNetwork
from .adapters import A2AAdapter, MCPAdapter, ANPAdapter

logger = logging.getLogger(__name__)


@dataclass
class ProtocolCapabilities:
    """Capabilities provided by each protocol."""
    tools: bool = False
    resources: bool = False
    prompts: bool = False
    discovery: bool = False
    consensus: bool = False
    mesh_networking: bool = False


@dataclass
class UnifiedAgentRegistration:
    """Unified registration across all protocols."""
    agent_id: str
    agent: AgentiCraftAgent
    a2a_endpoint: Optional[str] = None
    mcp_endpoint: Optional[str] = None
    anp_did: Optional[str] = None
    mesh_node_id: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedProtocolFabric:
    """
    Unified fabric that combines official SDKs with AgentiCraft's unique features.
    
    This is the main integration point that:
    - Uses official SDKs for protocol compliance
    - Preserves AgentiCraft's mesh networking and consensus
    - Provides a unified interface for all protocols
    - Enables seamless tool discovery and execution
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize unified fabric with optional configuration."""
        self.config_path = config_path or "agenticraft.yaml"
        self.config = self._load_config()
        
        # Protocol adapters
        self.a2a_adapter = A2AAdapter() if HAS_A2A else None
        self.mcp_adapter = MCPAdapter() if HAS_MCP else None
        self.anp_adapter = ANPAdapter() if HAS_ANP else None
        
        # AgentiCraft unique features
        self.mesh_network: Optional[MeshNetwork] = None
        self.consensus_engine = None  # Future implementation
        
        # Unified registry
        self.agents: Dict[str, UnifiedAgentRegistration] = {}
        self.tool_registry = UnifiedToolRegistry()
        
        # Protocol health tracking
        self.protocol_health = {
            'a2a': {'available': HAS_A2A, 'healthy': False},
            'mcp': {'available': HAS_MCP, 'healthy': False},
            'anp': {'available': HAS_ANP, 'healthy': False},
            'mesh': {'available': True, 'healthy': False}
        }
        
        logger.info("Unified Protocol Fabric initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml
        from pathlib import Path
        
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        return {}
    
    async def initialize(self):
        """Initialize all protocols and adapters."""
        initialization_tasks = []
        
        # Initialize SDK-based protocols
        if self.a2a_adapter:
            initialization_tasks.append(self._init_a2a())
        if self.mcp_adapter:
            initialization_tasks.append(self._init_mcp())
        if self.anp_adapter:
            initialization_tasks.append(self._init_anp())
            
        # Initialize AgentiCraft unique features
        initialization_tasks.append(self._init_mesh_network())
        
        # Run all initializations in parallel
        results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
        
        # Check results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Initialization failed: {result}")
        
        logger.info("Unified fabric initialization complete")
        return self
    
    async def _init_a2a(self):
        """Initialize A2A protocol with SDK."""
        try:
            await self.a2a_adapter.initialize(self.config.get('a2a', {}))
            self.protocol_health['a2a']['healthy'] = True
            logger.info("✅ A2A protocol initialized")
        except Exception as e:
            logger.error(f"❌ A2A initialization failed: {e}")
            self.protocol_health['a2a']['healthy'] = False
    
    async def _init_mcp(self):
        """Initialize MCP protocol with SDK."""
        try:
            # Connect to configured MCP servers
            mcp_config = self.config.get('mcp', {})
            servers = mcp_config.get('servers', {})
            
            for server_name, server_config in servers.items():
                if isinstance(server_config, str):
                    # Simple URL format
                    await self.mcp_adapter.connect_server(server_name, server_config)
                else:
                    # Full configuration
                    url = server_config.get('url')
                    if url:
                        await self.mcp_adapter.connect_server(
                            server_name, 
                            url,
                            headers=server_config.get('headers'),
                            auth=server_config.get('auth')
                        )
            
            self.protocol_health['mcp']['healthy'] = True
            logger.info("✅ MCP protocol initialized")
        except Exception as e:
            logger.error(f"❌ MCP initialization failed: {e}")
            self.protocol_health['mcp']['healthy'] = False
    
    async def _init_anp(self):
        """Initialize ANP protocol with SDK."""
        try:
            await self.anp_adapter.initialize(self.config.get('anp', {}))
            self.protocol_health['anp']['healthy'] = True
            logger.info("✅ ANP protocol initialized")
        except Exception as e:
            logger.error(f"❌ ANP initialization failed: {e}")
            self.protocol_health['anp']['healthy'] = False
    
    async def _init_mesh_network(self):
        """Initialize AgentiCraft's unique mesh networking."""
        try:
            mesh_config = self.config.get('mesh', {})
            node_id = mesh_config.get('node_id', 'agenticraft-node')
            
            self.mesh_network = MeshNetwork(
                node_id=node_id,
                max_connections=mesh_config.get('max_connections', 5),
                discovery_interval=mesh_config.get('discovery_interval', 30.0)
            )
            
            await self.mesh_network.start()
            self.protocol_health['mesh']['healthy'] = True
            logger.info("✅ Mesh network initialized")
        except Exception as e:
            logger.error(f"❌ Mesh network initialization failed: {e}")
            self.protocol_health['mesh']['healthy'] = False
    
    async def register_agent(
        self,
        agent: AgentiCraftAgent,
        protocols: Optional[List[str]] = None,
        enable_mesh: bool = True,
        enable_consensus: bool = False
    ) -> UnifiedAgentRegistration:
        """
        Register an agent across all requested protocols.
        
        Args:
            agent: AgentiCraft agent to register
            protocols: List of protocols to use (default: all available)
            enable_mesh: Enable mesh networking (AgentiCraft unique)
            enable_consensus: Enable consensus mechanisms (AgentiCraft unique)
            
        Returns:
            Unified registration with all endpoints
        """
        if protocols is None:
            # Use all healthy protocols by default
            protocols = [p for p, health in self.protocol_health.items() 
                        if health['healthy']]
        
        registration = UnifiedAgentRegistration(
            agent_id=str(agent.id),
            agent=agent,
            capabilities=self._extract_capabilities(agent)
        )
        
        # Register with each protocol
        registration_tasks = []
        
        if 'a2a' in protocols and self.a2a_adapter:
            registration_tasks.append(self._register_a2a(agent, registration))
            
        if 'mcp' in protocols and self.mcp_adapter:
            registration_tasks.append(self._register_mcp(agent, registration))
            
        if 'anp' in protocols and self.anp_adapter:
            registration_tasks.append(self._register_anp(agent, registration))
            
        if enable_mesh and self.mesh_network:
            registration_tasks.append(self._register_mesh(agent, registration))
        
        # Execute registrations in parallel
        await asyncio.gather(*registration_tasks)
        
        # Store registration
        self.agents[registration.agent_id] = registration
        
        # Register tools from agent
        await self._register_agent_tools(agent)
        
        logger.info(f"Agent '{agent.name}' registered across {len(protocols)} protocols")
        return registration
    
    def _extract_capabilities(self, agent: AgentiCraftAgent) -> List[str]:
        """Extract capabilities from agent."""
        capabilities = []
        
        # Tool capabilities
        if hasattr(agent, '_tool_registry'):
            tools = agent._tool_registry.list_tools()
            capabilities.extend([f"tool:{tool}" for tool in tools])
        
        # Workflow capabilities
        if hasattr(agent, 'workflows'):
            capabilities.extend([f"workflow:{wf}" for wf in agent.workflows])
        
        # Custom capabilities
        if hasattr(agent, 'capabilities'):
            capabilities.extend(agent.capabilities)
        
        return capabilities
    
    async def _register_a2a(self, agent: AgentiCraftAgent, registration: UnifiedAgentRegistration):
        """Register agent with A2A protocol."""
        endpoint = await self.a2a_adapter.register_agent(agent)
        registration.a2a_endpoint = endpoint
    
    async def _register_mcp(self, agent: AgentiCraftAgent, registration: UnifiedAgentRegistration):
        """Register agent with MCP protocol."""
        endpoint = await self.mcp_adapter.create_server_for_agent(agent)
        registration.mcp_endpoint = endpoint
    
    async def _register_anp(self, agent: AgentiCraftAgent, registration: UnifiedAgentRegistration):
        """Register agent with ANP protocol."""
        did = await self.anp_adapter.register_agent(agent)
        registration.anp_did = did
    
    async def _register_mesh(self, agent: AgentiCraftAgent, registration: UnifiedAgentRegistration):
        """Register agent with mesh network."""
        if self.mesh_network:
            await self.mesh_network.register_agent(agent)
            registration.mesh_node_id = self.mesh_network.node_id
    
    async def _register_agent_tools(self, agent: AgentiCraftAgent):
        """Register agent's tools in unified registry."""
        if hasattr(agent, '_tool_registry'):
            for tool_name in agent._tool_registry.list_tools():
                tool = agent._tool_registry.get_tool(tool_name)
                await self.tool_registry.register_tool(
                    tool=tool,
                    source='local',
                    agent_id=str(agent.id)
                )
    
    async def execute(
        self,
        task: str,
        target_agent: Optional[str] = None,
        capability: Optional[str] = None,
        protocol: Optional[str] = None,
        consensus_required: bool = False,
        timeout: float = 30.0,
        **kwargs
    ) -> Any:
        """
        Execute a task using the most appropriate protocol and agent.
        
        Args:
            task: Task description or prompt
            target_agent: Specific agent ID to use
            capability: Required capability (for discovery)
            protocol: Preferred protocol
            consensus_required: Require consensus from multiple agents
            timeout: Execution timeout
            **kwargs: Additional arguments
            
        Returns:
            Execution result
        """
        # If consensus required, use special handling
        if consensus_required:
            return await self._execute_with_consensus(
                task, capability, timeout, **kwargs
            )
        
        # Determine target agent
        if not target_agent and capability:
            target_agent = await self._discover_agent(capability, protocol)
        
        if not target_agent:
            raise ValueError("No target agent specified or discovered")
        
        # Get registration
        registration = self.agents.get(target_agent)
        if not registration:
            # Try external agent
            return await self._execute_external(
                task, target_agent, protocol, timeout, **kwargs
            )
        
        # Execute through appropriate protocol
        if protocol:
            return await self._execute_via_protocol(
                registration, task, protocol, timeout, **kwargs
            )
        else:
            # Direct execution
            return await registration.agent.arun(task, **kwargs)
    
    async def _execute_with_consensus(
        self,
        task: str,
        capability: Optional[str],
        timeout: float,
        **kwargs
    ) -> Any:
        """Execute with consensus from multiple agents."""
        # Find capable agents
        if capability:
            agents = await self._discover_agents(capability)
        else:
            agents = list(self.agents.values())
        
        if len(agents) < 3:
            logger.warning("Consensus requires at least 3 agents, falling back to single agent")
            return await self.execute(task, capability=capability, timeout=timeout, **kwargs)
        
        # Execute on multiple agents in parallel
        tasks = []
        for agent_reg in agents[:5]:  # Limit to 5 for performance
            tasks.append(
                self._execute_via_best_protocol(agent_reg, task, timeout, **kwargs)
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        # Apply consensus algorithm
        if self.consensus_engine:
            return await self.consensus_engine.reach_consensus(valid_results)
        else:
            # Simple majority voting
            from collections import Counter
            result_counts = Counter(str(r) for r in valid_results)
            consensus_result = result_counts.most_common(1)[0][0]
            return consensus_result
    
    async def _discover_agent(self, capability: str, protocol: Optional[str] = None) -> Optional[str]:
        """Discover an agent with the required capability."""
        agents = await self._discover_agents(capability, protocol)
        return agents[0].agent_id if agents else None
    
    async def _discover_agents(
        self,
        capability: str,
        protocol: Optional[str] = None
    ) -> List[UnifiedAgentRegistration]:
        """Discover agents with the required capability."""
        discovered = []
        
        # Check local agents
        for agent_reg in self.agents.values():
            if capability in agent_reg.capabilities:
                discovered.append(agent_reg)
        
        # Check through protocols
        if protocol != 'local':
            if self.anp_adapter and (not protocol or protocol == 'anp'):
                anp_agents = await self.anp_adapter.discover(capability)
                # Convert to registrations
                for agent_info in anp_agents:
                    discovered.append(
                        UnifiedAgentRegistration(
                            agent_id=agent_info['did'],
                            agent=None,  # External agent
                            anp_did=agent_info['did'],
                            capabilities=agent_info.get('capabilities', [])
                        )
                    )
        
        return discovered
    
    async def _execute_via_protocol(
        self,
        registration: UnifiedAgentRegistration,
        task: str,
        protocol: str,
        timeout: float,
        **kwargs
    ) -> Any:
        """Execute through specific protocol."""
        if protocol == 'a2a' and registration.a2a_endpoint:
            return await self.a2a_adapter.execute_task(
                registration.a2a_endpoint, task, timeout, **kwargs
            )
        elif protocol == 'mcp' and registration.mcp_endpoint:
            # For MCP, we might need to call a specific tool
            tool_name = kwargs.get('tool', 'execute')
            return await self.mcp_adapter.call_tool(
                registration.mcp_endpoint, tool_name, task=task, **kwargs
            )
        elif protocol == 'mesh' and self.mesh_network:
            return await self.mesh_network.execute_distributed(
                task, 
                capability_required=registration.capabilities[0] if registration.capabilities else None,
                timeout=timeout
            )
        else:
            # Fallback to direct execution
            return await registration.agent.arun(task, **kwargs)
    
    async def _execute_via_best_protocol(
        self,
        registration: UnifiedAgentRegistration,
        task: str,
        timeout: float,
        **kwargs
    ) -> Any:
        """Execute via the best available protocol for an agent."""
        # Priority order: direct > mesh > a2a > mcp > anp
        if registration.agent:
            return await registration.agent.arun(task, **kwargs)
        elif registration.mesh_node_id and self.mesh_network:
            return await self._execute_via_protocol(registration, task, 'mesh', timeout, **kwargs)
        elif registration.a2a_endpoint:
            return await self._execute_via_protocol(registration, task, 'a2a', timeout, **kwargs)
        elif registration.mcp_endpoint:
            return await self._execute_via_protocol(registration, task, 'mcp', timeout, **kwargs)
        else:
            raise RuntimeError(f"No protocol available for agent {registration.agent_id}")
    
    async def _execute_external(
        self,
        task: str,
        agent_id: str,
        protocol: Optional[str],
        timeout: float,
        **kwargs
    ) -> Any:
        """Execute on external agent."""
        # Try ANP first for external agents
        if self.anp_adapter:
            try:
                return await self.anp_adapter.execute_on_did(
                    agent_id, task, timeout, **kwargs
                )
            except Exception as e:
                logger.error(f"ANP execution failed: {e}")
        
        raise RuntimeError(f"Cannot execute on external agent {agent_id}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all protocols."""
        return {
            'protocols': self.protocol_health,
            'registered_agents': len(self.agents),
            'total_tools': self.tool_registry.count(),
            'mesh_nodes': len(self.mesh_network.nodes) if self.mesh_network else 0
        }
    
    async def shutdown(self):
        """Gracefully shutdown all protocols."""
        shutdown_tasks = []
        
        if self.a2a_adapter:
            shutdown_tasks.append(self.a2a_adapter.shutdown())
        if self.mcp_adapter:
            shutdown_tasks.append(self.mcp_adapter.shutdown())
        if self.anp_adapter:
            shutdown_tasks.append(self.anp_adapter.shutdown())
        if self.mesh_network:
            shutdown_tasks.append(self.mesh_network.stop())
        
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        logger.info("Unified fabric shutdown complete")


class UnifiedToolRegistry:
    """Unified tool registry that prioritizes SDK tools."""
    
    def __init__(self):
        self.tools = {
            'mcp': {},      # MCP tools (highest priority)
            'a2a': {},      # A2A agent capabilities as tools
            'local': {},    # Local AgentiCraft tools
        }
        self.tool_metadata = {}
    
    async def register_tool(
        self,
        tool: Any,
        source: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a tool from any source."""
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        
        self.tools[source][tool_name] = tool
        self.tool_metadata[f"{source}:{tool_name}"] = {
            'source': source,
            'agent_id': agent_id,
            'registered_at': datetime.now(),
            **(metadata or {})
        }
    
    async def get_tool(self, name: str) -> Optional[Any]:
        """Get tool by name with priority: MCP > A2A > Local."""
        # Check in priority order
        for source in ['mcp', 'a2a', 'local']:
            if name in self.tools[source]:
                return self.tools[source][name]
        return None
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = await self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        # Execute based on tool type
        if hasattr(tool, 'arun'):
            return await tool.arun(**kwargs)
        elif hasattr(tool, 'execute'):
            return await tool.execute(**kwargs)
        elif callable(tool):
            return await tool(**kwargs)
        else:
            raise ValueError(f"Tool '{name}' is not executable")
    
    def list_tools(self, source: Optional[str] = None) -> List[str]:
        """List all available tools."""
        if source:
            return list(self.tools.get(source, {}).keys())
        
        # All tools with source prefix
        all_tools = []
        for source, tools in self.tools.items():
            all_tools.extend([f"{source}:{name}" for name in tools.keys()])
        return all_tools
    
    def count(self) -> int:
        """Total number of registered tools."""
        return sum(len(tools) for tools in self.tools.values())
```

## 2. Fast-Agent Inspired Decorators

### `/agenticraft/fabric/decorators.py`

```python
"""Fast-agent inspired decorators for AgentiCraft with SDK integration."""

import asyncio
from functools import wraps
from typing import List, Optional, Dict, Any, Callable, Union
import inspect

from ..core.agent import Agent
from .unified import UnifiedProtocolFabric

# Global fabric instance
_fabric: Optional[UnifiedProtocolFabric] = None


def get_fabric() -> UnifiedProtocolFabric:
    """Get or create global fabric instance."""
    global _fabric
    if _fabric is None:
        _fabric = UnifiedProtocolFabric()
        # Initialize in background
        asyncio.create_task(_fabric.initialize())
    return _fabric


def agent(
    name: Optional[str] = None,
    instructions: Optional[str] = None,
    servers: Optional[List[str]] = None,
    model: Optional[str] = None,
    protocols: Optional[List[str]] = None,
    enable_mesh: bool = True,
    enable_consensus: bool = False,
    **kwargs
) -> Callable:
    """
    Create an agent with automatic SDK integration.
    
    Inspired by fast-agent but enhanced with AgentiCraft features.
    
    Args:
        name: Agent name
        instructions: System instructions
        servers: MCP servers to connect (e.g., ["brave_search", "github"])
        model: LLM model to use
        protocols: Protocols to enable (default: all)
        enable_mesh: Enable mesh networking
        enable_consensus: Enable consensus mechanisms
        **kwargs: Additional agent configuration
        
    Example:
        @agent("researcher", servers=["brave_search", "arxiv"])
        async def research_agent(self, topic: str):
            # Tools are automatically available
            results = await self.tools.brave_search(topic)
            papers = await self.tools.arxiv.search(topic)
            return self.synthesize(results, papers)
    """
    def decorator(func: Callable) -> 'SDKAgent':
        # Extract function metadata
        agent_name = name or func.__name__.replace('_', '-')
        agent_instructions = instructions or func.__doc__ or f"Agent {agent_name}"
        
        # Create agent class
        class SDKAgent(Agent):
            def __init__(self):
                super().__init__(
                    name=agent_name,
                    instructions=agent_instructions,
                    model=model or "gpt-4",
                    **kwargs
                )
                
                # Store configuration
                self.mcp_servers = servers or []
                self.protocols = protocols
                self.enable_mesh = enable_mesh
                self.enable_consensus = enable_consensus
                
                # Function binding
                self._func = func
                self._is_async = asyncio.iscoroutinefunction(func)
                
                # Tool access
                self.tools = ToolAccessor(self)
                
                # Fabric connection
                self._fabric = get_fabric()
                self._registered = False
            
            async def initialize(self):
                """Initialize SDK connections."""
                if not self._registered:
                    # Register with fabric
                    await self._fabric.register_agent(
                        self,
                        protocols=self.protocols,
                        enable_mesh=self.enable_mesh,
                        enable_consensus=self.enable_consensus
                    )
                    
                    # Connect to MCP servers
                    for server in self.mcp_servers:
                        if self._fabric.mcp_adapter:
                            await self._fabric.mcp_adapter.connect_server(
                                server,
                                self._get_server_url(server)
                            )
                    
                    self._registered = True
            
            def _get_server_url(self, server_name: str) -> str:
                """Get server URL from configuration."""
                config = self._fabric.config.get('mcp', {}).get('servers', {})
                server_config = config.get(server_name, {})
                
                if isinstance(server_config, str):
                    return server_config
                elif isinstance(server_config, dict):
                    return server_config.get('url', f"mcp://{server_name}")
                else:
                    return f"mcp://{server_name}"
            
            async def execute(self, *args, **kwargs) -> Any:
                """Execute the decorated function."""
                # Ensure initialized
                await self.initialize()
                
                # Bind self to function
                if self._is_async:
                    return await self._func(self, *args, **kwargs)
                else:
                    return self._func(self, *args, **kwargs)
            
            async def __call__(self, *args, **kwargs) -> Any:
                """Make agent directly callable."""
                return await self.execute(*args, **kwargs)
            
            # Enhanced methods
            async def synthesize(self, *data_sources) -> str:
                """Synthesize information from multiple sources."""
                combined = "\n\n".join(str(d) for d in data_sources)
                return await self.arun(
                    f"Synthesize the following information:\n{combined}"
                )
            
            async def analyze(self, data: Any) -> Dict[str, Any]:
                """Analyze data and return structured insights."""
                result = await self.arun(
                    f"Analyze this data and provide structured insights: {data}"
                )
                # Parse result as JSON if possible
                try:
                    import json
                    return json.loads(result.content)
                except:
                    return {"analysis": result.content}
            
            async def think(self, question: str) -> str:
                """Think through a problem step by step."""
                result = await self.arun(
                    f"Think through this step by step: {question}"
                )
                return result.reasoning or result.content
        
        # Create and return instance
        return SDKAgent()
    
    # Handle both @agent and @agent() syntax
    if callable(name) and instructions is None and servers is None:
        func = name
        name = None
        return decorator(func)
    else:
        return decorator


class ToolAccessor:
    """Provides natural tool access like self.tools.tool_name()"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self._cache = {}
    
    def __getattr__(self, name: str) -> Callable:
        """Dynamic tool access."""
        if name not in self._cache:
            # Create tool wrapper
            async def tool_wrapper(**kwargs):
                fabric = get_fabric()
                return await fabric.tool_registry.execute_tool(name, **kwargs)
            
            self._cache[name] = tool_wrapper
        
        return self._cache[name]
    
    def __dir__(self) -> List[str]:
        """List available tools."""
        fabric = get_fabric()
        return fabric.tool_registry.list_tools()


# Workflow decorators inspired by fast-agent

def workflow(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parallel: bool = False,
    checkpointed: bool = False
) -> Callable:
    """
    Create a workflow with automatic state management.
    
    Example:
        @workflow("research_pipeline", checkpointed=True)
        class ResearchWorkflow:
            async def search(self, query: str) -> List[str]:
                # Search implementation
                
            async def analyze(self, sources: List[str]) -> Dict:
                # Analysis implementation
                
            async def synthesize(self, analysis: Dict) -> str:
                # Synthesis implementation
    """
    def decorator(cls):
        # Workflow implementation in next section
        return cls
    
    return decorator


def chain(
    agents: List[Union[str, Agent]],
    aggregate: bool = False,
    timeout: float = 300.0
) -> Callable:
    """
    Chain multiple agents sequentially.
    
    Example:
        @chain(["researcher", "analyst", "writer"])
        async def content_pipeline(topic: str):
            # Automatically chains the agents
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            fabric = get_fabric()
            
            # Initial input from function arguments
            if args:
                current_input = args[0]
            else:
                current_input = kwargs
            
            results = []
            
            for agent_ref in agents:
                if isinstance(agent_ref, str):
                    # Execute via fabric
                    result = await fabric.execute(
                        str(current_input),
                        target_agent=agent_ref,
                        timeout=timeout / len(agents)
                    )
                else:
                    # Direct agent execution
                    result = await agent_ref.arun(str(current_input))
                
                results.append(result)
                
                # Use result as next input unless aggregating
                if not aggregate:
                    current_input = result
            
            return results if aggregate else current_input
        
        return wrapper
    
    if len(agents) == 1 and callable(agents[0]):
        # Handle @chain syntax without parentheses
        func = agents[0]
        agents = []
        return decorator(func)
    
    return decorator


def parallel(
    agents: List[Union[str, Agent]],
    merge_strategy: str = "all",
    timeout: float = 60.0
) -> Callable:
    """
    Execute agents in parallel.
    
    Args:
        agents: List of agents to execute in parallel
        merge_strategy: How to merge results ("all", "first", "consensus")
        timeout: Timeout for parallel execution
        
    Example:
        @parallel(["analyst1", "analyst2", "analyst3"], merge_strategy="consensus")
        async def multi_analysis(data: str):
            # Runs analysts in parallel and merges results
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            fabric = get_fabric()
            
            # Input from function
            input_data = args[0] if args else str(kwargs)
            
            # Create tasks
            tasks = []
            for agent_ref in agents:
                if isinstance(agent_ref, str):
                    task = fabric.execute(
                        input_data,
                        target_agent=agent_ref,
                        timeout=timeout
                    )
                else:
                    task = agent_ref.arun(input_data)
                
                tasks.append(task)
            
            # Execute in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            valid_results = [r for r in results if not isinstance(r, Exception)]
            
            # Apply merge strategy
            if merge_strategy == "all":
                return valid_results
            elif merge_strategy == "first":
                return valid_results[0] if valid_results else None
            elif merge_strategy == "consensus":
                # Use fabric's consensus mechanism
                return await fabric._execute_with_consensus(
                    input_data,
                    capability=None,
                    timeout=timeout
                )
            else:
                return valid_results
        
        return wrapper
    
    return decorator


def router(
    routes: Dict[str, Union[str, Agent]],
    default: Optional[Union[str, Agent]] = None,
    model: str = "gpt-4"
) -> Callable:
    """
    Route to different agents based on input.
    
    Example:
        @router({
            "technical": technical_agent,
            "creative": creative_agent,
            "analytical": analytical_agent
        })
        async def smart_assistant(query: str):
            # Automatically routes to the right agent
            pass
    """
    def decorator(func: Callable):
        # Create routing agent
        routing_instructions = f"""
        You are a routing agent. Analyze the user's query and determine which type of agent should handle it.
        
        Available routes:
        {', '.join(routes.keys())}
        
        Respond with just the route name.
        """
        
        router_agent = Agent(
            name="router",
            instructions=routing_instructions,
            model=model
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            fabric = get_fabric()
            
            # Get input
            query = args[0] if args else str(kwargs)
            
            # Determine route
            route_result = await router_agent.arun(query)
            selected_route = route_result.content.strip().lower()
            
            # Get agent for route
            agent_ref = routes.get(selected_route, default)
            
            if not agent_ref:
                raise ValueError(f"No route found for: {selected_route}")
            
            # Execute on selected agent
            if isinstance(agent_ref, str):
                return await fabric.execute(query, target_agent=agent_ref)
            else:
                return await agent_ref.arun(query)
        
        return wrapper
    
    return decorator
```

## 3. Simplified Tool System

### `/agenticraft/tools/base.py`

```python
"""Simplified tool system that prioritizes SDK tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio

from ..core.exceptions import ToolExecutionError, ToolNotFoundError


class Tool(ABC):
    """Minimal tool interface for AgentiCraft."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM providers."""
        pass
    
    def validate_args(self, **kwargs: Any) -> bool:
        """Validate arguments before execution."""
        return True


class SimpleTool(Tool):
    """Simple tool wrapper for functions."""
    
    def __init__(self, func: callable, name: Optional[str] = None, 
                 description: Optional[str] = None):
        self.func = func
        self.is_async = asyncio.iscoroutinefunction(func)
        
        super().__init__(
            name=name or func.__name__,
            description=description or func.__doc__ or ""
        )
    
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the wrapped function."""
        try:
            if self.is_async:
                return await self.func(**kwargs)
            else:
                return self.func(**kwargs)
        except Exception as e:
            raise ToolExecutionError(f"Tool '{self.name}' failed: {e}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate simple schema from function signature."""
        import inspect
        
        sig = inspect.signature(self.func)
        parameters = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            # Basic type inference
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
            
            parameters[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required
            }
        }


def tool(name: Optional[str] = None, description: Optional[str] = None) -> callable:
    """Simple tool decorator."""
    def decorator(func: callable) -> SimpleTool:
        return SimpleTool(func, name, description)
    
    if callable(name):
        func = name
        name = None
        return decorator(func)
    
    return decorator
```

### `/agenticraft/tools/registry.py`

```python
"""Unified tool registry that integrates with SDK tools."""

from typing import Dict, List, Any, Optional, Union
import logging

from .base import Tool
from ..fabric.unified import UnifiedProtocolFabric

logger = logging.getLogger(__name__)


class UnifiedToolRegistry:
    """
    Registry that unifies local tools with SDK tools.
    
    Priority order: MCP > A2A > Local
    """
    
    def __init__(self, fabric: Optional[UnifiedProtocolFabric] = None):
        self.fabric = fabric
        self.local_tools: Dict[str, Tool] = {}
        
    def register_local(self, tool: Union[Tool, callable], 
                      name: Optional[str] = None) -> None:
        """Register a local tool."""
        if callable(tool) and not isinstance(tool, Tool):
            from .base import SimpleTool
            tool = SimpleTool(tool, name)
        
        tool_name = name or tool.name
        self.local_tools[tool_name] = tool
        logger.info(f"Registered local tool: {tool_name}")
    
    async def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name with SDK priority."""
        # Try fabric registry first (includes MCP and A2A)
        if self.fabric:
            sdk_tool = await self.fabric.tool_registry.get_tool(name)
            if sdk_tool:
                return self._wrap_sdk_tool(sdk_tool, name)
        
        # Fall back to local tools
        return self.local_tools.get(name)
    
    def _wrap_sdk_tool(self, sdk_tool: Any, name: str) -> Tool:
        """Wrap SDK tool in AgentiCraft Tool interface."""
        from .adapters import SDKToolAdapter
        return SDKToolAdapter(sdk_tool, name)
    
    async def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute tool by name."""
        tool = await self.get_tool(name)
        
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        
        return await tool.execute(**kwargs)
    
    def list_tools(self) -> List[str]:
        """List all available tools."""
        tools = list(self.local_tools.keys())
        
        if self.fabric:
            sdk_tools = self.fabric.tool_registry.list_tools()
            tools.extend(sdk_tools)
        
        return sorted(set(tools))
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools."""
        schemas = []
        
        # Local tools
        for tool in self.local_tools.values():
            schemas.append(tool.get_schema())
        
        # SDK tools would need schema conversion
        # This is handled by the fabric
        
        return schemas
```

### `/agenticraft/tools/adapters.py`

```python
"""Adapters for SDK tools to work with AgentiCraft."""

from typing import Any, Dict
from .base import Tool


class SDKToolAdapter(Tool):
    """Adapter for SDK tools (MCP, A2A) to AgentiCraft Tool interface."""
    
    def __init__(self, sdk_tool: Any, name: str):
        self.sdk_tool = sdk_tool
        
        # Extract description
        description = ""
        if hasattr(sdk_tool, 'description'):
            description = sdk_tool.description
        elif hasattr(sdk_tool, '__doc__'):
            description = sdk_tool.__doc__ or ""
        
        super().__init__(name=name, description=description)
    
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the SDK tool."""
        # Different SDK tools have different execution methods
        if hasattr(self.sdk_tool, 'arun'):
            return await self.sdk_tool.arun(**kwargs)
        elif hasattr(self.sdk_tool, 'execute'):
            return await self.sdk_tool.execute(**kwargs)
        elif hasattr(self.sdk_tool, 'call'):
            return await self.sdk_tool.call(**kwargs)
        elif callable(self.sdk_tool):
            return await self.sdk_tool(**kwargs)
        else:
            raise ValueError(f"SDK tool {self.name} is not executable")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get schema from SDK tool."""
        # Try different schema methods
        if hasattr(self.sdk_tool, 'get_schema'):
            return self.sdk_tool.get_schema()
        elif hasattr(self.sdk_tool, 'schema'):
            return self.sdk_tool.schema
        elif hasattr(self.sdk_tool, 'to_openai_schema'):
            return self.sdk_tool.to_openai_schema()
        else:
            # Fallback schema
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
```

## 4. LangGraph-Inspired Orchestration

### `/agenticraft/orchestration/state.py`

```python
"""State management for stateful workflows."""

from typing import TypeVar, Generic, Type, Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import copy
import json

T = TypeVar('T')


@dataclass
class StateSnapshot:
    """Snapshot of state at a point in time."""
    timestamp: datetime
    data: Dict[str, Any]
    step: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager(Generic[T]):
    """
    Type-safe state management for workflows.
    
    Features:
    - Type safety with generics
    - State history and rollback
    - Persistence support
    - State validation
    """
    
    def __init__(self, state_class: Type[T], initial_data: Optional[Dict[str, Any]] = None):
        """Initialize state manager with state class."""
        self.state_class = state_class
        self._state = state_class(**(initial_data or {}))
        self._history: List[StateSnapshot] = []
        self._checkpoints: Dict[str, StateSnapshot] = {}
        self._listeners: List[callable] = []
    
    @property
    def current(self) -> T:
        """Get current state."""
        return self._state
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state attribute."""
        return getattr(self._state, key, default)
    
    def update(self, **kwargs) -> T:
        """Update state with validation."""
        # Create snapshot before update
        self._create_snapshot()
        
        # Update state
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
            else:
                raise AttributeError(f"State has no attribute '{key}'")
        
        # Notify listeners
        self._notify_listeners()
        
        return self._state
    
    def _create_snapshot(self, step: Optional[str] = None) -> StateSnapshot:
        """Create snapshot of current state."""
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            data=asdict(self._state) if hasattr(self._state, '__dataclass_fields__') else vars(self._state).copy(),
            step=step
        )
        self._history.append(snapshot)
        return snapshot
    
    def checkpoint(self, name: str) -> None:
        """Create named checkpoint."""
        snapshot = self._create_snapshot(step=name)
        self._checkpoints[name] = snapshot
    
    def rollback(self, steps: int = 1) -> T:
        """Rollback to previous state."""
        if len(self._history) < steps:
            raise ValueError(f"Cannot rollback {steps} steps, only {len(self._history)} available")
        
        # Get target snapshot
        target_snapshot = self._history[-(steps + 1)]
        
        # Restore state
        self._restore_from_snapshot(target_snapshot)
        
        # Remove rolled back history
        self._history = self._history[:-(steps)]
        
        return self._state
    
    def restore_checkpoint(self, name: str) -> T:
        """Restore from named checkpoint."""
        if name not in self._checkpoints:
            raise ValueError(f"Checkpoint '{name}' not found")
        
        snapshot = self._checkpoints[name]
        self._restore_from_snapshot(snapshot)
        
        return self._state
    
    def _restore_from_snapshot(self, snapshot: StateSnapshot) -> None:
        """Restore state from snapshot."""
        # Create new instance with snapshot data
        self._state = self.state_class(**snapshot.data)
        self._notify_listeners()
    
    def add_listener(self, listener: callable) -> None:
        """Add state change listener."""
        self._listeners.append(listener)
    
    def _notify_listeners(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            try:
                listener(self._state)
            except Exception:
                pass  # Don't let listener errors affect state management
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        if hasattr(self._state, '__dataclass_fields__'):
            return asdict(self._state)
        else:
            return vars(self._state).copy()
    
    def to_json(self) -> str:
        """Convert state to JSON."""
        return json.dumps(self.to_dict(), default=str)
    
    def get_history(self, limit: Optional[int] = None) -> List[StateSnapshot]:
        """Get state history."""
        if limit:
            return self._history[-limit:]
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear state history (keeps current state)."""
        self._history.clear()
    
    def merge(self, other_state: T) -> T:
        """Merge another state into current state."""
        self._create_snapshot()
        
        # Merge attributes
        for key, value in vars(other_state).items():
            if hasattr(self._state, key) and value is not None:
                setattr(self._state, key, value)
        
        self._notify_listeners()
        return self._state
```

### `/agenticraft/orchestration/graph.py`

```python
"""Graph-based agent orchestration inspired by LangGraph."""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

from ..core.agent import Agent
from .state import StateManager


@dataclass
class GraphNode:
    """Node in the agent graph."""
    id: str
    name: str
    agent: Optional[Agent] = None
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, state: Any, context: Dict[str, Any]) -> Any:
        """Execute node logic."""
        if self.agent:
            return await self.agent.arun(state, context=context)
        elif self.handler:
            if asyncio.iscoroutinefunction(self.handler):
                return await self.handler(state, context)
            else:
                return self.handler(state, context)
        else:
            raise ValueError(f"Node {self.name} has no agent or handler")


@dataclass
class GraphEdge:
    """Edge in the agent graph."""
    from_node: str
    to_node: str
    condition: Optional[Callable] = None
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    async def should_traverse(self, state: Any) -> bool:
        """Check if edge should be traversed."""
        if self.condition is None:
            return True
        
        if asyncio.iscoroutinefunction(self.condition):
            return await self.condition(state)
        else:
            return self.condition(state)


class AgentGraph:
    """
    Graph-based agent orchestration.
    
    Features:
    - Directed graph of agents
    - Conditional edges
    - Parallel execution
    - Cycle detection
    - State passing
    """
    
    def __init__(self, name: str = "AgentGraph"):
        self.name = name
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self.entry_point: Optional[str] = None
        self.exit_points: Set[str] = set()
    
    def add_node(
        self,
        name: str,
        agent: Optional[Agent] = None,
        handler: Optional[Callable] = None,
        node_id: Optional[str] = None,
        **metadata
    ) -> str:
        """Add node to graph."""
        if not agent and not handler:
            raise ValueError("Node must have either agent or handler")
        
        node_id = node_id or str(uuid.uuid4())
        node = GraphNode(
            id=node_id,
            name=name,
            agent=agent,
            handler=handler,
            metadata=metadata
        )
        
        self.nodes[node_id] = node
        
        # First node becomes entry point by default
        if self.entry_point is None:
            self.entry_point = node_id
        
        return node_id
    
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable] = None,
        weight: float = 1.0,
        **metadata
    ) -> None:
        """Add edge between nodes."""
        # Validate nodes exist
        if from_node not in self.nodes:
            raise ValueError(f"Node {from_node} not found")
        if to_node not in self.nodes:
            raise ValueError(f"Node {to_node} not found")
        
        edge = GraphEdge(
            from_node=from_node,
            to_node=to_node,
            condition=condition,
            weight=weight,
            metadata=metadata
        )
        
        self.edges[from_node].append(edge)
    
    def set_entry_point(self, node_id: str) -> None:
        """Set graph entry point."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        self.entry_point = node_id
    
    def add_exit_point(self, node_id: str) -> None:
        """Add exit point."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        self.exit_points.add(node_id)
    
    async def execute(
        self,
        initial_state: Any,
        context: Optional[Dict[str, Any]] = None,
        max_steps: int = 100
    ) -> Tuple[Any, List[str]]:
        """
        Execute graph from entry point.
        
        Returns:
            Tuple of (final_state, execution_path)
        """
        if not self.entry_point:
            raise ValueError("No entry point defined")
        
        context = context or {}
        state = initial_state
        current_node = self.entry_point
        path = []
        visited = set()
        steps = 0
        
        while current_node and steps < max_steps:
            # Check for cycles
            if current_node in visited:
                # Allow revisiting nodes but track it
                context['cycle_detected'] = True
            
            visited.add(current_node)
            path.append(current_node)
            steps += 1
            
            # Execute current node
            node = self.nodes[current_node]
            state = await node.execute(state, context)
            
            # Check if exit point
            if current_node in self.exit_points:
                break
            
            # Find next node
            next_node = await self._find_next_node(current_node, state)
            current_node = next_node
        
        if steps >= max_steps:
            raise RuntimeError(f"Graph execution exceeded max steps ({max_steps})")
        
        return state, path
    
    async def _find_next_node(self, current_node: str, state: Any) -> Optional[str]:
        """Find next node based on edges and conditions."""
        edges = self.edges.get(current_node, [])
        
        if not edges:
            return None
        
        # Evaluate all edges
        valid_edges = []
        for edge in edges:
            if await edge.should_traverse(state):
                valid_edges.append(edge)
        
        if not valid_edges:
            return None
        
        # Select edge with highest weight
        selected_edge = max(valid_edges, key=lambda e: e.weight)
        return selected_edge.to_node
    
    def get_parallel_groups(self) -> List[Set[str]]:
        """Identify groups of nodes that can execute in parallel."""
        # Simple analysis: nodes with no dependencies on each other
        groups = []
        
        # Find nodes with same incoming edges
        incoming = defaultdict(set)
        for from_node, edges in self.edges.items():
            for edge in edges:
                incoming[edge.to_node].add(from_node)
        
        # Group nodes with identical incoming sets
        grouped = defaultdict(set)
        for node, sources in incoming.items():
            key = tuple(sorted(sources))
            grouped[key].add(node)
        
        # Convert to list
        for nodes in grouped.values():
            if len(nodes) > 1:
                groups.append(nodes)
        
        return groups
    
    async def execute_parallel(
        self,
        nodes: List[str],
        state: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute multiple nodes in parallel."""
        tasks = []
        
        for node_id in nodes:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                task = node.execute(state, context)
                tasks.append((node_id, task))
        
        # Execute in parallel
        results = {}
        for node_id, task in tasks:
            try:
                result = await task
                results[node_id] = result
            except Exception as e:
                results[node_id] = {'error': str(e)}
        
        return results
    
    def visualize(self) -> str:
        """Generate Mermaid diagram of the graph."""
        lines = ["graph TD"]
        
        # Add nodes
        for node_id, node in self.nodes.items():
            shape = "[" if node_id == self.entry_point else "("
            shape_end = "]" if node_id == self.entry_point else ")"
            
            if node_id in self.exit_points:
                shape = "{{"
                shape_end = "}}"
            
            lines.append(f"    {node_id}{shape}{node.name}{shape_end}")
        
        # Add edges
        for from_node, edges in self.edges.items():
            for edge in edges:
                label = ""
                if edge.condition:
                    label = f"|{edge.condition.__name__ if hasattr(edge.condition, '__name__') else 'condition'}|"
                
                lines.append(f"    {from_node} -->{label} {edge.to_node}")
        
        return "\n".join(lines)
    
    def validate(self) -> List[str]:
        """Validate graph structure."""
        issues = []
        
        # Check entry point
        if not self.entry_point:
            issues.append("No entry point defined")
        
        # Check for unreachable nodes
        reachable = self._find_reachable_nodes()
        unreachable = set(self.nodes.keys()) - reachable
        if unreachable:
            issues.append(f"Unreachable nodes: {unreachable}")
        
        # Check for nodes with no outgoing edges (except exit points)
        for node_id in self.nodes:
            if node_id not in self.edges and node_id not in self.exit_points:
                issues.append(f"Node {node_id} has no outgoing edges and is not an exit point")
        
        return issues
    
    def _find_reachable_nodes(self) -> Set[str]:
        """Find all nodes reachable from entry point."""
        if not self.entry_point:
            return set()
        
        reachable = set()
        to_visit = [self.entry_point]
        
        while to_visit:
            current = to_visit.pop()
            if current in reachable:
                continue
            
            reachable.add(current)
            
            # Add connected nodes
            for edge in self.edges.get(current, []):
                to_visit.append(edge.to_node)
        
        return reachable
```

### `/agenticraft/orchestration/workflow.py`

```python
"""Stateful workflow implementation with LangGraph patterns."""

import asyncio
from typing import Any, Dict, List, Optional, Type, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import inspect

from .state import StateManager
from .graph import AgentGraph, GraphNode
from ..core.agent import Agent


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result from a workflow step."""
    step_name: str
    status: StepStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StatefulWorkflow:
    """
    Stateful workflow with LangGraph-inspired patterns.
    
    Features:
    - State management with history
    - Conditional branching
    - Parallel execution
    - Checkpointing
    - Error recovery
    """
    
    def __init__(
        self,
        name: str,
        state_class: Type,
        checkpointed: bool = False,
        max_retries: int = 3
    ):
        self.name = name
        self.state_class = state_class
        self.checkpointed = checkpointed
        self.max_retries = max_retries
        
        # Components
        self.graph = AgentGraph(name)
        self.state_manager: Optional[StateManager] = None
        self.steps: Dict[str, GraphNode] = {}
        self.results: List[StepResult] = []
        
        # Decorators for building workflow
        self._entry_point: Optional[str] = None
        self._current_building_node: Optional[str] = None
    
    def node(self, name: Optional[str] = None) -> Callable:
        """Decorator to define a workflow node."""
        def decorator(func: Callable) -> Callable:
            node_name = name or func.__name__
            
            # Add node to graph
            node_id = self.graph.add_node(
                name=node_name,
                handler=func
            )
            
            self.steps[node_name] = self.graph.nodes[node_id]
            
            # Store for edge building
            self._current_building_node = node_id
            
            # Mark as entry point if it's the first node
            if self._entry_point is None:
                self._entry_point = node_id
                self.graph.set_entry_point(node_id)
            
            return func
        
        return decorator
    
    def edge(
        self,
        from_node: Union[str, Callable],
        to_node: Union[str, Callable],
        condition: Optional[Callable] = None
    ) -> Callable:
        """Decorator to define edges between nodes."""
        def decorator(func: Callable) -> Callable:
            # Resolve node names
            from_name = from_node if isinstance(from_node, str) else from_node.__name__
            to_name = to_node if isinstance(to_node, str) else to_node.__name__
            
            # Find node IDs
            from_id = None
            to_id = None
            
            for node_id, node in self.graph.nodes.items():
                if node.name == from_name:
                    from_id = node_id
                if node.name == to_name:
                    to_id = node_id
            
            if from_id and to_id:
                self.graph.add_edge(
                    from_id,
                    to_id,
                    condition=condition or func
                )
            
            return func
        
        return decorator
    
    def parallel(self, *nodes: Union[str, Callable]) -> Callable:
        """Decorator to mark nodes for parallel execution."""
        def decorator(func: Callable) -> Callable:
            # This would be implemented with parallel execution logic
            # For now, it's a marker
            func._parallel_nodes = nodes
            return func
        
        return decorator
    
    async def run(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        resume_from: Optional[str] = None
    ) -> Any:
        """Run the workflow."""
        # Initialize state
        self.state_manager = StateManager(
            self.state_class,
            initial_state=initial_state
        )
        
        # Set up context
        workflow_context = {
            'workflow': self,
            'results': self.results,
            **(context or {})
        }
        
        # Handle resume
        if resume_from and self.checkpointed:
            self.state_manager.restore_checkpoint(resume_from)
        
        # Execute graph
        try:
            final_state, path = await self.graph.execute(
                self.state_manager,
                workflow_context
            )
            
            # Record success
            self.results.append(StepResult(
                step_name="workflow_complete",
                status=StepStatus.COMPLETED,
                result=final_state.current if hasattr(final_state, 'current') else final_state,
                completed_at=datetime.now()
            ))
            
            return final_state
            
        except Exception as e:
            # Record failure
            self.results.append(StepResult(
                step_name="workflow_error",
                status=StepStatus.FAILED,
                error=str(e),
                completed_at=datetime.now()
            ))
            raise
    
    def checkpoint(self, name: Optional[str] = None) -> Callable:
        """Decorator to mark checkpointing points."""
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                
                # Create checkpoint if enabled
                if self.checkpointed and self.state_manager:
                    checkpoint_name = name or f"{func.__name__}_checkpoint"
                    self.state_manager.checkpoint(checkpoint_name)
                
                return result
            
            return wrapper
        
        return decorator
    
    async def run_step(
        self,
        step_name: str,
        state: Any,
        context: Dict[str, Any]
    ) -> StepResult:
        """Run a single step with error handling and retries."""
        step_node = self.steps.get(step_name)
        if not step_node:
            return StepResult(
                step_name=step_name,
                status=StepStatus.FAILED,
                error=f"Step {step_name} not found"
            )
        
        result = StepResult(
            step_name=step_name,
            status=StepStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Execute step
                step_result = await step_node.execute(state, context)
                
                result.status = StepStatus.COMPLETED
                result.result = step_result
                result.completed_at = datetime.now()
                
                break
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                result.status = StepStatus.FAILED
                result.error = str(e)
                result.completed_at = datetime.now()
        
        self.results.append(result)
        return result


# Decorator for creating workflows
def stateful_workflow(
    name: Optional[str] = None,
    checkpointed: bool = False,
    max_retries: int = 3
) -> Callable:
    """
    Decorator to create a stateful workflow class.
    
    Example:
        @stateful_workflow(checkpointed=True)
        class ResearchWorkflow:
            class State:
                query: str
                results: List[str] = []
                
            @node
            async def search(self, state):
                # Implementation
                
            @edge("search", "analyze")
            def should_analyze(self, state):
                return len(state.results) > 0
    """
    def decorator(cls):
        # Extract state class
        state_class = getattr(cls, 'State', dict)
        
        # Create workflow instance
        workflow = StatefulWorkflow(
            name=name or cls.__name__,
            state_class=state_class,
            checkpointed=checkpointed,
            max_retries=max_retries
        )
        
        # Bind methods to workflow
        for attr_name, attr_value in inspect.getmembers(cls):
            if hasattr(attr_value, '__workflow_node__'):
                # This is a node
                workflow.node(attr_name)(attr_value)
            elif hasattr(attr_value, '__workflow_edge__'):
                # This is an edge
                edge_info = attr_value.__workflow_edge__
                workflow.edge(
                    edge_info['from'],
                    edge_info['to'],
                    edge_info.get('condition')
                )(attr_value)
        
        # Add run method to class
        cls.run = workflow.run
        cls.workflow = workflow
        
        return cls
    
    return decorator
```

### `/agenticraft/orchestration/checkpoint.py`

```python
"""Checkpointing and persistence for workflows."""

import json
import pickle
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path
import aiofiles
from abc import ABC, abstractmethod

from .state import StateSnapshot


class CheckpointStorage(ABC):
    """Abstract base for checkpoint storage."""
    
    @abstractmethod
    async def save(self, workflow_id: str, checkpoint: StateSnapshot) -> str:
        """Save checkpoint and return checkpoint ID."""
        pass
    
    @abstractmethod
    async def load(self, checkpoint_id: str) -> StateSnapshot:
        """Load checkpoint by ID."""
        pass
    
    @abstractmethod
    async def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """List checkpoints for a workflow."""
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        pass


class FileCheckpointStorage(CheckpointStorage):
    """File-based checkpoint storage."""
    
    def __init__(self, base_path: str = "./checkpoints"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save(self, workflow_id: str, checkpoint: StateSnapshot) -> str:
        """Save checkpoint to file."""
        # Create workflow directory
        workflow_dir = self.base_path / workflow_id
        workflow_dir.mkdir(exist_ok=True)
        
        # Generate checkpoint ID
        checkpoint_id = f"{workflow_id}_{checkpoint.timestamp.timestamp()}"
        
        # Save as JSON
        checkpoint_data = {
            'id': checkpoint_id,
            'workflow_id': workflow_id,
            'timestamp': checkpoint.timestamp.isoformat(),
            'step': checkpoint.step,
            'data': checkpoint.data,
            'metadata': checkpoint.metadata
        }
        
        checkpoint_file = workflow_dir / f"{checkpoint_id}.json"
        
        async with aiofiles.open(checkpoint_file, 'w') as f:
            await f.write(json.dumps(checkpoint_data, indent=2, default=str))
        
        return checkpoint_id
    
    async def load(self, checkpoint_id: str) -> StateSnapshot:
        """Load checkpoint from file."""
        # Find checkpoint file
        for workflow_dir in self.base_path.iterdir():
            checkpoint_file = workflow_dir / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                async with aiofiles.open(checkpoint_file, 'r') as f:
                    data = json.loads(await f.read())
                
                return StateSnapshot(
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    data=data['data'],
                    step=data.get('step'),
                    metadata=data.get('metadata', {})
                )
        
        raise ValueError(f"Checkpoint {checkpoint_id} not found")
    
    async def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """List checkpoints for a workflow."""
        workflow_dir = self.base_path / workflow_id
        
        if not workflow_dir.exists():
            return []
        
        checkpoints = []
        
        for checkpoint_file in workflow_dir.glob("*.json"):
            async with aiofiles.open(checkpoint_file, 'r') as f:
                data = json.loads(await f.read())
                checkpoints.append({
                    'id': data['id'],
                    'timestamp': data['timestamp'],
                    'step': data.get('step'),
                    'metadata': data.get('metadata', {})
                })
        
        # Sort by timestamp
        checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return checkpoints
    
    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        for workflow_dir in self.base_path.iterdir():
            checkpoint_file = workflow_dir / f"{checkpoint_id}.json"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                return True
        
        return False


class CheckpointManager:
    """Manager for workflow checkpointing."""
    
    def __init__(self, storage: Optional[CheckpointStorage] = None):
        self.storage = storage or FileCheckpointStorage()
        self._auto_checkpoint_interval = 5  # Steps between auto checkpoints
        self._step_counter = 0
    
    async def create_checkpoint(
        self,
        workflow_id: str,
        state: Any,
        step: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a checkpoint."""
        # Convert state to dict
        if hasattr(state, 'to_dict'):
            state_dict = state.to_dict()
        elif hasattr(state, '__dict__'):
            state_dict = vars(state).copy()
        else:
            state_dict = {'value': state}
        
        # Create snapshot
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            data=state_dict,
            step=step,
            metadata=metadata or {}
        )
        
        # Save to storage
        return await self.storage.save(workflow_id, snapshot)
    
    async def restore_checkpoint(self, checkpoint_id: str) -> StateSnapshot:
        """Restore from checkpoint."""
        return await self.storage.load(checkpoint_id)
    
    async def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """List available checkpoints."""
        return await self.storage.list_checkpoints(workflow_id)
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        return await self.storage.delete(checkpoint_id)
    
    def should_auto_checkpoint(self) -> bool:
        """Check if auto checkpoint should be created."""
        self._step_counter += 1
        if self._step_counter >= self._auto_checkpoint_interval:
            self._step_counter = 0
            return True
        return False
    
    async def auto_checkpoint(
        self,
        workflow_id: str,
        state: Any,
        step: str
    ) -> Optional[str]:
        """Create auto checkpoint if needed."""
        if self.should_auto_checkpoint():
            return await self.create_checkpoint(
                workflow_id,
                state,
                step=f"auto_{step}",
                metadata={'auto': True}
            )
        return None


# Global checkpoint manager
_checkpoint_manager = CheckpointManager()


def get_checkpoint_manager() -> CheckpointManager:
    """Get global checkpoint manager."""
    return _checkpoint_manager
```

## 5. Configuration System

### `/agenticraft/config/agenticraft.yaml`

```yaml
# AgentiCraft Configuration
# This file configures all protocols, servers, and agent defaults

# Protocol Configuration
protocols:
  # A2A Protocol (Google)
  a2a:
    enabled: true
    registry_url: https://a2a-registry.example.com
    auth:
      type: oauth2
      client_id: ${A2A_CLIENT_ID}
      client_secret: ${A2A_CLIENT_SECRET}
  
  # MCP Protocol (Anthropic)
  mcp:
    enabled: true
    servers:
      # Built-in MCP servers
      brave_search:
        command: npx
        args: ["-y", "@modelcontextprotocol/server-brave-search"]
        env:
          BRAVE_API_KEY: ${BRAVE_API_KEY}
      
      github:
        command: npx
        args: ["-y", "@modelcontextprotocol/server-github"]
        env:
          GITHUB_TOKEN: ${GITHUB_TOKEN}
      
      filesystem:
        command: npx
        args: ["-y", "@modelcontextprotocol/server-filesystem", "--allow-write"]
        
      # Custom HTTP MCP server
      internal_api:
        transport: http
        url: ${INTERNAL_API_URL}/mcp
        headers:
          Authorization: Bearer ${INTERNAL_API_TOKEN}
      
      # WebSocket MCP server
      realtime_data:
        transport: websocket
        url: wss://data.example.com/mcp
        reconnect: true
        
  # ANP Protocol (Decentralized)
  anp:
    enabled: true
    network: mainnet  # or testnet
    did_resolver: https://did-resolver.example.com
    
  # AgentiCraft Mesh Network
  mesh:
    enabled: true
    node_id: ${MESH_NODE_ID:-agenticraft-node}
    max_connections: 10
    discovery_interval: 30
    consensus:
      enabled: false
      algorithm: pbft  # or raft, or custom
      min_nodes: 3

# Model Configuration
models:
  default: gpt-4
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      organization: ${OPENAI_ORG}
      base_url: https://api.openai.com/v1
      
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
      base_url: https://api.anthropic.com
      
    ollama:
      base_url: ${OLLAMA_URL:-http://localhost:11434}
      models:
        - llama2
        - mistral
        - codellama

# Agent Defaults
agents:
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  max_retries: 3
  
  # Reasoning configuration
  reasoning:
    pattern: transparent  # transparent, chain-of-thought, tree-of-thought
    max_depth: 5
    
  # Memory configuration
  memory:
    provider: chromadb  # or qdrant, weaviate, pinecone
    max_items: 100
    embedding_model: text-embedding-ada-002

# Tool Configuration
tools:
  # Local tool directories
  directories:
    - ./tools
    - ./custom_tools
    
  # Tool discovery
  discovery:
    mcp_priority: true  # Prioritize MCP tools
    scan_interval: 300  # Seconds
    
  # Tool security
  security:
    sandbox: true
    allowed_domains:
      - "*.example.com"
      - "api.github.com"

# Workflow Configuration
workflows:
  checkpointing:
    enabled: true
    storage: file  # or redis, mongodb
    storage_path: ./checkpoints
    auto_checkpoint_interval: 5
    
  parallel_execution:
    max_workers: 10
    timeout: 300
    
  visualization:
    enabled: true
    format: mermaid  # or graphviz

# Security Configuration
security:
  sandbox:
    enabled: false  # Enable with caution
    type: docker  # or process, wasm
    resource_limits:
      memory_mb: 512
      cpu_percent: 50
      timeout_seconds: 30
      
  api_keys:
    encryption: true
    key_file: ${KEY_FILE:-~/.agenticraft/keys}

# Telemetry Configuration
telemetry:
  enabled: true
  anonymous: true
  metrics:
    - execution_time
    - token_usage
    - error_rate
  
  export:
    provider: otlp  # or prometheus, datadog
    endpoint: ${TELEMETRY_ENDPOINT}

# Development Configuration
development:
  debug: ${DEBUG:-false}
  log_level: ${LOG_LEVEL:-INFO}
  hot_reload: true
  
  # Testing
  test_mode: ${TEST_MODE:-false}
  mock_llm: ${MOCK_LLM:-false}
```

## Usage Examples

### Example 1: Simple Agent with SDK Tools

```python
from agenticraft import agent

@agent("researcher", servers=["brave_search", "arxiv"])
async def research_agent(self, topic: str):
    """Research any topic using MCP tools."""
    
    # Tools are automatically available through SDK
    search_results = await self.tools.brave_search(query=topic, count=5)
    academic_papers = await self.tools.arxiv.search(query=topic, max_results=3)
    
    # Use agent's LLM capabilities
    synthesis = await self.synthesize(search_results, academic_papers)
    
    return synthesis

# Usage
researcher = research_agent()
result = await researcher("quantum computing applications")
print(result)
```

### Example 2: Complex Workflow with State

```python
from agenticraft import stateful_workflow
from dataclasses import dataclass
from typing import List, Dict

@stateful_workflow(checkpointed=True)
class DataAnalysisWorkflow:
    """Complex data analysis with state management."""
    
    @dataclass
    class State:
        data_source: str
        raw_data: List[Dict] = None
        cleaned_data: List[Dict] = None
        analysis_results: Dict = None
        confidence_score: float = 0.0
        errors: List[str] = None
    
    @node
    async def fetch_data(self, state: State):
        """Fetch data from source."""
        # Use MCP file system tool
        data = await self.tools.filesystem.read(state.data_source)
        state.raw_data = json.loads(data)
        return state
    
    @node
    async def clean_data(self, state: State):
        """Clean and validate data."""
        # Data cleaning logic
        state.cleaned_data = [
            record for record in state.raw_data 
            if self.validate_record(record)
        ]
        state.confidence_score = len(state.cleaned_data) / len(state.raw_data)
        return state
    
    @node
    async def analyze(self, state: State):
        """Perform analysis."""
        # Use agent for analysis
        analysis = await self.agent.analyze(state.cleaned_data)
        state.analysis_results = analysis
        return state
    
    @edge("fetch_data", "clean_data")
    def data_fetched(self, state: State) -> bool:
        """Check if data was fetched successfully."""
        return state.raw_data is not None and len(state.raw_data) > 0
    
    @edge("clean_data", "analyze")
    def data_quality_ok(self, state: State) -> bool:
        """Check if data quality is sufficient."""
        return state.confidence_score > 0.7
    
    @edge("clean_data", "fetch_data")
    def retry_fetch(self, state: State) -> bool:
        """Retry if data quality is poor."""
        return state.confidence_score <= 0.7
    
    @checkpoint
    async def save_results(self, state: State):
        """Save analysis results."""
        await self.tools.filesystem.write(
            f"analysis_{datetime.now().isoformat()}.json",
            json.dumps(state.analysis_results)
        )

# Usage
workflow = DataAnalysisWorkflow()
result = await workflow.run(
    initial_state={'data_source': 'sales_data.json'}
)
```

### Example 3: Multi-Protocol Agent System

```python
from agenticraft.fabric import UnifiedProtocolFabric
from agenticraft import agent, parallel, chain

# Initialize fabric
fabric = UnifiedProtocolFabric()
await fabric.initialize()

# Create specialized agents
@agent("web_researcher", servers=["brave_search", "scrapler"])
async def web_researcher(self, query: str):
    """Research using web sources."""
    results = await self.tools.brave_search(query)
    return await self.analyze(results)

@agent("data_analyst", servers=["jupyter", "pandas"])
async def data_analyst(self, data: str):
    """Analyze data using computational tools."""
    return await self.tools.jupyter.execute(f"analyze({data})")

@agent("writer", model="claude-3-opus")
async def writer(self, content: str):
    """Write polished content."""
    return await self.run(f"Polish and improve: {content}")

# Register agents with fabric
await fabric.register_agent(web_researcher(), protocols=['mcp', 'mesh'])
await fabric.register_agent(data_analyst(), protocols=['mcp', 'a2a'])
await fabric.register_agent(writer(), protocols=['a2a', 'mesh'])

# Create complex workflow
@chain([web_researcher, data_analyst, writer])
async def research_pipeline(topic: str):
    """Complete research pipeline."""
    pass

# Execute with consensus
result = await fabric.execute(
    "Impact of AI on employment",
    capability="research",
    consensus_required=True,
    timeout=60.0
)

print(f"Consensus result: {result}")
```

### Example 4: Parallel Analysis with Consensus

```python
from agenticraft import agent, parallel

# Create multiple analyst agents
@agent("analyst_1", model="gpt-4")
async def analyst_1(self, data: str):
    """First analyst perspective."""
    return await self.analyze(data)

@agent("analyst_2", model="claude-3-opus")
async def analyst_2(self, data: str):
    """Second analyst perspective."""
    return await self.analyze(data)

@agent("analyst_3", model="llama2", servers=["local_tools"])
async def analyst_3(self, data: str):
    """Third analyst perspective with local tools."""
    enhanced_data = await self.tools.enhance_data(data)
    return await self.analyze(enhanced_data)

# Parallel execution with consensus
@parallel(
    [analyst_1, analyst_2, analyst_3],
    merge_strategy="consensus"
)
async def multi_perspective_analysis(data: str):
    """Analyze from multiple perspectives."""
    pass

# Usage
result = await multi_perspective_analysis("Q3 Financial Report")
print(f"Consensus analysis: {result}")
```

## Migration Guide

### From Current AgentiCraft

```python
# Before: Current AgentiCraft
from agenticraft import Agent
from agenticraft.tools import tool

@tool
def search(query: str) -> str:
    return f"Searching for {query}"

agent = Agent(
    name="researcher",
    tools=[search]
)

# After: With SDK Integration
from agenticraft import agent

@agent("researcher", servers=["brave_search"])
async def researcher(self, query: str):
    results = await self.tools.brave_search(query)
    return results

# Tools come from MCP servers - no local tool needed
```

### From LangChain

```python
# Before: LangChain
from langchain.agents import create_openai_agent
from langchain.tools import BraveSearchTool

agent = create_openai_agent(
    tools=[BraveSearchTool()],
    # Complex chain setup...
)

# After: AgentiCraft
from agenticraft import agent

@agent("researcher", servers=["brave_search"])
async def researcher(self, query: str):
    return await self.tools.brave_search(query)

# Much simpler!
```

## Benefits Summary

1. **SDK Integration** ✅
   - Full compliance with A2A, MCP, ANP standards
   - Access to entire tool ecosystem
   - Automatic updates with protocol changes

2. **Simplified Tools** ✅
   - Minimal tool abstraction
   - SDK tools take priority
   - Local tools only when needed

3. **Clean Decorators** ✅
   - Fast-agent inspired simplicity
   - Natural tool access
   - Powerful workflow patterns

4. **LangGraph Patterns** ✅
   - Without the complexity
   - State management built-in
   - Visual workflow design

5. **Unique Features Preserved** ✅
   - Mesh networking
   - Consensus mechanisms
   - Reasoning transparency

This implementation provides the best of all worlds: ecosystem compatibility, developer simplicity, and AgentiCraft's unique innovations!