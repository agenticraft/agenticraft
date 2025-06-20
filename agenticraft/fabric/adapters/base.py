"""
Base adapter interface for protocol adapters.

This module defines the abstract base class that all protocol
adapters must implement to work with the fabric layer.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import asyncio
import logging

from ...protocols.base import Protocol
from ...core.transport import Transport
from ...core.auth import AuthManager

logger = logging.getLogger(__name__)


class ProtocolAdapter(ABC):
    """
    Abstract base class for protocol adapters.
    
    Protocol adapters provide a uniform interface for different
    protocols within the fabric layer.
    """
    
    def __init__(
        self,
        protocol: Protocol,
        transport: Transport,
        auth: Optional[AuthManager] = None
    ):
        """
        Initialize protocol adapter.
        
        Args:
            protocol: Protocol instance
            transport: Transport layer
            auth: Optional auth manager
        """
        self.protocol = protocol
        self.transport = transport
        self.auth = auth
        
        self._initialized = False
        
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the adapter.
        
        Args:
            config: Adapter configuration
        """
        if self._initialized:
            return
            
        # Setup protocol with transport and auth
        self.protocol.transport = self.transport
        self.protocol.auth = self.auth
        
        # Protocol-specific initialization
        await self._initialize_protocol(config)
        
        self._initialized = True
        logger.info(f"Initialized adapter for protocol {self.get_protocol_name()}")
        
    @abstractmethod
    async def _initialize_protocol(self, config: Dict[str, Any]) -> None:
        """
        Protocol-specific initialization.
        
        Args:
            config: Configuration
        """
        pass
        
    @abstractmethod
    async def send_message(
        self,
        message: Any,
        target: Optional[str] = None
    ) -> Any:
        """
        Send a message using the protocol.
        
        Args:
            message: Message to send
            target: Target identifier
            
        Returns:
            Response (if any)
        """
        pass
        
    @abstractmethod
    async def receive_message(self) -> Any:
        """
        Receive a message from the protocol.
        
        Returns:
            Received message
        """
        pass
        
    @abstractmethod
    def get_protocol_name(self) -> str:
        """
        Get the protocol name.
        
        Returns:
            Protocol name
        """
        pass
        
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get protocol capabilities.
        
        Returns:
            Dictionary of capabilities
        """
        pass
        
    async def call_method(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None
    ) -> Any:
        """
        Call a method on the protocol.
        
        Args:
            method: Method name
            params: Method parameters
            target: Target identifier
            
        Returns:
            Method result
        """
        # Default implementation for RPC-style protocols
        message = {
            "method": method,
            "params": params or {}
        }
        
        return await self.send_message(message, target)
        
    async def subscribe(
        self,
        topic: str,
        handler: Any
    ) -> str:
        """
        Subscribe to a topic/event.
        
        Args:
            topic: Topic to subscribe to
            handler: Message handler
            
        Returns:
            Subscription ID
        """
        # Default implementation - protocols can override
        raise NotImplementedError(
            f"Protocol {self.get_protocol_name()} does not support subscriptions"
        )
        
    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from a topic/event.
        
        Args:
            subscription_id: Subscription to cancel
        """
        # Default implementation - protocols can override
        raise NotImplementedError(
            f"Protocol {self.get_protocol_name()} does not support subscriptions"
        )
        
    async def discover_services(self) -> List[Dict[str, Any]]:
        """
        Discover available services.
        
        Returns:
            List of discovered services
        """
        # Default implementation - protocols can override
        return []
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Check adapter and protocol health.
        
        Returns:
            Health status
        """
        health = {
            "adapter": self.__class__.__name__,
            "protocol": self.get_protocol_name(),
            "initialized": self._initialized,
            "transport_connected": self.transport.is_connected if self.transport else False
        }
        
        # Add protocol health if available
        if hasattr(self.protocol, 'health_check'):
            try:
                health["protocol_health"] = await self.protocol.health_check()
            except Exception as e:
                health["protocol_health"] = {"error": str(e)}
                
        return health
        
    async def close(self) -> None:
        """Close the adapter and cleanup resources."""
        if hasattr(self.protocol, 'stop'):
            await self.protocol.stop()
            
        if self.transport:
            await self.transport.disconnect()
            
        self._initialized = False
        logger.info(f"Closed adapter for protocol {self.get_protocol_name()}")
