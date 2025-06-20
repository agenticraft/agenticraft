"""Reasoning patterns for AgentiCraft.

This module contains implementations of various reasoning patterns
that can be used by agents to solve complex problems.
"""

# Export base classes
from .base import ReasoningPattern, ReasoningResult, ReasoningStep, StepType

# Export patterns (with error handling)
patterns = []

try:
    from .chain_of_thought import ChainOfThoughtReasoning
    patterns.append("ChainOfThoughtReasoning")
except ImportError:
    ChainOfThoughtReasoning = None

try:
    from .tree_of_thoughts import TreeOfThoughtsReasoning
    patterns.append("TreeOfThoughtsReasoning")
except ImportError:
    TreeOfThoughtsReasoning = None

try:
    from .react import ReActReasoning
    patterns.append("ReActReasoning")
except ImportError:
    ReActReasoning = None

try:
    from .selector import PatternSelector, select_best_pattern
    patterns.extend(["PatternSelector", "select_best_pattern"])
except ImportError:
    PatternSelector = None
    select_best_pattern = None

# Build __all__ dynamically based on what's available
__all__ = ["ReasoningPattern", "ReasoningResult", "ReasoningStep", "StepType"] + patterns
