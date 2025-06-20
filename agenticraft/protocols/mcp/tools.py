"""
MCP tool management and integration.

This module provides utilities for managing MCP tools,
converting between MCP and AgentiCraft formats, and
creating tool catalogs.
"""
import json
import logging
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime

from ...core.tool import BaseTool
from ...core.types import ToolDefinition, ToolParameter
from ..a2a.base import Protocol
from .types import MCPTool, MCPToolParameter, MCPCapability
from .client import MCPClient, MCPToolAdapter

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """Extended metadata for MCP tools."""
    
    name: str
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    usage_count: int = 0
    last_used: Optional[datetime] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def update_usage(self) -> None:
        """Update usage statistics."""
        self.usage_count += 1
        self.last_used = datetime.now()


class MCPToolRegistry:
    """Registry for managing MCP tools across multiple servers."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, MCPTool] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._clients: Dict[str, MCPClient] = {}
        self._tool_to_client: Dict[str, str] = {}  # tool_name -> client_url
        
    async def register_client(self, url: str, alias: Optional[str] = None) -> None:
        """
        Register an MCP client and discover its tools.
        
        Args:
            url: MCP server URL
            alias: Optional alias for the client
        """
        client_id = alias or url
        
        try:
            # Create and connect client
            client = MCPClient(url)
            await client.connect()
            
            # Store client
            self._clients[client_id] = client
            
            # Discover and register tools
            tools = client._tools
            for tool_name, tool in tools.items():
                # Handle naming conflicts
                full_name = f"{client_id}.{tool_name}" if tool_name in self._tools else tool_name
                
                self._tools[full_name] = tool
                self._tool_to_client[full_name] = client_id
                self._metadata[full_name] = ToolMetadata(
                    name=full_name,
                    tags=self._extract_tags(tool),
                    category=self._categorize_tool(tool)
                )
                
            logger.info(f"Registered {len(tools)} tools from {client_id}")
            
        except Exception as e:
            logger.error(f"Failed to register client {client_id}: {e}")
            raise
            
    def _extract_tags(self, tool: MCPTool) -> List[str]:
        """Extract tags from tool description."""
        # Simple tag extraction from description
        tags = []
        
        # Common keywords to look for
        keywords = ["file", "network", "data", "api", "search", "compute", "ai", "ml"]
        description_lower = tool.description.lower()
        
        for keyword in keywords:
            if keyword in description_lower:
                tags.append(keyword)
                
        return tags
        
    def _categorize_tool(self, tool: MCPTool) -> str:
        """Categorize tool based on name and description."""
        name_lower = tool.name.lower()
        desc_lower = tool.description.lower()
        
        # Simple categorization logic
        if any(word in name_lower + desc_lower for word in ["file", "read", "write", "save"]):
            return "file_operations"
        elif any(word in name_lower + desc_lower for word in ["http", "api", "request", "fetch"]):
            return "network"
        elif any(word in name_lower + desc_lower for word in ["search", "find", "query"]):
            return "search"
        elif any(word in name_lower + desc_lower for word in ["compute", "calculate", "process"]):
            return "computation"
        else:
            return "general"
            
    async def unregister_client(self, client_id: str) -> None:
        """
        Unregister a client and its tools.
        
        Args:
            client_id: Client identifier
        """
        if client_id not in self._clients:
            return
            
        # Disconnect client
        client = self._clients[client_id]
        await client.disconnect()
        
        # Remove tools
        tools_to_remove = [
            name for name, cid in self._tool_to_client.items()
            if cid == client_id
        ]
        
        for tool_name in tools_to_remove:
            del self._tools[tool_name]
            del self._metadata[tool_name]
            del self._tool_to_client[tool_name]
            
        # Remove client
        del self._clients[client_id]
        
        logger.info(f"Unregistered client {client_id} and {len(tools_to_remove)} tools")
        
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool adapter or None
        """
        if name not in self._tools:
            return None
            
        client_id = self._tool_to_client[name]
        client = self._clients[client_id]
        tool = self._tools[name]
        
        # Update metadata
        self._metadata[name].update_usage()
        
        return MCPToolAdapter(tool, client)
        
    def list_tools(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        client_id: Optional[str] = None
    ) -> List[str]:
        """
        List available tools with optional filtering.
        
        Args:
            category: Filter by category
            tags: Filter by tags (any match)
            client_id: Filter by client
            
        Returns:
            List of tool names
        """
        results = []
        
        for name, tool in self._tools.items():
            # Apply filters
            if client_id and self._tool_to_client[name] != client_id:
                continue
                
            metadata = self._metadata[name]
            
            if category and metadata.category != category:
                continue
                
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
                
            results.append(name)
            
        return sorted(results)
        
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool information or None
        """
        if name not in self._tools:
            return None
            
        tool = self._tools[name]
        metadata = self._metadata[name]
        
        return {
            "name": name,
            "description": tool.description,
            "parameters": [p.dict() for p in tool.parameters],
            "returns": tool.returns,
            "examples": tool.examples,
            "metadata": {
                "version": metadata.version,
                "author": metadata.author,
                "category": metadata.category,
                "tags": metadata.tags,
                "usage_count": metadata.usage_count,
                "last_used": metadata.last_used.isoformat() if metadata.last_used else None
            },
            "client": self._tool_to_client[name]
        }
        
    def search_tools(self, query: str) -> List[str]:
        """
        Search tools by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tool names
        """
        query_lower = query.lower()
        results = []
        
        for name, tool in self._tools.items():
            if (query_lower in name.lower() or 
                query_lower in tool.description.lower()):
                results.append(name)
                
        return sorted(results)
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        # Category counts
        category_counts = {}
        for metadata in self._metadata.values():
            category_counts[metadata.category] = category_counts.get(metadata.category, 0) + 1
            
        # Most used tools
        most_used = sorted(
            [(name, meta.usage_count) for name, meta in self._metadata.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_tools": len(self._tools),
            "total_clients": len(self._clients),
            "categories": category_counts,
            "most_used_tools": most_used,
            "clients": list(self._clients.keys())
        }


class MCPToolCatalog:
    """Catalog for organizing and presenting MCP tools."""
    
    def __init__(self, registry: MCPToolRegistry):
        """
        Initialize tool catalog.
        
        Args:
            registry: Tool registry to use
        """
        self.registry = registry
        
    def generate_markdown(self) -> str:
        """Generate markdown documentation for all tools."""
        lines = ["# MCP Tool Catalog", ""]
        
        # Statistics
        stats = self.registry.get_statistics()
        lines.extend([
            "## Overview",
            f"- Total Tools: {stats['total_tools']}",
            f"- Total Servers: {stats['total_clients']}",
            ""
        ])
        
        # Tools by category
        categories = stats["categories"].keys()
        for category in sorted(categories):
            lines.extend([
                f"## {category.replace('_', ' ').title()}",
                ""
            ])
            
            tools = self.registry.list_tools(category=category)
            for tool_name in tools:
                info = self.registry.get_tool_info(tool_name)
                
                lines.extend([
                    f"### {tool_name}",
                    f"*{info['description']}*",
                    ""
                ])
                
                # Parameters
                if info["parameters"]:
                    lines.append("**Parameters:**")
                    for param in info["parameters"]:
                        required = "required" if param["required"] else "optional"
                        lines.append(f"- `{param['name']}` ({param['type']}, {required}): {param.get('description', '')}")
                    lines.append("")
                    
                # Examples
                if info["examples"]:
                    lines.append("**Examples:**")
                    lines.append("```json")
                    for example in info["examples"]:
                        lines.append(json.dumps(example, indent=2))
                    lines.append("```")
                    lines.append("")
                    
        return "\n".join(lines)
        
    def export_json(self) -> Dict[str, Any]:
        """Export catalog as JSON."""
        tools = {}
        
        for tool_name in self.registry.list_tools():
            tools[tool_name] = self.registry.get_tool_info(tool_name)
            
        return {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "statistics": self.registry.get_statistics(),
            "tools": tools
        }


class MCPToolProtocol(Protocol):
    """A2A protocol for sharing MCP tools between agents."""
    
    def __init__(self, registry: MCPToolRegistry):
        """
        Initialize MCP tool protocol.
        
        Args:
            registry: Tool registry to share
        """
        super().__init__("mcp_tools")
        self.registry = registry
        
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle tool-related messages."""
        msg_type = message.get("type")
        
        if msg_type == "list_tools":
            # List available tools
            filters = message.get("filters", {})
            tools = self.registry.list_tools(**filters)
            return {"tools": tools}
            
        elif msg_type == "get_tool_info":
            # Get tool information
            tool_name = message.get("tool_name")
            info = self.registry.get_tool_info(tool_name)
            return {"tool_info": info}
            
        elif msg_type == "search_tools":
            # Search tools
            query = message.get("query", "")
            results = self.registry.search_tools(query)
            return {"results": results}
            
        elif msg_type == "execute_tool":
            # Execute tool (requires proper authorization)
            tool_name = message.get("tool_name")
            arguments = message.get("arguments", {})
            
            tool = self.registry.get_tool(tool_name)
            if tool:
                try:
                    result = await tool.arun(**arguments)
                    return {"result": result, "success": True}
                except Exception as e:
                    return {"error": str(e), "success": False}
            else:
                return {"error": f"Tool not found: {tool_name}", "success": False}
                
        return None


