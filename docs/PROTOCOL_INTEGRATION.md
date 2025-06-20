# 🌐 AgentiCraft External Protocol Integration

## Overview

AgentiCraft now supports seamless integration with external AI protocols, enabling your agents to participate in the broader AI ecosystem. This includes support for Google's Agent-to-Agent (A2A) Protocol and Anthropic's Model Context Protocol (MCP).

## 🚀 Key Features

### 1. **Protocol Gateway**
A unified management system for all protocol connections:
- Single point of control for internal and external protocols
- Automatic service discovery and registration
- Protocol translation and routing
- Load balancing and failover
- Comprehensive metrics and monitoring

### 2. **A2A Bridge**
Connect AgentiCraft to Google's A2A ecosystem:
- Expose agents as A2A-compliant servers
- Connect to external A2A agents
- Agent Card generation for discovery
- HTTP/REST endpoints with JSON-RPC support
- SSE streaming for real-time updates

### 3. **MCP Integration**
Full support for Model Context Protocol:
- Build MCP servers from AgentiCraft agents
- Connect to external MCP servers
- Support for tools, resources, and prompts
- Multiple transport options (stdio, SSE, HTTP)
- Claude Desktop integration

## 📦 Installation

```bash
# Install required dependencies
pip install "mcp[cli]"  # For MCP support
pip install aiohttp     # For HTTP communication
pip install fastapi     # For REST endpoints
pip install uvicorn     # For server hosting
```

## 🔧 Quick Start

### Expose an Agent through Multiple Protocols

```python
from agenticraft.core.agent import Agent
from agenticraft.protocols.external import (
    ProtocolGateway,
    ExternalProtocol
)

# Create your agent
agent = Agent(
    name="MyAgent",
    model="gpt-4",
    tools=[...],
    system_prompt="You are a helpful assistant."
)

# Create protocol gateway
gateway = ProtocolGateway()
await gateway.start()

# Expose through both A2A and MCP
registrations = await gateway.expose_agent(
    agent,
    protocols=[ExternalProtocol.GOOGLE_A2A, ExternalProtocol.MCP],
    base_port=8080
)

# Your agent is now accessible via:
# - A2A: http://localhost:8080
# - MCP: http://localhost:8081
```

### Create an MCP Server for Claude Desktop

```python
from agenticraft.protocols.external import MCPServerBuilder

# Create MCP server
builder = MCPServerBuilder(
    "My AgentiCraft Tools",
    "Custom tools for Claude Desktop"
)

# Add tools
@builder.add_tool(description="Calculate expressions")
def calculate(expression: str) -> float:
    """Safely evaluate mathematical expressions."""
    return eval(expression)  # Use safe eval in production

# Add resources
@builder.add_resource("data://info")
def get_info() -> str:
    """Get system information."""
    return "AgentiCraft MCP Server v1.0"

# Run the server
builder.run_stdio()  # For Claude Desktop
# or
builder.run_sse(port=8080)  # For web access
```

### Connect to External Services

```python
# Connect to external A2A agent
agent_card = await gateway.connect_external_a2a(
    "https://example.com/a2a-agent"
)

# Connect to external MCP server
tools = await gateway.connect_mcp_server(
    "filesystem-server",
    {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
)

# Execute tasks across protocols
result = await gateway.execute(
    task="Search for information about AI",
    capability="tool:search_web",
    prefer_external=False
)
```

## 🏗️ Architecture

### Protocol Gateway Architecture

```
┌─────────────────────────────────────────┐
│           Protocol Gateway              │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌────────────────┐ │
│  │  Internal   │    │   External     │ │
│  │    Mesh     │←──→│   A2A Bridge   │ │
│  └─────────────┘    └────────────────┘ │
│                                         │
│  ┌─────────────┐    ┌────────────────┐ │
│  │   Agent     │    │  MCP Server    │ │
│  │  Registry   │    │   Builder      │ │
│  └─────────────┘    └────────────────┘ │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      Unified Task Executor       │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### A2A Integration Flow

```
AgentiCraft Agent → A2A Server → Agent Card
                                      ↓
                              External Discovery
                                      ↓
                              Task Submission
                                      ↓
                              JSON-RPC/REST/SSE
```

### MCP Integration Flow

```
AgentiCraft Agent → MCP Server Builder → FastMCP Server
                                              ↓
                                    Tools + Resources + Prompts
                                              ↓
                                    Claude Desktop / Other Clients
