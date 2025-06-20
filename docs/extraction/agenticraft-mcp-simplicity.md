# AgentiCraft MCP Simplicity: Native Implementation Inspired by Fast-Agent

## What Makes Fast-Agent's MCP So Simple?

### 1. **Decorator-First Design**
```python
# Fast-agent's brilliance
@fast.agent("researcher", servers=["brave_search", "arxiv"])
```

### 2. **Zero Configuration**
- MCP servers defined in `fastagent.config.yaml`
- Auto-discovery of available tools
- No manual tool registration

### 3. **Implicit Tool Usage**
- Tools are just "there" - no explicit imports
- Natural language automatically maps to tools
- Seamless integration

### 4. **Unified Context**
- MCP resources, tools, and prompts all in one place
- Consistent access pattern
- No protocol details exposed

## AgentiCraft Native MCP Implementation

### Phase 1: Core MCP Decorator System

**File: `/agenticraft/mcp/decorators.py`**
```python
"""Native MCP decorators inspired by fast-agent's simplicity."""

from functools import wraps
from typing import List, Optional, Dict, Any, Callable
import asyncio

from agenticraft.core.agent import Agent
from agenticraft.protocols.mcp import MCPServer, MCPClient
from agenticraft.mcp.config import MCPConfig

# Global MCP configuration
_mcp_config = MCPConfig()

def agent(
    name: Optional[str] = None,
    instructions: Optional[str] = None,
    servers: Optional[List[str]] = None,
    model: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Create an MCP-enabled agent with minimal configuration.
    
    Inspired by fast-agent's simplicity but native to AgentiCraft.
    
    Examples:
        @agent("researcher", servers=["brave_search", "arxiv"])
        async def research_agent(topic: str):
            # Tools are automatically available via self.mcp
            results = await self.mcp.brave_search(topic)
            papers = await self.mcp.arxiv.search(topic)
            return self.synthesize(results, papers)
            
        @agent  # Even simpler - just a helpful agent
        async def assistant(query: str):
            return await self.respond(query)
    """
    def decorator(func: Callable) -> 'MCPAgent':
        # Auto-generate name if not provided
        agent_name = name or func.__name__.replace('_', '-')
        
        # Default instructions if not provided
        agent_instructions = instructions or f"You are {agent_name}, a helpful AI assistant."
        
        # Create MCPAgent class dynamically
        class MCPAgent(Agent):
            def __init__(self):
                super().__init__(
                    name=agent_name,
                    instructions=agent_instructions,
                    **kwargs
                )
                
                # Initialize MCP connections
                self.mcp_servers = servers or []
                self.mcp = MCPContext(self, self.mcp_servers)
                
                # Store the original function
                self._func = func
                
                # Bind the function to the instance
                self.execute = self._create_execute_method()
                
            def _create_execute_method(self):
                """Create the execute method that binds the decorated function."""
                async def execute(*args, **kwargs):
                    # Inject self into the function
                    return await self._func(self, *args, **kwargs)
                return execute
                
            async def __call__(self, *args, **kwargs):
                """Make agent directly callable."""
                return await self.execute(*args, **kwargs)
                
            async def __aenter__(self):
                """Context manager for automatic connection management."""
                await self.mcp.connect()
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                """Clean up MCP connections."""
                await self.mcp.disconnect()
        
        # Create and return instance
        return MCPAgent()
    
    # Handle both @agent and @agent() syntax
    if callable(name):
        func = name
        name = None
        return decorator(func)
    else:
        return decorator

class MCPContext:
    """
    Magical MCP context that makes tools feel native.
    
    Inspired by fast-agent's seamless tool access.
    """
    
    def __init__(self, agent: Agent, servers: List[str]):
        self.agent = agent
        self.servers = servers
        self.connections = {}
        self.tools = {}
        
    async def connect(self):
        """Connect to all configured MCP servers."""
        config = _mcp_config.load()
        
        for server_name in self.servers:
            if server_name in config.servers:
                server_config = config.servers[server_name]
                
                # Create appropriate client based on transport
                if server_config.transport == "stdio":
                    client = await self._connect_stdio(server_config)
                elif server_config.transport == "http":
                    client = await self._connect_http(server_config)
                else:  # websocket
                    client = await self._connect_websocket(server_config)
                    
                self.connections[server_name] = client
                
                # Discover and register tools
                await self._register_tools(server_name, client)
                
    async def _register_tools(self, server_name: str, client: MCPClient):
        """Register tools from MCP server for seamless access."""
        tools = await client.list_tools()
        
        for tool in tools:
            # Create a dynamic method for each tool
            tool_method = self._create_tool_method(client, tool)
            
            # Register in multiple ways for maximum flexibility
            # 1. Direct attribute: self.mcp.tool_name()
            setattr(self, tool.name, tool_method)
            
            # 2. Namespaced: self.mcp.server_name.tool_name()
            if not hasattr(self, server_name):
                setattr(self, server_name, type('MCPNamespace', (), {})())
            setattr(getattr(self, server_name), tool.name, tool_method)
            
            # 3. Tools dict: self.mcp.tools['tool_name']()
            self.tools[tool.name] = tool_method
            
    def _create_tool_method(self, client: MCPClient, tool):
        """Create a method that calls an MCP tool."""
        async def tool_method(**kwargs):
            return await client.call_tool(tool.name, kwargs)
            
        # Preserve metadata
        tool_method.__name__ = tool.name
        tool_method.__doc__ = tool.description
        
        return tool_method
        
    async def disconnect(self):
        """Disconnect all MCP clients."""
        for client in self.connections.values():
            await client.disconnect()
```

