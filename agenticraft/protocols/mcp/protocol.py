"""
MCP Protocol implementation using core abstractions.

This module provides the refactored MCP protocol that uses
the core transport, auth, and registry abstractions.
"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional, List, Union
from uuid import uuid4

from ..base import RequestResponseProtocol, ProtocolConfig
from ...core.transport import Transport, Message, MessageType
from ...core.auth import AuthManager
from ...core.registry import ServiceRegistry

from .types import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPErrorCode,
    MCPTool,
    MCPResource,
    MCPPrompt
)

logger = logging.getLogger(__name__)


class MCPProtocol(RequestResponseProtocol):
    """
    MCP (Model Context Protocol) implementation.
    
    This protocol provides tool calling, resource management,
    and prompt capabilities for AI models.
    """
    
    def __init__(
        self,
        transport: Optional[Transport] = None,
        auth: Optional[AuthManager] = None,
        registry: Optional[ServiceRegistry] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize MCP protocol."""
        protocol_config = ProtocolConfig(
            name="mcp",
            version="1.0",
            metadata=config or {}
        )
        
        super().__init__(
            config=protocol_config,
            transport=transport,
            auth=auth,
            registry=registry
        )
        
        # MCP-specific state
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, MCPPrompt] = {}
        
        # Setup default handlers
        self._setup_handlers()
        
    def _setup_handlers(self) -> None:
        """Setup default MCP handlers."""
        self.add_handler("initialize", self._handle_initialize)
        self.add_handler("tools/list", self._handle_list_tools)
        self.add_handler("tools/call", self._handle_call_tool)
        self.add_handler("resources/list", self._handle_list_resources)
        self.add_handler("resources/read", self._handle_read_resource)
        self.add_handler("prompts/list", self._handle_list_prompts)
        self.add_handler("prompts/get", self._handle_get_prompt)
        
    async def start(self) -> None:
        """Start MCP protocol."""
        if self._running:
            return
            
        # Connect transport if provided
        if self.transport:
            await self.transport.connect()
            self.transport.on_message(self._handle_transport_message)
            
        self._running = True
        logger.info("MCP protocol started")
        
    async def stop(self) -> None:
        """Stop MCP protocol."""
        if not self._running:
            return
            
        # Cleanup pending requests
        await self._cleanup_pending_requests()
        
        # Disconnect transport
        if self.transport:
            await self.transport.disconnect()
            
        self._running = False
        logger.info("MCP protocol stopped")
        
    async def send(
        self,
        message: Any,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Send MCP message."""
        if isinstance(message, dict):
            # Check if it's a request
            if "method" in message:
                return await self.request(
                    method=message["method"],
                    params=message.get("params"),
                    target=target,
                    timeout=timeout
                )
            else:
                # Send as generic message
                transport_message = Message(
                    id=str(uuid4()),
                    type=MessageType.REQUEST,
                    payload=message
                )
                
                response = await self.transport.send(transport_message)
                if response:
                    return response.payload
                    
        raise ValueError(f"Unsupported message type: {type(message)}")
        
    async def receive(self, timeout: Optional[float] = None) -> Any:
        """Receive MCP message."""
        if not self.transport:
            raise RuntimeError("No transport configured")
            
        transport_message = await self.transport.receive()
        return transport_message.payload
        
    async def request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Send MCP request and wait for response."""
        if not self.transport:
            raise RuntimeError("No transport configured")
            
        # Create request
        request_id = self._create_request_id()
        request = MCPRequest(
            jsonrpc="2.0",
            id=request_id,
            method=method,
            params=params or {}
        )
        
        # Store pending request
        future = self._store_pending_request(request_id)
        
        try:
            # Send request
            transport_message = Message(
                id=request_id,
                type=MessageType.REQUEST,
                payload=request.to_dict()
            )
            
            await self.transport.send(transport_message)
            
            # Wait for response
            response = await asyncio.wait_for(
                future,
                timeout=timeout or self.transport.config.timeout
            )
            
            if response.is_error:
                raise Exception(response.error.message)
                
            return response.result
            
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request timeout: {method}")
            
    async def notify(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None
    ) -> None:
        """Send MCP notification."""
        if not self.transport:
            raise RuntimeError("No transport configured")
            
        # Create notification (no ID)
        notification = MCPRequest(
            jsonrpc="2.0",
            id=None,
            method=method,
            params=params or {}
        )
        
        # Send notification
        transport_message = Message(
            id=None,
            type=MessageType.NOTIFICATION,
            payload=notification.to_dict()
        )
        
        await self.transport.send(transport_message)
        
    async def _handle_transport_message(self, message: Message) -> None:
        """Handle message from transport."""
        try:
            payload = message.payload
            
            # Check if it's a response
            if message.type == MessageType.RESPONSE and message.id:
                response = MCPResponse(**payload)
                self._complete_pending_request(message.id, response)
                
            # Check if it's a request
            elif message.type == MessageType.REQUEST:
                request = MCPRequest(**payload)
                
                # Handle request
                try:
                    result = await self._handle_request(request)
                    
                    # Send response
                    response = MCPResponse(
                        jsonrpc="2.0",
                        id=request.id,
                        result=result
                    )
                    
                    response_message = Message(
                        id=message.id,
                        type=MessageType.RESPONSE,
                        payload=response.to_dict()
                    )
                    
                    await self.transport.send(response_message)
                    
                except Exception as e:
                    # Send error response
                    error_response = MCPResponse(
                        jsonrpc="2.0",
                        id=request.id,
                        error=MCPError(
                            code=MCPErrorCode.INTERNAL_ERROR,
                            message=str(e)
                        )
                    )
                    
                    response_message = Message(
                        id=message.id,
                        type=MessageType.RESPONSE,
                        payload=error_response.to_dict()
                    )
                    
                    await self.transport.send(response_message)
                    
        except Exception as e:
            logger.error(f"Error handling transport message: {e}")
            
    async def _handle_request(self, request: MCPRequest) -> Any:
        """Handle incoming MCP request."""
        handler = self._handlers.get(request.method)
        if not handler:
            raise ValueError(f"Unknown method: {request.method}")
            
        return await handler(request.params)
        
    # MCP-specific methods
    
    def register_tool(self, tool: MCPTool) -> None:
        """Register an MCP tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered MCP tool: {tool.name}")
        
    def register_resource(self, resource: MCPResource) -> None:
        """Register an MCP resource."""
        self._resources[resource.uri] = resource
        logger.info(f"Registered MCP resource: {resource.uri}")
        
    def register_prompt(self, prompt: MCPPrompt) -> None:
        """Register an MCP prompt."""
        self._prompts[prompt.name] = prompt
        logger.info(f"Registered MCP prompt: {prompt.name}")
        
    # Default handlers
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            "protocolVersion": self.config.version,
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True
            },
            "serverInfo": {
                "name": "AgentiCraft MCP Server",
                "version": "1.0.0"
            }
        }
        
    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "tools": [
                tool.to_json_schema()
                for tool in self._tools.values()
            ]
        }
        
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        if not tool_name:
            raise ValueError("Tool name required")
            
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        # Tool execution would be implemented here
        # For now, return placeholder
        return {
            "content": [{
                "type": "text",
                "text": f"Tool {tool_name} called with params: {params.get('arguments', {})}"
            }]
        }
        
    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {
            "resources": [
                resource.to_dict()
                for resource in self._resources.values()
            ]
        }
        
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        if not uri:
            raise ValueError("Resource URI required")
            
        resource = self._resources.get(uri)
        if not resource:
            raise ValueError(f"Unknown resource: {uri}")
            
        # Resource reading would be implemented here
        return {
            "contents": [{
                "uri": uri,
                "mimeType": resource.mime_type or "text/plain",
                "text": f"Content of resource: {uri}"
            }]
        }
        
    async def _handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        return {
            "prompts": [
                prompt.to_dict()
                for prompt in self._prompts.values()
            ]
        }
        
    async def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        name = params.get("name")
        if not name:
            raise ValueError("Prompt name required")
            
        prompt = self._prompts.get(name)
        if not prompt:
            raise ValueError(f"Unknown prompt: {name}")
            
        # Prompt rendering would be implemented here
        return {
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"Rendered prompt: {name}"
                }
            }]
        }
