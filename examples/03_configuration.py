#!/usr/bin/env python3
"""Configuration example for AgentiCraft.

This example demonstrates how to use and manage configuration
in AgentiCraft applications.
"""

from agenticraft.core.config import settings, update_settings
from agenticraft.utils.config import (
    setup_environment,
    validate_config,
    get_config_info,
    create_env_template
)


def main():
    """Run configuration example."""
    print("AgentiCraft Configuration Example")
    print("=" * 40)
    
    # Show current configuration info
    print("\nCurrent Configuration:")
    config_info = get_config_info()
    for key, value in config_info.items():
        print(f"  {key}: {value}")
    
    # Access specific settings
    print("\nSpecific Settings:")
    print(f"  Default Model: {settings.default_model}")
    print(f"  Default Temperature: {settings.default_temperature}")
    print(f"  Memory Backend: {settings.memory_backend}")
    print(f"  Conversation Memory Size: {settings.conversation_memory_size}")
    
    # Check API keys
    print("\nAPI Key Status:")
    print(f"  OpenAI: {'✓' if settings.openai_api_key else '✗'}")
    print(f"  Anthropic: {'✓' if settings.anthropic_api_key else '✗'}")
    print(f"  Google: {'✓' if settings.google_api_key else '✗'}")
    
    # Update settings programmatically
    print("\nUpdating settings programmatically...")
    update_settings(
        default_model="gpt-3.5-turbo",
        default_temperature=0.5,
        debug=True
    )
    
    print("Updated settings:")
    print(f"  Default Model: {settings.default_model}")
    print(f"  Default Temperature: {settings.default_temperature}")
    print(f"  Debug: {settings.debug}")
    
    # Environment setup example
    print("\nEnvironment Setup:")
    print("To use .env files:")
    print("  1. Create a .env file with your settings")
    print("  2. Call setup_environment() to load it")
    print("  3. Call validate_config() to check everything is set")
    
    # Create template if it doesn't exist
    from pathlib import Path
    if not Path(".env.example").exists():
        print("\nCreating .env.example template...")
        create_env_template()
    
    # Validation example
    print("\nConfiguration Validation:")
    try:
        # This will fail if OpenAI key is not set
        validate_config(providers=["openai"])
        print("  ✓ Configuration valid for OpenAI")
    except ValueError as e:
        print(f"  ✗ Validation error: {e}")
    
    # Settings for different environments
    print("\nEnvironment-specific settings:")
    if settings.is_development:
        print("  Running in DEVELOPMENT mode")
        print("  - Debug enabled")
        print("  - Verbose logging")
    elif settings.is_production:
        print("  Running in PRODUCTION mode")
        print("  - Debug disabled")
        print("  - Optimized settings")


if __name__ == "__main__":
    main()
