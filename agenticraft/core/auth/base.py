"""
Base authentication interface for all protocols.

This module defines protocol-agnostic authentication abstractions
that can be used by MCP, A2A, and other protocols.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Types of authentication."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    HMAC = "hmac"
    JWT = "jwt"
    CUSTOM = "custom"


@dataclass
class AuthConfig:
    """Configuration for authentication."""
    type: AuthType
    credentials: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def none(cls) -> "AuthConfig":
        """Create no-auth configuration."""
        return cls(type=AuthType.NONE)
        
    @classmethod
    def api_key(cls, key: str, header: str = "X-API-Key") -> "AuthConfig":
        """Create API key configuration."""
        return cls(
            type=AuthType.API_KEY,
            credentials={"key": key},
            options={"header": header}
        )
        
    @classmethod
    def bearer(cls, token: str) -> "AuthConfig":
        """Create bearer token configuration."""
        return cls(
            type=AuthType.BEARER,
            credentials={"token": token}
        )
        
    @classmethod
    def basic(cls, username: str, password: str) -> "AuthConfig":
        """Create basic auth configuration."""
        return cls(
            type=AuthType.BASIC,
            credentials={"username": username, "password": password}
        )
        
    @classmethod
    def hmac(cls, key_id: str, secret_key: str, algorithm: str = "sha256") -> "AuthConfig":
        """Create HMAC configuration."""
        return cls(
            type=AuthType.HMAC,
            credentials={"key_id": key_id, "secret_key": secret_key},
            options={"algorithm": algorithm}
        )
        
    @classmethod
    def jwt(cls, token: str = None, secret: str = None, algorithm: str = "HS256") -> "AuthConfig":
        """Create JWT configuration."""
        return cls(
            type=AuthType.JWT,
            credentials={"token": token, "secret": secret},
            options={"algorithm": algorithm}
        )


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""
    
    def __init__(self, config: AuthConfig):
        """
        Initialize auth provider.
        
        Args:
            config: Authentication configuration
        """
        self.config = config
        
    @abstractmethod
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform authentication.
        
        Args:
            context: Authentication context (request, connection, etc.)
            
        Returns:
            Authentication result with credentials
        """
        pass
        
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for authentication.
        
        Returns:
            Dictionary of headers
        """
        pass
        
    @abstractmethod
    def get_connection_params(self) -> Dict[str, Any]:
        """
        Get connection parameters for authentication.
        
        Returns:
            Dictionary of connection parameters
        """
        pass
        
    async def validate(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate credentials.
        
        Args:
            credentials: Credentials to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Default implementation - subclasses can override
        return True
        
    async def refresh(self) -> Optional[Dict[str, Any]]:
        """
        Refresh credentials if supported.
        
        Returns:
            New credentials or None
        """
        # Default implementation - subclasses can override
        return None


class AuthManager:
    """Manages authentication providers and strategies."""
    
    def __init__(self):
        """Initialize auth manager."""
        self._providers: Dict[AuthType, type[AuthProvider]] = {}
        self._active_provider: Optional[AuthProvider] = None
        
    def register_provider(self, auth_type: AuthType, provider_class: type[AuthProvider]) -> None:
        """
        Register an authentication provider.
        
        Args:
            auth_type: Type of authentication
            provider_class: Provider class to register
        """
        self._providers[auth_type] = provider_class
        logger.info(f"Registered auth provider for type: {auth_type.value}")
        
    def set_auth(self, config: AuthConfig) -> None:
        """
        Set authentication configuration.
        
        Args:
            config: Authentication configuration
        """
        provider_class = self._providers.get(config.type)
        if not provider_class:
            raise ValueError(
                f"No auth provider registered for type: {config.type.value}. "
                f"Available: {[t.value for t in self._providers.keys()]}"
            )
            
        self._active_provider = provider_class(config)
        
    def get_provider(self) -> Optional[AuthProvider]:
        """Get active authentication provider."""
        return self._active_provider
        
    async def authenticate(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform authentication using active provider.
        
        Args:
            context: Authentication context
            
        Returns:
            Authentication result
        """
        if not self._active_provider:
            return {}
            
        return await self._active_provider.authenticate(context or {})
        
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self._active_provider:
            return {}
            
        return self._active_provider.get_headers()
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get authentication connection parameters."""
        if not self._active_provider:
            return {}
            
        return self._active_provider.get_connection_params()
        
    def create_provider(self, config: AuthConfig) -> AuthProvider:
        """
        Create auth provider without setting it as active.
        
        Args:
            config: Authentication configuration
            
        Returns:
            Authentication provider instance
        """
        provider_class = self._providers.get(config.type)
        if not provider_class:
            raise ValueError(f"No auth provider registered for type: {config.type.value}")
            
        return provider_class(config)


class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class AuthenticationError(AuthError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(AuthError):
    """Raised when authorization fails."""
    pass


# Global auth manager instance
_auth_manager = AuthManager()


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    return _auth_manager
