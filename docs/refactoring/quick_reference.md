# AgentiCraft Refactoring Quick Reference

## Import Changes Quick Reference

### Transport
| Old Import | New Import |
|------------|------------|
| `agenticraft.protocols.mcp.transport.HTTPTransport` | `agenticraft.core.transport.HTTPTransport` |
| `agenticraft.protocols.mcp.transport.WebSocketTransport` | `agenticraft.core.transport.WebSocketTransport` |
| `agenticraft.protocols.mcp.transport.base.IMCPTransport` | `agenticraft.core.transport.Transport` |

### Authentication
| Old Import | New Import |
|------------|------------|
| `agenticraft.protocols.mcp.auth.api_key.APIKeyAuth` | `agenticraft.core.auth.APIKeyAuthProvider` |
| `agenticraft.protocols.mcp.auth.bearer.BearerAuth` | `agenticraft.core.auth.BearerAuthProvider` |
| `agenticraft.protocols.mcp.auth.jwt.JWTAuth` | `agenticraft.core.auth.JWTAuthProvider` |

### Registry
| Old Import | New Import |
|------------|------------|
| `agenticraft.protocols.a2a.registry.ProtocolRegistry` | `agenticraft.core.registry.ServiceRegistry` |
| `agenticraft.protocols.mcp.registry.MCPRegistry` | `agenticraft.core.registry.ServiceRegistry` |

### Fabric/Agent
| Old Import | New Import |
|------------|------------|
| `agenticraft.fabric.unified.UnifiedFabric` | `agenticraft.fabric.agent.UnifiedAgent` |
| `agenticraft.fabric.unified_enhanced.EnhancedFabric` | `agenticraft.fabric.agent.UnifiedAgent` |
| `agenticraft.fabric.sdk_fabric.SDKFabric` | `agenticraft.fabric.builder.AgentBuilder` |

## Common Tasks

### Create MCP Agent
```python
# Old way
from agenticraft.fabric.unified import UnifiedFabric
fabric = UnifiedFabric()
agent = fabric.create_mcp_agent(name="agent", url="http://localhost:8080")

# New way
from agenticraft.fabric import create_mcp_agent
agent = create_mcp_agent(name="agent", url="http://localhost:8080")
```

### Create A2A Agent
```python
# Old way
from agenticraft.protocols.a2a import MeshNetwork
agent = MeshNetwork(node_id="node1")

# New way
from agenticraft.fabric import create_a2a_agent
agent = create_a2a_agent(name="node1", pattern="mesh")
```

### Add Authentication
```python
# Old way
auth = BearerAuth()
auth.add_token("my-token")

# New way
from agenticraft.core.auth import AuthConfig
auth_config = AuthConfig.bearer("my-token")
```

### Multi-Protocol Agent
```python
# Old way
fabric = UnifiedFabric()
agent = fabric.create_agent("multi")
agent.add_mcp_support(...)
agent.add_a2a_support(...)

# New way
from agenticraft.fabric import AgentBuilder
agent = (AgentBuilder("multi")
    .with_mcp("http://localhost:8080")
    .with_a2a("mesh")
    .build())
```

## Class/Function Mappings

### MCP Protocol
| Old | New |
|-----|-----|
| `MCPClient` | `MCPProtocol` |
| `MCPServer` | `MCPProtocol` (with server transport) |
| `client.send_request()` | `protocol.request()` |
| `client.send_notification()` | `protocol.notify()` |

### A2A Protocol
| Old | New |
|-----|-----|
| `MeshNetwork` | `A2AProtocol(pattern="mesh")` |
| `TaskRouter` | `A2AProtocol(pattern="centralized")` |
| `ConsensusProtocol` | `A2AProtocol(pattern="decentralized")` |

### Registry Operations
| Old | New |
|-----|-----|
| `registry.register_protocol()` | `registry.register()` |
| `registry.get_protocol()` | `registry.get()` |
| `registry.list_protocols()` | `registry.discover()` |

## Configuration Examples

