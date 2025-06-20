"""
Adapter registry for AgentiCraft fabric.

This module provides a registry for protocol adapters.
"""
import logging
from typing import Dict, Type, Optional, List, Any

from .base import ProtocolAdapter
from .mcp_adapter import MCPAdapter
from .a2a_adapter import A2AAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Registry for protocol adapters.
    
    This registry manages adapter classes and provides
    factory methods for creating adapter instances.
    """
    
    def __init__(self):
        """Initialize adapter registry."""
        self._adapters: Dict[str, Type[ProtocolAdapter]] = {}
        
        # Register built-in adapters
        self._register_builtin_adapters()
        
    def _register_builtin_adapters(self) -> None:
        """Register built-in adapter types."""
        self.register("mcp", MCPAdapter)
        self.register("a2a", A2AAdapter)
        
    def register(
        self,
        protocol_name: str,
        adapter_class: Type[ProtocolAdapter]
    ) -> None:
        """
        Register an adapter class.
        
        Args:
            protocol_name: Protocol name
            adapter_class: Adapter class
        """
        if not issubclass(adapter_class, ProtocolAdapter):
            raise TypeError(
                f"{adapter_class} must be a subclass of ProtocolAdapter"
            )
            
        self._adapters[protocol_name] = adapter_class
        logger.info(f"Registered adapter for protocol: {protocol_name}")
        
    def unregister(self, protocol_name: str) -> None:
        """
        Unregister an adapter.
        
        Args:
            protocol_name: Protocol name
        """
        if protocol_name in self._adapters:
            del self._adapters[protocol_name]
            logger.info(f"Unregistered adapter for protocol: {protocol_name}")
            
    def get_adapter_class(
        self,
        protocol_name: str
    ) -> Optional[Type[ProtocolAdapter]]:
        """
        Get adapter class for protocol.
        
        Args:
            protocol_name: Protocol name
            
        Returns:
            Adapter class or None
        """
        return self._adapters.get(protocol_name)
        
    def create_adapter(
        self,
        protocol_name: str,
        protocol: Any,
        transport: Any,
        auth: Optional[Any] = None
    ) -> ProtocolAdapter:
        """
        Create adapter instance.
        
        Args:
            protocol_name: Protocol name
            protocol: Protocol instance
            transport: Transport instance
            auth: Optional auth manager
            
        Returns:
            Adapter instance
        """
        adapter_class = self.get_adapter_class(protocol_name)
        if not adapter_class:
            # Fall back to generic adapter
            logger.warning(
                f"No specific adapter for {protocol_name}, "
                "using generic adapter"
            )
            adapter_class = ProtocolAdapter
            
        return adapter_class(protocol, transport, auth)
        
    def list_adapters(self) -> List[str]:
        """
        List registered adapter names.
        
        Returns:
            List of protocol names with adapters
        """
        return list(self._adapters.keys())
        
    def get_adapter_info(
        self,
        protocol_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about an adapter.
        
        Args:
            protocol_name: Protocol name
            
        Returns:
            Adapter information or None
        """
        adapter_class = self.get_adapter_class(protocol_name)
        if not adapter_class:
            return None
            
        return {
            "protocol": protocol_name,
            "adapter_class": adapter_class.__name__,
            "module": adapter_class.__module__,
            "docstring": adapter_class.__doc__
        }
        
    def clear(self) -> None:
        """Clear all registered adapters."""
        self._adapters.clear()
        
        # Re-register built-in adapters
        self._register_builtin_adapters()


# Global registry instance
_adapter_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    """Get global adapter registry."""
    return _adapter_registry


# Convenience functions

def register_adapter(
    protocol_name: str,
    adapter_class: Type[ProtocolAdapter]
) -> None:
    """Register an adapter globally."""
    get_adapter_registry().register(protocol_name, adapter_class)


def create_adapter(
    protocol_name: str,
    protocol: Any,
    transport: Any,
    auth: Optional[Any] = None
) -> ProtocolAdapter:
    """Create an adapter using global registry."""
    return get_adapter_registry().create_adapter(
        protocol_name,
        protocol,
        transport,
        auth
    )


def list_adapters() -> List[str]:
    """List globally registered adapters."""
    return get_adapter_registry().list_adapters()
