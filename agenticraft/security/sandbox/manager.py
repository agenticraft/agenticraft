"""Sandbox manager for AgentiCraft."""

import asyncio
import logging
from typing import Dict, Optional, Type

from ..abstractions.interfaces import ISandbox
from ..abstractions.types import SandboxType
from .base import BaseSandbox
from .process import ProcessSandbox, RestrictedPythonSandbox

logger = logging.getLogger(__name__)

# Lazy import for Docker
_docker_sandbox_class: Optional[Type[BaseSandbox]] = None


def _get_docker_sandbox():
    """Lazy load Docker sandbox."""
    global _docker_sandbox_class
    if _docker_sandbox_class is None:
        try:
            from .docker import DockerSandbox
            _docker_sandbox_class = DockerSandbox
        except ImportError:
            logger.warning("Docker sandbox not available - Docker SDK not installed")
            _docker_sandbox_class = None
    return _docker_sandbox_class


class SandboxManager:
    """Manages sandbox instances and lifecycle."""
    
    def __init__(self):
        """Initialize sandbox manager."""
        self._sandboxes: Dict[SandboxType, ISandbox] = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the sandbox manager.
        
        This is a no-op for the current implementation but provided
        for API compatibility.
        """
        pass
    
    async def get_sandbox(self, sandbox_type: SandboxType = SandboxType.RESTRICTED) -> ISandbox:
        """Get or create a sandbox instance."""
        async with self._lock:
            if sandbox_type not in self._sandboxes:
                sandbox = await self._create_sandbox(sandbox_type)
                await sandbox.initialize()
                self._sandboxes[sandbox_type] = sandbox
            
            return self._sandboxes[sandbox_type]
    
    async def _create_sandbox(self, sandbox_type: SandboxType) -> ISandbox:
        """Create a new sandbox instance."""
        if sandbox_type == SandboxType.PROCESS:
            return ProcessSandbox()
        elif sandbox_type == SandboxType.DOCKER:
            DockerSandbox = _get_docker_sandbox()
            if DockerSandbox is None:
                logger.warning("Docker sandbox requested but not available, falling back to process sandbox")
                return ProcessSandbox()
            sandbox = DockerSandbox()
            if not sandbox.is_available():
                logger.warning("Docker not available on system, falling back to process sandbox")
                return ProcessSandbox()
            return sandbox
        elif sandbox_type == SandboxType.RESTRICTED:
            return RestrictedPythonSandbox()
        else:
            raise ValueError(f"Unknown sandbox type: {sandbox_type}")
    
    async def cleanup(self):
        """Clean up all sandboxes."""
        async with self._lock:
            for sandbox in self._sandboxes.values():
                try:
                    await sandbox.cleanup()
                except Exception as e:
                    logger.error(f"Failed to cleanup sandbox: {e}")
            
            self._sandboxes.clear()
    
    def get_available_types(self) -> list[SandboxType]:
        """Get list of available sandbox types."""
        available = [SandboxType.RESTRICTED, SandboxType.PROCESS]
        
        # Check if Docker is available
        DockerSandbox = _get_docker_sandbox()
        if DockerSandbox and DockerSandbox().is_available():
            available.append(SandboxType.DOCKER)
        
        return available


# Global sandbox manager instance
_global_manager: Optional[SandboxManager] = None


def get_sandbox_manager() -> SandboxManager:
    """Get the global sandbox manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = SandboxManager()
    return _global_manager