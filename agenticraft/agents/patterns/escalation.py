"""Simple escalation system for human-in-the-loop approval.

This module implements basic escalation and approval capabilities for the
Customer Service Desk workflow, extracted and simplified from the
Agentic Framework's comprehensive approval system.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from agenticraft.core import Agent

logger = logging.getLogger(__name__)


class EscalationStatus(str, Enum):
    """Status of an escalation request."""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    EXPIRED = "expired"


class EscalationPriority(str, Enum):
    """Priority levels for escalation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EscalationRequest:
    """Represents an escalation request."""
    request_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    requester_id: str = ""
    requester_name: str = ""
    priority: EscalationPriority = EscalationPriority.MEDIUM
    status: EscalationStatus = EscalationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if request has expired."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.status = EscalationStatus.EXPIRED
            return True
        return False
    
    def approve(self, reviewer_id: str, comments: Optional[str] = None):
        """Approve the escalation."""
        self.status = EscalationStatus.APPROVED
        self.resolved_by = reviewer_id
        self.resolved_at = datetime.utcnow()
        self.resolution = comments or "Approved"
    
    def reject(self, reviewer_id: str, reason: Optional[str] = None):
        """Reject the escalation."""
        self.status = EscalationStatus.REJECTED
        self.resolved_by = reviewer_id
        self.resolved_at = datetime.utcnow()
        self.resolution = reason or "Rejected"


