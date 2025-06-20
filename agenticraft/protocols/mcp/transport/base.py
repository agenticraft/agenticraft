"""
Base transport interface for MCP protocol.

This module defines the transport abstraction that allows
MCP to work over different protocols (HTTP, WebSocket, etc.).
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Callable, Awaitable
import asyncio
import logging

from ..types import MCPRequest, MCPResponse, MCPConnectionConfig

logger = logging.getLogger(__name__)


class IMCPTransport(ABC):
    """Abstract base class for MCP transports."""
    
    def __init__(self, config: MCPConnectionConfig):
        """
        Initialize transport.
        
        Args:
            config: Connection configuration
        """
        self.config = config
        self._connected = False
        self._message_handler: Optional[Callable[[MCPResponse], Awaitable[None]]] = None
        
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass
        
    @abstractmethod
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """
        Send request and wait for response.
        
        Args:
            request: MCP request to send
            
        Returns:
            MCP response
        """
        pass
        
    @abstractmethod
    async def send_notification(self, request: MCPRequest) -> None:
        """
        Send notification (no response expected).
        
        Args:
            request: MCP notification to send
        """
        pass
        
    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected
        
    def set_message_handler(self, handler: Callable[[MCPResponse], Awaitable[None]]) -> None:
        """
        Set handler for incoming messages.
        
        Args:
            handler: Async function to handle incoming messages
        """
        self._message_handler = handler
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class TransportError(Exception):
    """Base exception for transport errors."""
    pass


class ConnectionError(TransportError):
    """Raised when connection fails."""
    pass


class TimeoutError(TransportError):
    """Raised when operation times out."""
    pass


class TransportRegistry:
    """Registry for transport implementations."""
    
    _transports: Dict[str, type[IMCPTransport]] = {}
    
    @classmethod
    def register(cls, scheme: str, transport_class: type[IMCPTransport]) -> None:
        """
        Register a transport implementation.
        
        Args:
            scheme: URL scheme (e.g., "http", "ws")
            transport_class: Transport class to register
        """
        cls._transports[scheme] = transport_class
        logger.info(f"Registered MCP transport for scheme: {scheme}")
        
    @classmethod
    def get(cls, url: str) -> Optional[type[IMCPTransport]]:
        """
        Get transport class for URL.
        
        Args:
            url: Connection URL
            
        Returns:
            Transport class or None
        """
        # Extract scheme
        if "://" in url:
            scheme = url.split("://")[0]
            return cls._transports.get(scheme)
        return None
        
    @classmethod
    def create(cls, config: MCPConnectionConfig) -> IMCPTransport:
        """
        Create transport instance for configuration.
        
        Args:
            config: Connection configuration
            
        Returns:
            Transport instance
            
        Raises:
            ValueError: If no transport available for URL scheme
        """
        transport_class = cls.get(config.url)
        if not transport_class:
            scheme = config.url.split("://")[0] if "://" in config.url else "unknown"
            raise ValueError(
                f"No transport registered for scheme: {scheme}. "
                f"Available: {list(cls._transports.keys())}"
            )
            
        return transport_class(config)
