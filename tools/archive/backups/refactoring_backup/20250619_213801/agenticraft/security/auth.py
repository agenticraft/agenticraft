"""
Base authentication module for AgentiCraft.

This module provides the core authentication abstractions and interfaces
used throughout the security system.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class AuthMethod(Enum):
    """Supported authentication methods."""
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH = "oauth"
    NONE = "none"


@dataclass
class AuthToken:
    """Represents an authentication token."""
    value: str
    method: AuthMethod
    issued_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class UserContext:
    """Represents authenticated user context."""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    auth_method: AuthMethod = AuthMethod.NONE
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    authenticated_at: datetime = field(default_factory=datetime.now)
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
        
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "permissions": self.permissions,
            "attributes": self.attributes,
            "auth_method": self.auth_method.value,
            "session_id": self.session_id,
            "authenticated_at": self.authenticated_at.isoformat()
        }


class IAuthProvider(ABC):
    """Interface for authentication providers."""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[UserContext]:
        """
        Authenticate user with provided credentials.
        
        Args:
            credentials: Provider-specific credentials
            
        Returns:
            UserContext if authentication successful, None otherwise
        """
        pass
        
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[UserContext]:
        """
        Validate an existing authentication token.
        
        Args:
            token: Authentication token to validate
            
        Returns:
            UserContext if token is valid, None otherwise
        """
        pass
        
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke an authentication token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revocation successful
        """
        pass
        
    @abstractmethod
    def get_auth_method(self) -> AuthMethod:
        """Get the authentication method this provider handles."""
        pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""
    pass
