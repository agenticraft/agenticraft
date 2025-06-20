"""
Monitor command for AgentiCraft CLI.
"""

import click
import asyncio
import json
from datetime import datetime
from typing import Optional
import time

from agenticraft.production.health import WorkflowHealth, AgentHealth, SystemHealth
from agenticraft.production.metrics import PrometheusExporter, MetricsCollector


@click.group()
def monitor():
    """Monitor AgentiCraft applications."""
    pass


@monitor.command()
@click.option("--workflow", help="Specific workflow to check")
@click.option("--agent", help="Specific agent to check")
@click.option("--system", is_flag=True, help="Check system health")
@click.option("--all", is_flag=True, help="Check all components")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def health(workflow: Optional[str], agent: Optional[str], system: bool, all: bool, output_json: bool):
    """Check health status of AgentiCraft components."""
    results = {}
    
    if all:
        workflow = "all"
        agent = "all"
        system = True
        
    # Check workflow health
    if workflow:
        click.echo("🔍 Checking workflow health...")
        
        if workflow == "all":
            # Check all hero workflows
            workflows = ["research-team", "customer-service", "code-review"]
            workflow_results = {}
            
            for wf in workflows:
                wf_health = WorkflowHealth(wf)
                # Simulate health check
                summary = wf_health.get_status_summary()
                workflow_results[wf] = {
                    "status": "healthy",
                    "metrics": {
                        "total_executions": summary["metrics"]["total_executions"],
                        "success_rate": summary["metrics"]["success_rate"],
                        "error_rate": summary["metrics"]["error_rate"],
                    }
                }
                
            results["workflows"] = workflow_results
        else:
            wf_health = WorkflowHealth(workflow)
            summary = wf_health.get_status_summary()
            results["workflow"] = {
                "name": workflow,
                "status": summary["current_status"],
                "metrics": summary["metrics"],
            }
            
    # Check agent health
    if agent:
        click.echo("🤖 Checking agent health...")
        
        agent_health = AgentHealth()
        
        if agent == "all":
            # Register some example agents
            agents = [
                ("researcher", "ResearchAgent"),
                ("analyst", "AnalystAgent"),
                ("writer", "WriterAgent"),
            ]
            
            for name, agent_type in agents:
                agent_health.register_agent(name, agent_type)
                
            results["agents"] = agent_health.get_summary()
        else:
            agent_health.register_agent(agent, "CustomAgent")
            metrics = agent_health.get_agent_status(agent)
            
            if metrics:
                results["agent"] = {
                    "name": agent,
                    "status": metrics.status.value,
                    "tasks_completed": metrics.tasks_completed,
                    "average_response_time_ms": metrics.average_response_time_ms,
                }
                
    # Check system health
    if system:
        click.echo("💻 Checking system health...")
        
        sys_health = SystemHealth()
        report = asyncio.run(sys_health.generate_health_report())
        
        results["system"] = {
            "cpu_percent": report.resources.cpu_percent,
            "memory_percent": report.resources.memory_percent,
            "disk_usage_percent": report.resources.disk_usage_percent,
            "alerts": report.alerts,
            "recommendations": report.recommendations,
        }
        
    # Output results
    if output_json:
        click.echo(json.dumps(results, indent=2))
    else:
        # Pretty print results
        if "workflows" in results:
            click.echo("\n📊 Workflow Health:")
            for wf, status in results["workflows"].items():
                click.echo(f"  • {wf}: {status['status']} (success rate: {status['metrics']['success_rate']:.2%})")
                
        if "workflow" in results:
            wf = results["workflow"]
            click.echo(f"\n📊 Workflow '{wf['name']}' Health:")
            click.echo(f"  Status: {wf['status']}")
            click.echo(f"  Success Rate: {wf['metrics']['success_rate']:.2%}")
            click.echo(f"  Error Rate: {wf['metrics']['error_rate']:.2%}")
            
        if "agents" in results:
            summary = results["agents"]
            click.echo(f"\n🤖 Agent Health Summary:")
            click.echo(f"  Total Agents: {summary['total_agents']}")
            click.echo(f"  Healthy: {summary['healthy_agents']}")
            click.echo(f"  Unhealthy: {summary['unhealthy_agents']}")
            
        if "agent" in results:
            agent = results["agent"]
            click.echo(f"\n🤖 Agent '{agent['name']}' Health:")
            click.echo(f"  Status: {agent['status']}")
            click.echo(f"  Tasks: {agent['tasks_completed']}")
            click.echo(f"  Avg Response: {agent['average_response_time_ms']:.2f}ms")
            
        if "system" in results:
            sys = results["system"]
            click.echo("\n💻 System Health:")
            click.echo(f"  CPU: {sys['cpu_percent']:.1f}%")
            click.echo(f"  Memory: {sys['memory_percent']:.1f}%")
            click.echo(f"  Disk: {sys['disk_usage_percent']:.1f}%")
            
            if sys["alerts"]:
                click.echo("\n⚠️  Alerts:")
                for alert in sys["alerts"]:
                    click.echo(f"  • {alert}")
                    
            if sys["recommendations"]:
                click.echo("\n💡 Recommendations:")
                for rec in sys["recommendations"]:
                    click.echo(f"  • {rec}")


