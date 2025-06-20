"""
MCP integration module for AgentiCraft.

This module provides high-level utilities for integrating
MCP clients and servers with AgentiCraft workflows and agents.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from ...core.agent import Agent
from ...workflows.base import Workflow
from ...core.tool import BaseTool
from .client import MCPClient
from .server import MCPServer
from .tools import (
    MCPToolRegistry,
    get_global_registry,
    register_mcp_server,
    get_mcp_tool
)
from agenticraft.core.transport import TransportRegistry

logger = logging.getLogger(__name__)


@dataclass
class MCPIntegrationConfig:
    """Configuration for MCP integration."""
    
    # Client settings
    auto_discover_tools: bool = True
    tool_prefix: Optional[str] = None  # Prefix for imported tools
    
    # Server settings
    expose_all_tools: bool = False
    tool_whitelist: Optional[List[str]] = None
    tool_blacklist: Optional[List[str]] = None
    
    # Security settings
    require_auth: bool = True
    allowed_hosts: Optional[List[str]] = None


class MCPEnabledAgent(Agent):
    """Agent with MCP tool discovery and execution capabilities."""
    
    def __init__(
        self,
        name: str,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[MCPIntegrationConfig] = None,
        **kwargs
    ):
        """
        Initialize MCP-enabled agent.
        
        Args:
            name: Agent name
            mcp_servers: List of MCP server URLs to connect to
            mcp_config: MCP integration configuration
            **kwargs: Additional agent arguments
        """
        super().__init__(name, **kwargs)
        
        self.mcp_config = mcp_config or MCPIntegrationConfig()
        self.mcp_servers = mcp_servers or []
        self._mcp_clients: Dict[str, MCPClient] = {}
        
    async def initialize(self) -> None:
        """Initialize agent and connect to MCP servers."""
        await super().initialize()
        
        # Connect to MCP servers
        for server_url in self.mcp_servers:
            await self.connect_mcp_server(server_url)
            
    async def connect_mcp_server(self, url: str) -> None:
        """
        Connect to an MCP server and discover tools.
        
        Args:
            url: MCP server URL
        """
        try:
            logger.info(f"Connecting to MCP server: {url}")
            
            # Create client
            client = MCPClient(url)
            await client.connect()
            
            # Store client
            self._mcp_clients[url] = client
            
            # Discover and add tools
            if self.mcp_config.auto_discover_tools:
                tools = client.get_tools()
                for tool in tools:
                    # Apply prefix if configured
                    if self.mcp_config.tool_prefix:
                        tool.name = f"{self.mcp_config.tool_prefix}.{tool.name}"
                        
                    # Add to agent's tools
                    self.add_tool(tool)
                    
                logger.info(f"Added {len(tools)} tools from {url}")
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {url}: {e}")
            raise
            
    async def disconnect_mcp_servers(self) -> None:
        """Disconnect from all MCP servers."""
        for url, client in self._mcp_clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected from MCP server: {url}")
            except Exception as e:
                logger.error(f"Error disconnecting from {url}: {e}")
                
        self._mcp_clients.clear()
        
    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        await self.disconnect_mcp_servers()
        await super().cleanup()


class MCPEnabledWorkflow(Workflow):
    """Workflow with MCP integration for distributed tool execution."""
    
    def __init__(
        self,
        name: str,
        mcp_registry: Optional[MCPToolRegistry] = None,
        **kwargs
    ):
        """
        Initialize MCP-enabled workflow.
        
        Args:
            name: Workflow name
            mcp_registry: MCP tool registry to use
            **kwargs: Additional workflow arguments
        """
        super().__init__(name, **kwargs)
        
        self.mcp_registry = mcp_registry or get_global_registry()
        
    async def add_mcp_server(self, url: str, alias: Optional[str] = None) -> None:
        """
        Add an MCP server to the workflow.
        
        Args:
            url: MCP server URL
            alias: Optional alias for the server
        """
        await self.mcp_registry.register_client(url, alias)
        
        # Update available tools for all agents
        for agent in self.agents.values():
            if isinstance(agent, MCPEnabledAgent):
                await agent.connect_mcp_server(url)
                
    def get_mcp_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get an MCP tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None
        """
        return self.mcp_registry.get_tool(name)
        
    def list_mcp_tools(self, **filters) -> List[str]:
        """
        List available MCP tools.
        
        Args:
            **filters: Optional filters (category, tags, client_id)
            
        Returns:
            List of tool names
        """
        return self.mcp_registry.list_tools(**filters)


