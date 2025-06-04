"""Comprehensive tests for reasoning module to achieve >95% coverage."""

from datetime import datetime
import time

import pytest

from agenticraft.core.reasoning import (
    BaseReasoning, ReasoningStep, ReasoningTrace,
    SimpleReasoning, ChainOfThought, ReflectiveReasoning
)


class TestReasoningStep:
    """Test ReasoningStep model."""
    
    def test_reasoning_step_creation(self):
        """Test creating a reasoning step."""
        step = ReasoningStep(
            step_type="test_step",
            description="Test description",
            data={"key": "value"}
        )
        
        assert step.step_type == "test_step"
        assert step.description == "Test description"
        assert step.data == {"key": "value"}
        assert isinstance(step.timestamp, datetime)
    
    def test_reasoning_step_defaults(self):
        """Test reasoning step with defaults."""
        step = ReasoningStep(
            step_type="test",
            description="Test"
        )
        
        assert step.data == {}
        assert isinstance(step.timestamp, datetime)


class TestReasoningTrace:
    """Test ReasoningTrace model."""
    
    def test_trace_creation(self):
        """Test creating a reasoning trace."""
        trace = ReasoningTrace(prompt="Test prompt")
        
        assert trace.prompt == "Test prompt"
        assert isinstance(trace.id, str)
        assert trace.steps == []
        assert isinstance(trace.started_at, datetime)
        assert trace.completed_at is None
        assert trace.result is None
    
    def test_add_step(self):
        """Test adding steps to trace."""
        trace = ReasoningTrace(prompt="Test")
        
        trace.add_step("test_type", {"data": "value"})
        
        assert len(trace.steps) == 1
        assert trace.steps[0].step_type == "test_type"
        assert trace.steps[0].data == {"data": "value"}
        assert isinstance(trace.steps[0].description, str)
    
    def test_step_descriptions(self):
        """Test automatic step descriptions."""
        trace = ReasoningTrace(prompt="Test")
        
        # Test known step types
        trace.add_step("analyzing_prompt", {})
        assert trace.steps[-1].description == "Analyzing the user's request"
        
        trace.add_step("calling_llm", {"model": "gpt-4"})
        assert trace.steps[-1].description == "Calling gpt-4"
        
        trace.add_step("executing_tool", {"tool": "calculator"})
        assert trace.steps[-1].description == "Executing tool: calculator"
        
        trace.add_step("tool_result", {"tool": "search"})
        assert trace.steps[-1].description == "Received result from search"
        
        trace.add_step("tool_error", {"tool": "broken_tool"})
        assert trace.steps[-1].description == "Tool broken_tool failed"
        
        trace.add_step("formulating_response", {})
        assert trace.steps[-1].description == "Formulating the response"
        
        # Test unknown step type
        trace.add_step("unknown_step", {})
        assert trace.steps[-1].description == "Processing: unknown_step"
    
    def test_complete_trace(self):
        """Test completing a trace."""
        trace = ReasoningTrace(prompt="Test")
        
        # Add some steps
        trace.add_step("step1", {"data": "1"})
        trace.add_step("step2", {"data": "2"})
        
        # Complete the trace
        result = {"response": "Final answer", "confidence": 0.9}
        trace.complete(result)
        
        assert trace.completed_at is not None
        assert trace.completed_at > trace.started_at
        assert trace.result == result
    
    def test_multiple_steps(self):
        """Test adding multiple steps."""
        trace = ReasoningTrace(prompt="Complex task")
        
        # Simulate a complex reasoning process
        trace.add_step("analyzing_prompt", {"prompt": "Complex task"})
        trace.add_step("calling_llm", {"model": "gpt-4", "temperature": 0.7})
        trace.add_step("executing_tool", {"tool": "search", "arguments": {"q": "info"}})
        trace.add_step("tool_result", {"tool": "search", "result": ["result1", "result2"]})
        trace.add_step("calling_llm", {"model": "gpt-4", "temperature": 0.5})
        trace.add_step("formulating_response", {})
        
        assert len(trace.steps) == 6
        
        # Check steps are in order
        assert trace.steps[0].step_type == "analyzing_prompt"
        assert trace.steps[-1].step_type == "formulating_response"


