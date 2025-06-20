"""
Protocol client and server stubs for compatibility.

These are temporary stubs to allow imports to work until the actual
implementations are created.
"""
from typing import Any, Dict, List, Optional


class MCPClient:
    """Stub for MCP client."""
    
    def __init__(self, url: str, **options):
        self.url = url
        self.options = options
        self.server_info = None
        
    async def connect(self):
        """Connect to MCP server."""
        pass
        
    async def disconnect(self):
        """Disconnect from server."""
        pass
        
    def get_tools(self):
        """Get available tools."""
        return []
        
    async def call_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Call a tool."""
        return {"result": "stub"}


class MCPServer:
    """Stub for MCP server."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        
    async def start(self):
        """Start server."""
        pass
        
    async def stop(self):
        """Stop server."""
        pass


class A2AClient:
    """Stub for A2A client."""
    
    def __init__(self, url: str, **options):
        self.url = url
        self.options = options
        
    async def connect(self):
        """Connect to A2A network."""
        pass
        
    async def disconnect(self):
        """Disconnect from network."""
        pass
        
    async def discover_agents(self) -> List[Any]:
        """Discover agents."""
        return []
        
    async def send_task(self, agent_id: str, skill: str, params: Dict[str, Any]) -> Any:
        """Send task to agent."""
        return {"status": "completed"}


class A2AServer:
    """Stub for A2A server."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        
    async def start(self):
        """Start server."""
        pass
        
    async def stop(self):
        """Stop server."""
        pass
