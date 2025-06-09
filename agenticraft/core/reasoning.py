"""Reasoning patterns for AgentiCraft agents.

This module provides various reasoning patterns that agents can use
to structure their thinking process. Each pattern provides a different
approach to problem-solving and decision-making.

Example:
    Using reasoning patterns::

        from agenticraft import Agent, ChainOfThought

        agent = Agent(
            name="Reasoner",
            reasoning_pattern=ChainOfThought()
        )

        response = agent.run("Solve this complex problem...")
        print(response.reasoning)  # See the chain of thought
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ReasoningStep(BaseModel):
    """A single step in the reasoning process."""

    step_type: str
    description: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "type": self.step_type,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class ReasoningTrace(BaseModel):
    """A trace of the reasoning process."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    prompt: str
    steps: list[ReasoningStep] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None

    def __init__(
        self, query: str | None = None, prompt: str | None = None, **data: Any
    ):
        """Initialize reasoning trace with query or prompt."""
        # Handle both query and prompt parameters
        if query is not None:
            prompt = query
        elif prompt is None:
            prompt = ""
        super().__init__(prompt=prompt, **data)

    # Add alias for prompt -> query
    @property
    def query(self) -> str:
        """Alias for prompt to match test expectations."""
        return self.prompt

    @property
    def duration(self) -> float:
        """Calculate duration in seconds."""
        if not self.completed_at:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "query": self.prompt,
            "steps": [step.to_dict() for step in self.steps],
            "result": self.result,
            "duration": self.duration,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    def add_step(self, step_type: str, data: dict[str, Any]) -> None:
        """Add a step to the reasoning trace."""
        step = ReasoningStep(
            step_type=step_type,
            description=self._describe_step(step_type, data),
            data=data,
        )
        self.steps.append(step)

    def _describe_step(self, step_type: str, data: dict[str, Any]) -> str:
        """Generate a human-readable description of a step."""
        descriptions = {
            "analyzing_prompt": "Analyzing the user's request",
            "calling_llm": f"Calling {data.get('model', 'LLM')}",
            "executing_tool": f"Executing tool: {data.get('tool', 'unknown')}",
            "tool_result": f"Received result from {data.get('tool', 'tool')}",
            "tool_error": f"Tool {data.get('tool', 'unknown')} failed",
            "formulating_response": "Formulating the response",
        }
        return descriptions.get(step_type, f"Processing: {step_type}")

    def complete(self, result: dict[str, Any]) -> None:
        """Mark the trace as complete."""
        self.completed_at = datetime.now()
        self.result = result


class BaseReasoning(ABC):
    """Base class for reasoning patterns."""

    def __init__(self, name: str = "base", description: str = "Base reasoning pattern"):
        """Initialize base reasoning."""
        self.name = name
        self.description = description

    @abstractmethod
    def start_trace(self, prompt: str) -> ReasoningTrace:
        """Start a new reasoning trace."""
        pass

    @abstractmethod
    def format_trace(self, trace: ReasoningTrace) -> str:
        """Format a trace for human consumption."""
        pass


class SimpleReasoning(BaseReasoning):
    """Simple reasoning that just tracks steps."""

    def __init__(self):
        """Initialize simple reasoning."""
        super().__init__(name="simple", description="Basic step-by-step reasoning")

    def analyze_problem(self, problem: str) -> dict[str, Any]:
        """Analyze a problem and return analysis."""
        return {
            "type": "general" if "?" in problem else "statement",
            "complexity": "low" if len(problem.split()) < 10 else "medium",
            "approach": "direct",
        }

    def start_trace(self, prompt: str) -> ReasoningTrace:
        """Start a new reasoning trace."""
        trace = ReasoningTrace(prompt=prompt)
        trace.add_step("analyzing_prompt", {"prompt": prompt})
        return trace

    def format_trace(self, trace: ReasoningTrace) -> str:
        """Format trace as a simple list of steps."""
        if not trace.steps:
            return "No reasoning steps recorded."

        # Include pattern name in output for tests
        lines = [f"[{self.name}] Reasoning process for: {trace.prompt}"]
        for i, step in enumerate(trace.steps, 1):
            lines.append(f"{i}. {step.description} ({step.step_type})")

        if trace.result:
            # Include all result keys in output
            result_parts = []
            for key, value in trace.result.items():
                result_parts.append(f"{key}: {value}")
            lines.append(f"\nResult: {', '.join(result_parts)}")

        return "\n".join(lines)


