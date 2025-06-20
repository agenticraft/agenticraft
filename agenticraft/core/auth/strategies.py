"""
Authentication strategies for core auth system.

This module provides various authentication strategies that can be
used by any protocol implementation.
"""
import base64
import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, List

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

from .base import AuthProvider, AuthConfig, AuthType

logger = logging.getLogger(__name__)


class NoAuthProvider(AuthProvider):
    """No authentication provider."""
    
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """No authentication required."""
        return {"authenticated": True, "client_id": "anonymous"}
        
    def get_headers(self) -> Dict[str, str]:
        """No headers needed."""
        return {}
        
    def get_connection_params(self) -> Dict[str, Any]:
        """No connection params needed."""
        return {}


class APIKeyAuthProvider(AuthProvider):
    """API Key authentication provider."""
    
    def __init__(self, config: AuthConfig):
        """Initialize API key auth."""
        super().__init__(config)
        self.api_key = config.credentials.get("key", "")
        self.header_name = config.options.get("header", "X-API-Key")
        
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using API key."""
        headers = context.get("headers", {})
        
        # Check for API key in headers
        provided_key = headers.get(self.header_name) or headers.get(self.header_name.lower())
        
        if provided_key == self.api_key:
            return {
                "authenticated": True,
                "client_id": "api_key_client",
                "auth_method": "api_key"
            }
        
        return {"authenticated": False}
        
    def get_headers(self) -> Dict[str, str]:
        """Get API key header."""
        return {self.header_name: self.api_key}
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection params."""
        return {"headers": self.get_headers()}


class BearerAuthProvider(AuthProvider):
    """Bearer token authentication provider."""
    
    def __init__(self, config: AuthConfig):
        """Initialize bearer auth."""
        super().__init__(config)
        self.token = config.credentials.get("token", "")
        
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using bearer token."""
        headers = context.get("headers", {})
        
        # Check Authorization header
        auth_header = headers.get("Authorization") or headers.get("authorization", "")
        
        if auth_header.startswith("Bearer ") and auth_header[7:] == self.token:
            return {
                "authenticated": True,
                "client_id": "bearer_client",
                "auth_method": "bearer"
            }
        
        return {"authenticated": False}
        
    def get_headers(self) -> Dict[str, str]:
        """Get bearer token header."""
        return {"Authorization": f"Bearer {self.token}"}
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection params."""
        return {"headers": self.get_headers()}


class BasicAuthProvider(AuthProvider):
    """Basic authentication provider."""
    
    def __init__(self, config: AuthConfig):
        """Initialize basic auth."""
        super().__init__(config)
        self.username = config.credentials.get("username", "")
        self.password = config.credentials.get("password", "")
        
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using basic auth."""
        headers = context.get("headers", {})
        
        # Check Authorization header
        auth_header = headers.get("Authorization") or headers.get("authorization", "")
        
        if auth_header.startswith("Basic "):
            try:
                # Decode credentials
                encoded = auth_header[6:]
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)
                
                if username == self.username and password == self.password:
                    return {
                        "authenticated": True,
                        "client_id": username,
                        "auth_method": "basic"
                    }
            except Exception:
                pass
        
        return {"authenticated": False}
        
    def get_headers(self) -> Dict[str, str]:
        """Get basic auth header."""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
        return {"Authorization": f"Basic {encoded}"}
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection params."""
        return {"headers": self.get_headers()}


