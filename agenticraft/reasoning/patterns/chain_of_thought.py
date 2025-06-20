"""Chain of Thought (CoT) reasoning pattern implementation.

This module implements step-by-step reasoning with explicit thinking processes,
allowing agents to break down complex problems into manageable steps.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agenticraft.core.reasoning import BaseReasoning, ReasoningTrace


@dataclass
class ThoughtStep:
    """A single step in the chain of thought reasoning process.

    Attributes:
        step_number: Sequential number of this step
        thought: The actual thought/reasoning content
        confidence: Confidence score for this step (0-1)
        evidence: Supporting evidence or facts used
        step_type: Type of reasoning step (analysis, synthesis, etc.)
        timestamp: When this step was created
    """

    step_number: int
    thought: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    step_type: str = "analysis"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "thought": self.thought,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "step_type": self.step_type,
            "timestamp": self.timestamp.isoformat(),
        }


class ChainOfThoughtReasoning(BaseReasoning):
    """Implements Chain of Thought reasoning pattern.

    This reasoning pattern breaks down complex problems into sequential steps,
    with each step building on previous ones. It maintains explicit reasoning
    traces and confidence scores.

    Example:
        >>> cot = ChainOfThoughtReasoning()
        >>> trace = await cot.think(
        ...     "How can we reduce carbon emissions in urban transportation?",
        ...     context={"city": "New York", "timeframe": "5 years"}
        ... )
        >>> print(trace.get_conclusion())
    """

    def __init__(self, min_confidence: float = 0.7, max_steps: int = 10):
        """Initialize Chain of Thought reasoning.

        Args:
            min_confidence: Minimum confidence threshold for accepting steps
            max_steps: Maximum number of reasoning steps allowed
        """
        super().__init__(
            name="chain_of_thought",
            description="Step-by-step reasoning with explicit thought progression",
        )
        self.steps: list[ThoughtStep] = []
        self.min_confidence = min_confidence
        self.max_steps = max_steps
        self.problem_complexity: str | None = None

    async def think(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> ReasoningTrace:
        """Generate chain of thought reasoning for a problem.

        Args:
            problem: The problem to reason about
            context: Additional context for reasoning

        Returns:
            ReasoningTrace containing the complete reasoning process
        """
        trace = ReasoningTrace()
        self.steps = []  # Reset steps for new problem

        # Step 1: Analyze the problem
        self.problem_complexity = self._assess_complexity(problem)
        trace.add_step(
            "problem_analysis",
            {
                "problem": problem,
                "complexity": self.problem_complexity,
                "context": context or {},
            },
        )

        # Step 2: Decompose into sub-problems
        sub_problems = self._decompose_problem(problem, context)
        trace.add_step(
            "decomposition", {"sub_problems": sub_problems, "count": len(sub_problems)}
        )

        # Step 3: Generate reasoning steps
        for i, sub_problem in enumerate(sub_problems):
            if len(self.steps) >= self.max_steps:
                trace.add_step(
                    "limit_reached",
                    {"message": f"Reached maximum steps limit ({self.max_steps})"},
                )
                break

            step = await self._generate_thought_step(
                sub_problem, i + 1, previous_steps=self.steps.copy()
            )

            if step.confidence >= self.min_confidence:
                self.steps.append(step)
                trace.add_step(f"thought_step_{i+1}", step.to_dict())
            else:
                # Try alternative reasoning if confidence is low
                alternative = await self._generate_alternative_thought(
                    sub_problem, i + 1
                )
                if alternative and alternative.confidence >= self.min_confidence:
                    self.steps.append(alternative)
                    trace.add_step(f"thought_step_{i+1}_alt", alternative.to_dict())

        # Step 4: Synthesize conclusion
        conclusion = self._synthesize_conclusion()
        trace.add_step(
            "conclusion",
            {
                "result": conclusion,
                "total_steps": len(self.steps),
                "average_confidence": self._calculate_average_confidence(),
            },
        )

        # Step 5: Generate confidence report
        confidence_report = self._generate_confidence_report()
        trace.add_step("confidence_analysis", confidence_report)

        return trace

    def _assess_complexity(self, problem: str) -> str:
        """Assess the complexity of the problem.

        Args:
            problem: The problem statement

        Returns:
            Complexity level: simple, moderate, complex, or highly_complex
        """
        # Heuristics for complexity assessment
        word_count = len(problem.split())
        question_marks = problem.count("?")
        technical_terms = len(re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", problem))

        complexity_score = (
            (word_count / 20)  # Longer problems tend to be more complex
            + (question_marks * 2)  # Multiple questions increase complexity
            + (technical_terms * 1.5)  # Technical terminology adds complexity
        )

        if complexity_score < 2:
            return "simple"
        elif complexity_score < 4:
            return "moderate"
        elif complexity_score < 6:
            return "complex"
        else:
            return "highly_complex"

    def _decompose_problem(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> list[str]:
        """Decompose problem into sub-problems.

        Args:
            problem: The main problem
            context: Additional context

        Returns:
            List of sub-problems to solve
        """
        # Simple heuristic decomposition
        # In a real implementation, this would use an LLM
        sub_problems = []

        # Look for explicit questions
        questions = re.findall(r"[^.!?]*\?", problem)
        if questions:
            sub_problems.extend([q.strip() for q in questions])

        # If no explicit questions, create logical sub-problems
        if not sub_problems:
            if self.problem_complexity in ["complex", "highly_complex"]:
                sub_problems = [
                    f"What is the core issue in: {problem[:50]}...?",
                    "What are the key factors involved?",
                    "What are potential approaches to address this?",
                    "What are the trade-offs of each approach?",
                    "What is the recommended solution?",
                ]
            else:
                sub_problems = [
                    f"What is being asked in: {problem[:50]}...?",
                    "What information is needed to answer this?",
                    "What is the solution?",
                ]

        return sub_problems

    async def _generate_thought_step(
        self, sub_problem: str, step_number: int, previous_steps: list[ThoughtStep]
    ) -> ThoughtStep:
        """Generate a single thought step.

        Args:
            sub_problem: The sub-problem to address
            step_number: The step number
            previous_steps: Previous reasoning steps

        Returns:
            A new ThoughtStep
        """
        # In a real implementation, this would use an LLM
        # For now, we'll create a structured response

        # Determine step type based on position and content
        if step_number == 1:
            step_type = "problem_understanding"
        elif "factor" in sub_problem.lower() or "component" in sub_problem.lower():
            step_type = "analysis"
        elif "approach" in sub_problem.lower() or "solution" in sub_problem.lower():
            step_type = "synthesis"
        elif "trade-off" in sub_problem.lower() or "compare" in sub_problem.lower():
            step_type = "evaluation"
        else:
            step_type = "reasoning"

        # Build on previous steps
        previous_context = ""
        if previous_steps:
            previous_context = f"Building on: {previous_steps[-1].thought[:50]}..."

        thought = f"Step {step_number}: Addressing '{sub_problem}'. {previous_context}"

        # Calculate confidence based on step type and previous steps
        base_confidence = 0.8
        if previous_steps:
            # Confidence decreases slightly with each step due to compounding uncertainty
            confidence_decay = 0.02 * len(previous_steps)
            base_confidence -= confidence_decay

        # Add some variation
        import random

        confidence = max(0.1, min(1.0, base_confidence + random.uniform(-0.1, 0.1)))

        return ThoughtStep(
            step_number=step_number,
            thought=thought,
            confidence=confidence,
            evidence=[f"Based on analysis of: {sub_problem}"],
            step_type=step_type,
        )

    async def _generate_alternative_thought(
        self, sub_problem: str, step_number: int
    ) -> ThoughtStep | None:
        """Generate alternative thought when confidence is low.

        Args:
            sub_problem: The sub-problem to address
            step_number: The step number

        Returns:
            Alternative ThoughtStep or None
        """
        # Try a different approach
        thought = f"Alternative approach for step {step_number}: Reconsidering '{sub_problem}' from a different angle."

        # Alternative approaches might have different confidence
        import random

        confidence = 0.7 + random.uniform(0, 0.2)

        return ThoughtStep(
            step_number=step_number,
            thought=thought,
            confidence=confidence,
            evidence=[f"Alternative analysis of: {sub_problem}"],
            step_type="alternative_reasoning",
        )

    def _synthesize_conclusion(self) -> str:
        """Synthesize final conclusion from all steps.

        Returns:
            Final conclusion based on reasoning steps
        """
        if not self.steps:
            return "Unable to reach a conclusion due to insufficient reasoning steps."

        # Group steps by type
        step_types = {}
        for step in self.steps:
            if step.step_type not in step_types:
                step_types[step.step_type] = []
            step_types[step.step_type].append(step)

        # Build conclusion
        conclusion_parts = []

        if "problem_understanding" in step_types:
            conclusion_parts.append("Problem understood.")

        if "analysis" in step_types:
            conclusion_parts.append(
                f"Analyzed {len(step_types['analysis'])} key factors."
            )

        if "synthesis" in step_types:
            conclusion_parts.append(
                f"Synthesized {len(step_types['synthesis'])} potential solutions."
            )

        if "evaluation" in step_types:
            conclusion_parts.append("Evaluated trade-offs.")

        conclusion = " ".join(conclusion_parts)
        conclusion += f" Based on {len(self.steps)} reasoning steps with average confidence of {self._calculate_average_confidence():.2f}."

        return conclusion

    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence across all steps.

        Returns:
            Average confidence score
        """
        if not self.steps:
            return 0.0

        total_confidence = sum(step.confidence for step in self.steps)
        return total_confidence / len(self.steps)

    def _generate_confidence_report(self) -> dict[str, Any]:
        """Generate detailed confidence analysis.

        Returns:
            Confidence report with statistics
        """
        if not self.steps:
            return {"status": "no_steps", "confidence": 0.0}

        confidences = [step.confidence for step in self.steps]

        return {
            "average_confidence": self._calculate_average_confidence(),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "total_steps": len(self.steps),
            "high_confidence_steps": sum(1 for c in confidences if c >= 0.8),
            "low_confidence_steps": sum(1 for c in confidences if c < 0.6),
            "confidence_trend": (
                "increasing" if confidences[-1] > confidences[0] else "decreasing"
            ),
        }

    def get_reasoning_summary(self) -> dict[str, Any]:
        """Get a summary of the reasoning process.

        Returns:
            Summary with key metrics
        """
        return {
            "total_steps": len(self.steps),
            "problem_complexity": self.problem_complexity,
            "average_confidence": self._calculate_average_confidence(),
            "step_types": list(set(step.step_type for step in self.steps)),
            "conclusion": self._synthesize_conclusion(),
        }

    def start_trace(self, prompt: str) -> ReasoningTrace:
        """Start a new reasoning trace.

        Args:
            prompt: The prompt to trace

        Returns:
            A new ReasoningTrace instance
        """
        trace = ReasoningTrace(prompt=prompt)
        trace.add_step(
            "problem_analysis", {"prompt": prompt, "approach": "chain_of_thought"}
        )
        return trace

    def format_trace(self, trace: ReasoningTrace) -> str:
        """Format a trace for human consumption.

        Args:
            trace: The trace to format

        Returns:
            Formatted string representation
        """
        if not trace.steps:
            return "No reasoning steps recorded."

        lines = [f"[{self.name}] Chain of Thought Reasoning:"]
        lines.append(f"\nProblem: {trace.prompt}")
        lines.append("\nReasoning Steps:")

        for i, step in enumerate(trace.steps, 1):
            lines.append(f"{i}. {step.step_type}: {step.description}")
            if step.data:
                for key, value in step.data.items():
                    if key not in ["prompt"]:  # Skip redundant data
                        lines.append(f"   - {key}: {value}")

        if trace.result:
            lines.append(f"\nResult: {trace.result}")

        return "\n".join(lines)
