"""Unit tests for reasoning module.

This module tests the reasoning functionality including:
- Reasoning patterns
- Trace creation and management
- Step tracking
- Formatting and visualization
"""

from datetime import datetime
from typing import Any, Dict

import pytest

from agenticraft.core.reasoning import (
    BaseReasoning,
    SimpleReasoning,
    ChainOfThought,
    ReasoningStep,
    ReasoningTrace,
)


class TestReasoningStep:
    """Test ReasoningStep class."""
    
    def test_reasoning_step_creation(self):
        """Test creating a reasoning step."""
        step = ReasoningStep(
            step_type="analysis",
            description="Analyzing the problem",
            data={"complexity": "high"}
        )
        
        assert step.step_type == "analysis"
        assert step.description == "Analyzing the problem"
        assert step.data == {"complexity": "high"}
        assert isinstance(step.timestamp, datetime)
    
    def test_reasoning_step_to_dict(self):
        """Test converting step to dictionary."""
        step = ReasoningStep(
            step_type="decision",
            description="Choosing approach",
            data={"selected": "option_a"}
        )
        
        step_dict = step.to_dict()
        
        assert step_dict["type"] == "decision"
        assert step_dict["description"] == "Choosing approach"
        assert step_dict["data"]["selected"] == "option_a"
        assert "timestamp" in step_dict


class TestReasoningTrace:
    """Test ReasoningTrace class."""
    
    def test_reasoning_trace_creation(self):
        """Test creating a reasoning trace."""
        trace = ReasoningTrace(query="What is 2 + 2?")
        
        assert trace.query == "What is 2 + 2?"
        assert trace.steps == []
        assert trace.result is None
        assert isinstance(trace.started_at, datetime)
        assert trace.completed_at is None
    
    def test_add_step(self):
        """Test adding steps to trace."""
        trace = ReasoningTrace(query="Test query")
        
        trace.add_step("parse", {"intent": "calculation"})
        trace.add_step("compute", {"operation": "addition"})
        
        assert len(trace.steps) == 2
        assert trace.steps[0].step_type == "parse"
        assert trace.steps[1].step_type == "compute"
    
    def test_complete_trace(self):
        """Test completing a trace."""
        trace = ReasoningTrace(query="Test query")
        
        trace.add_step("process", {"status": "working"})
        trace.complete({"answer": 42})
        
        assert trace.result == {"answer": 42}
        assert trace.completed_at is not None
    
    def test_trace_duration(self):
        """Test trace duration calculation."""
        trace = ReasoningTrace(query="Test query")
        
        # Simulate some work
        import time
        time.sleep(0.1)
        
        trace.complete({})
        
        duration = trace.duration
        assert duration > 0
        assert duration < 1  # Should be less than 1 second
    
    def test_trace_to_dict(self):
        """Test converting trace to dictionary."""
        trace = ReasoningTrace(query="What is AI?")
        
        trace.add_step("research", {"sources": 3})
        trace.add_step("synthesize", {"key_points": 5})
        trace.complete({"summary": "AI is..."})
        
        trace_dict = trace.to_dict()
        
        assert trace_dict["query"] == "What is AI?"
        assert len(trace_dict["steps"]) == 2
        assert trace_dict["result"]["summary"] == "AI is..."
        assert "duration" in trace_dict


class TestSimpleReasoning:
    """Test SimpleReasoning pattern."""
    
    def test_simple_reasoning_creation(self):
        """Test creating simple reasoning."""
        reasoning = SimpleReasoning()
        
        assert reasoning.name == "simple"
        assert reasoning.description == "Basic step-by-step reasoning"
    
    def test_start_trace(self):
        """Test starting a trace."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace("Test question")
        
        assert isinstance(trace, ReasoningTrace)
        assert trace.query == "Test question"
        assert len(trace.steps) >= 1  # Should have initial step
    
    def test_format_trace(self):
        """Test formatting a trace."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace("What is 2 + 2?")
        
        trace.add_step("calculate", {"operation": "2 + 2"})
        trace.complete({"answer": 4})
        
        formatted = reasoning.format_trace(trace)
        
        assert "What is 2 + 2?" in formatted
        assert "calculate" in formatted
        assert "answer" in formatted
    
    def test_analyze_problem(self):
        """Test problem analysis."""
        reasoning = SimpleReasoning()
        
        analysis = reasoning.analyze_problem("How do I learn Python?")
        
        assert "type" in analysis
        assert "complexity" in analysis
        assert "approach" in analysis


