# Migration Guide: Moving to Unified Protocol Fabric

This guide helps you migrate from direct protocol usage to the new Unified Protocol Fabric with decorator-based agents.

## Overview of Changes

The Unified Protocol Fabric simplifies agent creation and protocol management:

- **Before**: Manual protocol setup, explicit tool management
- **After**: Decorator-based agents with automatic tool discovery

## Migration Examples

### Example 1: Simple MCP Agent

#### Before (Direct MCP Usage)
```python
from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient

# Manual setup required
async def create_research_agent():
    # Connect to MCP server
    mcp_client = MCPClient("http://localhost:3000")
    await mcp_client.connect()
    
    # Get tools manually
    mcp_tools = mcp_client.get_tools()
    
    # Create agent with tools
    agent = Agent(
        name="researcher",
        tools=mcp_tools,
        model="gpt-4"
    )
    
    return agent, mcp_client

# Usage
agent, client = await create_research_agent()
response = await agent.arun("Research AI safety")

# Manual cleanup
await client.disconnect()
```

#### After (Unified Fabric)
```python
from agenticraft.fabric import agent

@agent("researcher", servers=["http://localhost:3000/mcp"])
async def research_agent(self, topic: str):
    # Direct tool access - no setup needed
    results = await self.tools.web_search(query=topic)
    return await self.tools.summarize(text=results)

# Usage - much simpler!
response = await research_agent("Research AI safety")
```

### Example 2: Multi-Protocol Agent

#### Before (Manual Multi-Protocol)
```python
from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient
from agenticraft.protocols.a2a import A2AClient

async def create_multi_protocol_agent():
    # Setup multiple protocols manually
    mcp_client = MCPClient("http://localhost:3000")
    await mcp_client.connect()
    
    a2a_client = A2AClient("http://localhost:8080")
    await a2a_client.connect()
    
    # Combine tools from both protocols
    all_tools = []
    all_tools.extend(mcp_client.get_tools())
    
    # A2A tools need manual wrapping
    for agent_card in await a2a_client.discover_agents():
        for skill in agent_card.skills:
            # Create tool wrapper for A2A skill
            tool = create_a2a_tool_wrapper(a2a_client, agent_card.id, skill)
            all_tools.append(tool)
    
    agent = Agent(name="multi_agent", tools=all_tools)
    return agent, mcp_client, a2a_client
```

#### After (Unified Fabric)
```python
from agenticraft.fabric import agent

@agent(
    "multi_agent",
    servers=[
        "http://localhost:3000/mcp",
        "http://localhost:8080/a2a"
    ]
)
async def multi_protocol_agent(self, task: str):
    # Use tools from any protocol seamlessly
    mcp_result = await self.tools.web_search(query=task)
    a2a_result = await self.tools.analyze_data(data=mcp_result)
    return a2a_result
```

### Example 3: Reasoning Agent with Tools

#### Before
```python
from agenticraft import ReasoningAgent
from agenticraft.protocols.mcp import MCPClient

async def create_reasoning_agent():
    client = MCPClient("http://localhost:3000")
    await client.connect()
    
    agent = ReasoningAgent(
        name="thinker",
        tools=client.get_tools(),
        reasoning_pattern="chain_of_thought",
        model="gpt-4"
    )
    
    return agent, client
```

#### After
```python
from agenticraft.fabric import agent

@agent(
    "thinker",
    servers=["http://localhost:3000/mcp"],
    reasoning="chain_of_thought",
    model="gpt-4"
)
async def reasoning_agent(self, problem: str):
    # Reasoning is automatically enabled
    analysis = await self.tools.analyze(text=problem)
    solution = await self.tools.solve(problem=analysis)
    return solution
```

## Step-by-Step Migration Process

### Step 1: Update Imports

```python
# Old imports
from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient
from agenticraft.protocols.a2a import A2AClient

# New imports
from agenticraft.fabric import agent, UnifiedProtocolFabric
```

### Step 2: Convert Agent Creation

Replace manual agent creation with decorators:

```python
# Old pattern
async def create_agent():
    client = MCPClient(url)
    await client.connect()
    agent = Agent(name="my_agent", tools=client.get_tools())
    return agent

# New pattern
@agent("my_agent", servers=[url])
async def my_agent(self, prompt: str):
    # Your agent logic here
    pass
```

### Step 3: Update Tool Usage

Replace explicit tool calls with natural access:

```python
# Old pattern
tool = next(t for t in agent.tools if t.name == "search")
result = await tool.arun(query="AI")

# New pattern
result = await self.tools.search(query="AI")
```

### Step 4: Remove Manual Cleanup

The fabric handles all connection management:

