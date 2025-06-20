"""
WebSocket transport implementation for core transport layer.

This module provides WebSocket transport that can be used
by any protocol implementation.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from collections import defaultdict
import uuid

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketClientProtocol = Any

from .base import (
    Transport, TransportConfig, Message, MessageType,
    ConnectionError, TimeoutError, TransportRegistry
)

logger = logging.getLogger(__name__)


class WebSocketTransport(Transport[Dict[str, Any], Dict[str, Any]]):
    """WebSocket transport implementation."""
    
    def __init__(self, config: TransportConfig):
        """Initialize WebSocket transport."""
        super().__init__(config)
        
        if not HAS_WEBSOCKETS:
            raise ImportError(
                "WebSocket support requires 'websockets' package. "
                "Install with: pip install websockets"
            )
            
        self._ws: Optional[WebSocketClientProtocol] = None
        self._message_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._reconnect_attempts = 0
        
        # Configuration from extra
        extra = config.extra or {}
        self._max_reconnect_attempts = extra.get("max_reconnect_attempts", 5)
        self._reconnect_delay = extra.get("reconnect_delay", 1.0)
        self._auto_reconnect = extra.get("auto_reconnect", True)
        self._ping_interval = extra.get("ping_interval", 20)
        self._ping_timeout = extra.get("ping_timeout", 10)
        
    async def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            # Connect to WebSocket server
            extra_headers = self.config.headers if self.config.headers else None
            
            # Add auth headers if configured
            if self.config.auth:
                extra_headers = extra_headers or {}
                auth_type = self.config.auth.get("type", "")
                
                if auth_type == "bearer":
                    extra_headers["Authorization"] = f"Bearer {self.config.auth.get('token', '')}"
                elif auth_type == "api_key":
                    key_header = self.config.auth.get("header", "X-API-Key")
                    extra_headers[key_header] = self.config.auth.get('key', '')
            
            # Create connection
            logger.info(f"Connecting to WebSocket server at {self.config.url}")
            self._ws = await websockets.connect(
                self.config.url,
                extra_headers=extra_headers,
                ping_interval=self._ping_interval,
                ping_timeout=self._ping_timeout,
                close_timeout=10
            )
            
            self._connected = True
            self._reconnect_attempts = 0
            
            # Start message handler task
            self._message_task = asyncio.create_task(self._handle_messages())
            
            logger.info(f"Connected to WebSocket server at {self.config.url}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to WebSocket server: {e}")
            
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        # Disable auto-reconnect
        self._auto_reconnect = False
        
        # Cancel message handler
        if self._message_task:
            self._message_task.cancel()
            try:
                await self._message_task
            except asyncio.CancelledError:
                pass
            self._message_task = None
            
        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None
            
        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        
        self._connected = False
        logger.info("Disconnected from WebSocket server")
        
    async def send(self, message: Message) -> Optional[Message]:
        """
        Send message over WebSocket.
        
        Args:
            message: Message to send
            
        Returns:
            Response message if request, None if notification
        """
        if not self._connected or not self._ws:
            raise ConnectionError("Not connected to server")
            
        # Generate ID if not present for requests
        if message.type == MessageType.REQUEST and not message.id:
            message.id = str(uuid.uuid4())
            
        # Create future for response if this is a request
        future = None
        if message.type == MessageType.REQUEST:
            future = asyncio.Future()
            self._pending_requests[message.id] = future
            
        try:
            # Serialize and send message
            serialized = self._serialize_message(message)
            await self._ws.send(serialized)
            
            # Wait for response if this is a request
            if future:
                response_data = await asyncio.wait_for(
                    future,
                    timeout=self.config.timeout
                )
                return response_data
                
            return None
            
        except asyncio.TimeoutError:
            # Remove from pending
            if message.id:
                self._pending_requests.pop(message.id, None)
            raise TimeoutError("Request timeout")
            
        except Exception as e:
            # Remove from pending
            if message.id:
                self._pending_requests.pop(message.id, None)
            raise ConnectionError(f"Failed to send message: {e}")
            
    async def receive(self) -> Message:
        """
        Receive next message from WebSocket.
        
        Returns:
            Received message
        """
        if not self._connected or not self._ws:
            raise ConnectionError("Not connected to server")
            
        try:
            raw_message = await self._ws.recv()
            return self._deserialize_message(raw_message)
        except Exception as e:
            raise ConnectionError(f"Failed to receive message: {e}")
            
    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for raw_message in self._ws:
                try:
                    # Deserialize message
                    message = self._deserialize_message(raw_message)
                    
                    # Check if it's a response to a request
                    if message.type == MessageType.RESPONSE and message.id:
                        if message.id in self._pending_requests:
                            future = self._pending_requests.pop(message.id)
                            future.set_result(message)
                            
                    # Otherwise, call message handler if set
                    elif self._message_handler:
                        await self._message_handler(message)
                        
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    if self._error_handler:
                        await self._error_handler(e)
                    
        except websockets.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            self._connected = False
            
            # Cancel all pending requests
            for future in self._pending_requests.values():
                if not future.done():
                    future.set_exception(ConnectionError("Connection closed"))
            self._pending_requests.clear()
            
            # Try to reconnect if configured
            if self._auto_reconnect and self._reconnect_attempts < self._max_reconnect_attempts:
                await self._try_reconnect()
                
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            self._connected = False
            if self._error_handler:
                await self._error_handler(e)
            
    async def _try_reconnect(self) -> None:
        """Attempt to reconnect to the server."""
        self._reconnect_attempts += 1
        delay = self._reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        
        logger.info(
            f"Attempting reconnect {self._reconnect_attempts}/{self._max_reconnect_attempts} "
            f"in {delay}s..."
        )
        
        await asyncio.sleep(delay)
        
        try:
            await self.connect()
            logger.info("Reconnection successful")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            
    def _serialize_message(self, message: Message) -> str:
        """Serialize message for transmission."""
        # Default JSON serialization
        # Protocols can override this in subclasses
        data = {
            "type": message.type.value,
            "payload": message.payload
        }
        if message.id:
            data["id"] = message.id
        if message.metadata:
            data["metadata"] = message.metadata
            
        return json.dumps(data)
        
    def _deserialize_message(self, data: Union[str, bytes]) -> Message:
        """Deserialize received message."""
        # Default JSON deserialization
        # Protocols can override this in subclasses
        if isinstance(data, bytes):
            data = data.decode('utf-8')
            
        parsed = json.loads(data)
        
        return Message(
            id=parsed.get("id"),
            type=MessageType(parsed.get("type", "notification")),
            payload=parsed.get("payload"),
            metadata=parsed.get("metadata")
        )
        
    async def ping(self) -> bool:
        """
        Send ping to check connection.
        
        Returns:
            True if connection is alive
        """
        if not self._connected or not self._ws:
            return False
            
        try:
            pong = await self._ws.ping()
            await asyncio.wait_for(pong, timeout=5.0)
            return True
        except Exception:
            return False
            
    @property
    def is_alive(self) -> bool:
        """Check if WebSocket connection is alive."""
        return self._connected and self._ws is not None and not self._ws.closed


# Auto-register WebSocket transports if available
if HAS_WEBSOCKETS:
    TransportRegistry.register("ws", WebSocketTransport)
    TransportRegistry.register("wss", WebSocketTransport)
