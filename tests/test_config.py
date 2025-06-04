"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from agenticraft.core.config import (
    AgentiCraftSettings,
    get_settings,
    reload_settings,
    update_settings,
)


class TestAgentiCraftSettings:
    """Test the AgentiCraftSettings class."""
    
    def test_default_settings(self, clean_settings):
        """Test default settings values."""
        settings = get_settings()
        
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.default_model == "gpt-4"
        assert settings.default_temperature == 0.7
        assert settings.default_timeout == 30
        assert settings.telemetry_enabled is True
    
    def test_environment_override(self, clean_settings):
        """Test environment variable override."""
        os.environ["AGENTICRAFT_ENVIRONMENT"] = "production"
        os.environ["AGENTICRAFT_DEBUG"] = "true"
        os.environ["AGENTICRAFT_DEFAULT_MODEL"] = "gpt-3.5-turbo"
        
        settings = reload_settings()
        
        assert settings.environment == "production"
        assert settings.debug is True
        assert settings.default_model == "gpt-3.5-turbo"
    
    def test_api_key_loading(self, clean_settings):
        """Test API key loading from environment."""
        test_keys = {
            "AGENTICRAFT_OPENAI_API_KEY": "sk-test-openai",
            "AGENTICRAFT_ANTHROPIC_API_KEY": "sk-ant-test",
            "AGENTICRAFT_GOOGLE_API_KEY": "google-test-key"
        }
        
        for key, value in test_keys.items():
            os.environ[key] = value
        
        settings = reload_settings()
        
        assert settings.openai_api_key == "sk-test-openai"
        assert settings.anthropic_api_key == "sk-ant-test"
        assert settings.google_api_key == "google-test-key"
        
        # Test get_api_key method
        assert settings.get_api_key("openai") == "sk-test-openai"
        assert settings.get_api_key("anthropic") == "sk-ant-test"
        assert settings.get_api_key("google") == "google-test-key"
        assert settings.get_api_key("unknown") is None
    
    def test_validation(self, clean_settings):
        """Test settings validation."""
        # Test invalid log level
        os.environ["AGENTICRAFT_LOG_LEVEL"] = "INVALID"
        with pytest.raises(ValueError, match="Invalid log level"):
            reload_settings()
        
        # Test invalid environment
        os.environ["AGENTICRAFT_LOG_LEVEL"] = "INFO"  # Reset
        os.environ["AGENTICRAFT_ENVIRONMENT"] = "invalid"
        with pytest.raises(ValueError, match="Invalid environment"):
            reload_settings()
        
        # Test invalid memory backend
        os.environ["AGENTICRAFT_ENVIRONMENT"] = "development"  # Reset
        os.environ["AGENTICRAFT_MEMORY_BACKEND"] = "invalid"
        with pytest.raises(ValueError, match="Invalid memory backend"):
            reload_settings()
    
    def test_update_settings(self, clean_settings):
        """Test programmatic settings update."""
        settings = get_settings()
        
        # Update settings
        update_settings(
            default_model="claude-3",
            default_temperature=0.5,
            debug=True
        )
        
        assert settings.default_model == "claude-3"
        assert settings.default_temperature == 0.5
        assert settings.debug is True
        
        # Test invalid setting
        with pytest.raises(ValueError, match="Unknown setting"):
            update_settings(invalid_setting="value")
    
    def test_base_urls(self, clean_settings):
        """Test provider base URL configuration."""
        settings = get_settings()
        
        assert settings.get_base_url("openai") == "https://api.openai.com/v1"
        assert settings.get_base_url("anthropic") == "https://api.anthropic.com"
        assert settings.get_base_url("ollama") == "http://localhost:11434"
        assert settings.get_base_url("unknown") is None
    
    def test_is_environment_helpers(self, clean_settings):
        """Test environment helper properties."""
        settings = get_settings()
        
        # Default is development
        assert settings.is_development is True
        assert settings.is_production is False
        
        # Change to production
        os.environ["AGENTICRAFT_ENVIRONMENT"] = "production"
        settings = reload_settings()
        
        assert settings.is_development is False
        assert settings.is_production is True
    
    def test_to_agent_config(self, clean_settings):
        """Test conversion to agent configuration."""
        settings = get_settings()
        agent_config = settings.to_agent_config()
        
        assert agent_config["model"] == settings.default_model
        assert agent_config["temperature"] == settings.default_temperature
        assert agent_config["max_tokens"] == settings.default_max_tokens
        assert agent_config["timeout"] == settings.default_timeout
        assert agent_config["max_retries"] == settings.default_max_retries
    
    def test_to_telemetry_config(self, clean_settings):
        """Test conversion to telemetry configuration."""
        settings = get_settings()
        telemetry_config = settings.to_telemetry_config()
        
        assert telemetry_config["service_name"] == settings.telemetry_service_name
        assert telemetry_config["export_to"] == settings.telemetry_export_endpoint
        assert telemetry_config["enabled"] == settings.telemetry_enabled
        assert telemetry_config["sample_rate"] == settings.telemetry_sample_rate
    
    def test_validate_required_keys(self, clean_settings):
        """Test API key validation."""
        settings = get_settings()
        
        # Should fail without keys
        with pytest.raises(ValueError, match="Missing API keys"):
            settings.validate_required_keys(["openai", "anthropic"])
        
        # Set one key
        os.environ["AGENTICRAFT_OPENAI_API_KEY"] = "sk-test"
        settings = reload_settings()
        
        # Should still fail for anthropic
        with pytest.raises(ValueError, match="anthropic"):
            settings.validate_required_keys(["openai", "anthropic"])
        
        # Should pass for just openai
        settings.validate_required_keys(["openai"])  # No exception
    
    def test_path_settings(self, clean_settings, temp_dir):
        """Test path-based settings."""
        os.environ["AGENTICRAFT_MEMORY_PATH"] = str(temp_dir / "memory")
        os.environ["AGENTICRAFT_PLUGIN_DIRS"] = f'["{temp_dir / "plugins"}"]'
        
        settings = reload_settings()
        
        assert settings.memory_path == temp_dir / "memory"
        assert settings.plugin_dirs == [temp_dir / "plugins"]