### Phase 2: Configuration System

**File: `/agenticraft/mcp/config.py`**
```python
"""MCP configuration system inspired by fast-agent."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ServerConfig:
    """Configuration for an MCP server."""
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    transport: str = "stdio"  # stdio, websocket, http
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

class MCPConfig:
    """
    MCP configuration manager that searches for agenticraft.yaml.
    
    Inspired by fast-agent's configuration approach.
    """
    
    def __init__(self):
        self.config_file = self._find_config_file()
        self._config = None
        
    def _find_config_file(self) -> Optional[Path]:
        """Search for configuration file in current and parent directories."""
        config_names = ['agenticraft.yaml', 'agenticraft.yml', '.agenticraft.yaml']
        
        current = Path.cwd()
        
        # Search up the directory tree
        while current != current.parent:
            for config_name in config_names:
                config_path = current / config_name
                if config_path.exists():
                    return config_path
            current = current.parent
            
        # Check home directory
        home = Path.home()
        for config_name in config_names:
            config_path = home / config_name
            if config_path.exists():
                return config_path
                
        return None
        
    def load(self) -> 'MCPConfig':
        """Load configuration from file."""
        if self._config:
            return self
            
        if self.config_file:
            with open(self.config_file) as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {}
            
        # Merge with environment variables
        self._merge_env_config()
        
        return self
        
    def _merge_env_config(self):
        """Merge environment variables into configuration."""
        # Support AGENTICRAFT_MCP_SERVER_* environment variables
        for key, value in os.environ.items():
            if key.startswith('AGENTICRAFT_MCP_SERVER_'):
                server_name = key[23:].lower()
                if 'servers' not in self._config:
                    self._config['servers'] = {}
                if server_name not in self._config['servers']:
                    self._config['servers'][server_name] = {}
                    
                # Parse the value as YAML for complex configs
                try:
                    self._config['servers'][server_name] = yaml.safe_load(value)
                except:
                    self._config['servers'][server_name] = {'command': value}
                    
    @property
    def servers(self) -> Dict[str, ServerConfig]:
        """Get server configurations."""
        if not self._config:
            self.load()
            
        servers = {}
        for name, config in self._config.get('servers', {}).items():
            if isinstance(config, str):
                # Simple command string
                servers[name] = ServerConfig(command=config)
            else:
                # Full configuration
                servers[name] = ServerConfig(**config)
                
        return servers

# Example agenticraft.yaml:
"""
servers:
  # Stdio transport (default)
  brave_search:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: ${BRAVE_API_KEY}
      
  # HTTP transport
  github:
    transport: http
    url: https://api.github.com/mcp
    headers:
      Authorization: Bearer ${GITHUB_TOKEN}
      
  # WebSocket transport
  slack:
    transport: websocket
    url: wss://slack.com/mcp
    env:
      SLACK_TOKEN: ${SLACK_TOKEN}
      
  # Simple command format
  filesystem: npx -y @modelcontextprotocol/server-filesystem --allow-write
"""
```

