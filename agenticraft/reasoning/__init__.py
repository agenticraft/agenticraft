"""Advanced reasoning patterns for AgentiCraft.

This module provides sophisticated reasoning patterns that agents can use
to break down complex problems, explore multiple solutions, and make
transparent decisions.

Available patterns:
- Chain of Thought (CoT): Step-by-step reasoning
- Tree of Thoughts (ToT): Explore multiple reasoning paths
- ReAct: Reasoning + Acting in interleaved fashion
"""

# Import base classes directly
try:
    from .patterns.base import ReasoningPattern, ReasoningResult, ReasoningStep, StepType
except ImportError:
    ReasoningPattern = None
    ReasoningResult = None
    ReasoningStep = None
    StepType = None

# Import patterns individually
try:
    from .patterns.chain_of_thought import ChainOfThoughtReasoning
except ImportError:
    ChainOfThoughtReasoning = None

try:
    from .patterns.tree_of_thoughts import TreeOfThoughtsReasoning
except ImportError:
    TreeOfThoughtsReasoning = None

try:
    from .patterns.react import ReActReasoning
except ImportError:
    ReActReasoning = None

try:
    from .patterns.selector import PatternSelector, select_best_pattern
except ImportError:
    PatternSelector = None
    select_best_pattern = None

# Build __all__ based on what's available
__all__ = []

if ReasoningPattern is not None:
    __all__.extend(["ReasoningPattern", "ReasoningResult", "ReasoningStep", "StepType"])

if ChainOfThoughtReasoning is not None:
    __all__.append("ChainOfThoughtReasoning")

if TreeOfThoughtsReasoning is not None:
    __all__.append("TreeOfThoughtsReasoning")

if ReActReasoning is not None:
    __all__.append("ReActReasoning")

if PatternSelector is not None:
    __all__.extend(["PatternSelector", "select_best_pattern"])
