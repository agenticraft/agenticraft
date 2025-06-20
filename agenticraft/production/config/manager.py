"""
Configuration manager for AgentiCraft applications.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """Supported configuration formats."""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"


@dataclass
class ConfigSource:
    """Represents a configuration source."""
    path: str
    format: ConfigFormat
    required: bool = True
    prefix: str = ""  # For environment variables


class ConfigManager:
    """
    Manage application configuration from multiple sources.
    
    Supports loading configuration from:
    - JSON files
    - YAML files
    - Environment variables
    - Default values
    
    Configuration sources are merged in order of priority (later sources override earlier ones).
    """
    
    def __init__(self, app_name: str = "agenticraft"):
        """
        Initialize configuration manager.
        
        Args:
            app_name: Application name (used for environment variable prefix)
        """
        self.app_name = app_name
        self.config: Dict[str, Any] = {}
        self.sources: List[ConfigSource] = []
        self._env_prefix = app_name.upper()
        
    def add_source(self, source: Union[str, ConfigSource], format: ConfigFormat = None, required: bool = True):
        """
        Add a configuration source.
        
        Args:
            source: Path to config file or ConfigSource object
            format: Format of the config file (auto-detected if None)
            required: Whether this source must exist
        """
        if isinstance(source, str):
            if format is None:
                # Auto-detect format from extension
                ext = Path(source).suffix.lower()
                if ext == ".json":
                    format = ConfigFormat.JSON
                elif ext in [".yaml", ".yml"]:
                    format = ConfigFormat.YAML
                else:
                    raise ValueError(f"Cannot auto-detect format for {source}")
                    
            source = ConfigSource(path=source, format=format, required=required)
            
        self.sources.append(source)
        
    def load_defaults(self, defaults: Dict[str, Any]):
        """
        Load default configuration values.
        
        Args:
            defaults: Dictionary of default values
        """
        self.config = self._deep_merge(self.config, defaults)
        logger.info(f"Loaded {len(defaults)} default configuration values")
        
    def load(self):
        """Load configuration from all sources."""
        # Load from files
        for source in self.sources:
            if source.format == ConfigFormat.ENV:
                self._load_from_env(source)
            else:
                self._load_from_file(source)
                
        # Always load environment variable overrides
        self._load_env_overrides()
        
        logger.info(f"Configuration loaded with {len(self.config)} top-level keys")
        
    def _load_from_file(self, source: ConfigSource):
        """Load configuration from a file."""
        path = Path(source.path)
        
        if not path.exists():
            if source.required:
                raise FileNotFoundError(f"Required config file not found: {path}")
            else:
                logger.debug(f"Optional config file not found: {path}")
                return
                
        try:
            with open(path, "r") as f:
                if source.format == ConfigFormat.JSON:
                    data = json.load(f)
                elif source.format == ConfigFormat.YAML:
                    data = yaml.safe_load(f) or {}
                else:
                    raise ValueError(f"Unsupported format: {source.format}")
                    
            self.config = self._deep_merge(self.config, data)
            logger.info(f"Loaded configuration from {path}")
            
        except Exception as e:
            logger.error(f"Error loading config from {path}: {e}")
            if source.required:
                raise
                
    def _load_from_env(self, source: ConfigSource):
        """Load configuration from environment variables."""
        prefix = source.prefix or self._env_prefix
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(f"{prefix}_"):
                # Convert AGENTICRAFT_WORKFLOW_TIMEOUT to workflow.timeout
                config_key = key[len(prefix) + 1:].lower().replace("_", ".")
                env_config[config_key] = self._parse_env_value(value)
                
        # Convert flat keys to nested structure
        nested_config = self._unflatten_dict(env_config)
        self.config = self._deep_merge(self.config, nested_config)
        
        if env_config:
            logger.info(f"Loaded {len(env_config)} values from environment variables")
            
    def _load_env_overrides(self):
        """Load environment variable overrides for existing config keys."""
        overrides = {}
        
        def check_env_override(path: str, value: Any):
            """Check if an environment variable exists for this config path."""
            env_key = f"{self._env_prefix}_{path.upper().replace('.', '_')}"
            if env_key in os.environ:
                overrides[path] = self._parse_env_value(os.environ[env_key])
                
        # Walk through existing config to find overrides
        self._walk_config(self.config, check_env_override)
        
        # Apply overrides
        for path, value in overrides.items():
            self._set_nested_value(self.config, path, value)
            logger.debug(f"Override {path} from environment variable")
            
        if overrides:
            logger.info(f"Applied {len(overrides)} environment variable overrides")
            
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Try to parse as JSON first (handles arrays, objects, booleans, numbers)
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # Return as string
            return value
            
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def _unflatten_dict(self, flat: Dict[str, Any]) -> Dict[str, Any]:
        """Convert flat dictionary with dot notation to nested dictionary."""
        result = {}
        
        for key, value in flat.items():
            parts = key.split(".")
            current = result
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
                
            current[parts[-1]] = value
            
        return result
        
    def _walk_config(self, config: Dict[str, Any], callback: callable, path: str = ""):
        """Walk through configuration calling callback for each value."""
        for key, value in config.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                self._walk_config(value, callback, current_path)
            else:
                callback(current_path, value)
                
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set a value in nested dictionary using dot notation."""
        parts = path.split(".")
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        current[parts[-1]] = value
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Dot-notation key (e.g., "workflow.timeout")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        parts = key.split(".")
        current = self.config
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
                
        return current
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Configuration section as dictionary
        """
        return self.get(section, {})
        
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Dot-notation key
            value: Value to set
        """
        self._set_nested_value(self.config, key, value)
        
    def validate(self, schema: Dict[str, Any] = None) -> List[str]:
        """
        Validate configuration against schema.
        
        Args:
            schema: JSON schema for validation
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic required field validation
        required_fields = [
            "workflows.default_timeout",
            "agents.max_retries",
            "system.log_level",
        ]
        
        for field in required_fields:
            if self.get(field) is None:
                errors.append(f"Required field '{field}' is missing")
                
        # Add custom schema validation if provided
        if schema:
            # This would use jsonschema or similar library
            pass
            
        return errors
        
    def save(self, path: str, format: ConfigFormat = ConfigFormat.YAML):
        """
        Save current configuration to file.
        
        Args:
            path: Output file path
            format: Output format
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            if format == ConfigFormat.JSON:
                json.dump(self.config, f, indent=2)
            elif format == ConfigFormat.YAML:
                yaml.dump(self.config, f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        logger.info(f"Saved configuration to {path}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self.config.copy()
        
    def __repr__(self) -> str:
        """String representation."""
        return f"ConfigManager(app_name='{self.app_name}', keys={list(self.config.keys())})"


# Helper function for common AgentiCraft configuration
def create_agenticraft_config(
    config_files: List[str] = None,
    env_prefix: str = "AGENTICRAFT"
) -> ConfigManager:
    """
    Create a pre-configured ConfigManager for AgentiCraft.
    
    Args:
        config_files: List of configuration files to load
        env_prefix: Environment variable prefix
        
    Returns:
        Configured ConfigManager instance
    """
    config = ConfigManager("agenticraft")
    
    # Load defaults
    defaults = {
        "workflows": {
            "default_timeout": 300,
            "max_retries": 3,
            "retry_delay": 1.0,
        },
        "agents": {
            "max_retries": 3,
            "timeout": 60,
            "max_concurrent_tasks": 10,
        },
        "system": {
            "log_level": "INFO",
            "log_format": "json",
            "metrics_enabled": True,
            "health_check_interval": 60,
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
        },
        "memory": {
            "enabled": False,
            "backend": "redis",
            "ttl": 3600,
        },
        "providers": {
            "default": "openai",
            "openai": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
        },
    }
    
    config.load_defaults(defaults)
    
    # Add default config file locations
    default_files = [
        "/etc/agenticraft/config.yaml",
        "~/.agenticraft/config.yaml",
        "./agenticraft.yaml",
        "./config.yaml",
    ]
    
    # Add user-specified files (higher priority)
    if config_files:
        default_files.extend(config_files)
        
    for file in default_files:
        expanded = os.path.expanduser(file)
        if os.path.exists(expanded):
            config.add_source(expanded, required=False)
            
    # Load all sources
    config.load()
    
    # Validate
    errors = config.validate()
    if errors:
        logger.warning(f"Configuration validation warnings: {errors}")
        
    return config


# Example configuration file templates
EXAMPLE_CONFIG_YAML = """
# AgentiCraft Configuration

workflows:
  default_timeout: 300
  max_retries: 3
  retry_delay: 1.0
  
agents:
  max_retries: 3
  timeout: 60
  max_concurrent_tasks: 10
  
system:
  log_level: INFO
  log_format: json
  metrics_enabled: true
  health_check_interval: 60
  
api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  
memory:
  enabled: true
  backend: redis
  redis:
    host: localhost
    port: 6379
    db: 0
  ttl: 3600
  
providers:
  default: openai
  openai:
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 2000
  anthropic:
    model: claude-2
    temperature: 0.7
    max_tokens: 2000
    
monitoring:
  prometheus:
    enabled: true
    port: 9090
  health_check:
    enabled: true
    path: /health
"""
