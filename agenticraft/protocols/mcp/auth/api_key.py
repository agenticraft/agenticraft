"""API Key authentication for AgentiCraft MCP protocol.

Simple API key authentication extracted from Agentic Framework,
focused on the Customer Service Desk use case.
"""

import logging
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class APIKeyAuth:
    """Simple API key authentication for customer service.
    
    This authenticator manages API keys for different clients/services
    that can interact with the customer service system.
    
    Args:
        valid_keys: Optional dict mapping API keys to client identities
    """
    
    def __init__(self, valid_keys: Optional[Dict[str, str]] = None):
        """Initialize with optional pre-configured keys."""
        self.valid_keys = valid_keys or {}
        self.key_metadata: Dict[str, Dict] = {}  # Store additional key info
        
        logger.info(f"Initialized APIKeyAuth with {len(self.valid_keys)} keys")
    
    def add_key(
        self,
        api_key: str,
        client_id: str,
        client_name: Optional[str] = None,
        permissions: Optional[Set[str]] = None
    ) -> bool:
        """Add a new API key.
        
        Args:
            api_key: The API key to add
            client_id: Unique client identifier
            client_name: Human-readable client name
            permissions: Set of permissions for this key
            
        Returns:
            True if key was added successfully
        """
        if api_key in self.valid_keys:
            logger.warning(f"API key already exists for client {self.valid_keys[api_key]}")
            return False
        
        self.valid_keys[api_key] = client_id
        self.key_metadata[api_key] = {
            "client_id": client_id,
            "client_name": client_name or client_id,
            "permissions": permissions or {"customer_service"},
            "created_at": None,  # Would use datetime.utcnow() in production
            "last_used": None
        }
        
        logger.info(f"Added API key for client '{client_name or client_id}'")
        return True
    
    def remove_key(self, api_key: str) -> bool:
        """Remove an API key.
        
        Args:
            api_key: The key to remove
            
        Returns:
            True if key was removed
        """
        if api_key in self.valid_keys:
            client_id = self.valid_keys[api_key]
            del self.valid_keys[api_key]
            self.key_metadata.pop(api_key, None)
            logger.info(f"Removed API key for client '{client_id}'")
            return True
        return False
    
    def authenticate(self, api_key: str) -> Optional[str]:
        """Authenticate with API key.
        
        Args:
            api_key: The API key to verify
            
        Returns:
            Client ID if authenticated, None otherwise
        """
        client_id = self.valid_keys.get(api_key)
        
        if client_id:
            # Update last used (in production)
            if api_key in self.key_metadata:
                # self.key_metadata[api_key]["last_used"] = datetime.utcnow()
                pass
            
            logger.debug(f"Authenticated client '{client_id}'")
            return client_id
        
        logger.warning("Authentication failed: Invalid API key")
        return None
    
    def check_permission(
        self,
        api_key: str,
        permission: str
    ) -> bool:
        """Check if API key has specific permission.
        
        Args:
            api_key: The API key
            permission: Permission to check
            
        Returns:
            True if key has permission
        """
        if api_key not in self.valid_keys:
            return False
        
        metadata = self.key_metadata.get(api_key, {})
        permissions = metadata.get("permissions", set())
        
        return permission in permissions or "*" in permissions
    
    def get_client_info(self, api_key: str) -> Optional[Dict]:
        """Get information about a client.
        
        Args:
            api_key: The API key
            
        Returns:
            Client information or None
        """
        if api_key not in self.valid_keys:
            return None
        
        return self.key_metadata.get(api_key, {
            "client_id": self.valid_keys[api_key],
            "client_name": self.valid_keys[api_key]
        })
    
    def list_clients(self) -> Dict[str, Dict]:
        """List all registered clients.
        
        Returns:
            Dict mapping client IDs to their info
        """
        clients = {}
        
        for api_key, client_id in self.valid_keys.items():
            info = self.key_metadata.get(api_key, {})
            clients[client_id] = {
                "client_name": info.get("client_name", client_id),
                "permissions": list(info.get("permissions", [])),
                "active": True
            }
        
        return clients
    
    @classmethod
    def create_default(cls) -> "APIKeyAuth":
        """Create auth manager with default keys for testing.
        
        Returns:
            APIKeyAuth instance with test keys
        """
        auth = cls()
        
        # Add some default keys for testing
        auth.add_key(
            "test-key-123",
            "test-client",
            "Test Client",
            {"customer_service", "escalation"}
        )
        
        auth.add_key(
            "admin-key-456", 
            "admin-client",
            "Admin Client",
            {"*"}  # All permissions
        )
        
        return auth
    
    def __repr__(self) -> str:
        """String representation."""
        return f"APIKeyAuth(keys={len(self.valid_keys)})"


# Convenience functions for header extraction

def extract_api_key(headers: Dict[str, str]) -> Optional[str]:
    """Extract API key from request headers.
    
    Checks both 'X-API-Key' and 'Authorization: Bearer' headers.
    
    Args:
        headers: HTTP headers
        
    Returns:
        API key if found
    """
    # Check X-API-Key header
    api_key = headers.get("X-API-Key") or headers.get("x-api-key")
    if api_key:
        return api_key
    
    # Check Authorization header
    auth_header = headers.get("Authorization") or headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return None


def require_api_key(auth: APIKeyAuth, permission: Optional[str] = None):
    """Decorator to require API key authentication.
    
    Args:
        auth: APIKeyAuth instance
        permission: Optional required permission
        
    Example:
        ```python
        auth = APIKeyAuth()
        
        @require_api_key(auth, "customer_service")
        async def handle_request(request):
            # Handler code
        ```
    """
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            # Extract API key
            headers = getattr(request, "headers", {})
            api_key = extract_api_key(headers)
            
            if not api_key:
                return {"error": "API key required", "status": 401}
            
            # Authenticate
            client_id = auth.authenticate(api_key)
            if not client_id:
                return {"error": "Invalid API key", "status": 401}
            
            # Check permission if specified
            if permission and not auth.check_permission(api_key, permission):
                return {"error": "Insufficient permissions", "status": 403}
            
            # Add client info to request
            if hasattr(request, "__dict__"):
                request.client_id = client_id
                request.client_info = auth.get_client_info(api_key)
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
