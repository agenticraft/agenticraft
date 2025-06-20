# 🚀 AgentiCraft Production Features - Quick Reference Guide

## 🔐 Security & Authentication

### Basic Setup
```python
from agenticraft import Agent
from agenticraft.security import security, SecurityContext, SandboxType

# Create secure agent
agent = Agent(
    name="SecureBot",
    sandbox_enabled=True,
    sandbox_type="docker",  # or "process", "restricted"
    memory_limit=256,       # MB
    cpu_limit=50.0         # Percent
)

# Create API key
api_key = await security.create_api_key(
    user_id="user123",
    username="john_doe",
    roles=["developer"],
    permissions=["agent:*", "workflow:*"],
    expires_in_days=30
)

# Authenticate request
request = {"headers": {"X-API-Key": api_key}}
user_context = await security.authenticate(request)

# Execute with security
result = await agent.execute("Hello!", user_context=user_context)
```

### Secure Endpoints
```python
@security.secure_endpoint("agent", "execute")
async def run_agent(request, user_context, task):
    # user_context is automatically injected
    return await agent.execute(task)

@security.require_permissions("agent:execute", "sandbox:execute")
async def run_sandboxed(user_context, code):
    # Requires both permissions
    return await agent.execute_secure(code)
```

## 🔗 Multi-Agent Coordination (A2A)

### Mesh Network (Distributed)
```python
from agenticraft.protocols.a2a.hybrid import MeshNetwork

mesh = MeshNetwork("research-coordinator")
result = await mesh.execute_distributed(
    task="Research quantum computing",
    capability_required="research",
    strategy="round_robin"
)
```

### Task Router (Centralized)
```python
from agenticraft.protocols.a2a.centralized import TaskRouter

router = TaskRouter("dispatcher")
router.register_worker("gpu-1", ["inference", "training"])
result = await router.route_task(
    "Train model",
    capability="training",
    priority=10
)
```

### Consensus (Critical Decisions)
```python
from agenticraft.protocols.a2a.decentralized import ConsensusProtocol

consensus = ConsensusProtocol("validator")
approved = await consensus.propose({
    "action": "deploy_production",
    "risk_level": 0.3
})
```

## 🔌 MCP Tool Integration

### Connect to MCP Servers
```python
from agenticraft.protocols.mcp import create_mcp_agent

# Create agent with MCP tools
agent = await create_mcp_agent(
    "researcher",
    servers=[
        "http://tools.example.com/mcp",
        "ws://realtime.example.com/mcp"
    ]
)

# Tools are auto-discovered
result = await agent.execute("Search for AI papers")
```

### Expose Tools via MCP
```python
from agenticraft.protocols.mcp import MCPServerBuilder

server = MCPServerBuilder("My Tools")
    .with_tool(MyCustomTool())
    .with_workflow(my_workflow)
    .build()

# Start server
await server.start_websocket_server(port=3000)
```

## 🔧 Production Configuration

### Secure Configuration
```python
from agenticraft.production import SecureConfigManager, ConfigEnvironment

config = SecureConfigManager(
    environment=ConfigEnvironment.PRODUCTION,
    auto_reload=True
)

# Regular config
config.set("app.name", "My App")
config.set("app.port", 8080)

# Encrypted secrets
config.set_secret("openai.api_key", "sk-...")
config.set_secret("database.password", "secret")

# Get typed values
port = config.get_typed("app.port", int, default=8080)
api_key = config.get_secret("openai.api_key")
```

## 📊 Monitoring & Metrics

### Health Checks
```python
from agenticraft.production import get_health_monitor

monitor = get_health_monitor()

# Add custom health check
async def database_health():
    # Check database
    return ComponentHealth("database", checks=[
        HealthCheck("connection", HealthStatus.HEALTHY)
    ])

monitor.register_checker("database", database_health)

# Get status
status = monitor.get_status()
if not monitor.is_healthy():
    # Handle unhealthy state
```

### Prometheus Metrics
```python
from agenticraft.production import get_metrics

metrics = get_metrics()

# Track execution
with metrics.track_agent_execution("my_agent"):
    # Agent code
    pass

# Custom metrics
counter = metrics.register_custom_metric(
    "my_requests_total",
    "counter",
    "Total requests",
    labels=["endpoint"]
)
counter.labels(endpoint="/api").inc()

# Export metrics
prometheus_data = metrics.generate_metrics()
```

