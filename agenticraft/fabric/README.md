# AgentiCraft Unified Protocol Fabric

## Overview

The Unified Protocol Fabric provides seamless integration between multiple agent communication protocols, enabling AgentiCraft agents to work with MCP servers, A2A networks, and future protocols through a single interface.

## Key Features

- **Multi-Protocol Support**: MCP and A2A protocols with extensible adapter system
- **Natural Tool Access**: Use `self.tools.tool_name` syntax for any protocol
- **Fast-Agent Decorators**: Simple `@agent` decorator for creating agents
- **Protocol Routing**: Automatic routing based on tool prefixes
- **Unified Discovery**: Find tools across all connected protocols

## Quick Start

### Basic Usage

```python
from agenticraft.fabric import agent

@agent("researcher", servers=["http://localhost:3000/mcp"])
async def research_agent(self, topic: str):
    # Natural tool access - no manual setup needed
    results = await self.tools.web_search(query=topic)
    summary = await self.tools.summarize(text=results)
    return summary

# Use the agent
result = await research_agent("AI safety research")
```

### Manual Fabric Usage

```python
from agenticraft.fabric import UnifiedProtocolFabric, initialize_fabric

# Initialize fabric with multiple protocols
fabric = await initialize_fabric({
    "mcp": {
        "servers": [
            {"url": "http://localhost:3000"}
        ]
    },
    "a2a": {
        "connection_type": "http",
        "url": "http://localhost:8080"
    }
})

# Execute tools from any protocol
result = await fabric.execute_tool("mcp:web_search", query="AI")
```

## Decorator Options

The `@agent` decorator supports many configuration options:

```python
@agent(
    "advanced_researcher",
    servers=["http://localhost:3000/mcp", "ws://localhost:8080/a2a"],
    model="gpt-4",
    provider="openai",
    reasoning="chain_of_thought",  # Enable reasoning patterns
    temperature=0.7,
    max_tokens=2000,
    sandbox=True,  # Enable sandboxed execution
    memory=True    # Enable memory system
)
async def advanced_agent(self, query: str):
    # Agent with reasoning and multiple protocols
    return await self.tools.analyze(query)
```

## Protocol Adapters

### MCP Adapter

Connects to Model Context Protocol servers:
- Supports all MCP primitives (tools, resources, prompts, sampling)
- WebSocket and HTTP transports
- Tool discovery and execution

### A2A Adapter  

Connects to Agent-to-Agent Protocol networks:
- Agent discovery via agent cards
- Skill-based tool access
- Bidirectional communication

### Custom Adapters

Create custom protocol adapters by implementing `IProtocolAdapter`:

```python
from agenticraft.fabric import IProtocolAdapter, ProtocolType

class MyProtocolAdapter(IProtocolAdapter):
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.CUSTOM
    
    async def connect(self, config: Dict[str, Any]) -> None:
        # Connect to your protocol
        pass
    
    async def discover_tools(self) -> List[UnifiedTool]:
        # Discover available tools
        pass
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        # Execute a tool
        pass
```

## Tool Namespacing

Tools are automatically namespaced to avoid conflicts:
- MCP tools: `mcp:tool_name`
- A2A tools: `a2a:agent_id.skill_name`

Both full and short names work:
```python
# Both of these work
await self.tools.web_search(query="AI")  # Short name
await self.tools['mcp:web_search'](query="AI")  # Full name
```

## Advanced Features

### Tool Discovery

```python
# Get all available tools
tools = fabric.get_tools()

# Get tools from specific protocol
mcp_tools = fabric.get_tools(protocol=ProtocolType.MCP)

# Get capabilities
capabilities = fabric.get_capabilities()
```

### Creating Unified Agents

```python
# Create agent with access to all fabric tools
agent = await fabric.create_unified_agent(
    name="multi_protocol_agent",
    model="gpt-4"
)

# Use the agent normally
response = await agent.arun("Search for AI news and summarize")
```

## Migration from Direct Protocol Usage

### Before (Manual Protocol Setup)
```python
from agenticraft.protocols.mcp import MCPClient

# Complex manual setup
client = MCPClient("http://localhost:3000")
await client.connect()
tools = client.get_tools()

# Manual tool execution
for tool in tools:
    if tool.name == "web_search":
        result = await client.call_tool("web_search", {"query": "AI"})
```

### After (Unified Fabric)
```python
from agenticraft.fabric import agent

@agent("searcher", servers=["http://localhost:3000/mcp"])
async def search(self, query):
    return await self.tools.web_search(query=query)
```

## Configuration

### Using YAML Configuration

Create `agenticraft.yaml`:
```yaml
agents:
  researcher:
    servers:
      - http://localhost:3000/mcp
      - ws://localhost:8080/a2a
    model: gpt-4
    temperature: 0.7
    
  writer:
    servers:
      - http://localhost:3001/mcp
    model: claude-3
    reasoning: chain_of_thought
```

Use in code:
```python
from agenticraft.fabric import from_config, agent

@from_config("agenticraft.yaml")
class MyAgents:
    @agent("researcher")
    async def research(self, topic: str):
        return await self.tools.search(topic)
```

## Best Practices

1. **Use decorators for new agents** - Simpler and more maintainable
2. **Let fabric handle connections** - Don't manually manage protocol clients
3. **Use short tool names** - The fabric handles namespacing automatically
4. **Enable features as needed** - Sandbox, memory, and reasoning are optional
5. **Configure via YAML** - Easier to manage multiple agents

## Troubleshooting

### Tool Not Found
```python
# Check available tools
fabric = get_global_fabric()
tools = fabric.get_tools()
print([t.name for t in tools])
```

### Connection Issues
```python
# Check protocol status
protocols = fabric.get_available_protocols()
capabilities = fabric.get_capabilities()
```

### Initialization Issues
```python
# Ensure fabric is initialized before use
fabric = await initialize_fabric(config)
```

## Next Steps

- See [examples/fabric](../../examples/fabric) for complete examples
- Read about [Protocol Adapters](./adapters.md) for custom protocols
- Learn about [Advanced Patterns](./patterns.md) for complex workflows
