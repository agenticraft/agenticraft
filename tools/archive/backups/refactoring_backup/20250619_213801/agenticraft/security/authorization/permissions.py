"""
Permissions management for AgentiCraft security.

This module defines standard permissions and provides utilities
for permission checking and management.
"""
from enum import Enum
from typing import Set, List, Dict, Any
from dataclasses import dataclass


class Resources(Enum):
    """Standard resources in AgentiCraft."""
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    SANDBOX = "sandbox"
    MEMORY = "memory"
    MODEL = "model"
    PLUGIN = "plugin"
    TEMPLATE = "template"
    CONFIG = "config"
    AUDIT = "audit"
    USER = "user"
    ROLE = "role"
    ALL = "*"


class Actions(Enum):
    """Standard actions in AgentiCraft."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LIST = "list"
    MANAGE = "manage"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    ALL = "*"


@dataclass
class PermissionDefinition:
    """Definition of a permission."""
    name: str
    resource: Resources
    action: Actions
    description: str
    risk_level: str = "low"  # low, medium, high, critical
    requires_audit: bool = False
    
    def to_string(self) -> str:
        """Convert to permission string format."""
        return f"{self.resource.value}:{self.action.value}"
        
    @classmethod
    def from_string(cls, perm_string: str) -> "PermissionDefinition":
        """Create from permission string."""
        resource_str, action_str = perm_string.split(":", 1)
        
        # Find matching enums
        resource = Resources(resource_str) if resource_str != "*" else Resources.ALL
        action = Actions(action_str) if action_str != "*" else Actions.ALL
        
        return cls(
            name=perm_string,
            resource=resource,
            action=action,
            description=f"{action_str} {resource_str}"
        )


# Standard permission definitions
STANDARD_PERMISSIONS = [
    # Agent permissions
    PermissionDefinition(
        "agent:create",
        Resources.AGENT,
        Actions.CREATE,
        "Create new agents",
        risk_level="medium"
    ),
    PermissionDefinition(
        "agent:read",
        Resources.AGENT,
        Actions.READ,
        "View agent details",
        risk_level="low"
    ),
    PermissionDefinition(
        "agent:execute",
        Resources.AGENT,
        Actions.EXECUTE,
        "Execute agent tasks",
        risk_level="high",
        requires_audit=True
    ),
    PermissionDefinition(
        "agent:delete",
        Resources.AGENT,
        Actions.DELETE,
        "Delete agents",
        risk_level="medium"
    ),
    
    # Workflow permissions
    PermissionDefinition(
        "workflow:create",
        Resources.WORKFLOW,
        Actions.CREATE,
        "Create new workflows",
        risk_level="medium"
    ),
    PermissionDefinition(
        "workflow:execute",
        Resources.WORKFLOW,
        Actions.EXECUTE,
        "Execute workflows",
        risk_level="high",
        requires_audit=True
    ),
    PermissionDefinition(
        "workflow:share",
        Resources.WORKFLOW,
        Actions.SHARE,
        "Share workflows with others",
        risk_level="medium"
    ),
    
    # Sandbox permissions
    PermissionDefinition(
        "sandbox:execute",
        Resources.SANDBOX,
        Actions.EXECUTE,
        "Execute code in sandbox",
        risk_level="critical",
        requires_audit=True
    ),
    
    # Tool permissions
    PermissionDefinition(
        "tool:execute",
        Resources.TOOL,
        Actions.EXECUTE,
        "Execute external tools",
        risk_level="high",
        requires_audit=True
    ),
    PermissionDefinition(
        "tool:manage",
        Resources.TOOL,
        Actions.MANAGE,
        "Add/remove tools",
        risk_level="high"
    ),
    
    # Admin permissions
    PermissionDefinition(
        "user:manage",
        Resources.USER,
        Actions.MANAGE,
        "Manage users",
        risk_level="critical"
    ),
    PermissionDefinition(
        "role:manage",
        Resources.ROLE,
        Actions.MANAGE,
        "Manage roles and permissions",
        risk_level="critical"
    ),
    PermissionDefinition(
        "audit:read",
        Resources.AUDIT,
        Actions.READ,
        "View audit logs",
        risk_level="high"
    ),
    PermissionDefinition(
        "config:manage",
        Resources.CONFIG,
        Actions.MANAGE,
        "Manage system configuration",
        risk_level="critical"
    )
]


class PermissionChecker:
    """Utility for checking permissions."""
    
    @staticmethod
    def format_permission(resource: str, action: str) -> str:
        """Format resource and action into permission string."""
        return f"{resource}:{action}"
        
    @staticmethod
    def parse_permission(permission: str) -> tuple[str, str]:
        """Parse permission string into resource and action."""
        parts = permission.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid permission format: {permission}")
        return parts[0], parts[1]
        
    @staticmethod
    def is_admin_permission(permission: str) -> bool:
        """Check if permission is an admin-level permission."""
        if permission == "*:*":
            return True
            
        resource, action = PermissionChecker.parse_permission(permission)
        
        # Admin resources
        admin_resources = {
            Resources.USER.value,
            Resources.ROLE.value,
            Resources.CONFIG.value,
            Resources.AUDIT.value
        }
        
        # Critical actions
        critical_actions = {
            Actions.MANAGE.value,
            Actions.DELETE.value
        }
        
        return resource in admin_resources or action in critical_actions
        
    @staticmethod
    def get_required_permissions(operation: str) -> List[str]:
        """
        Get required permissions for a high-level operation.
        
        Args:
            operation: Operation name (e.g., "create_agent", "run_workflow")
            
        Returns:
            List of required permission strings
        """
        permission_map = {
            # Agent operations
            "create_agent": ["agent:create"],
            "delete_agent": ["agent:delete"],
            "run_agent": ["agent:execute", "sandbox:execute"],
            "view_agent": ["agent:read"],
            
            # Workflow operations
            "create_workflow": ["workflow:create"],
            "run_workflow": ["workflow:execute", "agent:execute"],
            "share_workflow": ["workflow:share"],
            "delete_workflow": ["workflow:delete"],
            
            # Tool operations
            "add_tool": ["tool:manage"],
            "use_tool": ["tool:execute"],
            
            # Admin operations
            "manage_users": ["user:manage", "role:manage"],
            "view_audit_logs": ["audit:read"],
            "change_config": ["config:manage"]
        }
        
        return permission_map.get(operation, [])
        
    @staticmethod
    def get_risk_level(permission: str) -> str:
        """Get risk level for a permission."""
        # Find matching standard permission
        for perm_def in STANDARD_PERMISSIONS:
            if perm_def.to_string() == permission:
                return perm_def.risk_level
                
        # Default risk levels
        if permission == "*:*":
            return "critical"
        elif permission.endswith(":execute") or permission.endswith(":manage"):
            return "high"
        elif permission.endswith(":create") or permission.endswith(":delete"):
            return "medium"
        else:
            return "low"
            
    @staticmethod
    def requires_audit(permission: str) -> bool:
        """Check if permission requires audit logging."""
        # Find matching standard permission
        for perm_def in STANDARD_PERMISSIONS:
            if perm_def.to_string() == permission:
                return perm_def.requires_audit
                
        # Default audit requirements
        risk_level = PermissionChecker.get_risk_level(permission)
        return risk_level in ["high", "critical"]


def get_all_permissions() -> List[str]:
    """Get list of all standard permissions."""
    return [perm.to_string() for perm in STANDARD_PERMISSIONS]


def get_permissions_by_resource(resource: Resources) -> List[str]:
    """Get all permissions for a specific resource."""
    return [
        perm.to_string()
        for perm in STANDARD_PERMISSIONS
        if perm.resource == resource
    ]


def get_permissions_by_risk_level(risk_level: str) -> List[str]:
    """Get all permissions with specific risk level."""
    return [
        perm.to_string()
        for perm in STANDARD_PERMISSIONS
        if perm.risk_level == risk_level
    ]
