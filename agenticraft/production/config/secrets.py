"""
Secret management for AgentiCraft production deployments.
"""

import os
import json
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecretBackend(Enum):
    """Supported secret storage backends."""
    ENV = "environment"
    FILE = "file"
    VAULT = "vault"  # HashiCorp Vault
    AWS_SSM = "aws_ssm"  # AWS Systems Manager Parameter Store
    AZURE_KV = "azure_keyvault"  # Azure Key Vault
    GCP_SM = "gcp_secretmanager"  # Google Cloud Secret Manager


@dataclass
class Secret:
    """Represents a secret value."""
    name: str
    value: str
    metadata: Dict[str, Any] = None
    encrypted: bool = False


class SecretManager:
    """
    Manage secrets for AgentiCraft applications.
    
    Supports multiple backends:
    - Environment variables
    - Encrypted files
    - HashiCorp Vault
    - Cloud provider secret stores
    """
    
    def __init__(self, backend: SecretBackend = SecretBackend.ENV, **kwargs):
        """
        Initialize secret manager.
        
        Args:
            backend: Secret storage backend
            **kwargs: Backend-specific configuration
        """
        self.backend = backend
        self.config = kwargs
        self._cache: Dict[str, Secret] = {}
        self._encryption_key = None
        
        # Initialize encryption if using file backend
        if backend == SecretBackend.FILE:
            self._init_encryption()
            
    def _init_encryption(self):
        """Initialize encryption for file-based secrets."""
        # Get or generate encryption key
        key_path = self.config.get("key_path", "~/.agenticraft/secret.key")
        key_path = Path(os.path.expanduser(key_path))
        
        if key_path.exists():
            with open(key_path, "rb") as f:
                self._encryption_key = f.read()
        else:
            # Generate new key
            self._encryption_key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(key_path, "wb") as f:
                f.write(self._encryption_key)
                
            # Secure the key file
            os.chmod(key_path, 0o600)
            logger.info(f"Generated new encryption key at {key_path}")
            
        self._cipher = Fernet(self._encryption_key)
        
    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value.
        
        Args:
            name: Secret name
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name].value
            
        # Load from backend
        secret = self._load_secret(name)
        
        if secret:
            self._cache[name] = secret
            return secret.value
            
        return default
        
    def set(self, name: str, value: str, metadata: Dict[str, Any] = None):
        """
        Set a secret value.
        
        Args:
            name: Secret name
            value: Secret value
            metadata: Optional metadata
        """
        secret = Secret(name=name, value=value, metadata=metadata)
        
        # Store in backend
        self._store_secret(secret)
        
        # Update cache
        self._cache[name] = secret
        
    def delete(self, name: str):
        """Delete a secret."""
        # Remove from backend
        self._delete_secret(name)
        
        # Remove from cache
        if name in self._cache:
            del self._cache[name]
            
    def list(self) -> List[str]:
        """List all secret names."""
        if self.backend == SecretBackend.ENV:
            prefix = self.config.get("prefix", "AGENTICRAFT_SECRET_")
            return [
                key[len(prefix):] for key in os.environ.keys()
                if key.startswith(prefix)
            ]
        elif self.backend == SecretBackend.FILE:
            secrets_dir = self._get_secrets_dir()
            if secrets_dir.exists():
                return [f.stem for f in secrets_dir.glob("*.secret")]
            return []
        else:
            # Implement for other backends
            return []
            
    def _load_secret(self, name: str) -> Optional[Secret]:
        """Load secret from backend."""
        if self.backend == SecretBackend.ENV:
            return self._load_from_env(name)
        elif self.backend == SecretBackend.FILE:
            return self._load_from_file(name)
        elif self.backend == SecretBackend.AWS_SSM:
            return self._load_from_aws_ssm(name)
        # Add other backends as needed
        else:
            logger.warning(f"Backend {self.backend} not fully implemented")
            return None
            
    def _store_secret(self, secret: Secret):
        """Store secret in backend."""
        if self.backend == SecretBackend.ENV:
            self._store_in_env(secret)
        elif self.backend == SecretBackend.FILE:
            self._store_in_file(secret)
        elif self.backend == SecretBackend.AWS_SSM:
            self._store_in_aws_ssm(secret)
        # Add other backends as needed
        else:
            logger.warning(f"Backend {self.backend} not fully implemented")
            
    def _delete_secret(self, name: str):
        """Delete secret from backend."""
        if self.backend == SecretBackend.ENV:
            prefix = self.config.get("prefix", "AGENTICRAFT_SECRET_")
            env_key = f"{prefix}{name}"
            if env_key in os.environ:
                del os.environ[env_key]
        elif self.backend == SecretBackend.FILE:
            secret_path = self._get_secret_path(name)
            if secret_path.exists():
                secret_path.unlink()
        # Add other backends as needed
        else:
            logger.warning(f"Backend {self.backend} not fully implemented")
            
    # Environment variable backend
    def _load_from_env(self, name: str) -> Optional[Secret]:
        """Load secret from environment variable."""
        prefix = self.config.get("prefix", "AGENTICRAFT_SECRET_")
        env_key = f"{prefix}{name}"
        
        if env_key in os.environ:
            return Secret(name=name, value=os.environ[env_key])
            
        return None
        
    def _store_in_env(self, secret: Secret):
        """Store secret in environment variable."""
        prefix = self.config.get("prefix", "AGENTICRAFT_SECRET_")
        env_key = f"{prefix}{secret.name}"
        os.environ[env_key] = secret.value
        
    # File backend
    def _get_secrets_dir(self) -> Path:
        """Get secrets directory."""
        secrets_dir = self.config.get("secrets_dir", "~/.agenticraft/secrets")
        return Path(os.path.expanduser(secrets_dir))
        
    def _get_secret_path(self, name: str) -> Path:
        """Get path for a specific secret."""
        return self._get_secrets_dir() / f"{name}.secret"
        
    def _load_from_file(self, name: str) -> Optional[Secret]:
        """Load secret from encrypted file."""
        secret_path = self._get_secret_path(name)
        
        if not secret_path.exists():
            return None
            
        try:
            with open(secret_path, "rb") as f:
                encrypted_data = f.read()
                
            # Decrypt
            decrypted_data = self._cipher.decrypt(encrypted_data)
            secret_data = json.loads(decrypted_data.decode())
            
            return Secret(
                name=name,
                value=secret_data["value"],
                metadata=secret_data.get("metadata"),
                encrypted=True
            )
        except Exception as e:
            logger.error(f"Error loading secret '{name}': {e}")
            return None
            
    def _store_in_file(self, secret: Secret):
        """Store secret in encrypted file."""
        secrets_dir = self._get_secrets_dir()
        secrets_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        secret_data = {
            "value": secret.value,
            "metadata": secret.metadata,
        }
        
        # Encrypt
        encrypted_data = self._cipher.encrypt(json.dumps(secret_data).encode())
        
        # Write to file
        secret_path = self._get_secret_path(secret.name)
        with open(secret_path, "wb") as f:
            f.write(encrypted_data)
            
        # Secure the file
        os.chmod(secret_path, 0o600)
        
    # AWS SSM backend (example)
    def _load_from_aws_ssm(self, name: str) -> Optional[Secret]:
        """Load secret from AWS Systems Manager Parameter Store."""
        try:
            import boto3
            
            client = boto3.client("ssm", region_name=self.config.get("aws_region"))
            prefix = self.config.get("prefix", "/agenticraft/")
            
            response = client.get_parameter(
                Name=f"{prefix}{name}",
                WithDecryption=True
            )
            
            return Secret(
                name=name,
                value=response["Parameter"]["Value"],
                metadata={"version": response["Parameter"]["Version"]},
                encrypted=True
            )
        except Exception as e:
            logger.error(f"Error loading secret from AWS SSM: {e}")
            return None
            
    def _store_in_aws_ssm(self, secret: Secret):
        """Store secret in AWS Systems Manager Parameter Store."""
        try:
            import boto3
            
            client = boto3.client("ssm", region_name=self.config.get("aws_region"))
            prefix = self.config.get("prefix", "/agenticraft/")
            
            client.put_parameter(
                Name=f"{prefix}{secret.name}",
                Value=secret.value,
                Type="SecureString",
                Overwrite=True
            )
        except Exception as e:
            logger.error(f"Error storing secret in AWS SSM: {e}")
            raise
            
    # Utility methods
    def rotate_key(self, name: str, new_value: str):
        """
        Rotate a secret value.
        
        Args:
            name: Secret name
            new_value: New secret value
        """
        # Get existing metadata
        existing = self._load_secret(name)
        metadata = existing.metadata if existing else {}
        
        # Update rotation metadata
        metadata["rotated_at"] = datetime.now().isoformat()
        metadata["rotation_count"] = metadata.get("rotation_count", 0) + 1
        
        # Store new value
        self.set(name, new_value, metadata)
        logger.info(f"Rotated secret '{name}'")
        
    def export_env(self, prefix: str = "AGENTICRAFT_") -> Dict[str, str]:
        """
        Export all secrets as environment variables.
        
        Args:
            prefix: Environment variable prefix
            
        Returns:
            Dictionary of environment variables
        """
        env_vars = {}
        
        for name in self.list():
            value = self.get(name)
            if value:
                env_vars[f"{prefix}{name}"] = value
                
        return env_vars
        
    def validate_secrets(self, required: List[str]) -> List[str]:
        """
        Validate that required secrets exist.
        
        Args:
            required: List of required secret names
            
        Returns:
            List of missing secret names
        """
        missing = []
        
        for name in required:
            if self.get(name) is None:
                missing.append(name)
                
        return missing


# Helper functions for common secret patterns
def get_api_key(provider: str, secret_manager: Optional[SecretManager] = None) -> Optional[str]:
    """
    Get API key for a provider.
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic")
        secret_manager: Optional SecretManager instance
        
    Returns:
        API key or None
    """
    if secret_manager:
        # Try secret manager first
        key = secret_manager.get(f"{provider}_api_key")
        if key:
            return key
            
    # Fall back to environment variables
    env_names = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "cohere": "COHERE_API_KEY",
        "huggingface": "HUGGINGFACE_API_KEY",
    }
    
    env_name = env_names.get(provider, f"{provider.upper()}_API_KEY")
    return os.environ.get(env_name)


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """
    Mask a secret value for logging.
    
    Args:
        value: Secret value
        visible_chars: Number of characters to show at start and end
        
    Returns:
        Masked value
    """
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
        
    return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars * 2)}{value[-visible_chars:]}"


# Example secret configuration
EXAMPLE_SECRETS = {
    "required_secrets": [
        "openai_api_key",
        "database_password",
        "jwt_secret",
        "encryption_key",
    ],
    "optional_secrets": [
        "anthropic_api_key",
        "slack_webhook_url",
        "smtp_password",
        "redis_password",
    ],
}
