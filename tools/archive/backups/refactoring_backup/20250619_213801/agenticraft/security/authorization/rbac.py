"""
Role-Based Access Control (RBAC) authorization for AgentiCraft.

This module implements RBAC with support for roles, permissions,
and hierarchical role inheritance.
"""
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..auth import UserContext, AuthorizationError


@dataclass
class Role:
    """Represents a role in the RBAC system."""
    name: str
    description: str = ""
    permissions: Set[str] = field(default_factory=set)
    parent_roles: Set[str] = field(default_factory=set)  # Role inheritance
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "parent_roles": list(self.parent_roles),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Role":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            permissions=set(data.get("permissions", [])),
            parent_roles=set(data.get("parent_roles", [])),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )


@dataclass
class Permission:
    """Represents a permission in the system."""
    name: str
    resource: str
    action: str
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, resource: str, action: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if this permission matches the requested resource and action.
        
        Supports wildcards (*) for resource and action matching.
        """
        # Check resource match (with wildcard support)
        if self.resource != "*" and not self._matches_pattern(self.resource, resource):
            return False
            
        # Check action match (with wildcard support)
        if self.action != "*" and not self._matches_pattern(self.action, action):
            return False
            
        # Check constraints if any
        if self.constraints and context:
            for key, expected_value in self.constraints.items():
                if key not in context or context[key] != expected_value:
                    return False
                    
        return True
        
    def _matches_pattern(self, pattern: str, value: str) -> bool:
        """Check if pattern matches value (supports * wildcard)."""
        if pattern == value:
            return True
            
        # Simple wildcard matching
        if "*" in pattern:
            # Convert pattern to regex-like matching
            parts = pattern.split("*")
            if len(parts) == 2:
                # Pattern like "users:*" or "*:read"
                if pattern.startswith("*"):
                    return value.endswith(parts[1])
                elif pattern.endswith("*"):
                    return value.startswith(parts[0])
                else:
                    # Pattern like "users:*:profile"
                    return value.startswith(parts[0]) and value.endswith(parts[1])
                    
        return False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
            "constraints": self.constraints
        }


class RBACAuthorizer:
    """Role-Based Access Control authorizer."""
    
    # Default roles and permissions
    DEFAULT_ROLES = {
        "admin": {
            "description": "Administrator with full access",
            "permissions": ["*:*"],  # All resources, all actions
            "parent_roles": []
        },
        "user": {
            "description": "Standard user",
            "permissions": [
                "agent:execute",
                "workflow:execute",
                "workflow:read",
                "agent:read"
            ],
            "parent_roles": []
        },
        "guest": {
            "description": "Guest with limited read access",
            "permissions": [
                "agent:read",
                "workflow:read"
            ],
            "parent_roles": []
        },
        "developer": {
            "description": "Developer with extended permissions",
            "permissions": [
                "agent:*",
                "workflow:*",
                "tool:*",
                "sandbox:execute"
            ],
            "parent_roles": ["user"]
        }
    }
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize RBAC authorizer.
        
        Args:
            storage_path: Path to store roles and permissions
        """
        if storage_path is None:
            storage_path = Path.home() / ".agenticraft" / "rbac.json"
            
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load roles and permissions
        self.roles: Dict[str, Role] = {}
        self.permissions: Dict[str, Permission] = {}
        self.user_roles: Dict[str, Set[str]] = {}  # user_id -> roles
        
        self._load_data()
        self._ensure_default_roles()
        
    def _load_data(self):
        """Load RBAC data from storage."""
        if not self.storage_path.exists():
            return
            
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
            # Load roles
            for role_name, role_data in data.get("roles", {}).items():
                self.roles[role_name] = Role.from_dict(role_data)
                
            # Load user roles
            self.user_roles = {
                user_id: set(roles)
                for user_id, roles in data.get("user_roles", {}).items()
            }
            
        except Exception as e:
            print(f"Error loading RBAC data: {e}")
            
    def _save_data(self):
        """Save RBAC data to storage."""
        data = {
            "roles": {
                name: role.to_dict()
                for name, role in self.roles.items()
            },
            "user_roles": {
                user_id: list(roles)
                for user_id, roles in self.user_roles.items()
            }
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _ensure_default_roles(self):
        """Ensure default roles exist."""
        for role_name, role_info in self.DEFAULT_ROLES.items():
            if role_name not in self.roles:
                self.create_role(
                    role_name,
                    role_info["description"],
                    role_info["permissions"],
                    role_info.get("parent_roles", [])
                )
                
    def create_role(
        self,
        name: str,
        description: str = "",
        permissions: Optional[List[str]] = None,
        parent_roles: Optional[List[str]] = None
    ) -> Role:
        """Create a new role."""
        role = Role(
            name=name,
            description=description,
            permissions=set(permissions or []),
            parent_roles=set(parent_roles or [])
        )
        
        self.roles[name] = role
        self._save_data()
        
        return role
        
    def assign_role(self, user_id: str, role_name: str):
        """Assign a role to a user."""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' does not exist")
            
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
            
        self.user_roles[user_id].add(role_name)
        self._save_data()
        
    def revoke_role(self, user_id: str, role_name: str):
        """Revoke a role from a user."""
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role_name)
            if not self.user_roles[user_id]:
                del self.user_roles[user_id]
            self._save_data()
            
    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get all roles for a user."""
        return self.user_roles.get(user_id, set())
        
    def get_role_permissions(self, role_name: str) -> Set[str]:
        """Get all permissions for a role (including inherited)."""
        if role_name not in self.roles:
            return set()
            
        role = self.roles[role_name]
        permissions = role.permissions.copy()
        
        # Add inherited permissions
        for parent_role_name in role.parent_roles:
            permissions.update(self.get_role_permissions(parent_role_name))
            
        return permissions
        
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user."""
        permissions = set()
        
        # Get permissions from all user roles
        for role_name in self.get_user_roles(user_id):
            permissions.update(self.get_role_permissions(role_name))
            
        return permissions
        
    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has permission for resource:action.
        
        Args:
            user_id: User to check
            resource: Resource being accessed (e.g., "agent", "workflow")
            action: Action being performed (e.g., "execute", "read", "write")
            context: Additional context for constraint checking
            
        Returns:
            True if user has permission
        """
        # Get user permissions
        user_permissions = self.get_user_permissions(user_id)
        
        # Check each permission
        for perm_string in user_permissions:
            # Parse permission string (format: "resource:action")
            if ":" in perm_string:
                perm_resource, perm_action = perm_string.split(":", 1)
                
                # Create permission object for matching
                perm = Permission(
                    name=perm_string,
                    resource=perm_resource,
                    action=perm_action
                )
                
                if perm.matches(resource, action, context):
                    return True
                    
        return False
        
    async def authorize(
        self,
        user_context: UserContext,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Authorize a user action, raising exception if not authorized.
        
        Args:
            user_context: Authenticated user context
            resource: Resource being accessed
            action: Action being performed
            context: Additional context
            
        Raises:
            AuthorizationError: If user is not authorized
        """
        # Check using user context roles first (faster)
        for role in user_context.roles:
            role_perms = self.get_role_permissions(role)
            for perm_string in role_perms:
                if ":" in perm_string:
                    perm_resource, perm_action = perm_string.split(":", 1)
                    perm = Permission(
                        name=perm_string,
                        resource=perm_resource,
                        action=perm_action
                    )
                    if perm.matches(resource, action, context):
                        return
                        
        # Also check stored user permissions
        if await self.check_permission(user_context.user_id, resource, action, context):
            return
            
        # Not authorized
        raise AuthorizationError(
            f"User '{user_context.username}' not authorized for {action} on {resource}"
        )
        
    def add_permission_to_role(self, role_name: str, permission: str):
        """Add a permission to a role."""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' does not exist")
            
        self.roles[role_name].permissions.add(permission)
        self._save_data()
        
    def remove_permission_from_role(self, role_name: str, permission: str):
        """Remove a permission from a role."""
        if role_name in self.roles:
            self.roles[role_name].permissions.discard(permission)
            self._save_data()
