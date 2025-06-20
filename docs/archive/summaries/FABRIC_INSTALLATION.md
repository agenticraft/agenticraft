# Protocol Fabric Installation Guide

## Basic Installation

```bash
# Install AgentiCraft with protocol fabric
pip install agenticraft
```

## Feature-Specific Installation

AgentiCraft supports optional features through extras:

```bash
# Install with all protocol features
pip install agenticraft[protocols]

# Install with official SDK support
pip install agenticraft[sdk]

# Install with telemetry support
pip install agenticraft[telemetry]

# Install with all integrations
pip install agenticraft[all]
```

## Setup.py Extras Configuration

Add this to your `setup.py`:

```python
extras_require = {
    # Protocol support
    'protocols': [
        'aiohttp>=3.8.0',
        'websockets>=10.0',
    ],
    
    # Official SDK support (when available)
    'sdk': [
        # 'mcp>=0.1.0',
        # 'a2a-protocol>=0.1.0',
    ],
    
    # Telemetry integration
    'telemetry': [
        'opentelemetry-api>=1.15.0',
        'opentelemetry-sdk>=1.15.0',
        'opentelemetry-exporter-prometheus>=0.36b0',
    ],
    
    # Memory integration
    'memory': [
        'redis>=4.0.0',
        'chromadb>=0.3.0',
    ],
    
    # Security features
    'security': [
        'cryptography>=38.0.0',
        'pyjwt>=2.6.0',
    ],
    
    # All integrations
    'all': [
        'aiohttp>=3.8.0',
        'websockets>=10.0',
        'opentelemetry-api>=1.15.0',
        'opentelemetry-sdk>=1.15.0',
        'redis>=4.0.0',
        'cryptography>=38.0.0',
    ],
    
    # Development
    'dev': [
        'pytest>=7.0.0',
        'pytest-asyncio>=0.21.0',
        'black>=23.0.0',
        'mypy>=1.0.0',
        'pytest-cov>=4.0.0',
    ],
}
```

## Checking Installed Features

```python
# Check what's available
from agenticraft.fabric import UnifiedProtocolFabric

fabric = UnifiedProtocolFabric()

# Check SDK availability
sdk_info = fabric.get_sdk_info()
print("Available SDKs:", sdk_info['availability'])

# Check feature support
try:
    from agenticraft.reasoning import ChainOfThoughtReasoning
    print("✓ Reasoning patterns available")
except ImportError:
    print("✗ Reasoning patterns not installed")

try:
    from agenticraft.telemetry import get_tracer
    print("✓ Telemetry available")
except ImportError:
    print("✗ Telemetry not installed")
```

## Minimal Installation

For minimal protocol fabric without extras:

```bash
pip install agenticraft
pip install aiohttp  # For HTTP protocols
```

This gives you:
- Basic protocol fabric functionality
- MCP and A2A protocol support (custom implementations)
- Agent decorators
- Tool discovery and execution

## Recommended Installation

For most use cases:

```bash
pip install agenticraft[protocols,telemetry]
```

This gives you:
- Full protocol support
- Performance monitoring
- Distributed tracing
- Metrics collection

## Enterprise Installation

For production deployments:

```bash
pip install agenticraft[all]
```

This includes:
- All protocol implementations
- Security features
- Telemetry and monitoring
- Memory persistence
- High-performance backends
