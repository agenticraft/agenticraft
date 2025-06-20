"""
MCP Server Builder - Easy creation of MCP servers for AgentiCraft agents.

This module provides:
1. Simple decorators for creating MCP tools, resources, and prompts
2. Automatic server setup with multiple transport options
3. Integration with AgentiCraft agents
4. Testing utilities
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path

from agenticraft.core.agent import Agent

logger = logging.getLogger(__name__)

# Try to import MCP SDK
try:
    from mcp.server.fastmcp import FastMCP
    from mcp import types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None
    types = None
    logger.warning("MCP SDK not installed. Install with: pip install 'mcp[cli]'")


@dataclass
class MCPToolInfo:
    """Information about an MCP tool."""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]


class MCPToolRegistry:
    """Registry for MCP tools that can be shared across servers."""
    
    def __init__(self):
        self.tools: Dict[str, MCPToolInfo] = {}
        self.resources: Dict[str, Callable] = {}
        self.prompts: Dict[str, Callable] = {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Register a tool in the registry."""
        self.tools[name] = MCPToolInfo(
            name=name,
            description=description,
            function=function,
            parameters=parameters or {}
        )
    
    def register_resource(self, uri_pattern: str, function: Callable):
        """Register a resource handler."""
        self.resources[uri_pattern] = function
    
    def register_prompt(self, name: str, function: Callable):
        """Register a prompt template."""
        self.prompts[name] = function


class MCPServerBuilder:
    """
    Builder for creating MCP servers from AgentiCraft agents.
    
    Features:
    - Automatic tool extraction from agents
    - Resource and prompt generation
    - Multiple transport support
    - Easy testing with MCP inspector
    """
    
    def __init__(self, name: str, description: str = ""):
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK required. Install with: pip install 'mcp[cli]'")
        
        self.name = name
        self.description = description
        self.mcp = FastMCP(name)
        self.registry = MCPToolRegistry()
        
        # Track registered components
        self._tools: List[str] = []
        self._resources: List[str] = []
        self._prompts: List[str] = []
    
    def from_agent(self, agent: Agent) -> 'MCPServerBuilder':
        """Create MCP server from an AgentiCraft agent."""
        # Extract and register tools
        if hasattr(agent, 'tools'):
            for tool_name, tool_func in agent.tools.items():
                self.add_tool(
                    name=tool_name,
                    description=f"Tool from agent {agent.name}: {tool_name}",
                    function=tool_func
                )
        
        # Add agent info as resource (without URI parameters)
        @self.mcp.resource(f"agent-info")
        async def agent_info():
            """Get agent information."""
            return json.dumps({
                "name": agent.name,
                "model": getattr(agent, 'model', 'unknown'),
                "tools": list(agent.tools.keys()) if hasattr(agent, 'tools') else [],
                "capabilities": getattr(agent, 'capabilities', [])
            })
        
        self._resources.append("agent-info")
        
        # Add execution prompt
        self.add_prompt(
            f"{agent.name}_execute",
            lambda task: f"Execute this task using {agent.name}: {task}"
        )
        
        return self
    
    def add_tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        function: Optional[Callable] = None
    ) -> Union[Callable, 'MCPServerBuilder']:
        """Add a tool to the MCP server."""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or f"Tool: {tool_name}"
            
            # Register with FastMCP
            if asyncio.iscoroutinefunction(func):
                # Already async - register directly
                registered_func = self.mcp.tool()(func)
            else:
                # Create async wrapper
                @self.mcp.tool()
                async def async_tool(**kwargs):
                    return func(**kwargs)
                registered_func = async_tool
            
            # Track registration
            self._tools.append(tool_name)
            self.registry.register_tool(tool_name, tool_desc, func)
            
            return func
        
        if function:
            return decorator(function)
        return decorator
    
    def add_resource(
        self,
        uri_pattern: str,
        handler: Optional[Callable] = None
    ) -> Union[Callable, 'MCPServerBuilder']:
        """Add a resource to the MCP server."""
        def decorator(func: Callable) -> Callable:
            # For simplicity, we'll create the resource without complex URI parameter handling
            # This avoids the parameter mismatch issue
            
            if asyncio.iscoroutinefunction(func):
                # Already async
                self.mcp.resource(uri_pattern)(func)
            else:
                # Create async wrapper
                @self.mcp.resource(uri_pattern)
                async def async_resource():
                    return func()
            
            # Track registration
            self._resources.append(uri_pattern)
            self.registry.register_resource(uri_pattern, func)
            
            return func
        
        if handler:
            return decorator(handler)
        return decorator
    
    def add_prompt(
        self,
        name: Optional[str] = None,
        template: Optional[Union[str, Callable]] = None
    ) -> Union[Callable, 'MCPServerBuilder']:
        """Add a prompt template to the MCP server."""
        def decorator(func: Callable) -> Callable:
            prompt_name = name or func.__name__
            
            # Register with FastMCP
            if asyncio.iscoroutinefunction(func):
                self.mcp.prompt()(func)
            else:
                @self.mcp.prompt()
                async def async_prompt(**kwargs):
                    if isinstance(template, str):
                        return template.format(**kwargs)
                    else:
                        return func(**kwargs)
            
            # Track registration
            self._prompts.append(prompt_name)
            self.registry.register_prompt(prompt_name, func)
            
            return func
        
        if template:
            if isinstance(template, str):
                # String template
                return decorator(lambda **kwargs: template.format(**kwargs))
            else:
                # Function
                return decorator(template)
        return decorator
    
    def add_tool_registry(self, registry: MCPToolRegistry) -> 'MCPServerBuilder':
        """Add all tools from a registry."""
        for tool_info in registry.tools.values():
            self.add_tool(
                name=tool_info.name,
                description=tool_info.description,
                function=tool_info.function
            )
        
        for uri, handler in registry.resources.items():
            self.add_resource(uri, handler)
        
        for name, template in registry.prompts.items():
            self.add_prompt(name, template)
        
        return self
    
    def run_stdio(self):
        """Run server with stdio transport (for Claude Desktop, etc)."""
        self.mcp.run()
    
    def run_sse(self, host: str = "0.0.0.0", port: int = 8080):
        """Run server with SSE transport."""
        import uvicorn
        app = self.mcp.sse_app()
        uvicorn.run(app, host=host, port=port)
    
    def run_http(self, host: str = "0.0.0.0", port: int = 8080):
        """Run server with HTTP transport."""
        import uvicorn
        from fastapi import FastAPI
        
        # Create FastAPI app with MCP endpoints
        app = FastAPI(title=f"{self.name} MCP Server")
        
        # Mount MCP streamable HTTP app
        app.mount("/", self.mcp.streamable_http_app())
        
        uvicorn.run(app, host=host, port=port)
    
    def test_with_inspector(self):
        """Launch MCP inspector for testing."""
        import subprocess
        import tempfile
        
        # Create temporary server file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f'''
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{self.name}")

