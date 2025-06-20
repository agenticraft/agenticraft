# 🚀 AgentiCraft Quick Security Implementation Guide

## Emergency Security Patches (Can implement TODAY)

### 1. Basic Code Isolation (2 hours)

```python
# /agenticraft/security/quick_sandbox.py

import subprocess
import tempfile
import os
import signal
import resource
from typing import Any, Dict, Optional

class QuickSandbox:
    """Minimal sandbox for code execution."""
    
    def __init__(self, timeout: int = 30, memory_mb: int = 512):
        self.timeout = timeout
        self.memory_limit = memory_mb * 1024 * 1024
        
    def execute_code(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute code in isolated subprocess."""
        
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Add context injection
            if context:
                f.write(f"context = {repr(context)}\n\n")
            f.write(code)
            temp_file = f.name
            
        try:
            # Set up resource limits
            def limit_resources():
                # Memory limit
                resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
                # CPU time limit
                resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
                # Disable network (on Linux)
                if hasattr(os, 'setgroups'):
                    os.setgroups([])
                    
            # Run in subprocess
            proc = subprocess.Popen(
                ['python', temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=limit_resources,
                env={'PYTHONPATH': ''}  # Clear PYTHONPATH
            )
            
            try:
                stdout, stderr = proc.communicate(timeout=self.timeout)
                return {
                    'success': proc.returncode == 0,
                    'stdout': stdout.decode(),
                    'stderr': stderr.decode(),
                    'returncode': proc.returncode
                }
            except subprocess.TimeoutExpired:
                proc.kill()
                return {
                    'success': False,
                    'error': 'Execution timeout',
                    'stdout': '',
                    'stderr': ''
                }
                
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)

# Integration with agents
class SecureAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sandbox = QuickSandbox()
        
    async def execute_generated_code(self, code: str) -> Any:
        """Execute generated code in sandbox."""
        result = self.sandbox.execute_code(code)
        if not result['success']:
            raise RuntimeError(f"Code execution failed: {result.get('error', result.get('stderr'))}")
        return result['stdout']
```

### 2. Basic Authentication (1 hour)

```python
# /agenticraft/security/auth.py

import os
import hashlib
import secrets
from functools import wraps
from typing import Optional, Dict, Any
import json
from datetime import datetime, timedelta

class SimpleAuth:
    """Basic API key authentication."""
    
    def __init__(self, keys_file: str = "api_keys.json"):
        self.keys_file = keys_file
        self.keys = self._load_keys()
        
    def _load_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from file."""
        if os.path.exists(self.keys_file):
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_keys(self):
        """Save API keys to file."""
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys, f, indent=2)
            
    def generate_api_key(self, user_id: str, name: str = "default") -> str:
        """Generate new API key for user."""
        key = f"sk-{secrets.token_urlsafe(32)}"
        
        self.keys[key] = {
            "user_id": user_id,
            "name": name,
            "created": datetime.now().isoformat(),
            "last_used": None,
            "active": True
        }
        
        self._save_keys()
        return key
        
    def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user info."""
        if api_key in self.keys and self.keys[api_key]["active"]:
            # Update last used
            self.keys[api_key]["last_used"] = datetime.now().isoformat()
            self._save_keys()
            return self.keys[api_key]
        return None
        
    def revoke_key(self, api_key: str):
        """Revoke an API key."""
        if api_key in self.keys:
            self.keys[api_key]["active"] = False
            self._save_keys()

# Decorator for protecting functions
def require_auth(auth: SimpleAuth):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get API key from various sources
            api_key = None
            
            # 1. Check kwargs
            api_key = kwargs.pop('api_key', None)
            
            # 2. Check environment
            if not api_key:
                api_key = os.getenv('AGENTICRAFT_API_KEY')
                
            # 3. Check headers (for web requests)
            if not api_key and 'request' in kwargs:
                request = kwargs['request']
                api_key = request.headers.get('X-API-Key')
                
            # Validate
            if not api_key:
                raise AuthenticationError("API key required")
                
            user_info = auth.validate_key(api_key)
            if not user_info:
                raise AuthenticationError("Invalid API key")
                
            # Add user info to kwargs
            kwargs['user_info'] = user_info
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example
auth = SimpleAuth()

@require_auth(auth)
async def secure_workflow_execution(workflow_name: str, task: str, user_info: Dict = None):
    """Execute workflow with authentication."""
    print(f"User {user_info['user_id']} executing {workflow_name}")
    # ... rest of execution
```

### 3. Basic Audit Logging (30 minutes)