```

## 📋 Protocol Feature Comparison

| Feature | AgentiCraft Internal | Google A2A | MCP |
|---------|---------------------|------------|-----|
| Discovery | Mesh Network | Agent Cards | Tool Lists |
| Communication | Async Messages | HTTP/JSON-RPC | stdio/SSE |
| Coordination | Consensus/Router | Task Delegation | Tool Calls |
| State Management | Distributed | Stateless | Session-based |
| Security | Internal Trust | OAuth/JWT | Transport Security |

## 🎯 Use Cases

### 1. **Multi-Cloud Agent Deployment**
Deploy AgentiCraft agents that can be accessed by various AI platforms:
```python
# Expose to multiple clouds
await gateway.expose_agent(
    agent,
    protocols=[ExternalProtocol.GOOGLE_A2A, ExternalProtocol.MCP],
    base_port=8080
)
```

### 2. **Claude Desktop Integration**
Make your agents available in Claude Desktop:
```python
# Create MCP server
builder = create_agent_mcp_server(agent)

# Get Claude Desktop config
config = builder.get_config_for_claude()

# Add to ~/Library/Application Support/Claude/claude_desktop_config.json
```

### 3. **Hybrid Workflows**
Combine internal and external agents:
```python
# Create hybrid workflow
workflow = await gateway.create_hybrid_workflow("research-workflow")

# Execute using both internal and external agents
result = await workflow.execute_with_external(
    "Research quantum computing",
    prefer_external=True
)
```

### 4. **Tool Federation**
Share tools across different AI systems:
```python
# Register tool once
@builder.add_tool()
def my_tool(param: str) -> str:
    return f"Processed: {param}"

# Available through both A2A and MCP
```

## 🔒 Security Considerations

1. **Authentication**: Both A2A and MCP support authentication
   - A2A: OAuth, API keys, JWT
   - MCP: Transport-level security

2. **Authorization**: Control access to specific tools/agents
3. **Sandboxing**: Execute external code safely
4. **Rate Limiting**: Protect against abuse

## 📊 Monitoring and Metrics

```python
# Get gateway metrics
metrics = gateway.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Active connections: {metrics['active_connections']}")

# Health check
health = await gateway.health_check()
print(f"Status: {health['status']}")
print(f"Issues: {health['issues']}")

# List all services
services = gateway.list_services()
for service in services:
    print(f"{service['name']} ({service['protocol']}): {service['type']}")
```

## 🧪 Testing

### Test MCP Server with Inspector
```bash
# Install MCP CLI tools
pip install "mcp[cli]"

# Test your server
mcp dev my_server.py

# Inspector opens at http://localhost:5173
```

### Test A2A Integration
```python
# Create test client
import httpx

async with httpx.AsyncClient() as client:
    # Get agent card
    response = await client.get("http://localhost:8080/agent-card")
    agent_card = response.json()
    
    # Submit task
    task_response = await client.post(
        "http://localhost:8080/tasks",
        json={"task": {"description": "Test task"}}
    )
```

## 🚀 Advanced Features

### 1. **Protocol Translation**
Automatically translate between protocol formats:
```python
# A2A task → MCP tool call
# MCP resource → A2A discovery
# Internal message → External format
```

### 2. **Load Balancing**
Distribute tasks across multiple instances:
```python
# Gateway automatically balances load
result = await gateway.execute(
    task="Heavy computation",
    capability="compute",
    strategy="least_loaded"
)
```

### 3. **Failover and Resilience**
Automatic failover between protocols:
```python
# If A2A fails, try MCP
# If external fails, use internal
```

## 📚 Examples

See the `examples/protocol_integration/` directory for:
- `unified_demo.py` - Complete integration demonstration
- `mcp_claude_desktop.py` - Claude Desktop integration
- `a2a_external_agent.py` - External A2A agent connection

## 🔜 Roadmap

1. **Additional Protocol Support**
   - OpenAI Agent Protocol
   - LangChain Hub integration
   - Custom protocol adapters

2. **Enhanced Security**
   - End-to-end encryption
   - Advanced authentication
   - Audit logging

3. **Performance Optimizations**
   - Connection pooling
   - Response caching
   - Parallel execution

4. **Developer Tools**
   - Protocol debugger
   - Performance profiler
   - Integration testing framework

## 🤝 Contributing

We welcome contributions to improve protocol integration:
1. Add new protocol adapters
2. Enhance existing integrations
3. Improve documentation
4. Share example implementations

## 📝 License

The protocol integration features are part of AgentiCraft and follow the same license terms.

---

**Ready to connect your agents to the world?** 🌍

Start with the examples and build your own protocol-enabled agents today!
