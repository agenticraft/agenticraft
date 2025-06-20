"""
Workflow health monitoring for production deployments.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None


@dataclass
class WorkflowHealthMetrics:
    """Metrics for workflow health."""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration_ms: float = 0.0
    last_execution_time: Optional[datetime] = None
    error_rate: float = 0.0
    throughput_per_minute: float = 0.0


class WorkflowHealth:
    """Monitor health of AgentiCraft workflows."""
    
    def __init__(self, workflow_name: str):
        """Initialize workflow health monitor."""
        self.workflow_name = workflow_name
        self.health_checks: List[HealthCheckResult] = []
        self.metrics = WorkflowHealthMetrics()
        self.start_time = datetime.now()
        self._execution_times: List[float] = []
        self._execution_window = []  # For throughput calculation
        
    async def check_workflow_health(self, workflow_instance: Any) -> HealthCheckResult:
        """
        Perform comprehensive health check on a workflow.
        
        Args:
            workflow_instance: The workflow instance to check
            
        Returns:
            HealthCheckResult with status and details
        """
        start_time = time.time()
        checks_passed = 0
        total_checks = 0
        details = {}
        
        try:
            # Check 1: Workflow instance exists and is initialized
            total_checks += 1
            if workflow_instance is not None:
                checks_passed += 1
                details["instance_initialized"] = True
            else:
                details["instance_initialized"] = False
                
            # Check 2: All agents are available
            total_checks += 1
            if hasattr(workflow_instance, "agents"):
                agent_statuses = {}
                all_agents_healthy = True
                
                for agent_name, agent in workflow_instance.agents.items():
                    if agent is not None:
                        agent_statuses[agent_name] = "available"
                    else:
                        agent_statuses[agent_name] = "unavailable"
                        all_agents_healthy = False
                        
                details["agent_statuses"] = agent_statuses
                if all_agents_healthy:
                    checks_passed += 1
                    
            # Check 3: Memory system (if enabled)
            total_checks += 1
            if hasattr(workflow_instance, "memory") and workflow_instance.memory is not None:
                try:
                    # Test memory access
                    test_data = {"test": "health_check", "timestamp": datetime.now().isoformat()}
                    await workflow_instance.memory.store("health_check", test_data)
                    retrieved = await workflow_instance.memory.retrieve("health_check")
                    
                    if retrieved == test_data:
                        checks_passed += 1
                        details["memory_system"] = "healthy"
                    else:
                        details["memory_system"] = "degraded"
                except Exception as e:
                    details["memory_system"] = f"error: {str(e)}"
            else:
                # Memory not enabled, not a failure
                checks_passed += 1
                details["memory_system"] = "not_enabled"
                
            # Check 4: Workflow can accept tasks
            total_checks += 1
            if hasattr(workflow_instance, "add_task") or hasattr(workflow_instance, "execute"):
                checks_passed += 1
                details["can_accept_tasks"] = True
            else:
                details["can_accept_tasks"] = False
                
            # Check 5: Recent execution metrics
            total_checks += 1
            if self.metrics.error_rate < 0.1:  # Less than 10% error rate
                checks_passed += 1
                details["error_rate_acceptable"] = True
            else:
                details["error_rate_acceptable"] = False
                
            # Calculate overall status
            health_percentage = (checks_passed / total_checks) * 100
            
            if health_percentage >= 90:
                status = HealthStatus.HEALTHY
                message = f"Workflow '{self.workflow_name}' is healthy"
            elif health_percentage >= 70:
                status = HealthStatus.DEGRADED
                message = f"Workflow '{self.workflow_name}' is degraded ({checks_passed}/{total_checks} checks passed)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Workflow '{self.workflow_name}' is unhealthy ({checks_passed}/{total_checks} checks passed)"
                
            details["checks_passed"] = checks_passed
            details["total_checks"] = total_checks
            details["health_percentage"] = health_percentage
            
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Health check failed: {str(e)}"
            details["error"] = str(e)
            logger.error(f"Health check error for workflow '{self.workflow_name}': {e}")
            
        duration_ms = (time.time() - start_time) * 1000
        
        result = HealthCheckResult(
            status=status,
            message=message,
            details=details,
            duration_ms=duration_ms
        )
        
        self.health_checks.append(result)
        return result
        
    def record_execution(self, duration_ms: float, success: bool = True):
        """Record workflow execution metrics."""
        self.metrics.total_executions += 1
        
        if success:
            self.metrics.successful_executions += 1
        else:
            self.metrics.failed_executions += 1
            
        self._execution_times.append(duration_ms)
        self.metrics.last_execution_time = datetime.now()
        
        # Update average duration (keep last 100 executions)
        if len(self._execution_times) > 100:
            self._execution_times = self._execution_times[-100:]
        self.metrics.average_duration_ms = sum(self._execution_times) / len(self._execution_times)
        
        # Update error rate
        if self.metrics.total_executions > 0:
            self.metrics.error_rate = self.metrics.failed_executions / self.metrics.total_executions
            
        # Update throughput (executions in last minute)
        current_time = datetime.now()
        self._execution_window.append(current_time)
        cutoff_time = current_time - timedelta(minutes=1)
        self._execution_window = [t for t in self._execution_window if t > cutoff_time]
        self.metrics.throughput_per_minute = len(self._execution_window)
        
    def get_latest_health(self) -> Optional[HealthCheckResult]:
        """Get the most recent health check result."""
        return self.health_checks[-1] if self.health_checks else None
        
    def get_health_history(self, limit: int = 10) -> List[HealthCheckResult]:
        """Get recent health check history."""
        return self.health_checks[-limit:]
        
    def get_metrics(self) -> WorkflowHealthMetrics:
        """Get current workflow metrics."""
        return self.metrics
        
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary."""
        latest_health = self.get_latest_health()
        
        return {
            "workflow_name": self.workflow_name,
            "current_status": latest_health.status.value if latest_health else "unknown",
            "last_check": latest_health.timestamp.isoformat() if latest_health else None,
            "metrics": {
                "total_executions": self.metrics.total_executions,
                "success_rate": (
                    self.metrics.successful_executions / self.metrics.total_executions 
                    if self.metrics.total_executions > 0 else 0
                ),
                "error_rate": self.metrics.error_rate,
                "average_duration_ms": self.metrics.average_duration_ms,
                "throughput_per_minute": self.metrics.throughput_per_minute,
                "last_execution": (
                    self.metrics.last_execution_time.isoformat() 
                    if self.metrics.last_execution_time else None
                ),
            },
            "uptime": str(datetime.now() - self.start_time),
        }
        
    async def continuous_monitoring(self, workflow_instance: Any, interval_seconds: int = 60):
        """
        Continuously monitor workflow health.
        
        Args:
            workflow_instance: The workflow to monitor
            interval_seconds: Check interval in seconds
        """
        logger.info(f"Starting continuous monitoring for workflow '{self.workflow_name}'")
        
        while True:
            try:
                result = await self.check_workflow_health(workflow_instance)
                
                if result.status == HealthStatus.UNHEALTHY:
                    logger.error(f"Workflow unhealthy: {result.message}")
                elif result.status == HealthStatus.DEGRADED:
                    logger.warning(f"Workflow degraded: {result.message}")
                else:
                    logger.info(f"Workflow healthy: {result.message}")
                    
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
            await asyncio.sleep(interval_seconds)


# HTTP endpoint helper for health checks
async def create_health_endpoint(workflow_health: WorkflowHealth) -> Dict[str, Any]:
    """Create health check endpoint response."""
    summary = workflow_health.get_status_summary()
    latest_health = workflow_health.get_latest_health()
    
    # Determine HTTP status code
    if latest_health:
        if latest_health.status == HealthStatus.HEALTHY:
            http_status = 200
        elif latest_health.status == HealthStatus.DEGRADED:
            http_status = 503  # Service Unavailable
        else:
            http_status = 500  # Internal Server Error
    else:
        http_status = 503
        
    return {
        "status_code": http_status,
        "body": {
            "status": summary["current_status"],
            "workflow": summary["workflow_name"],
            "timestamp": datetime.now().isoformat(),
            "details": summary,
        }
    }