class EscalationManager:
    """Manages escalation requests for customer service.
    
    This manager handles escalation of customer service requests
    that require human intervention or higher-level approval.
    
    Args:
        default_timeout_minutes: Default timeout for escalations
        auto_assign: Whether to auto-assign to available reviewers
    """
    
    def __init__(
        self,
        default_timeout_minutes: int = 30,
        auto_assign: bool = True
    ):
        self.default_timeout_minutes = default_timeout_minutes
        self.auto_assign = auto_assign
        
        # Storage
        self.active_requests: Dict[str, EscalationRequest] = {}
        self.request_history: List[EscalationRequest] = []
        
        # Reviewers
        self.available_reviewers: Dict[str, Dict[str, Any]] = {}
        
        # Callbacks
        self.approval_callbacks: Dict[str, List[Callable]] = {}
        self.rejection_callbacks: Dict[str, List[Callable]] = {}
        self.escalation_callbacks: List[Callable] = []
        
        # Metrics
        self.escalation_count = 0
        self.approval_count = 0
        self.rejection_count = 0
        self.avg_resolution_time = timedelta(0)
        
        logger.info("Initialized EscalationManager")
    
    def add_reviewer(
        self,
        reviewer_id: str,
        name: str,
        max_concurrent: int = 5,
        specialties: Optional[Set[str]] = None
    ):
        """Add a human reviewer.
        
        Args:
            reviewer_id: Unique identifier
            name: Display name
            max_concurrent: Max concurrent escalations
            specialties: Topics they specialize in
        """
        self.available_reviewers[reviewer_id] = {
            "name": name,
            "max_concurrent": max_concurrent,
            "current_load": 0,
            "specialties": specialties or set(),
            "resolved_count": 0
        }
        
        logger.info(f"Added reviewer '{name}' with capacity {max_concurrent}")
    
    async def create_escalation(
        self,
        title: str,
        description: str,
        requester_id: str,
        requester_name: str = "Agent",
        priority: EscalationPriority = EscalationPriority.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        timeout_minutes: Optional[int] = None
    ) -> EscalationRequest:
        """Create a new escalation request.
        
        Args:
            title: Brief title
            description: Detailed description
            requester_id: ID of requesting agent
            requester_name: Name of requesting agent
            priority: Escalation priority
            context: Additional context
            timeout_minutes: Custom timeout
            
        Returns:
            Created escalation request
        """
        # Create request
        request = EscalationRequest(
            title=title,
            description=description,
            requester_id=requester_id,
            requester_name=requester_name,
            priority=priority,
            context=context or {}
        )
        
        # Set expiry
        timeout = timeout_minutes or self.default_timeout_minutes
        request.expires_at = datetime.utcnow() + timedelta(minutes=timeout)
        
        # Auto-assign if enabled
        if self.auto_assign:
            reviewer = self._find_best_reviewer(request)
            if reviewer:
                request.assigned_to = reviewer
                self.available_reviewers[reviewer]["current_load"] += 1
                logger.info(
                    f"Auto-assigned escalation to {self.available_reviewers[reviewer]['name']}"
                )
        
        # Store request
        self.active_requests[request.request_id] = request
        self.escalation_count += 1
        
        # Notify callbacks
        for callback in self.escalation_callbacks:
            try:
                await callback(request)
            except Exception as e:
                logger.error(f"Escalation callback error: {e}")
        
        logger.info(
            f"Created {priority.value} escalation: '{title}' "
            f"(assigned to: {request.assigned_to or 'unassigned'})"
        )
        
        return request
    
    async def process_approval(
        self,
        request_id: str,
        reviewer_id: str,
        approved: bool,
        comments: Optional[str] = None
    ) -> bool:
        """Process an escalation decision.
        
        Args:
            request_id: Request to process
            reviewer_id: Reviewer making decision
            approved: Whether approved or rejected
            comments: Additional comments
            
        Returns:
            True if processed successfully
        """
        if request_id not in self.active_requests:
            return False
        
        request = self.active_requests[request_id]
        
        # Check if expired
        if request.is_expired():
            return False
        
        # Check if already resolved
        if request.status != EscalationStatus.PENDING:
            return False
        
        # Process decision
        if approved:
            request.approve(reviewer_id, comments)
            self.approval_count += 1
            
            # Execute approval callbacks
            if request_id in self.approval_callbacks:
                for callback in self.approval_callbacks[request_id]:
                    try:
                        await callback(request)
                    except Exception as e:
                        logger.error(f"Approval callback error: {e}")
        else:
            request.reject(reviewer_id, comments)
            self.rejection_count += 1
            
            # Execute rejection callbacks
            if request_id in self.rejection_callbacks:
                for callback in self.rejection_callbacks[request_id]:
                    try:
                        await callback(request)
                    except Exception as e:
                        logger.error(f"Rejection callback error: {e}")
        
        # Update reviewer load
        if request.assigned_to and request.assigned_to in self.available_reviewers:
            reviewer_info = self.available_reviewers[request.assigned_to]
            reviewer_info["current_load"] = max(0, reviewer_info["current_load"] - 1)
            reviewer_info["resolved_count"] += 1
        
        # Move to history
        self.request_history.append(request)
        del self.active_requests[request_id]
        
        # Clean up callbacks
        self.approval_callbacks.pop(request_id, None)
        self.rejection_callbacks.pop(request_id, None)
        
        # Update average resolution time
        if request.resolved_at and request.created_at:
            resolution_time = request.resolved_at - request.created_at
            total_resolved = self.approval_count + self.rejection_count
            
            if total_resolved > 1:
                # Running average
                self.avg_resolution_time = (
                    (self.avg_resolution_time * (total_resolved - 1) + resolution_time)
                    / total_resolved
                )
            else:
                self.avg_resolution_time = resolution_time
        
        logger.info(
            f"Escalation {request_id} {'approved' if approved else 'rejected'} "
            f"by {self.available_reviewers.get(reviewer_id, {}).get('name', reviewer_id)}"
        )
        
        return True
    
    def register_approval_callback(self, request_id: str, callback: Callable):
        """Register callback for when request is approved."""
        if request_id not in self.approval_callbacks:
            self.approval_callbacks[request_id] = []
        self.approval_callbacks[request_id].append(callback)
    
    def register_rejection_callback(self, request_id: str, callback: Callable):
        """Register callback for when request is rejected.""" 
        if request_id not in self.rejection_callbacks:
            self.rejection_callbacks[request_id] = []
        self.rejection_callbacks[request_id].append(callback)
    
    def register_escalation_callback(self, callback: Callable):
        """Register callback for new escalations."""
        self.escalation_callbacks.append(callback)
    
    def get_pending_escalations(
        self,
        reviewer_id: Optional[str] = None
    ) -> List[EscalationRequest]:
        """Get pending escalation requests.
        
        Args:
            reviewer_id: Filter by assigned reviewer
            
        Returns:
            List of pending requests
        """
        pending = []
        
        for request in self.active_requests.values():
            # Skip expired
            if request.is_expired():
                continue
            
            # Filter by reviewer if specified
            if reviewer_id and request.assigned_to != reviewer_id:
                continue
            
            pending.append(request)
        
        # Sort by priority and age
        pending.sort(
            key=lambda r: (
                ["low", "medium", "high", "urgent"].index(r.priority.value),
                r.created_at
            ),
            reverse=True
        )
        
        return pending
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        total_processed = self.approval_count + self.rejection_count
        
        return {
            "total_escalations": self.escalation_count,
            "active_escalations": len(self.active_requests),
            "approved": self.approval_count,
            "rejected": self.rejection_count,
            "approval_rate": (
                self.approval_count / total_processed if total_processed > 0 else 0
            ),
            "avg_resolution_time": str(self.avg_resolution_time),
            "reviewers": {
                reviewer_id: {
                    "name": info["name"],
                    "current_load": info["current_load"],
                    "resolved_count": info["resolved_count"]
                }
                for reviewer_id, info in self.available_reviewers.items()
            }
        }
    
    def _find_best_reviewer(self, request: EscalationRequest) -> Optional[str]:
        """Find the best reviewer for a request."""
        available = []
        
        for reviewer_id, info in self.available_reviewers.items():
            # Check capacity
            if info["current_load"] >= info["max_concurrent"]:
                continue
            
            # Check specialties if relevant
            topic = request.context.get("topic", "").lower()
            if topic and info["specialties"]:
                if not any(topic in spec.lower() for spec in info["specialties"]):
                    continue
            
            available.append((reviewer_id, info))
        
        if not available:
            return None
        
        # Sort by load (ascending) and resolved count (descending)
        available.sort(
            key=lambda x: (x[1]["current_load"], -x[1]["resolved_count"])
        )
        
        return available[0][0]
    
    async def cleanup_expired(self):
        """Clean up expired requests."""
        expired = []
        
        for request_id, request in self.active_requests.items():
            if request.is_expired():
                expired.append(request_id)
        
        for request_id in expired:
            request = self.active_requests[request_id]
            
            # Update reviewer load if assigned
            if request.assigned_to and request.assigned_to in self.available_reviewers:
                self.available_reviewers[request.assigned_to]["current_load"] -= 1
            
            # Move to history
            self.request_history.append(request)
            del self.active_requests[request_id]
            
            # Clean up callbacks
            self.approval_callbacks.pop(request_id, None)
            self.rejection_callbacks.pop(request_id, None)
            
            logger.info(f"Cleaned up expired escalation: {request_id}")
        
        return len(expired)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EscalationManager(active={len(self.active_requests)}, "
            f"reviewers={len(self.available_reviewers)}, "
            f"approval_rate={self.approval_count/(self.approval_count+self.rejection_count)*100 if (self.approval_count+self.rejection_count) > 0 else 0:.1f}%)"
        )
