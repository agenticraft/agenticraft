"""Base classes for reasoning patterns."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from ..core.reasoning import ReasoningTrace


class StepType(Enum):
    """Types of reasoning steps."""

    UNDERSTANDING = "understanding"
    DECOMPOSITION = "decomposition"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    CONCLUSION = "conclusion"
    ACTION = "action"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    BRANCH = "branch"
    BACKTRACK = "backtrack"


@dataclass
class ReasoningStep:
    """A single step in a reasoning process.

    Attributes:
        step_type: The type of reasoning step
        content: The content/thought of this step
        confidence: Confidence level (0-1)
        evidence: Supporting evidence or data
        sub_steps: Child steps for hierarchical reasoning
        metadata: Additional step metadata
        timestamp: When this step was created
        duration: How long this step took
        step_id: Unique identifier
    """

    step_type: StepType
    content: str
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    sub_steps: list["ReasoningStep"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration: float | None = None
    step_id: str = field(default_factory=lambda: str(uuid4()))

    def add_evidence(self, evidence: str) -> None:
        """Add supporting evidence to this step."""
        self.evidence.append(evidence)

    def add_sub_step(self, step: "ReasoningStep") -> None:
        """Add a sub-step to this reasoning step."""
        self.sub_steps.append(step)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.step_id,
            "type": self.step_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "sub_steps": [s.to_dict() for s in self.sub_steps],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "duration": self.duration,
        }


@dataclass
class ReasoningResult:
    """Result of a reasoning process.

    Attributes:
        conclusion: Final conclusion or answer
        confidence: Overall confidence (0-1)
        steps: All reasoning steps taken
        total_duration: Total time taken
        pattern_used: Which reasoning pattern was used
        metadata: Additional result metadata
    """

    conclusion: str
    confidence: float
    steps: list[ReasoningStep]
    total_duration: float
    pattern_used: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_explanation(self) -> str:
        """Get human-readable explanation of reasoning."""
        explanation = [f"Using {self.pattern_used} reasoning pattern:"]

        for i, step in enumerate(self.steps, 1):
            explanation.append(f"\n{i}. {step.step_type.value.title()}: {step.content}")
            if step.evidence:
                explanation.append(f"   Evidence: {', '.join(step.evidence)}")
            if step.confidence < 0.5:
                explanation.append(f"   (Low confidence: {step.confidence:.2f})")

        explanation.append(f"\nConclusion: {self.conclusion}")
        explanation.append(f"Overall confidence: {self.confidence:.2%}")

        return "\n".join(explanation)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration": self.total_duration,
            "pattern_used": self.pattern_used,
            "metadata": self.metadata,
            "explanation": self.get_explanation(),
        }


class ReasoningPattern(ABC):
    """Base class for reasoning patterns.

    All reasoning patterns should inherit from this class and implement
    the reason method.
    """

    def __init__(self, name: str):
        """Initialize reasoning pattern.

        Args:
            name: Name of the reasoning pattern
        """
        self.name = name
        self._trace: ReasoningTrace | None = None

    @abstractmethod
    async def reason(
        self, problem: str, context: dict[str, Any] | None = None, **kwargs
    ) -> ReasoningResult:
        """Apply reasoning pattern to a problem.

        Args:
            problem: The problem or question to reason about
            context: Optional context information
            **kwargs: Pattern-specific parameters

        Returns:
            ReasoningResult with conclusion and steps
        """
        pass

    def start_trace(self, problem: str) -> ReasoningTrace:
        """Start a reasoning trace."""
        from ..core.reasoning import SimpleReasoning

        reasoning = SimpleReasoning()
        self._trace = reasoning.start_trace(problem)
        return self._trace

    def add_trace_step(self, step_type: str, data: dict[str, Any]) -> None:
        """Add a step to the reasoning trace."""
        if self._trace:
            self._trace.add_step(step_type, data)

    def complete_trace(self, result: dict[str, Any]) -> None:
        """Complete the reasoning trace."""
        if self._trace:
            self._trace.complete(result)

    def calculate_confidence(self, steps: list[ReasoningStep]) -> float:
        """Calculate overall confidence from steps.

        Args:
            steps: List of reasoning steps

        Returns:
            Overall confidence score (0-1)
        """
        if not steps:
            return 0.0

        # Weight recent steps more heavily
        weights = [0.5**i for i in range(len(steps))]
        weights.reverse()
        total_weight = sum(weights)

        weighted_confidence = sum(
            step.confidence * weight
            for step, weight in zip(steps, weights, strict=False)
        )

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    def format_for_llm(self, steps: list[ReasoningStep]) -> str:
        """Format reasoning steps for LLM context.

        Args:
            steps: List of reasoning steps

        Returns:
            Formatted string for LLM
        """
        formatted = []
        for i, step in enumerate(steps, 1):
            formatted.append(f"Step {i} ({step.step_type.value}): {step.content}")
            if step.evidence:
                formatted.append(f"Evidence: {', '.join(step.evidence)}")
        return "\n".join(formatted)
