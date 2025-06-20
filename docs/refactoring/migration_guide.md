# AgentiCraft Refactoring Migration Guide

## Overview

This guide helps you migrate from the old AgentiCraft structure to the new refactored architecture. The refactoring introduces cleaner separation of concerns, reduces code duplication, and provides a more maintainable codebase.

## Key Changes

### 1. Core Abstractions Layer

**Old Structure:**
- Transport, auth, and registry were scattered across protocol implementations
- Duplicate code in MCP and A2A protocols

**New Structure:**
- Centralized in `agenticraft.core`:
  - `core.transport` - Protocol-agnostic transport layer
  - `core.auth` - Unified authentication system
  - `core.registry` - Common service registry
  - `core.patterns` - Reusable communication patterns
  - `core.serialization` - Common serialization utilities

### 2. Protocol Implementations

**Old Structure:**
```python
# Protocols had their own transport/auth
from agenticraft.protocols.mcp.transport import HTTPTransport
from agenticraft.protocols.mcp.auth import BearerAuth
```

**New Structure:**
```python
# Use core abstractions
from agenticraft.core.transport import HTTPTransport
from agenticraft.core.auth import BearerAuthProvider, AuthConfig
```

### 3. Unified Agent Interface

**Old Structure:**
```python
# Multiple unified files
from agenticraft.fabric.unified import UnifiedFabric
from agenticraft.fabric.unified_enhanced import EnhancedFabric
from agenticraft.fabric.sdk_fabric import SDKFabric
```

**New Structure:**
```python
# Single, clean interface
from agenticraft.fabric import UnifiedAgent
```

## Migration Steps

### Step 1: Update Imports

#### Transport Imports

**Before:**
```python
from agenticraft.protocols.mcp.transport import HTTPTransport, WebSocketTransport
from agenticraft.protocols.mcp.transport.base import IMCPTransport
```

**After:**
```python
from agenticraft.core.transport import HTTPTransport, WebSocketTransport, Transport
```

#### Auth Imports

**Before:**
```python
from agenticraft.protocols.mcp.auth.bearer import BearerAuth
from agenticraft.protocols.mcp.auth.api_key import APIKeyAuth
```

**After:**
```python
from agenticraft.core.auth import (
    AuthConfig,
    BearerAuthProvider,
    APIKeyAuthProvider
)
```

#### Registry Imports

**Before:**
```python
from agenticraft.protocols.a2a.registry import ProtocolRegistry
from agenticraft.protocols.mcp.registry import MCPRegistry
```

**After:**
```python
from agenticraft.core.registry import ServiceRegistry, InMemoryRegistry
```

### Step 2: Update Agent Creation

#### Simple MCP Agent

**Before:**
```python
from agenticraft.fabric.unified import UnifiedFabric

fabric = UnifiedFabric()
agent = fabric.create_mcp_agent(
    name="my-agent",
    url="http://localhost:8080",
    auth_token="secret"
)
```

**After:**
```python
from agenticraft.fabric import create_mcp_agent

agent = create_mcp_agent(
    name="my-agent",
    url="http://localhost:8080",
    auth_config=AuthConfig.bearer("secret")
)
```

#### A2A Agent

**Before:**
```python
from agenticraft.fabric.unified_enhanced import EnhancedFabric

fabric = EnhancedFabric()
agent = fabric.create_a2a_agent(
    name="my-agent",
    pattern="mesh",
    peers=["peer1", "peer2"]
)
```

**After:**
```python
from agenticraft.fabric import create_a2a_agent

agent = create_a2a_agent(
    name="my-agent",
    pattern="mesh",
    peers=["peer1", "peer2"]
)
```

### Step 3: Update Complex Agent Configurations

#### Using the Builder Pattern

**Before:**
```python
fabric = UnifiedFabric()
agent = fabric.create_agent(name="complex-agent")
agent.add_mcp_support(url="http://localhost:8080")
agent.add_a2a_support(pattern="mesh")
agent.configure_auth("bearer", token="secret")
```

**After:**
```python
from agenticraft.fabric import AgentBuilder

agent = (AgentBuilder("complex-agent")
    .with_mcp("http://localhost:8080")
    .with_a2a("mesh")
    .with_auth(AuthConfig.bearer("secret"))
    .with_registry()
    .build())
```

### Step 4: Update Protocol-Specific Code

