# Official SDK Migration Guide

This guide explains how to migrate AgentiCraft to use official protocol SDKs while maintaining backward compatibility.

## Quick Start

```python
from agenticraft.fabric import UnifiedProtocolFabric
from agenticraft.fabric.adapters import SDKPreference

# Use official SDKs where available
fabric = UnifiedProtocolFabric(
    sdk_preferences={
        'mcp': SDKPreference.OFFICIAL,
        'a2a': SDKPreference.OFFICIAL,
        'acp': SDKPreference.OFFICIAL,  # Uses Bee framework patterns
        'anp': SDKPreference.CUSTOM    # No official SDK yet
    }
)
```

## Installation

### 1. MCP Official SDK
```bash
# Install from PyPI (when available)
pip install mcp

# Or install from GitHub
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
```

### 2. A2A Official SDK
```bash
# Install from PyPI (when available)
pip install a2a-protocol

# Or install from GitHub
pip install git+https://github.com/google-a2a/a2a-python.git
```

### 3. IBM ACP (Bee Framework)
```bash
# No official Python SDK yet, but we implement the protocol
# Our adapter follows IBM's Bee framework patterns
pip install aiohttp  # Required for REST communication
```

## Configuration

### Using Official SDKs Globally

```python
# config.yaml
fabric:
  sdk_preferences:
    mcp: official    # Use official MCP SDK
    a2a: official    # Use official A2A SDK
    acp: official    # Use Bee framework patterns
    anp: custom      # No SDK available
  
  # Fallback to custom implementation if SDK fails
  fallback_enabled: true
  
  # Feature requirements (affects SDK selection)
  required_features:
    - tools
    - discovery
    - streaming
```

### Per-Agent SDK Selection

```python
@agent(
    "my_agent",
    servers=["http://localhost:3000/mcp"],
    sdk_preference="official"  # Use official SDK for this agent
)
async def my_agent(self, task: str):
    return await self.tools.process(task)
```

### Hybrid Mode (Recommended)

```python
# Use official SDKs with custom fallback
fabric = UnifiedProtocolFabric(
    sdk_preferences={
        'mcp': SDKPreference.HYBRID,  # Official + custom fallback
        'a2a': SDKPreference.HYBRID,
        'acp': SDKPreference.HYBRID,
        'anp': SDKPreference.CUSTOM
    }
)
```

## Feature Compatibility

### MCP SDK Features

| Feature | Official SDK | Custom | Notes |
|---------|-------------|--------|-------|
| Tool Discovery | ✅ | ✅ | Full support |
| Tool Execution | ✅ | ✅ | Full support |
| Resources | ✅ | ✅ | MCP-specific |
| Prompts | ✅ | ✅ | MCP-specific |
| Streaming | ✅ | ⚠️ | Better in official |
| Schema Validation | ✅ | ❌ | Official only |

### A2A SDK Features

| Feature | Official SDK | Custom | Notes |
|---------|-------------|--------|-------|
| Agent Discovery | ✅ | ✅ | Full support |
| Trust/Cards | ✅ | ⚠️ | Better in official |
| Messaging | ✅ | ✅ | Full support |
| Delegation | ✅ | ❌ | Official only |
| Mesh Networking | ❌ | ✅ | AgentiCraft unique |

### IBM ACP Features (Bee Framework)

| Feature | Bee Adapter | Custom | Notes |
|---------|------------|--------|-------|
| REST Communication | ✅ | ✅ | Full support |
| Session Management | ✅ | ✅ | Full support |
| Tool Orchestration | ✅ | ✅ | Full support |
| Workflows | ✅ | ❌ | Bee framework |
| Async Execution | ✅ | ⚠️ | Better in Bee |

## Migration Examples

### Example 1: MCP Migration

```python
# Before: Using custom implementation
from agenticraft.fabric import UnifiedProtocolFabric

fabric = UnifiedProtocolFabric()
await fabric.register_server("mcp", "http://localhost:3000")

# After: Using official SDK
from agenticraft.fabric.adapters import SDKPreference

fabric = UnifiedProtocolFabric(
    sdk_preferences={'mcp': SDKPreference.OFFICIAL}
)
await fabric.register_server("mcp", {
    "url": "http://localhost:3000",
    "transport": "sse"  # Official SDK options
})
```

### Example 2: A2A Migration with Trust

```python
# Using official A2A SDK with trust verification
fabric = UnifiedProtocolFabric(
    sdk_preferences={'a2a': SDKPreference.OFFICIAL}
)

await fabric.register_server("a2a", {
    "url": "http://localhost:8080",
    "name": "my-agent",
    "private_key": private_key,  # For signing
    "public_key": public_key,    # For verification
    "trusted_agents": [          # Trust list
        "agent1.public.key",
        "agent2.public.key"
    ]
})
```

