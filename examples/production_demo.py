"""
Example demonstrating AgentiCraft production features from Phase 5.

This shows:
- Secure configuration management
- Health monitoring
- Prometheus metrics
- Performance optimization
- Integrated monitoring dashboard
"""
import asyncio
import time
from pathlib import Path

from agenticraft import Agent, Workflow
from agenticraft.workflows import ResearchTeam
from agenticraft.production import (
    # Configuration
    SecureConfigManager,
    ConfigEnvironment,
    get_config,
    
    # Monitoring
    IntegratedMonitoring,
    MonitoringConfig,
    get_monitoring,
    start_monitoring,
    
    # Performance
    cached,
    ConnectionPool,
    register_connection_pool,
    ResourceManager,
    get_resource_manager
)
from agenticraft.security import security


# Example 1: Secure Configuration
async def configure_production():
    """Set up production configuration."""
    print("\n=== Configuring Production Environment ===")
    
    # Initialize secure config
    config = SecureConfigManager(
        environment=ConfigEnvironment.PRODUCTION,
        auto_reload=True
    )
    
    # Set regular configuration
    config.set("app.name", "AgentiCraft Production")
    config.set("app.version", "1.0.0")
    config.set("app.debug", False)
    
    # Set encrypted secrets
    config.set_secret("openai.api_key", "sk-...")
    config.set_secret("database.password", "super-secret-password")
    config.set_secret("jwt.secret", "jwt-signing-secret")
    
    # Get typed configuration
    debug_mode = config.get_typed("app.debug", bool, default=False)
    print(f"Debug mode: {debug_mode}")
    
    # Validate configuration schema
    schema = {
        "app.name": {"required": True, "type": "string"},
        "app.version": {"required": True, "type": "string"},
        "app.port": {"type": "integer", "min": 1, "max": 65535}
    }
    
    errors = config.validate_schema(schema)
    if errors:
        print(f"Configuration errors: {errors}")
    else:
        print("✓ Configuration validated successfully")
        
    # Export configuration (without secrets)
    export_data = config.export_config(include_secrets=False)
    print(f"✓ Exported {len(export_data['configuration'])} config values")
    
    return config


# Example 2: Health Monitoring
async def setup_health_monitoring():
    """Set up health monitoring."""
    print("\n=== Setting Up Health Monitoring ===")
    
    # Get health monitor
    health_monitor = get_health_monitor()
    
    # Register custom health check
    async def database_health_check():
        """Check database connectivity."""
        from agenticraft.production.monitoring import ComponentHealth, HealthCheck, HealthStatus
        
        component = ComponentHealth("database")
        
        # Simulate database check
        try:
            # In real app, check actual database
            await asyncio.sleep(0.1)  # Simulate query
            
            component.checks.append(HealthCheck(
                name="connectivity",
                status=HealthStatus.HEALTHY,
                message="Database connection OK",
                details={"latency_ms": 10}
            ))
        except Exception as e:
            component.checks.append(HealthCheck(
                name="connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {e}"
            ))
            
        return component
        
    health_monitor.register_checker("database", database_health_check)
    
    # Run health check
    health_results = await health_monitor.check_all()
    
    # Display results
    for component_name, component_health in health_results.items():
        status = component_health.overall_status.value
        print(f"  {component_name}: {status}")
        
    return health_monitor


# Example 3: Performance Optimization
@cached(max_size=100, ttl_seconds=60)
async def expensive_operation(query: str) -> str:
    """Simulate expensive operation with caching."""
    print(f"  Computing result for: {query}")
    await asyncio.sleep(1)  # Simulate work
    return f"Result for {query}"


async def demonstrate_performance():
    """Demonstrate performance optimizations."""
    print("\n=== Performance Optimization Demo ===")
    
    # Test caching
    print("Testing LRU cache:")
    start = time.time()
    result1 = await expensive_operation("test query")
    duration1 = time.time() - start
    print(f"  First call: {duration1:.3f}s")
    
    start = time.time()
    result2 = await expensive_operation("test query")  # Should be cached
    duration2 = time.time() - start
    print(f"  Second call (cached): {duration2:.3f}s")
    
    # Check cache stats
    cache_stats = expensive_operation.cache.stats()
    print(f"  Cache stats: {cache_stats}")
    
    # Connection pooling
    print("\nTesting connection pool:")
    
    async def create_mock_connection():
        """Mock connection factory."""
        await asyncio.sleep(0.1)  # Simulate connection time
        return {"id": time.time(), "connected": True}
        
    # Register pool
    pool = register_connection_pool(
        "database",
        create_mock_connection,
        max_size=5,
        min_size=2
    )
    
    await pool.initialize()
    
    # Use connections
    conn1 = await pool.acquire()
    print(f"  Acquired connection: {conn1['id']}")
    
    conn2 = await pool.acquire()
    print(f"  Acquired another: {conn2['id']}")
    
    # Release back to pool
    await pool.release(conn1)
    await pool.release(conn2)
    
    print(f"  Pool stats: {pool.stats()}")
    
    # Resource management
    print("\nTesting resource management:")
    resource_manager = get_resource_manager()
    
    # Register agent resources
    resource_manager.register_resource(
        "research_agent",
        limits={"memory_mb": 1024, "cpu_percent": 50}
    )
    
    # Try to allocate
    can_allocate = resource_manager.can_allocate(
        "research_agent",
        {"memory_mb": 512, "cpu_percent": 25}
    )
    print(f"  Can allocate: {can_allocate}")
    
    if can_allocate:
        resource_manager.allocate(
            "research_agent",
            {"memory_mb": 512, "cpu_percent": 25}
        )
        
    utilization = resource_manager.get_utilization("research_agent")
    print(f"  Resource utilization: {utilization}")


