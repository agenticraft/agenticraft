"""
MCP adapter for AgentiCraft fabric.

This module provides the adapter implementation for MCP protocol.
"""
import logging
from typing import Any, Dict, Optional, List

from .base import ProtocolAdapter
from ...protocols.mcp import MCPProtocol, MCPTool, MCPResource, MCPPrompt

logger = logging.getLogger(__name__)


class MCPAdapter(ProtocolAdapter):
    """
    Adapter for MCP (Model Context Protocol).
    
    This adapter provides a unified interface for MCP protocol
    within the fabric layer.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize MCP adapter."""
        super().__init__(*args, **kwargs)
        
        # Ensure protocol is MCPProtocol
        if not isinstance(self.protocol, MCPProtocol):
            raise TypeError("MCPAdapter requires MCPProtocol instance")
            
    async def _initialize_protocol(self, config: Dict[str, Any]) -> None:
        """Initialize MCP protocol."""
        # Register tools if provided
        tools = config.get("tools", [])
        for tool in tools:
            if isinstance(tool, MCPTool):
                self.protocol.register_tool(tool)
                
        # Register resources if provided
        resources = config.get("resources", [])
        for resource in resources:
            if isinstance(resource, MCPResource):
                self.protocol.register_resource(resource)
                
        # Register prompts if provided
        prompts = config.get("prompts", [])
        for prompt in prompts:
            if isinstance(prompt, MCPPrompt):
                self.protocol.register_prompt(prompt)
                
        # Start protocol
        await self.protocol.start()
        
    async def send_message(
        self,
        message: Any,
        target: Optional[str] = None
    ) -> Any:
        """Send message via MCP."""
        return await self.protocol.send(message, target)
        
    async def receive_message(self) -> Any:
        """Receive message from MCP."""
        return await self.protocol.receive()
        
    def get_protocol_name(self) -> str:
        """Get protocol name."""
        return "mcp"
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Get MCP capabilities."""
        return {
            "tools": True,
            "resources": True,
            "prompts": True,
            "version": self.protocol.config.version
        }
        
    # MCP-specific methods
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        return await self.protocol.request(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        response = await self.protocol.request(
            method="tools/list",
            params={}
        )
        
        return response.get("tools", [])
        
    async def read_resource(self, uri: str) -> Any:
        """
        Read an MCP resource.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        return await self.protocol.request(
            method="resources/read",
            params={"uri": uri}
        )
        
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available MCP resources."""
        response = await self.protocol.request(
            method="resources/list",
            params={}
        )
        
        return response.get("resources", [])
        
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Get an MCP prompt.
        
        Args:
            name: Prompt name
            arguments: Prompt arguments
            
        Returns:
            Rendered prompt
        """
        return await self.protocol.request(
            method="prompts/get",
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )
        
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available MCP prompts."""
        response = await self.protocol.request(
            method="prompts/list",
            params={}
        )
        
        return response.get("prompts", [])
        
    async def initialize_session(self) -> Dict[str, Any]:
        """Initialize MCP session."""
        return await self.protocol.request(
            method="initialize",
            params={
                "clientInfo": {
                    "name": "AgentiCraft",
                    "version": "1.0.0"
                }
            }
        )
        
    def register_tool(self, tool: MCPTool) -> None:
        """Register a tool with MCP."""
        self.protocol.register_tool(tool)
        
    def register_resource(self, resource: MCPResource) -> None:
        """Register a resource with MCP."""
        self.protocol.register_resource(resource)
        
    def register_prompt(self, prompt: MCPPrompt) -> None:
        """Register a prompt with MCP."""
        self.protocol.register_prompt(prompt)
