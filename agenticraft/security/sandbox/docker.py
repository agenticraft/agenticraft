"""Docker-based sandbox implementation for AgentiCraft."""

import asyncio
import json
import logging
import tempfile
from typing import Any, Callable, Dict, Optional
import os
import shutil

try:
    import docker
    from docker.errors import DockerException, ImageNotFound
    HAS_DOCKER = True
except ImportError:
    HAS_DOCKER = False
    DockerException = Exception
    ImageNotFound = Exception

from ..abstractions.types import SecurityContext, SandboxType
from .base import BaseSandbox

logger = logging.getLogger(__name__)


class DockerSandbox(BaseSandbox):
    """Docker container-based isolation sandbox."""

    def __init__(self, base_image: str = "python:3.11-slim"):
        """Initialize Docker sandbox."""
        super().__init__(SandboxType.DOCKER)
        self.client: Optional[Any] = None
        self.base_image = base_image
        self.container_prefix = "agenticraft-sandbox-"
        self._temp_dir = None

    async def _initialize_impl(self) -> None:
        """Initialize Docker client and prepare base image."""
        if not HAS_DOCKER:
            raise RuntimeError(
                "Docker SDK not installed. Install with: pip install docker"
            )
        
        try:
            self.client = docker.from_env()
            
            # Test Docker connection
            self.client.ping()
            
            # Pull base image if not present
            try:
                self.client.images.get(self.base_image)
                logger.info(f"Docker image {self.base_image} already present")
            except ImageNotFound:
                logger.info(f"Pulling Docker image: {self.base_image}")
                self.client.images.pull(self.base_image)
            
            # Create temp directory for scripts
            self._temp_dir = tempfile.mkdtemp(prefix="agenticraft-docker-")
            
        except DockerException as e:
            raise RuntimeError(f"Failed to initialize Docker: {e}")

    async def _execute_code_impl(
        self,
        code: str,
        context: SecurityContext,
        globals_dict: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute code in Docker container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        container = None
        script_path = None
        
        try:
            # Create execution script
            script_path = os.path.join(self._temp_dir, f"script_{id(code)}.py")
            
            # Prepare the execution wrapper
            wrapper_code = self._create_wrapper_script(code, globals_dict)
            
            with open(script_path, 'w') as f:
                f.write(wrapper_code)
            
            # Container configuration
            container_config = {
                "image": self.base_image,
                "command": ["python", "/app/script.py"],
                "detach": True,
                "mem_limit": f"{context.resource_limits.memory_mb}m",
                "cpus": str(context.resource_limits.cpu_percent / 100),
                "network_mode": "none" if context.resource_limits.network_disabled else "bridge",
                "volumes": {
                    script_path: {"bind": "/app/script.py", "mode": "ro"}
                },
                "environment": {
                    "PYTHONUNBUFFERED": "1",
                    "AGENTICRAFT_SANDBOX": "1",
                },
                "name": f"{self.container_prefix}{os.getpid()}-{id(code)}",
                "remove": False,  # We'll remove manually after getting logs
            }
            
            # Create and start container
            container = self.client.containers.run(**container_config)
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=context.resource_limits.timeout_seconds)
            except Exception:
                container.kill()
                raise asyncio.TimeoutError(
                    f"Container execution exceeded timeout of {context.resource_limits.timeout_seconds}s"
                )
            
            # Get output
            logs = container.logs(stdout=True, stderr=True)
            output = logs.decode('utf-8')
            
            # Parse result
            if result["StatusCode"] == 0:
                return self._parse_output(output)
            else:
                # Extract error from output
                error_msg = self._extract_error(output)
                raise RuntimeError(f"Container execution failed: {error_msg}")
                
        finally:
            # Cleanup
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")
            
            # Remove script file
            if script_path and os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception as e:
                    logger.warning(f"Failed to remove script file: {e}")

    def _create_wrapper_script(self, code: str, globals_dict: Optional[Dict[str, Any]]) -> str:
        """Create wrapper script for container execution."""
        # Serialize globals safely
        safe_globals = self._serialize_globals(globals_dict or {})
        
        # Escape the code properly before using in f-string
        escaped_code = code.replace('\\', '\\\\').replace('"', '\\"')
        
        wrapper = f'''
import json
import sys
import traceback

# Result markers
RESULT_MARKER = "===AGENTICRAFT_RESULT==="
ERROR_MARKER = "===AGENTICRAFT_ERROR==="

# Safe globals
safe_globals = {safe_globals}

# Restricted builtins
safe_builtins = {{
    "abs": abs, "all": all, "any": any, "bool": bool,
    "dict": dict, "enumerate": enumerate, "filter": filter,
    "float": float, "int": int, "len": len, "list": list,
    "map": map, "max": max, "min": min, "print": print,
    "range": range, "round": round, "set": set, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "type": type, "zip": zip,
}}

safe_globals["__builtins__"] = safe_builtins

try:
    # Execute user code
    exec_locals = {{}}
    exec("""{escaped_code}""", safe_globals, exec_locals)
    
    # Serialize results
    result = {{}}
    for key, value in exec_locals.items():
        if not key.startswith("_"):
            try:
                json.dumps(value)  # Test if serializable
                result[key] = value
            except:
                result[key] = str(value)
    
    print(RESULT_MARKER)
    print(json.dumps(result))
    
except Exception as e:
    print(ERROR_MARKER)
    print(json.dumps({{
        "error": str(e),
        "traceback": traceback.format_exc()
    }}))
    sys.exit(1)
'''
        return wrapper

    def _serialize_globals(self, globals_dict: Dict[str, Any]) -> str:
        """Safely serialize globals for container."""
        safe_globals = {}
        
        for key, value in globals_dict.items():
            if key.startswith("__"):
                continue
                
            # Only allow safe types
            if isinstance(value, (int, float, str, bool, list, dict, tuple)):
                try:
                    json.dumps(value)  # Test serializability
                    safe_globals[key] = value
                except:
                    logger.warning(f"Skipping non-serializable global: {key}")
            
        return repr(safe_globals)

    def _parse_output(self, output: str) -> Any:
        """Parse container output to extract result."""
        lines = output.split('\n')
        
        # Look for result marker
        for i, line in enumerate(lines):
            if line.strip() == "===AGENTICRAFT_RESULT===":
                if i + 1 < len(lines):
                    try:
                        return json.loads(lines[i + 1])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse result: {lines[i + 1]}")
        
        # No result found
        return {"_output": output}

    def _extract_error(self, output: str) -> str:
        """Extract error message from container output."""
        lines = output.split('\n')
        
        # Look for error marker
        for i, line in enumerate(lines):
            if line.strip() == "===AGENTICRAFT_ERROR===":
                if i + 1 < len(lines):
                    try:
                        error_data = json.loads(lines[i + 1])
                        return error_data.get("error", "Unknown error")
                    except json.JSONDecodeError:
                        pass
        
        # Return raw output if no structured error
        return output.strip() or "Unknown error"

    async def _execute_impl(
        self,
        operation: Callable,
        context: SecurityContext,
        *args,
        **kwargs
    ) -> Any:
        """Execute a callable in Docker container."""
        # For Docker sandbox, we convert callable to code execution
        # This is a simplified approach - in production use cloudpickle
        import inspect
        
        try:
            source = inspect.getsource(operation)
            
            # Create execution code
            code = f"""
{source}

# Execute the operation
result = {operation.__name__}(*{repr(args)}, **{repr(kwargs)})
"""
            
            return await self._execute_code_impl(code, context)
            
        except Exception as e:
            logger.error(f"Failed to extract source for operation: {e}")
            raise RuntimeError(
                "Docker sandbox requires source code extraction. "
                "Consider using process sandbox for this operation."
            )

    async def cleanup(self) -> None:
        """Clean up Docker resources."""
        await super().cleanup()
        
        if self.client:
            # Clean up any remaining containers
            try:
                containers = self.client.containers.list(
                    all=True,
                    filters={"name": self.container_prefix}
                )
                for container in containers:
                    container.remove(force=True)
            except Exception as e:
                logger.error(f"Failed to clean up containers: {e}")
            
            self.client.close()
            self.client = None
        
        # Clean up temp directory
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.error(f"Failed to clean up temp directory: {e}")

    def is_available(self) -> bool:
        """Check if Docker is available."""
        if not HAS_DOCKER:
            return False
        
        try:
            client = docker.from_env()
            client.ping()
            client.close()
            return True
        except Exception:
            return False

    async def _get_resource_usage(self) -> Dict[str, Any]:
        """Get Docker resource usage."""
        if not self.client:
            return {}
        
        try:
            # Get Docker system info
            info = self.client.info()
            
            return {
                "containers_running": info.get("ContainersRunning", 0),
                "images": len(self.client.images.list()),
                "docker_version": info.get("ServerVersion", "unknown"),
            }
        except Exception as e:
            logger.warning(f"Failed to get Docker stats: {e}")
            return {}
