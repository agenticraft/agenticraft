"""Pattern selector for choosing appropriate reasoning patterns."""

from enum import Enum

from .base import ReasoningPattern
from .chain_of_thought import ChainOfThoughtReasoning
from .react import ReActReasoning
from .tree_of_thoughts import TreeOfThoughtsReasoning


class ProblemType(Enum):
    """Types of problems for pattern selection."""

    MATHEMATICAL = "mathematical"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    EXPLORATORY = "exploratory"
    INTERACTIVE = "interactive"
    PLANNING = "planning"
    OPTIMIZATION = "optimization"
    GENERAL = "general"


class PatternSelector:
    """Selects the most appropriate reasoning pattern for a problem."""

    # Pattern strengths for different problem types
    PATTERN_STRENGTHS = {
        ChainOfThoughtReasoning: {
            ProblemType.MATHEMATICAL: 0.9,
            ProblemType.ANALYTICAL: 0.8,
            ProblemType.CREATIVE: 0.4,
            ProblemType.EXPLORATORY: 0.5,
            ProblemType.INTERACTIVE: 0.3,
            ProblemType.PLANNING: 0.6,
            ProblemType.OPTIMIZATION: 0.5,
            ProblemType.GENERAL: 0.7,
        },
        TreeOfThoughtsReasoning: {
            ProblemType.MATHEMATICAL: 0.6,
            ProblemType.ANALYTICAL: 0.7,
            ProblemType.CREATIVE: 0.9,
            ProblemType.EXPLORATORY: 0.8,
            ProblemType.INTERACTIVE: 0.4,
            ProblemType.PLANNING: 0.9,
            ProblemType.OPTIMIZATION: 0.8,
            ProblemType.GENERAL: 0.6,
        },
        ReActReasoning: {
            ProblemType.MATHEMATICAL: 0.4,
            ProblemType.ANALYTICAL: 0.6,
            ProblemType.CREATIVE: 0.5,
            ProblemType.EXPLORATORY: 0.9,
            ProblemType.INTERACTIVE: 0.9,
            ProblemType.PLANNING: 0.5,
            ProblemType.OPTIMIZATION: 0.6,
            ProblemType.GENERAL: 0.5,
        },
    }

    # Keywords for problem type detection
    PROBLEM_KEYWORDS = {
        ProblemType.MATHEMATICAL: [
            "calculate",
            "compute",
            "solve",
            "equation",
            "formula",
            "math",
            "number",
            "percentage",
            "ratio",
            "sum",
        ],
        ProblemType.ANALYTICAL: [
            "analyze",
            "compare",
            "evaluate",
            "assess",
            "examine",
            "investigate",
            "study",
            "review",
            "critique",
        ],
        ProblemType.CREATIVE: [
            "create",
            "design",
            "imagine",
            "invent",
            "generate",
            "brainstorm",
            "innovate",
            "compose",
            "craft",
        ],
        ProblemType.EXPLORATORY: [
            "find",
            "search",
            "discover",
            "explore",
            "investigate",
            "research",
            "locate",
            "identify",
            "uncover",
        ],
        ProblemType.INTERACTIVE: [
            "interact",
            "use",
            "tool",
            "action",
            "execute",
            "perform",
            "operate",
            "manipulate",
            "control",
        ],
        ProblemType.PLANNING: [
            "plan",
            "strategy",
            "organize",
            "schedule",
            "arrange",
            "prepare",
            "coordinate",
            "structure",
            "outline",
        ],
        ProblemType.OPTIMIZATION: [
            "optimize",
            "improve",
            "enhance",
            "maximize",
            "minimize",
            "refine",
            "tune",
            "perfect",
            "streamline",
        ],
    }

    @classmethod
    def detect_problem_type(cls, problem: str) -> ProblemType:
        """Detect the type of problem from the problem statement.

        Args:
            problem: The problem description

        Returns:
            Detected ProblemType
        """
        problem_lower = problem.lower()

        # Count keyword matches for each type
        type_scores: dict[ProblemType, int] = {}

        for problem_type, keywords in cls.PROBLEM_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in problem_lower)
            type_scores[problem_type] = score

        # Return type with highest score, or GENERAL if no matches
        if max(type_scores.values()) == 0:
            return ProblemType.GENERAL

        return max(type_scores.items(), key=lambda x: x[1])[0]

    @classmethod
    def select_pattern(
        cls,
        problem: str,
        available_actions: list[str] | None = None,
        force_pattern: type[ReasoningPattern] | None = None,
    ) -> type[ReasoningPattern]:
        """Select the best reasoning pattern for a problem.

        Args:
            problem: The problem to solve
            available_actions: List of available action names
            force_pattern: Force selection of a specific pattern

        Returns:
            The recommended reasoning pattern class
        """
        if force_pattern:
            return force_pattern

        # Detect problem type
        problem_type = cls.detect_problem_type(problem)

        # Adjust for available actions
        if available_actions:
            # If actions are available, boost ReAct pattern
            react_boost = 0.3
        else:
            react_boost = -0.2

        # Calculate scores for each pattern
        pattern_scores: dict[type[ReasoningPattern], float] = {}

        for pattern_class, strengths in cls.PATTERN_STRENGTHS.items():
            base_score = strengths.get(problem_type, 0.5)

            # Apply adjustments
            if pattern_class == ReActReasoning:
                score = base_score + react_boost
            else:
                score = base_score

            # Clamp to [0, 1]
            pattern_scores[pattern_class] = max(0, min(1, score))

        # Select pattern with highest score
        best_pattern = max(pattern_scores.items(), key=lambda x: x[1])[0]

        return best_pattern

    @classmethod
    def get_pattern_description(cls, pattern_class: type[ReasoningPattern]) -> str:
        """Get a description of when to use a pattern.

        Args:
            pattern_class: The pattern class

        Returns:
            Description string
        """
        descriptions = {
            ChainOfThoughtReasoning: (
                "Best for: Mathematical problems, logical deduction, "
                "step-by-step analysis, and problems requiring systematic thinking."
            ),
            TreeOfThoughtsReasoning: (
                "Best for: Creative problem solving, planning tasks, "
                "optimization problems, and situations with multiple valid approaches."
            ),
            ReActReasoning: (
                "Best for: Interactive tasks, tool use, exploration, "
                "and problems requiring iterative refinement through action and observation."
            ),
        }

        return descriptions.get(
            pattern_class, "A reasoning pattern for structured problem solving."
        )

    @classmethod
    def create_pattern(
        cls, pattern_class: type[ReasoningPattern], **kwargs
    ) -> ReasoningPattern:
        """Create an instance of a reasoning pattern.

        Args:
            pattern_class: The pattern class to instantiate
            **kwargs: Arguments for the pattern constructor

        Returns:
            Instance of the reasoning pattern
        """
        return pattern_class(**kwargs)


def select_best_pattern(
    problem: str,
    available_actions: list[str] | None = None,
    force_pattern: str | None = None,
) -> ReasoningPattern:
    """Convenience function to select and create the best pattern.

    Args:
        problem: The problem to solve
        available_actions: List of available action names
        force_pattern: Force selection by name ("cot", "tot", "react")

    Returns:
        Instance of the selected reasoning pattern
    """
    # Map pattern names to classes
    pattern_map = {
        "cot": ChainOfThoughtReasoning,
        "chain_of_thought": ChainOfThoughtReasoning,
        "tot": TreeOfThoughtsReasoning,
        "tree_of_thoughts": TreeOfThoughtsReasoning,
        "react": ReActReasoning,
        "reasoning_acting": ReActReasoning,
    }

    # Handle forced pattern
    forced_class = None
    if force_pattern:
        forced_class = pattern_map.get(force_pattern.lower())

    # Select pattern class
    pattern_class = PatternSelector.select_pattern(
        problem, available_actions, forced_class
    )

    # Create and return instance
    return PatternSelector.create_pattern(pattern_class)