class ChainOfThought(BaseReasoning):
    """Chain of Thought reasoning pattern.

    This pattern encourages the agent to think step-by-step through
    a problem, making its reasoning process transparent and logical.
    """

    def __init__(self):
        """Initialize chain of thought reasoning."""
        super().__init__(
            name="chain_of_thought",
            description="Step-by-step reasoning with clear thought progression",
        )

    def break_down_problem(self, problem: str) -> list[str]:
        """Break down a complex problem into steps."""
        steps = []

        # Simple heuristic breakdown
        if "calculate" in problem.lower() or "total" in problem.lower():
            steps.append("Identify the numbers and quantities involved")
            if "each" in problem.lower():
                steps.append("Multiply quantity by unit price")
            if "tax" in problem.lower():
                steps.append("Calculate the tax amount")
                steps.append("Add tax to the subtotal")
            steps.append("Compute the final result")
        else:
            steps.append("Understand the core question")
            steps.append("Identify key components")
            steps.append("Analyze relationships")
            steps.append("Formulate response")

        return steps

    def start_trace(self, prompt: str) -> ReasoningTrace:
        """Start a new reasoning trace."""
        trace = ReasoningTrace(prompt=prompt)
        trace.add_step(
            "problem_analysis", {"prompt": prompt, "approach": "chain_of_thought"}
        )

        # Add breakdown step
        breakdown = self.break_down_problem(prompt)
        trace.add_step("breakdown", {"steps": breakdown, "count": len(breakdown)})

        return trace

    def format_trace(self, trace: ReasoningTrace) -> str:
        """Format trace as a chain of thought."""
        if not trace.steps:
            return "No reasoning steps recorded."

        lines = [f"[{self.name}] Chain of Thought:"]
        lines.append(f"\nQuestion: {trace.prompt}")
        lines.append("\nThinking process:")

        # Count non-metadata steps for numbering
        step_count = 0
        for step in trace.steps:
            if step.step_type not in ["problem_analysis", "breakdown"]:
                step_count += 1
                lines.append(f"{step_count}. {step.description}")
                # Include key data from the step
                if step.data:
                    for key, value in step.data.items():
                        if isinstance(value, (str, int, float)):
                            lines.append(f"   - {key}: {value}")
                        elif isinstance(value, dict):
                            lines.append(f"   - {key}: {value}")
                        elif isinstance(value, list) and len(value) > 0:
                            lines.append(
                                f"   - {key}: {', '.join(str(v) for v in value)}"
                            )
            elif step.step_type == "problem_analysis":
                lines.append("- First, I need to understand what's being asked...")
            elif step.step_type == "breakdown":
                lines.append("- Breaking down the problem into steps:")
                for i, breakdown_step in enumerate(step.data.get("steps", []), 1):
                    lines.append(f"  Step {i}: {breakdown_step}")

        if trace.result:
            lines.append("\nConclusion:")
            for key, value in trace.result.items():
                if isinstance(value, list):
                    lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
                else:
                    lines.append(f"- {key}: {value}")

        return "\n".join(lines)


class ReflectiveReasoning(BaseReasoning):
    """Reflective reasoning that considers multiple perspectives.

    This pattern encourages the agent to think about a problem from
    multiple angles and reflect on its own thinking.
    """

    def start_trace(self, prompt: str) -> ReasoningTrace:
        """Start a new reasoning trace."""
        trace = ReasoningTrace(prompt=prompt)
        trace.add_step("analyzing_prompt", {"prompt": prompt, "approach": "reflective"})
        return trace

    def format_trace(self, trace: ReasoningTrace) -> str:
        """Format trace with reflection."""
        if not trace.steps:
            return "No reasoning steps recorded."

        lines = ["Reflective Analysis:"]
        lines.append(f"\nConsidering: {trace.prompt}")
        lines.append("\nPerspectives explored:")

        perspectives = []
        for step in trace.steps:
            if step.step_type == "executing_tool":
                perspectives.append(f"- Data perspective from {step.data.get('tool')}")
            elif step.step_type == "calling_llm":
                perspectives.append("- Analytical perspective")

        lines.extend(perspectives or ["- Direct analysis"])

        if trace.result:
            lines.append(f"\nSynthesis: {trace.result.get('response', 'No response')}")

        return "\n".join(lines)