# Example 4: Integrated Monitoring
async def production_workflow_with_monitoring():
    """Run production workflow with full monitoring."""
    print("\n=== Production Workflow with Monitoring ===")
    
    # Start monitoring
    monitoring_config = MonitoringConfig(
        health_check_interval=10.0,
        metrics_collection_interval=5.0,
        alert_cooldown_minutes=5
    )
    
    monitoring = await start_monitoring(monitoring_config)
    
    try:
        # Create secure research team
        research_team = ResearchTeam(
            size=3,
            coordination_mode="hybrid",
            sandbox_type="process"
        )
        
        # Track metrics
        metrics = monitoring.metrics
        
        # Execute with monitoring
        with metrics.track_workflow_execution("research_team"):
            # Update agent health
            monitoring.health_monitor.agent_checker.update_agent_status(
                "researcher_1",
                "active",
                error_count=0
            )
            
            # Execute research
            result = await research_team.execute(
                "What are the latest developments in quantum computing?"
            )
            
            # Record step completion
            metrics.workflow.steps_completed.labels(
                workflow_name="research_team",
                step_name="research"
            ).inc()
            
        # Create alert if needed
        if len(str(result)) < 100:
            monitoring.alert_manager.create_alert(
                severity="warning",
                component="research_team",
                message="Research result too short",
                details={"length": len(str(result))}
            )
            
        # Get dashboard data
        dashboard = monitoring.get_dashboard()
        
        print("\n📊 Monitoring Dashboard:")
        print(f"  Health Status: {dashboard['health']['status']}")
        print(f"  Active Alerts: {dashboard['alerts']['summary']}")
        print(f"  System Metrics:")
        print(f"    CPU: {dashboard['system']['cpu_usage']:.1f}%")
        print(f"    Memory: {dashboard['system']['memory_usage_percent']:.1f}%")
        
        # Export metrics
        prometheus_metrics = monitoring.export_metrics("prometheus")
        print(f"\n  Prometheus metrics size: {len(prometheus_metrics)} bytes")
        
    finally:
        # Stop monitoring
        await monitoring.stop()


# Example 5: Production API with Monitoring
async def create_production_api():
    """Create production API with health and metrics endpoints."""
    print("\n=== Production API Endpoints ===")
    
    monitoring = get_monitoring()
    
    # Create health endpoint
    health_handler = await monitoring.create_health_endpoint()
    print("✓ Created health endpoint: GET /health")
    
    # Create metrics endpoint
    metrics_handler = await monitoring.create_metrics_endpoint()
    print("✓ Created metrics endpoint: GET /metrics")
    
    # Example FastAPI integration (conceptual)
    print("\nExample FastAPI integration:")
    print("""
    from fastapi import FastAPI
    from fastapi.responses import Response
    
    app = FastAPI()
    
    @app.get("/health")
    async def health():
        result = await health_handler(None)
        return Response(
            content=json.dumps(result["body"]),
            status_code=result["status_code"],
            media_type="application/json"
        )
        
    @app.get("/metrics")
    async def metrics():
        result = await metrics_handler(None)
        return Response(
            content=result["body"],
            media_type=result["headers"]["Content-Type"]
        )
    """)


# Main execution
async def main():
    """Run all production examples."""
    print("🚀 AgentiCraft Production Features Demo - Phase 5")
    print("=" * 60)
    
    # Configure production environment
    config = await configure_production()
    
    # Set up health monitoring
    health_monitor = await setup_health_monitoring()
    
    # Demonstrate performance features
    await demonstrate_performance()
    
    # Run production workflow with monitoring
    await production_workflow_with_monitoring()
    
    # Show API integration
    await create_production_api()
    
    print("\n✅ Production demo complete!")
    print("\nKey Features Demonstrated:")
    print("  - Secure configuration with encryption")
    print("  - Comprehensive health checks")
    print("  - Prometheus metrics export")
    print("  - Performance optimization (caching, pooling)")
    print("  - Integrated monitoring dashboard")
    print("  - Production-ready API endpoints")


if __name__ == "__main__":
    asyncio.run(main())
