"""
Comprehensive health check system for AgentiCraft.

This module provides health monitoring for all components including:
- System resources
- Agent health
- Workflow health
- Service dependencies
- Database connections
"""
import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Represents a single health check."""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None
    
    @property
    def is_healthy(self) -> bool:
        """Check if status is healthy."""
        return self.status == HealthStatus.HEALTHY
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "last_check": self.last_check.isoformat(),
            "duration_ms": self.duration_ms
        }


@dataclass 
class ComponentHealth:
    """Health information for a component."""
    component_name: str
    checks: List[HealthCheck] = field(default_factory=list)
    
    @property
    def overall_status(self) -> HealthStatus:
        """Get overall component status."""
        if not self.checks:
            return HealthStatus.UNKNOWN
            
        # If any check is unhealthy, component is unhealthy
        if any(not check.is_healthy for check in self.checks):
            statuses = [check.status for check in self.checks]
            if HealthStatus.UNHEALTHY in statuses:
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.DEGRADED
                
        return HealthStatus.HEALTHY
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component_name,
            "status": self.overall_status.value,
            "checks": [check.to_dict() for check in self.checks]
        }


class SystemHealthChecker:
    """Check system-level health."""
    
    def __init__(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        disk_threshold: float = 90.0
    ):
        """
        Initialize system health checker.
        
        Args:
            cpu_threshold: CPU usage threshold percentage
            memory_threshold: Memory usage threshold percentage
            disk_threshold: Disk usage threshold percentage
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        
    async def check_health(self) -> ComponentHealth:
        """Check system health."""
        component = ComponentHealth("system")
        
        # CPU check
        cpu_check = await self._check_cpu()
        component.checks.append(cpu_check)
        
        # Memory check
        memory_check = await self._check_memory()
        component.checks.append(memory_check)
        
        # Disk check
        disk_check = await self._check_disk()
        component.checks.append(disk_check)
        
        # Process check
        process_check = await self._check_process()
        component.checks.append(process_check)
        
        return component
        
    async def _check_cpu(self) -> HealthCheck:
        """Check CPU usage."""
        start = time.time()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            if cpu_percent < self.cpu_threshold:
                status = HealthStatus.HEALTHY
                message = f"CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent < self.cpu_threshold + 10:
                status = HealthStatus.DEGRADED
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical CPU usage: {cpu_percent:.1f}%"
                
            return HealthCheck(
                name="cpu",
                status=status,
                message=message,
                details={
                    "usage_percent": cpu_percent,
                    "threshold": self.cpu_threshold,
                    "core_count": psutil.cpu_count()
                },
                duration_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            return HealthCheck(
                name="cpu",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking CPU: {e}"
            )
            
    async def _check_memory(self) -> HealthCheck:
        """Check memory usage."""
        start = time.time()
        
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent < self.memory_threshold:
                status = HealthStatus.HEALTHY
                message = f"Memory usage: {memory.percent:.1f}%"
            elif memory.percent < self.memory_threshold + 10:
                status = HealthStatus.DEGRADED
                message = f"High memory usage: {memory.percent:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical memory usage: {memory.percent:.1f}%"
                
            return HealthCheck(
                name="memory",
                status=status,
                message=message,
                details={
                    "usage_percent": memory.percent,
                    "used_mb": memory.used / 1024 / 1024,
                    "available_mb": memory.available / 1024 / 1024,
                    "total_mb": memory.total / 1024 / 1024,
                    "threshold": self.memory_threshold
                },
                duration_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            return HealthCheck(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking memory: {e}"
            )
            
    async def _check_disk(self) -> HealthCheck:
        """Check disk usage."""
        start = time.time()
        
        try:
            disk = psutil.disk_usage('/')
            
            if disk.percent < self.disk_threshold:
                status = HealthStatus.HEALTHY
                message = f"Disk usage: {disk.percent:.1f}%"
            elif disk.percent < self.disk_threshold + 5:
                status = HealthStatus.DEGRADED
                message = f"High disk usage: {disk.percent:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk usage: {disk.percent:.1f}%"
                
            return HealthCheck(
                name="disk",
                status=status,
                message=message,
                details={
                    "usage_percent": disk.percent,
                    "used_gb": disk.used / 1024 / 1024 / 1024,
                    "free_gb": disk.free / 1024 / 1024 / 1024,
                    "total_gb": disk.total / 1024 / 1024 / 1024,
                    "threshold": self.disk_threshold
                },
                duration_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            return HealthCheck(
                name="disk",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking disk: {e}"
            )
            
    async def _check_process(self) -> HealthCheck:
        """Check current process health."""
        start = time.time()
        
        try:
            process = psutil.Process()
            
            # Check process info
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            num_threads = process.num_threads()
            
            # Basic health criteria
            if cpu_percent < 100 and num_threads < 100:
                status = HealthStatus.HEALTHY
                message = "Process healthy"
            else:
                status = HealthStatus.DEGRADED
                message = "Process under load"
                
            return HealthCheck(
                name="process",
                status=status,
                message=message,
                details={
                    "pid": process.pid,
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_info.rss / 1024 / 1024,
                    "num_threads": num_threads,
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
                },
                duration_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            return HealthCheck(
                name="process",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking process: {e}"
            )


class AgentHealthChecker:
    """Check agent health."""
    
    def __init__(self):
        """Initialize agent health checker."""
        self._agent_status: Dict[str, Dict[str, Any]] = {}
        
    def update_agent_status(
        self,
        agent_name: str,
        status: str,
        last_execution: Optional[datetime] = None,
        error_count: int = 0
    ):
        """Update agent status information."""
        self._agent_status[agent_name] = {
            "status": status,
            "last_execution": last_execution,
            "error_count": error_count,
            "last_update": datetime.now()
        }
        
    async def check_health(self) -> ComponentHealth:
        """Check agent health."""
        component = ComponentHealth("agents")
        
        # Check each registered agent
        for agent_name, status_info in self._agent_status.items():
            check = await self._check_agent(agent_name, status_info)
            component.checks.append(check)
            
        # Overall agents check
        if not self._agent_status:
            component.checks.append(HealthCheck(
                name="agents_overall",
                status=HealthStatus.HEALTHY,
                message="No agents registered"
            ))
        else:
            active_count = sum(
                1 for info in self._agent_status.values()
                if info.get("status") == "active"
            )
            
            component.checks.append(HealthCheck(
                name="agents_overall",
                status=HealthStatus.HEALTHY,
                message=f"{active_count} active agents",
                details={
                    "total_agents": len(self._agent_status),
                    "active_agents": active_count
                }
            ))
            
        return component
        
    async def _check_agent(
        self,
        agent_name: str,
        status_info: Dict[str, Any]
    ) -> HealthCheck:
        """Check individual agent health."""
        # Check if agent is stale
        last_update = status_info.get("last_update")
        if last_update and (datetime.now() - last_update) > timedelta(minutes=5):
            return HealthCheck(
                name=f"agent_{agent_name}",
                status=HealthStatus.DEGRADED,
                message="Agent status is stale",
                details=status_info
            )
            
        # Check error count
        error_count = status_info.get("error_count", 0)
        if error_count > 10:
            return HealthCheck(
                name=f"agent_{agent_name}",
                status=HealthStatus.UNHEALTHY,
                message=f"High error count: {error_count}",
                details=status_info
            )
        elif error_count > 5:
            return HealthCheck(
                name=f"agent_{agent_name}",
                status=HealthStatus.DEGRADED,
                message=f"Elevated error count: {error_count}",
                details=status_info
            )
            
        return HealthCheck(
            name=f"agent_{agent_name}",
            status=HealthStatus.HEALTHY,
            message="Agent healthy",
            details=status_info
        )


class HealthMonitor:
    """Main health monitoring system."""
    
    def __init__(self):
        """Initialize health monitor."""
        self._checkers: Dict[str, Callable[[], Awaitable[ComponentHealth]]] = {}
        self._results: Dict[str, ComponentHealth] = {}
        self._check_interval = 30.0  # seconds
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Register default checkers
        self.system_checker = SystemHealthChecker()
        self.agent_checker = AgentHealthChecker()
        
        self.register_checker("system", self.system_checker.check_health)
        self.register_checker("agents", self.agent_checker.check_health)
        
    def register_checker(
        self,
        name: str,
        checker: Callable[[], Awaitable[ComponentHealth]]
    ):
        """Register a health checker."""
        self._checkers[name] = checker
        logger.info(f"Registered health checker: {name}")
        
    async def check_all(self) -> Dict[str, ComponentHealth]:
        """Run all health checks."""
        results = {}
        
        # Run all checkers concurrently
        tasks = {
            name: asyncio.create_task(checker())
            for name, checker in self._checkers.items()
        }
        
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = ComponentHealth(
                    component_name=name,
                    checks=[HealthCheck(
                        name=f"{name}_error",
                        status=HealthStatus.UNKNOWN,
                        message=f"Check failed: {e}"
                    )]
                )
                
        self._results = results
        return results
        
    async def start_monitoring(self, interval: Optional[float] = None):
        """Start continuous health monitoring."""
        if interval:
            self._check_interval = interval
            
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started health monitoring with interval: {self._check_interval}s")
        
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Stopped health monitoring")
        
    async def _monitor_loop(self):
        """Continuous monitoring loop."""
        while True:
            try:
                await self.check_all()
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                
            await asyncio.sleep(self._check_interval)
            
    def get_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        if not self._results:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "message": "No health checks performed yet",
                "components": {}
            }
            
        # Determine overall status
        all_statuses = []
        for component in self._results.values():
            all_statuses.append(component.overall_status)
            
        if all(s == HealthStatus.HEALTHY for s in all_statuses):
            overall_status = HealthStatus.HEALTHY
            message = "All systems operational"
        elif HealthStatus.UNHEALTHY in all_statuses:
            overall_status = HealthStatus.UNHEALTHY
            unhealthy_count = sum(1 for s in all_statuses if s == HealthStatus.UNHEALTHY)
            message = f"{unhealthy_count} component(s) unhealthy"
        elif HealthStatus.DEGRADED in all_statuses:
            overall_status = HealthStatus.DEGRADED
            degraded_count = sum(1 for s in all_statuses if s == HealthStatus.DEGRADED)
            message = f"{degraded_count} component(s) degraded"
        else:
            overall_status = HealthStatus.UNKNOWN
            message = "Unknown status"
            
        return {
            "status": overall_status.value,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "components": {
                name: component.to_dict()
                for name, component in self._results.items()
            }
        }
        
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        status = self.get_status()
        return status["status"] == HealthStatus.HEALTHY.value


# Global health monitor
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor
    
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
        
    return _health_monitor
