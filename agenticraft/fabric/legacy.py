"""
Legacy unified protocol fabric implementations.

This module contains the old UnifiedProtocolFabric and EnhancedUnifiedProtocolFabric
classes for backwards compatibility. These are deprecated and will be removed
in a future version.

Please use the new UnifiedAgent from fabric.agent instead.
"""
import asyncio
import logging
import warnings
from typing import Any, Dict, List, Optional, Type, Union

from agenticraft.core import Agent, BaseTool
from agenticraft.core.exceptions import AgentError, ToolError

from .protocol_types import (
    ProtocolType,
    ProtocolCapability,
    UnifiedTool,
    IProtocolAdapter
)
from .protocol_adapters import (
    MCPAdapter,
    A2AAdapter,
    ACPAdapter,
    ANPAdapter
)

logger = logging.getLogger(__name__)


def _deprecation_warning(old_class: str, new_class: str = "UnifiedAgent"):
    """Show deprecation warning for legacy classes."""
    warnings.warn(
        f"{old_class} is deprecated and will be removed in a future version. "
        f"Please use {new_class} from agenticraft.fabric.agent instead.",
        DeprecationWarning,
        stacklevel=3
    )


class UnifiedProtocolFabric:
    """
    DEPRECATED: Legacy unified protocol fabric.
    
    This class is maintained for backwards compatibility only.
    Please use UnifiedAgent from fabric.agent instead.
    """
    
    def __init__(self, sdk_preferences: Optional[Dict[str, Union[str, Any]]] = None):
        _deprecation_warning("UnifiedProtocolFabric")
        
        self.adapters: Dict[ProtocolType, IProtocolAdapter] = {}
        self.unified_tools: Dict[str, UnifiedTool] = {}
        self.capabilities: Dict[ProtocolType, List[ProtocolCapability]] = {}
        self._initialized = False
        
        # SDK preferences (for compatibility)
        self.sdk_preferences: Dict[ProtocolType, Any] = self._parse_sdk_preferences(sdk_preferences or {})
        
        # Register default adapters
        self._register_default_adapters()
    
    def _parse_sdk_preferences(self, preferences: Dict[str, Union[str, Any]]) -> Dict[ProtocolType, Any]:
        """Parse SDK preferences from config."""
        parsed = {}
        
        # Try to import SDKPreference
        try:
            from .adapters import SDKPreference
        except ImportError:
            # If adapters module doesn't exist, use string values
            class SDKPreference:
                OFFICIAL = "official"
                HYBRID = "hybrid"
                CUSTOM = "custom"
                AUTO = "auto"
        
        # Default to AUTO for all protocols
        for protocol in ProtocolType:
            parsed[protocol] = SDKPreference.AUTO
        
        # Parse provided preferences
        for key, value in preferences.items():
            # Convert string key to ProtocolType
            try:
                protocol = ProtocolType(key)
            except ValueError:
                continue
            
            # Convert string value to SDKPreference
            if isinstance(value, str):
                if value == "official":
                    parsed[protocol] = SDKPreference.OFFICIAL
                elif value == "hybrid":
                    parsed[protocol] = SDKPreference.HYBRID
                elif value == "custom":
                    parsed[protocol] = SDKPreference.CUSTOM
                elif value == "auto":
                    parsed[protocol] = SDKPreference.AUTO
            else:
                # Assume it's already an SDKPreference enum
                parsed[protocol] = value
        
        return parsed
    
    def update_sdk_preference(self, protocol: Union[str, ProtocolType], preference: Union[str, Any]):
        """Update SDK preference for a protocol."""
        if isinstance(protocol, str):
            protocol = ProtocolType(protocol)
        
        # Try to import SDKPreference
        try:
            from .adapters import SDKPreference
            
            if isinstance(preference, str):
                if preference == "official":
                    self.sdk_preferences[protocol] = SDKPreference.OFFICIAL
                elif preference == "hybrid":
                    self.sdk_preferences[protocol] = SDKPreference.HYBRID
                elif preference == "custom":
                    self.sdk_preferences[protocol] = SDKPreference.CUSTOM
                elif preference == "auto":
                    self.sdk_preferences[protocol] = SDKPreference.AUTO
            else:
                self.sdk_preferences[protocol] = preference
        except ImportError:
            # Store as string if adapters module doesn't exist
            self.sdk_preferences[protocol] = preference
    
    def get_sdk_info(self) -> Dict[str, Any]:
        """Get SDK information and status."""
        try:
            from .adapters import AdapterFactory
            availability = AdapterFactory.get_available_adapters()
        except ImportError:
            availability = {}
        
        preferences = {}
        for protocol, pref in self.sdk_preferences.items():
            pref_str = pref.value if hasattr(pref, 'value') else str(pref)
            preferences[protocol.value] = pref_str
        
        return {
            "preferences": preferences,
            "availability": availability,
            "recommendations": {
                "mcp": "Use official SDK when available",
                "a2a": "Custom implementation recommended",
                "acp": "Bee framework optional",
                "anp": "Custom implementation only"
            }
        }
    
    async def migrate_to_official_sdks(self, protocols: List[str], test_mode: bool = False) -> Dict[str, bool]:
        """Migrate specified protocols to official SDKs."""
        results = {}
        
        try:
            from .adapters import AdapterFactory, SDKPreference
        except ImportError:
            # Return all False if adapters module doesn't exist
            return {p: False for p in protocols}
        
        for protocol_str in protocols:
            try:
                protocol = ProtocolType(protocol_str)
                
                # Check if official SDK is available
                is_available = AdapterFactory._is_sdk_available(protocol)
                
                if is_available and not test_mode:
                    # Update preference to official
                    self.sdk_preferences[protocol] = SDKPreference.OFFICIAL
                
                results[protocol_str] = is_available
            except ValueError:
                results[protocol_str] = False
        
        return results
    
    def _register_default_adapters(self):
        """Register default protocol adapters."""
        # Use SDK preferences if available
        try:
            from .adapters import AdapterFactory
            
            for protocol in [ProtocolType.MCP, ProtocolType.A2A]:
                preference = self.sdk_preferences.get(protocol)
                if preference:
                    adapter = AdapterFactory.create_adapter(protocol, preference)
                    self.adapters[protocol] = adapter
                else:
                    # Fall back to custom adapters
                    if protocol == ProtocolType.MCP:
                        self.register_adapter(protocol, MCPAdapter)
                    elif protocol == ProtocolType.A2A:
                        self.register_adapter(protocol, A2AAdapter)
        except ImportError:
            # Fall back to original implementation
            self.register_adapter(ProtocolType.MCP, MCPAdapter)
            self.register_adapter(ProtocolType.A2A, A2AAdapter)
    
    def register_adapter(self, protocol_type: ProtocolType, adapter_class: Type[IProtocolAdapter]):
        """Register a protocol adapter."""
        if protocol_type in self.adapters:
            logger.warning(f"Overriding existing adapter for {protocol_type}")
        
        adapter = adapter_class()
        self.adapters[protocol_type] = adapter
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the unified fabric with protocol configurations."""
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
        """Get available tools, optionally filtered by protocol."""
        if protocol:
            prefix = f"{protocol.value}:"
            return [
                tool for name, tool in self.unified_tools.items()
                if name.startswith(prefix)
            ]
        return list(self.unified_tools.values())
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name."""
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
        """Create an agent with access to all unified tools."""
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


