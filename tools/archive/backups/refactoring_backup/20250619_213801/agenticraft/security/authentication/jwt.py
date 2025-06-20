"""
JWT (JSON Web Token) authentication provider for AgentiCraft.

This module implements JWT-based authentication with support for
token generation, validation, and refresh tokens.
"""
import jwt
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from ..auth import IAuthProvider, AuthMethod, UserContext, AuthenticationError, TokenExpiredError


class JWTAuth(IAuthProvider):
    """JWT authentication provider."""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 30,
        issuer: str = "agenticraft"
    ):
        """
        Initialize JWT authentication provider.
        
        Args:
            secret_key: Secret key for signing tokens (auto-generated if not provided)
            algorithm: JWT algorithm to use
            access_token_expire_minutes: Access token expiration time
            refresh_token_expire_days: Refresh token expiration time
            issuer: Token issuer identifier
        """
        # Generate or use provided secret key
        if secret_key is None:
            secret_key = self._get_or_create_secret()
            
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.issuer = issuer
        
        # Store active refresh tokens (in production, use Redis or database)
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
        
    def _get_or_create_secret(self) -> str:
        """Get or create JWT secret key."""
        secret_file = Path.home() / ".agenticraft" / "jwt_secret.key"
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        
        if secret_file.exists():
            return secret_file.read_text().strip()
        else:
            # Generate secure random secret
            secret = secrets.token_urlsafe(64)
            secret_file.write_text(secret)
            secret_file.chmod(0o600)  # Secure file permissions
            return secret
            
    def _create_token(
        self,
        data: Dict[str, Any],
        expires_delta: timedelta,
        token_type: str = "access"
    ) -> str:
        """Create a JWT token."""
        to_encode = data.copy()
        
        # Add standard claims
        now = datetime.now(UTC)
        expire = now + expires_delta
        
        to_encode.update({
            "iat": now,  # Issued at
            "exp": expire,  # Expiration
            "iss": self.issuer,  # Issuer
            "type": token_type,  # Token type
            "jti": secrets.token_hex(16)  # JWT ID
        })
        
        # Create token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
        
    async def create_tokens(self, user_context: UserContext) -> Tuple[str, str]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user_context: Authenticated user context
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Token payload
        payload = {
            "sub": user_context.user_id,  # Subject
            "username": user_context.username,
            "email": user_context.email,
            "roles": user_context.roles,
            "permissions": user_context.permissions,
            "session_id": user_context.session_id
        }
        
        # Create access token
        access_token = self._create_token(
            payload,
            timedelta(minutes=self.access_token_expire_minutes),
            "access"
        )
        
        # Create refresh token
        refresh_token = self._create_token(
            payload,
            timedelta(days=self.refresh_token_expire_days),
            "refresh"
        )
        
        # Store refresh token
        self._refresh_tokens[refresh_token] = {
            "user_id": user_context.user_id,
            "created_at": datetime.now(UTC),
            "session_id": user_context.session_id
        }
        
        return access_token, refresh_token
        
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[UserContext]:
        """
        Authenticate using JWT token.
        
        For initial authentication, this would typically validate
        username/password and return tokens. Here we validate existing tokens.
        """
        token = credentials.get("token") or credentials.get("jwt")
        if not token:
            return None
            
        return await self.validate_token(token)
        
    async def validate_token(self, token: str) -> Optional[UserContext]:
        """Validate a JWT token and return user context."""
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer
            )
            
            # Check token type
            token_type = payload.get("type", "access")
            
            # Create user context from payload
            user_context = UserContext(
                user_id=payload["sub"],
                username=payload["username"],
                email=payload.get("email"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                attributes={
                    "token_type": token_type,
                    "session_id": payload.get("session_id"),
                    "jti": payload.get("jti")
                },
                auth_method=AuthMethod.JWT
            )
            
            return user_context
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("JWT token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid JWT token: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
            
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Use refresh token to get new access token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if refresh token is valid
        """
        # Check if refresh token exists and is valid
        if refresh_token not in self._refresh_tokens:
            raise AuthenticationError("Invalid refresh token")
            
        # Validate refresh token
        try:
            user_context = await self.validate_token(refresh_token)
            if user_context is None:
                raise AuthenticationError("Invalid refresh token")
                
            # Check token type
            if user_context.attributes.get("token_type") != "refresh":
                raise AuthenticationError("Not a refresh token")
                
            # Create new access token
            access_token = self._create_token(
                {
                    "sub": user_context.user_id,
                    "username": user_context.username,
                    "email": user_context.email,
                    "roles": user_context.roles,
                    "permissions": user_context.permissions,
                    "session_id": user_context.session_id
                },
                timedelta(minutes=self.access_token_expire_minutes),
                "access"
            )
            
            return access_token
            
        except Exception as e:
            raise AuthenticationError(f"Refresh failed: {str(e)}")
            
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token (primarily for refresh tokens)."""
        # For refresh tokens, remove from storage
        if token in self._refresh_tokens:
            del self._refresh_tokens[token]
            return True
            
        # For access tokens, we'd typically add to a blacklist
        # In production, use Redis with TTL matching token expiration
        return False
        
    async def revoke_all_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User ID whose tokens to revoke
            
        Returns:
            Number of tokens revoked
        """
        revoked = 0
        tokens_to_remove = []
        
        # Find all refresh tokens for user
        for token, data in self._refresh_tokens.items():
            if data["user_id"] == user_id:
                tokens_to_remove.append(token)
                
        # Remove tokens
        for token in tokens_to_remove:
            del self._refresh_tokens[token]
            revoked += 1
            
        return revoked
        
    def get_auth_method(self) -> AuthMethod:
        """Get authentication method."""
        return AuthMethod.JWT
        
    async def decode_token_unsafe(self, token: str) -> Dict[str, Any]:
        """
        Decode token without validation (for debugging only).
        
        WARNING: This does not validate the token signature!
        Only use for debugging or displaying token contents.
        """
        return jwt.decode(
            token,
            options={"verify_signature": False}
        )
