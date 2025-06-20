"""Agent coordination patterns for AgentiCraft.

This module provides patterns for coordinating multiple agents,
including hierarchical coordination, mesh networks, and more.
"""

from .coordinator import SimpleCoordinator
from .escalation import EscalationManager, EscalationRequest, EscalationPriority
from .mesh import ServiceMesh, ServiceNode, ServiceRequest, NodeRole

__all__ = [
    "SimpleCoordinator",
    "ServiceMesh",
    "ServiceNode", 
    "ServiceRequest",
    "NodeRole",
    "EscalationManager",
    "EscalationRequest",
    "EscalationPriority"
]