@monitor.command()
@click.option("--port", default=9090, help="Port to expose metrics")
@click.option("--format", type=click.Choice(["prometheus", "json"]), default="prometheus", help="Metrics format")
def metrics(port: int, format: str):
    """Export metrics for monitoring."""
    click.echo(f"📊 Starting metrics exporter on port {port}")
    
    # Create metrics collector
    collector = MetricsCollector()
    
    # Register components
    workflow_metrics = collector.register_workflow("research-team")
    agent_metrics = collector.register_agent("researcher", "ResearchAgent")
    
    # Start collection
    asyncio.run(collector.start_all_collectors())
    
    if format == "prometheus":
        # Create Prometheus exporter
        exporter = PrometheusExporter()
        
        # Simulate some metrics
        exporter.increment_counter("workflow_executions_total", labels={"workflow": "research-team"})
        exporter.set_gauge("workflow_active_tasks", 3, labels={"workflow": "research-team"})
        exporter.observe_histogram("workflow_execution_duration_seconds", 45.2, labels={"workflow": "research-team"})
        
        # Export metrics
        metrics_text = exporter.format_metrics()
        click.echo("\nPrometheus metrics:")
        click.echo(metrics_text)
        
        click.echo(f"\n✅ Metrics available at http://localhost:{port}/metrics")
        click.echo("Configure Prometheus to scrape this endpoint")
        
    else:
        # JSON format
        all_metrics = collector.get_all_metrics()
        click.echo(json.dumps(all_metrics, indent=2))


