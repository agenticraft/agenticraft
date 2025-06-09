"""Workflow components for AgentiCraft.

This module provides workflow execution capabilities including:
- Visual workflow representations (Mermaid, ASCII, JSON, HTML)
- Common workflow patterns (parallel, conditional, loops, map-reduce)
- Workflow templates for typical use cases
"""

from .patterns import WorkflowPatterns
from .visual import (
    VisualizationFormat,
    WorkflowVisualizer,
    save_workflow_visualization,
    visualize_workflow,
)

__all__ = [
    "WorkflowPatterns",
    "WorkflowVisualizer",
    "VisualizationFormat",
    "visualize_workflow",
    "save_workflow_visualization",
]
