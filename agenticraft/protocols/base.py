"""
Base protocol interface for all protocols.

This module defines the abstract base class that all protocol
implementations (MCP, A2A, etc.) must inherit from.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Callable, Awaitable
import asyncio
import logging

from ..core.transport import Transport
from ..core.auth import AuthManager
from ..core.registry import ServiceRegistry

logger = logging.getLogger(__name__)


@dataclass
class ProtocolConfig:
    """Configuration for a protocol."""
    name: str
    version: str = "1.0"
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "metadata": self.metadata or {}
        }


class Protocol(ABC):
    """
    Abstract base class for all protocols.
    
    This class defines the common interface that all protocol
    implementations must provide.
    """
    
    def __init__(
        self,
        config: ProtocolConfig,
        transport: Optional[Transport] = None,
        auth: Optional[AuthManager] = None,
        registry: Optional[ServiceRegistry] = None
    ):
        """
        Initialize protocol.
        
        Args:
            config: Protocol configuration
            transport: Transport layer (optional)
            auth: Authentication manager (optional)
            registry: Service registry (optional)
        """
        self.config = config
        self.transport = transport
        self.auth = auth
        self.registry = registry
        
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        
    @abstractmethod
    async def start(self) -> None:
        """Start the protocol."""
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """Stop the protocol."""
        pass
        
    @abstractmethod
    async def send(
        self,
        message: Any,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Send a message.
        
        Args:
            message: Message to send
            target: Target identifier
            timeout: Operation timeout
            
        Returns:
            Response (if applicable)
        """
        pass
        
    @abstractmethod
    async def receive(self, timeout: Optional[float] = None) -> Any:
        """
        Receive a message.
        
        Args:
            timeout: Receive timeout
            
        Returns:
            Received message
        """
        pass
        
    def add_handler(
        self,
        message_type: str,
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """
        Add a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Async handler function
        """
        self._handlers[message_type] = handler
        logger.debug(f"Added handler for message type: {message_type}")
        
    def remove_handler(self, message_type: str) -> None:
        """
        Remove a message handler.
        
        Args:
            message_type: Type of message
        """
        self._handlers.pop(message_type, None)
        
    async def handle_message(self, message: Any) -> Any:
        """
        Handle an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Handler response (if any)
        """
        # Default implementation - protocols can override
        message_type = self._get_message_type(message)
        handler = self._handlers.get(message_type)
        
        if handler:
            return await handler(message)
        else:
            logger.warning(f"No handler for message type: {message_type}")
            return None
            
    def _get_message_type(self, message: Any) -> str:
        """
        Extract message type from message.
        
        Args:
            message: Message to inspect
            
        Returns:
            Message type identifier
        """
        # Default implementation - protocols should override
        if isinstance(message, dict):
            return message.get("type", "unknown")
        elif hasattr(message, "type"):
            return message.type
        else:
            return type(message).__name__
            
    async def health_check(self) -> Dict[str, Any]:
        """
        Check protocol health.
        
        Returns:
            Health status information
        """
        return {
            "protocol": self.config.name,
            "version": self.config.version,
            "running": self._running,
            "transport_connected": self.transport.is_connected if self.transport else None,
            "handlers_registered": len(self._handlers)
        }
        
    @property
    def is_running(self) -> bool:
        """Check if protocol is running."""
        return self._running
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


class RequestResponseProtocol(Protocol):
    """
    Base class for request-response style protocols.
    
    This class provides common functionality for protocols that
    follow a request-response pattern (like JSON-RPC).
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
    async def request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Send a request and wait for response.
        
        Args:
            method: Method name
            params: Method parameters
            target: Target identifier
            timeout: Request timeout
            
        Returns:
            Response result
        """
        # Subclasses should implement
        raise NotImplementedError
        
    async def notify(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None
    ) -> None:
        """
        Send a notification (no response expected).
        
        Args:
            method: Method name
            params: Method parameters
            target: Target identifier
        """
        # Subclasses should implement
        raise NotImplementedError
        
    def _create_request_id(self) -> str:
        """Create unique request ID."""
        from uuid import uuid4
        return str(uuid4())
        
    def _store_pending_request(self, request_id: str) -> asyncio.Future:
        """Store pending request and return future."""
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        return future
        
    def _complete_pending_request(
        self,
        request_id: str,
        result: Any = None,
        error: Any = None
    ) -> None:
        """Complete a pending request."""
        future = self._pending_requests.pop(request_id, None)
        if future and not future.done():
            if error:
                future.set_exception(error)
            else:
                future.set_result(result)
                
    async def _cleanup_pending_requests(self) -> None:
        """Cancel all pending requests."""
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()


class StreamingProtocol(Protocol):
    """
    Base class for streaming protocols.
    
    This class provides common functionality for protocols that
    support streaming communication.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._streams: Dict[str, asyncio.Queue] = {}
        
    async def create_stream(
        self,
        stream_id: str,
        target: Optional[str] = None
    ) -> None:
        """
        Create a new stream.
        
        Args:
            stream_id: Stream identifier
            target: Target for the stream
        """
        if stream_id in self._streams:
            raise ValueError(f"Stream {stream_id} already exists")
            
        self._streams[stream_id] = asyncio.Queue()
        
    async def close_stream(self, stream_id: str) -> None:
        """
        Close a stream.
        
        Args:
            stream_id: Stream identifier
        """
        queue = self._streams.pop(stream_id, None)
        if queue:
            # Put sentinel value to indicate stream closed
            await queue.put(None)
            
    async def write_to_stream(
        self,
        stream_id: str,
        data: Any
    ) -> None:
        """
        Write data to a stream.
        
        Args:
            stream_id: Stream identifier
            data: Data to write
        """
        queue = self._streams.get(stream_id)
        if not queue:
            raise ValueError(f"Unknown stream: {stream_id}")
            
        await queue.put(data)
        
    async def read_from_stream(
        self,
        stream_id: str,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Read data from a stream.
        
        Args:
            stream_id: Stream identifier
            timeout: Read timeout
            
        Returns:
            Data from stream (None if stream closed)
        """
        queue = self._streams.get(stream_id)
        if not queue:
            raise ValueError(f"Unknown stream: {stream_id}")
            
        if timeout:
            return await asyncio.wait_for(queue.get(), timeout)
        else:
            return await queue.get()
            
    async def _cleanup_streams(self) -> None:
        """Close all streams."""
        for stream_id in list(self._streams.keys()):
            await self.close_stream(stream_id)
