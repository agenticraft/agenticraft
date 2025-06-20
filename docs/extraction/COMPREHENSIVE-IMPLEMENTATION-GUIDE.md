# 🔐 AgentiCraft Security & Infrastructure Implementation Guide

## Overview

This comprehensive guide provides step-by-step instructions to extract and integrate critical security and infrastructure components from `agentic-framework` into `AgentiCraft`. The implementation follows best practices, includes validation, and ensures production-grade security.

## Pre-Implementation Checklist

- [ ] Full backup of current AgentiCraft codebase
- [ ] Development environment separate from production
- [ ] All tests passing in current state
- [ ] Document current API endpoints and behaviors

## Phase 1: Security Sandbox System (Days 1-2)

### 1.1 Extract Core Sandbox Components

#### Source Files to Extract:
```
FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/sandbox/
- base_sandbox.py (154 lines)
- process_sandbox.py (~200 lines) 
- docker_sandbox.py (~300 lines)
- sandbox_manager.py (~250 lines)

FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/abstractions/
- interfaces.py (for ISandbox interface)
- types.py (for SecurityContext, SecureResult types)
```

#### Target Structure:
```
TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/
├── __init__.py
├── sandbox/
│   ├── __init__.py
│   ├── base.py (from base_sandbox.py)
│   ├── process.py (from process_sandbox.py)
│   ├── docker.py (from docker_sandbox.py)
│   └── manager.py (from sandbox_manager.py)
├── abstractions/
│   ├── __init__.py
│   ├── interfaces.py
│   └── types.py
└── exceptions.py
```

### 1.2 Integration Points

#### Modify Core Agent Class:
```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/agents/base.py

from agenticraft.security.sandbox.manager import SandboxManager
from agenticraft.security.abstractions.types import SecurityContext, SandboxType

class Agent:
    def __init__(self, name: str, sandbox_type: SandboxType = SandboxType.PROCESS, **kwargs):
        self.name = name
        self.sandbox_manager = SandboxManager()
        self.sandbox_type = sandbox_type
        self.security_context = SecurityContext(
            user_id="system",
            permissions=["execute"],
            resource_limits={
                "memory_mb": kwargs.get("memory_limit", 512),
                "cpu_percent": kwargs.get("cpu_limit", 50),
                "timeout_seconds": kwargs.get("timeout", 30)
            }
        )
        # ... existing init code
        
    async def execute_secure(self, operation: Callable, *args, **kwargs) -> SecureResult:
        """Execute operation in sandbox."""
        sandbox = await self.sandbox_manager.get_sandbox(self.sandbox_type)
        return await sandbox.execute(operation, self.security_context, *args, **kwargs)
```

#### Update Workflow Execution:
```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/workflows/base.py

async def execute(self, task: str, user_context: Optional[Dict] = None) -> Any:
    """Execute workflow with security context."""
    # Create security context from user context
    security_context = self._create_security_context(user_context)
    
    # Validate permissions
    if not await self._validate_permissions(security_context, "execute_workflow"):
        raise PermissionError(f"User lacks permission to execute {self.name}")
    
    # Execute with audit logging
    async with self.audit_logger.audit_context(
        user_id=security_context.user_id,
        action="workflow_execution",
        resource=self.name
    ) as audit_details:
        try:
            # Original execution logic, but wrapped in sandbox
            result = await self._execute_with_sandbox(task, security_context)
            audit_details["status"] = "success"
            return result
        except Exception as e:
            audit_details["status"] = "failure"
            audit_details["error"] = str(e)
            raise
```

### 1.3 Validation Tests

Create comprehensive tests:
```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/tests/security/test_sandbox.py

import pytest
import asyncio
from agenticraft.security.sandbox.manager import SandboxManager
from agenticraft.security.abstractions.types import SandboxType, SecurityContext

class TestSandboxSecurity:
    @pytest.mark.asyncio
    async def test_code_isolation(self):
        """Test that malicious code cannot escape sandbox."""
        manager = SandboxManager()
        sandbox = await manager.get_sandbox(SandboxType.PROCESS)
        
        malicious_code = """
import os
import shutil
# Try to delete files (should fail)
shutil.rmtree("/tmp/test")
        """
        
        result = await sandbox.execute_code(malicious_code, SecurityContext())
        assert not result.success
        assert "Permission denied" in result.error or "not permitted" in result.error
        
    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test resource limit enforcement."""
        manager = SandboxManager()
        context = SecurityContext(
            resource_limits={"memory_mb": 10, "timeout_seconds": 1}
        )
        
        # Memory bomb (should fail)
        memory_bomb = "x = 'a' * (100 * 1024 * 1024)"  # 100MB
        result = await sandbox.execute_code(memory_bomb, context)
        assert not result.success
        
    @pytest.mark.asyncio
    async def test_network_isolation(self):
        """Test network access is blocked."""
        network_code = """
import urllib.request
response = urllib.request.urlopen('http://example.com')
        """
        result = await sandbox.execute_code(network_code, SecurityContext())
        assert not result.success
```

