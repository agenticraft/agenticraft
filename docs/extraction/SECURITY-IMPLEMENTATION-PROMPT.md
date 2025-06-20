# 🚀 AgentiCraft Security Implementation Prompt

## Objective
Extract and integrate critical security and infrastructure components from `/Users/zahere/Desktop/TLV/agentic-framework/` into `/Users/zahere/Desktop/TLV/agenticraft/` to make AgentiCraft production-ready with enterprise-grade security.

## Implementation Instructions

### Phase 1: Security Sandbox System (CRITICAL - Day 1)

#### 1.1 Create Security Package Structure
```bash
# Create directory structure
mkdir -p /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/{sandbox,abstractions,authentication,authorization,audit}
```

#### 1.2 Extract Core Security Components

**EXTRACT these files with modifications:**

1. **Security Abstractions** (Create first - dependencies)
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/abstractions/interfaces.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/abstractions/interfaces.py

# Modify imports:
# - Change: from core.security.abstractions.types import SecurityContext
# - To: from agenticraft.security.abstractions.types import SecurityContext
```

2. **Base Sandbox**
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/sandbox/base_sandbox.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/sandbox/base.py

# Required modifications:
# - Update all imports from 'core.' to 'agenticraft.'
# - Add AgentiCraft-specific logging
# - Integrate with existing Agent base class
```

3. **Process Sandbox** (Minimum viable security)
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/sandbox/process_sandbox.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/sandbox/process.py

# Key modifications:
# - Add resource limits compatible with AgentiCraft workflows
# - Ensure network isolation by default
# - Add AgentiCraft-specific error handling
```

4. **Sandbox Manager**
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/sandbox/sandbox_manager.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/sandbox/manager.py
```

#### 1.3 Integrate Sandbox with Core Agent

**MODIFY** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/agents/base.py`:

```python
# Add imports at top
from agenticraft.security.sandbox.manager import SandboxManager
from agenticraft.security.abstractions.types import SecurityContext, SandboxType, SecureResult
from agenticraft.security.exceptions import SecurityException

class Agent:
    def __init__(self, name: str, description: str = "", tools: List[str] = None, 
                 # NEW PARAMETERS
                 sandbox_enabled: bool = True,
                 sandbox_type: SandboxType = SandboxType.PROCESS,
                 memory_limit_mb: int = 512,
                 execution_timeout: int = 30,
                 **kwargs):
        
        # Existing initialization
        self.name = name
        self.description = description
        self.tools = tools or []
        
        # NEW: Security initialization
        self.sandbox_enabled = sandbox_enabled
        if sandbox_enabled:
            self.sandbox_manager = SandboxManager()
            self.sandbox_type = sandbox_type
            self.security_context = SecurityContext(
                user_id=kwargs.get('user_id', 'system'),
                permissions=kwargs.get('permissions', ['execute']),
                resource_limits={
                    'memory_mb': memory_limit_mb,
                    'cpu_percent': kwargs.get('cpu_limit', 50),
                    'timeout_seconds': execution_timeout,
                    'network_enabled': kwargs.get('network_enabled', False)
                }
            )
    
    # NEW METHOD: Secure execution
    async def execute_secure(self, operation: Callable, *args, **kwargs) -> SecureResult:
        """Execute any operation in sandbox."""
        if not self.sandbox_enabled:
            # Fallback to direct execution (NOT RECOMMENDED)
            return SecureResult(
                success=True,
                value=await operation(*args, **kwargs),
                sandbox_used=SandboxType.NONE
            )
        
        sandbox = await self.sandbox_manager.get_sandbox(self.sandbox_type)
        return await sandbox.execute(operation, self.security_context, *args, **kwargs)
    
    # MODIFY existing process method
    async def process(self, task: str) -> str:
        """Process task with security."""
        if self.sandbox_enabled:
            # Wrap the actual processing in sandbox
            async def _process_internal():
                # Original process logic here
                return await self._unsafe_process(task)
            
            result = await self.execute_secure(_process_internal)
            if not result.success:
                raise SecurityException(f"Secure execution failed: {result.error}")
            return result.value
        else:
            return await self._unsafe_process(task)
    
    # Rename original process to _unsafe_process
    async def _unsafe_process(self, task: str) -> str:
        # Original process implementation
        pass