# Global tool registry
_global_registry = MCPToolRegistry()


def get_global_registry() -> MCPToolRegistry:
    """Get the global MCP tool registry."""
    return _global_registry


async def register_mcp_server(url: str, alias: Optional[str] = None) -> None:
    """
    Register an MCP server with the global registry.
    
    Args:
        url: MCP server URL
        alias: Optional alias for the server
    """
    await _global_registry.register_client(url, alias)


def list_mcp_tools(**filters) -> List[str]:
    """List available MCP tools from all registered servers."""
    return _global_registry.list_tools(**filters)


def get_mcp_tool(name: str) -> Optional[BaseTool]:
    """Get an MCP tool by name."""
    return _global_registry.get_tool(name)


def create_mcp_tool(
    name: str,
    description: str,
    func: Optional[Any] = None,
    parameters: Optional[List[MCPToolParameter]] = None
) -> MCPTool:
    """
    Create an MCP tool definition.
    
    Args:
        name: Tool name
        description: Tool description
        func: Optional function to wrap
        parameters: Tool parameters
        
    Returns:
        MCP tool definition
    """
    if parameters is None and func is not None:
        # Extract parameters from function signature
        import inspect
        sig = inspect.signature(func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
                
            # Get type annotation
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                type_map = {
                    int: "integer",
                    float: "number",
                    str: "string",
                    bool: "boolean",
                    list: "array",
                    dict: "object"
                }
                param_type = type_map.get(param.annotation, "string")
                
            # Check if required
            required = param.default == inspect.Parameter.empty
            
            parameters.append(MCPToolParameter(
                name=param_name,
                type=param_type,
                description=f"Parameter {param_name}",
                required=required,
                default=None if required else param.default
            ))
    
    return MCPTool(
        name=name,
        description=description,
        parameters=parameters or []
    )


def tool_to_mcp(tool: BaseTool) -> MCPTool:
    """
    Convert an AgentiCraft tool to MCP format.
    
    Args:
        tool: AgentiCraft tool
        
    Returns:
        MCP tool definition
    """
    definition = tool.get_definition()
    
    # Convert parameters
    mcp_params = []
    for param in definition.parameters:
        mcp_params.append(MCPToolParameter(
            name=param.name,
            type=param.type,
            description=param.description,
            required=param.required,
            default=param.default,
            enum=param.enum if hasattr(param, "enum") else None
        ))
    
    return MCPTool(
        name=definition.name,
        description=definition.description,
        parameters=mcp_params
    )


def mcp_to_tool(mcp_tool: MCPTool, client: Optional[MCPClient] = None) -> BaseTool:
    """
    Convert an MCP tool to AgentiCraft format.
    
    Args:
        mcp_tool: MCP tool definition
        client: Optional MCP client for execution
        
    Returns:
        AgentiCraft tool
    """
    if client:
        # Return adapter that can execute via client
        return MCPToolAdapter(mcp_tool, client)
    else:
        # Return a stub tool that just has the definition
        from ...core.tool import FunctionTool
        
        async def stub_func(**kwargs):
            raise NotImplementedError(
                f"Tool {mcp_tool.name} requires an MCP client for execution"
            )
        
        return FunctionTool(
            func=stub_func,
            name=mcp_tool.name,
            description=mcp_tool.description
        )