## Phase 2: A2A Protocol System (Days 2-3)

### 2.1 Extract A2A Components

#### Source Files:
```
FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/protocols/a2a/
├── __init__.py
├── centralized/
│   ├── supervisor_agent.py (~300 lines)
│   ├── hierarchical.py (~250 lines)
│   └── task_router.py (~200 lines)
├── decentralized/
│   ├── peer_discovery.py (~200 lines)
│   ├── consensus.py (~400 lines)
│   └── federation.py (~300 lines)
└── hybrid/
    ├── adaptive_mode.py (~250 lines)
    ├── mesh_network.py (~350 lines)
    └── protocol_bridge.py (~200 lines)
```

#### Target Structure:
```
TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/protocols/
├── __init__.py
├── a2a/
│   ├── __init__.py
│   ├── centralized/
│   ├── decentralized/
│   └── hybrid/
├── base.py
└── registry.py
```

### 2.2 Integration with Existing Workflows

#### Update Research Team to use A2A:
```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/workflows/research_team.py

from agenticraft.protocols.a2a.hybrid import MeshNetwork, AdaptiveModeSelector
from agenticraft.protocols.a2a.centralized import TaskRouter

class ResearchTeam(Workflow):
    def __init__(self, size: int = 5, coordination_mode: str = "hybrid", **kwargs):
        super().__init__("research-team", **kwargs)
        
        # Initialize A2A coordination
        if coordination_mode == "hybrid":
            self.coordinator = MeshNetwork(
                node_id=f"research-team-{self.id}",
                discovery_timeout=5.0
            )
            self.mode_selector = AdaptiveModeSelector()
        elif coordination_mode == "centralized":
            self.coordinator = TaskRouter()
        
        # Register agents with coordinator
        for agent in self.agents.values():
            self.coordinator.register_agent(agent)
            
    async def execute(self, query: str, **kwargs) -> ResearchReport:
        """Execute research with A2A coordination."""
        # Determine best coordination mode
        mode = await self.mode_selector.select_mode(
            task_complexity=self._estimate_complexity(query),
            agent_count=len(self.agents),
            latency_requirement=kwargs.get("max_latency_ms", 1000)
        )
        
        # Set coordination mode
        await self.coordinator.set_mode(mode)
        
        # Distribute tasks using A2A protocol
        task_distribution = await self.coordinator.distribute_tasks(
            main_task=query,
            agents=list(self.agents.values()),
            strategy="consensus" if mode == "decentralized" else "hierarchical"
        )
        
        # Execute with proper coordination
        results = await self.coordinator.execute_coordinated(task_distribution)
        
        # Aggregate results
        return self._create_research_report(results)
```

### 2.3 Protocol Registry

Create a central registry for protocol management:
```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/protocols/registry.py

from typing import Dict, Type, Optional
from agenticraft.protocols.base import Protocol

class ProtocolRegistry:
    """Central registry for all protocols."""
    
    _instance = None
    _protocols: Dict[str, Type[Protocol]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, name: str, protocol_class: Type[Protocol]):
        """Register a protocol."""
        if name in self._protocols:
            raise ValueError(f"Protocol '{name}' already registered")
        self._protocols[name] = protocol_class
        
    def get(self, name: str) -> Optional[Type[Protocol]]:
        """Get a protocol by name."""
        return self._protocols.get(name)
        
    def list_protocols(self) -> List[str]:
        """List all registered protocols."""
        return list(self._protocols.keys())

# Auto-register A2A protocols
registry = ProtocolRegistry()
registry.register("a2a.mesh", MeshNetwork)
registry.register("a2a.centralized", TaskRouter)
registry.register("a2a.consensus", ConsensusProtocol)
```

## Phase 3: Authentication & Authorization (Days 3-4)

### 3.1 Extract Auth Components

