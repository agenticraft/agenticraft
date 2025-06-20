"""
Integrated monitoring system for AgentiCraft.

This module combines health checks, metrics, and monitoring
into a unified system with dashboards and alerts.
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from pathlib import Path

from .prometheus import PrometheusExporter, get_metrics
from .health import HealthMonitor, HealthStatus, get_health_monitor
from ...security.audit import AuditLogger, AuditEventType

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Represents a monitoring alert."""
    id: str
    severity: str  # info, warning, error, critical
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        """Check if alert is still active."""
        return self.resolved_at is None
        
    def resolve(self):
        """Mark alert as resolved."""
        self.resolved_at = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "severity": self.severity,
            "component": self.component,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "is_active": self.is_active
        }


@dataclass
class MonitoringConfig:
    """Configuration for monitoring system."""
    # Health check settings
    health_check_interval: float = 30.0
    health_check_timeout: float = 10.0
    
    # Metrics settings
    metrics_collection_interval: float = 10.0
    metrics_retention_days: int = 30
    
    # Alert settings
    alert_cooldown_minutes: int = 30
    max_active_alerts: int = 100
    
    # Dashboard settings
    dashboard_refresh_interval: float = 5.0
    dashboard_history_hours: int = 24
    
    # Export settings
    export_path: Optional[Path] = None
    export_format: str = "json"  # json, csv, prometheus


