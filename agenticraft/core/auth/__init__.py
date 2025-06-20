"""
Core authentication abstractions for AgentiCraft.

This module provides protocol-agnostic authentication mechanisms
that can be used by any protocol implementation.
"""

from .base import (
    AuthProvider,
    AuthConfig,
    AuthManager,
    AuthError,
    AuthenticationError,
    AuthorizationError,
    AuthType,
    get_auth_manager
)

# Import strategies module to ensure providers are registered
from . import strategies

from .strategies import (
    NoAuthProvider,
    APIKeyAuthProvider,
    BearerAuthProvider,
    HMACAuthProvider,
    JWTAuthProvider,
    BasicAuthProvider
)

# Import simple auth for workflows
from .simple import APIKeyAuth

# Compatibility aliases for existing code
JWTAuth = JWTAuthProvider

__all__ = [
    # Base classes
    "AuthProvider",
    "AuthConfig",
    "AuthManager",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "AuthType",
    "get_auth_manager",
    
    # Auth providers
    "NoAuthProvider",
    "APIKeyAuthProvider", 
    "BearerAuthProvider",
    "HMACAuthProvider",
    "JWTAuthProvider",
    "BasicAuthProvider",
    
    # Simple auth
    "APIKeyAuth",
    
    # Compatibility aliases
    "JWTAuth"
]