# Generated server code
{self._generate_server_code()}

if __name__ == "__main__":
    mcp.run()
''')
            server_file = f.name
        
        # Run inspector
        try:
            subprocess.run(['mcp', 'dev', server_file], check=True)
        finally:
            Path(server_file).unlink()
    
    def _generate_server_code(self) -> str:
        """Generate server code for debugging."""
        code_lines = []
        
        # Add tools
        for tool_name in self._tools:
            code_lines.append(f'# Tool: {tool_name}')
        
        # Add resources  
        for uri in self._resources:
            code_lines.append(f'# Resource: {uri}')
        
        # Add prompts
        for prompt in self._prompts:
            code_lines.append(f'# Prompt: {prompt}')
        
        return '\n'.join(code_lines)
    
    def get_config_for_claude(self) -> Dict[str, Any]:
        """Get configuration for Claude Desktop."""
        return {
            "command": "python",
            "args": ["-m", self.name.lower().replace(" ", "_")],
            "name": self.name,
            "description": self.description,
            "tools": self._tools,
            "resources": self._resources,
            "prompts": self._prompts
        }


# Convenience functions for common patterns

def create_agent_mcp_server(agent: Agent, port: int = 8080) -> MCPServerBuilder:
    """Create an MCP server from an AgentiCraft agent."""
    builder = MCPServerBuilder(
        name=f"{agent.name} MCP Server",
        description=f"MCP interface for {agent.name}"
    )
    
    builder.from_agent(agent)
    
    # Add standard tools
    @builder.add_tool(description="Execute a task with the agent")
    async def execute_task(task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a task using the agent."""
        return await agent.execute(task, context=context)
    
    @builder.add_tool(description="Get agent status")
    def get_status() -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "name": agent.name,
            "status": "ready",
            "tools": list(agent.tools.keys()) if hasattr(agent, 'tools') else [],
            "model": getattr(agent, 'model', 'unknown')
        }
    
    return builder


def create_workflow_mcp_server(workflow_class, port: int = 8080) -> MCPServerBuilder:
    """Create an MCP server for an AgentiCraft workflow."""
    builder = MCPServerBuilder(
        name=f"{workflow_class.__name__} MCP Server",
        description=f"MCP interface for {workflow_class.__name__}"
    )
    
    # Add workflow execution tool
    @builder.add_tool(description="Execute workflow")
    async def execute_workflow(
        task: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a workflow instance."""
        workflow = workflow_class(**(config or {}))
        return await workflow.execute(task)
    
    # Add workflow info resource (no URI parameters)
    @builder.add_resource("workflow-info")
    def get_workflow_info() -> str:
        """Get workflow information."""
        return json.dumps({
            "name": workflow_class.__name__,
            "type": "AgentiCraft Workflow",
            "description": workflow_class.__doc__ or "No description"
        })
    
    return builder
