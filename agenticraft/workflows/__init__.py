"""Workflow components for AgentiCraft.

This module provides workflow execution capabilities including:
- Base workflow class
- Hero workflows (ResearchTeam, CustomerService, CodeReview)
- Visual workflow representations (Mermaid, ASCII, JSON, HTML)
- Common workflow patterns (parallel, conditional, loops, map-reduce)
- Workflow templates for typical use cases
"""

from .base import Workflow
from .code_review import CodeReviewPipeline
from .customer_service import CustomerServiceDesk
from .memory_research_team import MemoryResearchTeam
from .patterns import WorkflowPatterns
from .research_team import ResearchTeam
from .resilient.research_team import ResilientResearchTeam
from .visual import (
    VisualizationFormat,
    WorkflowVisualizer,
    save_workflow_visualization,
    visualize_workflow,
)

__all__ = [
    # Base
    "Workflow",
    # Hero Workflows
    "ResearchTeam",
    "MemoryResearchTeam",
    "ResilientResearchTeam",
    "CustomerServiceDesk",
    "CodeReviewPipeline",
    # Patterns
    "WorkflowPatterns",
    # Visualization
    "WorkflowVisualizer",
    "VisualizationFormat",
    "visualize_workflow",
    "save_workflow_visualization",
]
