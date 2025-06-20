# SDK Integration & Migration Guide

This guide helps you migrate existing AgentiCraft code to use the new Unified Protocol Fabric with SDK integration.

## What's New

### 1. Unified Protocol Fabric
- Single interface for multiple protocols (MCP, A2A)
- Automatic protocol detection and routing
- Tool namespacing to avoid conflicts
- Dynamic tool discovery

### 2. Decorator-Based Agents
- Natural tool access via `self.tools`
- Configuration through decorators
- YAML-based configuration support
- Automatic protocol initialization

### 3. Official SDK Support
- Native integration with Google A2A SDK
- Full MCP protocol implementation
- Extensible adapter system for new protocols

## Migration Examples

### Before: Manual MCP Integration

```python
# Old way
from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient

# Manual client setup
mcp_client = MCPClient("http://localhost:3000")
await mcp_client.connect()

# Get tools manually
tools = mcp_client.get_tools()

# Create agent with tools
agent = Agent(
    name="researcher",
    tools=tools
)

# Use agent
response = await agent.arun("Search for AI news")
```

### After: Unified Fabric with Decorators

```python
# New way
from agenticraft.fabric import agent

@agent(
    "researcher",
    servers=["http://localhost:3000/mcp"],
    model="gpt-4"
)
async def research_agent(self, topic: str):
    # Direct tool access
    return await self.tools.web_search(query=topic)

# Use agent
response = await research_agent("AI news")
```

### Before: A2A Protocol Setup

```python
# Old way
from agenticraft.protocols.a2a import A2AClient, MeshNetwork

# Complex setup
mesh = MeshNetwork("coordinator")
await mesh.join_network("research_network")

# Manual agent discovery
agents = await mesh.discover_agents()

# Delegate tasks manually
result = await mesh.execute_distributed(
    task="Analyze data",
    capability_required="analysis"
)
```

### After: Integrated A2A Support

```python
# New way
@agent(
    "coordinator",
    servers=["ws://localhost:8080/a2a"],
    reasoning="chain_of_thought"
)
async def coordinator(self, task: str):
    # Automatic agent discovery
    agents = await self.tools.discover_agents()
    
    # Natural delegation
    return await self.tools.delegate_to_best(task)
```

### Before: Multi-Protocol Agents

```python
# Old way - Complex manual setup
mcp_client = MCPClient("http://localhost:3000")
await mcp_client.connect()

a2a_client = A2AClient("ws://localhost:8080")
await a2a_client.connect()

# Manual tool merging
all_tools = []
all_tools.extend(mcp_client.get_tools())
all_tools.extend(a2a_client.get_tools())

agent = Agent(name="hybrid", tools=all_tools)

# Manual protocol routing
async def execute_task(task):
    if task.needs_web_search:
        # Use MCP tool
        result = await mcp_client.call_tool("web_search", {"query": task.query})
    else:
        # Use A2A delegation
        result = await a2a_client.delegate(task)
    return result
```

### After: Unified Multi-Protocol

```python
# New way - Automatic setup
@agent(
    "hybrid",
    servers=[
        "http://localhost:3000/mcp",
        "ws://localhost:8080/a2a"
    ]
)
async def hybrid_agent(self, task: str):
    # All tools available transparently
    data = await self.tools.web_search(query=task)
    analysis = await self.tools.expert_analysis(data=data)
    return {"data": data, "analysis": analysis}
```

## Step-by-Step Migration

### Step 1: Update Imports

```python
# Remove old imports
# from agenticraft.protocols.mcp import MCPClient
# from agenticraft.protocols.a2a import A2AClient

# Add new imports
from agenticraft.fabric import (
    agent,
    UnifiedProtocolFabric,
    initialize_fabric
)
```

### Step 2: Convert Agent Creation

```python
# Old
agent = Agent(
    name="my_agent",
    tools=[tool1, tool2],
    model="gpt-4"
)

# New
@agent(
    "my_agent",
    servers=["http://localhost:3000/mcp"],
    model="gpt-4"
)
async def my_agent(self, prompt: str):
    return await self.arun(prompt)
```

### Step 3: Update Tool Usage

```python
# Old - Manual tool execution
tool = agent.get_tool("web_search")
result = await tool.arun(query="test")

# New - Natural access
result = await self.tools.web_search(query="test")
```