### Integrated Monitoring
```python
from agenticraft.production import start_monitoring, MonitoringConfig

# Start monitoring
monitoring = await start_monitoring(MonitoringConfig(
    health_check_interval=30.0,
    metrics_collection_interval=10.0
))

# Get dashboard
dashboard = monitoring.get_dashboard()
print(f"Health: {dashboard['health']['status']}")
print(f"Alerts: {dashboard['alerts']['active']}")

# Create endpoints
health_handler = await monitoring.create_health_endpoint()
metrics_handler = await monitoring.create_metrics_endpoint()
```

## ⚡ Performance Optimization

### Caching
```python
from agenticraft.production import cached

@cached(max_size=100, ttl_seconds=300)
async def expensive_operation(query):
    # This result will be cached
    return await process_query(query)

# Check cache stats
print(expensive_operation.cache.stats())
```

### Connection Pooling
```python
from agenticraft.production import register_connection_pool

# Register pool
pool = register_connection_pool(
    "database",
    create_connection,
    max_size=20,
    min_size=5
)

# Use connections
conn = await pool.acquire()
try:
    # Use connection
    pass
finally:
    await pool.release(conn)
```

### Resource Management
```python
from agenticraft.production import get_resource_manager

manager = get_resource_manager()

# Register resource limits
manager.register_resource("agent", {
    "memory_mb": 1024,
    "cpu_percent": 50
})

# Check and allocate
if manager.can_allocate("agent", {"memory_mb": 512}):
    manager.allocate("agent", {"memory_mb": 512})
    # Do work
    manager.release("agent", {"memory_mb": 512})
```

## 🌐 Complete Production Example

```python
import asyncio
from agenticraft import Agent
from agenticraft.workflows import ResearchTeam
from agenticraft.security import security
from agenticraft.production import (
    SecureConfigManager,
    ConfigEnvironment,
    start_monitoring,
    cached
)

async def production_app():
    # 1. Configuration
    config = SecureConfigManager(ConfigEnvironment.PRODUCTION)
    config.set_secret("openai.api_key", "sk-...")
    
    # 2. Monitoring
    monitoring = await start_monitoring()
    
    # 3. Authentication
    api_key = await security.create_api_key(
        user_id="prod_user",
        username="production",
        roles=["user"],
        permissions=["workflow:execute"]
    )
    
    # 4. Create secure workflow
    workflow = ResearchTeam(
        size=3,
        sandbox_type="docker",
        coordination_mode="hybrid"  # Uses A2A
    )
    
    # 5. Execute with caching
    @cached(max_size=100, ttl_seconds=3600)
    async def research(topic, user_context):
        return await workflow.execute(topic, user_context=user_context)
    
    # 6. Run with full security
    request = {"headers": {"X-API-Key": api_key}}
    user_context = await security.authenticate(request)
    
    result = await research(
        "Latest AI developments",
        user_context
    )
    
    # 7. Check health
    health = monitoring.get_dashboard()
    print(f"System health: {health['health']['status']}")
    
    return result

# Run
asyncio.run(production_app())
```

## 📚 Additional Resources

- **Security Guide**: `SECURITY_README.md`
- **A2A Protocols**: `A2A_PROTOCOLS_README.md`
- **MCP Integration**: `MCP_QUICKSTART.md`
- **Production Guide**: `PRODUCTION_IMPLEMENTATION_SUMMARY.md`
- **Examples**: `/examples/` directory

## 🆘 Troubleshooting

### Docker Sandbox Issues
```bash
# Check Docker is running
docker info

# Install Docker support
pip install docker
```

### WebSocket Support
```bash
# For MCP WebSocket transport
pip install websockets
```

### Prometheus Metrics
```bash
# Install Prometheus client
pip install prometheus-client
```

### Performance Issues
- Enable caching for expensive operations
- Use connection pooling for external resources
- Monitor resource usage with metrics
- Check health status regularly

---

**AgentiCraft is now production-ready with enterprise features!** 🚀