class EnhancedUnifiedProtocolFabric(UnifiedProtocolFabric):
    """
    DEPRECATED: Legacy enhanced unified protocol fabric.
    
    This class is maintained for backwards compatibility only.
    Please use UnifiedAgent from fabric.agent instead.
    """
    
    def __init__(self, sdk_preferences: Optional[Dict[str, Union[str, 'SDKPreference']]] = None):
        # Don't call super().__init__() to avoid double deprecation warning
        _deprecation_warning("EnhancedUnifiedProtocolFabric")
        
        # Initialize base components
        self.adapters: Dict[ProtocolType, IProtocolAdapter] = {}
        self.unified_tools: Dict[str, UnifiedTool] = {}
        self.capabilities: Dict[ProtocolType, List[ProtocolCapability]] = {}
        self._initialized = False
        
        # Enhanced features
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._server_tools: Dict[str, List[UnifiedTool]] = {}
        self._tool_namespaces: Dict[str, List[str]] = {}
        
        # SDK preferences
        self.sdk_preferences: Dict[ProtocolType, Any] = self._parse_sdk_preferences(sdk_preferences or {})
        
        # Extensions for AgentiCraft unique features
        self.extensions: Dict[str, IProtocolExtension] = {}
        
        # Register components
        self._register_default_adapters()
        self._register_extensions()
    
    def _parse_sdk_preferences(self, preferences: Dict[str, Union[str, Any]]) -> Dict[ProtocolType, Any]:
        """Parse SDK preferences from config."""
        parsed = {}
        
        # Try to import SDKPreference
        try:
            from .adapters import SDKPreference
        except ImportError:
            # If adapters module doesn't exist, use string values
            class SDKPreference:
                OFFICIAL = "official"
                HYBRID = "hybrid"
                CUSTOM = "custom"
                AUTO = "auto"
        
        # Default to AUTO for all protocols
        for protocol in ProtocolType:
            parsed[protocol] = SDKPreference.AUTO
        
        # Parse provided preferences
        for key, value in preferences.items():
            # Convert string key to ProtocolType
            try:
                protocol = ProtocolType(key)
            except ValueError:
                continue
            
            # Convert string value to SDKPreference
            if isinstance(value, str):
                if value == "official":
                    parsed[protocol] = SDKPreference.OFFICIAL
                elif value == "hybrid":
                    parsed[protocol] = SDKPreference.HYBRID
                elif value == "custom":
                    parsed[protocol] = SDKPreference.CUSTOM
                elif value == "auto":
                    parsed[protocol] = SDKPreference.AUTO
            else:
                # Assume it's already an SDKPreference enum
                parsed[protocol] = value
        
        return parsed
    
    def update_sdk_preference(self, protocol: Union[str, ProtocolType], preference: Union[str, Any]):
        """Update SDK preference for a protocol."""
        if isinstance(protocol, str):
            protocol = ProtocolType(protocol)
        
        # Try to import SDKPreference
        try:
            from .adapters import SDKPreference
            
            if isinstance(preference, str):
                if preference == "official":
                    self.sdk_preferences[protocol] = SDKPreference.OFFICIAL
                elif preference == "hybrid":
                    self.sdk_preferences[protocol] = SDKPreference.HYBRID
                elif preference == "custom":
                    self.sdk_preferences[protocol] = SDKPreference.CUSTOM
                elif preference == "auto":
                    self.sdk_preferences[protocol] = SDKPreference.AUTO
            else:
                self.sdk_preferences[protocol] = preference
        except ImportError:
            # Store as string if adapters module doesn't exist
            self.sdk_preferences[protocol] = preference
    
    def get_sdk_info(self) -> Dict[str, Any]:
        """Get SDK information and status."""
        try:
            from .adapters import AdapterFactory
            availability = AdapterFactory.get_available_adapters()
        except ImportError:
            availability = {}
        
        preferences = {}
        for protocol, pref in self.sdk_preferences.items():
            pref_str = pref.value if hasattr(pref, 'value') else str(pref)
            preferences[protocol.value] = pref_str
        
        return {
            "preferences": preferences,
            "availability": availability,
            "recommendations": {
                "mcp": "Use official SDK when available",
                "a2a": "Custom implementation recommended",
                "acp": "Bee framework optional",
                "anp": "Custom implementation only"
            }
        }
    
    async def migrate_to_official_sdks(self, protocols: List[str], test_mode: bool = False) -> Dict[str, bool]:
        """Migrate specified protocols to official SDKs."""
        results = {}
        
        try:
            from .adapters import AdapterFactory, SDKPreference
        except ImportError:
            # Return all False if adapters module doesn't exist
            return {p: False for p in protocols}
        
        for protocol_str in protocols:
            try:
                protocol = ProtocolType(protocol_str)
                
                # Check if official SDK is available
                is_available = AdapterFactory._is_sdk_available(protocol)
                
                if is_available and not test_mode:
                    # Update preference to official
                    self.sdk_preferences[protocol] = SDKPreference.OFFICIAL
                
                results[protocol_str] = is_available
            except ValueError:
                results[protocol_str] = False
        
        return results
    
    def _register_default_adapters(self):
        """Register all protocol adapters."""
        # Use SDK preferences if available
        try:
            from .adapters import AdapterFactory
            
            for protocol in ProtocolType:
                preference = self.sdk_preferences.get(protocol)
                if preference:
                    adapter = AdapterFactory.create_adapter(protocol, preference)
                    self.adapters[protocol] = adapter
                else:
                    # Fall back to custom adapters
                    if protocol == ProtocolType.MCP:
                        self.register_adapter(protocol, MCPAdapter)
                    elif protocol == ProtocolType.A2A:
                        self.register_adapter(protocol, A2AAdapter)
                    elif protocol == ProtocolType.ACP:
                        self.register_adapter(protocol, ACPAdapter)
                    elif protocol == ProtocolType.ANP:
                        self.register_adapter(protocol, ANPAdapter)
        except ImportError:
            # Fall back to original implementation
            self.register_adapter(ProtocolType.MCP, MCPAdapter)
            self.register_adapter(ProtocolType.A2A, A2AAdapter)
            self.register_adapter(ProtocolType.ACP, ACPAdapter)
            self.register_adapter(ProtocolType.ANP, ANPAdapter)
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the fabric with protocol configurations."""
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
        
        self._initialized = True
        logger.info(f"Enhanced Unified Protocol Fabric initialized")
    
    async def register_server(
        self,
        protocol: Union[str, ProtocolType],
        config: Union[str, Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> str:
        """Register a protocol server."""
        # Convert string protocol to enum
        if isinstance(protocol, str):
            protocol = ProtocolType(protocol)
        
        # Convert string config to dict
        if isinstance(config, str):
            config = {"url": config}
        
        # Get adapter based on SDK preference
        preference = self.sdk_preferences.get(protocol)
        
        try:
            from .adapters import AdapterFactory
            adapter = AdapterFactory.create_adapter(protocol, preference)
        except ImportError:
            # Fall back to default adapter
            adapter = self.adapters.get(protocol)
            if not adapter:
                raise ValueError(f"No adapter registered for {protocol.value}")
        
        # Generate server ID
        server_id = f"{protocol.value}_{len(self._servers)}"
        
        # Connect adapter
        await adapter.connect(config)
        
        # Store server info
        self._servers[server_id] = {
            'protocol': protocol,
            'adapter': adapter,
            'config': config,
            'namespace': namespace
        }
        
        # Discover and register tools
        tools = await adapter.discover_tools()
        self._server_tools[server_id] = tools
        
        # Update namespaces
        ns = namespace or protocol.value
        if ns not in self._tool_namespaces:
            self._tool_namespaces[ns] = []
        self._tool_namespaces[ns].append(server_id)
        
        logger.info(
            f"Registered {protocol.value} server '{server_id}' "
            f"with {len(tools)} tools"
        )
        
        return server_id
    
    def _register_extensions(self):
        """Register AgentiCraft extensions."""
        # Extensions are optional, skip if not available
        try:
            from .extensions import (
                MeshNetworkingExtension,
                ConsensusExtension,
                ReasoningTraceExtension
            )
            self.register_extension(MeshNetworkingExtension())
            self.register_extension(ConsensusExtension())
            self.register_extension(ReasoningTraceExtension())
        except ImportError:
            # Extensions not available, use stub implementations
            pass
    
    def register_extension(self, extension: Any):
        """Register a protocol extension."""
        # Extension should have a 'name' attribute
        if hasattr(extension, 'name'):
            self.extensions[extension.name] = extension
            logger.info(f"Registered extension: {extension.name}")
    
    async def enable_extension(self, name: str, **kwargs) -> Any:
        """Enable a specific extension."""
        extension = self.extensions.get(name)
        if not extension:
            raise ValueError(f"Extension not found: {name}")
        
        return await extension.apply(self, **kwargs)
    
    async def create_mesh_network(self, agents: List[str], topology: str = "dynamic") -> Any:
        """Create mesh network for agents (AgentiCraft unique)."""
        return await self.enable_extension(
            "mesh_networking",
            agents=agents,
            topology=topology
        )
    
    async def enable_consensus(self, consensus_type: str = "byzantine", min_agents: int = 3) -> Any:
        """Enable consensus mechanism (AgentiCraft unique)."""
        return await self.enable_extension(
            "consensus",
            type=consensus_type,
            min_agents=min_agents
        )
    
    async def enable_reasoning_traces(self, level: str = "detailed") -> Any:
        """Enable reasoning trace collection (AgentiCraft unique)."""
        return await self.enable_extension(
            "reasoning_traces",
            level=level
        )


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
_global_fabric: Optional[EnhancedUnifiedProtocolFabric] = None


def get_global_fabric() -> EnhancedUnifiedProtocolFabric:
    """Get the global enhanced unified protocol fabric instance."""
    _deprecation_warning("get_global_fabric", "get_global_agent")
    
    global _global_fabric
    if _global_fabric is None:
        _global_fabric = EnhancedUnifiedProtocolFabric()
    return _global_fabric


async def initialize_fabric(config: Dict[str, Any]) -> EnhancedUnifiedProtocolFabric:
    """Initialize the global fabric with configuration."""
    _deprecation_warning("initialize_fabric", "create_unified_agent")
    
    fabric = get_global_fabric()
    await fabric.initialize(config)
    return fabric
