"""Sandbox module for secure code execution."""

from .base import BaseSandbox
from .manager import SandboxManager, get_sandbox_manager
from .process import ProcessSandbox, RestrictedPythonSandbox

# Lazy import for Docker
try:
    from .docker import DockerSandbox
    __all__ = [
        "BaseSandbox",
        "SandboxManager",
        "get_sandbox_manager",
        "ProcessSandbox",
        "RestrictedPythonSandbox",
        "DockerSandbox",
    ]
except ImportError:
    # Docker not available
    __all__ = [
        "BaseSandbox",
        "SandboxManager",
        "get_sandbox_manager",
        "ProcessSandbox",
        "RestrictedPythonSandbox",
    ]
