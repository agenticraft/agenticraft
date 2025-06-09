"""Tests for Chain of Thought reasoning pattern."""

from unittest.mock import MagicMock

import pytest

# Handle imports for not-yet-implemented modules
try:
    from agenticraft.reasoning.patterns.chain_of_thought import (
        ChainOfThoughtReasoning,
        ConfidenceLevel,
        ReasoningChain,
        ThoughtStep,
    )

    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False
    # Create dummy classes to prevent syntax errors
    ChainOfThoughtReasoning = None
    ThoughtStep = None
    ReasoningChain = None
    ConfidenceLevel = None

# Skip all tests if module not implemented
pytestmark = pytest.mark.skipif(
    not REASONING_AVAILABLE, reason="Chain of Thought reasoning not yet implemented"
)


@pytest.mark.asyncio
class TestChainOfThoughtReasoning:
    """Test Chain of Thought reasoning pattern."""

    async def test_basic_reasoning_chain(self, mock_provider):
        """Test basic chain of thought reasoning."""
        # Setup
        cot = ChainOfThoughtReasoning(provider=mock_provider)

        # Mock provider responses for each step
        mock_provider.complete.side_effect = [
            MagicMock(content="Let me break this down step by step..."),
            MagicMock(content="First, I need to identify the key components..."),
            MagicMock(content="Next, I'll analyze the relationships..."),
            MagicMock(content="Therefore, the answer is 42."),
        ]

        # Execute reasoning
        result = await cot.reason(query="What is the meaning of life?", max_steps=4)

        # Verify
        assert result.final_answer == "Therefore, the answer is 42."
        assert len(result.steps) == 4
        assert result.confidence > 0
        assert result.total_tokens > 0

    async def test_thought_step_creation(self):
        """Test individual thought step creation."""
        step = ThoughtStep(
            number=1,
            thought="I need to consider X",
            rationale="Because X affects Y",
            confidence=0.8,
        )

        assert step.number == 1
        assert step.thought == "I need to consider X"
        assert step.rationale == "Because X affects Y"
        assert step.confidence == 0.8
        assert step.confidence_level == ConfidenceLevel.HIGH

    async def test_confidence_scoring(self, mock_provider):
        """Test confidence scoring in reasoning."""
        cot = ChainOfThoughtReasoning(provider=mock_provider)

        # Test various confidence levels
        test_cases = [
            ("I'm certain that...", 0.9),
            ("I think maybe...", 0.5),
            ("I'm not sure but...", 0.3),
            ("Definitely...", 0.95),
        ]

        for text, expected_min in test_cases:
            confidence = cot._calculate_confidence(text)
            assert confidence >= expected_min - 0.1  # Allow small variance

    async def test_step_validation(self, mock_provider):
        """Test validation of reasoning steps."""
        cot = ChainOfThoughtReasoning(provider=mock_provider)

        # Valid step
        valid_step = ThoughtStep(number=1, thought="Valid reasoning", confidence=0.7)
        assert cot._validate_step(valid_step) is True

        # Invalid steps
        invalid_steps = [
            ThoughtStep(number=1, thought="", confidence=0.7),  # Empty thought
            ThoughtStep(
                number=1, thought="Too uncertain", confidence=0.1
            ),  # Low confidence
        ]

        for step in invalid_steps:
            assert cot._validate_step(step) is False

    async def test_reasoning_with_backtracking(self, mock_provider):
        """Test reasoning that backtracks on low confidence."""
        cot = ChainOfThoughtReasoning(
            provider=mock_provider, min_confidence=0.6, allow_backtrack=True
        )

        # Mock responses with one low-confidence step
        mock_provider.complete.side_effect = [
            MagicMock(content="Starting analysis..."),
            MagicMock(content="I'm not sure about this..."),  # Low confidence
            MagicMock(content="Let me reconsider..."),  # Backtrack
            MagicMock(content="Actually, the answer is clear."),
        ]

        result = await cot.reason("Complex question", max_steps=5)

        # Should have backtracked
        assert any(step.is_backtrack for step in result.steps)
        assert result.steps[-1].confidence > 0.6

    async def test_explanation_generation(self, mock_provider):
        """Test generating explanations from reasoning chain."""
        cot = ChainOfThoughtReasoning(provider=mock_provider)

        # Create a reasoning chain
        chain = ReasoningChain(
            query="How does photosynthesis work?",
            steps=[
                ThoughtStep(1, "Plants use sunlight", confidence=0.9),
                ThoughtStep(2, "Chlorophyll captures light energy", confidence=0.85),
                ThoughtStep(3, "CO2 + H2O → glucose + O2", confidence=0.95),
            ],
            final_answer="Photosynthesis converts light to chemical energy",
        )

        explanation = await cot.generate_explanation(chain)

        assert "step-by-step" in explanation.lower()
        assert "sunlight" in explanation
        assert "chlorophyll" in explanation

    async def test_parallel_reasoning_paths(self, mock_provider):
        """Test exploring multiple reasoning paths in parallel."""
        cot = ChainOfThoughtReasoning(
            provider=mock_provider, explore_parallel_paths=True, num_paths=3
        )

        # Mock different reasoning paths
        paths = [
            ["Path 1 step 1", "Path 1 step 2", "Path 1 conclusion"],
            ["Path 2 step 1", "Path 2 step 2", "Path 2 conclusion"],
            ["Path 3 step 1", "Path 3 step 2", "Path 3 conclusion"],
        ]

        # Setup mock responses for parallel paths
        all_responses = []
        for path in paths:
            for step in path:
                all_responses.append(MagicMock(content=step))

        mock_provider.complete.side_effect = all_responses

        result = await cot.reason("Multi-path question", max_steps=3)

        # Should have explored multiple paths and picked best
        assert result.num_paths_explored == 3
        assert result.selected_path_confidence > 0.7

    async def test_reasoning_with_examples(self, mock_provider):
        """Test reasoning with few-shot examples."""
        cot = ChainOfThoughtReasoning(provider=mock_provider)

        examples = [
            {
                "query": "What is 2+2?",
                "reasoning": ["I need to add 2 and 2", "2+2 equals 4"],
                "answer": "4",
            }
        ]

        mock_provider.complete.return_value = MagicMock(
            content="Following the example: 3+3 equals 6"
        )

        result = await cot.reason("What is 3+3?", examples=examples)

        # Should use examples in prompt
        call_args = mock_provider.complete.call_args
        assert "example" in str(call_args).lower()
        assert "2+2" in str(call_args)

    async def test_streaming_reasoning(self, mock_provider):
        """Test streaming chain of thought reasoning."""
        cot = ChainOfThoughtReasoning(provider=mock_provider, stream_steps=True)

        # Mock streaming responses
        async def mock_stream(*args, **kwargs):
            from agenticraft.core.streaming import StreamChunk

            chunks = ["Let me ", "think about ", "this step ", "by step..."]
            for chunk in chunks:
                yield StreamChunk(content=chunk)
            yield StreamChunk(content="", is_final=True)

        mock_provider.stream = mock_stream
        mock_provider.supports_streaming.return_value = True

        # Stream reasoning
        step_count = 0
        async for step in cot.stream_reason("Test query"):
            step_count += 1
            assert isinstance(step, ThoughtStep)

        assert step_count > 0

    async def test_max_steps_limit(self, mock_provider):
        """Test reasoning stops at max steps."""
        cot = ChainOfThoughtReasoning(provider=mock_provider)

        # Mock endless responses
        mock_provider.complete.side_effect = [
            MagicMock(content=f"Step {i}") for i in range(20)
        ]

        result = await cot.reason("Test", max_steps=5)

        assert len(result.steps) == 5
        assert result.terminated_reason == "max_steps_reached"

    async def test_reasoning_with_tools(self, mock_provider, async_mock_tool):
        """Test chain of thought with tool usage."""
        cot = ChainOfThoughtReasoning(provider=mock_provider, tools=[async_mock_tool])

        # Mock responses that include tool usage
        mock_provider.complete.side_effect = [
            MagicMock(content="I need to use the test_tool"),
            MagicMock(
                content="Using tool...",
                tool_calls=[{"name": "test_tool", "arguments": {}}],
            ),
            MagicMock(content="Based on tool result: success"),
        ]

        result = await cot.reason("Test with tools")

        # Should have tool usage in steps
        assert any(step.used_tool for step in result.steps)
        assert async_mock_tool.execute.called

    async def test_save_and_load_reasoning_chain(self, mock_provider, temp_dir):
        """Test saving and loading reasoning chains."""
        cot = ChainOfThoughtReasoning(provider=mock_provider)

        # Create a chain
        chain = ReasoningChain(
            query="Test query",
            steps=[
                ThoughtStep(1, "Step 1", confidence=0.8),
                ThoughtStep(2, "Step 2", confidence=0.9),
            ],
            final_answer="Answer",
            metadata={"test": True},
        )

        # Save
        save_path = temp_dir / "reasoning_chain.json"
        await cot.save_chain(chain, save_path)

        # Load
        loaded_chain = await cot.load_chain(save_path)

        assert loaded_chain.query == chain.query
        assert len(loaded_chain.steps) == len(chain.steps)
        assert loaded_chain.final_answer == chain.final_answer


@pytest.fixture
def sample_reasoning_chain():
    """Create a sample reasoning chain for testing."""
    return ReasoningChain(
        query="What is the capital of France?",
        steps=[
            ThoughtStep(
                number=1, thought="I need to recall European capitals", confidence=0.9
            ),
            ThoughtStep(
                number=2, thought="France is in Western Europe", confidence=0.95
            ),
            ThoughtStep(
                number=3, thought="The capital of France is Paris", confidence=1.0
            ),
        ],
        final_answer="Paris",
        confidence=0.95,
        total_tokens=150,
    )
