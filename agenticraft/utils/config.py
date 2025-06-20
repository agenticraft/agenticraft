"""Utilities for managing AgentiCraft configuration.

This module provides helper functions for configuration management,
including environment setup, validation, and initialization.

Example:
    Setting up configuration::

        from agenticraft.utils.config import setup_environment, validate_config

        # Set up from .env file
        setup_environment()

        # Validate configuration
        validate_config(providers=["openai"])
"""

from pathlib import Path

from dotenv import load_dotenv

from ..core.config import reload_settings, settings


def setup_environment(env_file: str | None = None, override: bool = True) -> bool:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file (defaults to searching for .env)
        override: Whether to override existing environment variables

    Returns:
        True if a .env file was loaded

    Example:
        setup_environment(".env.production")
    """
    if env_file:
        return load_dotenv(env_file, override=override)
    else:
        # Search for .env file in current and parent directories
        current = Path.cwd()
        while current != current.parent:
            env_path = current / ".env"
            if env_path.exists():
                return load_dotenv(env_path, override=override)
            current = current.parent

        # Try default location
        return load_dotenv(override=override)


def validate_config(
    providers: list[str] | None = None, require_telemetry: bool = False
) -> None:
    """Validate that configuration is properly set up.

    Args:
        providers: List of providers that need API keys
        require_telemetry: Whether telemetry configuration is required

    Raises:
        ValueError: If configuration is invalid

    Example:
        validate_config(providers=["openai", "anthropic"])
    """
    errors = []

    # Check API keys for requested providers
    if providers:
        for provider in providers:
            if not settings.get_api_key(provider):
                errors.append(f"Missing API key for {provider}")

    # Check telemetry if required
    if require_telemetry and settings.telemetry_enabled:
        if not settings.telemetry_export_endpoint:
            errors.append("Telemetry enabled but no export endpoint configured")

    # Check memory path exists
    if not settings.memory_path.exists():
        try:
            settings.memory_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create memory path: {e}")

    # Check plugin directories
    for plugin_dir in settings.plugin_dirs:
        if not plugin_dir.exists():
            try:
                plugin_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create plugin directory {plugin_dir}: {e}")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n"
            + "\n".join(f"  - {error}" for error in errors)
        )


def init_from_env(
    env_file: str | None = None, providers: list[str] | None = None
) -> None:
    """Initialize AgentiCraft from environment variables.

    This is a convenience function that:
    1. Loads environment variables from .env file
    2. Reloads settings
    3. Validates configuration

    Args:
        env_file: Path to .env file
        providers: Providers that need API keys

    Example:
        init_from_env(providers=["openai"])
    """
    # Load environment
    setup_environment(env_file)

    # Reload settings to pick up new environment variables
    reload_settings()

    # Validate
    validate_config(providers=providers)


def get_config_info() -> dict[str, any]:
    """Get information about current configuration.

    Returns:
        Dictionary with configuration information
    """
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "providers_configured": {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "google": bool(settings.google_api_key),
        },
        "default_model": settings.default_model,
        "telemetry_enabled": settings.telemetry_enabled,
        "memory_backend": settings.memory_backend,
        "plugins_enabled": settings.plugins_enabled,
        "mcp_enabled": settings.mcp_enabled,
    }


def create_env_template(path: str = ".env.example") -> None:
    """Create a template .env file with all available settings.

    Args:
        path: Path to create the template file
    """
    template = """# AgentiCraft Configuration
# Copy this file to .env and update with your values

# Environment
AGENTICRAFT_ENVIRONMENT=development
AGENTICRAFT_DEBUG=false
AGENTICRAFT_LOG_LEVEL=INFO

# API Keys
AGENTICRAFT_OPENAI_API_KEY=your-openai-key-here
AGENTICRAFT_ANTHROPIC_API_KEY=your-anthropic-key-here
AGENTICRAFT_GOOGLE_API_KEY=your-google-key-here

# Model Defaults
AGENTICRAFT_DEFAULT_MODEL=gpt-4
AGENTICRAFT_DEFAULT_TEMPERATURE=0.7
AGENTICRAFT_DEFAULT_MAX_TOKENS=
AGENTICRAFT_DEFAULT_TIMEOUT=30
AGENTICRAFT_DEFAULT_MAX_RETRIES=3

# Provider URLs (optional)
AGENTICRAFT_OPENAI_BASE_URL=https://api.openai.com/v1
AGENTICRAFT_ANTHROPIC_BASE_URL=https://api.anthropic.com
AGENTICRAFT_OLLAMA_BASE_URL=http://localhost:11434

# Memory Settings
AGENTICRAFT_MEMORY_BACKEND=sqlite
AGENTICRAFT_MEMORY_PATH=./memory
AGENTICRAFT_CONVERSATION_MEMORY_SIZE=10

# Telemetry
AGENTICRAFT_TELEMETRY_ENABLED=true
AGENTICRAFT_TELEMETRY_SERVICE_NAME=agenticraft
AGENTICRAFT_TELEMETRY_EXPORT_ENDPOINT=http://localhost:4317
AGENTICRAFT_TELEMETRY_SAMPLE_RATE=1.0

# Plugins
AGENTICRAFT_PLUGINS_ENABLED=true
AGENTICRAFT_PLUGIN_DIRS=["./plugins"]

# MCP (Model Context Protocol)
AGENTICRAFT_MCP_ENABLED=true
AGENTICRAFT_MCP_SERVERS=[]

# Tool Settings
AGENTICRAFT_TOOL_EXECUTION_TIMEOUT=10
AGENTICRAFT_TOOL_RETRY_ATTEMPTS=2

# Workflow Settings
AGENTICRAFT_WORKFLOW_STEP_TIMEOUT=60
AGENTICRAFT_WORKFLOW_MAX_PARALLEL_STEPS=5

# Security
AGENTICRAFT_ALLOW_CODE_EXECUTION=false
AGENTICRAFT_ALLOWED_DOMAINS=[]
"""

    with open(path, "w") as f:
        f.write(template)

    print(f"Created environment template at {path}")
