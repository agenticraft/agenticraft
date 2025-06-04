"""Test configuration system integration."""

import os
import tempfile
from pathlib import Path

import pytest

from agenticraft.core.config import (
    AgentiCraftSettings,
    get_settings,
    reload_settings,
    update_settings
)


def test_settings_from_env(monkeypatch):
    """Test settings load from environment variables."""
    # Set test environment variables
    monkeypatch.setenv("AGENTICRAFT_DEBUG", "true")
    monkeypatch.setenv("AGENTICRAFT_DEFAULT_MODEL", "gpt-3.5-turbo")
    monkeypatch.setenv("AGENTICRAFT_DEFAULT_TEMPERATURE", "0.5")
    
    # Reload settings to pick up env vars
    settings = reload_settings()
    
    assert settings.debug is True
    assert settings.default_model == "gpt-3.5-turbo"
    assert settings.default_temperature == 0.5


def test_settings_validation():
    """Test settings validation."""
    # Valid settings should work
    settings = AgentiCraftSettings(
        environment="development",
        log_level="INFO",
        default_temperature=0.7
    )
    assert settings.environment == "development"
    
    # Invalid values should raise errors
    with pytest.raises(ValueError, match="Invalid environment"):
        AgentiCraftSettings(environment="invalid")
    
    with pytest.raises(ValueError, match="Invalid log level"):
        AgentiCraftSettings(log_level="INVALID")


def test_update_settings():
    """Test programmatic settings update."""
    settings = get_settings()
    original_model = settings.default_model
    
    # Update settings
    update_settings(default_model="claude-3", debug=True)
    
    assert settings.default_model == "claude-3"
    assert settings.debug is True
    
    # Restore original
    update_settings(default_model=original_model, debug=False)


def test_api_key_helpers():
    """Test API key helper methods."""
    settings = AgentiCraftSettings(
        openai_api_key="test-openai",
        anthropic_api_key="test-anthropic"
    )
    
    assert settings.get_api_key("openai") == "test-openai"
    assert settings.get_api_key("anthropic") == "test-anthropic"
    assert settings.get_api_key("unknown") is None


def test_config_conversions():
    """Test configuration conversion methods."""
    settings = AgentiCraftSettings(
        default_model="gpt-4",
        default_temperature=0.8,
        telemetry_enabled=True,
        telemetry_service_name="test-service"
    )
    
    # Test agent config conversion
    agent_config = settings.to_agent_config()
    assert agent_config["model"] == "gpt-4"
    assert agent_config["temperature"] == 0.8
    
    # Test telemetry config conversion
    telemetry_config = settings.to_telemetry_config()
    assert telemetry_config["service_name"] == "test-service"
    assert telemetry_config["enabled"] is True


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
