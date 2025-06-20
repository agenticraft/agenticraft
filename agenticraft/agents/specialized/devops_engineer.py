"""DevOps Engineer Agent - Simplified for AgentiCraft.

A specialized agent for deployment automation, infrastructure management,
and CI/CD pipeline optimization.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from agenticraft.core.agent import Agent, AgentConfig
from agenticraft.core.reasoning import ReasoningTrace, SimpleReasoning


class DevOpsEngineer(Agent):
    """
    DevOps engineer agent for deployment and infrastructure automation.
    
    Focuses on:
    - Deployment strategies and automation
    - CI/CD pipeline configuration
    - Infrastructure as Code (IaC)
    - Container orchestration
    - Monitoring and alerting setup
    """
    
    def __init__(self, name: str = "DevOps Engineer", **kwargs):
        config = AgentConfig(
            name=name,
            role="devops_engineer",
            specialty="deployment and infrastructure automation",
            personality_traits={
                "systematic": 0.9,
                "reliable": 0.9,
                "efficient": 0.8,
                "cautious": 0.7,
                "innovative": 0.6
            },
            **kwargs
        )
        super().__init__(config)
        
        # Deployment strategies
        self.deployment_strategies = {
            "rolling": "Gradually replace instances with no downtime",
            "blue_green": "Deploy to parallel environment and switch",
            "canary": "Test with small percentage before full rollout",
            "recreate": "Stop all instances and deploy new version"
        }
        
        # Common platforms
        self.platforms = ["kubernetes", "docker", "aws", "azure", "gcp"]
    
    async def plan_deployment(self, 
                            service: str, 
                            version: str, 
                            environment: str = "staging",
                            strategy: str = "rolling") -> Dict[str, Any]:
        """Plan a deployment with appropriate strategy."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            f"Planning deployment of {service} v{version} to {environment}"
        )
        
        # Validate strategy
        if strategy not in self.deployment_strategies:
            strategy = "rolling"
            trace.add_step("strategy_selection", {
                "message": "Unknown strategy, defaulting to rolling deployment",
                "strategy": "rolling"
            })
        
        trace.add_step("strategy_chosen", {
            "strategy": strategy,
            "description": self.deployment_strategies.get(strategy, "")
        })
        
        # Create deployment plan
        plan = {
            "service": service,
            "version": version,
            "environment": environment,
            "strategy": strategy,
            "steps": [],
            "health_checks": [],
            "rollback_plan": []
        }
        
        # Define steps based on strategy
        if strategy == "rolling":
            plan["steps"] = [
                "1. Build and tag Docker image",
                "2. Push image to registry",
                "3. Update 25% of instances",
                "4. Health check and monitor",
                "5. Continue with remaining instances",
                "6. Verify deployment success"
            ]
        elif strategy == "blue_green":
            plan["steps"] = [
                "1. Deploy to green environment",
                "2. Run smoke tests on green",
                "3. Warm up green environment",
                "4. Switch traffic to green",
                "5. Monitor for issues",
                "6. Keep blue for quick rollback"
            ]
        elif strategy == "canary":
            plan["steps"] = [
                "1. Deploy canary version",
                "2. Route 5% traffic to canary",
                "3. Monitor error rates and latency",
                "4. Gradually increase traffic (25%, 50%, 100%)",
                "5. Full rollout if metrics are good",
                "6. Rollback if issues detected"
            ]
        
        # Add health checks
        plan["health_checks"] = [
            f"GET /health endpoint returns 200",
            f"Response time < 500ms",
            f"Error rate < 1%",
            f"CPU usage < 80%",
            f"Memory usage < 90%"
        ]
        
        # Add rollback plan
        plan["rollback_plan"] = [
            "1. Stop new deployment immediately",
            "2. Route traffic back to previous version",
            "3. Verify previous version is stable",
            "4. Investigate deployment failure",
            "5. Document lessons learned"
        ]
        
        # Estimate time
        time_estimates = {
            "rolling": "15-20 minutes",
            "blue_green": "10-15 minutes",
            "canary": "30-45 minutes",
            "recreate": "5-10 minutes (with downtime)"
        }
        
        plan["estimated_time"] = time_estimates.get(strategy, "20 minutes")
        plan["downtime_expected"] = strategy == "recreate"
        
        trace.complete({"result": f"Deployment plan created with {len(plan['steps'])} steps"})
        self.last_reasoning = trace
        
        return {
            "plan": plan,
            "risks": self._assess_deployment_risks(environment, strategy),
            "prerequisites": self._get_deployment_prerequisites(service, environment),
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def generate_ci_cd_pipeline(self, 
                                    project_type: str,
                                    platform: str = "github") -> Dict[str, Any]:
        """Generate CI/CD pipeline configuration."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            f"Creating CI/CD pipeline for {project_type} project on {platform}"
        )
        
        # Basic pipeline structure
        pipeline = {
            "stages": ["build", "test", "deploy"],
            "jobs": {}
        }
        
        # Build stage
        trace.add_step("configure_build", {"stage": "build"})
        pipeline["jobs"]["build"] = {
            "stage": "build",
            "steps": []
        }
        
        if project_type == "python":
            pipeline["jobs"]["build"]["steps"] = [
                "checkout code",
                "setup python 3.9",
                "pip install -r requirements.txt",
                "python -m build"
            ]
        elif project_type == "node":
            pipeline["jobs"]["build"]["steps"] = [
                "checkout code",
                "setup node 18",
                "npm ci",
                "npm run build"
            ]
        elif project_type == "java":
            pipeline["jobs"]["build"]["steps"] = [
                "checkout code",
                "setup java 11",
                "mvn clean package"
            ]
        
        # Test stage
        trace.add_step("configure_test", {"stage": "test"})
        pipeline["jobs"]["test"] = {
            "stage": "test",
            "steps": []
        }
        
        if project_type == "python":
            pipeline["jobs"]["test"]["steps"] = [
                "pytest tests/ --cov=src",
                "flake8 src/",
                "mypy src/"
            ]
        elif project_type == "node":
            pipeline["jobs"]["test"]["steps"] = [
                "npm run test",
                "npm run lint",
                "npm audit"
            ]
        
        # Deploy stage
        trace.add_step("configure_deploy", {"stage": "deploy"})
        pipeline["jobs"]["deploy"] = {
            "stage": "deploy",
            "steps": [
                "build docker image",
                "push to registry",
                "deploy to kubernetes",
                "run smoke tests"
            ],
            "only": ["main", "master"]  # Only deploy from main branch
        }
        
        # Generate platform-specific config
        if platform == "github":
            config = self._generate_github_actions(pipeline)
        elif platform == "gitlab":
            config = self._generate_gitlab_ci(pipeline)
        elif platform == "jenkins":
            config = self._generate_jenkinsfile(pipeline)
        else:
            config = pipeline
        
        trace.complete({"result": f"CI/CD pipeline generated with {len(pipeline['stages'])} stages"})
        self.last_reasoning = trace
        
        return {
            "pipeline": pipeline,
            "config": config,
            "platform": platform,
            "best_practices": [
                "Always run tests before deployment",
                "Use environment variables for secrets",
                "Tag releases with semantic versioning",
                "Keep build artifacts for rollback",
                "Monitor pipeline performance"
            ],
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def create_kubernetes_manifest(self,
                                       service: str,
                                       image: str,
                                       replicas: int = 3,
                                       port: int = 8080) -> Dict[str, Any]:
        """Create Kubernetes deployment manifest."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            f"Creating Kubernetes manifests for {service}"
        )
        
        trace.add_step("configure_deployment", {
            "replicas": replicas,
            "message": f"Configuring deployment with {replicas} replicas"
        })
        
        # Deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": service,
                "labels": {"app": service}
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {"app": service}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": service}
                    },
                    "spec": {
                        "containers": [{
                            "name": service,
                            "image": image,
                            "ports": [{"containerPort": port}],
                            "resources": {
                                "requests": {
                                    "cpu": "100m",
                                    "memory": "128Mi"
                                },
                                "limits": {
                                    "cpu": "500m",
                                    "memory": "512Mi"
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": port
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/ready",
                                    "port": port
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        }
        
        trace.add_step("create_service", {
            "message": "Creating service for load balancing"
        })
        
        # Service manifest
        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service
            },
            "spec": {
                "selector": {"app": service},
                "ports": [{
                    "port": 80,
                    "targetPort": port
                }],
                "type": "LoadBalancer"
            }
        }
        
        # HPA (Horizontal Pod Autoscaler)
        trace.add_step("add_autoscaling", {
            "message": "Adding autoscaling configuration"
        })
        
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": service
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": service
                },
                "minReplicas": replicas,
                "maxReplicas": replicas * 3,
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": 70
                        }
                    }
                }]
            }
        }
        
        trace.complete({"result": "Kubernetes manifests created with deployment, service, and HPA"})
        self.last_reasoning = trace
        
        return {
            "deployment": deployment,
            "service": service_manifest,
            "hpa": hpa,
            "combined_yaml": self._combine_manifests(deployment, service_manifest, hpa),
            "deployment_command": f"kubectl apply -f {service}-manifests.yaml",
            "verification_commands": [
                f"kubectl get deployment {service}",
                f"kubectl get service {service}",
                f"kubectl get hpa {service}"
            ],
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def setup_monitoring(self,
                             service: str,
                             metrics: List[str] = None) -> Dict[str, Any]:
        """Setup monitoring and alerting configuration."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(
            f"Setting up monitoring for {service}"
        )
        
        if not metrics:
            metrics = ["cpu", "memory", "requests", "errors", "latency"]
        
        trace.add_step("configure_metrics", {
            "count": len(metrics),
            "metrics": metrics
        })
        
        # Prometheus configuration
        prometheus_config = {
            "scrape_configs": [{
                "job_name": service,
                "kubernetes_sd_configs": [{
                    "role": "pod"
                }],
                "relabel_configs": [{
                    "source_labels": ["__meta_kubernetes_pod_label_app"],
                    "action": "keep",
                    "regex": service
                }]
            }]
        }
        
        # Grafana dashboard
        trace.add_step("create_dashboard", {
            "message": "Creating Grafana dashboard configuration"
        })
        
        dashboard = {
            "title": f"{service} Dashboard",
            "panels": []
        }
        
        # Create panels for each metric
        for i, metric in enumerate(metrics):
            panel = {
                "id": i + 1,
                "title": metric.title(),
                "type": "graph",
                "targets": [{
                    "expr": self._get_prometheus_query(metric, service)
                }]
            }
            dashboard["panels"].append(panel)
        
        # Alert rules
        trace.add_step("define_alerts", {
            "message": "Defining alert rules"
        })
        
        alerts = []
        alert_configs = {
            "cpu": {"threshold": 80, "severity": "warning"},
            "memory": {"threshold": 90, "severity": "warning"},
            "errors": {"threshold": 5, "severity": "critical"},
            "latency": {"threshold": 1000, "severity": "warning"}
        }
        
        for metric, config in alert_configs.items():
            if metric in metrics:
                alerts.append({
                    "name": f"{service}_{metric}_high",
                    "expr": self._get_alert_expression(metric, service, config["threshold"]),
                    "for": "5m",
                    "labels": {
                        "severity": config["severity"],
                        "service": service
                    },
                    "annotations": {
                        "summary": f"High {metric} for {service}",
                        "description": f"{metric} is above {config['threshold']} for {service}"
                    }
                })
        
        trace.complete({"result": f"Monitoring setup complete with {len(alerts)} alerts"})
        self.last_reasoning = trace
        
        return {
            "prometheus_config": prometheus_config,
            "dashboard": dashboard,
            "alerts": alerts,
            "setup_instructions": [
                "1. Apply Prometheus configuration",
                "2. Import Grafana dashboard",
                "3. Configure alert manager",
                "4. Set up notification channels",
                "5. Test alerts with synthetic data"
            ],
            "reasoning": reasoning.format_trace(trace)
        }
    
    def _assess_deployment_risks(self, environment: str, strategy: str) -> List[str]:
        """Assess risks for deployment."""
        risks = []
        
        if environment == "production":
            risks.extend([
                "Potential user impact during deployment",
                "Database migration compatibility",
                "Third-party service dependencies"
            ])
        
        if strategy == "recreate":
            risks.append("Downtime during deployment")
        elif strategy == "canary":
            risks.append("Inconsistent user experience during rollout")
        
        return risks
    
    def _get_deployment_prerequisites(self, service: str, environment: str) -> List[str]:
        """Get deployment prerequisites."""
        prerequisites = [
            "Docker image built and tested",
            "All tests passing",
            "Configuration updated for environment",
            "Database migrations ready",
            "Monitoring alerts configured"
        ]
        
        if environment == "production":
            prerequisites.extend([
                "Change approval obtained",
                "Rollback plan documented",
                "Team notified of deployment window"
            ])
        
        return prerequisites
    
    def _generate_github_actions(self, pipeline: Dict) -> str:
        """Generate GitHub Actions workflow."""
        yaml_content = f"""name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:"""
        
        for job_name, job_config in pipeline["jobs"].items():
            yaml_content += f"\n  {job_name}:\n    runs-on: ubuntu-latest\n    steps:"
            for step in job_config["steps"]:
                yaml_content += f"\n      - name: {step}\n        run: {step}"
        
        return yaml_content
    
    def _generate_gitlab_ci(self, pipeline: Dict) -> str:
        """Generate GitLab CI configuration."""
        yaml_content = f"stages:\n"
        for stage in pipeline["stages"]:
            yaml_content += f"  - {stage}\n"
        
        for job_name, job_config in pipeline["jobs"].items():
            yaml_content += f"\n{job_name}:\n  stage: {job_config['stage']}\n  script:"
            for step in job_config["steps"]:
                yaml_content += f"\n    - {step}"
        
        return yaml_content
    
    def _generate_jenkinsfile(self, pipeline: Dict) -> str:
        """Generate Jenkinsfile."""
        jenkinsfile = "pipeline {\n  agent any\n  stages {"
        
        for stage in pipeline["stages"]:
            jenkinsfile += f"\n    stage('{stage}') {{\n      steps {{"
            if stage in pipeline["jobs"]:
                for step in pipeline["jobs"][stage]["steps"]:
                    jenkinsfile += f"\n        sh '{step}'"
            jenkinsfile += "\n      }\n    }"
        
        jenkinsfile += "\n  }\n}"
        return jenkinsfile
    
    def _combine_manifests(self, *manifests) -> str:
        """Combine multiple Kubernetes manifests."""
        import json
        yaml_content = ""
        for manifest in manifests:
            yaml_content += "---\n"
            yaml_content += json.dumps(manifest, indent=2) + "\n"
        return yaml_content
    
    def _get_prometheus_query(self, metric: str, service: str) -> str:
        """Get Prometheus query for metric."""
        queries = {
            "cpu": f'rate(container_cpu_usage_seconds_total{{pod=~"{service}-.*"}}[5m])',
            "memory": f'container_memory_usage_bytes{{pod=~"{service}-.*"}}',
            "requests": f'rate(http_requests_total{{service="{service}"}}[5m])',
            "errors": f'rate(http_requests_total{{service="{service}",status=~"5.."}}[5m])',
            "latency": f'histogram_quantile(0.95, http_request_duration_seconds{{service="{service}"}})'
        }
        return queries.get(metric, f'{metric}{{service="{service}"}}')
    
    def _get_alert_expression(self, metric: str, service: str, threshold: float) -> str:
        """Get alert expression for metric."""
        expressions = {
            "cpu": f'{self._get_prometheus_query("cpu", service)} > {threshold/100}',
            "memory": f'{self._get_prometheus_query("memory", service)} > {threshold/100}',
            "errors": f'{self._get_prometheus_query("errors", service)} > {threshold}',
            "latency": f'{self._get_prometheus_query("latency", service)} > {threshold/1000}'
        }
        return expressions.get(metric, f'{metric} > {threshold}')
