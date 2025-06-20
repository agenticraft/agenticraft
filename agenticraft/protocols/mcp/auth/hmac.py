"""HMAC authentication for AgentiCraft MCP protocol.

HMAC (Hash-based Message Authentication Code) authentication for
secure API access with signature verification.
"""

import hashlib
import hmac
import logging
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class HMACAuth:
    """HMAC signature authentication for secure API access.
    
    This authenticator uses HMAC signatures to verify request authenticity
    and prevent tampering. Commonly used for webhook and API authentication.
    
    Args:
        shared_secrets: Dict mapping client IDs to their shared secrets
        algorithm: Hash algorithm to use (default: sha256)
        timestamp_tolerance: Seconds to allow timestamp drift (default: 300)
    """
    
    def __init__(
        self,
        shared_secrets: Optional[Dict[str, str]] = None,
        algorithm: str = "sha256",
        timestamp_tolerance: int = 300
    ):
        self.shared_secrets = shared_secrets or {}
        self.algorithm = algorithm
        self.timestamp_tolerance = timestamp_tolerance
        
        # Validate algorithm
        if algorithm not in hashlib.algorithms_available:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        logger.info(f"Initialized HMACAuth with {len(self.shared_secrets)} clients")
    
    def add_client(self, client_id: str, secret: str) -> bool:
        """Add a client with shared secret.
        
        Args:
            client_id: Unique client identifier
            secret: Shared secret for HMAC
            
        Returns:
            True if added successfully
        """
        if client_id in self.shared_secrets:
            logger.warning(f"Client {client_id} already exists")
            return False
        
        self.shared_secrets[client_id] = secret
        logger.info(f"Added HMAC client '{client_id}'")
        return True
    
    def remove_client(self, client_id: str) -> bool:
        """Remove a client.
        
        Args:
            client_id: Client to remove
            
        Returns:
            True if removed
        """
        if client_id in self.shared_secrets:
            del self.shared_secrets[client_id]
            logger.info(f"Removed HMAC client '{client_id}'")
            return True
        return False
    
    def generate_signature(
        self,
        client_id: str,
        method: str,
        path: str,
        timestamp: str,
        body: str = ""
    ) -> Optional[str]:
        """Generate HMAC signature for a request.
        
        Args:
            client_id: Client identifier
            method: HTTP method (GET, POST, etc.)
            path: Request path
            timestamp: Request timestamp (string)
            body: Request body (for POST/PUT)
            
        Returns:
            HMAC signature if client exists
        """
        secret = self.shared_secrets.get(client_id)
        if not secret:
            logger.error(f"Unknown client: {client_id}")
            return None
        
        # Build canonical string
        canonical = self._build_canonical_string(method, path, timestamp, body)
        
        # Generate HMAC
        signature = hmac.new(
            secret.encode('utf-8'),
            canonical.encode('utf-8'),
            getattr(hashlib, self.algorithm)
        ).hexdigest()
        
        return signature
    
    def verify_signature(
        self,
        client_id: str,
        signature: str,
        method: str,
        path: str,
        timestamp: str,
        body: str = ""
    ) -> bool:
        """Verify HMAC signature.
        
        Args:
            client_id: Client identifier
            signature: Provided signature
            method: HTTP method
            path: Request path
            timestamp: Request timestamp
            body: Request body
            
        Returns:
            True if signature is valid
        """
        # Check timestamp to prevent replay attacks
        try:
            ts = int(timestamp)
            current_time = int(time.time())
            
            if abs(current_time - ts) > self.timestamp_tolerance:
                logger.warning(f"Timestamp too old: {timestamp}")
                return False
        except ValueError:
            logger.error(f"Invalid timestamp: {timestamp}")
            return False
        
        # Generate expected signature
        expected = self.generate_signature(client_id, method, path, timestamp, body)
        if not expected:
            return False
        
        # Compare signatures (constant time)
        is_valid = hmac.compare_digest(signature, expected)
        
        if is_valid:
            logger.debug(f"Valid HMAC signature from client '{client_id}'")
        else:
            logger.warning(f"Invalid HMAC signature from client '{client_id}'")
        
        return is_valid
    
    def authenticate_request(
        self,
        headers: Dict[str, str],
        method: str,
        path: str,
        body: str = ""
    ) -> Optional[str]:
        """Authenticate a request using HMAC.
        
        Args:
            headers: Request headers
            method: HTTP method
            path: Request path
            body: Request body
            
        Returns:
            Client ID if authenticated, None otherwise
        """
        # Extract HMAC headers
        client_id = headers.get("X-Client-ID") or headers.get("x-client-id")
        signature = headers.get("X-Signature") or headers.get("x-signature")
        timestamp = headers.get("X-Timestamp") or headers.get("x-timestamp")
        
        if not all([client_id, signature, timestamp]):
            logger.warning("Missing HMAC headers")
            return None
        
        # Verify signature
        if self.verify_signature(client_id, signature, method, path, timestamp, body):
            return client_id
        
        return None
    
    def generate_auth_headers(
        self,
        client_id: str,
        method: str,
        path: str,
        body: str = ""
    ) -> Optional[Dict[str, str]]:
        """Generate authentication headers for a request.
        
        Args:
            client_id: Client identifier
            method: HTTP method
            path: Request path
            body: Request body
            
        Returns:
            Dict of headers if client exists
        """
        timestamp = str(int(time.time()))
        signature = self.generate_signature(client_id, method, path, timestamp, body)
        
        if not signature:
            return None
        
        return {
            "X-Client-ID": client_id,
            "X-Signature": signature,
            "X-Timestamp": timestamp
        }
    
    def _build_canonical_string(
        self,
        method: str,
        path: str,
        timestamp: str,
        body: str
    ) -> str:
        """Build canonical string for signing.
        
        Args:
            method: HTTP method
            path: Request path
            timestamp: Request timestamp
            body: Request body
            
        Returns:
            Canonical string
        """
        # Standard format: METHOD\nPATH\nTIMESTAMP\nBODY_HASH
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
    
    @classmethod
    def create_default(cls) -> "HMACAuth":
        """Create HMAC auth with default test clients.
        
        Returns:
            HMACAuth instance
        """
        auth = cls()
        
        # Add test clients
        auth.add_client(
            "test-client",
            "test-secret-key-123"
        )
        
        auth.add_client(
            "github-webhook",
            "github-webhook-secret"
        )
        
        return auth
    
    def __repr__(self) -> str:
        """String representation."""
        return f"HMACAuth(clients={len(self.shared_secrets)}, algorithm='{self.algorithm}')"