```python
# /agenticraft/security/audit.py

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
import asyncio
from contextlib import asynccontextmanager

class AuditLogger:
    """Simple audit logger for compliance."""
    
    def __init__(self, log_file: str = "audit.log"):
        self.logger = logging.getLogger("audit")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def log_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an audit event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result,
            "details": details or {}
        }
        
        self.logger.info(json.dumps(event))
        
    @asynccontextmanager
    async def audit_context(self, user_id: str, action: str, resource: str):
        """Context manager for auditing operations."""
        start_time = datetime.now()
        details = {"start_time": start_time.isoformat()}
        
        try:
            yield details
            self.log_event(
                event_type="action",
                user_id=user_id,
                action=action,
                resource=resource,
                result="success",
                details=details
            )
        except Exception as e:
            details["error"] = str(e)
            self.log_event(
                event_type="action",
                user_id=user_id,
                action=action,
                resource=resource,
                result="failure",
                details=details
            )
            raise
        finally:
            details["duration_ms"] = (datetime.now() - start_time).total_seconds() * 1000

# Integration example
audit = AuditLogger()

class AuditedWorkflow(Workflow):
    async def execute(self, task: str, user_info: Dict):
        async with audit.audit_context(
            user_id=user_info['user_id'],
            action="workflow_execution",
            resource=self.name
        ) as details:
            details["task"] = task
            result = await super().execute(task)
            details["result_summary"] = str(result)[:100]
            return result
```

### 4. Rate Limiting (30 minutes)

```python
# /agenticraft/security/rate_limit.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio

class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        
    def is_allowed(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, Optional[int]]:
        """Check if request is allowed."""
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= max_requests:
            # Calculate retry after
            oldest = min(self.requests[key])
            retry_after = int((oldest + timedelta(seconds=window_seconds) - now).total_seconds())
            return False, retry_after
            
        # Allow request
        self.requests[key].append(now)
        return True, None

# Decorator for rate limiting
rate_limiter = RateLimiter()

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user ID for rate limiting
            user_info = kwargs.get('user_info', {})
            user_id = user_info.get('user_id', 'anonymous')
            
            allowed, retry_after = rate_limiter.is_allowed(
                user_id,
                max_requests,
                window_seconds
            )
            
            if not allowed:
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 5. Integration Example

```python
# /agenticraft/secure_agent.py

from agenticraft.security.quick_sandbox import QuickSandbox
from agenticraft.security.auth import SimpleAuth, require_auth
from agenticraft.security.audit import AuditLogger
from agenticraft.security.rate_limit import rate_limit

# Initialize security components
sandbox = QuickSandbox()
auth = SimpleAuth()
audit = AuditLogger()

class SecureAgentiCraft:
    """Secure wrapper for AgentiCraft."""
    
    @require_auth(auth)
    @rate_limit(max_requests=100, window_seconds=60)
    async def execute_workflow(
        self,
        workflow_name: str,
        task: str,
        user_info: Dict = None
    ):
        """Execute workflow with full security."""
        
        # Audit log
        async with audit.audit_context(
            user_id=user_info['user_id'],
            action="execute_workflow",
            resource=workflow_name
        ) as details:
            
            # Get workflow
            workflow = self.get_workflow(workflow_name)
            
            # Execute with sandboxing
            if hasattr(workflow, 'generates_code') and workflow.generates_code:
                # Wrap code execution in sandbox
                original_execute = workflow.execute_code
                workflow.execute_code = lambda code: sandbox.execute_code(code)
                
            # Execute workflow
            result = await workflow.execute(task)
            
            details["success"] = True
            return result

# Setup CLI with auth
@click.command()
@click.option('--api-key', envvar='AGENTICRAFT_API_KEY', required=True)
def secure_cli(api_key: str):
    """Secure CLI requiring API key."""
    user_info = auth.validate_key(api_key)
    if not user_info:
        click.echo("Invalid API key", err=True)
        sys.exit(1)
        
    # Continue with authenticated user
    click.echo(f"Authenticated as {user_info['user_id']}")
```

## 🚀 Quick Start Security Checklist

### Today (2-3 hours)
- [ ] Implement `QuickSandbox` for code isolation
- [ ] Add `SimpleAuth` with API keys
- [ ] Set up `AuditLogger` for compliance
- [ ] Add `RateLimiter` to prevent abuse
- [ ] Update all workflows to use secure wrappers

### This Week (2-3 days)
- [ ] Extract proper sandbox from agentic-framework
- [ ] Implement proper authentication (JWT, OAuth)
- [ ] Add encryption for sensitive data
- [ ] Set up monitoring and alerts
- [ ] Security testing and penetration testing

### Next Week (Full extraction)
- [ ] Complete A2A protocol extraction
- [ ] Implement MCP standards
- [ ] Add human-in-the-loop controls
- [ ] Deploy with full security stack

---

**Remember**: These are emergency patches. For production use, extract the proper security components from agentic-framework.