class AlertManager:
    """Manages monitoring alerts."""
    
    def __init__(self, config: MonitoringConfig):
        """Initialize alert manager."""
        self.config = config
        self._alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._cooldowns: Dict[str, datetime] = {}
        
    def create_alert(
        self,
        severity: str,
        component: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """Create a new alert."""
        # Check cooldown
        cooldown_key = f"{component}:{message}"
        if cooldown_key in self._cooldowns:
            if datetime.now() < self._cooldowns[cooldown_key]:
                logger.debug(f"Alert in cooldown: {cooldown_key}")
                return None
                
        # Check max alerts
        active_alerts = sum(1 for a in self._alerts.values() if a.is_active)
        if active_alerts >= self.config.max_active_alerts:
            logger.warning("Max active alerts reached")
            return None
            
        # Create alert
        alert = Alert(
            id=f"alert_{datetime.now().timestamp()}",
            severity=severity,
            component=component,
            message=message,
            details=details or {}
        )
        
        # Store alert
        self._alerts[alert.id] = alert
        self._alert_history.append(alert)
        
        # Set cooldown
        self._cooldowns[cooldown_key] = datetime.now() + timedelta(
            minutes=self.config.alert_cooldown_minutes
        )
        
        # Notify handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
                
        logger.info(f"Created alert: {alert.id} - {message}")
        return alert
        
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.resolve()
            logger.info(f"Resolved alert: {alert_id}")
            
    def add_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler."""
        self._alert_handlers.append(handler)
        
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [a for a in self._alerts.values() if a.is_active]
        
    def get_alerts_by_component(self, component: str) -> List[Alert]:
        """Get alerts for a specific component."""
        return [
            a for a in self._alerts.values()
            if a.component == component and a.is_active
        ]
        
    def cleanup_old_alerts(self, days: int = 7):
        """Remove old resolved alerts."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Clean up resolved alerts
        to_remove = []
        for alert_id, alert in self._alerts.items():
            if alert.resolved_at and alert.resolved_at < cutoff:
                to_remove.append(alert_id)
                
        for alert_id in to_remove:
            del self._alerts[alert_id]
            
        # Clean up history
        self._alert_history = [
            a for a in self._alert_history
            if a.created_at > cutoff
        ]


class IntegratedMonitoring:
    """Unified monitoring system for AgentiCraft."""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        """Initialize integrated monitoring."""
        self.config = config or MonitoringConfig()
        
        # Components
        self.health_monitor = get_health_monitor()
        self.metrics = get_metrics()
        self.alert_manager = AlertManager(self.config)
        self.audit_logger = AuditLogger()
        
        # State
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._dashboard_data: Dict[str, Any] = {}
        
        # Set up alert handlers
        self._setup_alert_handlers()
        
    def _setup_alert_handlers(self):
        """Set up default alert handlers."""
        # Log critical alerts to audit log
        async def audit_critical_alerts(alert: Alert):
            if alert.severity == "critical":
                await self.audit_logger.log_security_alert(
                    alert_type="monitoring_alert",
                    severity=AuditSeverity.CRITICAL,
                    description=alert.message,
                    details=alert.to_dict()
                )
                
        self.alert_manager.add_handler(audit_critical_alerts)
        
    async def start(self):
        """Start integrated monitoring."""
        if self._is_running:
            logger.warning("Monitoring already running")
            return
            
        self._is_running = True
        
        # Start components
        await self.health_monitor.start_monitoring(self.config.health_check_interval)
        await self.metrics.start_collection(self.config.metrics_collection_interval)
        
        # Start monitoring loop
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Started integrated monitoring")
        
    async def stop(self):
        """Stop integrated monitoring."""
        self._is_running = False
        
        # Stop monitoring loop
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
                
        # Stop components
        await self.health_monitor.stop_monitoring()
        await self.metrics.stop_collection()
        
        logger.info("Stopped integrated monitoring")
        
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._is_running:
            try:
                # Check health and create alerts
                await self._check_health_alerts()
                
                # Update dashboard data
                await self._update_dashboard()
                
                # Clean up old alerts
                self.alert_manager.cleanup_old_alerts()
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                
            await asyncio.sleep(self.config.dashboard_refresh_interval)
            
    async def _check_health_alerts(self):
        """Check health status and create alerts."""
        health_status = self.health_monitor.get_status()
        
        # Check overall status
        if health_status["status"] == HealthStatus.UNHEALTHY.value:
            self.alert_manager.create_alert(
                severity="critical",
                component="system",
                message="System health critical",
                details=health_status
            )
        elif health_status["status"] == HealthStatus.DEGRADED.value:
            self.alert_manager.create_alert(
                severity="warning",
                component="system",
                message="System health degraded",
                details=health_status
            )
            
        # Check individual components
        for component_name, component_data in health_status.get("components", {}).items():
            if component_data["status"] == HealthStatus.UNHEALTHY.value:
                self.alert_manager.create_alert(
                    severity="error",
                    component=component_name,
                    message=f"{component_name} is unhealthy",
                    details=component_data
                )
                
    async def _update_dashboard(self):
        """Update dashboard data."""
        self._dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "health": self.health_monitor.get_status(),
            "metrics": self._get_key_metrics(),
            "alerts": {
                "active": [a.to_dict() for a in self.alert_manager.get_active_alerts()],
                "summary": self._get_alert_summary()
            },
            "system": self._get_system_info()
        }
        
    def _get_key_metrics(self) -> Dict[str, Any]:
        """Get key metrics for dashboard."""
        return {
            "agents": {
                "active": self.metrics.agent.active_agents._value.get(),
                "total_executions": sum(
                    self.metrics.agent.executions_total._metrics.values()
                ),
                "error_rate": self._calculate_error_rate("agent")
            },
            "workflows": {
                "active": self.metrics.workflow.active_workflows._value.get(),
                "total_executions": sum(
                    self.metrics.workflow.executions_total._metrics.values()
                ),
                "avg_duration": self._calculate_avg_duration("workflow")
            },
            "security": {
                "active_sessions": self.metrics.security.active_sessions._value.get(),
                "auth_failures": self._count_auth_failures(),
                "sandbox_violations": sum(
                    self.metrics.security.sandbox_violations._metrics.values()
                )
            }
        }
        
    def _get_alert_summary(self) -> Dict[str, int]:
        """Get alert summary by severity."""
        active_alerts = self.alert_manager.get_active_alerts()
        
        summary = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        for alert in active_alerts:
            summary[alert.severity] = summary.get(alert.severity, 0) + 1
            
        return summary
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "cpu_usage": self.metrics.system.cpu_usage._value.get(),
            "memory_usage_percent": self.metrics.system.memory_percent._value.get(),
            "active_tasks": self.metrics.system.active_tasks._value.get(),
            "uptime_hours": self._calculate_uptime()
        }
        
    def _calculate_error_rate(self, component: str) -> float:
        """Calculate error rate for a component."""
        # This is a simplified calculation
        # In production, you'd want time-windowed calculations
        return 0.0  # Placeholder
        
    def _calculate_avg_duration(self, component: str) -> float:
        """Calculate average duration for a component."""
        # This is a simplified calculation
        return 0.0  # Placeholder
        
    def _count_auth_failures(self) -> int:
        """Count authentication failures."""
        # This would query from metrics
        return 0  # Placeholder
        
    def _calculate_uptime(self) -> float:
        """Calculate system uptime in hours."""
        # This would track from start time
        return 0.0  # Placeholder
        
    def get_dashboard(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        return self._dashboard_data
        
    def export_metrics(self, format: str = "prometheus") -> bytes:
        """Export metrics in specified format."""
        if format == "prometheus":
            return self.metrics.generate_metrics()
        elif format == "json":
            data = {
                "timestamp": datetime.now().isoformat(),
                "dashboard": self.get_dashboard(),
                "health": self.health_monitor.get_status(),
                "alerts": [a.to_dict() for a in self.alert_manager.get_active_alerts()]
            }
            return json.dumps(data, indent=2).encode()
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    async def create_health_endpoint(self):
        """Create health check endpoint handler."""
        async def health_handler(request):
            """Handle health check requests."""
            status = self.health_monitor.get_status()
            
            # Determine HTTP status code
            if status["status"] == HealthStatus.HEALTHY.value:
                status_code = 200
            elif status["status"] == HealthStatus.DEGRADED.value:
                status_code = 200  # Still return 200 for degraded
            else:
                status_code = 503  # Service unavailable
                
            return {
                "status_code": status_code,
                "body": status,
                "headers": {"Content-Type": "application/json"}
            }
            
        return health_handler
        
    async def create_metrics_endpoint(self):
        """Create metrics endpoint handler."""
        async def metrics_handler(request):
            """Handle metrics requests."""
            metrics_data = self.metrics.generate_metrics()
            
            return {
                "status_code": 200,
                "body": metrics_data,
                "headers": {"Content-Type": self.metrics.content_type}
            }
            
        return metrics_handler


# Global monitoring instance
_monitoring: Optional[IntegratedMonitoring] = None


def get_monitoring() -> IntegratedMonitoring:
    """Get global monitoring instance."""
    global _monitoring
    
    if _monitoring is None:
        _monitoring = IntegratedMonitoring()
        
    return _monitoring


async def start_monitoring(config: Optional[MonitoringConfig] = None):
    """Start global monitoring."""
    global _monitoring
    
    _monitoring = IntegratedMonitoring(config)
    await _monitoring.start()
    
    return _monitoring
