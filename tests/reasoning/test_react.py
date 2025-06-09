"""Tests for ReAct (Reasoning and Acting) pattern."""

from unittest.mock import MagicMock

import pytest

# Handle imports for not-yet-implemented modules
try:
    from agenticraft.reasoning.patterns.react import (
        ReActConfig,
        ReActReasoning,
        ReActStep,
        ReActTrace,
        StepType,
    )

    REACT_AVAILABLE = True
except ImportError:
    REACT_AVAILABLE = False
    # Create dummy classes to prevent syntax errors
    ReActReasoning = None
    ReActStep = None
    StepType = None
    ReActTrace = None
    ReActConfig = None

try:
    from agenticraft.core.tool import tool
except ImportError:
    from unittest.mock import MagicMock

    tool = MagicMock

# Skip all tests if module not implemented
pytestmark = pytest.mark.skipif(
    not REACT_AVAILABLE, reason="ReAct reasoning not yet implemented"
)


@pytest.mark.asyncio
class TestReActPattern:
    """Test ReAct reasoning pattern."""

    async def test_react_step_types(self):
        """Test different ReAct step types."""
        thought = ReActStep(
            type=StepType.THOUGHT, content="I need to search for information"
        )

        action = ReActStep(
            type=StepType.ACTION,
            content="search",
            action_input={"query": "Python programming"},
        )

        observation = ReActStep(
            type=StepType.OBSERVATION, content="Found 10 results about Python"
        )

        assert thought.type == StepType.THOUGHT
        assert action.type == StepType.ACTION
        assert action.action_input["query"] == "Python programming"
        assert observation.type == StepType.OBSERVATION

    async def test_basic_react_cycle(self, mock_provider):
        """Test basic Thought → Action → Observation cycle."""

        # Create mock tools
        @tool
        def search(query: str) -> str:
            """Search for information."""
            return f"Results for {query}"

        @tool
        def calculate(expression: str) -> str:
            """Calculate math expression."""
            return "42"

        react = ReActReasoning(provider=mock_provider, tools=[search, calculate])

        # Mock provider responses
        mock_provider.complete.side_effect = [
            # First thought
            MagicMock(content="I need to search for the answer"),
            # Action decision
            MagicMock(
                content="Action: search",
                tool_calls=[
                    {"name": "search", "arguments": {"query": "meaning of life"}}
                ],
            ),
            # Thought after observation
            MagicMock(content="The search wasn't helpful, let me calculate"),
            # Another action
            MagicMock(
                content="Action: calculate",
                tool_calls=[
                    {"name": "calculate", "arguments": {"expression": "6 * 7"}}
                ],
            ),
            # Final thought
            MagicMock(content="The answer is 42!"),
        ]

        result = await react.reason("What is the meaning of life?")

        # Verify the trace
        assert len(result.steps) >= 5  # At least T→A→O→T→A→O→T
        assert result.final_answer == "The answer is 42!"
        assert result.tools_used == ["search", "calculate"]

    async def test_max_iterations_limit(self, mock_provider):
        """Test that ReAct stops at max iterations."""

        @tool
        def infinite_tool() -> str:
            """A tool that never provides final answer."""
            return "Keep searching..."

        react = ReActReasoning(
            provider=mock_provider, tools=[infinite_tool], max_iterations=3
        )

        # Mock endless loop
        mock_provider.complete.side_effect = [
            MagicMock(content="I need to use the tool"),
            MagicMock(
                content="Action: infinite_tool",
                tool_calls=[{"name": "infinite_tool", "arguments": {}}],
            ),
        ] * 10  # More than max iterations

        result = await react.reason("Infinite question")

        # Should stop at max iterations
        assert result.iterations <= 3
        assert result.terminated_reason == "max_iterations"

    async def test_self_correction(self, mock_provider):
        """Test self-correction when action fails."""

        @tool
        def fragile_tool(input: str) -> str:
            """Tool that fails on certain inputs."""
            if "fail" in input:
                raise ValueError("Tool failed!")
            return "Success"

        react = ReActReasoning(
            provider=mock_provider, tools=[fragile_tool], allow_self_correction=True
        )

        # Mock responses with failure and correction
        mock_provider.complete.side_effect = [
            MagicMock(content="Let me try the tool"),
            MagicMock(
                content="Action: fragile_tool",
                tool_calls=[
                    {"name": "fragile_tool", "arguments": {"input": "fail please"}}
                ],
            ),
            # After observing failure
            MagicMock(content="The tool failed, let me try differently"),
            MagicMock(
                content="Action: fragile_tool",
                tool_calls=[
                    {"name": "fragile_tool", "arguments": {"input": "succeed please"}}
                ],
            ),
            MagicMock(content="Great, it worked!"),
        ]

        result = await react.reason("Use the fragile tool")

        # Should have self-corrected
        assert any(step.is_correction for step in result.steps)
        assert result.final_answer == "Great, it worked!"

    async def test_multi_tool_coordination(self, mock_provider):
        """Test coordinating multiple tools."""

        @tool
        def get_weather(city: str) -> str:
            """Get weather for a city."""
            return f"Sunny in {city}, 25°C"

        @tool
        def get_events(city: str, weather: str) -> str:
            """Get events based on weather."""
            if "sunny" in weather.lower():
                return "Outdoor concert in the park"
            return "Indoor museum exhibition"

        react = ReActReasoning(provider=mock_provider, tools=[get_weather, get_events])

        # Mock coordinated tool usage
        mock_provider.complete.side_effect = [
            MagicMock(content="First, I'll check the weather"),
            MagicMock(
                content="Action: get_weather",
                tool_calls=[{"name": "get_weather", "arguments": {"city": "Paris"}}],
            ),
            MagicMock(content="It's sunny! Now for events..."),
            MagicMock(
                content="Action: get_events",
                tool_calls=[
                    {
                        "name": "get_events",
                        "arguments": {
                            "city": "Paris",
                            "weather": "Sunny in Paris, 25°C",
                        },
                    }
                ],
            ),
            MagicMock(content="Perfect day for the outdoor concert!"),
        ]

        result = await react.reason("What should I do in Paris today?")

        assert "outdoor concert" in result.final_answer.lower()
        assert len(result.tools_used) == 2

    async def test_reasoning_without_tools(self, mock_provider):
        """Test ReAct can reason without using tools."""
        react = ReActReasoning(
            provider=mock_provider,
            tools=[],  # No tools available
            allow_no_tool_response=True,
        )

        # Mock pure reasoning
        mock_provider.complete.side_effect = [
            MagicMock(content="This is a simple question I can answer directly"),
            MagicMock(content="The capital of France is Paris"),
        ]

        result = await react.reason("What is the capital of France?")

        assert result.final_answer == "The capital of France is Paris"
        assert len(result.tools_used) == 0

    async def test_parallel_actions(self, mock_provider):
        """Test executing multiple actions in parallel."""

        @tool
        async def slow_tool_1() -> str:
            """First slow tool."""
            return "Result 1"

        @tool
        async def slow_tool_2() -> str:
            """Second slow tool."""
            return "Result 2"

        react = ReActReasoning(
            provider=mock_provider,
            tools=[slow_tool_1, slow_tool_2],
            allow_parallel_actions=True,
        )

        # Mock decision to use both tools
        mock_provider.complete.side_effect = [
            MagicMock(content="I need both pieces of information"),
            MagicMock(
                content="Actions: slow_tool_1 and slow_tool_2",
                tool_calls=[
                    {"name": "slow_tool_1", "arguments": {}},
                    {"name": "slow_tool_2", "arguments": {}},
                ],
            ),
            MagicMock(content="Combined results show the answer"),
        ]

        result = await react.reason("Get both results")

        # Should have executed in parallel
        parallel_steps = [s for s in result.steps if s.is_parallel]
        assert len(parallel_steps) > 0

    async def test_config_validation(self):
        """Test ReAct configuration validation."""
        # Valid config
        config = ReActConfig(
            max_iterations=5, allow_self_correction=True, require_final_answer=True
        )
        assert config.max_iterations == 5

        # Invalid configs should raise
        with pytest.raises(ValueError):
            ReActConfig(max_iterations=0)  # Too low

        with pytest.raises(ValueError):
            ReActConfig(max_iterations=100)  # Too high

    async def test_streaming_react(self, mock_provider):
        """Test streaming ReAct execution."""

        @tool
        def dummy_tool() -> str:
            return "Tool result"

        react = ReActReasoning(
            provider=mock_provider, tools=[dummy_tool], stream_steps=True
        )

        # Mock streaming
        from agenticraft.core.streaming import StreamChunk

        async def mock_stream(*args, **kwargs):
            for word in ["Thinking", "about", "this..."]:
                yield StreamChunk(content=word + " ")
            yield StreamChunk(content="", is_final=True)

        mock_provider.stream = mock_stream
        mock_provider.supports_streaming.return_value = True

        # Stream execution
        steps_streamed = []
        async for step in react.stream_reason("Test"):
            steps_streamed.append(step)

        assert len(steps_streamed) > 0

    async def test_save_and_replay_trace(self, mock_provider, temp_dir):
        """Test saving and replaying ReAct traces."""

        @tool
        def test_tool() -> str:
            return "Result"

        react = ReActReasoning(provider=mock_provider, tools=[test_tool])

        # Create a trace
        trace = ReActTrace(
            query="Test query",
            steps=[
                ReActStep(StepType.THOUGHT, "Thinking..."),
                ReActStep(StepType.ACTION, "test_tool", action_input={}),
                ReActStep(StepType.OBSERVATION, "Result"),
                ReActStep(StepType.THOUGHT, "Done!"),
            ],
            final_answer="Done!",
            tools_used=["test_tool"],
        )

        # Save trace
        save_path = temp_dir / "react_trace.json"
        await react.save_trace(trace, save_path)

        # Load and replay
        loaded_trace = await react.load_trace(save_path)
        replay_result = await react.replay_trace(loaded_trace)

        assert replay_result.final_answer == trace.final_answer
        assert len(replay_result.steps) == len(trace.steps)

    async def test_custom_prompt_templates(self, mock_provider):
        """Test using custom prompt templates."""

        @tool
        def custom_tool() -> str:
            return "Custom result"

        custom_prompts = {
            "thought": "Think step by step: {context}",
            "action": "Decide which tool to use: {tools}",
            "reflection": "Reflect on: {observation}",
        }

        react = ReActReasoning(
            provider=mock_provider, tools=[custom_tool], prompt_templates=custom_prompts
        )

        mock_provider.complete.return_value = MagicMock(content="Using custom prompts")

        await react.reason("Test")

        # Verify custom prompts were used
        call_args = str(mock_provider.complete.call_args)
        assert "Think step by step" in call_args or "custom" in call_args.lower()


@pytest.fixture
def sample_react_trace():
    """Create a sample ReAct trace for testing."""
    return ReActTrace(
        query="What's the weather in Paris and what events are happening?",
        steps=[
            ReActStep(
                type=StepType.THOUGHT, content="I need to check the weather first"
            ),
            ReActStep(
                type=StepType.ACTION,
                content="get_weather",
                action_input={"city": "Paris"},
            ),
            ReActStep(type=StepType.OBSERVATION, content="Sunny, 25°C"),
            ReActStep(
                type=StepType.THOUGHT, content="Great weather! Let me find events"
            ),
            ReActStep(
                type=StepType.ACTION,
                content="search_events",
                action_input={"city": "Paris", "date": "today"},
            ),
            ReActStep(
                type=StepType.OBSERVATION, content="Jazz festival at Luxembourg Gardens"
            ),
            ReActStep(type=StepType.THOUGHT, content="Perfect combination!"),
        ],
        final_answer="It's sunny and 25°C in Paris. There's a Jazz festival at Luxembourg Gardens today!",
        tools_used=["get_weather", "search_events"],
        iterations=3,
        total_tokens=250,
    )
