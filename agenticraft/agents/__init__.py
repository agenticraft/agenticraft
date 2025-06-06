"""Pre-built agents for common use cases.

AgentiCraft provides specialized agents that extend the base Agent
class with additional capabilities for specific use cases.
"""

from .reasoning import (
    ReasoningAgent,
    ReasoningResponse,
    ReasoningStepDetail,
    AnalysisResponse
)
from .workflow import (
    WorkflowAgent,
    Workflow,
    WorkflowStep,
    WorkflowResult,
    StepResult,
    StepStatus
)

__all__ = [
    # Reasoning Agent
    "ReasoningAgent",
    "ReasoningResponse", 
    "ReasoningStepDetail",
    "AnalysisResponse",
    
    # Workflow Agent
    "WorkflowAgent",
    "Workflow",
    "WorkflowStep", 
    "WorkflowResult",
    "StepResult",
    "StepStatus",
]