class TestSimpleReasoning:
    """Test SimpleReasoning implementation."""
    
    def test_start_trace(self):
        """Test starting a trace with simple reasoning."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace("Test prompt")
        
        assert isinstance(trace, ReasoningTrace)
        assert trace.prompt == "Test prompt"
        assert len(trace.steps) == 1
        assert trace.steps[0].step_type == "analyzing_prompt"
        assert trace.steps[0].data == {"prompt": "Test prompt"}
    
    def test_format_empty_trace(self):
        """Test formatting an empty trace."""
        reasoning = SimpleReasoning()
        trace = ReasoningTrace(prompt="Test")
        trace.steps = []  # Clear steps
        
        formatted = reasoning.format_trace(trace)
        assert formatted == "No reasoning steps recorded."
    
    def test_format_trace_without_result(self):
        """Test formatting a trace without result."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace("Test")
        trace.add_step("calling_llm", {"model": "gpt-4"})
        trace.add_step("formulating_response", {})
        
        formatted = reasoning.format_trace(trace)
        
        assert "Reasoning process:" in formatted
        assert "1. Analyzing the user's request" in formatted
        assert "2. Calling gpt-4" in formatted
        assert "3. Formulating the response" in formatted
        assert "Result:" not in formatted
    
    def test_format_trace_with_result(self):
        """Test formatting a complete trace."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace("What is 2+2?")
        trace.add_step("calling_llm", {"model": "gpt-4"})
        trace.complete({"response": "4"})
        
        formatted = reasoning.format_trace(trace)
        
        assert "Reasoning process:" in formatted
        assert "Result: 4" in formatted


class TestChainOfThought:
    """Test ChainOfThought reasoning pattern."""
    
    def test_start_trace(self):
        """Test starting a chain of thought trace."""
        reasoning = ChainOfThought()
        trace = reasoning.start_trace("Solve this problem")
        
        assert isinstance(trace, ReasoningTrace)
        assert trace.prompt == "Solve this problem"
        assert len(trace.steps) == 1
        assert trace.steps[0].step_type == "analyzing_prompt"
        assert trace.steps[0].data["approach"] == "chain_of_thought"
    
    def test_format_empty_trace(self):
        """Test formatting an empty CoT trace."""
        reasoning = ChainOfThought()
        trace = ReasoningTrace(prompt="Test")
        trace.steps = []
        
        formatted = reasoning.format_trace(trace)
        assert formatted == "No reasoning steps recorded."
    
    def test_format_complete_trace(self):
        """Test formatting a complete CoT trace."""
        reasoning = ChainOfThought()
        trace = reasoning.start_trace("What is the capital of France?")
        
        # Simulate reasoning process
        trace.add_step("calling_llm", {"model": "gpt-4"})
        trace.add_step("executing_tool", {"tool": "search"})
        trace.add_step("tool_result", {"tool": "search", "result": "Paris info"})
        trace.add_step("formulating_response", {})
        trace.complete({"response": "The capital of France is Paris"})
        
        formatted = reasoning.format_trace(trace)
        
        assert "Chain of Thought:" in formatted
        assert "Question: What is the capital of France?" in formatted
        assert "Thinking process:" in formatted
        assert "First, I need to understand what's being asked" in formatted
        assert "Consulting gpt-4" in formatted
        assert "I need to use search to get information" in formatted
        assert "The tool provided: Paris info" in formatted
        assert "Based on all this, I can now formulate my response" in formatted
        assert "Conclusion: The capital of France is Paris" in formatted
    
    def test_format_trace_all_step_types(self):
        """Test formatting trace with all step types."""
        reasoning = ChainOfThought()
        trace = ReasoningTrace(prompt="Complex question")
        
        # Add all types of steps
        trace.add_step("analyzing_prompt", {})
        trace.add_step("calling_llm", {"model": "claude"})
        trace.add_step("executing_tool", {"tool": "calculator"})
        trace.add_step("tool_result", {"tool": "calculator", "result": "42"})
        trace.add_step("formulating_response", {})
        
        formatted = reasoning.format_trace(trace)
        
        # Check all step descriptions are present
        assert "First, I need to understand" in formatted
        assert "Consulting claude" in formatted
        assert "I need to use calculator" in formatted
        assert "The tool provided: 42" in formatted
        assert "Based on all this" in formatted


class TestReflectiveReasoning:
    """Test ReflectiveReasoning pattern."""
    
    def test_start_trace(self):
        """Test starting a reflective reasoning trace."""
        reasoning = ReflectiveReasoning()
        trace = reasoning.start_trace("Analyze this situation")
        
        assert isinstance(trace, ReasoningTrace)
        assert trace.prompt == "Analyze this situation"
        assert len(trace.steps) == 1
        assert trace.steps[0].step_type == "analyzing_prompt"
        assert trace.steps[0].data["approach"] == "reflective"
    
    def test_format_empty_trace(self):
        """Test formatting an empty reflective trace."""
        reasoning = ReflectiveReasoning()
        trace = ReasoningTrace(prompt="Test")
        trace.steps = []
        
        formatted = reasoning.format_trace(trace)
        assert formatted == "No reasoning steps recorded."
    
    def test_format_trace_with_perspectives(self):
        """Test formatting trace with multiple perspectives."""
        reasoning = ReflectiveReasoning()
        trace = reasoning.start_trace("Should I invest in stocks?")
        
        # Add steps representing different perspectives
        trace.add_step("executing_tool", {"tool": "market_data"})
        trace.add_step("calling_llm", {"model": "gpt-4"})
        trace.add_step("executing_tool", {"tool": "risk_calculator"})
        trace.complete({"response": "Consider diversifying your portfolio"})
        
        formatted = reasoning.format_trace(trace)
        
        assert "Reflective Analysis:" in formatted
        assert "Considering: Should I invest in stocks?" in formatted
        assert "Perspectives explored:" in formatted
        assert "Data perspective from market_data" in formatted
        assert "Analytical perspective" in formatted
        assert "Data perspective from risk_calculator" in formatted
        assert "Synthesis: Consider diversifying your portfolio" in formatted
    
    def test_format_trace_no_perspectives(self):
        """Test formatting trace with no tool/llm steps."""
        reasoning = ReflectiveReasoning()
        trace = reasoning.start_trace("Simple question")
        
        # Only add non-perspective steps
        trace.add_step("formulating_response", {})
        trace.complete({"response": "Simple answer"})
        
        formatted = reasoning.format_trace(trace)
        
        assert "Perspectives explored:" in formatted
        assert "- Direct analysis" in formatted  # Default when no perspectives
    
    def test_format_trace_only_llm_perspective(self):
        """Test formatting trace with only LLM perspective."""
        reasoning = ReflectiveReasoning()
        trace = reasoning.start_trace("Question")
        
        trace.add_step("calling_llm", {"model": "gpt-4"})
        trace.add_step("calling_llm", {"model": "claude"})  # Multiple LLM calls
        
        formatted = reasoning.format_trace(trace)
        
        # Should show analytical perspective (but only once)
        assert formatted.count("Analytical perspective") == 1


class TestBaseReasoningAbstract:
    """Test that BaseReasoning is properly abstract."""
    
    def test_cannot_instantiate_base_reasoning(self):
        """Test BaseReasoning cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseReasoning()
    
    def test_subclass_must_implement_methods(self):
        """Test subclass must implement all abstract methods."""
        class IncompleteReasoning(BaseReasoning):
            pass
        
        with pytest.raises(TypeError):
            IncompleteReasoning()
    
    def test_complete_implementation(self):
        """Test a complete implementation works."""
        class CompleteReasoning(BaseReasoning):
            def start_trace(self, prompt: str) -> ReasoningTrace:
                return ReasoningTrace(prompt=prompt)
            
            def format_trace(self, trace: ReasoningTrace) -> str:
                return "Formatted trace"
        
        # Should work
        reasoning = CompleteReasoning()
        trace = reasoning.start_trace("test")
        assert isinstance(trace, ReasoningTrace)
        assert reasoning.format_trace(trace) == "Formatted trace"