### Phase 3: Workflow Decorators

**File: `/agenticraft/mcp/workflows.py`**
```python
"""Workflow patterns inspired by fast-agent."""

from typing import List, Optional, Dict, Any, Union
from agenticraft.mcp.decorators import agent, _mcp_config

def chain(
    name: Optional[str] = None,
    sequence: Optional[List[str]] = None,
    cumulative: bool = False,
    servers: Optional[List[str]] = None
) -> Callable:
    """
    Chain multiple agents sequentially.
    
    Examples:
        @chain(sequence=["researcher", "writer", "editor"])
        async def content_pipeline(topic: str):
            # Automatically chains the agents
            pass
            
        # Or define inline
        @agent("researcher", servers=["brave_search"])
        async def researcher(topic): ...
        
        @agent("writer")
        async def writer(research): ...
        
        @chain(sequence=[researcher, writer])
        async def pipeline(topic):
            # Auto-chains the decorated functions
            pass
    """
    def decorator(func):
        # Create a chain agent
        @agent(name or func.__name__, servers=servers)
        async def chain_agent(self, *args, **kwargs):
            agents = sequence or []
            
            # Resolve agents from strings or direct references
            resolved_agents = []
            for agent_ref in agents:
                if isinstance(agent_ref, str):
                    # Look up by name
                    agent_obj = self.mcp._registry.get(agent_ref)
                    if not agent_obj:
                        raise ValueError(f"Agent '{agent_ref}' not found")
                    resolved_agents.append(agent_obj)
                else:
                    # Direct agent reference
                    resolved_agents.append(agent_ref)
                    
            # Execute chain
            result = args[0] if args else kwargs
            results = [] if cumulative else None
            
            for agent in resolved_agents:
                if cumulative:
                    result = await agent(result)
                    results.append(result)
                else:
                    result = await agent(result)
                    
            return results if cumulative else result
            
        return chain_agent
        
    return decorator

def parallel(
    name: Optional[str] = None,
    fan_out: Optional[List[str]] = None,
    fan_in: Optional[str] = None,
    servers: Optional[List[str]] = None
) -> Callable:
    """
    Execute agents in parallel.
    
    Examples:
        @parallel(
            fan_out=["analyst1", "analyst2", "analyst3"],
            fan_in="synthesizer"
        )
        async def multi_analysis(data):
            # Runs analysts in parallel, then synthesizes
            pass
    """
    def decorator(func):
        @agent(name or func.__name__, servers=servers)
        async def parallel_agent(self, *args, **kwargs):
            import asyncio
            
            # Execute fan-out agents in parallel
            tasks = []
            for agent_name in fan_out:
                agent_obj = self.mcp._registry.get(agent_name)
                if not agent_obj:
                    raise ValueError(f"Agent '{agent_name}' not found")
                    
                task = asyncio.create_task(agent_obj(*args, **kwargs))
                tasks.append(task)
                
            # Gather results
            results = await asyncio.gather(*tasks)
            
            # Fan-in if specified
            if fan_in:
                fan_in_agent = self.mcp._registry.get(fan_in)
                if not fan_in_agent:
                    raise ValueError(f"Fan-in agent '{fan_in}' not found")
                    
                return await fan_in_agent(results)
                
            return results
            
        return parallel_agent
        
    return decorator

def router(
    name: Optional[str] = None,
    agents: Optional[List[str]] = None,
    servers: Optional[List[str]] = None,
    model: Optional[str] = None
) -> Callable:
    """
    Route to the best agent based on input.
    
    Examples:
        @router(agents=["weather", "news", "calculator"])
        async def assistant(query):
            # Automatically routes to the right agent
            pass
    """
    def decorator(func):
        @agent(
            name or func.__name__, 
            servers=servers,
            model=model or "gpt-4"  # Router benefits from better model
        )
        async def router_agent(self, query: str, **kwargs):
            # Build routing prompt
            agent_descriptions = []
            for agent_name in agents:
                agent_obj = self.mcp._registry.get(agent_name)
                if agent_obj:
                    agent_descriptions.append(
                        f"- {agent_name}: {agent_obj.instructions}"
                    )
                    
            routing_prompt = f"""
            Given the user query, select the most appropriate agent:
            
            Available agents:
            {chr(10).join(agent_descriptions)}
            
            Query: {query}
            
            Respond with just the agent name.
            """
            
            # Use LLM to route
            selected = await self.complete(routing_prompt)
            selected_agent = selected.strip()
            
            # Execute selected agent
            agent_obj = self.mcp._registry.get(selected_agent)
            if not agent_obj:
                raise ValueError(f"Selected agent '{selected_agent}' not found")
                
            return await agent_obj(query, **kwargs)
            
        return router_agent
        
    return decorator
```

