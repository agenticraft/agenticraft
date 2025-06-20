"""Pre-built agents for common use cases.

AgentiCraft provides specialized agents that extend the base Agent
class with additional capabilities for specific use cases.
"""

from .patterns import (
    EscalationManager,
    EscalationRequest,
    ServiceMesh,
    ServiceNode,
    ServiceRequest,
    SimpleCoordinator,
)
from .reasoning import (
    AnalysisResponse,
    ReasoningAgent,
    ReasoningResponse,
    ReasoningStepDetail,
)
from .specialized import DataAnalyst, TechnicalWriter, WebResearcher
from .workflow import (
    StepResult,
    StepStatus,
    Workflow,
    WorkflowAgent,
    WorkflowResult,
    WorkflowStep,
)

__all__ = [
    # Patterns
    "SimpleCoordinator",
    "ServiceMesh",
    "ServiceNode",
    "ServiceRequest",
    "EscalationManager",
    "EscalationRequest",
    # Specialized Agents
    "WebResearcher",
    "DataAnalyst",
    "TechnicalWriter",
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
