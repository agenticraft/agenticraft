"""Tests for the Agent class."""

import asyncio
from unittest.mock import Mock, AsyncMock, patch

import pytest

from agenticraft import Agent, tool
from agenticraft.core.agent import AgentConfig, AgentResponse
from agenticraft.core.exceptions import AgentError
from agenticraft.core.memory import ConversationMemory
from agenticraft.core.reasoning import ChainOfThought, SimpleReasoning
from agenticraft.core.types import Message, MessageRole, CompletionResponse


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
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = AgentConfig(
            name="CustomAgent",
            instructions="Custom instructions",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=100
        )
        
        assert config.name == "CustomAgent"
        assert config.instructions == "Custom instructions"
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 100
    
    def test_tool_validation(self):
        """Test tool validation in config."""
        @tool
        def test_tool():
            return "test"
        
        # Should accept tool instances
        config = AgentConfig(tools=[test_tool])
        assert len(config.tools) == 1
        
        # Should accept callables
        def plain_func():
            return "plain"
        
        config = AgentConfig(tools=[plain_func])
        assert len(config.tools) == 1
        
        # Should reject non-callables
        with pytest.raises(ValueError, match="Invalid tool type"):
            AgentConfig(tools=["not a tool"])


class TestAgent:
    """Test the Agent class."""
    
    def test_agent_creation(self, mock_openai_key):
        """Test basic agent creation."""
        agent = Agent(
            name="TestAgent",
            instructions="Test instructions",
            model="gpt-4"
        )
        
        assert agent.name == "TestAgent"
        assert agent.config.instructions == "Test instructions"
        assert agent.config.model == "gpt-4"
        assert agent.id is not None  # UUID should be generated
        assert len(agent._messages) == 0
    
    def test_agent_with_tools(self, mock_openai_key):
        """Test agent creation with tools."""
        @tool
        def calculate(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y
        
        @tool
        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"
        
        agent = Agent(
            name="ToolAgent",
            tools=[calculate, greet]
        )
        
        assert len(agent._tool_registry.list_tools()) == 2
        assert "calculate" in agent._tool_registry.list_tools()
        assert "greet" in agent._tool_registry.list_tools()
    
    def test_agent_with_memory(self, mock_openai_key):
        """Test agent creation with memory."""
        memory = ConversationMemory(max_entries=10)  # 5 turns = 10 entries (user + assistant)
        
        agent = Agent(
            name="MemoryAgent",
            memory=[memory]
        )
        
        assert len(agent.config.memory) == 1
        assert isinstance(agent.config.memory[0], ConversationMemory)
    
    def test_agent_with_reasoning(self, mock_openai_key):
        """Test agent with custom reasoning pattern."""
        reasoning = ChainOfThought()
        
        agent = Agent(
            name="ReasoningAgent",
            reasoning_pattern=reasoning
        )
        
        assert agent._reasoning == reasoning
        assert isinstance(agent._reasoning, ChainOfThought)
    
    @pytest.mark.asyncio
    async def test_agent_run_basic(self, mock_openai_key, mock_provider):
        """Test basic agent run."""
        agent = Agent(name="TestAgent")
        agent._provider = mock_provider
        
        response = await agent.arun("Hello")
        
        assert isinstance(response, AgentResponse)
        assert response.content == "This is a test response"
        assert response.agent_id == agent.id
        assert response.reasoning is not None
    
    @pytest.mark.asyncio
    async def test_agent_run_with_context(self, mock_openai_key, mock_provider):
        """Test agent run with context."""
        agent = Agent(name="TestAgent")
        agent._provider = mock_provider
        
        context = {"document": "Important information"}
        response = await agent.arun("Summarize this", context=context)
        
        assert isinstance(response, AgentResponse)
        assert response.content == "This is a test response"
    
    @pytest.mark.asyncio
    async def test_agent_with_tool_execution(self, mock_openai_key):
        """Test agent executing tools."""
        @tool
        def get_weather(city: str) -> str:
            """Get weather for a city."""
            return f"Sunny in {city}"
        
        agent = Agent(name="WeatherAgent", tools=[get_weather])
        
        # Mock provider that returns tool calls
        mock_provider = AsyncMock()
        mock_provider.complete = AsyncMock()
        
        # First call returns tool request
        from agenticraft.core.types import ToolCall
        tool_response = CompletionResponse(
            content="Let me check the weather",
            tool_calls=[
                ToolCall(
                    id="call_123",
                    name="get_weather",
                    arguments={"city": "New York"}
                )
            ],
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
    
    def test_add_tool_dynamically(self, mock_openai_key):
        """Test adding tools after agent creation."""
        agent = Agent(name="DynamicAgent")
        
        assert len(agent._tool_registry.list_tools()) == 0
        
        @tool
        def new_tool():
            return "new"
        
        agent.add_tool(new_tool)
        
        assert len(agent._tool_registry.list_tools()) == 1
        assert "new_tool" in agent._tool_registry.list_tools()
    
    def test_clear_memory(self, mock_openai_key):
        """Test clearing agent memory."""
        agent = Agent(name="TestAgent")
        
        # Add some messages
        agent._messages.append(Message(
            role=MessageRole.USER,
            content="Hello"
        ))
        agent._messages.append(Message(
            role=MessageRole.ASSISTANT,
            content="Hi there"
        ))
        
        assert len(agent._messages) == 2
        
        agent.clear_memory()
        
        assert len(agent._messages) == 0
    
    def test_agent_repr(self, mock_openai_key):
        """Test agent string representation."""
        agent = Agent(
            name="TestAgent",
            model="gpt-4",
            tools=[lambda x: x]  # Dummy tool
        )
        
        repr_str = repr(agent)
        assert "TestAgent" in repr_str
        assert "gpt-4" in repr_str
        assert "tools=1" in repr_str
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_openai_key):
        """Test agent error handling."""
        agent = Agent(name="ErrorAgent")
        
        # Mock provider that raises an error
        mock_provider = AsyncMock()
        mock_provider.complete = AsyncMock(side_effect=Exception("API Error"))
        agent._provider = mock_provider
        
        with pytest.raises(AgentError, match="Agent execution failed"):
            await agent.arun("Test")
    
    def test_sync_run(self, mock_openai_key, mock_provider):
        """Test synchronous run method."""
        agent = Agent(name="SyncAgent")
        agent._provider = mock_provider
        
        # This should work even though it's calling async internally
        response = agent.run("Hello")
        
        assert isinstance(response, AgentResponse)
        assert response.content == "This is a test response"
