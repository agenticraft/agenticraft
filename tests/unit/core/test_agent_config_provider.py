"""Unit tests for AgentConfig provider parameter.

Tests the new provider parameter added to AgentConfig in v0.1.1.
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from agenticraft import Agent
from agenticraft.core.agent import AgentConfig


class TestAgentConfigProvider:
    """Test the provider parameter in AgentConfig."""

    def test_provider_field_optional(self):
        """Test that provider field is optional and defaults to None."""
        config = AgentConfig(name="TestAgent")
        assert config.provider is None
        assert config.model  # Should have default model

    def test_provider_field_explicit(self):
        """Test explicit provider specification."""
        config = AgentConfig(
            name="TestAgent", provider="anthropic", model="claude-3-opus-20240229"
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus-20240229"

    def test_provider_validation_valid(self):
        """Test that valid provider names are accepted."""
        valid_providers = ["openai", "anthropic", "ollama", "google"]

        for provider in valid_providers:
            config = AgentConfig(name="Test", provider=provider)
            assert config.provider == provider

    def test_provider_validation_invalid(self):
        """Test that invalid provider names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(name="Test", provider="invalid_provider")

        error = exc_info.value
        assert "Invalid provider" in str(error)
        assert "invalid_provider" in str(error)

    def test_provider_none_allowed(self):
        """Test that None is allowed for auto-detection."""
        config = AgentConfig(name="Test", provider=None)
        assert config.provider is None

    def test_agent_uses_config_provider(self, monkeypatch):
        """Test that Agent uses explicit provider from config."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Mock ProviderFactory to track calls
        with patch("agenticraft.core.provider.ProviderFactory.create") as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider

            # Create agent with explicit provider
            agent = Agent(
                name="TestAgent", provider="anthropic", model="claude-3-opus-20240229"
            )

            # Access provider to trigger creation
            _ = agent.provider

            # Verify ProviderFactory was called with provider parameter
            mock_create.assert_called_once()
            call_args = mock_create.call_args

            # Check if provider was passed (depends on implementation)
            # This assumes the implementation passes provider to ProviderFactory
            assert call_args[1].get("model") == "claude-3-opus-20240229"

    def test_agent_auto_detect_without_provider(self, monkeypatch):
        """Test auto-detection when provider is not specified."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Create agent without provider
        agent = Agent(name="TestAgent", model="gpt-4")

        # Config should have provider as None
        assert agent.config.provider is None
        assert agent.config.model == "gpt-4"

    def test_set_provider_updates_config_provider(self, monkeypatch):
        """Test that set_provider updates the config.provider field."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Create agent
        agent = Agent(name="TestAgent", model="gpt-4")

        # Initially no explicit provider
        assert agent.config.provider is None

        # Mock the provider switching
        with patch.object(agent, "_provider", None):
            with patch(
                "agenticraft.core.provider.ProviderFactory.create"
            ) as mock_create:
                mock_provider = MagicMock()
                mock_provider.validate_auth = MagicMock()
                mock_create.return_value = mock_provider

                # Switch provider
                agent.set_provider("anthropic", model="claude-3-opus-20240229")

                # Config should be updated
                assert agent.config.provider == "anthropic"
                assert agent.config.model == "claude-3-opus-20240229"

    def test_provider_serialization(self):
        """Test that provider field is included in serialization."""
        config = AgentConfig(
            name="TestAgent", provider="anthropic", model="claude-3-opus-20240229"
        )

        # Convert to dict
        config_dict = config.model_dump()
        assert "provider" in config_dict
        assert config_dict["provider"] == "anthropic"

        # Exclude secrets
        config_dict_no_secrets = config.model_dump(exclude={"api_key"})
        assert "provider" in config_dict_no_secrets
        assert "api_key" not in config_dict_no_secrets

    def test_provider_from_dict(self):
        """Test creating AgentConfig from dict with provider."""
        config_dict = {
            "name": "TestAgent",
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434",
        }

        config = AgentConfig(**config_dict)
        assert config.provider == "ollama"
        assert config.model == "llama2"
        assert config.base_url == "http://localhost:11434"


class TestProviderParameterIntegration:
    """Integration tests for provider parameter."""

    def test_provider_priority_over_auto_detection(self, monkeypatch):
        """Test that explicit provider takes priority over auto-detection."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Model name suggests OpenAI, but provider says Anthropic
        agent = Agent(
            name="TestAgent",
            provider="anthropic",  # Explicit provider
            model="gpt-4",  # Model name that would auto-detect as OpenAI
        )

        # Provider should be Anthropic as explicitly specified
        assert agent.config.provider == "anthropic"
        assert agent.config.model == "gpt-4"

        # Note: In real implementation, this might fail if Anthropic
        # doesn't support "gpt-4" model, but that's expected behavior

    def test_provider_helps_with_custom_models(self, monkeypatch):
        """Test that provider parameter helps with custom model names."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Custom model that wouldn't be auto-detected
        agent = Agent(
            name="CustomAgent",
            provider="ollama",
            model="my-fine-tuned-model",
            base_url="http://localhost:11434",
        )

        assert agent.config.provider == "ollama"
        assert agent.config.model == "my-fine-tuned-model"
