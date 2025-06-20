# AgentiCraft Protocol Fabric - Official SDK Support

## Overview

The AgentiCraft Protocol Fabric now supports **official SDKs** for all major agent protocols while maintaining full backward compatibility. This implementation provides seamless integration with:

- **MCP SDK**: Model Context Protocol official Python SDK
- **A2A SDK**: Google's Agent-to-Agent Protocol SDK  
- **IBM ACP**: Bee framework-based implementation
- **ANP**: Custom implementation (no official SDK yet)

## Quick Start

### Using Official SDKs

```python
from agenticraft.fabric import UnifiedProtocolFabric, SDKPreference

# Create fabric with official SDK preferences
fabric = UnifiedProtocolFabric(
    sdk_preferences={
        'mcp': SDKPreference.OFFICIAL,
        'a2a': SDKPreference.OFFICIAL,
        'acp': SDKPreference.OFFICIAL,
        'anp': SDKPreference.CUSTOM
    }
)

# Use as normal - SDKs are handled transparently
await fabric.register_server('mcp', 'http://localhost:3000')
```

### Hybrid Mode (Recommended)

```python
# Official SDKs with automatic fallback to custom implementations
fabric = UnifiedProtocolFabric(
    sdk_preferences={
        'mcp': SDKPreference.HYBRID,
        'a2a': SDKPreference.HYBRID,
        'acp': SDKPreference.HYBRID,
        'anp': SDKPreference.CUSTOM
    }
)
```

### Automatic SDK Selection

```python
# Let AgentiCraft choose the best implementation
fabric = UnifiedProtocolFabric(
    sdk_preferences={'mcp': SDKPreference.AUTO}
)
```

## Installation

```bash
# Install AgentiCraft with SDK support
pip install agenticraft

# Install official SDKs (optional)
pip install mcp                    # MCP SDK
pip install a2a-protocol           # A2A SDK
pip install aiohttp                # Required for ACP
```

## Key Features

### 1. Zero Breaking Changes
Your existing code continues to work without modification:

```python
@agent("my_agent", servers=["http://localhost:3000/mcp"])
async def my_agent(self, task: str):
    return await self.tools.process(task)
```

### 2. SDK Preferences
Configure SDK usage per protocol:

- `OFFICIAL` - Use only official SDK
- `CUSTOM` - Use only AgentiCraft implementation
- `HYBRID` - Official with custom fallback
- `AUTO` - Automatically choose best option

### 3. Feature Preservation
AgentiCraft's unique features work with any SDK:

```python
# These work regardless of SDK choice
await fabric.create_mesh_network(['agent1', 'agent2'])
await fabric.enable_consensus(min_agents=3)
await fabric.enable_reasoning_traces()
```

### 4. Migration Tools

```python
# Check SDK availability
info = fabric.get_sdk_info()
print(info['availability'])

# Test migration
results = await fabric.migrate_to_official_sdks(test_mode=True)

# Update preferences dynamically
fabric.update_sdk_preference('mcp', SDKPreference.OFFICIAL)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Agent Code                       │
├─────────────────────────────────────────────────────────┤
│                 UnifiedProtocolFabric                    │
│                   (SDK-Enabled)                          │
├─────────────────────────────────────────────────────────┤
│                   AdapterFactory                         │
│         (Intelligent SDK/Custom Selection)               │
├────────────┬────────────┬────────────┬─────────────────┤
│    MCP     │    A2A     │    ACP     │      ANP        │
├────────────┼────────────┼────────────┼─────────────────┤
│  Official  │  Official  │    Bee     │    Custom       │
│    SDK     │    SDK     │ Framework  │ Implementation  │
│     ↕      │     ↕      │     ↕      │                 │
│  Custom    │  Custom    │  Custom    │                 │
│   Impl.    │   Impl.    │   Impl.    │                 │
└────────────┴────────────┴────────────┴─────────────────┘
```

## SDK Status

| Protocol | Official SDK | Custom | Hybrid | Recommended |
|----------|-------------|--------|--------|-------------|
| MCP | ✅ Available | ✅ | ✅ | Hybrid |
| A2A | ✅ Available | ✅ | ✅ | Hybrid |
| ACP | 🔧 Bee Framework | ✅ | ✅ | Official |
| ANP | ❌ Not yet | ✅ | N/A | Custom |

## Examples

See [SDK Migration Examples](./examples/fabric/sdk_migration_examples.py) for:
- Using official SDKs
- Hybrid mode configuration
- Gradual migration strategy
- Real-world multi-protocol agents

## Documentation

- [SDK Migration Guide](./agenticraft/fabric/adapters/SDK_MIGRATION_GUIDE.md)
- [API Reference](./agenticraft/fabric/adapters/)
- [Test Suite](./tests/fabric/test_sdk_integration.py)

## Benefits

1. **Future-Proof**: Ready for official SDKs as they become available
2. **Flexible**: Choose implementation based on your needs
3. **Safe**: Hybrid mode prevents failures with automatic fallback
4. **Compatible**: No changes required to existing agent code
5. **Innovative**: AgentiCraft features work with any SDK

## Contributing

We welcome contributions! Areas of interest:
- Additional protocol SDK adapters
- Performance optimizations
- Cross-protocol translation
- SDK compatibility testing

## License

MIT License - See LICENSE file for details