### Phase 4: Enhanced Agent Base

**File: `/agenticraft/agents/mcp_agent.py`**
```python
"""Enhanced Agent base class with native MCP support."""

from agenticraft.core.agent import Agent
from agenticraft.mcp.decorators import MCPContext

class MCPAgent(Agent):
    """
    Agent with built-in MCP support inspired by fast-agent.
    
    This becomes the new base class for MCP-enabled agents.
    """
    
    def __init__(self, name: str, instructions: str = None, servers: List[str] = None, **kwargs):
        super().__init__(name, instructions, **kwargs)
        
        # Initialize MCP context
        self.servers = servers or []
        self.mcp = MCPContext(self, self.servers)
        
        # Auto-connect on creation
        self._connected = False
        
    async def __aenter__(self):
        """Async context manager for automatic connection."""
        if not self._connected:
            await self.mcp.connect()
            self._connected = True
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up connections."""
        if self._connected:
            await self.mcp.disconnect()
            self._connected = False
            
    async def think(self, prompt: str) -> str:
        """
        Enhanced thinking that can use MCP tools transparently.
        
        Tools are available in the thought process!
        """
        # Original thinking logic
        thought = await super().think(prompt)
        
        # But now MCP tools are available during thinking
        # The LLM can naturally call them through function calling
        
        return thought
```

### Phase 5: Usage Examples

