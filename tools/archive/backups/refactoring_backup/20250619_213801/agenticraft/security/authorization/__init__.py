"""
Authorization module for AgentiCraft security.

This module provides:
- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC) - future
- Permission management
- Access control policies
"""

from .rbac import RBACAuthorizer, Role, Permission
from .permissions import (
    Resources,
    Actions,
    PermissionDefinition,
    PermissionChecker,
    STANDARD_PERMISSIONS,
    get_all_permissions,
    get_permissions_by_resource,
    get_permissions_by_risk_level
)

__all__ = [
    # RBAC
    "RBACAuthorizer",
    "Role",
    "Permission",
    
    # Permissions
    "Resources",
    "Actions", 
    "PermissionDefinition",
    "PermissionChecker",
    "STANDARD_PERMISSIONS",
    "get_all_permissions",
    "get_permissions_by_resource",
    "get_permissions_by_risk_level"
]
