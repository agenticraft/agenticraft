Great question! Let me analyze whether we can remove AgentiCraft's custom tool system after implementing the SDK integration.# Can We Get Rid of AgentiCraft's Custom Tools?

## Short Answer: **No, but we can simplify and consolidate**

After reviewing the codebase, I recommend **keeping a minimal tool abstraction layer** while delegating most functionality to the official SDKs. Here's why and how:

## Current Tool System Analysis

### What AgentiCraft's Tool System Provides:

1. **Unified Interface** (`BaseTool`)
   - Consistent `arun()` and `run()` methods
   - Standard `get_definition()` for schema generation
   - Error handling with `ToolExecutionError`

2. **Function-to-Tool Conversion** (`@tool` decorator)
   - Automatic parameter extraction from function signatures
   - Type mapping (Python types → JSON schema)
   - Sync/async handling

3. **Tool Registry**
   - Centralized tool management
   - Dynamic tool execution
   - Schema generation for LLM providers

4. **Provider Compatibility**
   - Converts tools to OpenAI function calling format
   - Handles tool results in conversation flow
   - Manages tool call/response sequencing

## Why We Can't Completely Remove It

### 1. **Provider Abstraction** ⚡
The tool system acts as a bridge between different LLM providers:
```python
# AgentiCraft normalizes tools for any provider
tools_schema = self._tool_registry.get_tools_schema()  # Works with OpenAI, Anthropic, etc.
```

### 2. **SDK Tools Need Adaptation** 🔄
MCP tools from SDKs need to be adapted to work with AgentiCraft agents:
```python
# Current code already does this!
class MCPToolAdapter(BaseTool):
    """Adapter to use MCP tools as AgentiCraft tools."""
    def __init__(self, mcp_tool: MCPTool, client: MCPClient):
        # Wraps MCP tool in AgentiCraft interface
```

### 3. **Local Tools Still Needed** 🛠️
Not everything will come from MCP servers:
- Quick utility functions
- Agent-specific logic
- Tools that don't justify a full MCP server

### 4. **Backward Compatibility** 📦
Existing AgentiCraft users have tools that need to keep working.

## Recommended Approach: Minimal Tool Layer + SDK Integration

### Phase 1: Simplify Core Tool System

```python
# /agenticraft/core/tool_minimal.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """Minimal tool interface for AgentiCraft."""
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM."""
        pass
```

### Phase 2: SDK-First Tool Discovery

```python
# /agenticraft/fabric/tool_fabric.py
class UnifiedToolFabric:
    """Unified tool management across protocols."""
    
    def __init__(self):
        self.local_tools = {}      # AgentiCraft native tools
        self.mcp_tools = {}        # From MCP servers
        self.a2a_capabilities = {} # From A2A agents
        
    async def discover_tools(self):
        """Discover tools from all sources."""
        # 1. MCP servers (primary source)
        for server in self.mcp_servers:
            tools = await server.list_tools()
            self.mcp_tools.update(tools)
            
        # 2. A2A agents (as tools)
        for agent in self.a2a_registry:
            self.a2a_capabilities[agent.id] = agent.capabilities
            
        # 3. Local tools (fallback)
        # Keep minimal local tools
```

### Phase 3: Fast-Agent Style Decorators

```python
# /agenticraft/decorators.py
@agent("researcher", servers=["brave_search", "arxiv"])
async def research_agent(self, topic: str):
    # Tools from MCP servers are automatically available
    results = await self.tools.brave_search(query=topic)
    papers = await self.tools.arxiv.search(topic)
    
    # But can still use local tools if needed
    summary = await self.tools.local.summarize(results + papers)
    
    return summary
```

## Migration Strategy

### What to Keep:

1. **Tool Interface** (simplified)
   - Just `execute()` and `get_schema()`
   - Remove complex validation

2. **Tool Registry** (modified)
   - Primarily for routing to SDKs
   - Minimal local tool storage

3. **Provider Adapters**
   - Convert SDK tools to provider format
   - Handle tool results

### What to Remove:

1. **Complex Tool Validation** ❌
   - Let SDKs handle their own validation

2. **Tool Parameter Parsing** ❌
   - Use SDK-provided schemas

3. **Custom Tool Types** ❌
   - Everything is either SDK tool or simple function

### What to Add:

1. **SDK Tool Priority** ✅
```python
async def get_tool(self, name: str) -> Tool:
    # 1. Check MCP tools first
    if name in self.mcp_tools:
        return MCPToolAdapter(self.mcp_tools[name])
    
    # 2. Check A2A capabilities
    if name in self.a2a_capabilities:
        return A2AToolAdapter(self.a2a_capabilities[name])
    
    # 3. Fall back to local tools
    if name in self.local_tools:
        return self.local_tools[name]
    
    raise ToolNotFoundError(name)
```

2. **Unified Tool Access** ✅
```python
# All tools accessible through single interface
self.tools.brave_search()     # MCP tool
self.tools.analyze()          # A2A agent capability  
self.tools.calculate()        # Local tool
```

## Benefits of This Approach

### 1. **Simplicity** ✨
- Minimal code to maintain
- Clear separation of concerns
- SDK complexity hidden

### 2. **Compatibility** 🔧
- Existing tools keep working
- Gradual migration path
- No breaking changes

### 3. **Flexibility** 🎯
- Use best tool source for each case
- Mix local and remote tools
- Easy to extend

### 4. **Performance** 🚀
- Local tools for low latency
- SDK tools for complex operations
- Intelligent routing

## Example Implementation

```python
# Simplified tool usage with SDK integration
from agenticraft import agent

@agent(
    "analyst",
    servers=["mcp://github", "mcp://jupyter"],
    local_tools=["quick_calc", "format_report"]
)
async def data_analyst(self, repo: str):
    # SDK tools (from MCP)
    code = await self.tools.github.get_file(repo, "analysis.py")
    results = await self.tools.jupyter.execute(code)
    
    # Local tool (for performance)
    stats = await self.tools.quick_calc(results)
    
    # Format with local tool
    report = await self.tools.format_report(stats)
    
    return report
```

## Conclusion

**Don't remove the tool system entirely**. Instead:

1. **Simplify** it to a minimal routing layer
2. **Prioritize** SDK tools (MCP, A2A)
3. **Keep** local tools for performance and simplicity
4. **Hide** complexity behind elegant decorators

This gives you the best of both worlds:
- ✅ Full SDK ecosystem access
- ✅ Backward compatibility
- ✅ Performance for simple operations
- ✅ Clean, simple API

The tool system becomes a thin orchestration layer rather than a complex implementation, which aligns perfectly with the SDK integration strategy.