### Step 4: Configuration Files

Create `agenticraft.yaml`:

```yaml
agents:
  my_agent:
    servers:
      - http://localhost:3000/mcp
      - ws://localhost:8080/a2a
    model: gpt-4
    temperature: 0.7
```

Use in code:

```python
from agenticraft.fabric import from_config

@from_config("agenticraft.yaml")
class MyAgents:
    @agent("my_agent")
    async def process(self, data):
        return await self.tools.analyze(data)
```

## Breaking Changes

### 1. Tool Naming
Tools are now namespaced by protocol:
- MCP: `mcp:tool_name`
- A2A: `a2a:agent_id.skill_name`

The decorator system handles this automatically, but direct fabric usage requires full names:

```python
# Decorator (automatic)
await self.tools.web_search(...)

# Direct fabric (explicit)
await fabric.execute_tool("mcp:web_search", ...)
```

### 2. Agent Methods
Decorated agents have a different API:

```python
# Old
response = await agent.arun("prompt")
agent.add_tool(new_tool)

# New
response = await my_agent("prompt")
# Tools are managed by fabric
```

### 3. Protocol Configuration
Configuration is now centralized:

```python
# Old - Per protocol
mcp_client = MCPClient(url, headers={...})
a2a_client = A2AClient(mesh_config={...})

# New - Unified
config = {
    "mcp": {"servers": [{"url": "...", "options": {...}}]},
    "a2a": {"connection_type": "mesh", "mesh_config": {...}}
}
await initialize_fabric(config)
```

## Compatibility Mode

For gradual migration, you can use both systems:

```python
# Use old system
from agenticraft.protocols.mcp import MCPClient
old_client = MCPClient("http://localhost:3000")

# Use new system alongside
from agenticraft.fabric import agent

@agent("new_agent", servers=["http://localhost:3000/mcp"])
async def new_agent(self, prompt):
    return await self.tools.process(prompt)
```

## Advanced Migration

### Custom Protocol Adapters

If you have custom protocols:

```python
from agenticraft.fabric import IProtocolAdapter, ProtocolType

class MyAdapter(IProtocolAdapter):
    @property
    def protocol_type(self):
        return ProtocolType.CUSTOM
    
    async def connect(self, config):
        # Your connection logic
        pass
    
    async def discover_tools(self):
        # Return UnifiedTool instances
        pass

# Register
fabric = UnifiedProtocolFabric()
fabric.register_adapter(ProtocolType.CUSTOM, MyAdapter)
```

### Workflow Migration

```python
# Old workflow
workflow = Workflow("research")
workflow.add_step(research_step)
workflow.add_step(analysis_step)

# New approach
@workflow("research")
class ResearchWorkflow:
    @step(order=1)
    async def research(self, topic):
        return await self.tools.search(topic)
    
    @step(order=2)
    async def analyze(self, data):
        return await self.tools.analyze(data)
```

## Testing Your Migration

1. **Unit Tests**: Update mocks for new structure
2. **Integration Tests**: Test with real protocol servers
3. **Performance Tests**: Compare old vs new implementation

Example test:

```python
import pytest
from agenticraft.fabric import agent

@pytest.mark.asyncio
async def test_migrated_agent():
    @agent("test", servers=["http://mock-server"])
    async def test_agent(self, prompt):
        return await self.tools.mock_tool(prompt)
    
    # Mock the fabric
    with patch('agenticraft.fabric.get_global_fabric'):
        result = await test_agent("test")
        assert result is not None
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```python
   # Make sure fabric is imported
   from agenticraft.fabric import agent
   ```

2. **Tool Not Found**
   ```python
   # List available tools
   fabric = get_global_fabric()
   tools = fabric.get_tools()
   print([t.name for t in tools])
   ```

3. **Connection Failures**
   ```python
   # Enable debug logging
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Performance Considerations

- Connection pooling is automatic
- Tools are cached after discovery
- Parallel protocol initialization

## Next Steps

1. Start with one agent migration
2. Test thoroughly
3. Migrate remaining agents
4. Remove old protocol code
5. Optimize configuration

For questions, see:
- [Full Documentation](https://docs.agenticraft.ai/fabric)
- [Examples](examples/fabric/)
- [API Reference](https://docs.agenticraft.ai/api/fabric)
