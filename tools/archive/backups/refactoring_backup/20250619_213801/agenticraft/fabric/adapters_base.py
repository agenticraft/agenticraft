"""
Adapter factory and SDK management for unified protocol fabric.

This module provides the factory pattern for creating protocol adapters
with support for official SDKs, custom implementations, and hybrid modes.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, Type

from agenticraft.fabric.agent_enhanced import (
    ProtocolType,
    IProtocolAdapter,
    MCPAdapter,
    A2AAdapter,
    ACPAdapter,
    ANPAdapter
)

logger = logging.getLogger(__name__)


class SDKPreference(Enum):
    """SDK preference modes."""
    OFFICIAL = "official"  # Use official SDK only
    CUSTOM = "custom"      # Use custom implementation only
    HYBRID = "hybrid"      # Use official SDK with custom fallback
    AUTO = "auto"          # Automatically select best option


class AdapterFactory:
    """
    Factory for creating protocol adapters with SDK preference support.
    
    This factory:
    - Detects available official SDKs
    - Creates appropriate adapters based on preferences
    - Provides hybrid mode with fallback support
    """
    
    # Official SDK availability flags
    # These would be set based on actual SDK imports
    _SDK_AVAILABLE = {
        ProtocolType.MCP: False,  # Will be True when official MCP SDK is available
        ProtocolType.A2A: False,  # Will be True when official A2A SDK is available
        ProtocolType.ACP: False,  # IBM ACP SDK
        ProtocolType.ANP: False,  # ANP SDK
    }
    
    # Custom adapter classes
    _CUSTOM_ADAPTERS = {
        ProtocolType.MCP: MCPAdapter,
        ProtocolType.A2A: A2AAdapter,
        ProtocolType.ACP: ACPAdapter,
        ProtocolType.ANP: ANPAdapter,
    }
    
    # Official adapter classes (when available)
    _OFFICIAL_ADAPTERS: Dict[ProtocolType, Type[IProtocolAdapter]] = {}
    
    @classmethod
    def _detect_official_sdks(cls):
        """Detect and register official SDKs."""
        # Try to import official MCP SDK
        try:
            import mcp  # type: ignore
            from agenticraft.fabric.adapters_official import OfficialMCPAdapter
            cls._SDK_AVAILABLE[ProtocolType.MCP] = True
            cls._OFFICIAL_ADAPTERS[ProtocolType.MCP] = OfficialMCPAdapter
            logger.info("Official MCP SDK detected")
        except ImportError:
            logger.debug("Official MCP SDK not available")
        
        # Try to import official A2A SDK
        try:
            import a2a_protocol  # type: ignore
            from agenticraft.fabric.adapters_official import OfficialA2AAdapter
            cls._SDK_AVAILABLE[ProtocolType.A2A] = True
            cls._OFFICIAL_ADAPTERS[ProtocolType.A2A] = OfficialA2AAdapter
            logger.info("Official A2A SDK detected")
        except ImportError:
            logger.debug("Official A2A SDK not available")
    
    @classmethod
    def _is_sdk_available(cls, protocol: ProtocolType) -> bool:
        """Check if official SDK is available for protocol."""
        # Detect SDKs on first check
        if not any(cls._SDK_AVAILABLE.values()):
            cls._detect_official_sdks()
        
        return cls._SDK_AVAILABLE.get(protocol, False)
    
    @classmethod
    def create_adapter(
        cls,
        protocol: ProtocolType,
        preference: SDKPreference = SDKPreference.AUTO
    ) -> IProtocolAdapter:
        """
        Create protocol adapter based on preference.
        
        Args:
            protocol: Protocol type
            preference: SDK preference mode
            
        Returns:
            Protocol adapter instance
            
        Raises:
            ValueError: If requested adapter type is not available
        """
        # Check SDK availability
        sdk_available = cls._is_sdk_available(protocol)
        custom_available = protocol in cls._CUSTOM_ADAPTERS
        
        # Determine which adapter to use
        use_official = False
        
        if preference == SDKPreference.OFFICIAL:
            if not sdk_available:
                raise ValueError(
                    f"Official SDK not available for {protocol.value}. "
                    f"Install it or use CUSTOM/HYBRID preference."
                )
            use_official = True
            
        elif preference == SDKPreference.CUSTOM:
            if not custom_available:
                raise ValueError(f"Custom adapter not available for {protocol.value}")
            use_official = False
            
        elif preference == SDKPreference.HYBRID:
            # Use official if available, fallback to custom
            use_official = sdk_available
            
        elif preference == SDKPreference.AUTO:
            # Automatically select best option
            # Prefer official SDK if available
            use_official = sdk_available
        
        # Create adapter
        if use_official:
            adapter_class = cls._OFFICIAL_ADAPTERS[protocol]
            logger.info(f"Creating official {protocol.value} adapter")
        else:
            adapter_class = cls._CUSTOM_ADAPTERS[protocol]
            logger.info(f"Creating custom {protocol.value} adapter")
        
        adapter = adapter_class()
        
        # For hybrid mode, wrap adapter with fallback support
        if preference == SDKPreference.HYBRID and sdk_available:
            adapter = HybridAdapter(
                primary=adapter,
                fallback=cls._CUSTOM_ADAPTERS[protocol]()
            )
        
        return adapter
    
    @classmethod
    def get_available_adapters(cls) -> Dict[str, Dict[str, bool]]:
        """Get availability status of all adapters."""
        # Ensure SDKs are detected
        if not any(cls._SDK_AVAILABLE.values()):
            cls._detect_official_sdks()
        
        status = {}
        for protocol in ProtocolType:
            status[protocol.value] = {
                "official": cls._SDK_AVAILABLE.get(protocol, False),
                "custom": protocol in cls._CUSTOM_ADAPTERS
            }
        
        return status
    
    @classmethod
    def get_best_adapter(cls, protocol: ProtocolType) -> str:
        """Get recommendation for best adapter type."""
        sdk_available = cls._is_sdk_available(protocol)
        
        if sdk_available:
            return "official"
        elif protocol in cls._CUSTOM_ADAPTERS:
            return "custom"
        else:
            return "unavailable"
    
    @classmethod
    def register_official_adapter(
        cls,
        protocol: ProtocolType,
        adapter_class: Type[IProtocolAdapter]
    ):
        """Register an official SDK adapter."""
        cls._OFFICIAL_ADAPTERS[protocol] = adapter_class
        cls._SDK_AVAILABLE[protocol] = True
        logger.info(f"Registered official adapter for {protocol.value}")
    
    @classmethod
    def register_custom_adapter(
        cls,
        protocol: ProtocolType,
        adapter_class: Type[IProtocolAdapter]
    ):
        """Register a custom adapter."""
        cls._CUSTOM_ADAPTERS[protocol] = adapter_class
        logger.info(f"Registered custom adapter for {protocol.value}")


class HybridAdapter(IProtocolAdapter):
    """
    Hybrid adapter that uses primary adapter with fallback support.
    
    This adapter:
    - Tries primary adapter first
    - Falls back to secondary adapter on failure
    - Provides seamless failover
    """
    
    def __init__(self, primary: IProtocolAdapter, fallback: IProtocolAdapter):
        """
        Initialize hybrid adapter.
        
        Args:
            primary: Primary adapter (usually official SDK)
            fallback: Fallback adapter (usually custom)
        """
        self.primary = primary
        self.fallback = fallback
        self._active_adapter = primary
    
    @property
    def protocol_type(self) -> ProtocolType:
        """Get protocol type from primary adapter."""
        return self.primary.protocol_type
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect using primary, fallback if needed."""
        try:
            await self.primary.connect(config)
            self._active_adapter = self.primary
            logger.info(f"Connected via primary adapter for {self.protocol_type.value}")
        except Exception as e:
            logger.warning(f"Primary adapter failed: {e}, trying fallback")
            await self.fallback.connect(config)
            self._active_adapter = self.fallback
            logger.info(f"Connected via fallback adapter for {self.protocol_type.value}")
    
    async def disconnect(self) -> None:
        """Disconnect active adapter."""
        await self._active_adapter.disconnect()
    
    async def discover_tools(self) -> list:
        """Discover tools from active adapter."""
        return await self._active_adapter.discover_tools()
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute tool with failover support."""
        try:
            return await self._active_adapter.execute_tool(tool_name, **kwargs)
        except Exception as e:
            if self._active_adapter == self.primary:
                logger.warning(f"Primary execution failed: {e}, trying fallback")
                return await self.fallback.execute_tool(tool_name, **kwargs)
            else:
                raise
    
    async def get_capabilities(self) -> list:
        """Get capabilities from active adapter."""
        caps = await self._active_adapter.get_capabilities()
        
        # Add hybrid capability
        from agenticraft.fabric.agent_enhanced import ProtocolCapability
        caps.append(ProtocolCapability(
            name="hybrid_mode",
            description="Hybrid adapter with failover support",
            protocol=self.protocol_type,
            metadata={
                "primary": type(self.primary).__name__,
                "fallback": type(self.fallback).__name__,
                "active": type(self._active_adapter).__name__
            }
        ))
        
        return caps
    
    def supports_feature(self, feature: str) -> bool:
        """Check if feature is supported by either adapter."""
        primary_supports = (
            hasattr(self.primary, 'supports_feature') and
            self.primary.supports_feature(feature)
        )
        fallback_supports = (
            hasattr(self.fallback, 'supports_feature') and
            self.fallback.supports_feature(feature)
        )
        
        return primary_supports or fallback_supports
