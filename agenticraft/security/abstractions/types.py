"""Security type definitions."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class SandboxType(Enum):
    """Types of sandbox environments."""
    PROCESS = "process"  # Separate process isolation
    DOCKER = "docker"    # Docker container isolation
    PYODIDE = "pyodide"  # Browser-based isolation
    RESTRICTED = "restricted"  # Restricted Python environment


class PermissionLevel(Enum):
    """Permission levels for operations."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class UserContext:
    """Context for authenticated users."""
    user_id: str
    username: Optional[str] = None
    roles: List[str] = None
    permissions: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.permissions is None:
            self.permissions = []
        if self.metadata is None:
            self.metadata = {}
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions


@dataclass
class ResourceLimits:
    """Resource limits for sandboxed execution."""
    memory_mb: int = 512
    cpu_percent: float = 50.0
    timeout_seconds: int = 30
    max_file_size_mb: int = 10
    network_access: bool = False
    filesystem_access: bool = False
    network_disabled: bool = True  # For docker compatibility
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "timeout_seconds": self.timeout_seconds,
            "max_file_size_mb": self.max_file_size_mb,
            "network_access": self.network_access,
            "filesystem_access": self.filesystem_access,
            "network_disabled": self.network_disabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceLimits":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SecurityContext:
    """Security context for operations."""
    user_id: str = "system"
    permissions: List[str] = None
    resource_limits: Union[ResourceLimits, Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        
        # Convert dict to ResourceLimits if needed
        if isinstance(self.resource_limits, dict):
            self.resource_limits = ResourceLimits.from_dict(self.resource_limits)
        elif self.resource_limits is None:
            self.resource_limits = ResourceLimits()
        
        if self.metadata is None:
            self.metadata = {}
    
    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission."""
        return permission in self.permissions or "admin" in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "permissions": self.permissions,
            "resource_limits": self.resource_limits.to_dict() if isinstance(self.resource_limits, ResourceLimits) else self.resource_limits,
            "metadata": self.metadata
        }


@dataclass
class SecureResult:
    """Result from secure execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    resource_usage: Dict[str, Any] = None
    sandbox_type: Optional[SandboxType] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.resource_usage is None:
            self.resource_usage = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "resource_usage": self.resource_usage,
            "sandbox_type": self.sandbox_type.value if self.sandbox_type else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class AuditEntry:
    """Audit log entry."""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    success: bool
    details: Dict[str, Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "success": self.success,
            "details": self.details,
            "error": self.error
        }
