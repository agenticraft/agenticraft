"""
Client-Server communication pattern.

This module provides a protocol-agnostic client-server pattern
that can be used by any protocol implementation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, Awaitable, List
import asyncio
import logging
from uuid import uuid4

from ..transport.base import Transport, Message, MessageType

logger = logging.getLogger(__name__)


@dataclass
class Request:
    """Client request."""
    id: str
    method: str
    params: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class Response:
    """Server response."""
    id: str
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Server(ABC):
    """Abstract server for client-server pattern."""
    
    def __init__(self, transport: Transport):
        """
        Initialize server.
        
        Args:
            transport: Transport layer
        """
        self.transport = transport
        self._handlers: Dict[str, Callable] = {}
        self._middleware: List[Callable] = []
        self._running = False
        
    def add_handler(
        self,
        method: str,
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """
        Add method handler.
        
        Args:
            method: Method name
            handler: Async handler function
        """
        self._handlers[method] = handler
        logger.debug(f"Added handler for method: {method}")
        
    def add_middleware(
        self,
        middleware: Callable[[Request, Callable], Awaitable[Response]]
    ) -> None:
        """
        Add middleware.
        
        Args:
            middleware: Middleware function
        """
        self._middleware.append(middleware)
        
    async def start(self) -> None:
        """Start server."""
        await self.transport.connect()
        self.transport.on_message(self._handle_message)
        self._running = True
        logger.info("Server started")
        
    async def stop(self) -> None:
        """Stop server."""
        self._running = False
        await self.transport.disconnect()
        logger.info("Server stopped")
        
    async def _handle_message(self, message: Message) -> None:
        """Handle incoming message."""
        if message.type != MessageType.REQUEST:
            return
            
        try:
            # Parse request
            request = self._parse_request(message)
            
            # Process through middleware
            response = await self._process_request(request)
            
            # Send response
            response_message = Message(
                id=message.id,
                type=MessageType.RESPONSE,
                payload=self._serialize_response(response)
            )
            
            await self.transport.send(response_message)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            
            # Send error response
            error_response = Response(
                id=message.id or "unknown",
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            )
            
            response_message = Message(
                id=message.id,
                type=MessageType.RESPONSE,
                payload=self._serialize_response(error_response)
            )
            
            await self.transport.send(response_message)
            
    async def _process_request(self, request: Request) -> Response:
        """Process request through handlers and middleware."""
        # Find handler
        handler = self._handlers.get(request.method)
        if not handler:
            return Response(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                }
            )
            
        # Apply middleware
        async def next_handler(req: Request) -> Response:
            try:
                result = await handler(req.params)
                return Response(id=req.id, result=result)
            except Exception as e:
                return Response(
                    id=req.id,
                    error={
                        "code": -32603,
                        "message": str(e)
                    }
                )
                
        current_handler = next_handler
        for middleware in reversed(self._middleware):
            async def wrapped(req: Request, handler=current_handler, mw=middleware):
                return await mw(req, handler)
            current_handler = wrapped
            
        return await current_handler(request)
        
    @abstractmethod
    def _parse_request(self, message: Message) -> Request:
        """Parse message into request."""
        pass
        
    @abstractmethod
    def _serialize_response(self, response: Response) -> Any:
        """Serialize response for transport."""
        pass


class Client(ABC):
    """Abstract client for client-server pattern."""
    
    def __init__(self, transport: Transport):
        """
        Initialize client.
        
        Args:
            transport: Transport layer
        """
        self.transport = transport
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
    async def connect(self) -> None:
        """Connect to server."""
        await self.transport.connect()
        self.transport.on_message(self._handle_response)
        logger.info("Client connected")
        
    async def disconnect(self) -> None:
        """Disconnect from server."""
        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        
        await self.transport.disconnect()
        logger.info("Client disconnected")
        
    async def request(
        self,
        method: str,
        params: Any = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Send request to server.
        
        Args:
            method: Method name
            params: Method parameters
            timeout: Request timeout
            
        Returns:
            Response result
            
        Raises:
            Exception: If request fails
        """
        request_id = str(uuid4())
        
        # Create request
        request = Request(
            id=request_id,
            method=method,
            params=params
        )
        
        # Create future for response
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # Send request
            message = Message(
                id=request_id,
                type=MessageType.REQUEST,
                payload=self._serialize_request(request)
            )
            
            await self.transport.send(message)
            
            # Wait for response
            response = await asyncio.wait_for(
                future,
                timeout=timeout or self.transport.config.timeout
            )
            
            if response.error:
                raise Exception(response.error.get("message", "Unknown error"))
                
            return response.result
            
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request timeout: {method}")
        except Exception:
            self._pending_requests.pop(request_id, None)
            raise
            
    async def notify(self, method: str, params: Any = None) -> None:
        """
        Send notification to server (no response expected).
        
        Args:
            method: Method name
            params: Method parameters
        """
        request = Request(
            id=None,  # No ID for notifications
            method=method,
            params=params
        )
        
        message = Message(
            id=None,
            type=MessageType.NOTIFICATION,
            payload=self._serialize_request(request)
        )
        
        await self.transport.send(message)
        
    async def _handle_response(self, message: Message) -> None:
        """Handle response from server."""
        if message.type != MessageType.RESPONSE or not message.id:
            return
            
        future = self._pending_requests.pop(message.id, None)
        if not future:
            return
            
        try:
            response = self._parse_response(message)
            future.set_result(response)
        except Exception as e:
            future.set_exception(e)
            
    @abstractmethod
    def _serialize_request(self, request: Request) -> Any:
        """Serialize request for transport."""
        pass
        
    @abstractmethod
    def _parse_response(self, message: Message) -> Response:
        """Parse message into response."""
        pass


