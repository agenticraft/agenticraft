"""
Simple API Key authentication for workflows.

This provides a simple API key manager that can be used by workflows
for basic authentication without the full complexity of the auth providers.
"""
import secrets
from typing import Dict, Optional, Set


class APIKeyAuth:
    """Simple API key authentication manager."""
    
    def __init__(self):
        """Initialize API key store."""
        self._keys: Dict[str, Dict[str, any]] = {}
        
    @classmethod
    def create_default(cls) -> "APIKeyAuth":
        """Create a default instance with some demo keys."""
        auth = cls()
        
        # Add some default demo keys
        auth.add_key(
            api_key="demo-key-1234",
            client_id="demo_client",
            client_name="Demo Client",
            permissions={"read", "write"}
        )
        
        return auth
        
    def authenticate(self, api_key: str) -> Optional[str]:
        """Authenticate an API key and return client ID."""
        if api_key in self._keys:
            return self._keys[api_key]["client_id"]
        return None
        
    def add_key(
        self,
        api_key: str,
        client_id: str,
        client_name: Optional[str] = None,
        permissions: Optional[Set[str]] = None
    ) -> bool:
        """Add an API key."""
        self._keys[api_key] = {
            "client_id": client_id,
            "client_name": client_name or client_id,
            "permissions": permissions or set()
        }
        return True
        
    def remove_key(self, api_key: str) -> bool:
        """Remove an API key."""
        if api_key in self._keys:
            del self._keys[api_key]
            return True
        return False
        
    def list_clients(self) -> Dict[str, Dict[str, any]]:
        """List all registered clients."""
        clients = {}
        for key_data in self._keys.values():
            client_id = key_data["client_id"]
            if client_id not in clients:
                clients[client_id] = {
                    "name": key_data["client_name"],
                    "permissions": key_data["permissions"]
                }
        return clients
        
    def generate_key(self) -> str:
        """Generate a new API key."""
        return f"sk-{secrets.token_urlsafe(32)}"
