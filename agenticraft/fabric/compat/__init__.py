"""
Backwards compatibility layer for refactored AgentiCraft.

This module provides compatibility imports and wrappers
to help migrate from the old structure to the new one.
"""
import warnings
from typing import Any

def _deprecated(old_path: str, new_path: str):
    """Show deprecation warning."""
    warnings.warn(
        f"Import from '{old_path}' is deprecated. Use '{new_path}' instead.",
        DeprecationWarning,
        stacklevel=3
    )


# Old import mappings

# protocols.mcp.transport -> core.transport
class _MCPTransportCompat:
    def __getattr__(self, name: str) -> Any:
        _deprecated(
            "agenticraft.protocols.mcp.transport",
            "agenticraft.core.transport"
        )
        from ...core import transport
        return getattr(transport, name)

mcp_transport = _MCPTransportCompat()


# protocols.mcp.auth -> core.auth
class _MCPAuthCompat:
    def __getattr__(self, name: str) -> Any:
        _deprecated(
            "agenticraft.protocols.mcp.auth",
            "agenticraft.core.auth"
        )
        from ...core import auth
        return getattr(auth, name)

mcp_auth = _MCPAuthCompat()


# fabric.unified -> fabric.legacy
class UnifiedProtocolFabric:
    """Compatibility wrapper for old UnifiedProtocolFabric class."""
    
    def __new__(cls, *args, **kwargs):
        _deprecated(
            "agenticraft.fabric.unified.UnifiedProtocolFabric",
            "agenticraft.fabric.agent.UnifiedAgent"
        )
        from ..legacy import UnifiedProtocolFabric as LegacyFabric
        return LegacyFabric(*args, **kwargs)


# fabric.unified_enhanced -> fabric.legacy  
class EnhancedUnifiedProtocolFabric:
    """Compatibility wrapper for old EnhancedUnifiedProtocolFabric class."""
    
    def __new__(cls, *args, **kwargs):
        _deprecated(
            "agenticraft.fabric.unified_enhanced.EnhancedUnifiedProtocolFabric",
            "agenticraft.fabric.agent.UnifiedAgent"
        )
        from ..legacy import EnhancedUnifiedProtocolFabric as LegacyFabric
        return LegacyFabric(*args, **kwargs)


# Unified protocol types (now in protocol_types.py)
class _ProtocolTypesCompat:
    def __getattr__(self, name: str) -> Any:
        _deprecated(
            f"agenticraft.fabric.unified.{name}",
            f"agenticraft.fabric.protocol_types.{name}"
        )
        from ..protocol_types import (
            ProtocolType, ProtocolCapability, UnifiedTool, IProtocolAdapter
        )
        
        if name == "ProtocolType":
            return ProtocolType
        elif name == "ProtocolCapability":
            return ProtocolCapability
        elif name == "UnifiedTool":
            return UnifiedTool
        elif name == "IProtocolAdapter":
            return IProtocolAdapter
        else:
            raise AttributeError(f"No attribute {name}")

_protocol_types_compat = _ProtocolTypesCompat()


# Adapter classes (now in protocol_adapters.py)
class _AdaptersCompat:
    def __getattr__(self, name: str) -> Any:
        _deprecated(
            f"agenticraft.fabric.unified.{name}",
            f"agenticraft.fabric.protocol_adapters.{name}"
        )
        from ..protocol_adapters import (
            MCPAdapter, A2AAdapter, ACPAdapter, ANPAdapter
        )
        
        if name == "MCPAdapter":
            return MCPAdapter
        elif name == "A2AAdapter":
            return A2AAdapter
        elif name == "ACPAdapter":
            return ACPAdapter
        elif name == "ANPAdapter":
            return ANPAdapter
        else:
            raise AttributeError(f"No adapter {name}")

_adapters_compat = _AdaptersCompat()


# Legacy functions
def get_global_fabric():
    """Compatibility function for get_global_fabric."""
    _deprecated(
        "agenticraft.fabric.unified.get_global_fabric",
        "agenticraft.fabric.agent.UnifiedAgent"
    )
    from ..legacy import get_global_fabric as legacy_func
    return legacy_func()


def initialize_fabric(config):
    """Compatibility function for initialize_fabric."""
    _deprecated(
        "agenticraft.fabric.unified.initialize_fabric",
        "agenticraft.fabric.agent.create_mcp_agent or create_a2a_agent"
    )
    from ..legacy import initialize_fabric as legacy_func
    return legacy_func(config)


# fabric.sdk_fabric -> fabric.agent + builder
def create_sdk_agent(*args, **kwargs):
    """Compatibility function for SDK agent creation."""
    _deprecated(
        "agenticraft.fabric.sdk_fabric.create_sdk_agent",
        "agenticraft.fabric.builder.AgentBuilder"
    )
    from ..builder import AgentBuilder
    
    # Extract name from args/kwargs
    name = args[0] if args else kwargs.get("name", "agent")
    
    builder = AgentBuilder(name)
    
    # Add protocols based on kwargs
    if "mcp_url" in kwargs:
        builder.with_mcp(kwargs["mcp_url"])
        
    if "a2a_config" in kwargs:
        a2a_config = kwargs["a2a_config"]
        builder.with_a2a(
            pattern=a2a_config.get("pattern", "mesh"),
            peers=a2a_config.get("peers")
        )
        
    return builder.build()


# Old adapter imports
class _AdapterFactoryCompat:
    def create_adapter(self, protocol_name: str, *args, **kwargs):
        _deprecated(
            "agenticraft.fabric.adapters.adapter_factory.create_adapter",
            "agenticraft.fabric.adapters.create_adapter"
        )
        from ..adapters import create_adapter
        return create_adapter(protocol_name, *args, **kwargs)

adapter_factory = _AdapterFactoryCompat()


# Protocol registry compatibility
class _ProtocolRegistryCompat:
    def __getattr__(self, name: str) -> Any:
        if name == "registry":
            _deprecated(
                "agenticraft.protocols.a2a.registry.registry",
                "agenticraft.protocols.a2a.registry.ProtocolRegistry"
            )
            from ...protocols.a2a.registry import ProtocolRegistry
            return ProtocolRegistry()
        else:
            from ...protocols.a2a import registry
            return getattr(registry, name)

a2a_registry_compat = _ProtocolRegistryCompat()


# MCP types compatibility
def get_mcp_types():
    """Get MCP types with deprecation warning."""
    _deprecated(
        "agenticraft.protocols.mcp.types",
        "agenticraft.protocols.mcp"
    )
    from ...protocols import mcp
    return mcp


# Export commonly used old names
__all__ = [
    "UnifiedFabric",
    "EnhancedUnifiedFabric",
    "create_sdk_agent",
    "adapter_factory",
    "mcp_transport",
    "mcp_auth",
    "a2a_registry_compat",
    "get_mcp_types"
]
