"""
System-wide health monitoring for AgentiCraft deployments.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import psutil
import platform
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SystemResources:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    disk_available_gb: float
    network_io_bytes_sent: int
    network_io_bytes_recv: int
    open_file_descriptors: int
    thread_count: int
    process_count: int


@dataclass
class SystemHealthReport:
    """Complete system health report."""
    timestamp: datetime
    system_info: Dict[str, str]
    resources: SystemResources
    workflows_status: Dict[str, str]
    agents_summary: Dict[str, Any]
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SystemHealth:
    """Monitor overall system health for AgentiCraft deployments."""
    
    def __init__(self):
        """Initialize system health monitor."""
        self.start_time = datetime.now()
        self.health_reports: List[SystemHealthReport] = []
        self._network_baseline = None
        self._init_network_baseline()
        
    def _init_network_baseline(self):
        """Initialize network I/O baseline."""
        try:
            net_io = psutil.net_io_counters()
            self._network_baseline = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
            }
        except:
            self._network_baseline = {"bytes_sent": 0, "bytes_recv": 0}
            
    def get_system_info(self) -> Dict[str, str]:
        """Get static system information."""
        try:
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "processor": platform.processor(),
                "cpu_count": str(psutil.cpu_count()),
                "hostname": platform.node(),
                "agenticraft_version": self._get_agenticraft_version(),
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
            
    def _get_agenticraft_version(self) -> str:
        """Get AgentiCraft version."""
        try:
            from agenticraft import __version__
            return __version__
        except:
            return "unknown"
            
    def collect_system_resources(self) -> SystemResources:
        """Collect current system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / 1024 / 1024
            memory_total_mb = memory.total / 1024 / 1024
            
            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_usage_percent = disk.percent
            disk_available_gb = disk.free / 1024 / 1024 / 1024
            
            # Network metrics
            net_io = psutil.net_io_counters()
            network_io_bytes_sent = net_io.bytes_sent - self._network_baseline["bytes_sent"]
            network_io_bytes_recv = net_io.bytes_recv - self._network_baseline["bytes_recv"]
            
            # Process metrics
            process = psutil.Process(os.getpid())
            open_file_descriptors = len(process.open_files())
            thread_count = process.num_threads()
            
            # System-wide process count
            process_count = len(psutil.pids())
            
            return SystemResources(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                memory_total_mb=memory_total_mb,
                disk_usage_percent=disk_usage_percent,
                disk_available_gb=disk_available_gb,
                network_io_bytes_sent=network_io_bytes_sent,
                network_io_bytes_recv=network_io_bytes_recv,
                open_file_descriptors=open_file_descriptors,
                thread_count=thread_count,
                process_count=process_count,
            )
            
        except Exception as e:
            logger.error(f"Error collecting system resources: {e}")
            # Return safe defaults
            return SystemResources(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                memory_total_mb=0.0,
                disk_usage_percent=0.0,
                disk_available_gb=0.0,
                network_io_bytes_sent=0,
                network_io_bytes_recv=0,
                open_file_descriptors=0,
                thread_count=0,
                process_count=0,
            )
            
    def analyze_system_health(
        self,
        resources: SystemResources,
        workflows_status: Dict[str, str],
        agents_summary: Dict[str, Any]
    ) -> tuple[List[str], List[str]]:
        """
        Analyze system health and generate alerts and recommendations.
        
        Returns:
            Tuple of (alerts, recommendations)
        """
        alerts = []
        recommendations = []
        
        # CPU alerts
        if resources.cpu_percent > 90:
            alerts.append(f"Critical: CPU usage is {resources.cpu_percent:.1f}%")
            recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")
        elif resources.cpu_percent > 70:
            alerts.append(f"Warning: CPU usage is {resources.cpu_percent:.1f}%")
            
        # Memory alerts
        if resources.memory_percent > 90:
            alerts.append(f"Critical: Memory usage is {resources.memory_percent:.1f}%")
            recommendations.append("Consider increasing memory or optimizing memory usage")
        elif resources.memory_percent > 80:
            alerts.append(f"Warning: Memory usage is {resources.memory_percent:.1f}%")
            
        # Disk alerts
        if resources.disk_usage_percent > 90:
            alerts.append(f"Critical: Disk usage is {resources.disk_usage_percent:.1f}%")
            recommendations.append("Clean up disk space or increase storage capacity")
        elif resources.disk_usage_percent > 80:
            alerts.append(f"Warning: Disk usage is {resources.disk_usage_percent:.1f}%")
            
        # File descriptor alerts
        if resources.open_file_descriptors > 1000:
            alerts.append(f"Warning: High number of open file descriptors ({resources.open_file_descriptors})")
            recommendations.append("Check for file descriptor leaks")
            
        # Workflow alerts
        unhealthy_workflows = [
            name for name, status in workflows_status.items() 
            if status not in ["healthy", "unknown"]
        ]
        if unhealthy_workflows:
            alerts.append(f"Warning: {len(unhealthy_workflows)} unhealthy workflows: {', '.join(unhealthy_workflows)}")
            recommendations.append("Check workflow logs and restart if necessary")
            
        # Agent alerts
        if agents_summary:
            unhealthy_agents = agents_summary.get("unhealthy_agents", 0)
            total_agents = agents_summary.get("total_agents", 0)
            
            if total_agents > 0 and unhealthy_agents / total_agents > 0.3:
                alerts.append(f"Warning: {unhealthy_agents}/{total_agents} agents are unhealthy")
                recommendations.append("Check agent health and restart failed agents")
                
            # Check agent response times
            avg_response_time = agents_summary.get("average_response_time_ms", 0)
            if avg_response_time > 1000:
                alerts.append(f"Warning: High average agent response time ({avg_response_time:.0f}ms)")
                recommendations.append("Check agent performance and consider scaling")
                
        return alerts, recommendations
        
    async def generate_health_report(
        self,
        workflow_healths: Dict[str, Any] = None,
        agent_health: Any = None
    ) -> SystemHealthReport:
        """
        Generate comprehensive system health report.
        
        Args:
            workflow_healths: Dictionary of workflow_name -> WorkflowHealth instances
            agent_health: AgentHealth instance
            
        Returns:
            SystemHealthReport with current status
        """
        # Collect system info and resources
        system_info = self.get_system_info()
        resources = self.collect_system_resources()
        
        # Get workflow status
        workflows_status = {}
        if workflow_healths:
            for name, health in workflow_healths.items():
                latest = health.get_latest_health()
                workflows_status[name] = latest.status.value if latest else "unknown"
                
        # Get agents summary
        agents_summary = {}
        if agent_health:
            agents_summary = agent_health.get_summary()
            
        # Analyze health and generate alerts/recommendations
        alerts, recommendations = self.analyze_system_health(
            resources, workflows_status, agents_summary
        )
        
        # Create report
        report = SystemHealthReport(
            timestamp=datetime.now(),
            system_info=system_info,
            resources=resources,
            workflows_status=workflows_status,
            agents_summary=agents_summary,
            alerts=alerts,
            recommendations=recommendations,
        )
        
        self.health_reports.append(report)
        return report
        
    def get_latest_report(self) -> Optional[SystemHealthReport]:
        """Get the most recent health report."""
        return self.health_reports[-1] if self.health_reports else None
        
    def get_report_history(self, limit: int = 10) -> List[SystemHealthReport]:
        """Get recent health report history."""
        return self.health_reports[-limit:]
        
    def get_uptime(self) -> timedelta:
        """Get system uptime."""
        return datetime.now() - self.start_time
        
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze health trends over specified time period.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_reports = [
            report for report in self.health_reports
            if report.timestamp > cutoff_time
        ]
        
        if not recent_reports:
            return {"error": "No data available for specified time period"}
            
        # Calculate trends
        cpu_values = [r.resources.cpu_percent for r in recent_reports]
        memory_values = [r.resources.memory_percent for r in recent_reports]
        
        trends = {
            "period_hours": hours,
            "report_count": len(recent_reports),
            "cpu": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing",
            },
            "memory": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing",
            },
            "alerts": {
                "total": sum(len(r.alerts) for r in recent_reports),
                "recent": recent_reports[-1].alerts if recent_reports else [],
            },
        }
        
        return trends
        
    async def continuous_monitoring(
        self,
        workflow_healths: Dict[str, Any] = None,
        agent_health: Any = None,
        interval_seconds: int = 300  # 5 minutes default
    ):
        """
        Continuously monitor system health.
        
        Args:
            workflow_healths: Dictionary of workflow_name -> WorkflowHealth instances
            agent_health: AgentHealth instance
            interval_seconds: Check interval in seconds
        """
        logger.info("Starting system health monitoring")
        
        while True:
            try:
                report = await self.generate_health_report(workflow_healths, agent_health)
                
                # Log summary
                logger.info(
                    f"System health: CPU {report.resources.cpu_percent:.1f}%, "
                    f"Memory {report.resources.memory_percent:.1f}%, "
                    f"Alerts: {len(report.alerts)}"
                )
                
                # Log alerts
                for alert in report.alerts:
                    logger.warning(f"System alert: {alert}")
                    
                # Log recommendations
                for rec in report.recommendations:
                    logger.info(f"Recommendation: {rec}")
                    
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                
            await asyncio.sleep(interval_seconds)
            
    def export_health_dashboard(self) -> Dict[str, Any]:
        """Export health data for dashboard visualization."""
        latest = self.get_latest_report()
        trends = self.get_health_trends(hours=24)
        
        if not latest:
            return {"status": "no_data"}
            
        return {
            "timestamp": latest.timestamp.isoformat(),
            "uptime": str(self.get_uptime()),
            "system": latest.system_info,
            "current": {
                "cpu_percent": latest.resources.cpu_percent,
                "memory_percent": latest.resources.memory_percent,
                "disk_percent": latest.resources.disk_usage_percent,
                "workflows": latest.workflows_status,
                "agents": latest.agents_summary,
                "alert_count": len(latest.alerts),
                "alerts": latest.alerts,
            },
            "trends": trends,
            "recommendations": latest.recommendations,
        }


# HTTP endpoint helper for system health
async def create_system_health_endpoint(system_health: SystemHealth) -> Dict[str, Any]:
    """Create system health check endpoint response."""
    dashboard = system_health.export_health_dashboard()
    latest = system_health.get_latest_report()
    
    # Determine HTTP status based on alerts
    if latest and latest.alerts:
        critical_alerts = [a for a in latest.alerts if "Critical" in a]
        if critical_alerts:
            http_status = 500
        else:
            http_status = 503
    else:
        http_status = 200
        
    return {
        "status_code": http_status,
        "body": {
            "status": "critical" if http_status == 500 else "warning" if http_status == 503 else "healthy",
            "timestamp": datetime.now().isoformat(),
            "dashboard": dashboard,
        }
    }