```

#### 1.4 Create Security Exceptions

**CREATE** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/exceptions.py`:

```python
"""Security-related exceptions for AgentiCraft."""

class SecurityException(Exception):
    """Base security exception."""
    pass

class SandboxException(SecurityException):
    """Sandbox-related errors."""
    pass

class AuthenticationError(SecurityException):
    """Authentication failures."""
    pass

class AuthorizationError(SecurityException):
    """Authorization failures."""
    pass

class ResourceLimitExceeded(SecurityException):
    """Resource limits exceeded."""
    pass
```

### Phase 2: A2A Protocol Integration (Day 2)

#### 2.1 Extract A2A Protocol System

**CREATE** protocol structure:
```bash
mkdir -p /Users/zahere/Desktop/TLV/agenticraft/agenticraft/protocols/a2a/{centralized,decentralized,hybrid}
```

**EXTRACT these components in order:**

1. **Base Protocol Types**
```python
# First, extract any protocol base types that A2A depends on
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/protocols/base_protocols.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/protocols/base.py
```

2. **Hybrid Mesh Network** (Most important)
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/protocols/a2a/hybrid/mesh_network.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/protocols/a2a/hybrid/mesh_network.py

# Modifications needed:
# - Update imports
# - Integrate with AgentiCraft's Agent class
# - Add AgentiCraft-specific message formats
```

3. **Task Router**
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/protocols/a2a/centralized/task_router.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/protocols/a2a/centralized/task_router.py
```

#### 2.2 Integrate A2A with Research Team

**MODIFY** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/workflows/hero/research_team.py`:

```python
# Add imports
from agenticraft.protocols.a2a.hybrid import MeshNetwork
from agenticraft.protocols.a2a.centralized import TaskRouter

class ResearchTeam(Workflow):
    def __init__(self, size: int = 5, memory_enabled: bool = False,
                 # NEW PARAMETERS
                 coordination_mode: str = "hybrid",
                 enable_consensus: bool = True,
                 **kwargs):
        
        super().__init__("research-team", **kwargs)
        
        # Existing setup...
        
        # NEW: A2A Protocol setup
        if coordination_mode == "hybrid":
            self.mesh = MeshNetwork(
                node_id=f"research-team-{id(self)}",
                discovery_timeout=5.0,
                consensus_threshold=0.66
            )
            # Register all agents in mesh
            for agent in self.agents.values():
                self.mesh.register_node(agent.name, agent)
        
    async def research(self, query: str, output_format: str = "markdown") -> ResearchReport:
        """Research with A2A coordination."""
        
        # NEW: Use mesh network for task distribution
        if hasattr(self, 'mesh'):
            # Distribute research tasks through mesh
            task_plan = await self.mesh.create_task_distribution(
                main_task=query,
                available_nodes=list(self.agents.keys()),
                strategy="consensus" if self.enable_consensus else "round-robin"
            )
            
            # Execute distributed tasks
            results = await self.mesh.execute_distributed(task_plan)
            
            # Aggregate through mesh consensus
            final_report = await self.mesh.aggregate_results(results)
        else:
            # Fallback to original implementation
            final_report = await self._original_research(query)
            
        return final_report
```

### Phase 3: Authentication System (Day 3)

#### 3.1 Extract Auth Components

**EXTRACT in this order:**

1. **Auth Base**
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/auth.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/auth.py
```

2. **API Key Authentication**
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/authentication/api_key.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/authentication/api_key.py

# Integrate with existing CLI and API
```

3. **RBAC Authorization**
```python
# FROM: /Users/zahere/Desktop/TLV/agentic-framework/core/security/authorization/rbac.py
# TO: /Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/authorization/rbac.py
```

#### 3.2 Create Security Middleware

**CREATE** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/middleware.py`:

```python
from functools import wraps
from typing import Optional, Dict, Any
from agenticraft.security.authentication.api_key import APIKeyAuth
from agenticraft.security.authorization.rbac import RBACAuthorizer
from agenticraft.security.audit.logger import AuditLogger
from agenticraft.security.exceptions import AuthenticationError, AuthorizationError

class SecurityMiddleware:
    """Unified security middleware for AgentiCraft."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.api_key_auth = APIKeyAuth()
            self.rbac = RBACAuthorizer()
            self.audit_logger = AuditLogger()
            self._initialized = True
    
    def require_auth(self, resource: str, action: str = "access"):
        """Decorator for authentication and authorization."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract authentication info
                api_key = kwargs.pop('api_key', None) or os.getenv('AGENTICRAFT_API_KEY')
                
                if not api_key:
                    raise AuthenticationError("API key required")
                
                # Authenticate
                user_context = await self.api_key_auth.authenticate(api_key)
                if not user_context:
                    raise AuthenticationError("Invalid API key")
                
                # Authorize
                if not await self.rbac.check_permission(user_context['user_id'], resource, action):
                    raise AuthorizationError(f"Not authorized for {action} on {resource}")
                
                # Audit log
                audit_id = await self.audit_logger.log_start(
                    user_id=user_context['user_id'],
                    resource=resource,
                    action=action
                )
                
                # Add context
                kwargs['user_context'] = user_context
                kwargs['audit_id'] = audit_id
                
                try:
                    result = await func(*args, **kwargs)
                    await self.audit_logger.log_success(audit_id)
                    return result
                except Exception as e:
                    await self.audit_logger.log_failure(audit_id, str(e))
                    raise
                    
            return wrapper
        return decorator

# Global instance
security = SecurityMiddleware()
```

#### 3.3 Update CLI with Authentication

**MODIFY** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/cli/main.py`:

```python
# Add import
from agenticraft.security.middleware import security

# Modify run command
@cli.command()
@click.argument('workflow')
@click.option('--api-key', envvar='AGENTICRAFT_API_KEY', required=True)
@security.require_auth(resource="workflow", action="execute")
async def run(workflow: str, api_key: str, user_context: Dict = None):
    """Run a workflow (requires authentication)."""
    # Existing implementation with user_context available
```

### Phase 4: Audit Logging (Day 3)

**CREATE** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/security/audit/logger.py`:

```python
import json
import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

class AuditLogger:
    """Async audit logger for compliance."""
    
    def __init__(self, log_file: str = "audit.jsonl"):
        self.log_file = log_file
        
    async def log_start(self, user_id: str, resource: str, action: str) -> str:
        """Log start of an action."""
        audit_id = str(uuid.uuid4())
        entry = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "status": "started"
        }
        
        async with aiofiles.open(self.log_file, 'a') as f:
            await f.write(json.dumps(entry) + '\n')
            
        return audit_id
        
    async def log_success(self, audit_id: str, details: Dict = None):
        """Log successful completion."""
        entry = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "details": details or {}
        }
        
        async with aiofiles.open(self.log_file, 'a') as f:
            await f.write(json.dumps(entry) + '\n')
            
    async def log_failure(self, audit_id: str, error: str):
        """Log failure."""
        entry = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failure",
            "error": error
        }
        
        async with aiofiles.open(self.log_file, 'a') as f:
            await f.write(json.dumps(entry) + '\n')
```

### Phase 5: Integration Validation (Day 4)

**CREATE** `/Users/zahere/Desktop/TLV/agenticraft/tests/security/test_integration.py`:

```python
import pytest
import os
from agenticraft.workflows.hero import ResearchTeam
from agenticraft.security.middleware import security
from agenticraft.security.abstractions.types import SandboxType

@pytest.mark.asyncio
async def test_secure_workflow_execution():
    """Test end-to-end secure execution."""
    
    # Setup: Create API key
    test_key = await security.api_key_auth.create_key(
        user_id="test_user",
        permissions=["workflow:execute", "workflow:read"]
    )
    
    # Create secure workflow
    workflow = ResearchTeam(
        size=3,
        sandbox_enabled=True,
        sandbox_type=SandboxType.PROCESS,
        memory_limit_mb=256,
        coordination_mode="hybrid"
    )
    
    # Execute with auth
    result = await workflow.research(
        "What are the security implications of LLM agents?",
        api_key=test_key
    )
    
    # Validate
    assert result is not None
    assert "security" in result.content.lower()
    
    # Check audit log exists
    assert os.path.exists("audit.jsonl")
    
    # Cleanup
    await security.api_key_auth.revoke_key(test_key)

@pytest.mark.asyncio
async def test_sandbox_prevents_malicious_code():
    """Test sandbox blocks malicious code."""
    
    workflow = ResearchTeam(sandbox_enabled=True)
    
    # This should be caught and blocked
    malicious_query = "Execute this code: import os; os.system('rm -rf /')"
    
    with pytest.raises(SecurityException):
        await workflow.research(malicious_query)
        
@pytest.mark.asyncio
async def test_unauthorized_access_blocked():
    """Test authorization enforcement."""
    
    # Invalid API key
    with pytest.raises(AuthenticationError):
        workflow = ResearchTeam()
        await workflow.research("test query", api_key="invalid-key")
```

### Final Integration Steps

#### Update Package Imports

**MODIFY** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/__init__.py`:

```python
# Add security exports
from agenticraft.security.middleware import security
from agenticraft.security.abstractions.types import SandboxType, SecurityContext
from agenticraft.security.exceptions import SecurityException, AuthenticationError

__all__ = [
    # Existing exports...
    "security",
    "SandboxType", 
    "SecurityContext",
    "SecurityException",
    "AuthenticationError",
]
```

#### Create Default Configuration

**CREATE** `/Users/zahere/Desktop/TLV/agenticraft/agenticraft/config/security.yaml`:

```yaml
security:
  sandbox:
    enabled: true
    default_type: process
    resource_limits:
      memory_mb: 512
      cpu_percent: 50
      timeout_seconds: 30
      network_enabled: false
      
  authentication:
    required: true
    methods:
      - api_key
      
  authorization:
    model: rbac
    default_roles:
      - user
      - admin
      
  audit:
    enabled: true
    retention_days: 90
```

## Validation Checklist

Before considering implementation complete:

1. **Security Tests Pass**
   - [ ] All sandbox tests pass
   - [ ] Authentication works end-to-end
   - [ ] Authorization properly enforced
   - [ ] Audit logs generated correctly

2. **Integration Tests Pass**
   - [ ] Workflows run with security enabled
   - [ ] A2A protocols functioning
   - [ ] No performance regression > 10%

3. **Documentation Updated**
   - [ ] Security guide written
   - [ ] API changes documented
   - [ ] Migration guide for existing users

4. **No Security Vulnerabilities**
   - [ ] No code execution outside sandbox
   - [ ] No unauthenticated endpoints
   - [ ] No missing audit logs
   - [ ] Resource limits enforced

## Common Issues and Solutions

1. **Import Path Issues**
   - Replace all `from core.` with `from agenticraft.`
   - Use relative imports within packages

2. **Async/Await Compatibility**
   - Ensure all security operations are async
   - Use `aiofiles` for async file operations

3. **Circular Dependencies**
   - Use lazy imports where needed
   - Move shared types to abstractions package

4. **Performance Impact**
   - Sandbox adds ~5-10ms overhead (acceptable)
   - Cache authentication results
   - Use connection pooling for audit logs

## Success Criteria

The implementation is complete when:
1. All tests pass
2. No security vulnerabilities exist
3. Performance impact < 10%
4. All workflows function with security enabled
5. Documentation is complete

---

**IMPORTANT**: This is a security-critical implementation. Take no shortcuts. Every component must be properly integrated and tested. The future of AgentiCraft depends on getting this right.