#### Source Files:
```
FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/
├── auth.py (~200 lines)
├── authentication/
│   ├── api_key.py (~150 lines)
│   ├── jwt.py (~200 lines)
│   └── oauth.py (~300 lines)
├── authorization/
│   ├── rbac.py (~250 lines)
│   ├── abac.py (~300 lines)
│   └── permissions.py (~150 lines)
└── audit/
    ├── audit_logger.py (~200 lines)
    └── compliance.py (~300 lines)
```

### 3.2 Integrate Authentication

#### Create Auth Middleware:
```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/middleware.py

from typing import Optional, Dict, Any
from functools import wraps
from agenticraft.security.authentication import APIKeyAuth, JWTAuth
from agenticraft.security.authorization import RBACAuthorizer
from agenticraft.security.audit import AuditLogger

class SecurityMiddleware:
    """Comprehensive security middleware."""
    
    def __init__(self):
        self.api_key_auth = APIKeyAuth()
        self.jwt_auth = JWTAuth()
        self.authorizer = RBACAuthorizer()
        self.audit_logger = AuditLogger()
        
    async def authenticate(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate request and return user context."""
        # Try API key first
        if api_key := request.get("headers", {}).get("X-API-Key"):
            return await self.api_key_auth.authenticate(api_key)
            
        # Try JWT token
        if auth_header := request.get("headers", {}).get("Authorization"):
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                return await self.jwt_auth.authenticate(token)
                
        return None
        
    async def authorize(self, user_context: Dict, resource: str, action: str) -> bool:
        """Check if user is authorized for action."""
        return await self.authorizer.check_permission(
            user_id=user_context["user_id"],
            resource=resource,
            action=action,
            context=user_context
        )
        
    def secure_endpoint(self, resource: str, action: str):
        """Decorator for securing endpoints."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request context
                request = kwargs.get("request", {})
                
                # Authenticate
                user_context = await self.authenticate(request)
                if not user_context:
                    raise AuthenticationError("Authentication required")
                    
                # Authorize
                if not await self.authorize(user_context, resource, action):
                    raise AuthorizationError(f"Not authorized for {action} on {resource}")
                    
                # Audit log
                audit_id = await self.audit_logger.log_access(
                    user_id=user_context["user_id"],
                    resource=resource,
                    action=action,
                    timestamp=datetime.now()
                )
                
                # Add context to kwargs
                kwargs["user_context"] = user_context
                kwargs["audit_id"] = audit_id
                
                try:
                    result = await func(*args, **kwargs)
                    await self.audit_logger.log_success(audit_id, result_summary=str(result)[:100])
                    return result
                except Exception as e:
                    await self.audit_logger.log_failure(audit_id, error=str(e))
                    raise
                    
            return wrapper
        return decorator

# Global security instance
security = SecurityMiddleware()
```

#### Update CLI with Auth:
```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/cli/main.py

from agenticraft.security.middleware import security

@click.group(invoke_without_command=True)
@click.option('--api-key', envvar='AGENTICRAFT_API_KEY')
@click.option('--token', envvar='AGENTICRAFT_TOKEN')
@click.pass_context
async def cli(ctx, api_key: Optional[str], token: Optional[str]):
    """AgentiCraft CLI with authentication."""
    # Create request context
    request = {
        "headers": {}
    }
    
    if api_key:
        request["headers"]["X-API-Key"] = api_key
    elif token:
        request["headers"]["Authorization"] = f"Bearer {token}"
    else:
        click.echo("Warning: No authentication provided. Some commands may fail.", err=True)
        
    # Authenticate
    try:
        user_context = await security.authenticate(request)
        ctx.obj = {"user_context": user_context}
    except Exception as e:
        click.echo(f"Authentication failed: {e}", err=True)
        ctx.obj = {"user_context": None}
```

## Phase 4: MCP Protocol Integration (Day 4)

### 4.1 Extract MCP Components

#### Source Files:
```
FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/protocols/mcp/
├── types.py (~150 lines)
├── client.py (~300 lines)
├── server.py (~400 lines)
├── registry.py (~200 lines)
├── tools.py (~250 lines)
└── transport/
    ├── http.py (~200 lines)
    └── websocket.py (~250 lines)
```

### 4.2 Create MCP Adapter

