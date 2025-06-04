"""Comprehensive tests for the Agent class to achieve >95% coverage."""

import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import UUID

import pytest

from agenticraft import Agent, tool
from agenticraft.core.agent import AgentConfig, AgentResponse
from agenticraft.core.exceptions import AgentError, ToolExecutionError
from agenticraft.core.memory import ConversationMemory, KnowledgeMemory
from agenticraft.core.reasoning import ChainOfThought, SimpleReasoning, ReflectiveReasoning
from agenticraft.core.types import Message, MessageRole, CompletionResponse, ToolCall, ToolResult
from agenticraft.core.tool import BaseTool, FunctionTool


class TestAgentConfig:
    """Test AgentConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AgentConfig()
        
        assert config.name == "Agent"
        assert config.instructions == "You are a helpful AI assistant."
        assert config.model is not None  # From settings
        assert 0 <= config.temperature <= 2
        assert config.tools == []
        assert config.memory == []
        assert config.reasoning_pattern is None
        assert config.metadata == {}
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = AgentConfig(
            name="CustomAgent",
            instructions="Custom instructions",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=100,
            timeout=30,
            max_retries=3,
            metadata={"custom": "data"}
        )
        
        assert config.name == "CustomAgent"
        assert config.instructions == "Custom instructions"
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 100
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.metadata == {"custom": "data"}
    
    def test_tool_validation_with_base_tool(self):
        """Test tool validation with BaseTool instances."""
        class TestTool(BaseTool):
            def execute(self, **kwargs):
                return "test"
        
        tool_instance = TestTool()
        config = AgentConfig(tools=[tool_instance])
        assert len(config.tools) == 1
    
    def test_tool_validation_with_callable(self):
        """Test tool validation with callables."""
        def plain_func():
            return "plain"
        
        config = AgentConfig(tools=[plain_func])
        assert len(config.tools) == 1
    
    def test_tool_validation_invalid(self):
        """Test tool validation rejects non-callables."""
        with pytest.raises(ValueError, match="Invalid tool type"):
            AgentConfig(tools=["not a tool"])
    
    def test_memory_validation_valid(self):
        """Test memory validation with valid memory types."""
        conv_memory = ConversationMemory(max_turns=5)
        knowledge_memory = KnowledgeMemory()
        
        config = AgentConfig(memory=[conv_memory, knowledge_memory])
        assert len(config.memory) == 2
    
    def test_memory_validation_invalid(self):
        """Test memory validation rejects invalid types."""
        with pytest.raises(ValueError, match="Invalid memory type"):
            AgentConfig(memory=["not a memory"])
    
    def test_api_key_excluded(self):
        """Test api_key is excluded from serialization."""
        config = AgentConfig(api_key="secret-key")
        config_dict = config.model_dump()
        assert "api_key" not in config_dict
    
    def test_temperature_bounds(self):
        """Test temperature validation."""
        # Valid temperatures
        AgentConfig(temperature=0.0)
        AgentConfig(temperature=1.0)
        AgentConfig(temperature=2.0)
        
        # Invalid temperatures
        with pytest.raises(ValueError):
            AgentConfig(temperature=-0.1)
        
        with pytest.raises(ValueError):
            AgentConfig(temperature=2.1)
    
    def test_positive_constraints(self):
        """Test positive value constraints."""
        with pytest.raises(ValueError):
            AgentConfig(max_tokens=0)
        
        with pytest.raises(ValueError):
            AgentConfig(timeout=0)
        
        with pytest.raises(ValueError):
            AgentConfig(max_retries=-1)


class TestAgent:
    """Test the Agent class."""
    
    @pytest.fixture
    def mock_settings(self, monkeypatch):
        """Mock settings for tests."""
        monkeypatch.setattr("agenticraft.core.config.settings.default_model", "gpt-4")
        monkeypatch.setattr("agenticraft.core.config.settings.default_temperature", 0.7)
        monkeypatch.setattr("agenticraft.core.config.settings.default_max_tokens", 1000)
        monkeypatch.setattr("agenticraft.core.config.settings.default_timeout", 30)
        monkeypatch.setattr("agenticraft.core.config.settings.default_max_retries", 3)
        monkeypatch.setattr("agenticraft.core.config.settings.conversation_memory_size", 10)
    
    def test_agent_creation_minimal(self, mock_settings):
        """Test minimal agent creation."""
        agent = Agent()
        
        assert agent.name == "Agent"
        assert agent.config.instructions == "You are a helpful AI assistant."
        assert agent.config.model == "gpt-4"
        assert isinstance(agent.id, UUID)
        assert len(agent._messages) == 0
        assert agent._provider is None  # Lazy loaded
    
    def test_agent_creation_custom(self, mock_settings):
        """Test agent creation with custom parameters."""
        agent = Agent(
            name="TestAgent",
            instructions="Test instructions",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=500,
            api_key="test-key",
            base_url="https://test.com",
            timeout=60,
            max_retries=5,
            metadata={"version": "1.0"}
        )
        
        assert agent.name == "TestAgent"
        assert agent.config.instructions == "Test instructions"
        assert agent.config.model == "gpt-3.5-turbo"
        assert agent.config.temperature == 0.5
        assert agent.config.max_tokens == 500
        assert agent.config.api_key == "test-key"
        assert agent.config.base_url == "https://test.com"
        assert agent.config.timeout == 60
        assert agent.config.max_retries == 5
        assert agent.config.metadata == {"version": "1.0"}
    
    def test_agent_with_tools(self, mock_settings):
        """Test agent creation with tools."""
        @tool
        def calculate(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y
        
        def plain_function():
            """Plain function tool."""
            return "result"
        
        agent = Agent(
            name="ToolAgent",
            tools=[calculate, plain_function]
        )
        
        assert len(agent._tool_registry._tools) == 2
    
    def test_agent_with_memory(self, mock_settings):
        """Test agent creation with memory."""
        conv_memory = ConversationMemory(max_turns=5)
        knowledge_memory = KnowledgeMemory()
        
        agent = Agent(
            name="MemoryAgent",
            memory=[conv_memory, knowledge_memory]
        )
        
        assert len(agent.config.memory) == 2
        assert len(agent._memory_store._memories) == 2
    
    def test_agent_with_reasoning_patterns(self, mock_settings):
        """Test agent with different reasoning patterns."""
        # Default reasoning
        agent1 = Agent(name="DefaultReasoning")
        assert isinstance(agent1._reasoning, SimpleReasoning)
        
        # Chain of thought
        cot = ChainOfThought()
        agent2 = Agent(name="CoTAgent", reasoning_pattern=cot)
        assert agent2._reasoning == cot
        
        # Reflective reasoning
        reflective = ReflectiveReasoning()
        agent3 = Agent(name="ReflectiveAgent", reasoning_pattern=reflective)
        assert agent3._reasoning == reflective
    
    def test_provider_lazy_loading(self, mock_settings):
        """Test that provider is lazy loaded."""
        agent = Agent(name="TestAgent")
        assert agent._provider is None
        
        # Mock ProviderFactory
        with patch("agenticraft.core.agent.ProviderFactory") as mock_factory:
            mock_provider = Mock()
            mock_factory.create.return_value = mock_provider
            
            # Access provider property
            provider = agent.provider
            
            assert provider == mock_provider
            assert agent._provider == mock_provider
            mock_factory.create.assert_called_once_with(
                model=agent.config.model,
                api_key=agent.config.api_key,
                base_url=agent.config.base_url,
                timeout=agent.config.timeout,
                max_retries=agent.config.max_retries
            )
    
    @pytest.mark.asyncio
    async def test_agent_run_basic(self, mock_settings):
        """Test basic agent run."""
        agent = Agent(name="TestAgent")
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_response = CompletionResponse(
            content="This is a test response",
            tool_calls=[],
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            metadata={"model": "gpt-4"}
        )
        mock_provider.complete.return_value = mock_response
        agent._provider = mock_provider
        
        response = await agent.arun("Hello")
        
        assert isinstance(response, AgentResponse)
        assert response.content == "This is a test response"
        assert response.agent_id == agent.id
        assert response.reasoning is not None
        assert "gpt-4" in response.metadata["model"]
        assert len(agent._messages) == 2  # User + Assistant
    
    @pytest.mark.asyncio
    async def test_agent_run_with_context(self, mock_settings):
        """Test agent run with context."""
        agent = Agent(name="TestAgent")
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_response = CompletionResponse(
            content="Summary of document",
            tool_calls=[],
            finish_reason="stop"
        )
        mock_provider.complete.return_value = mock_response
        agent._provider = mock_provider
        
        context = {"document": "Important information"}
        response = await agent.arun("Summarize this", context=context)
        
        assert response.content == "Summary of document"
        
        # Verify context was included in system message
        call_args = mock_provider.complete.call_args[1]
        messages = call_args["messages"]
        system_msg = messages[0]
        assert "document: Important information" in system_msg["content"]
    
    @pytest.mark.asyncio
    async def test_agent_with_tool_execution(self, mock_settings):
        """Test agent executing tools."""
        @tool
        def get_weather(city: str) -> str:
            """Get weather for a city."""
            return f"Sunny in {city}"
        
        agent = Agent(name="WeatherAgent", tools=[get_weather])
        
        # Mock provider
        mock_provider = AsyncMock()
        
        # First call returns tool request
        tool_call = ToolCall(
            id="call_123",
            name="get_weather",
            arguments={"city": "New York"}
        )
        tool_response = CompletionResponse(
            content="Let me check the weather",
            tool_calls=[tool_call],
            finish_reason="tool_calls"
        )
        
        # Second call returns final response
        final_response = CompletionResponse(
            content="The weather in New York is sunny",
            tool_calls=[],
            finish_reason="stop"
        )
        
        mock_provider.complete.side_effect = [tool_response, final_response]
        agent._provider = mock_provider
        
        response = await agent.arun("What's the weather in New York?")
        
        assert response.content == "The weather in New York is sunny"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "get_weather"
        assert mock_provider.complete.call_count == 2
    
    @pytest.mark.asyncio
    async def test_agent_tool_execution_error(self, mock_settings):
        """Test agent handling tool execution errors."""
        @tool
        def failing_tool() -> str:
            """A tool that fails."""
            raise Exception("Tool error")
        
        agent = Agent(name="FailAgent", tools=[failing_tool])
        
        # Mock provider
        mock_provider = AsyncMock()
        
        # First call requests tool
        tool_call = ToolCall(
            id="call_456",
            name="failing_tool",
            arguments={}
        )
        tool_response = CompletionResponse(
            content="Using tool",
            tool_calls=[tool_call],
            finish_reason="tool_calls"
        )
        
        # Second call handles error
        error_response = CompletionResponse(
            content="The tool failed with an error",
            tool_calls=[],
            finish_reason="stop"
        )
        
        mock_provider.complete.side_effect = [tool_response, error_response]
        agent._provider = mock_provider
        
        response = await agent.arun("Use the failing tool")
        
        assert response.content == "The tool failed with an error"
        assert "tool_error" in response.reasoning
    
    @pytest.mark.asyncio
    async def test_agent_with_memory_storage(self, mock_settings):
        """Test agent stores messages in memory."""
        conv_memory = ConversationMemory(max_turns=5)
        agent = Agent(name="MemoryAgent", memory=[conv_memory])
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_response = CompletionResponse(
            content="Hello there!",
            tool_calls=[],
            finish_reason="stop"
        )
        mock_provider.complete.return_value = mock_response
        agent._provider = mock_provider
        
        await agent.arun("Hello")
        
        # Check messages were stored
        stored_messages = conv_memory.get_messages()
        assert len(stored_messages) == 2
        assert stored_messages[0].role == MessageRole.USER
        assert stored_messages[0].content == "Hello"
        assert stored_messages[1].role == MessageRole.ASSISTANT
        assert stored_messages[1].content == "Hello there!"
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_settings):
        """Test agent error handling."""
        agent = Agent(name="ErrorAgent")
        
        # Mock provider that raises an error
        mock_provider = AsyncMock()
        mock_provider.complete.side_effect = Exception("API Error")
        agent._provider = mock_provider
        
        with pytest.raises(AgentError, match="Agent execution failed"):
            await agent.arun("Test")
    
    def test_sync_run(self, mock_settings):
        """Test synchronous run method."""
        agent = Agent(name="SyncAgent")
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_response = CompletionResponse(
            content="Sync response",
            tool_calls=[],
            finish_reason="stop"
        )
        mock_provider.complete.return_value = mock_response
        agent._provider = mock_provider
        
        # This should work even though it's calling async internally
        response = agent.run("Hello")
        
        assert isinstance(response, AgentResponse)
        assert response.content == "Sync response"
    
    def test_add_tool_dynamically(self, mock_settings):
        """Test adding tools after agent creation."""
        agent = Agent(name="DynamicAgent")
        
        assert len(agent._tool_registry._tools) == 0
        
        @tool
        def new_tool():
            return "new"
        
        agent.add_tool(new_tool)
        
        assert len(agent._tool_registry._tools) == 1
        assert len(agent.config.tools) == 1
    
    def test_clear_memory(self, mock_settings):
        """Test clearing agent memory."""
        conv_memory = ConversationMemory()
        agent = Agent(name="TestAgent", memory=[conv_memory])
        
        # Add some messages
        agent._messages.append(Message(
            role=MessageRole.USER,
            content="Hello"
        ))
        agent._messages.append(Message(
            role=MessageRole.ASSISTANT,
            content="Hi there"
        ))
        
        # Also add to memory
        asyncio.run(conv_memory.store("Hello", {"role": MessageRole.USER}))
        asyncio.run(conv_memory.store("Hi there", {"role": MessageRole.ASSISTANT}))
        
        assert len(agent._messages) == 2
        assert asyncio.run(conv_memory.size()) == 2
        
        agent.clear_memory()
        
        assert len(agent._messages) == 0
        assert asyncio.run(conv_memory.size()) == 0
    
    def test_agent_repr(self, mock_settings):
        """Test agent string representation."""
        @tool
        def dummy_tool():
            return "dummy"
        
        agent = Agent(
            name="TestAgent",
            model="gpt-4",
            tools=[dummy_tool]
        )
        
        repr_str = repr(agent)
        assert "Agent(name='TestAgent'" in repr_str
        assert "model='gpt-4'" in repr_str
        assert "tools=1)" in repr_str
    
    @pytest.mark.asyncio
    async def test_build_messages_with_memory_context(self, mock_settings):
        """Test message building with memory context."""
        agent = Agent(name="TestAgent")
        
        # Add some memory context
        memory_msg1 = Message(role=MessageRole.USER, content="Previous question")
        memory_msg2 = Message(role=MessageRole.ASSISTANT, content="Previous answer")
        
        # Add current messages
        agent._messages.append(Message(role=MessageRole.USER, content="Current question"))
        
        messages = agent._build_messages(
            memory_context=[memory_msg1, memory_msg2],
            user_context={"key": "value"}
        )
        
        # Check system message
        assert messages[0]["role"] == "system"
        assert "You are a helpful AI assistant" in messages[0]["content"]
        assert "key: value" in messages[0]["content"]
        
        # Check memory context is included
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Previous question"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Previous answer"
        
        # Check current message
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "Current question"
    
    @pytest.mark.asyncio
    async def test_agent_kwargs_passed_to_provider(self, mock_settings):
        """Test that additional kwargs are passed to provider."""
        agent = Agent(name="TestAgent")
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_response = CompletionResponse(
            content="Response",
            tool_calls=[],
            finish_reason="stop"
        )
        mock_provider.complete.return_value = mock_response
        agent._provider = mock_provider
        
        # Run with custom kwargs
        await agent.arun("Test", stream=True, custom_param="value")
        
        # Check kwargs were passed
        call_kwargs = mock_provider.complete.call_args[1]
        assert call_kwargs["stream"] == True
        assert call_kwargs["custom_param"] == "value"
    
    def test_agent_logging(self, mock_settings, caplog):
        """Test agent logs important events."""
        import logging
        caplog.set_level(logging.INFO)
        
        agent = Agent(name="LogAgent")
        
        # Check initialization was logged
        assert "Initialized agent 'LogAgent'" in caplog.text
        assert str(agent.id) in caplog.text
