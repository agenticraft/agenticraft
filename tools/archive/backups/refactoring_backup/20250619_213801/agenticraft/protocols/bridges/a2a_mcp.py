"""
Bridge between A2A and MCP protocols.

This module provides bidirectional translation between
Agent-to-Agent and Model Context Protocol messages.
"""
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from .base import ProtocolBridge
from ..a2a import Message as A2AMessage, MessageType as A2AMessageType
from ..mcp import MCPRequest, MCPResponse

logger = logging.getLogger(__name__)


class A2AMCPBridge(ProtocolBridge):
    """
    Bridge between A2A and MCP protocols.
    
    This bridge enables agents using A2A protocol to communicate
    with MCP servers and vice versa.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize A2A-MCP bridge."""
        super().__init__(*args, **kwargs)
        
        # Method mapping
        self._a2a_to_mcp_methods = {
            "call_tool": "tools/call",
            "list_tools": "tools/list",
            "read_resource": "resources/read",
            "list_resources": "resources/list",
            "get_prompt": "prompts/get",
            "list_prompts": "prompts/list"
        }
        
        self._mcp_to_a2a_methods = {
            v: k for k, v in self._a2a_to_mcp_methods.items()
        }
        
    async def translate_a_to_b(self, message: Any) -> Any:
        """Translate A2A message to MCP format."""
        if isinstance(message, A2AMessage):
            # Extract payload
            payload = message.payload
            
            if isinstance(payload, dict):
                # Check for method call
                if "method" in payload:
                    method = payload["method"]
                    
                    # Map A2A method to MCP method
                    mcp_method = self._a2a_to_mcp_methods.get(method, method)
                    
                    # Create MCP request
                    return MCPRequest(
                        jsonrpc="2.0",
                        id=message.id,
                        method=mcp_method,
                        params=payload.get("params", {})
                    )
                    
                # Check for tool call pattern
                elif "tool" in payload:
                    return MCPRequest(
                        jsonrpc="2.0",
                        id=message.id,
                        method="tools/call",
                        params={
                            "name": payload["tool"],
                            "arguments": payload.get("arguments", {})
                        }
                    )
                    
        # Default: wrap in MCP request
        return MCPRequest(
            jsonrpc="2.0",
            id=str(uuid4()),
            method="a2a/message",
            params={"message": message}
        )
        
    async def translate_b_to_a(self, message: Any) -> Any:
        """Translate MCP message to A2A format."""
        if isinstance(message, MCPRequest):
            # Map MCP method to A2A
            method = message.method
            a2a_method = self._mcp_to_a2a_methods.get(method, method)
            
            # Create A2A message
            return A2AMessage(
                id=message.id or str(uuid4()),
                source="mcp_bridge",
                target=None,
                type=A2AMessageType.REQUEST,
                payload={
                    "method": a2a_method,
                    "params": message.params
                }
            )
            
        elif isinstance(message, MCPResponse):
            # Convert response
            if message.is_error:
                payload = {
                    "error": {
                        "code": message.error.code,
                        "message": message.error.message,
                        "data": message.error.data
                    }
                }
            else:
                payload = {"result": message.result}
                
            return A2AMessage(
                id=message.id or str(uuid4()),
                source="mcp_bridge",
                target=None,
                type=A2AMessageType.RESPONSE,
                payload=payload
            )
            
        # Default: wrap in A2A message
        return A2AMessage(
            id=str(uuid4()),
            source="mcp_bridge",
            target=None,
            type=A2AMessageType.REQUEST,
            payload=message
        )
        
    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        source_protocol: str
    ) -> Any:
        """
        Handle tool call across protocols.
        
        Args:
            tool_name: Tool to call
            arguments: Tool arguments
            source_protocol: Protocol making the call
            
        Returns:
            Tool execution result
        """
        if source_protocol == "a2a":
            # A2A agent calling MCP tool
            request = MCPRequest(
                jsonrpc="2.0",
                id=str(uuid4()),
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            response = await self.protocol_b.send(request)
            
            if isinstance(response, MCPResponse):
                if response.is_error:
                    raise Exception(response.error.message)
                return response.result
                
        elif source_protocol == "mcp":
            # MCP calling A2A tool
            message = A2AMessage(
                id=str(uuid4()),
                source="mcp_bridge",
                target=None,
                type=A2AMessageType.REQUEST,
                payload={
                    "method": "call_tool",
                    "params": {
                        "tool": tool_name,
                        "arguments": arguments
                    }
                }
            )
            
            return await self.protocol_a.send(message)
            
        return None
        
    async def discover_capabilities(self) -> Dict[str, Any]:
        """
        Discover capabilities of both protocols.
        
        Returns:
            Combined capabilities from both protocols
        """
        capabilities = {
            "a2a": {},
            "mcp": {}
        }
        
        # Discover A2A capabilities
        try:
            a2a_response = await self.protocol_a.send({
                "method": "discover",
                "params": {}
            })
            capabilities["a2a"] = a2a_response
        except Exception as e:
            logger.error(f"Failed to discover A2A capabilities: {e}")
            
        # Discover MCP capabilities
        try:
            mcp_response = await self.protocol_b.request(
                method="initialize",
                params={}
            )
            capabilities["mcp"] = mcp_response
        except Exception as e:
            logger.error(f"Failed to discover MCP capabilities: {e}")
            
        return capabilities
