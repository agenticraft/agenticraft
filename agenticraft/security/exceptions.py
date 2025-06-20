"""Security-related exceptions."""


class SecurityException(Exception):
    """Base exception for security-related errors."""
    pass


# Authentication and Authorization errors are now in core.auth
# Use: from agenticraft.core.auth import AuthenticationError, AuthorizationError


class SandboxError(SecurityException):
    """Raised when sandbox operations fail."""
    pass


class ResourceLimitExceeded(SecurityException):
    """Raised when resource limits are exceeded."""
    pass


class PermissionDenied(SecurityException):
    """Raised when permission is denied for an operation."""
    pass
