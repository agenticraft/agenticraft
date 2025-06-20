"""
Adapter Factory for intelligent SDK selection.

Provides seamless switching between official SDKs and custom implementations.
"""

from enum import Enum
from typing import Dict, Optional, Type, Any
from agenticraft.fabric.protocol_types import IProtocolAdapter, ProtocolType

# Import custom adapters
from agenticraft.fabric.protocol_adapters import (
    MCPAdapter as MCPCustomAdapter,
    A2AAdapter as A2ACustomAdapter,
    ACPAdapter as ACPCustomAdapter,
    ANPAdapter as ANPCustomAdapter
)

# Import official SDK adapters
from .mcp_official import MCPOfficialAdapter, MCPHybridAdapter
from .a2a_official import A2AOfficialAdapter, A2AHybridAdapter
# from .acp_bee import ACPBeeAdapter, ACPEnhancedAdapter


class SDKPreference(Enum):
    """SDK selection preference."""
    OFFICIAL = "official"      # Use official SDK only
    CUSTOM = "custom"          # Use custom implementation only
    HYBRID = "hybrid"          # Use official with custom fallback
    AUTO = "auto"              # Automatically choose best option


class AdapterFactory:
    """
    Factory for creating protocol adapters with intelligent SDK selection.
    
    Features:
    - Automatic SDK availability detection
    - Fallback to custom implementations
    - Feature compatibility checking
    - Performance-based selection
    """
    
    # Adapter mappings
    ADAPTERS = {
        ProtocolType.MCP: {
            'official': MCPOfficialAdapter,
            'custom': MCPCustomAdapter,
            'hybrid': MCPHybridAdapter
        },
        ProtocolType.A2A: {
            'official': A2AOfficialAdapter,
            'custom': A2ACustomAdapter,
            'hybrid': A2AHybridAdapter
        },
        ProtocolType.ACP: {
            'official': None,  # ACPBeeAdapter - commented out for now
            'custom': ACPCustomAdapter,
            'hybrid': ACPCustomAdapter  # Falls back to custom
        },
        ProtocolType.ANP: {
            'official': None,  # No official SDK yet
            'custom': ANPCustomAdapter,
            'hybrid': ANPCustomAdapter  # Falls back to custom
        }
    }
    
    # SDK availability cache
    _sdk_availability: Dict[ProtocolType, bool] = {}
    
    @classmethod
    def create_adapter(
        cls,
        protocol: ProtocolType,
        preference: SDKPreference = SDKPreference.AUTO,
        **kwargs
    ) -> IProtocolAdapter:
        """
        Create a protocol adapter based on preference and availability.
        
        Args:
            protocol: Protocol type to create adapter for
            preference: SDK selection preference
            **kwargs: Additional arguments for adapter initialization
            
        Returns:
            IProtocolAdapter instance
        """
        if preference == SDKPreference.AUTO:
            return cls._create_auto_adapter(protocol, **kwargs)
        
        adapter_class = cls._get_adapter_class(protocol, preference)
        
        if preference == SDKPreference.HYBRID:
            # Create hybrid with custom fallback
            custom_class = cls.ADAPTERS[protocol]['custom']
            custom_adapter = custom_class() if custom_class else None
            return adapter_class(fallback_adapter=custom_adapter)
        
        return adapter_class()
    
    @classmethod
    def _create_auto_adapter(
        cls,
        protocol: ProtocolType,
        **kwargs
    ) -> IProtocolAdapter:
        """Automatically select best adapter based on availability and features."""
        # Check SDK availability
        if cls._is_sdk_available(protocol):
            # Check if official SDK supports required features
            required_features = kwargs.get('required_features', [])
            official_class = cls.ADAPTERS[protocol]['official']
            
            if official_class and cls._supports_features(
                official_class, required_features
            ):
                # Use official SDK
                return official_class()
            else:
                # Use hybrid for feature compatibility
                return cls.create_adapter(
                    protocol, SDKPreference.HYBRID, **kwargs
                )
        else:
            # Fall back to custom implementation
            custom_class = cls.ADAPTERS[protocol]['custom']
            if custom_class:
                return custom_class()
            else:
                raise ValueError(
                    f"No implementation available for {protocol.value}"
                )
    
    @classmethod
    def _get_adapter_class(
        cls,
        protocol: ProtocolType,
        preference: SDKPreference
    ) -> Type[IProtocolAdapter]:
        """Get adapter class based on preference."""
        if protocol not in cls.ADAPTERS:
            raise ValueError(f"Unknown protocol: {protocol}")
        
        pref_key = preference.value
        if pref_key == 'auto':
            pref_key = 'hybrid'  # Default to hybrid for auto
        
        adapter_class = cls.ADAPTERS[protocol].get(pref_key)
        
        if not adapter_class:
            # Fall back to custom if requested type not available
            adapter_class = cls.ADAPTERS[protocol]['custom']
        
        if not adapter_class:
            raise ValueError(
                f"No {preference.value} adapter for {protocol.value}"
            )
        
        return adapter_class
    
    @classmethod
    def _is_sdk_available(cls, protocol: ProtocolType) -> bool:
        """Check if official SDK is available for protocol."""
        if protocol in cls._sdk_availability:
            return cls._sdk_availability[protocol]
        
        # Check imports
        available = False
        
        if protocol == ProtocolType.MCP:
            try:
                import mcp
                available = True
            except ImportError:
                pass
        
        elif protocol == ProtocolType.A2A:
            try:
                import a2a
                available = True
            except ImportError:
                pass
        
        # ACP uses REST, so always "available" if aiohttp is installed
        elif protocol == ProtocolType.ACP:
            try:
                import aiohttp
                available = True
            except ImportError:
                pass
        
        # ANP has no Python SDK yet
        elif protocol == ProtocolType.ANP:
            available = False
        
        cls._sdk_availability[protocol] = available
        return available
    
    @classmethod
    def _supports_features(
        cls,
        adapter_class: Type[IProtocolAdapter],
        features: list
    ) -> bool:
        """Check if adapter supports required features."""
        if not features:
            return True
        
        # Create temporary instance to check features
        try:
            adapter = adapter_class()
            for feature in features:
                if not adapter.supports_feature(feature):
                    return False
            return True
        except Exception:
            return False
    
    @classmethod
    def get_available_adapters(cls) -> Dict[str, Dict[str, bool]]:
        """Get availability status of all adapters."""
        status = {}
        
        for protocol in ProtocolType:
            status[protocol.value] = {
                'official': cls._is_sdk_available(protocol),
                'custom': cls.ADAPTERS[protocol]['custom'] is not None,
                'hybrid': (
                    cls._is_sdk_available(protocol) and
                    cls.ADAPTERS[protocol]['custom'] is not None
                )
            }
        
        return status
    
    @classmethod
    def get_best_adapter(
        cls,
        protocol: ProtocolType,
        features: Optional[list] = None
    ) -> str:
        """Recommend best adapter type based on requirements."""
        if not cls._is_sdk_available(protocol):
            return "custom"
        
        official_class = cls.ADAPTERS[protocol]['official']
        if official_class and cls._supports_features(official_class, features or []):
            return "official"
        
        # Hybrid provides best of both worlds
        return "hybrid"


# Convenience functions
def create_mcp_adapter(preference: SDKPreference = SDKPreference.AUTO) -> IProtocolAdapter:
    """Create MCP adapter with specified preference."""
    return AdapterFactory.create_adapter(ProtocolType.MCP, preference)


def create_a2a_adapter(preference: SDKPreference = SDKPreference.AUTO) -> IProtocolAdapter:
    """Create A2A adapter with specified preference."""
    return AdapterFactory.create_adapter(ProtocolType.A2A, preference)


def create_acp_adapter(preference: SDKPreference = SDKPreference.AUTO) -> IProtocolAdapter:
    """Create ACP adapter with specified preference."""
    return AdapterFactory.create_adapter(ProtocolType.ACP, preference)


def create_anp_adapter(preference: SDKPreference = SDKPreference.AUTO) -> IProtocolAdapter:
    """Create ANP adapter with specified preference."""
    return AdapterFactory.create_adapter(ProtocolType.ANP, preference)
