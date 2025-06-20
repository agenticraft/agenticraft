# Security & Sandbox System

## Overview

AgentiCraft's security system provides comprehensive protection for agent execution, including:

- **Sandboxed Execution**: Run code and operations in isolated environments
- **Resource Limits**: Control memory, CPU, and execution time
- **Permission System**: Fine-grained access control
- **Multiple Sandbox Types**: Process isolation, Docker containers, and restricted Python

## Quick Start

### Basic Secure Agent

```python
from agenticraft import Agent

# Create agent with sandbox enabled
agent = Agent(
    name="SecureBot",
    sandbox_enabled=True,
    sandbox_type="restricted",
    memory_limit=256,  # MB
    cpu_limit=50.0     # percentage
)

# Execute code securely
code = "result = sum([1, 2, 3, 4, 5])"
result = await agent.execute_secure(code)
print(result)  # {"result": 15}
```

### Secure Workflow Execution

```python
from agenticraft.workflows import ResearchTeam

team = ResearchTeam()

# Define user context with permissions
user_context = {
    "user_id": "alice@company.com",
    "permissions": ["execute_workflow", "read_results"],
    "resource_limits": {
        "memory_mb": 512,
        "timeout_seconds": 60
    }
}

# Execute with security context
report = await team.research(
    topic="AI safety",
    user_context=user_context
)
```

## Sandbox Types

### 1. Restricted Python Sandbox
- **Best for**: Simple code execution, calculations
- **Features**: Limited built-ins, no imports, memory safety
- **Performance**: Fastest, minimal overhead

```python
agent = Agent(
    sandbox_enabled=True,
    sandbox_type="restricted"
)
```

### 2. Process Sandbox
- **Best for**: Complete isolation, untrusted code
- **Features**: Separate process, resource limits via OS
- **Requirements**: Unix-like system with resource module

```python
agent = Agent(
    sandbox_enabled=True,
    sandbox_type="process"
)
```

### 3. Docker Sandbox (Coming Soon)
- **Best for**: Full isolation, complex environments
- **Features**: Container isolation, custom images
- **Requirements**: Docker installed and running

## Security Context

The `SecurityContext` defines permissions and limits:

```python
from agenticraft.security import SecurityContext

context = SecurityContext(
    user_id="user@example.com",
    permissions=["execute", "read", "write"],
    resource_limits={
        "memory_mb": 512,
        "cpu_percent": 50.0,
        "timeout_seconds": 30,
        "network_access": False,
        "filesystem_access": False
    }
)
```

## Resource Limits

Control resource usage to prevent abuse:

- **memory_mb**: Maximum memory allocation
- **cpu_percent**: CPU usage percentage
- **timeout_seconds**: Maximum execution time
- **max_file_size_mb**: File size limits
- **network_access**: Allow/deny network
- **filesystem_access**: Allow/deny filesystem

## Permission System

Fine-grained permissions for operations:

- `execute`: Run code/operations
- `execute_workflow`: Run workflows
- `read_results`: Access results
- `write`: Modify data
- `admin`: Full access

## Advanced Usage

### Custom Sandbox Manager

```python
from agenticraft.security import SandboxManager

# Create custom manager
manager = SandboxManager()
await manager.initialize()

# Get specific sandbox type
sandbox = await manager.get_sandbox(SandboxType.PROCESS)

# Execute with custom context
result = await sandbox.execute_code(
    code="print('Hello')",
    context=SecurityContext(user_id="custom")
)
```

### Secure Tool Execution

```python
# Execute tools in sandbox
result = await agent.execute_tool_secure(
    "web_search",
    query="Python security",
    user_context={"user_id": "alice"}
)
```

### Audit Logging

All security events are logged for compliance:

```python
# Security events automatically logged:
# - Authentication attempts
# - Authorization checks
# - Resource limit violations
# - Sandbox execution results
```

## Best Practices

1. **Always Enable Sandbox for Untrusted Code**
   ```python
   agent = Agent(sandbox_enabled=True)
   ```

2. **Set Appropriate Resource Limits**
   ```python
   # For simple tasks
   memory_limit=128
   timeout=10
   
   # For complex operations
   memory_limit=1024
   timeout=60
   ```

3. **Use Least Privilege Principle**
   ```python
   # Only grant necessary permissions
   permissions=["execute", "read_results"]
   ```

4. **Monitor Resource Usage**
   ```python
   result = await agent.execute_secure(code)
   print(f"Memory used: {result.resource_usage['memory_mb']}MB")
   print(f"Time taken: {result.execution_time_ms}ms")
   ```

## Error Handling

```python
from agenticraft.security.exceptions import (
    SecurityException,
    PermissionDenied,
    ResourceLimitExceeded
)

try:
    result = await agent.execute_secure(code)
except PermissionDenied as e:
    print(f"Access denied: {e}")
except ResourceLimitExceeded as e:
    print(f"Resource limit hit: {e}")
except SecurityException as e:
    print(f"Security error: {e}")
```

## Configuration

### Environment Variables

```bash
# Default sandbox type
export AGENTICRAFT_DEFAULT_SANDBOX=process

# Default resource limits
export AGENTICRAFT_DEFAULT_MEMORY_MB=512
export AGENTICRAFT_DEFAULT_TIMEOUT=30
```

### Config File

```python
# config.py
SECURITY_CONFIG = {
    "default_sandbox_type": "restricted",
    "default_memory_mb": 256,
    "default_cpu_percent": 50.0,
    "enable_audit_logging": True
}
```

## Migration Guide

### Existing Code

```python
# Before
agent = Agent(name="MyAgent")
response = agent.run("Calculate 2+2")

# After (with security)
agent = Agent(
    name="MyAgent",
    sandbox_enabled=True
)
response = agent.run("Calculate 2+2")
```

### Workflows

```python
# Before
workflow.run(task="Research AI")

# After (with user context)
workflow.run(
    task="Research AI",
    user_context={"user_id": "alice", "permissions": ["execute_workflow"]}
)
```

## Troubleshooting

### "Sandbox not available"
- Check system requirements
- Ensure resource module available (Unix)
- Try different sandbox type

### "Permission denied"
- Check user permissions in context
- Ensure "execute" permission granted
- Verify resource limits

### "Resource limit exceeded"
- Increase memory/timeout limits
- Optimize code execution
- Use streaming for large operations

## Security Considerations

1. **Never Disable Sandbox for Production**
2. **Regularly Review Permissions**
3. **Monitor Resource Usage**
4. **Keep Audit Logs**
5. **Update Security Patches**

## Future Enhancements

- Docker container sandbox
- Network isolation policies
- Custom security policies
- Integration with cloud security services
- Advanced threat detection
