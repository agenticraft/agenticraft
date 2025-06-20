"""Bearer token authentication for AgentiCraft MCP protocol.

Simple bearer token authentication for stateless API access,
commonly used with OAuth2 and other token-based systems.
"""

import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Tuple, List, Any

logger = logging.getLogger(__name__)


class BearerAuth:
    """Bearer token authentication for API access.
    
    This authenticator manages bearer tokens for simple, stateless
    authentication. Tokens can be pre-generated or dynamically created.
    
    Args:
        token_length: Length of generated tokens (default: 32)
        token_prefix: Optional prefix for tokens (e.g., "sk_")
        default_expiry: Default expiry in seconds (0 = no expiry)
    """
    
    def __init__(
        self,
        token_length: int = 32,
        token_prefix: str = "",
        default_expiry: int = 0
    ):
        self.token_length = token_length
        self.token_prefix = token_prefix
        self.default_expiry = default_expiry
        
        # Token storage: token -> metadata
        self.tokens: Dict[str, Dict] = {}
        
        # Reverse lookup: client_id -> tokens
        self.client_tokens: Dict[str, Set[str]] = {}
        
        logger.info(f"Initialized BearerAuth (prefix: '{token_prefix}')")
    
    def generate_token(
        self,
        client_id: str,
        client_name: Optional[str] = None,
        permissions: Optional[Set[str]] = None,
        expiry_seconds: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Generate a new bearer token.
        
        Args:
            client_id: Client identifier
            client_name: Human-readable client name
            permissions: Set of permissions
            expiry_seconds: Token expiry (overrides default)
            metadata: Additional metadata
            
        Returns:
            Generated bearer token
        """
        # Generate token
        token_value = secrets.token_urlsafe(self.token_length)
        token = f"{self.token_prefix}{token_value}"
        
        # Calculate expiry
        expiry = None
        if expiry_seconds is not None:
            if expiry_seconds > 0:
                expiry = datetime.utcnow() + timedelta(seconds=expiry_seconds)
        elif self.default_expiry > 0:
            expiry = datetime.utcnow() + timedelta(seconds=self.default_expiry)
        
        # Store token
        self.tokens[token] = {
            "client_id": client_id,
            "client_name": client_name or client_id,
            "permissions": permissions or set(),
            "created_at": datetime.utcnow(),
            "expires_at": expiry,
            "last_used": None,
            "usage_count": 0,
            "metadata": metadata or {}
        }
        
        # Update client tokens
        if client_id not in self.client_tokens:
            self.client_tokens[client_id] = set()
        self.client_tokens[client_id].add(token)
        
        logger.info(f"Generated bearer token for client '{client_id}'")
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a bearer token.
        
        Args:
            token: Bearer token to verify
            
        Returns:
            Client ID if valid, None otherwise
        """
        token_data = self.tokens.get(token)
        if not token_data:
            logger.warning("Invalid bearer token")
            return None
        
        # Check expiry
        if token_data["expires_at"]:
            if datetime.utcnow() > token_data["expires_at"]:
                logger.warning("Bearer token expired")
                return None
        
        # Update usage
        token_data["last_used"] = datetime.utcnow()
        token_data["usage_count"] += 1
        
        client_id = token_data["client_id"]
        logger.debug(f"Verified bearer token for client '{client_id}'")
        
        return client_id
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a bearer token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked successfully
        """
        token_data = self.tokens.get(token)
        if not token_data:
            return False
        
        # Remove from tokens
        client_id = token_data["client_id"]
        del self.tokens[token]
        
        # Remove from client tokens
        if client_id in self.client_tokens:
            self.client_tokens[client_id].discard(token)
            if not self.client_tokens[client_id]:
                del self.client_tokens[client_id]
        
        logger.info(f"Revoked bearer token for client '{client_id}'")
        return True
    
    def revoke_client_tokens(self, client_id: str) -> int:
        """Revoke all tokens for a client.
        
        Args:
            client_id: Client whose tokens to revoke
            
        Returns:
            Number of tokens revoked
        """
        if client_id not in self.client_tokens:
            return 0
        
        tokens = list(self.client_tokens[client_id])
        count = 0
        
        for token in tokens:
            if self.revoke_token(token):
                count += 1
        
        logger.info(f"Revoked {count} tokens for client '{client_id}'")
        return count
    
    def check_permission(
        self,
        token: str,
        permission: str
    ) -> bool:
        """Check if token has specific permission.
        
        Args:
            token: Bearer token
            permission: Permission to check
            
        Returns:
            True if token has permission
        """
        token_data = self.tokens.get(token)
        if not token_data:
            return False
        
        permissions = token_data.get("permissions", set())
        return permission in permissions or "*" in permissions
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """Get information about a token.
        
        Args:
            token: Bearer token
            
        Returns:
            Token information or None
        """
        token_data = self.tokens.get(token)
        if not token_data:
            return None
        
        # Return safe copy
        return {
            "client_id": token_data["client_id"],
            "client_name": token_data["client_name"],
            "permissions": list(token_data["permissions"]),
            "created_at": token_data["created_at"].isoformat(),
            "expires_at": token_data["expires_at"].isoformat() if token_data["expires_at"] else None,
            "last_used": token_data["last_used"].isoformat() if token_data["last_used"] else None,
            "usage_count": token_data["usage_count"],
            "active": self.verify_token(token) is not None
        }
    
    def list_client_tokens(self, client_id: str) -> List[Dict]:
        """List all tokens for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of token information
        """
        if client_id not in self.client_tokens:
            return []
        
        tokens = []
        for token in self.client_tokens[client_id]:
            info = self.get_token_info(token)
            if info:
                # Add masked token
                if len(token) > 8:
                    info["token"] = f"{token[:4]}...{token[-4:]}"
                else:
                    info["token"] = "***"
                tokens.append(info)
        
        return tokens
    
    def cleanup_expired(self) -> int:
        """Remove expired tokens.
        
        Returns:
            Number of tokens removed
        """
        expired = []
        now = datetime.utcnow()
        
        for token, data in self.tokens.items():
            if data["expires_at"] and now > data["expires_at"]:
                expired.append(token)
        
        for token in expired:
            self.revoke_token(token)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired tokens")
        
        return len(expired)
    
    @classmethod
    def create_default(cls) -> "BearerAuth":
        """Create bearer auth with default test tokens.
        
        Returns:
            BearerAuth instance
        """
        auth = cls(token_prefix="test_")
        
        # Add test tokens
        auth.generate_token(
            "test-client",
            "Test Client",
            {"read", "write"},
            metadata={"environment": "test"}
        )
        
        auth.generate_token(
            "admin-client",
            "Admin Client",
            {"*"},  # All permissions
            metadata={"role": "admin"}
        )
        
        return auth
    
    def __repr__(self) -> str:
        """String representation."""
        active_tokens = sum(
            1 for token_data in self.tokens.values()
            if not token_data["expires_at"] or datetime.utcnow() <= token_data["expires_at"]
        )
        return f"BearerAuth(tokens={active_tokens}, clients={len(self.client_tokens)})"


# OAuth2-style bearer token support
class OAuth2Bearer(BearerAuth):
    """OAuth2-compatible bearer token authentication.
    
    Extends BearerAuth with OAuth2-specific features like
    refresh tokens and token introspection.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Refresh tokens
        self.refresh_tokens: Dict[str, Dict] = {}
    
    def generate_token_pair(
        self,
        client_id: str,
        client_name: Optional[str] = None,
        permissions: Optional[Set[str]] = None,
        access_expiry: int = 3600,  # 1 hour
        refresh_expiry: int = 2592000,  # 30 days
        metadata: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """Generate access and refresh token pair.
        
        Args:
            client_id: Client identifier
            client_name: Human-readable name
            permissions: Set of permissions
            access_expiry: Access token expiry in seconds
            refresh_expiry: Refresh token expiry in seconds
            metadata: Additional metadata
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Generate access token
        access_token = self.generate_token(
            client_id,
            client_name,
            permissions,
            access_expiry,
            metadata
        )
        
        # Generate refresh token
        refresh_value = secrets.token_urlsafe(self.token_length)
        refresh_token = f"{self.token_prefix}r_{refresh_value}"
        
        self.refresh_tokens[refresh_token] = {
            "client_id": client_id,
            "client_name": client_name or client_id,
            "permissions": permissions or set(),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=refresh_expiry),
            "last_used": None,
            "access_tokens": [access_token],
            "metadata": metadata or {}
        }
        
        logger.info(f"Generated token pair for client '{client_id}'")
        return access_token, refresh_token
    
    def refresh_access_token(
        self,
        refresh_token: str,
        access_expiry: int = 3600
    ) -> Optional[str]:
        """Use refresh token to get new access token.
        
        Args:
            refresh_token: Refresh token
            access_expiry: New access token expiry
            
        Returns:
            New access token if refresh successful
        """
        refresh_data = self.refresh_tokens.get(refresh_token)
        if not refresh_data:
            logger.warning("Invalid refresh token")
            return None
        
        # Check expiry
        if datetime.utcnow() > refresh_data["expires_at"]:
            logger.warning("Refresh token expired")
            return None
        
        # Generate new access token
        access_token = self.generate_token(
            refresh_data["client_id"],
            refresh_data["client_name"],
            refresh_data["permissions"],
            access_expiry,
            refresh_data["metadata"]
        )
        
        # Update refresh token
        refresh_data["last_used"] = datetime.utcnow()
        refresh_data["access_tokens"].append(access_token)
        
        logger.info(f"Refreshed access token for client '{refresh_data['client_id']}'")
        return access_token
    
    def introspect_token(self, token: str) -> Dict[str, Any]:
        """OAuth2 token introspection.
        
        Args:
            token: Token to introspect
            
        Returns:
            Token introspection response
        """
        # Check access token
        token_data = self.tokens.get(token)
        if token_data:
            active = True
            if token_data["expires_at"]:
                active = datetime.utcnow() <= token_data["expires_at"]
            
            return {
                "active": active,
                "token_type": "access_token",
                "client_id": token_data["client_id"],
                "scope": " ".join(token_data["permissions"]),
                "exp": int(token_data["expires_at"].timestamp()) if token_data["expires_at"] else None,
                "iat": int(token_data["created_at"].timestamp())
            }
        
        # Check refresh token
        refresh_data = self.refresh_tokens.get(token)
        if refresh_data:
            active = datetime.utcnow() <= refresh_data["expires_at"]
            
            return {
                "active": active,
                "token_type": "refresh_token",
                "client_id": refresh_data["client_id"],
                "scope": " ".join(refresh_data["permissions"]),
                "exp": int(refresh_data["expires_at"].timestamp()),
                "iat": int(refresh_data["created_at"].timestamp())
            }
        
        return {"active": False}


# Bearer token validation decorator
def require_bearer(auth: BearerAuth, permission: Optional[str] = None):
    """Decorator to require bearer token authentication.
    
    Args:
        auth: BearerAuth instance
        permission: Optional required permission
        
    Example:
        ```python
        auth = BearerAuth()
        
        @require_bearer(auth, "write")
        async def protected_endpoint(request):
            # Handler code
        ```
    """
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"error": "Bearer token required", "status": 401}
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Verify token
            client_id = auth.verify_token(token)
            if not client_id:
                return {"error": "Invalid or expired token", "status": 401}
            
            # Check permission if specified
            if permission and not auth.check_permission(token, permission):
                return {"error": "Insufficient permissions", "status": 403}
            
            # Add client info to request
            if hasattr(request, "__dict__"):
                request.bearer_client_id = client_id
                request.bearer_token_info = auth.get_token_info(token)
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
