"""
API Key authentication provider for AgentiCraft.

This module implements API key-based authentication with support for
key generation, validation, and management.
"""
import hashlib
import secrets
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List,Set
from dataclasses import dataclass, field

from ..auth import IAuthProvider, AuthMethod, UserContext, AuthenticationError


@dataclass
class APIKey:
    """Represents an API key."""
    key_id: str
    key_hash: str  # Store hash, not plaintext
    user_id: str
    username: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    permissions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "permissions": self.permissions,
            "roles": self.roles,
            "metadata": self.metadata,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "is_active": self.is_active
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        """Create from dictionary."""
        return cls(
            key_id=data["key_id"],
            key_hash=data["key_hash"],
            user_id=data["user_id"],
            username=data["username"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            permissions=data.get("permissions", []),
            roles=data.get("roles", []),
            metadata=data.get("metadata", {}),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            usage_count=data.get("usage_count", 0),
            is_active=data.get("is_active", True)
        )


class APIKeyAuth(IAuthProvider):
    """API key authentication provider."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize API key authentication provider.
        
        Args:
            storage_path: Path to store API keys (defaults to ~/.agenticraft/api_keys.json)
        """
        if storage_path is None:
            storage_path = Path.home() / ".agenticraft" / "api_keys.json"
        
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing keys
        self._keys: Dict[str, APIKey] = self._load_keys()
        
        # Cache for performance
        self._key_hash_cache: Dict[str, str] = {}
        
    def _load_keys(self) -> Dict[str, APIKey]:
        """Load API keys from storage."""
        if not self.storage_path.exists():
            return {}
            
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return {
                    key_id: APIKey.from_dict(key_data)
                    for key_id, key_data in data.items()
                }
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}
            
    def _save_keys(self):
        """Save API keys to storage."""
        data = {
            key_id: key.to_dict()
            for key_id, key in self._keys.items()
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _hash_key(self, key: str) -> str:
        """Hash an API key."""
        if key in self._key_hash_cache:
            return self._key_hash_cache[key]
            
        # Use SHA-256 with salt
        salt = "agenticraft_api_key_salt"  # In production, use unique salt per key
        hash_value = hashlib.sha256(f"{salt}{key}".encode()).hexdigest()
        
        # Cache for performance
        self._key_hash_cache[key] = hash_value
        
        return hash_value
        
    async def create_key(
        self,
        user_id: str,
        username: str,
        permissions: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new API key.
        
        Args:
            user_id: User ID to associate with key
            username: Username for display
            permissions: List of permissions to grant
            roles: List of roles to assign
            expires_in_days: Days until key expires (None for no expiration)
            metadata: Additional metadata to store
            
        Returns:
            The generated API key (show this to user only once!)
        """
        # Generate secure random key
        key = f"sk_{secrets.token_urlsafe(32)}"
        key_id = f"key_{secrets.token_hex(8)}"
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
            
        # Create key object
        api_key = APIKey(
            key_id=key_id,
            key_hash=self._hash_key(key),
            user_id=user_id,
            username=username,
            created_at=datetime.now(),
            expires_at=expires_at,
            permissions=permissions or [],
            roles=roles or ["user"],  # Default role
            metadata=metadata or {}
        )
        
        # Store key
        self._keys[key_id] = api_key
        self._save_keys()
        
        return key
        
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[UserContext]:
        """Authenticate using API key."""
        api_key = credentials.get("api_key")
        if not api_key:
            return None
            
        # Hash the provided key
        key_hash = self._hash_key(api_key)
        
        # Find matching key
        for key_id, key_obj in self._keys.items():
            if key_obj.key_hash == key_hash:
                # Check if key is valid
                if not key_obj.is_active:
                    raise AuthenticationError("API key is inactive")
                    
                if key_obj.is_expired:
                    raise AuthenticationError("API key has expired")
                    
                # Update usage
                key_obj.last_used = datetime.now()
                key_obj.usage_count += 1
                self._save_keys()
                
                # Create user context
                return UserContext(
                    user_id=key_obj.user_id,
                    username=key_obj.username,
                    roles=key_obj.roles,
                    permissions=key_obj.permissions,
                    attributes={
                        "key_id": key_obj.key_id,
                        "key_metadata": key_obj.metadata
                    },
                    auth_method=AuthMethod.API_KEY
                )
                
        return None
        
    async def validate_token(self, token: str) -> Optional[UserContext]:
        """Validate an API key (same as authenticate for API keys)."""
        return await self.authenticate({"api_key": token})
        
    async def revoke_token(self, token: str) -> bool:
        """Revoke an API key."""
        key_hash = self._hash_key(token)
        
        for key_id, key_obj in self._keys.items():
            if key_obj.key_hash == key_hash:
                key_obj.is_active = False
                self._save_keys()
                return True
                
        return False
        
    async def revoke_by_id(self, key_id: str) -> bool:
        """Revoke a key by its ID."""
        if key_id in self._keys:
            self._keys[key_id].is_active = False
            self._save_keys()
            return True
        return False
        
    async def list_keys(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List API keys.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of key information (without sensitive data)
        """
        keys = []
        for key_id, key_obj in self._keys.items():
            if user_id and key_obj.user_id != user_id:
                continue
                
            keys.append({
                "key_id": key_obj.key_id,
                "user_id": key_obj.user_id,
                "username": key_obj.username,
                "created_at": key_obj.created_at.isoformat(),
                "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else None,
                "last_used": key_obj.last_used.isoformat() if key_obj.last_used else None,
                "usage_count": key_obj.usage_count,
                "is_active": key_obj.is_active,
                "is_expired": key_obj.is_expired
            })
            
        return keys
        
    def get_auth_method(self) -> AuthMethod:
        """Get authentication method."""
        return AuthMethod.API_KEY
