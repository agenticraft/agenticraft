"""Configuration management for AgentiCraft.

This module provides centralized configuration management using
pydantic-settings. Configuration can be loaded from environment
variables, .env files, or set programmatically.

Example:
    Loading configuration::

        from agenticraft.core.config import settings

        # Access configuration
        print(settings.openai_api_key)
        print(settings.default_model)

        # Override configuration
        settings.default_temperature = 0.5
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentiCraftSettings(BaseSettings):
    """Global settings for AgentiCraft.

    Settings are loaded from (in order of priority):
    1. Environment variables
    2. .env file in current directory
    3. .env file in parent directories
    4. Default values

    All settings can be overridden using environment variables
    with the AGENTICRAFT_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENTICRAFT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # General settings
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Keys
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    google_api_key: str | None = Field(default=None, description="Google API key")

    # Model defaults
    default_model: str = Field(default="gpt-4", description="Default LLM model")
    default_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Default temperature for LLM"
    )
    default_max_tokens: int | None = Field(
        default=None, gt=0, description="Default max tokens for LLM"
    )
    default_timeout: int = Field(
        default=30, gt=0, description="Default timeout in seconds"
    )
    default_max_retries: int = Field(default=3, ge=0, description="Default max retries")

    # Provider settings
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API base URL"
    )
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com", description="Anthropic API base URL"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama base URL"
    )

    # Memory settings
    memory_backend: str = Field(
        default="sqlite", description="Memory backend (sqlite, json, redis)"
    )
    memory_path: Path = Field(
        default=Path("./memory"), description="Path for memory storage"
    )
    conversation_memory_size: int = Field(
        default=10, gt=0, description="Number of conversation turns to keep"
    )

    # Telemetry settings
    telemetry_enabled: bool = Field(default=True, description="Enable telemetry")
    telemetry_service_name: str = Field(
        default="agenticraft", description="Service name for telemetry"
    )
    telemetry_export_endpoint: str | None = Field(
        default=None, description="OTLP endpoint for telemetry export"
    )
    telemetry_sample_rate: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Telemetry sampling rate"
    )

    # Plugin settings
    plugins_enabled: bool = Field(default=True, description="Enable plugin system")
    plugin_dirs: list[Path] = Field(
        default_factory=lambda: [Path("./plugins")],
        description="Directories to load plugins from",
    )

    # MCP settings
    mcp_enabled: bool = Field(default=True, description="Enable Model Context Protocol")
    mcp_servers: list[str] = Field(
        default_factory=list, description="MCP server URLs to connect to"
    )

    # Tool settings
    tool_execution_timeout: int = Field(
        default=10, gt=0, description="Timeout for tool execution in seconds"
    )
    tool_retry_attempts: int = Field(
        default=2, ge=0, description="Number of retry attempts for failed tools"
    )

    # Workflow settings
    workflow_step_timeout: int = Field(
        default=60, gt=0, description="Default timeout for workflow steps in seconds"
    )
    workflow_max_parallel_steps: int = Field(
        default=5, gt=0, description="Maximum parallel steps in workflows"
    )

    # Security settings
    allow_code_execution: bool = Field(
        default=False, description="Allow execution of arbitrary code in tools"
    )
    allowed_domains: set[str] = Field(
        default_factory=set, description="Allowed domains for web requests"
    )

    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = {"development", "staging", "production", "test"}
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v_lower

    @field_validator("memory_backend")
    def validate_memory_backend(cls, v: str) -> str:
        """Validate memory backend."""
        valid_backends = {"sqlite", "json", "redis"}
        v_lower = v.lower()
        if v_lower not in valid_backends:
            raise ValueError(
                f"Invalid memory backend: {v}. Must be one of {valid_backends}"
            )
        return v_lower

    def get_api_key(self, provider: str) -> str | None:
        """Get API key for a provider.

        Args:
            provider: Provider name (openai, anthropic, google)

        Returns:
            API key if available
        """
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
        }
        return key_map.get(provider.lower())

    def get_base_url(self, provider: str) -> str | None:
        """Get base URL for a provider.

        Args:
            provider: Provider name

        Returns:
            Base URL if available
        """
        url_map = {
            "openai": self.openai_base_url,
            "anthropic": self.anthropic_base_url,
            "ollama": self.ollama_base_url,
        }
        return url_map.get(provider.lower())

    def to_agent_config(self) -> dict[str, Any]:
        """Convert settings to agent configuration.

        Returns:
            Dictionary suitable for Agent initialization
        """
        return {
            "model": self.default_model,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
            "timeout": self.default_timeout,
            "max_retries": self.default_max_retries,
        }

    def to_telemetry_config(self) -> dict[str, Any]:
        """Convert settings to telemetry configuration.

        Returns:
            Dictionary suitable for Telemetry initialization
        """
        return {
            "service_name": self.telemetry_service_name,
            "export_to": self.telemetry_export_endpoint,
            "enabled": self.telemetry_enabled,
            "sample_rate": self.telemetry_sample_rate,
        }

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    def validate_required_keys(self, providers: list[str]) -> None:
        """Validate that required API keys are present.

        Args:
            providers: List of providers that need keys

        Raises:
            ValueError: If required keys are missing
        """
        missing = []
        for provider in providers:
            if not self.get_api_key(provider):
                missing.append(provider)

        if missing:
            raise ValueError(
                f"Missing API keys for providers: {', '.join(missing)}. "
                f"Set environment variables or update .env file."
            )


@lru_cache
def get_settings() -> AgentiCraftSettings:
    """Get the global settings instance (cached).

    Returns:
        AgentiCraftSettings instance
    """
    return AgentiCraftSettings()


# Global settings instance
settings = get_settings()


def reload_settings() -> AgentiCraftSettings:
    """Reload settings from environment.

    This clears the cache and creates a new settings instance.
    Useful for testing or when environment variables change.

    Returns:
        New AgentiCraftSettings instance
    """
    get_settings.cache_clear()
    global settings
    settings = get_settings()
    return settings


def update_settings(**kwargs: Any) -> None:
    """Update settings programmatically.

    Args:
        **kwargs: Setting values to update

    Example:
        update_settings(default_model="gpt-3.5-turbo", debug=True)
    """
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
        else:
            raise ValueError(f"Unknown setting: {key}")
