"""
AgentiCraft: Dead simple AI agents with reasoning traces.

A lightweight, production-ready framework for building AI agents with
transparent reasoning, MCP protocol support, and comprehensive observability.
"""

__version__ = "0.2.0-alpha"
__author__ = "AgentiCraft Team"
__email__ = "hello@agenticraft.ai"

# Version check
import sys

if sys.version_info < (3, 10):
    raise RuntimeError("AgentiCraft requires Python 3.10 or higher")

# Core imports
# Advanced agents
from .agents import (
    ReasoningAgent,
    WorkflowAgent,
)
from .core.agent import Agent
from .core.exceptions import (
    AgentError,
    AgenticraftError,
    StepExecutionError,
    ToolError,
    WorkflowError,
)
from .core.tool import BaseTool, tool
from .core.workflow import Step, Workflow

# Optional security imports (if available)
try:
    from .security import (
        SandboxManager,
        SecurityContext,
        SandboxType,
        SecureResult
    )
    SECURITY_AVAILABLE = True
except ImportError:
    # Security module is optional
    SECURITY_AVAILABLE = False

# Optional fabric imports (if available)
try:
    from .fabric import (
        agent as fabric_agent,
        UnifiedProtocolFabric,
        initialize_fabric,
        get_global_fabric,
    )
    FABRIC_AVAILABLE = True
except ImportError:
    # Fabric module is optional
    FABRIC_AVAILABLE = False

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

# Add fabric exports if available
if FABRIC_AVAILABLE:
    __all__.extend([
        "fabric_agent",
        "UnifiedProtocolFabric",
        "initialize_fabric",
        "get_global_fabric",
    ])
