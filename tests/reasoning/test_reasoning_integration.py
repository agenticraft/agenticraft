"""Integration tests for ReasoningAgent with advanced patterns."""

from unittest.mock import patch

import pytest

from agenticraft.agents.reasoning import (
    ADVANCED_PATTERNS_AVAILABLE,
    AnalysisResponse,
    ReasoningAgent,
    ReasoningResponse,
    ReasoningStepDetail,
)
from agenticraft.core.provider import BaseProvider


class MockProvider(BaseProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response="Mock response", **kwargs):
        super().__init__(**kwargs)
        self.response = response
        self.model = kwargs.get("model", "mock-model")

    async def complete(self, messages, **kwargs):
        """Mock completion."""
        from agenticraft.core.types import CompletionResponse

        return CompletionResponse(content=self.response, tool_calls=[], metadata={})

    def validate_auth(self):
        """Mock auth validation."""
        pass


@pytest.mark.skipif(
    not ADVANCED_PATTERNS_AVAILABLE, reason="Advanced patterns not available"
)
class TestReasoningAgentIntegration:
    """Integration tests for ReasoningAgent with advanced patterns."""

    @pytest.mark.asyncio
    async def test_chain_of_thought_integration(self):
        """Test ReasoningAgent with Chain of Thought pattern."""
        # Create mock provider
        mock_provider = MockProvider()

        # Patch ProviderFactory to return our mock
        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(
                name="TestAgent",
                reasoning_pattern="chain_of_thought",
                pattern_config={"max_steps": 5},
                model="gpt-4",  # Use a valid model name
            )

        response = await agent.think_and_act("Solve a problem")

        assert isinstance(response, ReasoningResponse)
        assert response.reasoning_steps is not None
        assert response.metadata["pattern"] == "chain_of_thought"

    @pytest.mark.asyncio
    async def test_tree_of_thoughts_integration(self):
        """Test ReasoningAgent with Tree of Thoughts pattern."""
        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(
                name="TestAgent",
                reasoning_pattern="tree_of_thoughts",
                pattern_config={"max_depth": 3, "beam_width": 2},
                model="gpt-4",
            )

        response = await agent.think_and_act("Design something")

        assert isinstance(response, ReasoningResponse)
        assert response.metadata["pattern"] == "tree_of_thoughts"

    @pytest.mark.asyncio
    async def test_react_integration(self):
        """Test ReasoningAgent with ReAct pattern."""
        # Create mock tools
        from agenticraft import tool

        @tool
        def test_tool(**kwargs):
            """Test tool."""
            return "Tool result"

        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(
                name="TestAgent",
                reasoning_pattern="react",
                tools=[test_tool],
                model="gpt-4",
            )

        response = await agent.think_and_act("Research something")

        assert isinstance(response, ReasoningResponse)
        assert response.metadata["pattern"] == "react"
        assert hasattr(agent.advanced_reasoning, "tools")
        assert "test_tool" in agent.advanced_reasoning.tools

    def test_pattern_selection(self):
        """Test automatic pattern selection."""
        agent = ReasoningAgent(name="TestAgent")

        # Tool-based problem
        pattern = agent.select_best_pattern("Search for the current weather")
        assert pattern == "react"

        # Creative problem
        pattern = agent.select_best_pattern("Design a new logo")
        assert pattern == "tree_of_thoughts"

        # Step-by-step problem
        pattern = agent.select_best_pattern("Explain how to bake a cake")
        assert pattern == "chain_of_thought"

    @pytest.mark.asyncio
    async def test_fallback_to_basic_reasoning(self):
        """Test fallback when patterns not available."""
        mock_provider = MockProvider()

        # Temporarily disable patterns
        with patch("agenticraft.agents.reasoning.ADVANCED_PATTERNS_AVAILABLE", False):
            with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
                mock_factory.return_value = mock_provider

                agent = ReasoningAgent(
                    name="TestAgent",
                    reasoning_pattern="tree_of_thoughts",  # Will fallback
                    model="gpt-4",
                )

            assert agent.advanced_reasoning is None

            response = await agent.think_and_act("Test problem")
            assert isinstance(response, ReasoningResponse)

    @pytest.mark.asyncio
    async def test_expose_thinking_parameter(self):
        """Test expose_thinking parameter."""
        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(model="gpt-4")

        # With thinking exposed
        response = await agent.think_and_act("Test problem", expose_thinking=True)
        assert response is not None

        # Without thinking exposed
        response = await agent.think_and_act("Test problem", expose_thinking=False)
        assert response is not None

    @pytest.mark.asyncio
    async def test_use_advanced_reasoning_parameter(self):
        """Test use_advanced_reasoning parameter."""
        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(reasoning_pattern="chain_of_thought", model="gpt-4")

        # With advanced reasoning
        response = await agent.think_and_act(
            "Test problem", use_advanced_reasoning=True
        )
        assert response.metadata.get("pattern") == "chain_of_thought"

        # Without advanced reasoning (fallback)
        response = await agent.think_and_act(
            "Test problem", use_advanced_reasoning=False
        )
        assert response is not None

    @pytest.mark.asyncio
    async def test_analyze_method(self):
        """Test multi-perspective analysis."""
        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(model="gpt-4")

        response = await agent.analyze(
            "Analyze renewable energy", perspectives=["economic", "environmental"]
        )

        assert isinstance(response, AnalysisResponse)
        assert hasattr(response, "perspectives")
        assert hasattr(response, "synthesis")

    def test_reasoning_step_detail(self):
        """Test ReasoningStepDetail model."""
        step = ReasoningStepDetail(
            number=1,
            description="Test step",
            details=["detail1", "detail2"],
            conclusion="Test conclusion",
            confidence=0.85,
        )

        assert str(step) == "Step 1: Test step (Details: 2) → Test conclusion"
        assert step.confidence == 0.85

    def test_reasoning_response_methods(self):
        """Test ReasoningResponse methods."""
        steps = [
            ReasoningStepDetail(number=1, description="First step"),
            ReasoningStepDetail(number=2, description="Second step"),
        ]

        from uuid import uuid4

        response = ReasoningResponse(
            content="Final answer",
            reasoning="Reasoning text",
            reasoning_steps=steps,
            tool_calls=[],
            metadata={},
            agent_id=uuid4(),
        )

        assert response.step_count == 2
        assert response.get_step(1).description == "First step"
        assert response.get_step(3) is None

        formatted = response.format_reasoning()
        assert "Reasoning Process:" in formatted
        assert "First step" in formatted
        assert "Second step" in formatted

    def test_analysis_response_methods(self):
        """Test AnalysisResponse methods."""
        from uuid import uuid4

        response = AnalysisResponse(
            content="Analysis content",
            perspectives={"economic": "Economic analysis", "social": "Social analysis"},
            synthesis="Combined insights",
            reasoning_steps=[],
            tool_calls=[],
            metadata={},
            agent_id=uuid4(),
        )

        assert response.get_perspective("economic") == "Economic analysis"
        assert response.get_perspective("missing") is None

        formatted = response.format_analysis()
        assert "Multi-Perspective Analysis:" in formatted
        assert "ECONOMIC PERSPECTIVE:" in formatted
        assert "Economic analysis" in formatted
        assert "Combined insights" in formatted

    @pytest.mark.asyncio
    async def test_reasoning_history(self):
        """Test reasoning history tracking."""
        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(model="gpt-4")

        # Generate some responses
        for i in range(3):
            await agent.think_and_act(f"Problem {i}")

        history = agent.get_reasoning_history(limit=2)
        assert len(history) == 2

        # Test explain last response
        explanation = agent.explain_last_response()
        assert explanation != "No reasoning history available."

    @pytest.mark.asyncio
    async def test_pattern_config_propagation(self):
        """Test that pattern config is properly propagated."""
        config = {"max_steps": 20, "min_confidence": 0.9}

        agent = ReasoningAgent(
            reasoning_pattern="chain_of_thought", pattern_config=config
        )

        assert agent.advanced_reasoning.max_steps == 20
        assert agent.advanced_reasoning.min_confidence == 0.9

    @pytest.mark.asyncio
    async def test_instructions_augmentation(self):
        """Test that instructions are properly augmented based on pattern."""
        # Chain of Thought
        cot_agent = ReasoningAgent(
            instructions="Base instructions", reasoning_pattern="chain_of_thought"
        )
        assert "step-by-step chain of thought" in cot_agent.config.instructions
        assert "REASONING:" in cot_agent.config.instructions

        # ReAct
        react_agent = ReasoningAgent(
            instructions="Base instructions", reasoning_pattern="react", tools=[]
        )
        assert "ReAct pattern" in react_agent.config.instructions
        assert "Thought:" in react_agent.config.instructions
        assert "Action:" in react_agent.config.instructions

    @pytest.mark.asyncio
    async def test_parse_reasoning_steps_fallback(self):
        """Test _parse_reasoning_steps with various content formats."""
        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(model="gpt-4")

        # Test with structured content
        content = """
        REASONING:
        1. First step analysis
        2. Second step calculation
        - Detail about calculation
        Therefore, the result is X
        
        ANSWER:
        The answer is X
        """

        from agenticraft.core.reasoning import ReasoningTrace

        trace = ReasoningTrace()
        steps = agent._parse_reasoning_steps(content, trace)

        assert len(steps) >= 2
        assert steps[0].number == 1
        assert "First step" in steps[0].description

    @pytest.mark.asyncio
    async def test_parse_perspectives(self):
        """Test _parse_perspectives method."""
        mock_provider = MockProvider()

        with patch("agenticraft.core.agent.ProviderFactory.create") as mock_factory:
            mock_factory.return_value = mock_provider

            agent = ReasoningAgent(model="gpt-4")

        content = """
        Economic perspective:
        This is the economic analysis.
        
        Environmental perspective:
        This is the environmental analysis.
        """

        perspectives = agent._parse_perspectives(content, ["economic", "environmental"])

        assert "economic" in perspectives
        assert "environmental" in perspectives
        assert "economic analysis" in perspectives["economic"]

    def test_synthesize_perspectives(self):
        """Test _synthesize_perspectives method."""
        agent = ReasoningAgent()

        # Multiple perspectives
        perspectives = {"economic": "...", "social": "...", "environmental": "..."}
        synthesis = agent._synthesize_perspectives(perspectives)
        assert "multiple important dimensions" in synthesis

        # Single perspective
        single = {"economic": "..."}
        synthesis = agent._synthesize_perspectives(single)
        assert "economic perspective provides" in synthesis

        # No perspectives
        synthesis = agent._synthesize_perspectives({})
        assert "No perspectives" in synthesis
