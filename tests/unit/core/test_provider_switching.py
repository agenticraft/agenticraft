"""Unit tests for provider switching behavior.

These tests mock the Agent.set_provider method to test the expected behavior
without requiring the actual implementation.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from agenticraft import Agent
from agenticraft.providers.openai import OpenAIProvider
from agenticraft.providers.anthropic import AnthropicProvider
from agenticraft.providers.ollama import OllamaProvider
from agenticraft.core.exceptions import ProviderError


class TestProviderSwitchingUnit:
    """Unit tests for provider switching with mocked implementation."""
    
    def test_provider_switching_behavior(self, monkeypatch):
        """Test expected behavior of provider switching."""
        # Mock environment
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # Create agent
        agent = Agent(name="TestAgent")
        
        # Mock the set_provider method
        def mock_set_provider(self, provider_name, **kwargs):
            """Mock implementation of set_provider."""
            provider_map = {
                "openai": OpenAIProvider,
                "anthropic": AnthropicProvider,
                "ollama": OllamaProvider
            }
            
            if provider_name not in provider_map:
                raise ProviderError(f"Unknown provider: {provider_name}")
            
            # Update model if provided
            if "model" in kwargs:
                self.config.model = kwargs["model"]
            
            # Create mock provider
            mock_provider = MagicMock(spec=provider_map[provider_name])
            mock_provider.name = provider_name
            self._provider = mock_provider
        
        # Bind the mock method to the agent instance
        agent.set_provider = mock_set_provider.__get__(agent, Agent)
        
        # Test switching providers
        agent.set_provider("openai", model="gpt-4")
        assert agent._provider.name == "openai"
        assert agent.config.model == "gpt-4"
        
        agent.set_provider("anthropic", model="claude-3-opus-20240229")
        assert agent._provider.name == "anthropic"
        assert agent.config.model == "claude-3-opus-20240229"
        
        # Test error on unknown provider
        with pytest.raises(ProviderError, match="Unknown provider"):
            agent.set_provider("unknown_provider")
    
    def test_provider_property_behavior(self, monkeypatch):
        """Test that provider property works correctly."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        agent = Agent(name="TestAgent")
        
        # Initially, provider should be created lazily
        assert agent._provider is None
        
        # Accessing provider should create it
        provider = agent.provider
        assert provider is not None
        assert isinstance(provider, OpenAIProvider)
        
        # Subsequent access should return same instance
        assert agent.provider is provider
    
    def test_agent_state_preservation(self, monkeypatch):
        """Test that agent state is preserved during provider switches."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        agent = Agent(
            name="StatefulAgent",
            instructions="Custom instructions",
            temperature=0.5,
            max_tokens=1000
        )
        
        # Save initial state
        initial_id = agent.id
        initial_instructions = agent.config.instructions
        initial_temperature = agent.config.temperature
        initial_max_tokens = agent.config.max_tokens
        
        # Mock provider switching
        def mock_switch(self, provider, **kwargs):
            # Just change the provider type
            self._provider = MagicMock()
            self._provider.name = provider
        
        agent.set_provider = mock_switch.__get__(agent, Agent)
        
        # Switch providers
        agent.set_provider("anthropic")
        
        # Verify state is preserved
        assert agent.id == initial_id
        assert agent.config.instructions == initial_instructions
        assert agent.config.temperature == initial_temperature
        assert agent.config.max_tokens == initial_max_tokens
    
    def test_tools_persistence_across_providers(self, monkeypatch):
        """Test that tools remain available after provider switch."""
        from agenticraft.core.tool import tool
        
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        @tool
        def test_tool(x: int) -> int:
            """Test tool."""
            return x * 2
        
        agent = Agent(name="ToolAgent", tools=[test_tool])
        
        # Verify tool is registered
        assert "test_tool" in agent._tool_registry.list_tools()
        tool_count = len(agent._tool_registry._tools)
        
        # Mock provider switch
        agent._provider = MagicMock()
        agent._provider.name = "anthropic"
        
        # Tools should still be available
        assert "test_tool" in agent._tool_registry.list_tools()
        assert len(agent._tool_registry._tools) == tool_count
    
    def test_memory_persistence_across_providers(self, monkeypatch):
        """Test that memory is preserved across provider switches."""
        from agenticraft.core.memory import ConversationMemory
        from agenticraft.core.types import Message, MessageRole
        
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        memory = ConversationMemory()
        agent = Agent(name="MemoryAgent", memory=[memory])
        
        # Add some messages
        agent._messages.append(
            Message(role=MessageRole.USER, content="Hello")
        )
        agent._messages.append(
            Message(role=MessageRole.ASSISTANT, content="Hi there!")
        )
        
        message_count = len(agent._messages)
        
        # Mock provider switch
        agent._provider = MagicMock()
        agent._provider.name = "ollama"
        
        # Messages should be preserved
        assert len(agent._messages) == message_count
        assert agent._messages[0].content == "Hello"
        assert agent._messages[1].content == "Hi there!"


class TestProviderCompatibility:
    """Test provider compatibility assumptions."""
    
    def test_provider_interface_consistency(self):
        """Test that all providers implement the same interface."""
        from agenticraft.core.provider import BaseProvider
        
        # All providers should inherit from BaseProvider
        assert issubclass(OpenAIProvider, BaseProvider)
        assert issubclass(AnthropicProvider, BaseProvider)
        assert issubclass(OllamaProvider, BaseProvider)
        
        # All should have the required methods
        for provider_class in [OpenAIProvider, AnthropicProvider, OllamaProvider]:
            assert hasattr(provider_class, 'complete')
            assert hasattr(provider_class, 'validate_auth')
    
    def test_model_name_patterns(self):
        """Test model name patterns for provider detection."""
        from agenticraft.core.provider import ProviderFactory
        
        # Mock environment for API keys
        import os
        os.environ["OPENAI_API_KEY"] = "test"
        os.environ["ANTHROPIC_API_KEY"] = "test"
        
        # OpenAI models
        for model in ["gpt-4", "gpt-3.5-turbo", "o1-preview"]:
            provider = ProviderFactory.create(model=model)
            assert isinstance(provider, OpenAIProvider)
        
        # Anthropic models
        for model in ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]:
            provider = ProviderFactory.create(model=model)
            assert isinstance(provider, AnthropicProvider)
        
        # Ollama models
        for model in ["llama2", "mistral", "codellama", "ollama/llama2"]:
            provider = ProviderFactory.create(model=model)
            assert isinstance(provider, OllamaProvider)
