"""Process-based sandbox implementation for code isolation."""

import asyncio
import json
import logging
import multiprocessing
import os
import resource
import signal
import sys
import tempfile
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional

from ..abstractions.types import SecurityContext, SandboxType
from .base import BaseSandbox

logger = logging.getLogger(__name__)


def _set_resource_limits(limits: Dict[str, Any]) -> None:
    """Set resource limits for the process."""
    # Memory limit
    memory_bytes = limits.get("memory_mb", 512) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    
    # CPU time limit (soft limit)
    cpu_seconds = limits.get("timeout_seconds", 30)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 5))
    
    # Disable core dumps
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    
    # Limit file size
    max_file_size = limits.get("max_file_size_mb", 10) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_size, max_file_size))
    
    # Limit number of processes
    resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))


def _execute_in_process(
    code: str,
    globals_dict: Optional[Dict[str, Any]],
    limits: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute code in an isolated process."""
    try:
        # Set resource limits
        _set_resource_limits(limits)
        
        # Create restricted globals
        safe_globals = {
            "__builtins__": {
                # Allow only safe built-ins
                "abs": abs,
                "all": all,
                "any": any,
                "bool": bool,
                "dict": dict,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "int": int,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "print": print,
                "range": range,
                "round": round,
                "set": set,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "type": type,
                "zip": zip,
            }
        }
        
        # Add user-provided globals
        if globals_dict:
            safe_globals.update(globals_dict)
        
        # Execute code
        exec_globals = {}
        exec_locals = {}
        exec(code, safe_globals, exec_locals)
        
        # Extract serializable results
        result = {}
        for key, value in exec_locals.items():
            try:
                # Test if value is JSON serializable
                json.dumps(value)
                result[key] = value
            except (TypeError, ValueError):
                result[key] = str(value)
        
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


class ProcessSandbox(BaseSandbox):
    """Process-based sandbox using multiprocessing for isolation."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize process sandbox.
        
        Args:
            max_workers: Maximum number of worker processes
        """
        super().__init__(SandboxType.PROCESS)
        self.max_workers = max_workers
        self._executor: Optional[ProcessPoolExecutor] = None
    
    async def _initialize_impl(self) -> None:
        """Initialize the process pool."""
        self._executor = ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=self._worker_init
        )
        self.register_cleanup(self._shutdown_executor)
    
    def _worker_init(self) -> None:
        """Initialize worker process."""
        # Ignore SIGINT in workers
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    
    async def _shutdown_executor(self) -> None:
        """Shutdown the process pool."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
    
    async def _execute_code_impl(
        self,
        code: str,
        context: SecurityContext,
        globals_dict: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute code in an isolated process."""
        if not self._executor:
            raise RuntimeError("Sandbox not initialized")
        
        # Prepare limits
        limits = {
            "memory_mb": context.resource_limits.memory_mb,
            "timeout_seconds": context.resource_limits.timeout_seconds,
            "max_file_size_mb": context.resource_limits.max_file_size_mb,
        }
        
        # Execute in process with timeout
        loop = asyncio.get_event_loop()
        
        try:
            future = self._executor.submit(_execute_in_process, code, globals_dict, limits)
            result = await asyncio.wait_for(
                loop.run_in_executor(None, future.result),
                timeout=context.resource_limits.timeout_seconds
            )
            
            if result["success"]:
                return result["result"]
            else:
                raise RuntimeError(result["error"])
                
        except asyncio.TimeoutError:
            # Try to cancel the future
            future.cancel()
            raise
    
    async def _execute_impl(
        self,
        operation: Callable,
        context: SecurityContext,
        *args,
        **kwargs
    ) -> Any:
        """Execute a callable in an isolated process."""
        # Convert callable to code execution
        # This is a simplified version - in production, you'd serialize the callable
        code = f"""
import pickle
import base64

# Deserialize operation (simplified - assumes operation is pickleable)
# In production, use cloudpickle or dill for better serialization

result = operation(*args, **kwargs)
"""
        
        globals_dict = {
            "operation": operation,
            "args": args,
            "kwargs": kwargs
        }
        
        return await self._execute_code_impl(code, context, globals_dict)
    
    def is_available(self) -> bool:
        """Check if process sandbox is available."""
        # Check if we're on a Unix-like system with resource module
        try:
            import resource
            # Test setting a limit
            resource.getrlimit(resource.RLIMIT_AS)
            return True
        except (ImportError, AttributeError, OSError):
            return False
    
    async def _get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage information."""
        try:
            # Get current process info
            pid = os.getpid()
            
            # Read from /proc if available (Linux)
            if os.path.exists(f"/proc/{pid}/status"):
                with open(f"/proc/{pid}/status", "r") as f:
                    status = f.read()
                
                # Extract memory usage
                vm_size = 0
                for line in status.split("\n"):
                    if line.startswith("VmSize:"):
                        vm_size = int(line.split()[1]) // 1024  # Convert to MB
                        break
                
                return {
                    "memory_mb": vm_size,
                    "process_count": self.max_workers
                }
            else:
                # Fallback for non-Linux systems
                usage = resource.getrusage(resource.RUSAGE_SELF)
                return {
                    "memory_mb": usage.ru_maxrss // 1024,  # Convert to MB
                    "cpu_time": usage.ru_utime + usage.ru_stime
                }
        except Exception as e:
            logger.warning(f"Failed to get resource usage: {e}")
            return {}


class RestrictedPythonSandbox(BaseSandbox):
    """Restricted Python environment sandbox (lightweight alternative)."""
    
    def __init__(self):
        """Initialize restricted Python sandbox."""
        super().__init__(SandboxType.RESTRICTED)
        self._restricted_builtins = {
            # Safe built-ins only
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "print": self._safe_print,
            "range": range,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "type": type,
            "zip": zip,
        }
        self._output_buffer = []
    
    def _safe_print(self, *args, **kwargs) -> None:
        """Safe print function that captures output."""
        output = " ".join(str(arg) for arg in args)
        self._output_buffer.append(output)
    
    async def _execute_code_impl(
        self,
        code: str,
        context: SecurityContext,
        globals_dict: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute code in restricted environment."""
        # Clear output buffer
        self._output_buffer.clear()
        
        # Create restricted globals
        safe_globals = {
            "__builtins__": self._restricted_builtins.copy(),
            "__name__": "__restricted__",
            "__doc__": None,
        }
        
        # Add user globals if provided
        if globals_dict:
            # Filter out dangerous items
            for key, value in globals_dict.items():
                if not key.startswith("__") and self._is_safe_value(value):
                    safe_globals[key] = value
        
        # Execute with timeout using threading
        exec_locals = {}
        exception = None
        
        def execute_code():
            nonlocal exception
            try:
                exec(code, safe_globals, exec_locals)
            except Exception as e:
                exception = e
        
        # Run in thread with timeout
        thread = threading.Thread(target=execute_code)
        thread.daemon = True
        thread.start()
        thread.join(timeout=context.resource_limits.timeout_seconds)
        
        if thread.is_alive():
            # Timeout occurred
            raise asyncio.TimeoutError(f"Code execution timed out after {context.resource_limits.timeout_seconds}s")
        
        if exception:
            raise exception
        
        result = exec_locals
        
        # Include captured output
        if self._output_buffer:
            result["__output__"] = "\n".join(self._output_buffer)
        
        return result
    
    def _is_safe_value(self, value: Any) -> bool:
        """Check if a value is safe to include in globals."""
        # Allow basic types
        if isinstance(value, (int, float, str, bool, list, dict, tuple, set)):
            return True
        
        # Allow specific safe callables
        if callable(value) and hasattr(value, "__name__"):
            safe_callables = {"len", "str", "int", "float", "bool"}
            return value.__name__ in safe_callables
        
        return False
    
    async def _execute_impl(
        self,
        operation: Callable,
        context: SecurityContext,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation in restricted environment."""
        # For restricted sandbox, we can't execute arbitrary callables safely
        # This would need to be implemented based on specific use cases
        raise NotImplementedError(
            "RestrictedPythonSandbox does not support arbitrary callable execution"
        )
    
    def is_available(self) -> bool:
        """Restricted Python sandbox is always available."""
        return True