```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/protocols/mcp/adapter.py

from typing import Any, Dict, List
from agenticraft.protocols.mcp import MCPClient, MCPServer, ToolRegistry
from agenticraft.core.agent import Agent

class MCPAdapter:
    """Adapt AgentiCraft agents to MCP protocol."""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self.server = MCPServer(port=8080)
        
    def register_agent(self, agent: Agent):
        """Register agent capabilities with MCP."""
        # Convert agent tools to MCP format
        for tool_name, tool_func in agent.tools.items():
            mcp_tool = self._convert_to_mcp_tool(tool_name, tool_func)
            self.registry.register_tool(mcp_tool)
            
        # Register agent as MCP service
        self.server.register_service(
            name=agent.name,
            capabilities=agent.capabilities,
            tools=list(agent.tools.keys())
        )
        
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        # Validate request format
        if not self._validate_mcp_request(request):
            return {"error": "Invalid MCP request format"}
            
        # Route to appropriate agent
        agent_name = request.get("agent")
        tool_name = request.get("tool")
        parameters = request.get("parameters", {})
        
        # Execute through sandbox
        agent = self.get_agent(agent_name)
        result = await agent.execute_tool_secure(tool_name, **parameters)
        
        # Format MCP response
        return {
            "id": request.get("id"),
            "result": result,
            "metadata": {
                "agent": agent_name,
                "tool": tool_name,
                "execution_time_ms": result.execution_time_ms
            }
        }
```

## Phase 5: Advanced Configuration & Monitoring (Day 5)

### 5.1 Enhanced Configuration Management

```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/production/config/secure_config.py

from typing import Dict, Any, Optional
import os
from cryptography.fernet import Fernet
from agenticraft.production.config.manager import ConfigManager

class SecureConfigManager(ConfigManager):
    """Enhanced config manager with encryption."""
    
    def __init__(self, app_name: str = "agenticraft"):
        super().__init__(app_name)
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        key_file = os.path.expanduser("~/.agenticraft/config.key")
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
            
    def set_secret(self, key: str, value: str):
        """Set encrypted configuration value."""
        encrypted = self.cipher.encrypt(value.encode()).decode()
        self.set(f"_encrypted_{key}", encrypted)
        
    def get_secret(self, key: str) -> Optional[str]:
        """Get decrypted configuration value."""
        encrypted = self.get(f"_encrypted_{key}")
        if encrypted:
            return self.cipher.decrypt(encrypted.encode()).decode()
        return None
```

### 5.2 Production Monitoring Integration

```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/production/monitoring/integrated.py

from typing import Dict, Any
from agenticraft.production.health import WorkflowHealth, AgentHealth, SystemHealth
from agenticraft.production.metrics import PrometheusExporter, MetricsCollector
from agenticraft.security.audit import AuditLogger
from agenticraft.protocols.monitoring import HealthCheck, MetricsProtocol

class IntegratedMonitoring:
    """Unified monitoring system."""
    
    def __init__(self):
        self.workflow_health = {}
        self.agent_health = AgentHealth()
        self.system_health = SystemHealth()
        self.metrics_collector = MetricsCollector()
        self.prometheus_exporter = PrometheusExporter()
        self.audit_logger = AuditLogger()
        
    async def register_workflow(self, workflow):
        """Register workflow for monitoring."""
        # Health monitoring
        self.workflow_health[workflow.name] = WorkflowHealth(workflow.name)
        
        # Metrics collection
        workflow_metrics = self.metrics_collector.register_workflow(workflow.name)
        
        # Hook into workflow lifecycle
        original_execute = workflow.execute
        
        async def monitored_execute(*args, **kwargs):
            # Start metrics
            start_time = workflow_metrics.record_execution_start()
            
            try:
                # Execute with monitoring
                result = await original_execute(*args, **kwargs)
                
                # Record success
                workflow_metrics.record_execution_end(start_time, success=True)
                self.workflow_health[workflow.name].record_execution(
                    duration_ms=(time.time() - start_time) * 1000,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Record failure
                workflow_metrics.record_execution_end(start_time, success=False)
                self.workflow_health[workflow.name].record_execution(
                    duration_ms=(time.time() - start_time) * 1000,
                    success=False
                )
                
                # Audit log error
                await self.audit_logger.log_error(
                    workflow=workflow.name,
                    error=str(e),
                    context=kwargs.get("user_context")
                )
                
                raise
                
        workflow.execute = monitored_execute
        
    def get_unified_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.system_health.export_health_dashboard(),
            "workflows": {
                name: health.get_status_summary()
                for name, health in self.workflow_health.items()
            },
            "agents": self.agent_health.get_summary(),
            "metrics": self.metrics_collector.get_all_metrics(),
        }
```

## Validation Suite

### Create Comprehensive Tests:

