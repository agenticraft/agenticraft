"""
HTTP transport implementation for MCP protocol.

This module provides HTTP/HTTPS transport for MCP,
suitable for request-response style communication.
"""
import json
import logging
from typing import Dict, Any, Optional

import httpx

from .base import IMCPTransport, ConnectionError, TimeoutError
from ..types import MCPRequest, MCPResponse, MCPError, MCPErrorCode

logger = logging.getLogger(__name__)


class HTTPTransport(IMCPTransport):
    """HTTP transport for MCP protocol."""
    
    def __init__(self, config):
        """Initialize HTTP transport."""
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None
        self._rpc_endpoint = "/rpc"  # Default JSON-RPC endpoint
        
    async def connect(self) -> None:
        """Establish HTTP client connection."""
        try:
            # Parse base URL
            base_url = self.config.url
            if not base_url.endswith("/"):
                base_url += "/"
                
            # Create HTTP client
            self._client = httpx.AsyncClient(
                base_url=base_url,
                headers=self.config.headers,
                timeout=httpx.Timeout(self.config.timeout),
                follow_redirects=True
            )
            
            # Test connection with a simple request
            # Some servers might have a health endpoint
            try:
                response = await self._client.get("/health", timeout=5.0)
                if response.status_code == 404:
                    # Health endpoint doesn't exist, that's OK
                    pass
                elif response.status_code >= 400:
                    logger.warning(f"Health check returned {response.status_code}")
            except Exception:
                # Health check is optional
                pass
                
            self._connected = True
            logger.info(f"Connected to MCP HTTP server at {self.config.url}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to HTTP server: {e}")
            
    async def disconnect(self) -> None:
        """Close HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
            
        self._connected = False
        logger.info("Disconnected from MCP HTTP server")
        
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """
        Send HTTP request and wait for response.
        
        Args:
            request: MCP request to send
            
        Returns:
            MCP response
            
        Raises:
            ConnectionError: If not connected
            TimeoutError: If request times out
        """
        if not self._connected or not self._client:
            raise ConnectionError("Not connected to MCP server")
            
        try:
            # Send JSON-RPC request
            http_response = await self._client.post(
                self._rpc_endpoint,
                json=request.to_dict(),
                headers={"Content-Type": "application/json"}
            )
            
            # Check HTTP status
            if http_response.status_code != 200:
                error_text = http_response.text
                raise ConnectionError(
                    f"HTTP error {http_response.status_code}: {error_text}"
                )
                
            # Parse JSON-RPC response
            try:
                response_data = http_response.json()
            except json.JSONDecodeError as e:
                raise ConnectionError(f"Invalid JSON response: {e}")
                
            # Create MCP response
            if "error" in response_data:
                error_data = response_data["error"]
                error = MCPError(
                    code=MCPErrorCode(error_data.get("code", "internal_error")),
                    message=error_data.get("message", "Unknown error"),
                    data=error_data.get("data")
                )
                response = MCPResponse(
                    jsonrpc=response_data.get("jsonrpc", "2.0"),
                    id=response_data.get("id"),
                    error=error
                )
            else:
                response = MCPResponse(
                    jsonrpc=response_data.get("jsonrpc", "2.0"),
                    id=response_data.get("id"),
                    result=response_data.get("result")
                )
                
            return response
            
        except httpx.TimeoutException:
            raise TimeoutError(f"Request timeout: {request.method}")
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP error: {e}")
            
    async def send_notification(self, request: MCPRequest) -> None:
        """
        Send HTTP notification (fire-and-forget).
        
        Args:
            request: MCP notification to send
        """
        if not self._connected or not self._client:
            raise ConnectionError("Not connected to MCP server")
            
        try:
            # For notifications, we don't wait for response
            # Set a shorter timeout since we don't care about the response
            await self._client.post(
                self._rpc_endpoint,
                json=request.to_dict(),
                headers={"Content-Type": "application/json"},
                timeout=5.0  # Short timeout for notifications
            )
            
        except Exception as e:
            # Log but don't raise for notifications
            logger.warning(f"Notification failed: {e}")
            
    def set_rpc_endpoint(self, endpoint: str) -> None:
        """
        Set custom RPC endpoint path.
        
        Args:
            endpoint: Endpoint path (e.g., "/api/mcp/rpc")
        """
        self._rpc_endpoint = endpoint
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the server.
        
        Returns:
            Health status information
        """
        if not self._connected or not self._client:
            return {"status": "disconnected"}
            
        try:
            # Try common health endpoints
            for endpoint in ["/health", "/api/health", "/status"]:
                try:
                    response = await self._client.get(endpoint, timeout=5.0)
                    if response.status_code == 200:
                        try:
                            return response.json()
                        except:
                            return {"status": "healthy", "endpoint": endpoint}
                except:
                    continue
                    
            # If no health endpoint, try OPTIONS on RPC endpoint
            response = await self._client.options(self._rpc_endpoint, timeout=5.0)
            if response.status_code < 400:
                return {"status": "healthy", "method": "OPTIONS"}
                
            return {"status": "unknown"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Register HTTP transports
from .base import TransportRegistry

TransportRegistry.register("http", HTTPTransport)
TransportRegistry.register("https", HTTPTransport)
