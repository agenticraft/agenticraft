"""Security abstractions and interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Dict
from .types import SecurityContext, SecureResult


class ISandbox(ABC):
    """Abstract interface for sandbox implementations."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the sandbox environment."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        operation: Callable,
        context: SecurityContext,
        *args,
        **kwargs
    ) -> SecureResult:
        """Execute an operation within the sandbox.
        
        Args:
            operation: The operation to execute
            context: Security context with permissions and limits
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            SecureResult with execution outcome
        """
        pass
    
    @abstractmethod
    async def execute_code(
        self,
        code: str,
        context: SecurityContext,
        globals_dict: Optional[Dict[str, Any]] = None
    ) -> SecureResult:
        """Execute code string within the sandbox.
        
        Args:
            code: Python code to execute
            context: Security context with permissions and limits
            globals_dict: Optional globals dictionary
            
        Returns:
            SecureResult with execution outcome
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this sandbox type is available on the system."""
        pass


class IAuthenticator(ABC):
    """Abstract interface for authentication providers."""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate credentials and return user context."""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a token and return user context."""
        pass


class IAuthorizer(ABC):
    """Abstract interface for authorization providers."""
    
    @abstractmethod
    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has permission for action on resource."""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> list[str]:
        """Get all permissions for a user."""
        pass