### Example 3: IBM ACP with Workflows

```python
# Using Bee framework patterns
fabric = UnifiedProtocolFabric(
    sdk_preferences={'acp': SDKPreference.OFFICIAL}
)

# Register ACP server
await fabric.register_server("acp", {
    "url": "http://localhost:9000",
    "agent_id": "workflow-agent",
    "capabilities": ["workflow-execution"]
})

# Create and execute workflow
adapter = fabric.get_adapter("acp")
workflow_id = await adapter.create_workflow({
    "name": "data-pipeline",
    "steps": [
        {"tool": "fetch_data", "inputs": {"source": "api"}},
        {"tool": "process_data", "inputs": {"format": "json"}},
        {"tool": "store_data", "inputs": {"destination": "db"}}
    ]
})

result = await adapter.execute_workflow(
    workflow_id,
    {"initial_params": {"date": "2024-01-01"}}
)
```

## Gradual Migration Strategy

### Phase 1: Test Official SDKs
```python
# Start with one protocol
fabric = UnifiedProtocolFabric(
    sdk_preferences={
        'mcp': SDKPreference.OFFICIAL,  # Test MCP first
        'a2a': SDKPreference.CUSTOM,
        'acp': SDKPreference.CUSTOM,
        'anp': SDKPreference.CUSTOM
    }
)
```

### Phase 2: Enable Hybrid Mode
```python
# Use official with fallback
fabric = UnifiedProtocolFabric(
    sdk_preferences={
        'mcp': SDKPreference.HYBRID,
        'a2a': SDKPreference.HYBRID,
        'acp': SDKPreference.CUSTOM,
        'anp': SDKPreference.CUSTOM
    }
)
```

### Phase 3: Full Migration
```python
# All protocols using best available option
fabric = UnifiedProtocolFabric(
    sdk_preferences={
        'mcp': SDKPreference.OFFICIAL,
        'a2a': SDKPreference.OFFICIAL,
        'acp': SDKPreference.OFFICIAL,
        'anp': SDKPreference.CUSTOM  # Until SDK available
    }
)
```

## Preserving AgentiCraft Features

Even when using official SDKs, AgentiCraft's unique features remain available:

```python
# Enable extensions with official SDKs
fabric = UnifiedProtocolFabric(
    sdk_preferences={'mcp': SDKPreference.OFFICIAL}
)

# AgentiCraft extensions still work!
await fabric.enable_extension('mesh_networking')
await fabric.enable_extension('consensus', min_agents=3)
await fabric.enable_extension('reasoning_traces')

# Use in agents
@agent(
    "advanced_agent",
    servers=["http://localhost:3000/mcp"],
    extensions={'mesh': True, 'consensus': 'byzantine'}
)
async def my_agent(self, task: str):
    # Official SDK + AgentiCraft features
    result = await self.tools.analyze(task)
    
    # Use consensus
    decision = await self.consensus.decide(
        options=result['options'],
        min_votes=3
    )
    
    return decision
```

## Troubleshooting

### SDK Not Found
```python
# Check SDK availability
from agenticraft.fabric.adapters import AdapterFactory

status = AdapterFactory.get_available_adapters()
print(status)
# {'mcp': {'official': True, 'custom': True, 'hybrid': True}, ...}
```

### Feature Not Supported
```python
# Check feature support
adapter = AdapterFactory.create_adapter(
    ProtocolType.MCP,
    SDKPreference.OFFICIAL
)
print(adapter.supports_feature('streaming'))  # True
print(adapter.supports_feature('mesh_networking'))  # False
```

### Automatic Fallback
```python
# Hybrid mode handles failures gracefully
fabric = UnifiedProtocolFabric(
    sdk_preferences={'mcp': SDKPreference.HYBRID}
)

# If official SDK fails, automatically uses custom
result = await fabric.execute_tool(
    'mcp', 'experimental_tool', {}
)  # Works even if not in official SDK
```

## Performance Considerations

- **Official SDKs**: Generally more optimized and maintained
- **Custom Implementation**: More flexible, supports all AgentiCraft features
- **Hybrid Mode**: Best balance of performance and features

## Next Steps

1. Install official SDKs as they become available
2. Test with hybrid mode first
3. Monitor performance and feature usage
4. Gradually move to official SDKs where beneficial
5. Keep custom implementations for unique features

The migration is designed to be gradual and non-breaking. Your existing code continues to work while you gain the benefits of official SDKs!
