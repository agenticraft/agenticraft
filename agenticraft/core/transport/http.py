"""
HTTP transport implementation for core transport layer.

This module provides HTTP/HTTPS transport that can be used
by any protocol implementation.
"""
import json
import logging
from typing import Dict, Any, Optional, Union

import httpx

from .base import (
    Transport, TransportConfig, Message, MessageType,
    ConnectionError, TimeoutError, TransportRegistry
)

logger = logging.getLogger(__name__)


class HTTPTransport(Transport[Dict[str, Any], Dict[str, Any]]):
    """HTTP transport implementation."""
    
    def __init__(self, config: TransportConfig):
        """Initialize HTTP transport."""
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None
        self._endpoint_path = config.extra.get("endpoint", "/") if config.extra else "/"
        
    async def connect(self) -> None:
        """Establish HTTP client connection."""
        try:
            # Parse base URL
            base_url = self.config.url
            if not base_url.endswith("/"):
                base_url += "/"
                
            # Create HTTP client
            headers = self.config.headers or {}
            
            # Add auth headers if configured
            if self.config.auth:
                auth_type = self.config.auth.get("type", "")
                if auth_type == "bearer":
                    headers["Authorization"] = f"Bearer {self.config.auth.get('token', '')}"
                elif auth_type == "api_key":
                    key_header = self.config.auth.get("header", "X-API-Key")
                    headers[key_header] = self.config.auth.get('key', '')
                    
            self._client = httpx.AsyncClient(
                base_url=base_url,
                headers=headers,
                timeout=httpx.Timeout(self.config.timeout),
                follow_redirects=True
            )
            
            # Optional connection test
            if self.config.extra and self.config.extra.get("test_connection"):
                await self._test_connection()
                
            self._connected = True
            logger.info(f"Connected to HTTP server at {self.config.url}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to HTTP server: {e}")
            
    async def disconnect(self) -> None:
        """Close HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
            
        self._connected = False
        logger.info("Disconnected from HTTP server")
        
    async def send(self, message: Message) -> Optional[Message]:
        """
        Send message over HTTP.
        
        Args:
            message: Message to send
            
        Returns:
            Response message if request, None if notification
        """
        if not self._connected or not self._client:
            raise ConnectionError("Not connected to server")
            
        try:
            # Prepare request based on message type
            is_notification = message.type == MessageType.NOTIFICATION
            
            # Use configured content type or default to JSON
            content_type = self.config.extra.get("content_type", "application/json") if self.config.extra else "application/json"
            
            # Serialize payload
            if content_type == "application/json":
                body = json.dumps(message.payload)
            else:
                body = message.payload
                
            # Send HTTP request
            http_response = await self._client.post(
                self._endpoint_path,
                content=body,
                headers={"Content-Type": content_type},
                timeout=5.0 if is_notification else self.config.timeout
            )
            
            # For notifications, we don't process response
            if is_notification:
                return None
                
            # Check HTTP status
            if http_response.status_code >= 400:
                error_text = http_response.text
                raise ConnectionError(
                    f"HTTP error {http_response.status_code}: {error_text}"
                )
                
            # Parse response based on content type
            response_content_type = http_response.headers.get("content-type", "")
            
            if "application/json" in response_content_type:
                try:
                    response_data = http_response.json()
                except json.JSONDecodeError as e:
                    raise ConnectionError(f"Invalid JSON response: {e}")
            else:
                response_data = http_response.text
                
            # Create response message
            return Message(
                id=message.id,
                type=MessageType.RESPONSE,
                payload=response_data,
                metadata={"status_code": http_response.status_code}
            )
            
        except httpx.TimeoutException:
            raise TimeoutError(f"Request timeout")
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP error: {e}")
            
    async def receive(self) -> Message:
        """
        Receive message over HTTP.
        
        Note: HTTP is request-response, so this is not typically used.
        """
        raise NotImplementedError("HTTP transport doesn't support receiving messages")
        
    async def _test_connection(self) -> None:
        """Test connection with a simple request."""
        health_endpoint = self.config.extra.get("health_endpoint", "/health")
        
        try:
            response = await self._client.get(health_endpoint, timeout=5.0)
            if response.status_code == 404:
                # Health endpoint doesn't exist, that's OK
                pass
            elif response.status_code >= 400:
                logger.warning(f"Health check returned {response.status_code}")
        except Exception:
            # Health check is optional
            pass
            
    def set_endpoint(self, endpoint: str) -> None:
        """
        Set custom endpoint path.
        
        Args:
            endpoint: Endpoint path (e.g., "/api/rpc")
        """
        self._endpoint_path = endpoint
        
    async def request(
        self, 
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make arbitrary HTTP request.
        
        Args:
            method: HTTP method
            path: Request path
            **kwargs: Additional arguments for httpx
            
        Returns:
            HTTP response
        """
        if not self._connected or not self._client:
            raise ConnectionError("Not connected to server")
            
        return await self._client.request(method, path, **kwargs)


# Auto-register HTTP transports
TransportRegistry.register("http", HTTPTransport)
TransportRegistry.register("https", HTTPTransport)