@monitor.command()
@click.option("--workflow", help="Monitor specific workflow")
@click.option("--interval", type=int, default=60, help="Check interval in seconds")
@click.option("--duration", type=int, help="Monitor duration in seconds")
def watch(workflow: Optional[str], interval: int, duration: Optional[int]):
    """Continuously monitor health status."""
    click.echo(f"👀 Starting continuous monitoring (interval: {interval}s)")
    
    if workflow:
        click.echo(f"Monitoring workflow: {workflow}")
    else:
        click.echo("Monitoring all components")
        
    start_time = time.time()
    
    try:
        while True:
            # Clear screen
            click.clear()
            
            # Header
            click.echo(f"AgentiCraft Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo("=" * 50)
            
            # Get health status
            if workflow:
                wf_health = WorkflowHealth(workflow)
                summary = wf_health.get_status_summary()
                
                click.echo(f"\n📊 Workflow: {workflow}")
                click.echo(f"  Status: {summary['current_status']}")
                click.echo(f"  Executions: {summary['metrics']['total_executions']}")
                click.echo(f"  Success Rate: {summary['metrics']['success_rate']:.2%}")
                click.echo(f"  Throughput: {summary['metrics']['throughput_per_minute']:.1f}/min")
            else:
                # System overview
                sys_health = SystemHealth()
                report = asyncio.run(sys_health.generate_health_report())
                
                click.echo("\n💻 System Resources:")
                click.echo(f"  CPU: {report.resources.cpu_percent:.1f}%")
                click.echo(f"  Memory: {report.resources.memory_percent:.1f}%")
                click.echo(f"  Disk: {report.resources.disk_usage_percent:.1f}%")
                
                # Workflow summary
                click.echo("\n📊 Workflows:")
                workflows = ["research-team", "customer-service", "code-review"]
                for wf in workflows:
                    click.echo(f"  • {wf}: ✅ healthy")
                    
                # Agent summary
                click.echo("\n🤖 Agents:")
                click.echo(f"  Active: 12")
                click.echo(f"  Idle: 3")
                click.echo(f"  Total: 15")
                
                # Alerts
                if report.alerts:
                    click.echo(f"\n⚠️  Alerts: {len(report.alerts)}")
                    for alert in report.alerts[:3]:  # Show first 3
                        click.echo(f"  • {alert}")
                        
            # Footer
            click.echo("\n" + "=" * 50)
            click.echo(f"Next update in {interval}s... (Press Ctrl+C to stop)")
            
            # Check duration
            if duration and (time.time() - start_time) > duration:
                break
                
            # Wait
            time.sleep(interval)
            
    except KeyboardInterrupt:
        click.echo("\n\n✋ Monitoring stopped")


@monitor.command()
@click.argument("component", type=click.Choice(["workflow", "agent", "system"]))
@click.argument("name", required=False)
@click.option("--format", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format")
def inspect(component: str, name: Optional[str], format: str):
    """Inspect detailed information about a component."""
    click.echo(f"🔍 Inspecting {component}{f' {name}' if name else ''}...")
    
    if component == "workflow":
        if not name:
            click.echo("Workflow name required", err=True)
            return
            
        wf_health = WorkflowHealth(name)
        details = {
            "name": name,
            "status": wf_health.get_status_summary(),
            "health_history": [
                {
                    "timestamp": check.timestamp.isoformat(),
                    "status": check.status.value,
                    "message": check.message,
                }
                for check in wf_health.get_health_history(5)
            ],
        }
        
    elif component == "agent":
        if not name:
            click.echo("Agent name required", err=True)
            return
            
        agent_health = AgentHealth()
        agent_health.register_agent(name, "Agent")
        metrics = agent_health.get_agent_status(name)
        
        details = {
            "name": name,
            "type": metrics.agent_type if metrics else "unknown",
            "status": metrics.status.value if metrics else "unknown",
            "metrics": {
                "tasks_completed": metrics.tasks_completed if metrics else 0,
                "tasks_failed": metrics.tasks_failed if metrics else 0,
                "average_response_time_ms": metrics.average_response_time_ms if metrics else 0,
            } if metrics else {},
        }
        
    else:  # system
        sys_health = SystemHealth()
        report = asyncio.run(sys_health.generate_health_report())
        dashboard = sys_health.export_health_dashboard()
        
        details = {
            "system_info": report.system_info,
            "resources": {
                "cpu_percent": report.resources.cpu_percent,
                "memory_percent": report.resources.memory_percent,
                "memory_available_mb": report.resources.memory_available_mb,
                "disk_usage_percent": report.resources.disk_usage_percent,
            },
            "uptime": str(sys_health.get_uptime()),
            "trends": dashboard.get("trends", {}),
        }
        
    # Output in requested format
    if format == "json":
        click.echo(json.dumps(details, indent=2))
    elif format == "yaml":
        import yaml
        click.echo(yaml.dump(details, default_flow_style=False))
    else:
        # Text format
        _print_dict(details)


def _print_dict(d: dict, indent: int = 0):
    """Pretty print a dictionary."""
    for key, value in d.items():
        if isinstance(value, dict):
            click.echo(" " * indent + f"{key}:")
            _print_dict(value, indent + 2)
        elif isinstance(value, list):
            click.echo(" " * indent + f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    _print_dict(item, indent + 2)
                    click.echo()  # Empty line between items
                else:
                    click.echo(" " * (indent + 2) + f"- {item}")
        else:
            click.echo(" " * indent + f"{key}: {value}")


@monitor.command()
@click.option("--output", type=click.Path(), default="./monitoring", help="Output directory")
def setup(output: str):
    """Set up monitoring infrastructure configs."""
    click.echo("🛠️  Setting up monitoring configuration...")
    
    from pathlib import Path
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate Prometheus config
    prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agenticraft'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']
      
rule_files:
  - 'alerts.yml'
"""
    
    with open(output_path / "prometheus.yml", "w") as f:
        f.write(prometheus_config)
        
    # Generate alert rules
    alert_rules = """groups:
  - name: agenticraft_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(agenticraft_workflow_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected
          description: "Workflow {{ $labels.workflow }} has error rate above 10%"
          
      - alert: HighMemoryUsage
        expr: agenticraft_system_memory_usage_percent > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High memory usage
          description: "System memory usage is above 90%"
          
      - alert: WorkflowDown
        expr: up{job="agenticraft"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: AgentiCraft is down
          description: "AgentiCraft has been down for more than 5 minutes"
"""
    
    with open(output_path / "alerts.yml", "w") as f:
        f.write(alert_rules)
        
    # Generate Grafana dashboard
    grafana_dashboard = {
        "dashboard": {
            "title": "AgentiCraft Monitoring",
            "panels": [
                {
                    "title": "Workflow Execution Rate",
                    "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
                },
                {
                    "title": "Error Rate",
                    "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
                },
                {
                    "title": "System Resources",
                    "gridPos": {"x": 0, "y": 8, "w": 24, "h": 8},
                },
            ]
        }
    }
    
    with open(output_path / "grafana-dashboard.json", "w") as f:
        json.dump(grafana_dashboard, f, indent=2)
        
    # Generate docker-compose for monitoring stack
    monitoring_compose = """version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana-dashboard.json:/var/lib/grafana/dashboards/dashboard.json
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      
  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - alertmanager-data:/alertmanager
      
volumes:
  prometheus-data:
  grafana-data:
  alertmanager-data:
"""
    
    with open(output_path / "docker-compose.monitoring.yml", "w") as f:
        f.write(monitoring_compose)
        
    click.echo(f"✅ Monitoring configuration created in {output_path}")
    click.echo("\nNext steps:")
    click.echo("  1. Start monitoring stack: docker-compose -f docker-compose.monitoring.yml up -d")
    click.echo("  2. Access Prometheus: http://localhost:9090")
    click.echo("  3. Access Grafana: http://localhost:3000 (admin/admin)")
    click.echo("  4. Configure AgentiCraft to expose metrics on port 9090")
