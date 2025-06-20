# AgentiCraft Refactored Architecture

## Overview

The refactored AgentiCraft architecture introduces a cleaner, more maintainable structure with clear separation of concerns. This document explains the new architecture and design decisions.

## Architecture Principles

1. **DRY (Don't Repeat Yourself)**: Eliminate code duplication between protocols
2. **Single Responsibility**: Each module has one clear purpose
3. **Dependency Inversion**: Protocols depend on abstractions, not concrete implementations
4. **Open/Closed**: Easy to extend with new protocols without modifying existing code
5. **Interface Segregation**: Clean, focused interfaces for each abstraction

## Layer Architecture

```
┌─────────────────────────────────────────────┐
│           Application Layer                  │
│         (Your Agent Code)                   │
├─────────────────────────────────────────────┤
│           Fabric Layer                       │
│   (UnifiedAgent, Adapters, Builder)         │
├─────────────────────────────────────────────┤
│         Protocol Layer                       │
│      (MCP, A2A, External)                   │
├─────────────────────────────────────────────┤
│          Core Layer                          │
│ (Transport, Auth, Registry, Patterns)       │
└─────────────────────────────────────────────┘
```

## Core Layer

The core layer provides fundamental abstractions used by all protocols.

### Transport (`core.transport`)

Protocol-agnostic communication layer.

```python
# Base transport interface
class Transport(ABC):
    async def connect(self) -> None
    async def disconnect(self) -> None
    async def send(self, message: Message) -> Optional[Message]
    async def receive(self) -> Message
```

**Implementations:**
- `HTTPTransport` - REST/HTTP communication
- `WebSocketTransport` - Real-time bidirectional communication

### Authentication (`core.auth`)

Unified authentication system supporting multiple strategies.

```python
# Auth configuration
class AuthConfig:
    @classmethod
    def bearer(cls, token: str) -> "AuthConfig"
    @classmethod
    def api_key(cls, key: str, header: str) -> "AuthConfig"
    @classmethod
    def jwt(cls, token: str, secret: str) -> "AuthConfig"
```

**Providers:**
- `NoAuthProvider` - No authentication
- `BearerAuthProvider` - Bearer token authentication
- `APIKeyAuthProvider` - API key authentication
- `JWTAuthProvider` - JWT authentication
- `HMACAuthProvider` - HMAC signature authentication
- `BasicAuthProvider` - Basic HTTP authentication

### Registry (`core.registry`)

Service discovery and registration.

```python
# Service registry interface
class ServiceRegistry(ABC):
    async def register(self, name: str, service_type: str, ...) -> ServiceInfo
    async def discover(self, service_type: str = None, ...) -> List[ServiceInfo]
    async def health_check(self, name: str) -> bool
```

**Implementations:**
- `InMemoryRegistry` - Local in-memory storage
- `DistributedRegistry` - Distributed consensus-based registry

### Patterns (`core.patterns`)

Reusable communication patterns.

- **Client-Server**: Request-response pattern
- **Pub-Sub**: Publish-subscribe messaging
- **Mesh**: Peer-to-peer mesh network
- **Consensus**: Distributed consensus protocols

### Serialization (`core.serialization`)

Data serialization utilities.

- `JSONSerializer` - JSON serialization with enhanced type support
- `MsgPackSerializer` - Efficient binary serialization

## Protocol Layer

Protocol implementations using core abstractions.

### Base Protocol (`protocols.base`)

```python
class Protocol(ABC):
    def __init__(self, config: ProtocolConfig, 
                 transport: Transport = None,
                 auth: AuthManager = None,
                 registry: ServiceRegistry = None)
    
    async def start(self) -> None
    async def stop(self) -> None
    async def send(self, message: Any, target: str = None) -> Any
    async def receive(self) -> Any
```

### MCP Protocol (`protocols.mcp`)

Model Context Protocol implementation.

**Features:**
- Tools management
- Resource handling
- Prompt templates
- JSON-RPC communication

**Usage:**
```python
from agenticraft.protocols.mcp import MCPProtocol
from agenticraft.core.transport import HTTPTransport

transport = HTTPTransport(TransportConfig(url="http://localhost:8080"))
protocol = MCPProtocol(transport=transport)

await protocol.start()
tools = await protocol.request("tools/list")
```

### A2A Protocol (`protocols.a2a`)

Agent-to-Agent protocol implementation.

**Patterns:**
- Mesh networking
- Centralized coordination
- Decentralized consensus
- Hybrid approaches

**Usage:**
```python
from agenticraft.protocols.a2a import A2AProtocol

protocol = A2AProtocol(
    pattern="mesh",
    node_id="agent-1",
    peers=["agent-2", "agent-3"]
)

await protocol.start()
await protocol.broadcast({"message": "Hello network!"})
```

### Protocol Bridges (`protocols.bridges`)

Enable cross-protocol communication.

```python
from agenticraft.protocols.bridges import A2AMCPBridge

bridge = A2AMCPBridge(a2a_protocol, mcp_protocol)
await bridge.start()

# Now A2A agents can call MCP tools
result = await bridge.handle_tool_call(
    "calculator",
    {"operation": "add", "a": 1, "b": 2},
    source_protocol="a2a"
)
```

## Fabric Layer

The fabric layer provides a unified interface for working with multiple protocols.

### UnifiedAgent (`fabric.agent`)

Single agent interface supporting multiple protocols.

```python
class UnifiedAgent:
    def add_protocol(self, protocol_id: str, protocol: Protocol, 
                     transport: Transport, auth: AuthManager = None)
    async def send(self, message: Any, target: str = None, 
                   protocol: str = None) -> Any
    async def start(self) -> None
    async def stop(self) -> None
```

### Agent Builder (`fabric.builder`)

Fluent interface for building complex agents.

```python
agent = (AgentBuilder("my-agent")
    .with_mcp("http://localhost:8080")
    .with_a2a("mesh", peers=["peer1", "peer2"])
    .with_auth(AuthConfig.bearer("token"))
    .with_registry()
    .build())
```

### Protocol Adapters (`fabric.adapters`)

Adapt protocols to work seamlessly in the fabric layer.

- `MCPAdapter` - MCP protocol adapter
- `A2AAdapter` - A2A protocol adapter
- `AdapterRegistry` - Dynamic adapter registration

## Design Patterns Used

### 1. Abstract Factory

Used in transport and auth provider creation.

```python
# Transport factory
transport = TransportRegistry.create(config)

# Auth provider factory
provider = auth_manager.create_provider(config)
```

### 2. Strategy Pattern

Authentication strategies can be swapped at runtime.

```python
auth_manager.set_auth(AuthConfig.bearer("token"))
# Later...
auth_manager.set_auth(AuthConfig.jwt("token", "secret"))
```

### 3. Adapter Pattern

Protocol adapters provide uniform interface.

```python
# All adapters implement same interface
adapter = AdapterRegistry.create_adapter(protocol_name, ...)
await adapter.send_message(message)
```

### 4. Builder Pattern

Agent builder for complex configurations.

```python
agent = AgentBuilder("agent").with_mcp(...).with_a2a(...).build()
```

### 5. Registry Pattern

Service discovery and dependency injection.

```python
registry.register("my-service", service)
service = registry.discover("my-service")
```

## Benefits of New Architecture

### 1. Reduced Code Duplication

- **Before**: ~15,000 lines with 40% duplication
- **After**: ~9,000 lines with <5% duplication

### 2. Better Testability

```python
# Easy to mock core abstractions
mock_transport = Mock(spec=Transport)
mock_auth = Mock(spec=AuthManager)

protocol = MyProtocol(transport=mock_transport, auth=mock_auth)
```

### 3. Easier Protocol Addition

Adding a new protocol requires:
1. Implement `Protocol` base class
2. Create protocol-specific features
3. Optional: Create fabric adapter

### 4. Protocol Interoperability

Bridges enable seamless cross-protocol communication:
- A2A agents can use MCP tools
- MCP servers can broadcast to A2A networks
- External systems integrate through gateway

### 5. Cleaner Dependencies

```
# Old: Circular dependencies
protocols.mcp -> protocols.a2a -> protocols.mcp

# New: Clean dependency flow
protocols.mcp -> core
protocols.a2a -> core
```

## Extension Points

### Adding a New Transport

```python
from agenticraft.core.transport import Transport

class GRPCTransport(Transport):
    async def connect(self) -> None:
        # GRPC connection logic
        
    async def send(self, message: Message) -> Optional[Message]:
        # GRPC send logic

# Register globally
TransportRegistry.register("grpc", GRPCTransport)
```

### Adding a New Protocol

```python
from agenticraft.protocols.base import Protocol

class MyProtocol(Protocol):
    async def start(self) -> None:
        # Protocol initialization
        
    async def send(self, message: Any, target: str = None) -> Any:
        # Protocol-specific sending
```

### Adding a New Auth Strategy

```python
from agenticraft.core.auth import AuthProvider

class OAuth2Provider(AuthProvider):
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # OAuth2 flow
        
    def get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}
```

## Performance Considerations

### 1. Connection Pooling

Transports maintain connection pools for efficiency:
```python
# HTTP transport reuses connections
transport = HTTPTransport(config)
# Multiple requests use same connection
```

### 2. Message Caching

Protocol bridges cache translated messages:
```python
# Bridge caches message translations
bridge._translation_cache[message_id] = translated
```

### 3. Async Throughout

All I/O operations are async:
```python
# Non-blocking operations
await asyncio.gather(
    agent1.send(msg1),
    agent2.send(msg2),
    agent3.send(msg3)
)
```

## Security Considerations

### 1. Auth Abstraction

Authentication is protocol-agnostic:
- Credentials never stored in protocols
- Auth providers handle secure storage
- Easy to audit auth usage

### 2. Transport Security

- HTTPS/WSS by default
- Certificate validation
- Configurable TLS options

### 3. Registry Security

- Service authentication
- Health check validation
- Access control for registry operations

## Future Enhancements

### 1. Protocol Negotiation

Automatic protocol selection based on capabilities:
```python
# Future: Auto-select best protocol
agent.send(message)  # Automatically uses optimal protocol
```

### 2. Metrics and Monitoring

Built-in observability:
```python
# Future: Protocol metrics
metrics = agent.get_metrics()
print(f"Messages sent: {metrics.messages_sent}")
```

### 3. Plugin System

Dynamic protocol loading:
```python
# Future: Load protocols as plugins
agent.load_protocol_plugin("custom-protocol")
```

## Conclusion

The refactored architecture provides a solid foundation for building sophisticated agent systems. The clean separation of concerns, reduced duplication, and extensible design make it easier to maintain and enhance AgentiCraft going forward.
