"""
AgentiCraft Fabric - Unified Protocol Abstraction Layer.

This module provides a unified interface for working with multiple
protocols, allowing seamless integration and protocol switching.
"""

# Import unified agent interface
from .agent import UnifiedAgent, create_mcp_agent, create_a2a_agent

# Import protocol types
from .protocol_types import (
    ProtocolType,
    ProtocolCapability,
    UnifiedTool,
    IProtocolAdapter
)

# Import legacy fabric for backwards compatibility
from .legacy import (
    UnifiedProtocolFabric,
    EnhancedUnifiedProtocolFabric,
    UnifiedToolWrapper,
    get_global_fabric,
    initialize_fabric
)

# Import protocol adapters
from .protocol_adapters import (
    MCPAdapter,
    A2AAdapter,
    ACPAdapter,
    ANPAdapter
)

# Import adapters
try:
    from .adapters import (
        SDKPreference,
        AdapterFactory,
        MCPOfficialAdapter,
        A2AOfficialAdapter,
        ACPBeeAdapter,
        AdapterRegistry
    )
except ImportError:
    # Adapters module might not exist yet
    SDKPreference = None
    AdapterFactory = None
    MCPOfficialAdapter = None
    A2AOfficialAdapter = None
    ACPBeeAdapter = None
    AdapterRegistry = None

# Import builder pattern
from .builder import AgentBuilder

# Import configuration
from .config import FabricConfig

__all__ = [
    # Agent interface
    "UnifiedAgent",
    "create_mcp_agent",
    "create_a2a_agent",
    
    # Protocol types
    "ProtocolType",
    "ProtocolCapability",
    "UnifiedTool",
    "IProtocolAdapter",
    
    # Legacy fabric (backwards compatibility)
    "UnifiedProtocolFabric",
    "EnhancedUnifiedProtocolFabric",
    "UnifiedToolWrapper",
    "get_global_fabric",
    "initialize_fabric",
    
    # Protocol adapters
    "MCPAdapter",
    "A2AAdapter",
    "ACPAdapter",
    "ANPAdapter",
    
    # SDK Adapters
    "SDKPreference",
    "AdapterFactory",
    "MCPOfficialAdapter",
    "A2AOfficialAdapter",
    "ACPBeeAdapter",
    "AdapterRegistry",
    
    # Builder
    "AgentBuilder",
    
    # Configuration
    "FabricConfig"
]
