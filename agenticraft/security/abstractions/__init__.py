"""Security abstractions module."""

from .interfaces import ISandbox, IAuthenticator, IAuthorizer
from .types import (
    SecurityContext,
    SandboxType,
    SecureResult,
    ResourceLimits,
    PermissionLevel,
    AuditEntry
)

__all__ = [
    # Interfaces
    "ISandbox",
    "IAuthenticator", 
    "IAuthorizer",
    # Types
    "SecurityContext",
    "SandboxType",
    "SecureResult",
    "ResourceLimits",
    "PermissionLevel",
    "AuditEntry",
]