class ClientServerPattern:
    """Client-server communication pattern."""
    
    def __init__(self):
        """Initialize pattern."""
        self._servers: Dict[str, Server] = {}
        self._clients: Dict[str, Client] = {}
        
    def create_server(
        self,
        server_id: str,
        transport: Transport,
        server_class: type[Server] = None
    ) -> Server:
        """
        Create a server.
        
        Args:
            server_id: Server identifier
            transport: Transport layer
            server_class: Server class (uses default if None)
            
        Returns:
            Server instance
        """
        if server_class is None:
            server_class = self._get_default_server_class()
            
        server = server_class(transport)
        self._servers[server_id] = server
        
        return server
        
    def create_client(
        self,
        client_id: str,
        transport: Transport,
        client_class: type[Client] = None
    ) -> Client:
        """
        Create a client.
        
        Args:
            client_id: Client identifier
            transport: Transport layer
            client_class: Client class (uses default if None)
            
        Returns:
            Client instance
        """
        if client_class is None:
            client_class = self._get_default_client_class()
            
        client = client_class(transport)
        self._clients[client_id] = client
        
        return client
        
    def get_server(self, server_id: str) -> Optional[Server]:
        """Get server by ID."""
        return self._servers.get(server_id)
        
    def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID."""
        return self._clients.get(client_id)
        
    async def stop_all(self) -> None:
        """Stop all servers and disconnect all clients."""
        # Stop servers
        for server in self._servers.values():
            await server.stop()
            
        # Disconnect clients
        for client in self._clients.values():
            await client.disconnect()
            
        self._servers.clear()
        self._clients.clear()
        
    def _get_default_server_class(self) -> type[Server]:
        """Get default server implementation."""
        
        class DefaultServer(Server):
            def _parse_request(self, message: Message) -> Request:
                payload = message.payload
                return Request(
                    id=payload.get("id", str(uuid4())),
                    method=payload.get("method", ""),
                    params=payload.get("params"),
                    metadata=payload.get("metadata")
                )
                
            def _serialize_response(self, response: Response) -> Any:
                return {
                    "id": response.id,
                    "result": response.result,
                    "error": response.error,
                    "metadata": response.metadata
                }
                
        return DefaultServer
        
    def _get_default_client_class(self) -> type[Client]:
        """Get default client implementation."""
        
        class DefaultClient(Client):
            def _serialize_request(self, request: Request) -> Any:
                return {
                    "id": request.id,
                    "method": request.method,
                    "params": request.params,
                    "metadata": request.metadata
                }
                
            def _parse_response(self, message: Message) -> Response:
                payload = message.payload
                return Response(
                    id=payload.get("id", ""),
                    result=payload.get("result"),
                    error=payload.get("error"),
                    metadata=payload.get("metadata")
                )
                
        return DefaultClient
