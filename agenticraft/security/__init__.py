"""Security module for AgentiCraft.

This module provides comprehensive security features including:
- Sandboxed execution environments
- Authentication and authorization  
- Role-based access control (RBAC)
- Audit logging and compliance
- Resource limits and isolation
"""

# Sandbox components
from .abstractions.interfaces import ISandbox
from .abstractions.types import SecurityContext, SandboxType, SecureResult, UserContext
from .sandbox.manager import SandboxManager

# Security exceptions
from .exceptions import (
    SecurityException,
    SandboxError,
    ResourceLimitExceeded,
    PermissionDenied
)

# Import auth exceptions from core
from agenticraft.core.auth import (
    AuthenticationError,
    AuthorizationError
)

# Authentication components - now in core.auth
from agenticraft.core.auth import (
    AuthProvider as IAuthProvider,
    AuthConfig,
    AuthType as AuthMethod,
    APIKeyAuthProvider,
    JWTAuthProvider as JWTAuth,
    APIKeyAuth
)

# Authorization components - TO BE IMPLEMENTED
# from agenticraft.core.auth import (
#     RBACAuthorizer,
#     Role,
#     Permission,
#     Resources,
#     Actions,
#     PermissionDefinition,
#     PermissionChecker,
#     get_all_permissions
# )

# Audit logging
from .audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity
)

# Security middleware
from .middleware import SecurityMiddleware, security

__all__ = [
    # Sandbox
    "ISandbox",
    "SecurityContext",
    "SandboxType", 
    "SecureResult",
    "SandboxManager",
    "UserContext",
    
    # Authentication (from core.auth)
    "AuthMethod",
    "AuthConfig",
    "IAuthProvider",
    "AuthenticationError",
    "AuthorizationError",
    "APIKeyAuthProvider",
    "JWTAuth",
    "APIKeyAuth",
    
    # Authorization - TO BE IMPLEMENTED
    # "RBACAuthorizer",
    # "Role",
    # "Permission",
    # "Resources",
    # "Actions",
    # "PermissionDefinition", 
    # "PermissionChecker",
    # "get_all_permissions",
    
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    
    # Middleware
    "SecurityMiddleware",
    "security",
    
    # Exceptions
    "SecurityException",
    "AuthenticationError",
    "AuthorizationError",
    "SandboxError",
    "ResourceLimitExceeded",
    "PermissionDenied"
]
