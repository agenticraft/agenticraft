"""Unit tests for agent module.

This module tests the agent functionality including:
- Agent creation and configuration
- Agent execution
- Tool integration
- Memory integration
- Response handling
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from agenticraft.core.agent import (
    Agent,
    AgentConfig,
    AgentResponse,
)
from agenticraft.core.exceptions import AgentError
from agenticraft.core.memory import ConversationMemory
from agenticraft.core.reasoning import SimpleReasoning
from agenticraft.core.tool import tool
from agenticraft.core.types import Message, MessageRole, ToolCall


class TestAgentConfig:
    """Test AgentConfig model."""

    def test_agent_config_defaults(self):
        """Test default agent configuration."""
        config = AgentConfig()

        assert config.name == "Agent"
        assert config.instructions == "You are a helpful AI assistant."
        # The default comes from settings.default_model which might be overridden
        # Let's check what the actual default is
        from agenticraft.core.config import settings

        assert config.model == settings.default_model
        assert config.temperature == settings.default_temperature
        assert config.max_tokens == settings.default_max_tokens
        assert config.timeout == settings.default_timeout
        assert config.max_retries == settings.default_max_retries
        assert config.tools == []
        assert config.memory == []
        assert config.reasoning_pattern is None

    def test_agent_config_custom(self):
        """Test custom agent configuration."""
        config = AgentConfig(
            name="CustomAgent",
            instructions="You are a specialized assistant.",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1000,
            api_key="test-key",
            base_url="https://api.example.com",
            timeout=60,
            max_retries=5,
            metadata={"version": "1.0", "type": "custom"},
        )

        assert config.name == "CustomAgent"
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.timeout == 60
        assert config.metadata["version"] == "1.0"

    def test_agent_config_tool_validation(self):
        """Test tool validation in config."""

        @tool
        def valid_tool() -> str:
            return "result"

        # Valid tool should work
        config = AgentConfig(tools=[valid_tool])
        assert len(config.tools) == 1

        # Invalid tool should raise
        with pytest.raises(ValueError, match="Invalid tool type"):
            AgentConfig(tools=["not a tool"])

    def test_agent_config_memory_validation(self):
        """Test memory validation in config."""
        memory = ConversationMemory()

        # Valid memory should work
        config = AgentConfig(memory=[memory])
        assert len(config.memory) == 1

        # Invalid memory should raise
        with pytest.raises(ValueError, match="Invalid memory type"):
            AgentConfig(memory=["not a memory"])


class TestAgentResponse:
    """Test AgentResponse model."""

    def test_agent_response_basic(self):
        """Test basic agent response."""
        response = AgentResponse(content="Hello! How can I help you?")

        assert response.content == "Hello! How can I help you?"
        assert response.reasoning is None
        assert response.tool_calls == []
        assert response.metadata == {}
        assert response.agent_id is None
        assert isinstance(response.created_at, datetime)

    def test_agent_response_complete(self):
        """Test complete agent response."""
        agent_id = UUID("12345678-1234-5678-1234-567812345678")

        response = AgentResponse(
            content="I'll help you with that calculation.",
            reasoning="User asked for calculation, using calculator tool",
            tool_calls=[{"name": "calculator", "arguments": {"expression": "2+2"}}],
            metadata={"model": "gpt-4", "tokens": 150},
            agent_id=agent_id,
        )

        assert response.reasoning is not None
        assert len(response.tool_calls) == 1
        assert response.metadata["model"] == "gpt-4"
        assert response.agent_id == agent_id


class TestAgent:
    """Test Agent class functionality."""

    def test_agent_creation_basic(self):
        """Test basic agent creation."""
        agent = Agent(name="TestAgent")

        assert agent.name == "TestAgent"
        assert agent.config.name == "TestAgent"
        assert isinstance(agent.id, UUID)
        assert agent._messages == []

    def test_agent_creation_with_tools(self):
        """Test agent creation with tools."""

        @tool
        def search(query: str) -> str:
            """Search for information."""
            return f"Results for: {query}"

        @tool
        def calculate(expr: str) -> float:
            """Calculate expression."""
            return eval(expr)

        agent = Agent(name="ToolAgent", tools=[search, calculate])

        assert len(agent.config.tools) == 2
        assert "search" in agent._tool_registry.list_tools()
        assert "calculate" in agent._tool_registry.list_tools()

    def test_agent_creation_with_memory(self):
        """Test agent creation with memory."""
        conv_memory = ConversationMemory(max_entries=50)

        agent = Agent(name="MemoryAgent", memory=[conv_memory])

        assert len(agent.config.memory) == 1
        assert agent._memory_store.get_memory("conversation") is not None

    def test_agent_creation_with_reasoning(self):
        """Test agent creation with reasoning pattern."""
        reasoning = SimpleReasoning()

        agent = Agent(name="ReasoningAgent", reasoning_pattern=reasoning)

        assert agent._reasoning == reasoning

    def test_agent_provider_lazy_loading(self):
        """Test that provider is lazily loaded."""
        agent = Agent(name="LazyAgent")

        # Provider should not be created yet
        assert agent._provider is None

        # Accessing provider should create it
        with patch("agenticraft.core.provider.ProviderFactory.create") as mock_create:
            mock_provider = MagicMock()
            mock_create.return_value = mock_provider

            provider = agent.provider

            assert provider == mock_provider
            mock_create.assert_called_once()

    def test_agent_add_tool(self):
        """Test adding tool to agent after creation."""
        agent = Agent(name="DynamicAgent")

        @tool
        def new_tool(x: int) -> int:
            """Double the input."""
            return x * 2

        agent.add_tool(new_tool)

        assert "new_tool" in agent._tool_registry.list_tools()
        assert new_tool in agent.config.tools

    def test_agent_clear_memory(self):
        """Test clearing agent memory."""
        agent = Agent(name="MemoryAgent", memory=[ConversationMemory()])

        # Add some messages
        agent._messages.append(Message(role=MessageRole.USER, content="Test"))

        # Add to memory store
        conv_memory = agent._memory_store.get_memory("conversation")
        if conv_memory:
            conv_memory.entries.append(MagicMock())

        # Clear memory
        agent.clear_memory()

        assert len(agent._messages) == 0
        # Check that memory entries are cleared (not the memory objects themselves)
        conv_memory = agent._memory_store.get_memory("conversation")
        if conv_memory:
            assert len(conv_memory.entries) == 0

    @pytest.mark.asyncio
    async def test_agent_run_simple(self):
        """Test simple agent run."""
        agent = Agent(name="SimpleAgent")

        # Mock provider
        mock_provider = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Hello! I can help you with that."
        mock_response.tool_calls = []
        mock_response.metadata = {}

        mock_provider.complete = AsyncMock(return_value=mock_response)

        # Set the mock provider directly on the private attribute
        agent._provider = mock_provider

        response = await agent.arun("Hello, how are you?")

        assert isinstance(response, AgentResponse)
        assert response.content == "Hello! I can help you with that."
        assert len(agent._messages) == 2  # User + Assistant

    @pytest.mark.asyncio
    async def test_agent_run_with_context(self):
        """Test agent run with context."""
        agent = Agent(name="ContextAgent")

        # Mock provider
        mock_provider = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Based on the document..."
        mock_response.tool_calls = []
        mock_response.metadata = {}

        mock_provider.complete = AsyncMock(return_value=mock_response)

        context = {
            "document": "Important information here",
            "metadata": {"source": "test.pdf"},
        }

        # Set the mock provider directly on the private attribute
        agent._provider = mock_provider

        response = await agent.arun("Summarize the document", context=context)

        # Check that context was passed to provider
        call_args = mock_provider.complete.call_args
        messages = call_args[1]["messages"]

        # System message should contain context
        system_msg = messages[0]
        assert "document: Important information here" in system_msg["content"]

    @pytest.mark.asyncio
    async def test_agent_run_with_tools(self):
        """Test agent run with tool execution."""

        @tool
        def calculator(expression: str) -> float:
            """Calculate math expression."""
            return eval(expression)

        agent = Agent(name="ToolAgent", tools=[calculator])

        # Mock provider responses
        mock_provider = AsyncMock()

        # First response requests tool use
        first_response = MagicMock()
        first_response.content = "I'll calculate that for you."
        first_response.tool_calls = [
            ToolCall(
                id="call_1", name="calculator", arguments={"expression": "10 + 20"}
            )
        ]
        first_response.metadata = {}

        # Second response with result
        second_response = MagicMock()
        second_response.content = "The result is 30."
        second_response.tool_calls = []
        second_response.metadata = {}

        mock_provider.complete = AsyncMock(
            side_effect=[first_response, second_response]
        )

        # Set the mock provider directly on the private attribute
        agent._provider = mock_provider

        response = await agent.arun("What is 10 + 20?")

        assert response.content == "The result is 30."
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "calculator"

        # Provider should be called twice
        assert mock_provider.complete.call_count == 2

    @pytest.mark.asyncio
    async def test_agent_run_with_memory(self):
        """Test agent run with memory integration."""
        memory = ConversationMemory()
        agent = Agent(name="MemoryAgent", memory=[memory])

        # Mock provider
        mock_provider = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "I remember our conversation."
        mock_response.tool_calls = []
        mock_response.metadata = {}

        mock_provider.complete = AsyncMock(return_value=mock_response)

        # Pre-populate memory
        await memory.store(
            Message(role=MessageRole.USER, content="My name is Alice"),
            Message(role=MessageRole.ASSISTANT, content="Nice to meet you, Alice!"),
        )

        # Set the mock provider directly on the private attribute
        agent._provider = mock_provider

        response = await agent.arun("Do you remember my name?")

        # Check that memory context was included
        call_args = mock_provider.complete.call_args

        # The provider should have been called with messages
        assert call_args is not None
        messages = call_args[1]["messages"]

        # Convert all messages to string representation to search for Alice
        # Memory might be in different formats (as content, in metadata, etc.)
        all_text = str(messages)

        # Check that Alice appears somewhere in the messages
        # This is more lenient but ensures memory was included
        assert (
            "Alice" in all_text or "alice" in all_text.lower()
        ), "Memory not found in messages"

    @pytest.mark.asyncio
    async def test_agent_run_with_reasoning(self):
        """Test agent run with reasoning pattern."""
        reasoning = SimpleReasoning()
        agent = Agent(name="ReasoningAgent", reasoning_pattern=reasoning)

        # Mock provider
        mock_provider = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Here's my reasoned response."
        mock_response.tool_calls = []
        mock_response.metadata = {}

        mock_provider.complete = AsyncMock(return_value=mock_response)

        # Set the mock provider directly on the private attribute
        agent._provider = mock_provider

        response = await agent.arun("Explain quantum computing")

        assert response.reasoning is not None
        assert "Explain quantum computing" in response.reasoning

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent error handling."""
        agent = Agent(name="ErrorAgent")

        # Mock provider that raises error
        mock_provider = AsyncMock()
        mock_provider.complete = AsyncMock(side_effect=Exception("Provider error"))

        # Set the mock provider directly on the private attribute
        agent._provider = mock_provider

        with pytest.raises(AgentError, match="Agent execution failed"):
            await agent.arun("This will fail")

    @pytest.mark.asyncio
    async def test_agent_tool_error_handling(self):
        """Test agent handling tool execution errors."""

        @tool
        def failing_tool() -> str:
            """Tool that always fails."""
            raise ValueError("Tool failure!")

        agent = Agent(name="ToolErrorAgent", tools=[failing_tool])

        # Mock provider
        mock_provider = AsyncMock()

        # Response that calls failing tool
        tool_response = MagicMock()
        tool_response.content = "I'll use the tool."
        tool_response.tool_calls = [
            ToolCall(id="call_1", name="failing_tool", arguments={})
        ]
        tool_response.metadata = {}

        # Recovery response
        recovery_response = MagicMock()
        recovery_response.content = "The tool failed, but I can still help."
        recovery_response.tool_calls = []
        recovery_response.metadata = {}

        mock_provider.complete = AsyncMock(
            side_effect=[tool_response, recovery_response]
        )

        # Set the mock provider directly on the private attribute
        agent._provider = mock_provider

        response = await agent.arun("Use the failing tool")

        # Should handle the error and continue
        assert response.content == "The tool failed, but I can still help."

    def test_agent_sync_run(self):
        """Test synchronous run method."""
        agent = Agent(name="SyncAgent")

        # Mock the async run
        mock_response = AgentResponse(content="Sync response")

        with patch.object(agent, "arun", AsyncMock(return_value=mock_response)):
            response = agent.run("Test prompt")

        assert response.content == "Sync response"

    def test_agent_repr(self):
        """Test agent string representation."""
        agent = Agent(name="TestAgent", model="gpt-4", tools=[tool(lambda: "test")])

        repr_str = repr(agent)

        assert "TestAgent" in repr_str
        assert "gpt-4" in repr_str
        assert "tools=1" in repr_str

    @pytest.mark.asyncio
    async def test_agent_message_building(self):
        """Test message building logic."""
        agent = Agent(name="MessageAgent")

        # Add some messages
        agent._messages.extend(
            [
                Message(role=MessageRole.USER, content="First question"),
                Message(role=MessageRole.ASSISTANT, content="First answer"),
                Message(role=MessageRole.USER, content="Second question"),
                Message(role=MessageRole.ASSISTANT, content="Second answer"),
            ]
        )

        # Mock memory context
        memory_context = [
            Message(role=MessageRole.USER, content="Memory: Previous context"),
            Message(role=MessageRole.ASSISTANT, content="Memory: Previous response"),
        ]

        # Build messages
        messages = agent._build_messages(
            memory_context=memory_context, user_context={"key": "value"}
        )

        # Check structure
        assert messages[0]["role"] == "system"
        assert "key: value" in messages[0]["content"]

        # Should include memory context
        assert any(msg["content"] == "Memory: Previous context" for msg in messages)

        # Should include recent messages (limited to last 10)
        assert any(msg["content"] == "Second question" for msg in messages)

    @pytest.mark.asyncio
    async def test_agent_tool_execution_details(self):
        """Test detailed tool execution flow."""
        call_count = 0

        @tool
        def counter() -> int:
            """Increment and return counter."""
            nonlocal call_count
            call_count += 1
            return call_count

        agent = Agent(name="CounterAgent", tools=[counter])

        # Execute tool directly through registry
        result = await agent._tool_registry.execute("counter")
        assert result == 1

        result = await agent._tool_registry.execute("counter")
        assert result == 2
