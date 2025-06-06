"""
AgentiCraft: Dead simple AI agents with reasoning traces.

A lightweight, production-ready framework for building AI agents with
transparent reasoning, MCP protocol support, and comprehensive observability.
"""

__version__ = "0.1.1"
__author__ = "AgentiCraft Team"
__email__ = "hello@agenticraft.ai"

# Version check
import sys

if sys.version_info < (3, 10):
    raise RuntimeError("AgentiCraft requires Python 3.10 or higher")

# Core imports
from .core.agent import Agent
from .core.tool import tool, BaseTool
from .core.workflow import Workflow, Step
from .core.exceptions import (
    AgenticraftError,
    AgentError,
    ToolError,
    WorkflowError,
    StepExecutionError,
)

# Advanced agents
from .agents import (
    ReasoningAgent,
    WorkflowAgent,
)

__all__ = [
    "__version__",
    # Core
    "Agent",
    "tool",
    "BaseTool",
    "Workflow",
    "Step",
    # Advanced agents
    "ReasoningAgent",
    "WorkflowAgent",
    # Exceptions
    "AgenticraftError",
    "AgentError",
    "ToolError",
    "WorkflowError",
    "StepExecutionError",
]