**File: `/examples/mcp/simple_agent.py`**
```python
"""Simple MCP agent example showing fast-agent inspired simplicity."""

from agenticraft import agent, chain, parallel, router

# Simplest possible agent
@agent
async def assistant(self, query: str):
    """I'm a helpful assistant."""
    return await self.respond(query)

# Agent with MCP servers
@agent("researcher", servers=["brave_search", "arxiv", "wikipedia"])
async def researcher(self, topic: str):
    """Research any topic comprehensively."""
    # Tools are magically available
    web_results = await self.mcp.brave_search(topic)
    papers = await self.mcp.arxiv.search(topic, max_results=5)
    wiki = await self.mcp.wikipedia.get_summary(topic)
    
    # Synthesize with reasoning
    return await self.synthesize([web_results, papers, wiki])

# Agent using specific server namespace
@agent("github_analyst", servers=["github"])
async def analyze_repo(self, repo: str):
    """Analyze a GitHub repository."""
    # Namespaced access
    repo_info = await self.mcp.github.get_repository(repo)
    issues = await self.mcp.github.list_issues(repo, state="open")
    prs = await self.mcp.github.list_pull_requests(repo)
    
    return {
        "repository": repo_info,
        "open_issues": len(issues),
        "active_prs": len(prs),
        "analysis": await self.analyze(repo_info, issues, prs)
    }

# Chain workflow
@agent("writer", "Write engaging content")
async def writer(self, research): ...

@agent("editor", "Edit and improve content")  
async def editor(self, content): ...

@chain(sequence=["researcher", "writer", "editor"])
async def content_pipeline(topic: str):
    """Research, write, and edit content about any topic."""
    pass

# Parallel analysis
@agent("sentiment_analyzer", servers=["sentiment_api"])
async def sentiment(self, text): ...

@agent("keyword_extractor", servers=["nlp_toolkit"])
async def keywords(self, text): ...

@agent("summarizer")
async def summarize(self, text): ...

@parallel(
    fan_out=["sentiment", "keywords", "summarizer"],
    fan_in="synthesizer"
)
async def analyze_text(text: str):
    """Analyze text from multiple perspectives."""
    pass

# Router pattern
@router(agents=["researcher", "calculator", "weather", "news"])
async def smart_assistant(query: str):
    """Routes queries to the right specialist."""
    pass

# Usage
async def main():
    # Simple usage
    response = await assistant("Hello!")
    
    # With context manager (auto-connects MCP)
    async with researcher as r:
        report = await r("quantum computing breakthroughs 2024")
        
    # Direct execution
    repo_analysis = await analyze_repo("langchain-ai/langchain")
    
    # Workflow execution
    article = await content_pipeline("AI agents and the future of work")
    
    # Router automatically selects the right agent
    answer = await smart_assistant("What's 2+2?")  # -> calculator
    answer = await smart_assistant("Latest AI news?")  # -> news

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Phase 6: Configuration File

**File: `/agenticraft.yaml`**
```yaml
# AgentiCraft configuration with MCP servers
# Inspired by fast-agent's fastagent.config.yaml

# MCP Servers
servers:
  # Search and research
  brave_search:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: ${BRAVE_API_KEY}
      
  # Development tools
  github:
    command: github-mcp-server
    args: ["--repo", "${GITHUB_REPO}"]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      
  # File system access
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "--allow-write"]
    
  # Databases
  postgres:
    command: postgres-mcp-server
    env:
      DATABASE_URL: ${DATABASE_URL}
      
  # Communication
  slack:
    transport: websocket
    url: wss://slack-mcp.com/connect
    env:
      SLACK_TOKEN: ${SLACK_TOKEN}
      
  # Custom HTTP server
  internal_api:
    transport: http
    url: https://api.company.com/mcp
    headers:
      Authorization: Bearer ${API_TOKEN}

# Model defaults
models:
  default: gpt-4
  router: gpt-4  # Routers benefit from better models
  orchestrator: gpt-4

# Agent defaults
agents:
  timeout: 30
  max_retries: 3
  temperature: 0.7
```

## Benefits of This Native Implementation

### 1. **Simplicity** ✨
- Decorator-first design
- Zero boilerplate
- Natural tool access

### 2. **AgentiCraft Integration** 🔧
- Works with existing Agent base class
- Compatible with current features
- Preserves reasoning transparency

### 3. **Flexibility** 🎯
- Easy to extend
- Multiple access patterns
- Gradual adoption path

### 4. **Production Ready** 🚀
- Async throughout
- Connection management
- Error handling

## Migration Path

```python
# Current AgentiCraft
agent = Agent(
    name="researcher",
    instructions="Research topics",
    tools=[brave_search_tool, arxiv_tool]
)

# New MCP-native AgentiCraft
@agent("researcher", servers=["brave_search", "arxiv"])
async def researcher(self, topic):
    results = await self.mcp.brave_search(topic)
    return results
```

## Conclusion

This native implementation brings fast-agent's brilliant MCP simplicity to AgentiCraft while:
- Preserving AgentiCraft's unique features
- Maintaining backward compatibility
- Enabling gradual adoption
- Keeping the codebase cohesive

The key insight from fast-agent is that **MCP should feel invisible** - tools should just work, without developers thinking about protocols or connections.