# HMAC validation decorator
def require_hmac(auth: HMACAuth):
    """Decorator to require HMAC authentication.
    
    Args:
        auth: HMACAuth instance
        
    Example:
        ```python
        auth = HMACAuth()
        
        @require_hmac(auth)
        async def webhook_handler(request):
            # Handler code
        ```
    """
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            # Extract request details
            method = request.method
            path = request.path
            body = await request.body() if hasattr(request, 'body') else ""
            headers = dict(request.headers) if hasattr(request, 'headers') else {}
            
            # Authenticate
            client_id = auth.authenticate_request(headers, method, path, body)
            if not client_id:
                return {"error": "Invalid HMAC signature", "status": 401}
            
            # Add client info to request
            if hasattr(request, "__dict__"):
                request.hmac_client_id = client_id
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Webhook signature verification
class WebhookVerifier:
    """Helper for webhook signature verification."""
    
    @staticmethod
    def verify_github_webhook(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify GitHub webhook signature.
        
        Args:
            payload: Request body bytes
            signature: X-Hub-Signature-256 header
            secret: Webhook secret
            
        Returns:
            True if valid
        """
        if not signature.startswith("sha256="):
            return False
        
        expected = "sha256=" + hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    @staticmethod
    def verify_stripe_webhook(
        payload: bytes,
        signature: str,
        secret: str,
        tolerance: int = 300
    ) -> bool:
        """Verify Stripe webhook signature.
        
        Args:
            payload: Request body bytes
            signature: Stripe-Signature header
            secret: Webhook secret
            tolerance: Timestamp tolerance in seconds
            
        Returns:
            True if valid
        """
        # Parse Stripe signature format
        elements = {}
        for item in signature.split(","):
            key, value = item.split("=", 1)
            elements[key] = value
        
        timestamp = elements.get("t")
        if not timestamp:
            return False
        
        # Check timestamp
        try:
            ts = int(timestamp)
            if abs(time.time() - ts) > tolerance:
                return False
        except ValueError:
            return False
        
        # Verify signature
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Stripe can have multiple signatures
        signatures = [s for k, s in elements.items() if k.startswith("v")]
        return any(hmac.compare_digest(sig, expected) for sig in signatures)
