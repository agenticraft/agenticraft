"""Comprehensive tests for utils/config module."""

import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest
from dotenv import load_dotenv

from agenticraft.utils.config import (
    setup_environment, validate_config, init_from_env,
    get_config_info, create_env_template
)
from agenticraft.core.config import settings


class TestSetupEnvironment:
    """Test environment setup functionality."""
    
    def test_setup_environment_with_file(self, tmp_path):
        """Test loading environment from specific file."""
        env_file = tmp_path / ".env.test"
        env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value")
        
        with patch.dict(os.environ, {}, clear=True):
            result = setup_environment(str(env_file))
            
            assert result is True
            assert os.environ.get("TEST_VAR") == "test_value"
            assert os.environ.get("ANOTHER_VAR") == "another_value"
    
    def test_setup_environment_no_override(self, tmp_path):
        """Test loading environment without overriding existing vars."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=new_value")
        
        with patch.dict(os.environ, {"TEST_VAR": "existing_value"}):
            result = setup_environment(str(env_file), override=False)
            
            assert result is True
            assert os.environ.get("TEST_VAR") == "existing_value"  # Not overridden
    
    def test_setup_environment_search_parent_dirs(self, tmp_path):
        """Test searching for .env in parent directories."""
        # Create directory structure
        parent = tmp_path / "parent"
        child = parent / "child"
        child.mkdir(parents=True)
        
        # Put .env in parent
        env_file = parent / ".env"
        env_file.write_text("FOUND_IN_PARENT=yes")
        
        # Change to child directory
        original_cwd = Path.cwd()
        try:
            os.chdir(child)
            
            with patch.dict(os.environ, {}, clear=True):
                result = setup_environment()
                
                assert result is True
                assert os.environ.get("FOUND_IN_PARENT") == "yes"
        finally:
            os.chdir(original_cwd)
    
    def test_setup_environment_no_env_file(self, tmp_path):
        """Test when no .env file is found."""
        # Change to temp directory with no .env
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            
            with patch('dotenv.load_dotenv', return_value=False) as mock_load:
                result = setup_environment()
                
                assert result is False
                # Should still try default location
                mock_load.assert_called()
        finally:
            os.chdir(original_cwd)


class TestValidateConfig:
    """Test configuration validation."""
    
    def test_validate_config_success(self, tmp_path):
        """Test successful configuration validation."""
        with patch.object(settings, 'memory_path', tmp_path / "memory"):
            with patch.object(settings, 'plugin_dirs', [tmp_path / "plugins"]):
                # Should create directories and validate successfully
                validate_config()
                
                assert (tmp_path / "memory").exists()
                assert (tmp_path / "plugins").exists()
    
    def test_validate_config_missing_api_keys(self):
        """Test validation fails with missing API keys."""
        with patch.object(settings, 'get_api_key', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                validate_config(providers=["openai", "anthropic"])
            
            error_msg = str(exc_info.value)
            assert "Missing API key for openai" in error_msg
            assert "Missing API key for anthropic" in error_msg
    
    def test_validate_config_telemetry_error(self):
        """Test validation with telemetry configuration error."""
        with patch.object(settings, 'telemetry_enabled', True):
            with patch.object(settings, 'telemetry_export_endpoint', None):
                with pytest.raises(ValueError) as exc_info:
                    validate_config(require_telemetry=True)
                
                assert "Telemetry enabled but no export endpoint" in str(exc_info.value)
    
    def test_validate_config_directory_creation_error(self, tmp_path):
        """Test validation when directory creation fails."""
        bad_path = tmp_path / "readonly" / "memory"
        
        # Make parent directory read-only
        (tmp_path / "readonly").mkdir()
        (tmp_path / "readonly").chmod(0o444)
        
        try:
            with patch.object(settings, 'memory_path', bad_path):
                with patch.object(settings, 'plugin_dirs', []):
                    with pytest.raises(ValueError) as exc_info:
                        validate_config()
                    
                    assert "Cannot create memory path" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            (tmp_path / "readonly").chmod(0o755)
    
    def test_validate_config_partial_providers(self):
        """Test validation with some providers configured."""
        def mock_get_api_key(provider):
            if provider == "openai":
                return "key-123"
            return None
        
        with patch.object(settings, 'get_api_key', side_effect=mock_get_api_key):
            with patch.object(settings, 'memory_path', Path("/tmp/memory")):
                with patch.object(settings, 'plugin_dirs', []):
                    # Should only fail for anthropic
                    with pytest.raises(ValueError) as exc_info:
                        validate_config(providers=["openai", "anthropic"])
                    
                    assert "Missing API key for anthropic" in str(exc_info.value)
                    assert "openai" not in str(exc_info.value)


class TestInitFromEnv:
    """Test initialization from environment."""
    
    def test_init_from_env_complete_flow(self, tmp_path):
        """Test complete initialization flow."""
        env_file = tmp_path / ".env"
        env_file.write_text("AGENTICRAFT_OPENAI_API_KEY=test-key")
        
        with patch('agenticraft.utils.config.setup_environment') as mock_setup:
            with patch('agenticraft.utils.config.reload_settings') as mock_reload:
                with patch('agenticraft.utils.config.validate_config') as mock_validate:
                    init_from_env(str(env_file), providers=["openai"])
                    
                    # Check all steps were called
                    mock_setup.assert_called_once_with(str(env_file))
                    mock_reload.assert_called_once()
                    mock_validate.assert_called_once_with(providers=["openai"])
    
    def test_init_from_env_validation_error(self, tmp_path):
        """Test initialization with validation error."""
        env_file = tmp_path / ".env"
        env_file.write_text("SOME_VAR=value")
        
        with patch('agenticraft.utils.config.setup_environment'):
            with patch('agenticraft.utils.config.reload_settings'):
                with patch('agenticraft.utils.config.validate_config', 
                          side_effect=ValueError("Invalid config")):
                    with pytest.raises(ValueError):
                        init_from_env(str(env_file))


class TestGetConfigInfo:
    """Test configuration info retrieval."""
    
    def test_get_config_info(self):
        """Test getting configuration information."""
        with patch.multiple(
            settings,
            environment="production",
            debug=True,
            openai_api_key="key1",
            anthropic_api_key=None,
            google_api_key="key3",
            default_model="gpt-4",
            telemetry_enabled=True,
            memory_backend="redis",
            plugins_enabled=False,
            mcp_enabled=True
        ):
            info = get_config_info()
            
            assert info["environment"] == "production"
            assert info["debug"] is True
            assert info["providers_configured"]["openai"] is True
            assert info["providers_configured"]["anthropic"] is False
            assert info["providers_configured"]["google"] is True
            assert info["default_model"] == "gpt-4"
            assert info["telemetry_enabled"] is True
            assert info["memory_backend"] == "redis"
            assert info["plugins_enabled"] is False
            assert info["mcp_enabled"] is True


class TestCreateEnvTemplate:
    """Test environment template creation."""
    
    def test_create_env_template_default_path(self, tmp_path):
        """Test creating env template at default path."""
        template_path = tmp_path / ".env.example"
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            
            with patch('builtins.print') as mock_print:
                create_env_template()
                
                assert template_path.exists()
                content = template_path.read_text()
                
                # Check key sections are present
                assert "# AgentiCraft Configuration" in content
                assert "AGENTICRAFT_OPENAI_API_KEY=" in content
                assert "AGENTICRAFT_DEFAULT_MODEL=" in content
                assert "AGENTICRAFT_MEMORY_BACKEND=" in content
                assert "AGENTICRAFT_TELEMETRY_ENABLED=" in content
                
                mock_print.assert_called_with(f"Created environment template at .env.example")
        finally:
            os.chdir(original_cwd)
    
    def test_create_env_template_custom_path(self, tmp_path):
        """Test creating env template at custom path."""
        custom_path = tmp_path / "custom" / ".env.template"
        custom_path.parent.mkdir()
        
        with patch('builtins.print'):
            create_env_template(str(custom_path))
            
            assert custom_path.exists()
            content = custom_path.read_text()
            
            # Check it's a valid template
            assert "your-openai-key-here" in content
            assert "AGENTICRAFT_ENVIRONMENT=" in content
    
    def test_create_env_template_overwrite(self, tmp_path):
        """Test overwriting existing template."""
        template_path = tmp_path / ".env.example"
        template_path.write_text("old content")
        
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            
            with patch('builtins.print'):
                create_env_template()
                
                content = template_path.read_text()
                assert "old content" not in content
                assert "# AgentiCraft Configuration" in content
        finally:
            os.chdir(original_cwd)
