# AgentiCraft Experimental Features

⚠️ **WARNING**: Features listed in this document are experimental and should NOT be used in production environments. They may change significantly or be removed in future versions.

## 🚧 Experimental Features Overview

### 1. Protocol Support

#### Model Context Protocol (MCP)
```python
from agenticraft.protocols.mcp import MCPClient, MCPServer

# Connect to MCP server
client = MCPClient("http://mcp-server.com:3000")
await client.connect()
tools = await client.discover_tools()
```
**Status**: 🚧 Experimental  
**Issues**: API may change, limited testing  
**Use Case**: Tool federation across services

#### Agent-to-Agent Protocol (A2A)
```python
from agenticraft.protocols.a2a import A2ARegistry, A2AClient

# Register agent for discovery
registry = A2ARegistry()
await registry.register_agent(agent, capabilities=["search", "analyze"])
```
**Status**: 🚧 Experimental  
**Issues**: Protocol spec still evolving  
**Use Case**: Multi-agent systems

#### Protocol Fabric
```python
from agenticraft.fabric import UnifiedProtocolFabric

fabric = UnifiedProtocolFabric()
await fabric.add_protocol("mcp", mcp_config)
await fabric.add_protocol("a2a", a2a_config)
```
**Status**: 🚧 Highly Experimental  
**Issues**: Complex, untested in production  
**Use Case**: Unified protocol management

### 2. Security Features

#### Sandboxed Execution
```python
from agenticraft.security import SandboxManager, SandboxType

sandbox = SandboxManager()
result = await sandbox.execute_secure(
    untrusted_code,
    sandbox_type=SandboxType.RESTRICTED_PYTHON,
    timeout=30
)
```
**Status**: 🚧 Experimental  
**Issues**: Performance overhead, limited language support  
**Use Case**: Executing untrusted code

#### Role-Based Access Control
```python
from agenticraft.security.auth import RBACMiddleware

rbac = RBACMiddleware()
rbac.add_role("admin", permissions=["*"])
rbac.add_role("user", permissions=["read", "execute"])
```
**Status**: 🚧 Experimental  
**Issues**: Incomplete permission model  
**Use Case**: Multi-tenant applications

### 3. Advanced Agent Features

#### Mesh Networking
```python
from agenticraft.experimental.mesh import AgentMesh

mesh = AgentMesh()
await mesh.add_agent(agent1)
await mesh.add_agent(agent2)
await mesh.enable_consensus()
```
**Status**: 🚧 Highly Experimental  
**Issues**: Not tested at scale  
**Use Case**: Distributed agent systems

#### Plugin Marketplace
```python
from agenticraft.marketplace import PluginRegistry

registry = PluginRegistry()
plugin = await registry.install("enhanced-reasoning")
agent.enable_plugin(plugin)
```
**Status**: 🚧 Experimental  
**Issues**: No actual marketplace yet  
**Use Case**: Extending agent capabilities

### 4. Advanced Memory Systems

#### Graph Memory
```python
from agenticraft.memory.graph import GraphMemory

memory = GraphMemory()
await memory.add_entity("Paris", type="city")
await memory.add_relation("Paris", "capital_of", "France")
```
**Status**: 🚧 Experimental  
**Issues**: Performance not optimized  
**Use Case**: Complex knowledge representation

## ⚠️ Known Issues

### General Issues
1. **API Instability**: All experimental APIs may change without notice
2. **Limited Testing**: Minimal test coverage for experimental features
3. **Performance**: Not optimized for production workloads
4. **Documentation**: Limited or outdated documentation

### Specific Feature Issues

#### Protocols
- Incomplete error handling
- No standardized authentication
- Limited protocol bridging

#### Security
- RestrictedPython limitations
- Docker sandbox requires privileged access
- Audit logging performance impact

#### Advanced Features
- Mesh networking untested beyond 3 agents
- Plugin system has no versioning
- Memory systems lack garbage collection

## 🔬 Enabling Experimental Features

### Method 1: Import from experimental
```python
from agenticraft.experimental import (
    enable_features,
    MCPClient,
    A2ARegistry,
    SandboxManager
)

# Enable specific features
enable_features(["mcp", "security"])
```

### Method 2: Feature flags
```python
import agenticraft

agenticraft.config.enable_experimental = True
agenticraft.config.experimental_features = ["all"]
```

### Method 3: Environment variables
```bash
export AGENTICRAFT_EXPERIMENTAL=true
export AGENTICRAFT_EXPERIMENTAL_FEATURES=mcp,a2a,security
```

## 📊 Experimental Feature Status

| Feature | Added | Stability | Target Stable | Notes |
|---------|-------|-----------|---------------|-------|
| MCP Protocol | v0.2.0 | 30% | v0.4.0 | Needs protocol v2 |
| A2A Protocol | v0.2.0 | 20% | v0.5.0 | Spec not final |
| Sandboxing | v0.2.0 | 40% | v0.4.0 | Docker only |
| RBAC | v0.2.0 | 25% | v0.5.0 | Basic impl |
| Mesh Network | v0.2.0 | 10% | v1.0.0 | Research phase |
| Plugins | v0.2.0 | 15% | v0.6.0 | No marketplace |
| Graph Memory | v0.2.0 | 35% | v0.4.0 | Needs optimization |

## 🧪 Testing Experimental Features

### Safe Testing Environment
```python
# Create isolated test environment
import agenticraft.experimental as exp

# Use context manager for safety
with exp.experimental_context():
    # Experimental code here
    client = exp.MCPClient("test-server")
    # Changes are isolated
```

### Feature-Specific Tests
```bash
# Run experimental feature tests
pytest tests/experimental/ -v

# Run specific feature tests
pytest tests/experimental/protocols/test_mcp.py -v
```

## 🚫 Do NOT Use For

- Production applications
- Customer-facing features
- Mission-critical systems
- Applications requiring stability
- Systems needing support

## 📢 Feedback

We welcome feedback on experimental features:

1. **Bug Reports**: Use GitHub issues with `experimental` label
2. **Feature Requests**: Discuss in GitHub Discussions
3. **API Feedback**: Comment on feature PRs
4. **Use Cases**: Share what you're building

## 🔮 Future of Experimental Features

### Graduation Path
1. **Experimental** (current) → Gather feedback
2. **Beta** → API stabilization
3. **Release Candidate** → Production testing
4. **Stable** → Full support

### Deprecation Risk
Features may be removed if:
- Low adoption after 6 months
- Better alternatives emerge
- Maintenance burden too high
- Security issues discovered

---

*Last Updated: November 2024*  
*Use at your own risk - no support provided for experimental features*
