"""Reasoning patterns for AgentiCraft.

This module contains implementations of various reasoning patterns
that can be used by agents to solve complex problems.
"""

# Import only what exists
__all__ = []

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
