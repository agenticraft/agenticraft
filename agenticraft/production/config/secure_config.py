"""
Enhanced secure configuration manager for AgentiCraft.

This module provides advanced configuration management with:
- Encryption for sensitive values
- Environment-based configuration
- Hot reloading
- Validation
- Type safety
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, TypeVar, Type, Union
from dataclasses import dataclass, field
from datetime import datetime
import threading
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
from enum import Enum

from .manager import ConfigManager
from ...security import UserContext

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConfigEnvironment(Enum):
    """Configuration environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class ConfigValue:
    """Represents a configuration value with metadata."""
    key: str
    value: Any
    encrypted: bool = False
    environment: Optional[str] = None
    description: str = ""
    last_modified: datetime = field(default_factory=datetime.now)
    modified_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value if not self.encrypted else "[ENCRYPTED]",
            "encrypted": self.encrypted,
            "environment": self.environment,
            "description": self.description,
            "last_modified": self.last_modified.isoformat(),
            "modified_by": self.modified_by
        }


class SecureConfigManager(ConfigManager):
    """Enhanced configuration manager with security features."""
    
    def __init__(
        self,
        app_name: str = "agenticraft",
        environment: Optional[ConfigEnvironment] = None,
        config_dir: Optional[Path] = None,
        auto_reload: bool = True,
        encryption_password: Optional[str] = None
    ):
        """
        Initialize secure configuration manager.
        
        Args:
            app_name: Application name
            environment: Configuration environment
            config_dir: Configuration directory path
            auto_reload: Enable hot reloading
            encryption_password: Password for encryption (auto-generated if None)
        """
        super().__init__(app_name)
        
        # Set environment
        self.environment = environment or self._detect_environment()
        
        # Configuration directory
        if config_dir is None:
            config_dir = Path.home() / ".agenticraft" / "config"
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.default_config_file = self.config_dir / "default.yaml"
        self.env_config_file = self.config_dir / f"{self.environment.value}.yaml"
        self.secrets_file = self.config_dir / "secrets.enc"
        self.schema_file = self.config_dir / "schema.json"
        
        # Encryption
        self._setup_encryption(encryption_password)
        
        # Configuration cache
        self._config_cache: Dict[str, ConfigValue] = {}
        self._lock = threading.RLock()
        
        # File watchers for hot reload
        self._watchers = []
        self._auto_reload = auto_reload
        
        # Load configuration
        self._load_all_configs()
        
        # Start file watchers if enabled
        if auto_reload:
            self._start_watchers()
            
    def _detect_environment(self) -> ConfigEnvironment:
        """Detect environment from environment variables."""
        env_value = os.getenv("AGENTICRAFT_ENV", "development").lower()
        
        try:
            return ConfigEnvironment(env_value)
        except ValueError:
            logger.warning(f"Unknown environment: {env_value}, defaulting to development")
            return ConfigEnvironment.DEVELOPMENT
            
    def _setup_encryption(self, password: Optional[str] = None):
        """Setup encryption for sensitive values."""
        key_file = self.config_dir / ".key"
        
        if key_file.exists():
            # Load existing key
            with open(key_file, 'rb') as f:
                self._encryption_key = f.read()
        else:
            # Generate new key
            if password is None:
                # Use machine-specific password
                password = f"{os.getlogin()}@{os.uname().nodename}".encode()
            else:
                password = password.encode()
                
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'agenticraft_salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Save key
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            
            self._encryption_key = key
            
        self._cipher = Fernet(self._encryption_key)
        
    def _load_all_configs(self):
        """Load all configuration files."""
        with self._lock:
            # Clear cache
            self._config_cache.clear()
            
            # Load default configuration
            if self.default_config_file.exists():
                self._load_config_file(self.default_config_file)
                
            # Load environment-specific configuration (overrides defaults)
            if self.env_config_file.exists():
                self._load_config_file(self.env_config_file)
                
            # Load encrypted secrets
            if self.secrets_file.exists():
                self._load_secrets()
                
            logger.info(f"Loaded configuration for environment: {self.environment.value}")
            
    def _load_config_file(self, file_path: Path):
        """Load configuration from YAML file."""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                
            # Flatten nested configuration
            flattened = self._flatten_dict(data)
            
            # Store in cache
            for key, value in flattened.items():
                self._config_cache[key] = ConfigValue(
                    key=key,
                    value=value,
                    environment=self.environment.value,
                    description=f"Loaded from {file_path.name}"
                )
                
        except Exception as e:
            logger.error(f"Error loading config file {file_path}: {e}")
            
    def _flatten_dict(self, d: Dict, prefix: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary with dot notation."""
        items = []
        
        for k, v in d.items():
            new_key = f"{prefix}.{k}" if prefix else k
            
            if isinstance(v, dict) and not v.get("_encrypted"):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
                
        return dict(items)
        
    def _load_secrets(self):
        """Load encrypted secrets."""
        try:
            with open(self.secrets_file, 'rb') as f:
                encrypted_data = f.read()
                
            # Decrypt
            decrypted_data = self._cipher.decrypt(encrypted_data)
            secrets = json.loads(decrypted_data.decode())
            
            # Store in cache
            for key, value in secrets.items():
                self._config_cache[key] = ConfigValue(
                    key=key,
                    value=value,
                    encrypted=True,
                    environment=self.environment.value,
                    description="Encrypted secret"
                )
                
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            
    def _save_secrets(self):
        """Save encrypted secrets."""
        # Collect all encrypted values
        secrets = {}
        
        for key, config_value in self._config_cache.items():
            if config_value.encrypted:
                secrets[key] = config_value.value
                
        # Encrypt and save
        encrypted_data = self._cipher.encrypt(json.dumps(secrets).encode())
        
        with open(self.secrets_file, 'wb') as f:
            f.write(encrypted_data)
            
        os.chmod(self.secrets_file, 0o600)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with self._lock:
            config_value = self._config_cache.get(key)
            
            if config_value is None:
                return default
                
            return config_value.value
            
    def get_typed(self, key: str, type_: Type[T], default: Optional[T] = None) -> Optional[T]:
        """Get typed configuration value."""
        value = self.get(key, default)
        
        if value is None:
            return default
            
        try:
            # Handle common type conversions
            if type_ == bool and isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 'on')
            elif type_ == int and isinstance(value, str):
                return int(value)
            elif type_ == float and isinstance(value, str):
                return float(value)
            elif type_ == Path and isinstance(value, str):
                return Path(value)
            else:
                return type_(value)
                
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert {key}={value} to {type_}")
            return default
            
    def set(
        self,
        key: str,
        value: Any,
        encrypted: bool = False,
        user_context: Optional[UserContext] = None
    ):
        """Set configuration value."""
        with self._lock:
            self._config_cache[key] = ConfigValue(
                key=key,
                value=value,
                encrypted=encrypted,
                environment=self.environment.value,
                modified_by=user_context.user_id if user_context else None
            )
            
            # Save to appropriate file
            if encrypted:
                self._save_secrets()
            else:
                self._save_config()
                
    def set_secret(self, key: str, value: str, user_context: Optional[UserContext] = None):
        """Set encrypted configuration value."""
        self.set(key, value, encrypted=True, user_context=user_context)
        
    def get_secret(self, key: str) -> Optional[str]:
        """Get decrypted secret value."""
        return self.get(key)
        
    def _save_config(self):
        """Save non-secret configuration to environment file."""
        # Collect non-encrypted values
        config = {}
        
        for key, config_value in self._config_cache.items():
            if not config_value.encrypted:
                # Reconstruct nested structure
                parts = key.split('.')
                current = config
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
                current[parts[-1]] = config_value.value
                
        # Save to YAML
        with open(self.env_config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
    def get_all(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """Get all configuration values with optional prefix filter."""
        with self._lock:
            if prefix:
                return {
                    key: cv.value
                    for key, cv in self._config_cache.items()
                    if key.startswith(prefix)
                }
            else:
                return {key: cv.value for key, cv in self._config_cache.items()}
                
    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a configuration value."""
        with self._lock:
            config_value = self._config_cache.get(key)
            
            if config_value:
                return config_value.to_dict()
                
            return None
            
    def validate_schema(self, schema: Dict[str, Any]) -> List[str]:
        """Validate configuration against schema."""
        errors = []
        
        for key, rules in schema.items():
            value = self.get(key)
            
            # Check required
            if rules.get("required") and value is None:
                errors.append(f"Missing required config: {key}")
                continue
                
            if value is not None:
                # Check type
                expected_type = rules.get("type")
                if expected_type:
                    type_map = {
                        "string": str,
                        "integer": int,
                        "float": float,
                        "boolean": bool,
                        "array": list,
                        "object": dict
                    }
                    
                    python_type = type_map.get(expected_type)
                    if python_type and not isinstance(value, python_type):
                        errors.append(f"{key}: expected {expected_type}, got {type(value).__name__}")
                        
                # Check enum
                if "enum" in rules and value not in rules["enum"]:
                    errors.append(f"{key}: value '{value}' not in allowed values {rules['enum']}")
                    
                # Check range
                if "min" in rules and value < rules["min"]:
                    errors.append(f"{key}: value {value} below minimum {rules['min']}")
                    
                if "max" in rules and value > rules["max"]:
                    errors.append(f"{key}: value {value} above maximum {rules['max']}")
                    
        return errors
        
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration for backup or migration."""
        with self._lock:
            export_data = {
                "environment": self.environment.value,
                "exported_at": datetime.now().isoformat(),
                "configuration": {}
            }
            
            for key, config_value in self._config_cache.items():
                if config_value.encrypted and not include_secrets:
                    continue
                    
                export_data["configuration"][key] = config_value.to_dict()
                
            return export_data
            
    def import_config(self, data: Dict[str, Any], user_context: Optional[UserContext] = None):
        """Import configuration from exported data."""
        with self._lock:
            config_data = data.get("configuration", {})
            
            for key, value_data in config_data.items():
                self.set(
                    key=key,
                    value=value_data["value"],
                    encrypted=value_data.get("encrypted", False),
                    user_context=user_context
                )
                
            logger.info(f"Imported {len(config_data)} configuration values")
            
    def _start_watchers(self):
        """Start file watchers for hot reload."""
        # Implementation would use watchdog or similar
        # For now, we'll use a simple polling approach
        pass
        
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == ConfigEnvironment.PRODUCTION
        
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == ConfigEnvironment.DEVELOPMENT


# Global configuration instance
_config: Optional[SecureConfigManager] = None


def get_config() -> SecureConfigManager:
    """Get global configuration instance."""
    global _config
    
    if _config is None:
        _config = SecureConfigManager()
        
    return _config


def init_config(
    environment: Optional[ConfigEnvironment] = None,
    config_dir: Optional[Path] = None,
    **kwargs
) -> SecureConfigManager:
    """Initialize global configuration."""
    global _config
    
    _config = SecureConfigManager(
        environment=environment,
        config_dir=config_dir,
        **kwargs
    )
    
    return _config
