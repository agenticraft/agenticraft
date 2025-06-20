"""Simple mesh networking for distributed agent coordination.

This module implements basic mesh networking capabilities for the
Customer Service Desk workflow, extracted and simplified from the
Agentic Framework's comprehensive mesh network implementation.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from agenticraft.core import Agent

logger = logging.getLogger(__name__)


class NodeRole(Enum):
    """Roles for nodes in the service mesh."""
    FRONTLINE = "frontline"  # L1 support agents
    SPECIALIST = "specialist"  # L2 support agents
    EXPERT = "expert"  # L3 support / escalation
    COORDINATOR = "coordinator"  # Routes requests


@dataclass
class ServiceNode:
    """Represents a service agent in the mesh."""
    node_id: str = field(default_factory=lambda: str(uuid4()))
    agent: Agent = None
    role: NodeRole = NodeRole.FRONTLINE
    specialties: Set[str] = field(default_factory=set)
    current_load: int = 0
    max_capacity: int = 5
    available: bool = True
    
    @property
    def load_percentage(self) -> float:
        """Get load as percentage."""
        return (self.current_load / self.max_capacity) * 100 if self.max_capacity > 0 else 0
    
    def can_handle(self, topic: str) -> bool:
        """Check if node can handle a topic."""
        if not self.available or self.current_load >= self.max_capacity:
            return False
        
        # Experts can handle anything
        if self.role == NodeRole.EXPERT:
            return True
        
        # Check specialties if any defined
        if self.specialties:
            return topic.lower() in [s.lower() for s in self.specialties]
        
        # Frontline handles general queries
        return self.role == NodeRole.FRONTLINE


@dataclass
class ServiceRequest:
    """Customer service request in the mesh."""
    request_id: str = field(default_factory=lambda: str(uuid4()))
    customer_id: str = ""
    query: str = ""
    topic: str = "general"
    priority: int = 5  # 1-10, higher is more urgent
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = None
    escalation_count: int = 0
    resolution: Optional[str] = None
    status: str = "pending"  # pending, assigned, escalated, resolved
    history: List[Dict[str, Any]] = field(default_factory=list)


class ServiceMesh:
    """Simple service mesh for customer service coordination.
    
    This mesh coordinates customer service agents across different
    tiers, handling routing, load balancing, and escalation.
    
    Args:
        coordinator: Optional coordinator agent for complex routing
    """
    
    def __init__(self, coordinator: Optional[Agent] = None):
        self.coordinator = coordinator
        self.nodes: Dict[str, ServiceNode] = {}
        self.requests: Dict[str, ServiceRequest] = {}
        
        # Routing configuration
        self.escalation_threshold = 2  # Max attempts before escalation
        self.load_balance_strategy = "least_loaded"  # or "round_robin"
        
        # Callbacks
        self.escalation_handlers: List[Callable] = []
        self.resolution_handlers: List[Callable] = []
        
        # Metrics
        self.routing_history: List[Dict[str, Any]] = []
        self.last_assigned_node: Optional[str] = None
        
        logger.info("Initialized ServiceMesh")
    
    def add_node(
        self,
        agent: Agent,
        role: NodeRole = NodeRole.FRONTLINE,
        specialties: Optional[Set[str]] = None,
        max_capacity: int = 5
    ) -> ServiceNode:
        """Add an agent node to the mesh.
        
        Args:
            agent: The agent to add
            role: Role in the service hierarchy
            specialties: Topics this agent specializes in
            max_capacity: Maximum concurrent requests
            
        Returns:
            The created ServiceNode
        """
        node = ServiceNode(
            agent=agent,
            role=role,
            specialties=specialties or set(),
            max_capacity=max_capacity
        )
        
        self.nodes[node.node_id] = node
        logger.info(f"Added {role.value} node '{agent.name}' to mesh")
        
        return node
    
    async def route_request(
        self,
        customer_id: str,
        query: str,
        topic: str = "general",
        priority: int = 5
    ) -> ServiceRequest:
        """Route a customer request to appropriate agent.
        
        Args:
            customer_id: Customer identifier
            query: Customer's question or issue
            topic: Topic/category of the request
            priority: Priority level (1-10)
            
        Returns:
            The created service request
        """
        # Create request
        request = ServiceRequest(
            customer_id=customer_id,
            query=query,
            topic=topic,
            priority=priority
        )
        
        # Store request
        self.requests[request.request_id] = request
        
        # Find suitable node
        node = await self._find_best_node(request)
        
        if node:
            # Assign request
            await self._assign_request(request, node)
        else:
            # No available nodes - mark for escalation
            request.status = "escalated"
            request.history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "no_agents_available",
                "details": "Request queued for escalation"
            })
            
            # Trigger escalation handlers
            for handler in self.escalation_handlers:
                await handler(request)
        
        # Track routing
        self.routing_history.append({
            "request_id": request.request_id,
            "topic": topic,
            "assigned_to": node.node_id if node else None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return request
    
    async def escalate_request(
        self,
        request_id: str,
        reason: str = "Unable to resolve"
    ) -> bool:
        """Escalate a request to higher tier.
        
        Args:
            request_id: Request to escalate
            reason: Reason for escalation
            
        Returns:
            True if escalated successfully
        """
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        request.escalation_count += 1
        
        # Release current assignment
        if request.assigned_to:
            node = self.nodes.get(request.assigned_to)
            if node:
                node.current_load -= 1
        
        # Log escalation
        request.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "escalated",
            "reason": reason,
            "from_node": request.assigned_to
        })
        
        # Find higher tier node
        current_role = NodeRole.FRONTLINE
        if request.assigned_to:
            current_node = self.nodes.get(request.assigned_to)
            if current_node:
                current_role = current_node.role
        
        # Determine next tier
        next_tier = self._get_next_tier(current_role)
        
        # Find node in next tier
        higher_nodes = [
            n for n in self.nodes.values()
            if n.role == next_tier and n.can_handle(request.topic)
        ]
        
        if higher_nodes:
            # Use load balancing to select
            if self.load_balance_strategy == "least_loaded":
                node = min(higher_nodes, key=lambda n: n.current_load)
            else:
                # Round robin
                node = random.choice(higher_nodes)
            
            await self._assign_request(request, node)
            request.status = "escalated"
            
            # Notify escalation handlers
            for handler in self.escalation_handlers:
                await handler(request)
            
            return True
        
        # No higher tier available
        request.status = "escalation_failed"
        return False
    
    async def resolve_request(
        self,
        request_id: str,
        resolution: str,
        node_id: Optional[str] = None
    ) -> bool:
        """Mark a request as resolved.
        
        Args:
            request_id: Request to resolve
            resolution: Resolution details
            node_id: Node that resolved it
            
        Returns:
            True if resolved successfully
        """
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        request.resolution = resolution
        request.status = "resolved"
        
        # Release node capacity
        if request.assigned_to:
            node = self.nodes.get(request.assigned_to)
            if node:
                node.current_load -= 1
        
        # Log resolution
        request.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "resolved",
            "by_node": node_id or request.assigned_to,
            "resolution": resolution[:100]  # Truncate for logging
        })
        
        # Notify resolution handlers
        for handler in self.resolution_handlers:
            await handler(request)
        
        return True
    
    def register_escalation_handler(self, handler: Callable):
        """Register handler for escalations."""
        self.escalation_handlers.append(handler)
    
    def register_resolution_handler(self, handler: Callable):
        """Register handler for resolutions."""
        self.resolution_handlers.append(handler)
    
    async def get_node_status(self) -> Dict[str, Any]:
        """Get current mesh status."""
        total_capacity = sum(n.max_capacity for n in self.nodes.values())
        current_load = sum(n.current_load for n in self.nodes.values())
        
        nodes_by_role = {}
        for node in self.nodes.values():
            role = node.role.value
            if role not in nodes_by_role:
                nodes_by_role[role] = []
            
            nodes_by_role[role].append({
                "agent": node.agent.name,
                "load": f"{node.current_load}/{node.max_capacity}",
                "load_percentage": f"{node.load_percentage:.1f}%",
                "specialties": list(node.specialties),
                "available": node.available
            })
        
        pending_requests = [
            r for r in self.requests.values()
            if r.status in ["pending", "assigned", "escalated"]
        ]
        
        return {
            "total_nodes": len(self.nodes),
            "total_capacity": total_capacity,
            "current_load": current_load,
            "utilization": f"{(current_load/total_capacity*100):.1f}%" if total_capacity > 0 else "0%",
            "nodes_by_role": nodes_by_role,
            "active_requests": len(pending_requests),
            "escalation_count": sum(r.escalation_count for r in self.requests.values()),
            "resolution_count": len([r for r in self.requests.values() if r.status == "resolved"])
        }
    
    async def _find_best_node(self, request: ServiceRequest) -> Optional[ServiceNode]:
        """Find the best node for a request."""
        # Get eligible nodes
        eligible_nodes = [
            n for n in self.nodes.values()
            if n.can_handle(request.topic)
        ]
        
        if not eligible_nodes:
            return None
        
        # If coordinator exists, ask for routing decision
        if self.coordinator:
            thought = await self.coordinator.think(
                f"Route customer request about '{request.topic}' with priority {request.priority}. "
                f"Available agents: {[n.agent.name for n in eligible_nodes]}"
            )
            # Simple parsing - in production would be more sophisticated
            # For now, continue with load balancing
        
        # Apply strategy
        if self.load_balance_strategy == "least_loaded":
            # Sort by load percentage, then by role (prefer frontline first)
            eligible_nodes.sort(
                key=lambda n: (n.load_percentage, n.role.value)
            )
            return eligible_nodes[0]
        else:
            # Round robin
            if self.last_assigned_node:
                # Find next node after last assigned
                node_ids = [n.node_id for n in eligible_nodes]
                try:
                    last_idx = node_ids.index(self.last_assigned_node)
                    return eligible_nodes[(last_idx + 1) % len(eligible_nodes)]
                except ValueError:
                    pass
            
            return eligible_nodes[0]
    
    async def _assign_request(self, request: ServiceRequest, node: ServiceNode):
        """Assign request to a node."""
        request.assigned_to = node.node_id
        request.status = "assigned"
        node.current_load += 1
        self.last_assigned_node = node.node_id
        
        request.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "assigned",
            "to_node": node.node_id,
            "agent": node.agent.name,
            "role": node.role.value
        })
        
        logger.info(
            f"Assigned request {request.request_id} to {node.agent.name} "
            f"({node.role.value})"
        )
    
    def _get_next_tier(self, current_role: NodeRole) -> NodeRole:
        """Get the next tier for escalation."""
        if current_role == NodeRole.FRONTLINE:
            return NodeRole.SPECIALIST
        elif current_role == NodeRole.SPECIALIST:
            return NodeRole.EXPERT
        else:
            return NodeRole.EXPERT  # Already at highest
    
    def get_request_history(self, request_id: str) -> List[Dict[str, Any]]:
        """Get history of a request."""
        if request_id in self.requests:
            return self.requests[request_id].history
        return []
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ServiceMesh(nodes={len(self.nodes)}, active_requests={len([r for r in self.requests.values() if r.status != 'resolved'])})"