### Transport Configuration
```python
from agenticraft.core.transport import TransportConfig

config = TransportConfig(
    url="http://localhost:8080",
    timeout=30.0,
    headers={"User-Agent": "AgentiCraft"},
    auth={"type": "bearer", "token": "secret"}
)
```

### Auth Configuration
```python
from agenticraft.core.auth import AuthConfig

# Different auth types
bearer = AuthConfig.bearer("token")
api_key = AuthConfig.api_key("key", header="X-API-Key")
basic = AuthConfig.basic("user", "pass")
jwt = AuthConfig.jwt(token="...", secret="...")
hmac = AuthConfig.hmac(key_id="id", secret_key="secret")
```

### Protocol Configuration
```python
from agenticraft.protocols.base import ProtocolConfig

config = ProtocolConfig(
    name="mcp",
    version="1.0",
    metadata={"server": "my-server"}
)
```

## Error Handling

### Old Way
```python
try:
    response = client.send_request(request)
except MCPError as e:
    print(f"MCP error: {e}")
except A2AError as e:
    print(f"A2A error: {e}")
```

### New Way
```python
from agenticraft.core.exceptions import (
    TransportError, 
    AuthError,
    RegistryError
)

try:
    response = await agent.send(message)
except TransportError as e:
    print(f"Transport error: {e}")
except AuthError as e:
    print(f"Auth error: {e}")
```

## Testing

### Mock Core Components
```python
from unittest.mock import Mock
from agenticraft.core.transport import Transport
from agenticraft.core.auth import AuthManager

# Mock transport
mock_transport = Mock(spec=Transport)
mock_transport.is_connected = True
mock_transport.send.return_value = Mock(payload={"result": "ok"})

# Mock auth
mock_auth = Mock(spec=AuthManager)
mock_auth.get_headers.return_value = {"Authorization": "Bearer test"}

# Use in tests
protocol = MyProtocol(transport=mock_transport, auth=mock_auth)
```

## Async Context Managers

### Old Way
```python
client = MCPClient(...)
await client.connect()
try:
    # use client
finally:
    await client.disconnect()
```

### New Way
```python
async with UnifiedAgent("agent") as agent:
    # agent is automatically started and stopped
    await agent.send(message)
```

## Environment Variables

### Old
```
MCP_SERVER_URL=http://localhost:8080
A2A_NODE_ID=node1
```

### New
```
AGENTICRAFT_DEFAULT_TRANSPORT=http
AGENTICRAFT_DEFAULT_AUTH=bearer
AGENTICRAFT_REGISTRY_TYPE=memory
```

## Debugging

### Enable Debug Logging
```python
import logging

# Debug core components
logging.getLogger("agenticraft.core").setLevel(logging.DEBUG)

# Debug specific protocol
logging.getLogger("agenticraft.protocols.mcp").setLevel(logging.DEBUG)

# Debug fabric layer
logging.getLogger("agenticraft.fabric").setLevel(logging.DEBUG)
```

### Inspect Agent State
```python
# Check agent health
health = await agent.health_check()
print(health)

# List protocols
protocols = agent.list_protocols()
print(f"Protocols: {protocols}")

# Check transport status
transport = agent.get_transport("mcp")
print(f"Connected: {transport.is_connected}")
```

## Performance Tips

1. **Reuse Agents**: Create once, use many times
2. **Connection Pooling**: Transports handle this automatically
3. **Batch Operations**: Use `asyncio.gather()` for parallel operations
4. **Protocol Selection**: Set primary protocol for better performance
5. **Registry Caching**: Use distributed registry for production

## Common Gotchas

1. **Import Errors**: Update all imports to use new paths
2. **Async Required**: All operations are now async
3. **Config Objects**: Use config classes instead of dicts
4. **Protocol Names**: Use lowercase ("mcp", "a2a")
5. **Auth Headers**: Let auth providers generate headers

## Need Help?

- [Full Migration Guide](migration_guide.md)
- [Architecture Overview](architecture.md)
- [API Reference](../api/core/)
- [Examples](../examples/refactored/)
