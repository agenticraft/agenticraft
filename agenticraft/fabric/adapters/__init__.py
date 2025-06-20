"""
Protocol adapters for AgentiCraft fabric.

This module provides adapters that allow protocols to work
seamlessly within the unified fabric layer.
"""

from .base import ProtocolAdapter
from .mcp_adapter import MCPAdapter
from .a2a_adapter import A2AAdapter
from .registry import AdapterRegistry, get_adapter_registry
from .adapter_factory import AdapterFactory, SDKPreference

# Import official SDK adapters if available
try:
    from .mcp_official import MCPOfficialAdapter
except ImportError:
    MCPOfficialAdapter = None

try:
    from .a2a_official import A2AOfficialAdapter
except ImportError:
    A2AOfficialAdapter = None

try:
    from .acp_bee import ACPBeeAdapter
except ImportError:
    ACPBeeAdapter = None

__all__ = [
    "ProtocolAdapter",
    "MCPAdapter",
    "A2AAdapter",
    "AdapterRegistry",
    "get_adapter_registry",
    "AdapterFactory",
    "SDKPreference",
    "MCPOfficialAdapter",
    "A2AOfficialAdapter",
    "ACPBeeAdapter"
]
