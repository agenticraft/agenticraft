"""JWT authentication for AgentiCraft MCP protocol.

JWT (JSON Web Token) authentication for secure, stateless authentication
in the Code Review Pipeline workflow.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

logger = logging.getLogger(__name__)


class JWTAuth:
    """JWT authentication for code review services.
    
    This authenticator manages JWT tokens for secure access to
    code review pipelines and related services.
    
    Args:
        secret_key: Secret key for signing tokens
        issuer: Token issuer (default: "agenticraft")
        audience: Token audience (default: "code-review")
        algorithm: JWT algorithm (default: "HS256")
        token_expiry: Token expiry in seconds (default: 3600)
    """
    
    def __init__(
        self,
        secret_key: str,
        issuer: str = "agenticraft",
        audience: str = "code-review",
        algorithm: str = "HS256",
        token_expiry: int = 3600
    ):
        if not JWT_AVAILABLE:
            raise ImportError(
                "PyJWT is required for JWT authentication. "
                "Install with: pip install pyjwt"
            )
        
        if not secret_key:
            raise ValueError("Secret key is required for JWT authentication")
        
        self.secret_key = secret_key
        self.issuer = issuer
        self.audience = audience
        self.algorithm = algorithm
        self.token_expiry = token_expiry
        
        # Token blacklist for revocation
        self.revoked_tokens: set = set()
        
        logger.info(f"Initialized JWTAuth (issuer: {issuer}, audience: {audience})")
    
    def generate_token(
        self,
        subject: str,
        claims: Optional[Dict[str, Any]] = None,
        expiry: Optional[int] = None
    ) -> str:
        """Generate a JWT token.
        
        Args:
            subject: Subject identifier (user/service ID)
            claims: Additional claims to include
            expiry: Custom expiry time in seconds
            
        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expiry_time = now + timedelta(seconds=expiry or self.token_expiry)
        
        # Build payload
        payload = {
            "sub": subject,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": expiry_time,
            "jti": f"{subject}-{int(now.timestamp())}"  # Unique token ID
        }
        
        # Add custom claims
        if claims:
            payload.update(claims)
        
        # Generate token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"Generated JWT token for subject '{subject}'")
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                logger.warning("Attempted to use revoked token")
                return None
            
            # Decode and verify
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            
            logger.debug(f"Verified JWT token for subject '{payload.get('sub')}'")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh a JWT token if valid.
        
        Args:
            token: Current JWT token
            
        Returns:
            New JWT token if refresh successful
        """
        payload = self.verify_token(token)
        if not payload:
            return None
        
        # Check if token is too old to refresh (e.g., older than 7 days)
        issued_at = payload.get("iat", 0)
        if time.time() - issued_at > 7 * 24 * 3600:
            logger.warning("Token too old to refresh")
            return None
        
        # Generate new token with same claims
        subject = payload.get("sub")
        claims = {k: v for k, v in payload.items() 
                 if k not in ["sub", "iss", "aud", "iat", "exp", "jti"]}
        
        return self.generate_token(subject, claims)
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked successfully
        """
        self.revoked_tokens.add(token)
        logger.info("Revoked JWT token")
        return True
    
    def get_subject(self, token: str) -> Optional[str]:
        """Extract subject from token without full verification.
        
        Args:
            token: JWT token
            
        Returns:
            Subject identifier if found
        """
        try:
            # Decode without verification (for subject extraction only)
            unverified = jwt.decode(token, options={"verify_signature": False})
            return unverified.get("sub")
        except:
            return None
    
    def create_service_token(
        self,
        service_name: str,
        permissions: list,
        expiry: int = 86400  # 24 hours
    ) -> str:
        """Create a service-to-service token.
        
        Args:
            service_name: Name of the service
            permissions: List of permissions
            expiry: Token expiry in seconds
            
        Returns:
            Service JWT token
        """
        claims = {
            "type": "service",
            "permissions": permissions,
            "service": service_name
        }
        
        return self.generate_token(f"service:{service_name}", claims, expiry)
    
    @classmethod
    def create_default(cls, secret_key: Optional[str] = None) -> "JWTAuth":
        """Create JWT auth with default settings.
        
        Args:
            secret_key: Optional secret key (generates if not provided)
            
        Returns:
            JWTAuth instance
        """
        if not secret_key:
            # In production, use a secure secret
            import secrets
            secret_key = secrets.token_urlsafe(32)
            logger.warning("Using generated secret key - not for production!")
        
        return cls(
            secret_key=secret_key,
            issuer="agenticraft",
            audience="code-review"
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"JWTAuth(issuer='{self.issuer}', audience='{self.audience}')"


# Token validation decorator
def require_jwt(auth: JWTAuth, required_claims: Optional[Dict[str, Any]] = None):
    """Decorator to require JWT authentication.
    
    Args:
        auth: JWTAuth instance
        required_claims: Claims that must be present
        
    Example:
        ```python
        auth = JWTAuth(secret_key="secret")
        
        @require_jwt(auth, {"type": "service"})
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
            payload = auth.verify_token(token)
            if not payload:
                return {"error": "Invalid or expired token", "status": 401}
            
            # Check required claims
            if required_claims:
                for claim, value in required_claims.items():
                    if payload.get(claim) != value:
                        return {"error": "Insufficient permissions", "status": 403}
            
            # Add token info to request
            if hasattr(request, "__dict__"):
                request.jwt_payload = payload
                request.jwt_subject = payload.get("sub")
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
