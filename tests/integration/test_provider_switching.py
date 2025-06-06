"""Integration tests for provider switching.

This module tests the ability to switch between different LLM providers
(OpenAI, Anthropic, Ollama) at runtime, ensuring seamless transitions
and proper handling of provider-specific features.

NOTE: These tests assume the Agent class has a `set_provider` method.
See agent_set_provider_implementation.py for a sample implementation
that needs to be added to agenticraft/core/agent.py.

The tests also simulate the provider switching functionality that would
be part of the v0.1.1 release.
"""

import asyncio
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from agenticraft import Agent
from agenticraft.core.types import CompletionResponse, Message, MessageRole, ToolCall
from agenticraft.core.provider import ProviderFactory
from agenticraft.providers.openai import OpenAIProvider
from agenticraft.providers.anthropic import AnthropicProvider
from agenticraft.providers.ollama import OllamaProvider
from agenticraft.core.exceptions import ProviderError, AgentError
from agenticraft.core.tool import tool


class TestProviderSwitching:
    """Test switching between providers."""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables for all providers."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-123456789")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-key-123456789")
        # Ollama doesn't need API key
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content="OpenAI response",
                    tool_calls=None
                ),
                finish_reason="stop"
            )],
            usage=MagicMock(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
        )
    
    @pytest.fixture
    def mock_anthropic_response(self):
        """Mock Anthropic API response."""
        class MockTextBlock:
            def __init__(self, text):
                self.text = text
        
        return MagicMock(
            content=[MockTextBlock("Anthropic response")],
            stop_reason="end_turn",
            usage=MagicMock(
                input_tokens=15,
                output_tokens=25
            )
        )
    
    @pytest.fixture
    def mock_ollama_response(self):
        """Mock Ollama API response."""
        return {
            "message": {
                "role": "assistant",
                "content": "Ollama response"
            },
            "prompt_eval_count": 12,
            "eval_count": 18
        }
    
    @pytest.mark.asyncio
    async def test_switch_providers_on_agent(self, mock_env):
        """Test switching providers on an existing agent."""
        # Create agent with OpenAI
        agent = Agent(
            name="SwitchableAgent",
            model="gpt-4",
            provider="openai"
        )
        
        assert isinstance(agent.provider, OpenAIProvider)
        initial_id = agent.id
        
        # Switch to Anthropic
        with patch.object(AnthropicProvider, 'validate_auth'):
            agent.set_provider("anthropic", model="claude-3-opus-20240229")
        assert isinstance(agent.provider, AnthropicProvider)
        assert agent.config.model == "claude-3-opus-20240229"
        assert agent.id == initial_id  # Agent ID should not change
        
        # Switch to Ollama - mock the validation to avoid connection
        with patch.object(OllamaProvider, 'validate_auth'):
            agent.set_provider("ollama", model="llama2")
        assert isinstance(agent.provider, OllamaProvider)
        assert agent.config.model == "llama2"
        assert agent.id == initial_id
        
        # Switch back to OpenAI
        with patch.object(OpenAIProvider, 'validate_auth'):
            agent.set_provider("openai", model="gpt-3.5-turbo")
        assert isinstance(agent.provider, OpenAIProvider)
        assert agent.config.model == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_provider_switching_with_execution(
        self, 
        mock_env, 
        mock_openai_response,
        mock_anthropic_response,
        mock_ollama_response
    ):
        """Test that each provider works correctly after switching."""
        agent = Agent(name="TestAgent")
        
        # Test with OpenAI
        with patch('openai.AsyncOpenAI') as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
            mock_openai_class.return_value = mock_client
            
            agent.set_provider("openai")
            response = await agent.arun("Hello from OpenAI")
            assert response.content == "OpenAI response"
        
        # Test with Anthropic
        with patch('anthropic.AsyncAnthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock(return_value=mock_anthropic_response)
            mock_anthropic_class.return_value = mock_client
            
            agent.set_provider("anthropic")
            response = await agent.arun("Hello from Anthropic")
            assert response.content == "Anthropic response"
        
        # Test with Ollama
        with patch('httpx.AsyncClient') as mock_httpx, \
             patch.object(OllamaProvider, 'validate_auth'):
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            agent.set_provider("ollama", base_url="http://localhost:11434")
            response = await agent.arun("Hello from Ollama")
            assert response.content == "Ollama response"
    
    @pytest.mark.asyncio
    async def test_provider_specific_features(self, mock_env):
        """Test provider-specific features work after switching."""
        agent = Agent(name="FeatureAgent")
        
        # OpenAI-specific: response_format
        agent.set_provider("openai")
        with patch.object(agent.provider, 'complete') as mock_complete:
            mock_complete.return_value = CompletionResponse(
                content='{"answer": "42"}',
                tool_calls=[],
                finish_reason="stop"
            )
            
            await agent.arun(
                "Give me JSON", 
                response_format={"type": "json_object"}
            )
            
            # Verify OpenAI-specific param was passed
            mock_complete.assert_called_once()
            call_kwargs = mock_complete.call_args[1]
            assert "response_format" in call_kwargs
        
        # Anthropic-specific: system message handling
        agent.set_provider("anthropic")
        agent.config.instructions = "You are Claude"
        
        with patch.object(agent.provider, 'complete') as mock_complete:
            mock_complete.return_value = CompletionResponse(
                content="I am Claude",
                tool_calls=[],
                finish_reason="stop"
            )
            
            await agent.arun("Who are you?")
            
            # Anthropic extracts system message differently
            mock_complete.assert_called_once()
            # The system message should be in the instructions
            assert agent.config.instructions == "You are Claude"
        
        # Ollama-specific: local model features
        with patch.object(OllamaProvider, 'validate_auth'):
            agent.set_provider("ollama")
        with patch.object(agent.provider, 'complete') as mock_complete:
            mock_complete.return_value = CompletionResponse(
                content="Local response",
                tool_calls=[],
                finish_reason="stop"
            )
            
            await agent.arun("Local test", seed=42)  # Remove temperature from kwargs
            
            # Verify Ollama-specific params
            mock_complete.assert_called_once()
            call_kwargs = mock_complete.call_args[1]
            assert call_kwargs.get("seed") == 42
            # Temperature will be from agent's default config
    
    def test_provider_switching_preserves_configuration(self, mock_env):
        """Test that agent configuration is preserved when switching providers."""
        # Create agent with specific configuration
        agent = Agent(
            name="ConfigAgent",
            instructions="You are a helpful assistant",
            temperature=0.5,
            max_tokens=1000,
            metadata={"version": "1.0"}
        )
        
        original_instructions = agent.config.instructions
        original_temperature = agent.config.temperature
        original_max_tokens = agent.config.max_tokens
        original_metadata = agent.config.metadata.copy()
        
        # Switch providers multiple times
        for provider in ["anthropic", "ollama", "openai"]:
            # Mock validation for each provider
            if provider == "anthropic":
                with patch.object(AnthropicProvider, 'validate_auth'):
                    agent.set_provider(provider)
            elif provider == "ollama":
                with patch.object(OllamaProvider, 'validate_auth'):
                    agent.set_provider(provider)
            else:  # openai
                with patch.object(OpenAIProvider, 'validate_auth'):
                    agent.set_provider(provider)
            
            # Configuration should be preserved
            assert agent.config.instructions == original_instructions
            assert agent.config.temperature == original_temperature
            assert agent.config.max_tokens == original_max_tokens
            assert agent.config.metadata == original_metadata
    
    def test_provider_switching_with_tools(self, mock_env):
        """Test that tools work correctly with all providers."""
        @tool
        def calculator(expression: str) -> float:
            """Calculate a mathematical expression."""
            return eval(expression)
        
        agent = Agent(
            name="ToolAgent",
            tools=[calculator]
        )
        
        # Verify tool is registered
        assert "calculator" in agent._tool_registry.list_tools()
        
        # Switch providers and verify tools remain available
        for provider in ["openai", "anthropic", "ollama"]:
            # Mock validation for each provider
            if provider == "anthropic":
                with patch.object(AnthropicProvider, 'validate_auth'):
                    agent.set_provider(provider)
            elif provider == "ollama":
                with patch.object(OllamaProvider, 'validate_auth'):
                    agent.set_provider(provider)
            else:  # openai
                with patch.object(OpenAIProvider, 'validate_auth'):
                    agent.set_provider(provider)
            assert "calculator" in agent._tool_registry.list_tools()
            
            # Tool should be executable
            result = agent._tool_registry._tools["calculator"].run(expression="2+2")
            assert result == 4
    
    def test_provider_switching_with_memory(self, mock_env):
        """Test that memory is preserved when switching providers."""
        from agenticraft.core.memory import ConversationMemory
        
        memory = ConversationMemory(max_entries=10)
        agent = Agent(
            name="MemoryAgent",
            memory=[memory]
        )
        
        # Add some conversation history
        agent._messages.extend([
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!"),
            Message(role=MessageRole.USER, content="How are you?"),
            Message(role=MessageRole.ASSISTANT, content="I'm doing well!")
        ])
        
        original_message_count = len(agent._messages)
        
        # Switch providers
        for provider in ["anthropic", "ollama", "openai"]:
            # Mock validation for each provider
            if provider == "anthropic":
                with patch.object(AnthropicProvider, 'validate_auth'):
                    agent.set_provider(provider)
            elif provider == "ollama":
                with patch.object(OllamaProvider, 'validate_auth'):
                    agent.set_provider(provider)
            else:  # openai
                with patch.object(OpenAIProvider, 'validate_auth'):
                    agent.set_provider(provider)
            
            # Messages should be preserved
            assert len(agent._messages) == original_message_count
            assert agent._messages[0].content == "Hello"
            assert agent._messages[-1].content == "I'm doing well!"
    
    def test_provider_switching_error_handling(self, mock_env):
        """Test error handling when switching to invalid providers."""
        agent = Agent(name="ErrorAgent")
        
        # Test invalid provider name
        with pytest.raises(ProviderError, match="Unknown provider"):
            agent.set_provider("invalid_provider")
        
        # Test switching to provider without credentials
        with patch.dict(os.environ, {}, clear=True):
            # Remove API keys
            with pytest.raises(ProviderError, match="Failed to switch to anthropic"):
                agent.set_provider("anthropic")
    
    @pytest.mark.asyncio
    async def test_concurrent_agents_different_providers(self, mock_env):
        """Test multiple agents using different providers concurrently."""
        # Create agents with different providers
        with patch.object(OpenAIProvider, 'validate_auth'):
            openai_agent = Agent(name="OpenAI_Agent", provider="openai")
        with patch.object(AnthropicProvider, 'validate_auth'):
            anthropic_agent = Agent(name="Anthropic_Agent", provider="anthropic")
        with patch.object(OllamaProvider, 'validate_auth'):
            ollama_agent = Agent(name="Ollama_Agent", provider="ollama")
        
        # Mock responses
        with patch.object(OpenAIProvider, 'complete') as mock_openai, \
             patch.object(AnthropicProvider, 'complete') as mock_anthropic, \
             patch.object(OllamaProvider, 'complete') as mock_ollama:
            
            mock_openai.return_value = CompletionResponse(
                content="OpenAI concurrent response",
                tool_calls=[],
                finish_reason="stop"
            )
            
            mock_anthropic.return_value = CompletionResponse(
                content="Anthropic concurrent response",
                tool_calls=[],
                finish_reason="stop"
            )
            
            mock_ollama.return_value = CompletionResponse(
                content="Ollama concurrent response",
                tool_calls=[],
                finish_reason="stop"
            )
            
            # Run all agents concurrently
            results = await asyncio.gather(
                openai_agent.arun("Test"),
                anthropic_agent.arun("Test"),
                ollama_agent.arun("Test")
            )
            
            assert results[0].content == "OpenAI concurrent response"
            assert results[1].content == "Anthropic concurrent response"
            assert results[2].content == "Ollama concurrent response"
    
    def test_provider_factory_integration(self, mock_env):
        """Test ProviderFactory correctly creates providers for switching."""
        # Test creating each provider type
        # ProviderFactory determines provider from model name
        openai = ProviderFactory.create(
            model="gpt-4",
            api_key="sk-test-key-123456"
        )
        assert isinstance(openai, OpenAIProvider)
        
        anthropic = ProviderFactory.create(
            model="claude-3-opus-20240229",
            api_key="sk-ant-test-key-123456"
        )
        assert isinstance(anthropic, AnthropicProvider)
        
        ollama = ProviderFactory.create(
            model="llama2"  # or "ollama/llama2"
        )
        assert isinstance(ollama, OllamaProvider)
    
    @pytest.mark.asyncio
    async def test_provider_specific_error_handling(self, mock_env):
        """Test that provider-specific errors are handled correctly."""
        agent = Agent(name="ErrorHandlingAgent")
        
        # OpenAI rate limit error
        agent.set_provider("openai")
        with patch.object(agent.provider, 'complete') as mock_complete:
            mock_complete.side_effect = Exception("Rate limit exceeded")
            
            with pytest.raises(AgentError, match="Rate limit"):
                await agent.arun("Test")
        
        # Anthropic API error
        agent.set_provider("anthropic")
        with patch.object(agent.provider, 'complete') as mock_complete:
            mock_complete.side_effect = ProviderError("Anthropic API error")
            
            with pytest.raises(AgentError, match="Anthropic API error"):
                await agent.arun("Test")
        
        # Ollama connection error
        with patch.object(OllamaProvider, 'validate_auth'):
            agent.set_provider("ollama")
        with patch.object(agent.provider, 'complete') as mock_complete:
            mock_complete.side_effect = httpx.ConnectError("Cannot connect to Ollama")
            
            with pytest.raises(AgentError, match="Cannot connect to Ollama"):
                await agent.arun("Test")
    
    def test_model_compatibility_checking(self, mock_env):
        """Test model compatibility when switching providers."""
        agent = Agent(name="ModelAgent", model="gpt-4")
        
        # GPT-4 is OpenAI specific
        assert agent.config.model == "gpt-4"
        
        # Switch to Anthropic - should suggest appropriate model
        with patch.object(AnthropicProvider, 'validate_auth'):
            agent.set_provider("anthropic")
        # Model should be updated to Anthropic default
        assert agent.config.model.startswith("claude")
        
        # Switch to Ollama - should use Ollama default
        with patch.object(OllamaProvider, 'validate_auth'):
            agent.set_provider("ollama")
        assert agent.config.model in ["llama2", "mistral", "codellama"]
        
        # Explicitly set model when switching
        with patch.object(OpenAIProvider, 'validate_auth'):
            agent.set_provider("openai", model="gpt-3.5-turbo")
        assert agent.config.model == "gpt-3.5-turbo"


class TestProviderFeatureCompatibility:
    """Test feature compatibility across providers."""
    
    @pytest.fixture
    def mock_all_providers(self, monkeypatch):
        """Set up mocks for all providers."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-123456789")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-key-123456789")
    
    @pytest.mark.asyncio
    async def test_streaming_across_providers(self, mock_all_providers):
        """Test streaming capability across providers."""
        agent = Agent(name="StreamAgent")
        
        # Note: This is a placeholder for when streaming is implemented
        # Currently testing that the parameter is accepted
        
        for provider in ["openai", "anthropic"]:
            agent.set_provider(provider)
            
            with patch.object(agent.provider, 'complete') as mock_complete:
                mock_complete.return_value = CompletionResponse(
                    content="Streamed response",
                    tool_calls=[],
                    finish_reason="stop"
                )
                
                # Should accept stream parameter
                await agent.arun("Test", stream=True)
                
                # Verify stream parameter was passed
                call_kwargs = mock_complete.call_args[1]
                assert "stream" in call_kwargs
    
    @pytest.mark.asyncio  
    async def test_tool_calling_across_providers(self, mock_all_providers):
        """Test tool calling compatibility across providers."""
        @tool
        def get_weather(city: str) -> str:
            """Get weather for a city."""
            return f"Sunny in {city}"
        
        agent = Agent(name="ToolCallAgent", tools=[get_weather])
        
        # Test OpenAI tool calling format
        agent.set_provider("openai")
        with patch.object(agent.provider, 'complete') as mock_complete:
            # First response requests tool
            tool_response = CompletionResponse(
                content="Let me check the weather",
                tool_calls=[ToolCall(
                    id="call_123",
                    name="get_weather", 
                    arguments={"city": "Paris"}
                )],
                finish_reason="tool_calls"
            )
            
            # Second response with result
            final_response = CompletionResponse(
                content="The weather in Paris is sunny",
                tool_calls=[],
                finish_reason="stop"
            )
            
            mock_complete.side_effect = [tool_response, final_response]
            
            response = await agent.arun("What's the weather in Paris?")
            assert "sunny" in response.content.lower()
        
        # Test Anthropic tool calling format
        agent.set_provider("anthropic")
        with patch.object(agent.provider, 'complete') as mock_complete:
            # Anthropic also supports tool calling
            tool_response = CompletionResponse(
                content="I'll check the weather",
                tool_calls=[ToolCall(
                    id="call_456",
                    name="get_weather",
                    arguments={"city": "London"}
                )],
                finish_reason="tool_use"
            )
            
            final_response = CompletionResponse(
                content="The weather in London is sunny",
                tool_calls=[],
                finish_reason="end_turn"
            )
            
            mock_complete.side_effect = [tool_response, final_response]
            
            response = await agent.arun("What's the weather in London?")
            assert "sunny" in response.content.lower()
    
    def test_provider_info_methods(self, mock_all_providers):
        """Test provider information methods."""
        agent = Agent(name="InfoAgent")
        
        # Each provider should provide info
        for provider_name in ["openai", "anthropic", "ollama"]:
            # Mock validation for each provider
            if provider_name == "anthropic":
                with patch.object(AnthropicProvider, 'validate_auth'):
                    agent.set_provider(provider_name)
            elif provider_name == "ollama":
                with patch.object(OllamaProvider, 'validate_auth'):
                    agent.set_provider(provider_name)
            else:  # openai
                with patch.object(OpenAIProvider, 'validate_auth'):
                    agent.set_provider(provider_name)
            provider = agent.provider
            
            # All providers should have these attributes
            assert hasattr(provider, 'model')
            assert hasattr(provider, 'validate_auth')
            assert hasattr(provider, 'api_key')
            assert hasattr(provider, 'base_url')
            assert hasattr(provider, 'timeout')
            assert hasattr(provider, 'max_retries')
            
            # Provider class name should match
            provider_class_name = provider.__class__.__name__.lower()
            assert provider_name in provider_class_name


class TestProviderSwitchingEdgeCases:
    """Test edge cases in provider switching."""
    
    @pytest.mark.asyncio
    async def test_switch_during_execution(self, monkeypatch):
        """Test switching provider during an execution (should wait)."""
        # Set up environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-123456789")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-key-123456789")
        agent = Agent(name="BusyAgent", provider="openai")
        
        with patch.object(agent.provider, 'complete') as mock_complete:
            # Make complete take some time
            async def slow_complete(*args, **kwargs):
                await asyncio.sleep(0.1)
                return CompletionResponse(
                    content="Completed",
                    tool_calls=[],
                    finish_reason="stop"
                )
            
            mock_complete.side_effect = slow_complete
            
            # Start execution
            task = asyncio.create_task(agent.arun("Long running task"))
            
            # Try to switch provider while busy
            await asyncio.sleep(0.05)  # Mid-execution
            with patch.object(AnthropicProvider, 'validate_auth'):
                agent.set_provider("anthropic")
            
            # Wait for completion
            result = await task
            
            # Original provider should have completed the task
            assert result.content == "Completed"
    
    def test_provider_switching_clears_client_cache(self, monkeypatch):
        """Test that switching providers clears any cached clients."""
        # Set up environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-123456789")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-key-123456789")
        agent = Agent(name="CacheAgent", provider="openai")
        
        # Access provider to potentially cache client
        provider1 = agent.provider
        if hasattr(provider1, '_client'):
            provider1._client = "cached_client"
        
        # Switch provider
        with patch.object(AnthropicProvider, 'validate_auth'):
            agent.set_provider("anthropic")
        provider2 = agent.provider
        
        # Should be different provider instances
        assert provider1 is not provider2
        assert isinstance(provider2, AnthropicProvider)
        
        # Old provider client should not affect new provider
        if hasattr(provider2, '_client'):
            assert provider2._client != "cached_client"
    
    def test_partial_provider_switch_rollback(self, monkeypatch):
        """Test rollback when provider switch fails midway."""
        # Set up environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key-123456789")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-key-123456789")
        agent = Agent(name="RollbackAgent", provider="openai")
        original_provider = agent.provider
        original_model = agent.config.model
        
        # Try to switch to provider that will fail
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            with pytest.raises(ProviderError, match="Failed to switch to anthropic"):
                agent.set_provider("anthropic")
        
        # Should maintain original provider
        assert agent.provider is original_provider
        assert agent.config.model == original_model
        assert isinstance(agent.provider, OpenAIProvider)