class TestChainOfThought:
    """Test ChainOfThought pattern."""
    
    def test_chain_of_thought_creation(self):
        """Test creating chain of thought reasoning."""
        reasoning = ChainOfThought()
        
        assert reasoning.name == "chain_of_thought"
        assert "step-by-step" in reasoning.description.lower()
    
    def test_start_trace_with_breakdown(self):
        """Test starting trace with problem breakdown."""
        reasoning = ChainOfThought()
        trace = reasoning.start_trace("Solve: If John has 5 apples and gives 2 away")
        
        # Should have initial analysis and breakdown steps
        assert len(trace.steps) >= 2
        
        step_types = [step.step_type for step in trace.steps]
        assert "problem_analysis" in step_types
        assert "breakdown" in step_types
    
    def test_format_trace_numbered(self):
        """Test that chain of thought formats with numbers."""
        reasoning = ChainOfThought()
        trace = reasoning.start_trace("Test problem")
        
        trace.add_step("step1", {"action": "First"})
        trace.add_step("step2", {"action": "Second"})
        trace.add_step("step3", {"action": "Third"})
        trace.complete({"solution": "Done"})
        
        formatted = reasoning.format_trace(trace)
        
        # Should have numbered steps
        assert "1." in formatted or "Step 1" in formatted
        assert "2." in formatted or "Step 2" in formatted
        assert "3." in formatted or "Step 3" in formatted
    
    def test_break_down_problem(self):
        """Test breaking down complex problems."""
        reasoning = ChainOfThought()
        
        breakdown = reasoning.break_down_problem(
            "Calculate the total cost of 3 items at $10 each with 8% tax"
        )
        
        assert isinstance(breakdown, list)
        assert len(breakdown) > 0
        assert any("multiply" in step.lower() for step in breakdown)
        assert any("tax" in step.lower() for step in breakdown)


# ReflectiveReasoning not implemented yet
# class TestReflectiveReasoning:
#     """Test ReflectiveReasoning pattern."""
#     ...
# Tests removed as ReflectiveReasoning is not implemented


class TestBaseReasoning:
    """Test BaseReasoning abstract class."""
    
    def test_base_reasoning_cannot_be_instantiated(self):
        """Test that BaseReasoning is abstract."""
        with pytest.raises(TypeError):
            BaseReasoning()
    
    def test_custom_reasoning_pattern(self):
        """Test creating custom reasoning pattern."""
        class CustomReasoning(BaseReasoning):
            def __init__(self):
                super().__init__(
                    name="custom",
                    description="Custom reasoning pattern"
                )
            
            def start_trace(self, query: str) -> ReasoningTrace:
                trace = ReasoningTrace(query=query)
                trace.add_step("custom_init", {"mode": "custom"})
                return trace
            
            def format_trace(self, trace: ReasoningTrace) -> str:
                return f"Custom: {trace.query}"
        
        reasoning = CustomReasoning()
        trace = reasoning.start_trace("Test")
        
        assert reasoning.name == "custom"
        assert len(trace.steps) == 1
        assert trace.steps[0].step_type == "custom_init"


class TestReasoningIntegration:
    """Test reasoning integration scenarios."""
    
    def test_switching_reasoning_patterns(self):
        """Test switching between reasoning patterns."""
        patterns = [
            SimpleReasoning(),
            ChainOfThought()
        ]
        
        query = "What is the meaning of life?"
        
        for pattern in patterns:
            trace = pattern.start_trace(query)
            formatted = pattern.format_trace(trace)
            
            assert query in formatted
            assert pattern.name in formatted or pattern.name == "simple"
    
    def test_reasoning_with_complex_data(self):
        """Test reasoning with complex data structures."""
        reasoning = ChainOfThought()
        trace = reasoning.start_trace("Analyze this data")
        
        # Add steps with complex data
        trace.add_step("load_data", {
            "source": "database",
            "records": 1000,
            "fields": ["id", "name", "value"]
        })
        
        trace.add_step("analyze", {
            "statistics": {
                "mean": 45.2,
                "median": 42.0,
                "std_dev": 12.3
            },
            "patterns": ["increasing trend", "seasonal variation"]
        })
        
        trace.complete({
            "insights": ["Pattern A", "Pattern B"],
            "recommendations": ["Action 1", "Action 2"]
        })
        
        formatted = reasoning.format_trace(trace)
        
        assert "database" in formatted
        assert "statistics" in formatted
        assert "insights" in formatted
