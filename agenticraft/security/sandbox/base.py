"""Base sandbox implementation with common functionality."""

import asyncio
import logging
import time
from abc import ABC
from typing import Any, Callable, Dict, Optional

from ..abstractions.interfaces import ISandbox
from ..abstractions.types import SecurityContext, SecureResult, SandboxType

logger = logging.getLogger(__name__)


class BaseSandbox(ISandbox, ABC):
    """Base implementation for sandbox environments."""
    
    def __init__(self, sandbox_type: SandboxType):
        """Initialize base sandbox.
        
        Args:
            sandbox_type: Type of sandbox
        """
        self.sandbox_type = sandbox_type
        self._initialized = False
        self._cleanup_handlers = []
        
    async def initialize(self) -> None:
        """Initialize the sandbox environment."""
        if self._initialized:
            return
            
        logger.info(f"Initializing {self.sandbox_type.value} sandbox")
        
        try:
            await self._initialize_impl()
            self._initialized = True
            logger.info(f"{self.sandbox_type.value} sandbox initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize {self.sandbox_type.value} sandbox: {e}")
            raise
    
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization."""
        pass
    
    async def execute(
        self,
        operation: Callable,
        context: SecurityContext,
        *args,
        **kwargs
    ) -> SecureResult:
        """Execute an operation within the sandbox."""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Validate security context
            self._validate_context(context)
            
            # Apply resource limits
            await self._apply_resource_limits(context)
            
            # Execute operation
            result = await self._execute_impl(operation, context, *args, **kwargs)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            return SecureResult(
                success=True,
                result=result,
                execution_time_ms=execution_time_ms,
                sandbox_type=self.sandbox_type,
                resource_usage=await self._get_resource_usage()
            )
            
        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            return SecureResult(
                success=False,
                error=f"Operation timed out after {context.resource_limits.timeout_seconds}s",
                execution_time_ms=execution_time_ms,
                sandbox_type=self.sandbox_type
            )
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Sandbox execution failed: {e}")
            return SecureResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                sandbox_type=self.sandbox_type
            )
        finally:
            # Clean up resources
            await self._cleanup_execution()
    
    async def execute_code(
        self,
        code: str,
        context: SecurityContext,
        globals_dict: Optional[Dict[str, Any]] = None
    ) -> SecureResult:
        """Execute code string within the sandbox."""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Validate security context
            self._validate_context(context)
            
            # Apply resource limits
            await self._apply_resource_limits(context)
            
            # Execute code
            result = await self._execute_code_impl(code, context, globals_dict)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            return SecureResult(
                success=True,
                result=result,
                execution_time_ms=execution_time_ms,
                sandbox_type=self.sandbox_type,
                resource_usage=await self._get_resource_usage()
            )
            
        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            return SecureResult(
                success=False,
                error=f"Code execution timed out after {context.resource_limits.timeout_seconds}s",
                execution_time_ms=execution_time_ms,
                sandbox_type=self.sandbox_type
            )
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Sandbox code execution failed: {e}")
            return SecureResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                sandbox_type=self.sandbox_type
            )
        finally:
            # Clean up resources
            await self._cleanup_execution()
    
    def _validate_context(self, context: SecurityContext) -> None:
        """Validate security context."""
        if not context.permissions:
            raise ValueError("Security context must have at least one permission")
        
        if not context.has_permission("execute"):
            raise PermissionError("Security context lacks execute permission")
        
        if context.resource_limits.memory_mb < 10:
            raise ValueError("Memory limit must be at least 10MB")
        
        if context.resource_limits.timeout_seconds < 1:
            raise ValueError("Timeout must be at least 1 second")
    
    async def _apply_resource_limits(self, context: SecurityContext) -> None:
        """Apply resource limits to the sandbox."""
        # Implementation-specific
        pass
    
    async def _execute_impl(
        self,
        operation: Callable,
        context: SecurityContext,
        *args,
        **kwargs
    ) -> Any:
        """Implementation-specific execution."""
        raise NotImplementedError("Subclass must implement _execute_impl")
    
    async def _execute_code_impl(
        self,
        code: str,
        context: SecurityContext,
        globals_dict: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Implementation-specific code execution."""
        raise NotImplementedError("Subclass must implement _execute_code_impl")
    
    async def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        return {}
    
    async def _cleanup_execution(self) -> None:
        """Clean up after execution."""
        pass
    
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        logger.info(f"Cleaning up {self.sandbox_type.value} sandbox")
        
        # Run cleanup handlers
        for handler in self._cleanup_handlers:
            try:
                await handler()
            except Exception as e:
                logger.error(f"Cleanup handler failed: {e}")
        
        self._initialized = False
    
    def register_cleanup(self, handler: Callable) -> None:
        """Register a cleanup handler."""
        self._cleanup_handlers.append(handler)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(type={self.sandbox_type.value}, initialized={self._initialized})"