#### MCP Protocol

**Before:**
```python
from agenticraft.protocols.mcp import MCPClient
from agenticraft.protocols.mcp.types import MCPRequest

client = MCPClient(url="http://localhost:8080")
request = MCPRequest(method="tools/list", params={})
response = await client.send_request(request)
```

**After:**
```python
from agenticraft.protocols.mcp import MCPProtocol
from agenticraft.core.transport import HTTPTransport

transport = HTTPTransport(TransportConfig(url="http://localhost:8080"))
protocol = MCPProtocol(transport=transport)

await protocol.start()
response = await protocol.request(method="tools/list", params={})
```

#### A2A Protocol

**Before:**
```python
from agenticraft.protocols.a2a import Protocol
from agenticraft.protocols.a2a.mesh_network import MeshNetwork

protocol = MeshNetwork(node_id="node1")
await protocol.join_network(["peer1", "peer2"])
```

**After:**
```python
from agenticraft.protocols.a2a import A2AProtocol

protocol = A2AProtocol(
    pattern="mesh",
    node_id="node1",
    peers=["peer1", "peer2"]
)
await protocol.start()
```

### Step 5: Update Service Registry Usage

**Before:**
```python
# Different registries for different protocols
from agenticraft.protocols.mcp.registry import MCPRegistry
from agenticraft.protocols.a2a.registry import ProtocolRegistry

mcp_registry = MCPRegistry()
a2a_registry = ProtocolRegistry()
```

**After:**
```python
# Single unified registry
from agenticraft.core.registry import InMemoryRegistry

registry = InMemoryRegistry()

# Register any service
await registry.register(
    name="my-service",
    service_type="mcp",
    endpoint="http://localhost:8080"
)
```

### Step 6: Update Authentication

**Before:**
```python
# Protocol-specific auth
from agenticraft.protocols.mcp.auth.bearer import BearerAuth

auth = BearerAuth()
token = auth.generate_token("client-id", permissions={"read", "write"})
```

**After:**
```python
# Unified auth system
from agenticraft.core.auth import AuthManager, AuthConfig

auth_manager = AuthManager()
auth_manager.set_auth(AuthConfig.bearer("token"))

# Or use specific providers
from agenticraft.core.auth import BearerAuthProvider

provider = BearerAuthProvider(AuthConfig.bearer("token"))
headers = provider.get_headers()
```

## Backwards Compatibility

We provide a compatibility layer to ease migration:

```python
# This will work but show deprecation warnings
from agenticraft.fabric.compat import UnifiedFabric

# The compatibility layer maps to new interfaces
fabric = UnifiedFabric()  # Shows deprecation warning
```

To silence deprecation warnings during migration:

```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

## Common Migration Issues

### Issue 1: Import Errors

**Problem:**
```
ImportError: cannot import name 'IMCPTransport' from 'agenticraft.protocols.mcp.transport.base'
```

**Solution:**
Update to use core transport:
```python
from agenticraft.core.transport import Transport
```

### Issue 2: Missing Methods

**Problem:**
```
AttributeError: 'UnifiedAgent' object has no attribute 'create_mcp_agent'
```

**Solution:**
Use factory functions or builder pattern:
```python
from agenticraft.fabric import create_mcp_agent
# or
from agenticraft.fabric import AgentBuilder
```

### Issue 3: Authentication Changes

**Problem:**
```
TypeError: BearerAuth() takes no arguments
```

**Solution:**
Use AuthConfig:
```python
from agenticraft.core.auth import AuthConfig
auth_config = AuthConfig.bearer("token")
```

## Benefits After Migration

1. **Cleaner Code**: Less duplication, better organization
2. **Better Type Safety**: Improved type hints throughout
3. **Easier Testing**: Mock core abstractions instead of protocols
4. **More Flexible**: Easy to add new protocols
5. **Better Performance**: Reduced overhead from duplicate code

## Getting Help

- Check the [new architecture guide](architecture.md)
- Review [code examples](../examples/refactored/)
- Ask questions in [discussions](https://github.com/yourusername/agenticraft/discussions)

## Timeline

- **Phase 1** (Current): Compatibility layer available
- **Phase 2** (3 months): Deprecation warnings active
- **Phase 3** (6 months): Old imports removed

Start migrating now to take advantage of the cleaner architecture!
