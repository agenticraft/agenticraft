"""
Environment-specific configuration for AgentiCraft.
"""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"
    LOCAL = "local"


@dataclass
class EnvironmentSettings:
    """Settings specific to an environment."""
    name: Environment
    debug: bool = False
    log_level: str = "INFO"
    api_timeout: int = 300
    max_workers: int = 4
    enable_metrics: bool = True
    enable_health_checks: bool = True
    allowed_origins: List[str] = field(default_factory=list)
    features: Dict[str, bool] = field(default_factory=dict)


class EnvironmentConfig:
    """
    Manage environment-specific configuration for AgentiCraft.
    
    Provides different settings for development, staging, and production environments.
    """
    
    # Default settings for each environment
    ENVIRONMENT_DEFAULTS = {
        Environment.DEVELOPMENT: EnvironmentSettings(
            name=Environment.DEVELOPMENT,
            debug=True,
            log_level="DEBUG",
            api_timeout=600,
            max_workers=2,
            enable_metrics=False,
            enable_health_checks=True,
            allowed_origins=["http://localhost:*", "http://127.0.0.1:*"],
            features={
                "experimental": True,
                "rate_limiting": False,
                "authentication": False,
                "caching": False,
            }
        ),
        Environment.STAGING: EnvironmentSettings(
            name=Environment.STAGING,
            debug=False,
            log_level="INFO",
            api_timeout=300,
            max_workers=4,
            enable_metrics=True,
            enable_health_checks=True,
            allowed_origins=["https://*.staging.example.com"],
            features={
                "experimental": True,
                "rate_limiting": True,
                "authentication": True,
                "caching": True,
            }
        ),
        Environment.PRODUCTION: EnvironmentSettings(
            name=Environment.PRODUCTION,
            debug=False,
            log_level="WARNING",
            api_timeout=300,
            max_workers=8,
            enable_metrics=True,
            enable_health_checks=True,
            allowed_origins=["https://*.example.com"],
            features={
                "experimental": False,
                "rate_limiting": True,
                "authentication": True,
                "caching": True,
            }
        ),
        Environment.TEST: EnvironmentSettings(
            name=Environment.TEST,
            debug=True,
            log_level="DEBUG",
            api_timeout=60,
            max_workers=1,
            enable_metrics=False,
            enable_health_checks=False,
            allowed_origins=["*"],
            features={
                "experimental": True,
                "rate_limiting": False,
                "authentication": False,
                "caching": False,
            }
        ),
        Environment.LOCAL: EnvironmentSettings(
            name=Environment.LOCAL,
            debug=True,
            log_level="DEBUG",
            api_timeout=600,
            max_workers=2,
            enable_metrics=False,
            enable_health_checks=True,
            allowed_origins=["*"],
            features={
                "experimental": True,
                "rate_limiting": False,
                "authentication": False,
                "caching": False,
            }
        ),
    }
    
    def __init__(self, env: Optional[str] = None):
        """
        Initialize environment configuration.
        
        Args:
            env: Environment name (auto-detected if None)
        """
        self.environment = self._detect_environment(env)
        self.settings = self._load_settings()
        self._overrides: Dict[str, Any] = {}
        
    def _detect_environment(self, env: Optional[str] = None) -> Environment:
        """Detect current environment."""
        if env:
            env_lower = env.lower()
        else:
            # Check environment variables
            env_lower = os.environ.get("AGENTICRAFT_ENV", "").lower()
            if not env_lower:
                env_lower = os.environ.get("ENVIRONMENT", "").lower()
            if not env_lower:
                env_lower = os.environ.get("ENV", "").lower()
                
        # Map to Environment enum
        env_map = {
            "dev": Environment.DEVELOPMENT,
            "development": Environment.DEVELOPMENT,
            "staging": Environment.STAGING,
            "stg": Environment.STAGING,
            "prod": Environment.PRODUCTION,
            "production": Environment.PRODUCTION,
            "test": Environment.TEST,
            "testing": Environment.TEST,
            "local": Environment.LOCAL,
        }
        
        detected = env_map.get(env_lower, Environment.LOCAL)
        logger.info(f"Detected environment: {detected.value}")
        
        return detected
        
    def _load_settings(self) -> EnvironmentSettings:
        """Load settings for current environment."""
        # Start with defaults
        settings = self.ENVIRONMENT_DEFAULTS.get(
            self.environment,
            self.ENVIRONMENT_DEFAULTS[Environment.LOCAL]
        )
        
        # Load environment-specific overrides from file if exists
        config_file = self._get_env_config_file()
        if config_file and config_file.exists():
            import yaml
            
            try:
                with open(config_file, "r") as f:
                    overrides = yaml.safe_load(f) or {}
                    
                # Apply overrides
                for key, value in overrides.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                        
                logger.info(f"Loaded environment config from {config_file}")
            except Exception as e:
                logger.error(f"Error loading environment config: {e}")
                
        return settings
        
    def _get_env_config_file(self) -> Optional[Path]:
        """Get path to environment-specific config file."""
        # Look in standard locations
        locations = [
            f"./config/{self.environment.value}.yaml",
            f"~/.agenticraft/{self.environment.value}.yaml",
            f"/etc/agenticraft/{self.environment.value}.yaml",
        ]
        
        for location in locations:
            path = Path(os.path.expanduser(location))
            if path.exists():
                return path
                
        return None
        
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION
        
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment in [Environment.DEVELOPMENT, Environment.LOCAL]
        
    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == Environment.TEST
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        # Check overrides first
        if key in self._overrides:
            return self._overrides[key]
            
        # Check settings
        if hasattr(self.settings, key):
            return getattr(self.settings, key)
            
        return default
        
    def set(self, key: str, value: Any):
        """
        Set configuration override.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self._overrides[key] = value
        
    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature: Feature name
            
        Returns:
            True if feature is enabled
        """
        return self.settings.features.get(feature, False)
        
    def enable_feature(self, feature: str):
        """Enable a feature."""
        self.settings.features[feature] = True
        
    def disable_feature(self, feature: str):
        """Disable a feature."""
        self.settings.features[feature] = False
        
    def get_database_url(self) -> str:
        """Get database URL for current environment."""
        # Environment-specific database URLs
        db_urls = {
            Environment.DEVELOPMENT: "postgresql://agenticraft:dev@localhost/agenticraft_dev",
            Environment.TEST: "sqlite:///test.db",
            Environment.STAGING: os.environ.get(
                "DATABASE_URL",
                "postgresql://agenticraft:staging@db-staging/agenticraft_staging"
            ),
            Environment.PRODUCTION: os.environ.get(
                "DATABASE_URL",
                "postgresql://agenticraft:prod@db-prod/agenticraft"
            ),
            Environment.LOCAL: "sqlite:///agenticraft.db",
        }
        
        return db_urls.get(self.environment, db_urls[Environment.LOCAL])
        
    def get_redis_url(self) -> str:
        """Get Redis URL for current environment."""
        redis_urls = {
            Environment.DEVELOPMENT: "redis://localhost:6379/0",
            Environment.TEST: "redis://localhost:6379/15",
            Environment.STAGING: os.environ.get(
                "REDIS_URL",
                "redis://redis-staging:6379/0"
            ),
            Environment.PRODUCTION: os.environ.get(
                "REDIS_URL",
                "redis://redis-prod:6379/0"
            ),
            Environment.LOCAL: "redis://localhost:6379/0",
        }
        
        return redis_urls.get(self.environment, redis_urls[Environment.LOCAL])
        
    def get_api_base_url(self) -> str:
        """Get API base URL for current environment."""
        api_urls = {
            Environment.DEVELOPMENT: "http://localhost:8000",
            Environment.TEST: "http://localhost:8001",
            Environment.STAGING: "https://api-staging.example.com",
            Environment.PRODUCTION: "https://api.example.com",
            Environment.LOCAL: "http://localhost:8000",
        }
        
        return api_urls.get(self.environment, api_urls[Environment.LOCAL])
        
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "environment": self.environment.value,
            "debug": self.settings.debug,
            "log_level": self.settings.log_level,
            "api_timeout": self.settings.api_timeout,
            "max_workers": self.settings.max_workers,
            "enable_metrics": self.settings.enable_metrics,
            "enable_health_checks": self.settings.enable_health_checks,
            "allowed_origins": self.settings.allowed_origins,
            "features": self.settings.features,
            "database_url": self.get_database_url(),
            "redis_url": self.get_redis_url(),
            "api_base_url": self.get_api_base_url(),
            "overrides": self._overrides,
        }
        
    def validate(self) -> List[str]:
        """
        Validate environment configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Production-specific validations
        if self.is_production:
            if self.settings.debug:
                errors.append("Debug mode should be disabled in production")
                
            if self.settings.log_level == "DEBUG":
                errors.append("Log level should not be DEBUG in production")
                
            if "*" in self.settings.allowed_origins:
                errors.append("Wildcard origins not allowed in production")
                
            if self.settings.features.get("experimental", False):
                errors.append("Experimental features should be disabled in production")
                
        # General validations
        if self.settings.max_workers < 1:
            errors.append("max_workers must be at least 1")
            
        if self.settings.api_timeout < 1:
            errors.append("api_timeout must be positive")
            
        return errors
        
    def __repr__(self) -> str:
        """String representation."""
        return f"EnvironmentConfig(environment={self.environment.value})"


# Helper function to get current environment config
_env_config: Optional[EnvironmentConfig] = None


def get_environment_config() -> EnvironmentConfig:
    """Get or create global environment configuration."""
    global _env_config
    
    if _env_config is None:
        _env_config = EnvironmentConfig()
        
    return _env_config


def reset_environment_config(env: Optional[str] = None):
    """Reset global environment configuration."""
    global _env_config
    _env_config = EnvironmentConfig(env)
    return _env_config


# Environment-specific decorators
def production_only(func):
    """Decorator to ensure function only runs in production."""
    def wrapper(*args, **kwargs):
        config = get_environment_config()
        if not config.is_production:
            logger.warning(f"{func.__name__} is production-only, skipping in {config.environment.value}")
            return None
        return func(*args, **kwargs)
    return wrapper


def development_only(func):
    """Decorator to ensure function only runs in development."""
    def wrapper(*args, **kwargs):
        config = get_environment_config()
        if not config.is_development:
            logger.warning(f"{func.__name__} is development-only, skipping in {config.environment.value}")
            return None
        return func(*args, **kwargs)
    return wrapper


def feature_required(feature: str):
    """Decorator to ensure feature is enabled."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            config = get_environment_config()
            if not config.is_feature_enabled(feature):
                logger.warning(f"{func.__name__} requires feature '{feature}' which is disabled")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