class TestReasoningIntegration:
    """Integration tests for reasoning with traces."""
    
    def test_complete_reasoning_flow(self):
        """Test a complete reasoning flow."""
        # Use Chain of Thought
        reasoning = ChainOfThought()
        
        # Start reasoning
        trace = reasoning.start_trace("How do I bake a cake?")
        
        # Simulate agent reasoning process
        trace.add_step("calling_llm", {"model": "gpt-4", "temperature": 0.7})
        
        # Simulate needing more info
        trace.add_step("executing_tool", {"tool": "recipe_search", "arguments": {"query": "chocolate cake"}})
        
        # Tool returns results
        trace.add_step("tool_result", {
            "tool": "recipe_search",
            "result": ["Recipe 1", "Recipe 2"]
        })
        
        # Final LLM call
        trace.add_step("calling_llm", {"model": "gpt-4", "temperature": 0.3})
        
        # Formulate response
        trace.add_step("formulating_response", {})
        
        # Complete with result
        trace.complete({
            "response": "Here's how to bake a chocolate cake: [detailed steps]",
            "confidence": 0.95
        })
        
        # Format the trace
        formatted = reasoning.format_trace(trace)
        
        # Verify the complete flow is represented
        assert "Chain of Thought:" in formatted
        assert "How do I bake a cake?" in formatted
        assert len(trace.steps) == 6  # Including initial analyzing_prompt
        assert trace.completed_at is not None
        assert trace.result["confidence"] == 0.95
    
    def test_reasoning_patterns_produce_different_output(self):
        """Test different reasoning patterns produce different formatted output."""
        prompt = "What should I do?"
        
        # Create same trace structure
        steps = [
            ("calling_llm", {"model": "gpt-4"}),
            ("executing_tool", {"tool": "analyzer"}),
            ("tool_result", {"tool": "analyzer", "result": "data"})
        ]
        
        # Format with different patterns
        simple = SimpleReasoning()
        cot = ChainOfThought()
        reflective = ReflectiveReasoning()
        
        trace1 = simple.start_trace(prompt)
        trace2 = cot.start_trace(prompt)
        trace3 = reflective.start_trace(prompt)
        
        for step_type, data in steps:
            trace1.add_step(step_type, data)
            trace2.add_step(step_type, data)
            trace3.add_step(step_type, data)
        
        formatted1 = simple.format_trace(trace1)
        formatted2 = cot.format_trace(trace2)
        formatted3 = reflective.format_trace(trace3)
        
        # They should all be different
        assert formatted1 != formatted2
        assert formatted2 != formatted3
        assert formatted1 != formatted3
        
        # Check for pattern-specific content
        assert "Reasoning process:" in formatted1
        assert "Chain of Thought:" in formatted2
        assert "Reflective Analysis:" in formatted3
