"""MCP Authentication for AgentiCraft.

This module provides authentication methods for the MCP protocol,
including API key, JWT, HMAC, and Bearer token authentication.
"""

from .api_key import APIKeyAuth, extract_api_key, require_api_key
from .bearer import BearerAuth, OAuth2Bearer, require_bearer
from .hmac import HMACAuth, WebhookVerifier, require_hmac
from .jwt import JWTAuth, require_jwt

__all__ = [
    # API Key
    "APIKeyAuth",
    "extract_api_key", 
    "require_api_key",
    # JWT
    "JWTAuth",
    "require_jwt",
    # HMAC
    "HMACAuth",
    "WebhookVerifier",
    "require_hmac",
    # Bearer
    "BearerAuth",
    "OAuth2Bearer",
    "require_bearer",
]
