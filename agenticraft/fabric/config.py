"""
Fabric configuration for AgentiCraft.

This module provides configuration management for the
fabric abstraction layer.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json
import yaml
from pathlib import Path


@dataclass
class FabricConfig:
    """Configuration for fabric layer."""
    
    # Agent defaults
    default_registry: str = "memory"  # memory, distributed
    default_transport_timeout: float = 30.0
    default_auth_type: str = "none"
    
    # Protocol defaults
    mcp_version: str = "1.0"
    a2a_default_pattern: str = "mesh"
    
    # Bridge configuration
    enable_auto_bridging: bool = True
    bridge_cache_size: int = 1000
    
    # Gateway configuration
    gateway_enabled: bool = False
    gateway_port: int = 8888
    
    # Logging
    log_level: str = "INFO"
    log_protocol_messages: bool = False
    
    # Performance
    max_concurrent_requests: int = 100
    request_pool_size: int = 10
    
    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FabricConfig":
        """Create config from dictionary."""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })
        
    @classmethod
    def from_file(cls, path: Path) -> "FabricConfig":
        """Load config from file."""
        path = Path(path)
        
        if path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)
        elif path.suffix in (".yaml", ".yml"):
            with open(path) as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
            
        return cls.from_dict(data)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "default_registry": self.default_registry,
            "default_transport_timeout": self.default_transport_timeout,
            "default_auth_type": self.default_auth_type,
            "mcp_version": self.mcp_version,
            "a2a_default_pattern": self.a2a_default_pattern,
            "enable_auto_bridging": self.enable_auto_bridging,
            "bridge_cache_size": self.bridge_cache_size,
            "gateway_enabled": self.gateway_enabled,
            "gateway_port": self.gateway_port,
            "log_level": self.log_level,
            "log_protocol_messages": self.log_protocol_messages,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_pool_size": self.request_pool_size,
            "custom": self.custom
        }
        
    def save(self, path: Path) -> None:
        """Save config to file."""
        path = Path(path)
        data = self.to_dict()
        
        if path.suffix == ".json":
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        elif path.suffix in (".yaml", ".yml"):
            with open(path, "w") as f:
                yaml.dump(data, f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
            
    def merge(self, other: "FabricConfig") -> "FabricConfig":
        """Merge with another config."""
        merged_data = self.to_dict()
        other_data = other.to_dict()
        
        # Deep merge custom settings
        merged_data["custom"].update(other_data.get("custom", {}))
        
        # Update other fields
        for key, value in other_data.items():
            if key != "custom":
                merged_data[key] = value
                
        return FabricConfig.from_dict(merged_data)
        
    def validate(self) -> List[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate registry type
        if self.default_registry not in ("memory", "distributed"):
            errors.append(f"Invalid registry type: {self.default_registry}")
            
        # Validate auth type
        valid_auth_types = ("none", "api_key", "bearer", "basic", "hmac", "jwt")
        if self.default_auth_type not in valid_auth_types:
            errors.append(f"Invalid auth type: {self.default_auth_type}")
            
        # Validate A2A pattern
        valid_patterns = ("mesh", "centralized", "decentralized", "pubsub")
        if self.a2a_default_pattern not in valid_patterns:
            errors.append(f"Invalid A2A pattern: {self.a2a_default_pattern}")
            
        # Validate log level
        valid_log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.log_level not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}")
            
        # Validate numeric values
        if self.default_transport_timeout <= 0:
            errors.append("Transport timeout must be positive")
            
        if self.bridge_cache_size < 0:
            errors.append("Bridge cache size must be non-negative")
            
        if self.max_concurrent_requests <= 0:
            errors.append("Max concurrent requests must be positive")
            
        if self.request_pool_size <= 0:
            errors.append("Request pool size must be positive")
            
        return errors


# Global configuration instance
_global_config = FabricConfig()


def get_config() -> FabricConfig:
    """Get global fabric configuration."""
    return _global_config


def set_config(config: FabricConfig) -> None:
    """Set global fabric configuration."""
    global _global_config
    _global_config = config


def load_config(path: Path) -> FabricConfig:
    """Load and set global configuration from file."""
    config = FabricConfig.from_file(path)
    set_config(config)
    return config
