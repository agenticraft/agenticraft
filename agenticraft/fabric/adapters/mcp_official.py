"""
MCP Official SDK Adapter - Updated for current MCP SDK (1.9+).

Uses the official Model Context Protocol Python SDK.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from ..protocol_types import IProtocolAdapter, ProtocolType, ProtocolCapability

@dataclass 
class ToolInfo:
    """Information about a tool."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    from mcp.types import (
        Tool, 
        TextContent, 
        CallToolRequest,
        CallToolResult,
        Resource,
        Prompt,
        CreateMessageRequest,
        CreateMessageResult
    )
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    ClientSession = None


class MCPOfficialAdapter(IProtocolAdapter):
    """
    Adapter for Model Context Protocol using the official SDK.
    
    Installation:
        pip install mcp
        # or with CLI tools
        pip install "mcp[cli]"
    
    Features:
        - Full tool discovery and execution
        - Resource management
        - Prompt templates
        - Streaming support
        - Multiple transport support (stdio, SSE, HTTP)
    """
    
    def __init__(self):
        if not MCP_SDK_AVAILABLE:
            raise ImportError(
                "MCP SDK not installed. Install with: pip install 'mcp[cli]'"
            )
        self.session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._transport_type: Optional[str] = None
        self._tools_cache: Dict[str, Tool] = {}
        self._resources_cache: Dict[str, Resource] = {}
        self._prompts_cache: Dict[str, Prompt] = {}
        self._connected = False
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.MCP
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to MCP server using official SDK."""
        transport = config.get("transport", "stdio")
        self._transport_type = transport
        
        if transport == "stdio":
            # stdio transport for local servers
            server_params = StdioServerParameters(
                command=config.get("command", "python"),
                args=config.get("args", []),
                env=config.get("env", {})
            )
            
            # Create stdio connection
            self._read_stream, self._write_stream = await stdio_client(server_params)
            
        elif transport == "sse":
            # SSE transport for HTTP servers
            url = config.get("url")
            if not url:
                raise ValueError("SSE transport requires 'url' in config")
            
            headers = config.get("headers", {})
            # Create SSE connection
            self._read_stream, self._write_stream = await sse_client(
                url, 
                headers=headers
            )
            
        else:
            raise ValueError(f"Unsupported transport: {transport}")
        
        # Handle sampling callback if provided
        sampling_callback = None
        if "sampling_callback" in config:
            sampling_callback = config["sampling_callback"]
        
        # Create client session
        self.session = ClientSession(
            self._read_stream, 
            self._write_stream,
            sampling_callback=sampling_callback
        )
        
        # Initialize the session
        init_params = config.get("client_info", {
            "name": "agenticraft",
            "version": "1.0.0"
        })
        
        await self.session.initialize(**init_params)
        self._connected = True
        
        # Cache available capabilities
        await self._cache_capabilities()
    
    async def _cache_capabilities(self) -> None:
        """Cache tools, resources, and prompts for faster access."""
        if not self._connected:
            return
            
        # Cache tools
        tools_response = await self.session.list_tools()
        if tools_response and hasattr(tools_response, 'tools'):
            self._tools_cache = {
                tool.name: tool for tool in tools_response.tools
            }
        
        # Cache resources
        resources_response = await self.session.list_resources()
        if resources_response and hasattr(resources_response, 'resources'):
            self._resources_cache = {
                res.uri: res for res in resources_response.resources
            }
        
        # Cache prompts
        prompts_response = await self.session.list_prompts()
        if prompts_response and hasattr(prompts_response, 'prompts'):
            self._prompts_cache = {
                prompt.name: prompt for prompt in prompts_response.prompts
            }
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.session and self._connected:
            # Close session - the SDK doesn't have explicit close, 
            # but we can clean up our state
            self._connected = False
            
            # Clear caches
            self._tools_cache.clear()
            self._resources_cache.clear()
            self._prompts_cache.clear()
            
            # Clear streams
            self._read_stream = None
            self._write_stream = None
            self.session = None
    
    async def discover_tools(self) -> List[ToolInfo]:
        """Discover available tools from the MCP server."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        # Refresh cache to get latest tools
        await self._cache_capabilities()
        
        tools = []
        for tool_name, tool in self._tools_cache.items():
            tools.append(ToolInfo(
                name=tool_name,
                description=tool.description or "",
                parameters=tool.inputSchema if hasattr(tool, 'inputSchema') else {}
            ))
        
        return tools
    
    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a tool using the official SDK."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        if tool_name not in self._tools_cache:
            # Refresh cache in case new tools were added
            await self._cache_capabilities()
            
        if tool_name not in self._tools_cache:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Call tool through session
        result = await self.session.call_tool(
            tool_name,
            arguments=arguments or {}
        )
        
        # Handle different result types
        if isinstance(result, CallToolResult):
            if result.content:
                # Extract text content if available
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        return content_item.text
                    elif isinstance(content_item, dict) and 'text' in content_item:
                        return content_item['text']
                # Return raw content if not text
                return result.content
            return None
        
        # Handle direct response
        if hasattr(result, 'content'):
            return result.content
        
        return result
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        # Refresh cache
        await self._cache_capabilities()
        
        return [
            {
                "uri": uri,
                "name": res.name if hasattr(res, 'name') else uri,
                "description": res.description if hasattr(res, 'description') else "",
                "mimeType": res.mimeType if hasattr(res, 'mimeType') else "text/plain"
            }
            for uri, res in self._resources_cache.items()
        ]
    
    async def read_resource(self, uri: str) -> Any:
        """Read a specific resource."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self.session.read_resource(uri)
        
        # Extract content from result
        if hasattr(result, 'contents'):
            contents = []
            for content_item in result.contents:
                if hasattr(content_item, 'text'):
                    contents.append(content_item.text)
                elif isinstance(content_item, dict) and 'text' in content_item:
                    contents.append(content_item['text'])
                else:
                    contents.append(str(content_item))
            return "\n".join(contents) if len(contents) > 1 else contents[0] if contents else ""
        
        # Handle direct content
        if hasattr(result, 'content'):
            return result.content
        
        return result
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompt templates."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        # Refresh cache
        await self._cache_capabilities()
        
        return [
            {
                "name": name,
                "description": prompt.description if hasattr(prompt, 'description') else "",
                "arguments": prompt.arguments if hasattr(prompt, 'arguments') else []
            }
            for name, prompt in self._prompts_cache.items()
        ]
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Get a prompt with filled arguments."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self.session.get_prompt(name, arguments)
        
        # Extract text from messages
        if hasattr(result, 'messages'):
            message_texts = []
            for msg in result.messages:
                if hasattr(msg, 'content'):
                    if hasattr(msg.content, 'text'):
                        message_texts.append(msg.content.text)
                    elif isinstance(msg.content, str):
                        message_texts.append(msg.content)
                    elif isinstance(msg.content, dict) and 'text' in msg.content:
                        message_texts.append(msg.content['text'])
                    else:
                        message_texts.append(str(msg.content))
            return "\n".join(message_texts)
        
        # Handle direct content
        if hasattr(result, 'content'):
            return result.content
        
        return str(result)
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get MCP protocol capabilities."""
        capabilities = []
        
        # Basic MCP capabilities
        if self._connected:
            capabilities.append(ProtocolCapability(
                name="tools",
                description="Tool discovery and execution",
                protocol=ProtocolType.MCP
            ))
            
            capabilities.append(ProtocolCapability(
                name="resources",
                description="Resource management",
                protocol=ProtocolType.MCP
            ))
            
            capabilities.append(ProtocolCapability(
                name="prompts",
                description="Prompt template support",
                protocol=ProtocolType.MCP
            ))
            
            capabilities.append(ProtocolCapability(
                name="streaming",
                description="Streaming support",
                protocol=ProtocolType.MCP,
                metadata={"transport": self._transport_type}
            ))
            
            # Add tool discovery capability if tools are cached
            if self._tools_cache:
                capabilities.append(ProtocolCapability(
                    name="tool_discovery",
                    description="Dynamic tool discovery",
                    protocol=ProtocolType.MCP,
                    metadata={"tool_count": len(self._tools_cache)}
                ))
        
        return capabilities
    
    def supports_feature(self, feature: str) -> bool:
        """Check if adapter supports a specific feature."""
        return feature in {
            'tools', 'resources', 'prompts', 'streaming',
            'schema_validation', 'stdio', 'sse', 'http',
            'sampling'
        }
    
    # Additional methods for advanced features
    
    async def create_message(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Use sampling/completion if server supports it."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        # Check if session has sampling callback
        if not hasattr(self.session, '_sampling_callback') or not self.session._sampling_callback:
            raise RuntimeError("No sampling callback configured")
        
        # This requires server support for sampling
        result = await self.session.create_message(
            messages=messages,
            **kwargs
        )
        
        return {
            "role": result.role if hasattr(result, 'role') else 'assistant',
            "content": result.content.text if hasattr(result.content, 'text') else str(result.content),
            "model": result.model if hasattr(result, 'model') else None,
            "stopReason": result.stopReason if hasattr(result, 'stopReason') else None
        }
    
    async def subscribe_to_resource(self, uri: str) -> Any:
        """Subscribe to resource updates if supported."""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        # This is a placeholder for future MCP features
        # The current SDK doesn't have explicit subscription support
        raise NotImplementedError("Resource subscription not yet supported in MCP SDK")


class MCPHybridAdapter(MCPOfficialAdapter):
    """
    Hybrid adapter that can fall back to custom implementation.
    
    This allows gradual migration and handles cases where the official
    SDK might not support all features yet.
    """
    
    def __init__(self, fallback_adapter=None):
        self.fallback_adapter = fallback_adapter
        self._use_official = True
        
        try:
            super().__init__()
        except ImportError:
            if not self.fallback_adapter:
                raise
            self._use_official = False
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect with fallback support."""
        if self._use_official:
            try:
                await super().connect(config)
            except Exception as e:
                if self.fallback_adapter:
                    print(f"Official SDK failed: {e}, falling back to custom")
                    self._use_official = False
                    await self.fallback_adapter.connect(config)
                else:
                    raise
        else:
            await self.fallback_adapter.connect(config)
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get capabilities with fallback support."""
        if self._use_official:
            try:
                return await super().get_capabilities()
            except Exception:
                if self.fallback_adapter:
                    return await self.fallback_adapter.get_capabilities()
                raise
        else:
            if self.fallback_adapter:
                return await self.fallback_adapter.get_capabilities()
            return []
    
    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute with fallback for unsupported features."""
        if self._use_official:
            try:
                return await super().execute_tool(tool_name, arguments)
            except NotImplementedError:
                if self.fallback_adapter:
                    return await self.fallback_adapter.execute_tool(
                        tool_name, arguments
                    )
                raise
        else:
            return await self.fallback_adapter.execute_tool(tool_name, arguments)
