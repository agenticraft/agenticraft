# AgentiCraft Security Implementation

## 🔐 Overview

This implementation adds comprehensive security features to AgentiCraft, including:

1. **Sandboxed Execution** - Isolate code execution in secure environments
2. **A2A Protocols** - Advanced agent-to-agent coordination (next phase)
3. **Authentication & Authorization** - API keys, RBAC (next phase)
4. **Audit Logging** - Complete security event tracking (next phase)

## ✅ What's Implemented

### Phase 1: Security Sandbox (COMPLETE)

- ✅ **Process Sandbox** - Process-level isolation with resource limits
- ✅ **Docker Sandbox** - Container-based isolation (requires Docker)
- ✅ **Restricted Python Sandbox** - Lightweight restricted environment
- ✅ **Sandbox Manager** - Centralized sandbox lifecycle management
- ✅ **Security Context** - User permissions and resource limits
- ✅ **Agent Integration** - Agents can execute code securely

### Security Features

1. **Code Isolation**
   - Separate process execution
   - Docker container support
   - Restricted Python environment

2. **Resource Limits**
   - Memory limits (MB)
   - CPU limits (percentage)
   - Execution timeouts
   - File size limits
   - Network access control

3. **Permission System**
   - User-based permissions
   - Resource access control
   - Execution permissions

## 🚀 Quick Start

### 1. Test Sandbox Security

```bash
# Quick test
python test_sandbox_quick.py

# Comprehensive test
python test_sandbox_security.py
```

### 2. Use Sandboxed Agent

```python
from agenticraft import Agent

# Create a secure agent
agent = Agent(
    name="SecureBot",
    instructions="You are a helpful assistant.",
    sandbox_enabled=True,
    sandbox_type="process",  # or "docker" if available
    memory_limit=256,        # MB
    cpu_limit=50.0          # Percentage
)

# Execute code securely
code = """
def calculate(x, y):
    return x + y

result = calculate(10, 20)
"""

result = await agent.execute_secure(code)
print(result)  # Output: {'result': 30}
```

### 3. Direct Sandbox Usage

```python
from agenticraft.security import SecurityContext, SandboxType
from agenticraft.security.sandbox import get_sandbox_manager

# Get sandbox
manager = get_sandbox_manager()
sandbox = await manager.get_sandbox(SandboxType.PROCESS)

# Create security context
context = SecurityContext(
    user_id="john_doe",
    permissions=["execute"],
    resource_limits={
        "memory_mb": 512,
        "cpu_percent": 75.0,
        "timeout_seconds": 30
    }
)

# Execute code
result = await sandbox.execute_code("print('Hello!')", context)
```

## 🛡️ Security Guarantees

### What's Blocked:
- ❌ File system access (except temp files)
- ❌ Network requests (configurable)
- ❌ System commands (`os.system`, `subprocess`)
- ❌ Dangerous imports
- ❌ Resource exhaustion
- ❌ Infinite loops (timeout)

### What's Allowed:
- ✅ Pure computation
- ✅ Safe built-in functions
- ✅ Memory within limits
- ✅ CPU within limits
- ✅ Standard library (safe parts)

## 🐳 Docker Sandbox

For maximum security, use Docker sandbox:

```bash
# Install Docker SDK
pip install docker

# Ensure Docker daemon is running
docker version

# Docker sandbox will be auto-detected
```

## 📊 Performance

- **Process Sandbox**: ~10-50ms overhead
- **Docker Sandbox**: ~100-500ms overhead (first run pulls image)
- **Restricted Sandbox**: ~1-5ms overhead

## ⚠️ Known Limitations

1. **Process Sandbox**
   - Unix/Linux only (uses `resource` module)
   - Limited on macOS (some limits not enforced)
   - Not available on Windows

2. **Docker Sandbox**
   - Requires Docker installed
   - Higher overhead
   - Requires proper permissions

3. **Restricted Sandbox**
   - Less secure than process/Docker
   - In-process execution
   - Basic protection only

## 🔜 Next Steps

### Phase 2: A2A Protocols
- Mesh network coordination
- Protocol bridges
- Consensus mechanisms

### Phase 3: Authentication
- API key management
- JWT tokens
- OAuth integration

### Phase 4: Authorization
- Role-based access control (RBAC)
- Attribute-based access control (ABAC)
- Fine-grained permissions

### Phase 5: Audit Logging
- Security event tracking
- Compliance logging
- Threat detection

## 🧪 Testing

```bash
# Run all security tests
pytest tests/security/ -v

# Test specific sandbox
pytest tests/security/test_sandbox.py::test_process_sandbox -v

# Benchmark performance
python scripts/benchmark_sandbox.py
```

## 📝 Configuration

```python
# In your .env file
AGENTICRAFT_DEFAULT_SANDBOX=process  # or docker, restricted
AGENTICRAFT_SANDBOX_MEMORY_MB=512
AGENTICRAFT_SANDBOX_CPU_PERCENT=50
AGENTICRAFT_SANDBOX_TIMEOUT=30
```

## 🐛 Troubleshooting

### "Docker not available"
- Install Docker: `pip install docker`
- Start Docker daemon
- Check permissions: `docker ps`

### "Resource limits not enforced"
- Linux: Should work fully
- macOS: Some limits may not work
- Windows: Use Docker or restricted sandbox

### "Import error"
- Ensure you're in the right directory
- Check Python path includes AgentiCraft

## 📚 API Reference

### SecurityContext
```python
SecurityContext(
    user_id: str,
    permissions: List[str],
    resource_limits: Dict[str, Any],
    metadata: Dict[str, Any] = None
)
```

### SandboxManager
```python
manager = get_sandbox_manager()
sandbox = await manager.get_sandbox(SandboxType.PROCESS)
available = manager.get_available_types()
await manager.cleanup()
```

### SecureResult
```python
result = await sandbox.execute_code(code, context)
if result.success:
    print(result.result)
else:
    print(result.error)
```

---

For more information, see the [full implementation guide](docs/extraction/paste.txt).
