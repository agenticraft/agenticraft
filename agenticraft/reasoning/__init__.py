"""Advanced reasoning patterns for AgentiCraft.

This module provides sophisticated reasoning patterns that agents can use
to break down complex problems, explore multiple solutions, and make
transparent decisions.

Available patterns:
- Chain of Thought (CoT): Step-by-step reasoning
- Tree of Thoughts (ToT): Explore multiple reasoning paths
- ReAct: Reasoning + Acting in interleaved fashion
"""

# Import only what exists
__all__ = []

# Try to import base classes
try:
    from .base import ReasoningPattern, ReasoningResult, ReasoningStep

    __all__.extend(["ReasoningPattern", "ReasoningStep", "ReasoningResult"])
except ImportError:
    pass

# Try to import patterns
try:
    from .chain_of_thought import ChainOfThoughtReasoning

    __all__.append("ChainOfThoughtReasoning")
except ImportError:
    pass

try:
    from .tree_of_thoughts import TreeOfThoughtsReasoning

    __all__.append("TreeOfThoughtsReasoning")
except ImportError:
    pass

try:
    from .react import ReActReasoning

    __all__.append("ReActReasoning")
except ImportError:
    pass

# Try to import utilities
try:
    from .selector import PatternSelector, select_best_pattern

    __all__.extend(["PatternSelector", "select_best_pattern"])
except ImportError:
    pass