```python
# Old pattern - manual cleanup needed
try:
    agent, client = await create_agent()
    result = await agent.arun(prompt)
finally:
    await client.disconnect()

# New pattern - automatic cleanup
result = await my_agent(prompt)
```

## Migration Patterns

### Pattern 1: Gradual Migration

Keep existing code working while migrating:

```python
from agenticraft.fabric import UnifiedProtocolFabric

# Create fabric that wraps existing clients
fabric = UnifiedProtocolFabric()

# Register your existing protocol clients
if hasattr(your_module, 'mcp_client'):
    await fabric.initialize({
        "mcp": {"servers": [{"url": your_mcp_url}]}
    })

# Now you can use both old and new patterns
```

### Pattern 2: Configuration-Based Migration

Move settings to YAML:

```yaml
# agenticraft.yaml
agents:
  researcher:
    servers:
      - http://localhost:3000/mcp
    model: gpt-4
    
  analyst:
    servers:
      - http://localhost:8080/a2a
    reasoning: tree_of_thoughts
```

```python
from agenticraft.fabric import from_config, agent

@from_config("agenticraft.yaml")
class MigratedAgents:
    @agent("researcher")
    async def research(self, topic):
        return await self.tools.search(topic)
```

### Pattern 3: Backward Compatibility

Create a compatibility wrapper:

```python
from agenticraft.fabric import agent as fabric_agent

def legacy_agent_wrapper(name: str, mcp_url: str):
    """Compatibility wrapper for old code."""
    
    @fabric_agent(name, servers=[mcp_url])
    async def wrapped_agent(self, prompt: str):
        return await self.arun(prompt)
    
    # Make it look like old agent
    class LegacyCompatibleAgent:
        async def arun(self, prompt: str):
            return await wrapped_agent(prompt)
    
    return LegacyCompatibleAgent()
```

## Common Migration Issues

### Issue 1: Tool Name Changes

**Problem**: Tool names might be namespaced differently

**Solution**: Use short names or check available tools
```python
# List all available tools
fabric = get_global_fabric()
tools = fabric.get_tools()
print([t.name for t in tools])
```

### Issue 2: Async Context

**Problem**: Decorator creates async context automatically

**Solution**: Ensure your agent functions are async
```python
# Wrong
@agent("my_agent", servers=[...])
def my_agent(self, prompt):  # Not async!
    return self.tools.search(prompt)

# Correct  
@agent("my_agent", servers=[...])
async def my_agent(self, prompt):  # Async function
    return await self.tools.search(prompt)
```

### Issue 3: Multiple Agent Instances

**Problem**: Need multiple instances of same agent type

**Solution**: Create agent factory
```python
def create_researcher(name: str, specialty: str):
    @agent(name, servers=["http://localhost:3000/mcp"])
    async def researcher(self, topic: str):
        context = f"As a {specialty} specialist, research: {topic}"
        return await self.tools.search(query=context)
    
    return researcher

# Create specialized researchers
ai_researcher = create_researcher("ai_researcher", "AI Safety")
ml_researcher = create_researcher("ml_researcher", "Machine Learning")
```

## Testing Your Migration

### Unit Tests

Update your tests to use the new patterns:

```python
# Old test
async def test_agent():
    client = MCPClient("http://test-server")
    await client.connect()
    agent = Agent("test", tools=client.get_tools())
    result = await agent.arun("test prompt")
    assert result is not None
    await client.disconnect()

# New test
async def test_agent():
    @agent("test", servers=["http://test-server"])
    async def test_agent(self, prompt):
        return await self.tools.test_tool(prompt=prompt)
    
    result = await test_agent("test prompt")
    assert result is not None
```

### Integration Tests

Test multi-protocol scenarios:

```python
async def test_multi_protocol():
    @agent("integrated", servers=[
        "http://localhost:3000/mcp",
        "http://localhost:8080/a2a"
    ])
    async def integrated_agent(self, task):
        # Test cross-protocol communication
        mcp_data = await self.tools.fetch_data()
        a2a_result = await self.tools.process_remotely(data=mcp_data)
        return a2a_result
    
    result = await integrated_agent("test task")
    assert "mcp:" in str(result) or "a2a:" in str(result)
```

## Benefits After Migration

1. **Less Code**: 80% reduction in boilerplate
2. **Better Errors**: Automatic connection handling and retries  
3. **Tool Discovery**: No manual tool management
4. **Protocol Agnostic**: Switch protocols without code changes
5. **Type Safety**: Better IDE support with tool proxy

## Next Steps

1. Start with one simple agent
2. Test the migration thoroughly
3. Gradually migrate complex agents
4. Update your documentation
5. Remove old protocol management code

For more examples, see the [examples/fabric](../../examples/fabric) directory.