```python
# FILE: /Users/zahere/Desktop/TLV/agenticraft/tests/integration/test_security_integration.py

import pytest
import asyncio
from agenticraft.workflows import ResearchTeam
from agenticraft.security.middleware import security
from agenticraft.protocols.a2a.hybrid import MeshNetwork

class TestSecurityIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_secure_execution(self):
        """Test complete secure workflow execution."""
        # Create authenticated user context
        api_key = await security.api_key_auth.create_key(
            user_id="test_user",
            permissions=["execute_workflow", "read_results"]
        )
        
        request = {"headers": {"X-API-Key": api_key}}
        user_context = await security.authenticate(request)
        
        # Create workflow with all security features
        workflow = ResearchTeam(
            size=3,
            coordination_mode="hybrid",
            sandbox_type=SandboxType.PROCESS,
            memory_limit=512,
            timeout=30
        )
        
        # Register for monitoring
        monitoring = IntegratedMonitoring()
        await monitoring.register_workflow(workflow)
        
        # Execute with full security
        task = "Research the latest developments in quantum computing"
        result = await workflow.execute(task, user_context=user_context)
        
        # Validate results
        assert result is not None
        assert isinstance(result, ResearchReport)
        
        # Check audit log
        audit_entries = await security.audit_logger.get_entries(
            user_id="test_user",
            resource="research-team"
        )
        assert len(audit_entries) > 0
        
        # Check metrics
        metrics = monitoring.get_unified_status()
        assert metrics["workflows"]["research-team"]["metrics"]["total_executions"] == 1
        
    @pytest.mark.asyncio
    async def test_malicious_code_prevention(self):
        """Test that malicious code is blocked."""
        workflow = ResearchTeam(sandbox_type=SandboxType.PROCESS)
        
        # Try to execute malicious task
        malicious_task = "Execute this code: import os; os.system('rm -rf /')"
        
        with pytest.raises(SecurityException):
            await workflow.execute(malicious_task)
            
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self):
        """Test resource limits are enforced."""
        workflow = ResearchTeam(
            memory_limit=10,  # Very low limit
            timeout=1  # 1 second timeout
        )
        
        # Task that would exceed limits
        heavy_task = "Generate a detailed 10000 word research report"
        
        with pytest.raises(ResourceLimitExceeded):
            await workflow.execute(heavy_task)
```

## Post-Implementation Checklist

### Security Validation:
- [ ] All code execution happens in sandbox
- [ ] No direct file system access from agents
- [ ] All API endpoints require authentication
- [ ] Authorization checks on all operations
- [ ] Audit logs for all security events
- [ ] Resource limits enforced
- [ ] Network isolation verified

### Integration Validation:
- [ ] A2A protocols working with all workflows
- [ ] MCP compatibility verified
- [ ] Monitoring captures all metrics
- [ ] Configuration encryption working
- [ ] Health checks operational
- [ ] Prometheus metrics exported

### Performance Validation:
- [ ] Sandbox overhead < 10ms
- [ ] A2A coordination < 50ms overhead
- [ ] Auth checks < 5ms
- [ ] No memory leaks
- [ ] Scales to 100+ agents

### Documentation Updates:
- [ ] Security guide written
- [ ] API documentation updated
- [ ] Migration guide for existing users
- [ ] Performance tuning guide
- [ ] Troubleshooting guide

## Common Issues and Fixes

### Issue 1: Import Errors
```python
# If you see: ImportError: cannot import name 'ISandbox'
# Fix: Ensure all abstract interfaces are properly extracted

# Check that interfaces.py has:
from abc import ABC, abstractmethod

class ISandbox(ABC):
    @abstractmethod
    async def execute(self, operation, context, *args, **kwargs):
        pass
```

### Issue 2: Circular Dependencies
```python
# If you see: ImportError: circular import
# Fix: Use lazy imports or reorganize modules

# Instead of:
from agenticraft.workflows import ResearchTeam

# Use:
def get_research_team():
    from agenticraft.workflows import ResearchTeam
    return ResearchTeam
```

### Issue 3: Async Context Issues
```python
# If you see: RuntimeError: This event loop is already running
# Fix: Use proper async context managers

# Wrong:
result = asyncio.run(workflow.execute(task))

# Right:
async with workflow.execution_context() as ctx:
    result = await workflow.execute(task)
```

## Final Notes

1. **No Shortcuts**: Every security measure must be properly implemented
2. **Test Everything**: Each component needs comprehensive tests
3. **Monitor Performance**: Security shouldn't kill performance
4. **Document Changes**: Every API change needs documentation
5. **Gradual Rollout**: Deploy to staging first, monitor, then production

---

This implementation makes AgentiCraft production-ready with enterprise-grade security while maintaining its ease of use and powerful features.
