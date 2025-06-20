"""
AgentiCraft Production Utilities.

This module provides production-ready utilities for deploying and monitoring
AgentiCraft workflows in production environments.

Phase 5 adds:
- Enhanced configuration management with encryption
- Comprehensive monitoring with Prometheus metrics
- Integrated health checks
- Performance optimization tools
"""

# Legacy imports (keep for backward compatibility)
from agenticraft.production.health import WorkflowHealth, AgentHealth, SystemHealth
from agenticraft.production.metrics import MetricsCollector, PrometheusExporter
from agenticraft.production.config import ConfigManager, SecretManager, EnvironmentConfig
from agenticraft.production.deploy import DockerDeployer, KubernetesDeployer, CloudDeployer

# Phase 5: Enhanced configuration
from agenticraft.production.config.secure_config import (
    SecureConfigManager,
    ConfigEnvironment,
    ConfigValue,
    get_config,
    init_config
)

# Phase 5: Advanced monitoring
from agenticraft.production.monitoring import (
    # Health monitoring
    HealthMonitor,
    HealthStatus,
    HealthCheck,
    ComponentHealth,
    SystemHealthChecker,
    AgentHealthChecker,
    get_health_monitor,
    
    # Prometheus metrics
    PrometheusExporter as PrometheusExporterV2,
    AgentMetrics,
    WorkflowMetrics,
    SecurityMetrics,
    ProtocolMetrics,
    SystemMetrics,
    get_metrics,
    init_metrics,
    
    # Integrated monitoring
    IntegratedMonitoring,
    MonitoringConfig,
    Alert,
    AlertManager,
    get_monitoring,
    start_monitoring
)

# Phase 5: Performance optimization
from agenticraft.production.performance import (
    LRUCache,
    cached,
    ConnectionPool,
    AsyncBatcher,
    ResourceManager,
    get_connection_pool,
    register_connection_pool,
    get_resource_manager
)

__all__ = [
    # Legacy exports (backward compatibility)
    "WorkflowHealth",
    "AgentHealth", 
    "SystemHealth",
    "MetricsCollector",
    "PrometheusExporter",
    "ConfigManager",
    "SecretManager",
    "EnvironmentConfig",
    "DockerDeployer",
    "KubernetesDeployer",
    "CloudDeployer",
    
    # Phase 5: Enhanced configuration
    "SecureConfigManager",
    "ConfigEnvironment",
    "ConfigValue",
    "get_config",
    "init_config",
    
    # Phase 5: Health monitoring
    "HealthMonitor",
    "HealthStatus",
    "HealthCheck",
    "ComponentHealth",
    "SystemHealthChecker",
    "AgentHealthChecker",
    "get_health_monitor",
    
    # Phase 5: Prometheus metrics (v2)
    "PrometheusExporterV2",
    "AgentMetrics",
    "WorkflowMetrics",
    "SecurityMetrics",
    "ProtocolMetrics",
    "SystemMetrics",
    "get_metrics",
    "init_metrics",
    
    # Phase 5: Integrated monitoring
    "IntegratedMonitoring",
    "MonitoringConfig",
    "Alert",
    "AlertManager",
    "get_monitoring",
    "start_monitoring",
    
    # Phase 5: Performance optimization
    "LRUCache",
    "cached",
    "ConnectionPool",
    "AsyncBatcher",
    "ResourceManager",
    "get_connection_pool",
    "register_connection_pool",
    "get_resource_manager"
]
