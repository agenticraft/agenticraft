"""
Authentication module for AgentiCraft security.

This module provides various authentication methods including:
- API Key authentication
- JWT (JSON Web Token) authentication
- OAuth authentication (future)
"""

from .api_key import APIKeyAuth, APIKey
from .jwt import JWTAuth

__all__ = [
    "APIKeyAuth",
    "APIKey", 
    "JWTAuth"
]
