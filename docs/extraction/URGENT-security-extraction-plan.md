# 🚨 URGENT: AgentiCraft Security & Infrastructure Extraction Plan

## Critical Gap Analysis

After deeper analysis, we discovered that AgentiCraft is missing **critical infrastructure** that makes it unsafe for production use without immediate remediation.

## 🔴 CRITICAL COMPONENTS (Must Extract)

### 1. Security Sandbox System (Days 1-2)
**Risk**: Agents can execute arbitrary code without isolation

```python
# Extract from /core/security/sandbox/
- base_sandbox.py      # Core abstraction
- process_sandbox.py   # Process isolation (minimum viable)
- docker_sandbox.py    # Docker isolation (recommended)
- sandbox_manager.py   # Orchestration

# Integration points:
- Wrap all agent execute() methods
- Isolate tool execution
- Contain code generation outputs
```

**Minimal Implementation** (1 day):
```python
class AgentSandbox:
    async def execute_isolated(self, agent, task):
        # Process-level isolation
        # Resource limits (CPU, memory, time)
        # No network access by default
```

### 2. A2A (Agent-to-Agent) Protocol (Days 2-4)
**Risk**: No sophisticated multi-agent coordination

```python
# Extract from /core/protocols/a2a/
Priority order:
1. hybrid/mesh_network.py      # Flexible agent networking
2. hybrid/protocol_bridge.py   # Protocol compatibility
3. centralized/task_router.py  # Task distribution
4. decentralized/consensus.py  # Agreement protocols

# Current AgentiCraft uses basic message passing
# A2A provides:
- Agent discovery
- Load balancing
- Fault tolerance
- Consensus mechanisms
```

### 3. Authentication & Authorization (Days 4-5)
**Risk**: No user authentication or permission management

```python
# Extract from /core/security/
- auth.py                    # Authentication base
- authentication/api_key.py  # API key auth (minimum)
- authorization/rbac.py      # Role-based access
- audit/audit_logger.py      # Compliance logging

# Must integrate with:
- CLI commands
- API endpoints
- Agent execution
- Resource access
```

### 4. MCP (Model Communication Protocol) (Day 5)
**Risk**: Non-standard communication patterns limit interoperability

```python
# Extract from /core/protocols/mcp/
- types.py     # Protocol types
- client.py    # MCP client
- server.py    # MCP server
- registry.py  # Capability registry

# Provides:
- Standardized tool calling
- Model capability negotiation
- Transport abstraction
```

## 📋 5-Day Emergency Extraction Plan

### Day 1: Basic Sandbox
- [ ] Extract process_sandbox.py
- [ ] Create AgentSandbox wrapper
- [ ] Integrate with agent execution
- [ ] Add resource limits

### Day 2: Advanced Sandbox + A2A Start
- [ ] Extract docker_sandbox.py
- [ ] Extract sandbox_manager.py
- [ ] Begin A2A mesh_network.py extraction
- [ ] Test isolation

### Day 3: A2A Protocol Completion
- [ ] Complete mesh network
- [ ] Extract protocol_bridge.py
- [ ] Extract task_router.py
- [ ] Integrate with workflows

### Day 4: Security Suite
- [ ] Extract authentication system
- [ ] Add API key support
- [ ] Extract RBAC authorization
- [ ] Add audit logging

### Day 5: MCP + Integration
- [ ] Extract MCP protocol
- [ ] Integration testing
- [ ] Security audit
- [ ] Documentation

## 🛡️ Immediate Mitigations (Can do TODAY)

### 1. Basic Process Isolation
```python
import subprocess
import resource

class QuickSandbox:
    def execute_isolated(self, code, timeout=30):
        # Limit resources
        def limit_resources():
            resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))  # 512MB
            resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
            
        # Run in subprocess with limits
        proc = subprocess.Popen(
            [sys.executable, '-c', code],
            preexec_fn=limit_resources,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
```

### 2. Basic Auth
```python
from functools import wraps

def require_api_key(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        api_key = kwargs.get('api_key') or os.getenv('AGENTICRAFT_API_KEY')
        if not api_key or api_key != VALID_API_KEY:
            raise AuthenticationError("Invalid API key")
        return await func(*args, **kwargs)
    return wrapper
```

### 3. Basic Audit
```python
import logging
from datetime import datetime

class AuditLogger:
    def log_execution(self, user, agent, action, result):
        audit_log.info(f"{datetime.now()} | USER:{user} | AGENT:{agent} | ACTION:{action} | RESULT:{result}")
```

## 🎯 Success Criteria

After 5-day extraction:
1. **No arbitrary code execution** - All code runs in sandbox
2. **Authenticated access** - API key required
3. **Agent coordination** - A2A protocols active
4. **Audit trail** - All actions logged
5. **Standard protocols** - MCP compliance

## ⚠️ Current Production Risks

Without these components, AgentiCraft has:
1. **Remote Code Execution** vulnerability
2. **No access control** - Anyone can use
3. **No audit trail** - No compliance
4. **Limited scale** - Basic coordination only
5. **No isolation** - Agent compromise affects all

## 📊 Extraction Complexity

| Component | Files | LoC | Complexity | Priority |
|-----------|-------|-----|------------|----------|
| Process Sandbox | 2 | 400 | Medium | CRITICAL |
| Docker Sandbox | 1 | 300 | Medium | HIGH |
| A2A Mesh | 3 | 800 | High | CRITICAL |
| Auth System | 4 | 600 | Medium | CRITICAL |
| MCP Protocol | 5 | 1000 | High | HIGH |
| **Total** | **15** | **3100** | - | - |

## 🚀 Post-Extraction Architecture

```
┌─────────────────┐
│   User/API      │
├─────────────────┤
│ Auth Layer      │ ← New: API keys, RBAC
├─────────────────┤
│ AgentiCraft     │
├─────────────────┤
│ A2A Protocol    │ ← New: Mesh network
├─────────────────┤
│ Agent Sandbox   │ ← New: Isolation
├─────────────────┤
│ LLM/Tools       │
└─────────────────┘
```

## 💡 Key Takeaway

**Current AgentiCraft**: Feature-complete but not production-safe
**After extraction**: Production-ready with enterprise-grade security

**Time to production-ready**: 5 days of focused extraction

---

**RECOMMENDATION**: Start extraction immediately. The sandbox system alone (1 day) would significantly improve security posture.
