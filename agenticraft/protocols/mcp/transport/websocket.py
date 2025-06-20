"""
WebSocket transport implementation for MCP protocol.

This module provides WebSocket transport for MCP,
suitable for bidirectional, real-time communication.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from collections import defaultdict

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    WebSocketClientProtocol = Any

from .base import IMCPTransport, ConnectionError, TimeoutError
from ..types import MCPRequest, MCPResponse, MCPError, MCPErrorCode

logger = logging.getLogger(__name__)


class WebSocketTransport(IMCPTransport):
    """WebSocket transport for MCP protocol."""
    
    def __init__(self, config):
        """Initialize WebSocket transport."""
        super().__init__(config)
        
        if not HAS_WEBSOCKETS:
            raise ImportError(
                "WebSocket support requires 'websockets' package. "
                "Install with: pip install agenticraft[websocket]"
            )
            
        self._ws: Optional[WebSocketClientProtocol] = None
        self._message_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[str | int, asyncio.Future] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 1.0  # seconds
        
    async def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            # Connect to WebSocket server
            extra_headers = self.config.headers if self.config.headers else None
            
            # Create connection with appropriate parameters
            logger.info(f"Connecting to WebSocket server at {self.config.url}")
            self._ws = await websockets.connect(
                self.config.url,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self._connected = True
            self._reconnect_attempts = 0
            
            # Start message handler task
            self._message_task = asyncio.create_task(self._handle_messages())
            
            logger.info(f"Connected to MCP WebSocket server at {self.config.url}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to WebSocket server: {e}")
            
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
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
        logger.info("Disconnected from MCP WebSocket server")
        
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """
        Send WebSocket request and wait for response.
        
        Args:
            request: MCP request to send
            
        Returns:
            MCP response
            
        Raises:
            ConnectionError: If not connected
            TimeoutError: If request times out
        """
        if not self._connected or not self._ws:
            raise ConnectionError("Not connected to MCP server")
            
        # Create future for response
        future = asyncio.Future()
        self._pending_requests[request.id] = future
        
        try:
            # Send request
            await self._ws.send(json.dumps(request.to_dict()))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(
                future,
                timeout=self.config.timeout
            )
            
            return response
            
        except asyncio.TimeoutError:
            # Remove from pending
            self._pending_requests.pop(request.id, None)
            raise TimeoutError(f"Request timeout: {request.method}")
            
        except Exception as e:
            # Remove from pending
            self._pending_requests.pop(request.id, None)
            raise ConnectionError(f"Failed to send request: {e}")
            
    async def send_notification(self, request: MCPRequest) -> None:
        """
        Send WebSocket notification (no response expected).
        
        Args:
            request: MCP notification to send
        """
        if not self._connected or not self._ws:
            raise ConnectionError("Not connected to MCP server")
            
        try:
            # For notifications, id should be None
            request.id = None
            await self._ws.send(json.dumps(request.to_dict()))
            
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
            # Don't raise for notifications
            
    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for message in self._ws:
                try:
                    # Parse message
                    data = json.loads(message)
                    
                    # Check if it's a response or notification
                    if "id" in data and data["id"] is not None:
                        # Response to a request
                        response = self._parse_response(data)
                        
                        # Find pending request
                        request_id = response.id
                        if request_id in self._pending_requests:
                            future = self._pending_requests.pop(request_id)
                            
                            if response.is_error:
                                future.set_exception(
                                    ConnectionError(f"MCP error: {response.error.message}")
                                )
                            else:
                                future.set_result(response)
                                
                    else:
                        # Server notification/event
                        if self._message_handler:
                            response = self._parse_response(data)
                            await self._message_handler(response)
                            
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            self._connected = False
            
            # Cancel all pending requests
            for future in self._pending_requests.values():
                if not future.done():
                    future.set_exception(ConnectionError("Connection closed"))
            self._pending_requests.clear()
            
            # Try to reconnect if configured
            if self._reconnect_attempts < self._max_reconnect_attempts:
                await self._try_reconnect()
                
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            self._connected = False
            
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
            
    def _parse_response(self, data: Dict[str, Any]) -> MCPResponse:
        """Parse response data into MCPResponse object."""
        if "error" in data:
            error_data = data["error"]
            error = MCPError(
                code=MCPErrorCode(error_data.get("code", "internal_error")),
                message=error_data.get("message", "Unknown error"),
                data=error_data.get("data")
            )
            return MCPResponse(
                jsonrpc=data.get("jsonrpc", "2.0"),
                id=data.get("id"),
                error=error
            )
        else:
            return MCPResponse(
                jsonrpc=data.get("jsonrpc", "2.0"),
                id=data.get("id"),
                result=data.get("result")
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


# Register WebSocket transports
if HAS_WEBSOCKETS:
    from .base import TransportRegistry
    
    TransportRegistry.register("ws", WebSocketTransport)
    TransportRegistry.register("wss", WebSocketTransport)
