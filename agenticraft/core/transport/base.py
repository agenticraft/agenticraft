"""
Base transport interface for all protocols.

This module defines protocol-agnostic transport abstractions
that can be used by MCP, A2A, and other protocols.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Dict, Callable, Awaitable, Generic, TypeVar
import asyncio
import logging

logger = logging.getLogger(__name__)

# Type variables for generic message types
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class MessageType(Enum):
    """Types of messages in transport layer."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class Message:
    """Generic message structure."""
    id: Optional[str]
    type: MessageType
    payload: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class TransportConfig:
    """Protocol-agnostic transport configuration."""
    url: str
    timeout: float = 30.0
    max_retries: int = 3
    headers: Optional[Dict[str, str]] = None
    auth: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "headers": self.headers or {},
            "auth": self.auth or {},
            "extra": self.extra or {}
        }


class Transport(ABC, Generic[TRequest, TResponse]):
    """Abstract base class for all transports."""
    
    def __init__(self, config: TransportConfig):
        """
        Initialize transport.
        
        Args:
            config: Transport configuration
        """
        self.config = config
        self._connected = False
        self._message_handler: Optional[Callable[[Message], Awaitable[None]]] = None
        self._error_handler: Optional[Callable[[Exception], Awaitable[None]]] = None
        
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass
        
    @abstractmethod
    async def send(self, message: Message) -> Optional[Message]:
        """
        Send message and optionally wait for response.
        
        Args:
            message: Message to send
            
        Returns:
            Response message if request, None if notification
        """
        pass
        
    @abstractmethod
    async def receive(self) -> Message:
        """
        Receive next message.
        
        Returns:
            Received message
        """
        pass
        
    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected
        
    def on_message(self, handler: Callable[[Message], Awaitable[None]]) -> None:
        """
        Set handler for incoming messages.
        
        Args:
            handler: Async function to handle incoming messages
        """
        self._message_handler = handler
        
    def on_error(self, handler: Callable[[Exception], Awaitable[None]]) -> None:
        """
        Set handler for errors.
        
        Args:
            handler: Async function to handle errors
        """
        self._error_handler = handler
        
    async def send_request(self, request: TRequest, timeout: Optional[float] = None) -> TResponse:
        """
        Send request and wait for response.
        
        Args:
            request: Request to send
            timeout: Optional timeout override
            
        Returns:
            Response
        """
        # Default implementation - subclasses can override
        message = self._request_to_message(request)
        response = await asyncio.wait_for(
            self.send(message),
            timeout or self.config.timeout
        )
        if response is None:
            raise TransportError("No response received")
        return self._message_to_response(response)
        
    async def send_notification(self, notification: TRequest) -> None:
        """
        Send notification (no response expected).
        
        Args:
            notification: Notification to send
        """
        # Default implementation - subclasses can override
        message = self._notification_to_message(notification)
        await self.send(message)
        
    def _request_to_message(self, request: TRequest) -> Message:
        """Convert protocol-specific request to generic message."""
        # Subclasses should override
        return Message(
            id=str(id(request)),
            type=MessageType.REQUEST,
            payload=request
        )
        
    def _notification_to_message(self, notification: TRequest) -> Message:
        """Convert protocol-specific notification to generic message."""
        # Subclasses should override
        return Message(
            id=None,
            type=MessageType.NOTIFICATION,
            payload=notification
        )
        
    def _message_to_response(self, message: Message) -> TResponse:
        """Convert generic message to protocol-specific response."""
        # Subclasses should override
        return message.payload
        
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
    
    _transports: Dict[str, type[Transport]] = {}
    
    @classmethod
    def register(cls, scheme: str, transport_class: type[Transport]) -> None:
        """
        Register a transport implementation.
        
        Args:
            scheme: URL scheme (e.g., "http", "ws")
            transport_class: Transport class to register
        """
        cls._transports[scheme] = transport_class
        logger.info(f"Registered transport for scheme: {scheme}")
        
    @classmethod
    def get(cls, url: str) -> Optional[type[Transport]]:
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
    def create(cls, config: TransportConfig) -> Transport:
        """
        Create transport instance for configuration.
        
        Args:
            config: Transport configuration
            
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
        
    @classmethod
    def list_schemes(cls) -> list[str]:
        """List all registered schemes."""
        return list(cls._transports.keys())
