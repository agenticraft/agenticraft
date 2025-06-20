"""
Base protocol bridge interface.

This module defines the abstract base class for protocol bridges
that enable communication between different protocols.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import logging

from ..base import Protocol

logger = logging.getLogger(__name__)


class ProtocolBridge(ABC):
    """
    Abstract base class for protocol bridges.
    
    A protocol bridge translates messages between two different
    protocols, enabling cross-protocol communication.
    """
    
    def __init__(
        self,
        protocol_a: Protocol,
        protocol_b: Protocol,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize protocol bridge.
        
        Args:
            protocol_a: First protocol
            protocol_b: Second protocol
            config: Bridge configuration
        """
        self.protocol_a = protocol_a
        self.protocol_b = protocol_b
        self.config = config or {}
        
        self._running = False
        self._translation_cache: Dict[str, Any] = {}
        
    async def start(self) -> None:
        """Start the bridge."""
        if self._running:
            return
            
        # Setup message handlers
        self.protocol_a.add_handler("bridge_message", self._handle_a_to_b)
        self.protocol_b.add_handler("bridge_message", self._handle_b_to_a)
        
        self._running = True
        logger.info(
            f"Started bridge between {self.protocol_a.config.name} "
            f"and {self.protocol_b.config.name}"
        )
        
    async def stop(self) -> None:
        """Stop the bridge."""
        if not self._running:
            return
            
        # Remove handlers
        self.protocol_a.remove_handler("bridge_message")
        self.protocol_b.remove_handler("bridge_message")
        
        self._running = False
        logger.info("Protocol bridge stopped")
        
    @abstractmethod
    async def translate_a_to_b(self, message: Any) -> Any:
        """
        Translate message from protocol A to protocol B.
        
        Args:
            message: Message in protocol A format
            
        Returns:
            Message in protocol B format
        """
        pass
        
    @abstractmethod
    async def translate_b_to_a(self, message: Any) -> Any:
        """
        Translate message from protocol B to protocol A.
        
        Args:
            message: Message in protocol B format
            
        Returns:
            Message in protocol A format
        """
        pass
        
    async def bridge_message(
        self,
        message: Any,
        source_protocol: str,
        target: Optional[str] = None
    ) -> Any:
        """
        Bridge a message between protocols.
        
        Args:
            message: Message to bridge
            source_protocol: Source protocol name
            target: Target identifier
            
        Returns:
            Response from target protocol
        """
        if source_protocol == self.protocol_a.config.name:
            # A to B
            translated = await self.translate_a_to_b(message)
            return await self.protocol_b.send(translated, target)
            
        elif source_protocol == self.protocol_b.config.name:
            # B to A
            translated = await self.translate_b_to_a(message)
            return await self.protocol_a.send(translated, target)
            
        else:
            raise ValueError(f"Unknown source protocol: {source_protocol}")
            
    async def _handle_a_to_b(self, message: Any) -> Any:
        """Handle message from protocol A to B."""
        translated = await self.translate_a_to_b(message)
        return await self.protocol_b.send(translated)
        
    async def _handle_b_to_a(self, message: Any) -> Any:
        """Handle message from protocol B to A."""
        translated = await self.translate_b_to_a(message)
        return await self.protocol_a.send(translated)
        
    def get_supported_protocols(self) -> Tuple[str, str]:
        """Get names of bridged protocols."""
        return (
            self.protocol_a.config.name,
            self.protocol_b.config.name
        )
        
    @property
    def is_running(self) -> bool:
        """Check if bridge is running."""
        return self._running