class HMACAuthProvider(AuthProvider):
    """HMAC signature authentication provider."""
    
    def __init__(self, config: AuthConfig):
        """Initialize HMAC auth."""
        super().__init__(config)
        self.key_id = config.credentials.get("key_id", "")
        self.secret_key = config.credentials.get("secret_key", "")
        self.algorithm = config.options.get("algorithm", "sha256")
        
        # Validate algorithm
        if self.algorithm not in hashlib.algorithms_available:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
            
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using HMAC signature."""
        headers = context.get("headers", {})
        method = context.get("method", "GET")
        path = context.get("path", "/")
        body = context.get("body", "")
        
        # Extract HMAC headers
        client_id = headers.get("X-Client-ID") or headers.get("x-client-id")
        signature = headers.get("X-Signature") or headers.get("x-signature")
        timestamp = headers.get("X-Timestamp") or headers.get("x-timestamp")
        
        if not all([client_id, signature, timestamp]):
            return {"authenticated": False}
            
        # Verify client ID
        if client_id != self.key_id:
            return {"authenticated": False}
            
        # Verify timestamp (prevent replay attacks)
        try:
            ts = int(timestamp)
            current_time = int(time.time())
            
            if abs(current_time - ts) > 300:  # 5 minute tolerance
                return {"authenticated": False}
        except ValueError:
            return {"authenticated": False}
            
        # Generate expected signature
        canonical = self._build_canonical_string(method, path, timestamp, body)
        expected = hmac.new(
            self.secret_key.encode('utf-8'),
            canonical.encode('utf-8'),
            getattr(hashlib, self.algorithm)
        ).hexdigest()
        
        # Compare signatures
        if hmac.compare_digest(signature, expected):
            return {
                "authenticated": True,
                "client_id": client_id,
                "auth_method": "hmac"
            }
        
        return {"authenticated": False}
        
    def get_headers(self) -> Dict[str, str]:
        """Get HMAC headers for a request."""
        # This requires context, so return empty
        # Use get_headers_for_request instead
        return {}
        
    def get_headers_for_request(
        self, 
        method: str, 
        path: str, 
        body: str = ""
    ) -> Dict[str, str]:
        """Get HMAC headers for specific request."""
        timestamp = str(int(time.time()))
        
        # Generate signature
        canonical = self._build_canonical_string(method, path, timestamp, body)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            canonical.encode('utf-8'),
            getattr(hashlib, self.algorithm)
        ).hexdigest()
        
        return {
            "X-Client-ID": self.key_id,
            "X-Signature": signature,
            "X-Timestamp": timestamp
        }
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection params."""
        return {}  # HMAC headers are request-specific
        
    def _build_canonical_string(
        self, 
        method: str, 
        path: str, 
        timestamp: str, 
        body: str
    ) -> str:
        """Build canonical string for signing."""
        body_hash = ""
        if body:
            h = hashlib.new(self.algorithm)
            h.update(body.encode('utf-8'))
            body_hash = h.hexdigest()
        
        parts = [
            method.upper(),
            path,
            timestamp,
            body_hash
        ]
        
        return "\n".join(parts)


class JWTAuthProvider(AuthProvider):
    """JWT authentication provider."""
    
    def __init__(self, config: AuthConfig):
        """Initialize JWT auth."""
        super().__init__(config)
        
        if not JWT_AVAILABLE:
            raise ImportError(
                "PyJWT is required for JWT authentication. "
                "Install with: pip install pyjwt"
            )
            
        self.token = config.credentials.get("token", "")
        self.secret = config.credentials.get("secret", "")
        self.algorithm = config.options.get("algorithm", "HS256")
        self.issuer = config.options.get("issuer", "agenticraft")
        self.audience = config.options.get("audience", "agenticraft")
        
        # Token cache
        self._cached_token = None
        self._token_expiry = None
        
    async def authenticate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using JWT."""
        headers = context.get("headers", {})
        
        # Extract token from Authorization header
        auth_header = headers.get("Authorization") or headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return {"authenticated": False}
            
        token = auth_header[7:]
        
        try:
            # Verify token
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            
            return {
                "authenticated": True,
                "client_id": payload.get("sub", "jwt_client"),
                "auth_method": "jwt",
                "claims": payload
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            
        return {"authenticated": False}
        
    def get_headers(self) -> Dict[str, str]:
        """Get JWT header."""
        token = self._get_or_generate_token()
        return {"Authorization": f"Bearer {token}"}
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection params."""
        return {"headers": self.get_headers()}
        
    def _get_or_generate_token(self) -> str:
        """Get cached token or generate new one."""
        # If we have a provided token, use it
        if self.token:
            return self.token
            
        # Check if cached token is still valid
        if self._cached_token and self._token_expiry:
            if datetime.utcnow() < self._token_expiry:
                return self._cached_token
                
        # Generate new token
        now = datetime.utcnow()
        expiry = now + timedelta(hours=1)
        
        payload = {
            "sub": "agenticraft_client",
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": expiry
        }
        
        self._cached_token = jwt.encode(
            payload, 
            self.secret, 
            algorithm=self.algorithm
        )
        self._token_expiry = expiry
        
        return self._cached_token


# Register providers with auth manager
from .base import get_auth_manager

auth_manager = get_auth_manager()
auth_manager.register_provider(AuthType.NONE, NoAuthProvider)
auth_manager.register_provider(AuthType.API_KEY, APIKeyAuthProvider)
auth_manager.register_provider(AuthType.BEARER, BearerAuthProvider)
auth_manager.register_provider(AuthType.BASIC, BasicAuthProvider)
auth_manager.register_provider(AuthType.HMAC, HMACAuthProvider)
auth_manager.register_provider(AuthType.JWT, JWTAuthProvider)