class MCPServerBuilder:
    """Builder for creating and configuring MCP servers."""
    
    def __init__(self, name: str = "AgentiCraft MCP Server"):
        """
        Initialize server builder.
        
        Args:
            name: Server name
        """
        self.server = MCPServer(name=name)
        self.config = MCPIntegrationConfig()
        
    def with_tool(self, tool: Union[BaseTool, Agent]) -> "MCPServerBuilder":
        """
        Add a tool to expose via MCP.
        
        Args:
            tool: Tool or agent to expose
            
        Returns:
            Self for chaining
        """
        if isinstance(tool, Agent):
            # Expose agent as a tool
            agent_tool = AgentTool(tool)
            self.server.register_tool(agent_tool)
        else:
            self.server.register_tool(tool)
            
        return self
        
    def with_workflow(self, workflow: Workflow) -> "MCPServerBuilder":
        """
        Expose all tools from a workflow.
        
        Args:
            workflow: Workflow whose tools to expose
            
        Returns:
            Self for chaining
        """
        # Get all tools from workflow agents
        for agent in workflow.agents.values():
            for tool in agent.tools.values():
                if self._should_expose_tool(tool):
                    self.server.register_tool(tool)
                    
        return self
        
    def with_whitelist(self, tool_names: List[str]) -> "MCPServerBuilder":
        """
        Set tool whitelist.
        
        Args:
            tool_names: Tools to expose
            
        Returns:
            Self for chaining
        """
        self.config.tool_whitelist = tool_names
        return self
        
    def with_blacklist(self, tool_names: List[str]) -> "MCPServerBuilder":
        """
        Set tool blacklist.
        
        Args:
            tool_names: Tools to exclude
            
        Returns:
            Self for chaining
        """
        self.config.tool_blacklist = tool_names
        return self
        
    def _should_expose_tool(self, tool: BaseTool) -> bool:
        """Check if tool should be exposed based on config."""
        # Check whitelist
        if self.config.tool_whitelist:
            return tool.name in self.config.tool_whitelist
            
        # Check blacklist
        if self.config.tool_blacklist:
            return tool.name not in self.config.tool_blacklist
            
        # Default behavior
        return self.config.expose_all_tools
        
    def build(self) -> MCPServer:
        """
        Build the configured server.
        
        Returns:
            Configured MCP server
        """
        return self.server
        
    async def start_websocket(self, host: str = "localhost", port: int = 3000) -> None:
        """
        Start the server as WebSocket.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        await self.server.start_websocket_server(host, port)
        
    def create_fastapi_app(self):
        """
        Create FastAPI app for HTTP mode.
        
        Returns:
            FastAPI application
        """
        return self.server.create_fastapi_app()


class AgentTool(BaseTool):
    """Wrapper to expose an agent as an MCP tool."""
    
    def __init__(self, agent: Agent):
        """
        Initialize agent tool wrapper.
        
        Args:
            agent: Agent to wrap
        """
        super().__init__(
            name=f"agent_{agent.name}",
            description=f"Execute tasks using {agent.name} agent"
        )
        self.agent = agent
        
    async def arun(self, task: str, **kwargs) -> Any:
        """Execute task using the agent."""
        return await self.agent.execute(task, **kwargs)


# Convenience functions

async def create_mcp_agent(
    name: str,
    servers: List[str],
    **kwargs
) -> MCPEnabledAgent:
    """
    Create and initialize an MCP-enabled agent.
    
    Args:
        name: Agent name
        servers: List of MCP server URLs
        **kwargs: Additional agent arguments
        
    Returns:
        Initialized MCP-enabled agent
    """
    agent = MCPEnabledAgent(name, mcp_servers=servers, **kwargs)
    await agent.initialize()
    return agent


async def expose_workflow_as_mcp(
    workflow: Workflow,
    host: str = "localhost",
    port: int = 3000
) -> None:
    """
    Expose a workflow's tools as an MCP server.
    
    Args:
        workflow: Workflow to expose
        host: Server host
        port: Server port
    """
    builder = MCPServerBuilder(f"{workflow.name} MCP Server")
    builder.with_workflow(workflow)
    
    # Start server
    await builder.start_websocket(host, port)


def create_mcp_transport(url: str) -> Any:
    """
    Create appropriate transport for URL.
    
    Args:
        url: Connection URL
        
    Returns:
        Transport instance
    """
    from agenticraft.core.transport import MCPConnectionConfig
    
    config = MCPConnectionConfig(url=url)
    return TransportRegistry.create(config)
