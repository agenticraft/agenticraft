"""
Kubernetes deployment utilities for AgentiCraft.
"""

import os
import yaml
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class KubernetesConfig:
    """Kubernetes deployment configuration."""
    name: str
    namespace: str = "default"
    image: str = "agenticraft:latest"
    replicas: int = 1
    cpu_request: str = "100m"
    cpu_limit: str = "2000m"
    memory_request: str = "256Mi"
    memory_limit: str = "2Gi"
    service_type: str = "ClusterIP"  # ClusterIP, NodePort, LoadBalancer
    ingress_enabled: bool = False
    ingress_host: str = ""
    config_maps: Dict[str, Dict[str, str]] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    health_check_path: str = "/health"
    metrics_path: str = "/metrics"
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


class KubernetesDeployer:
    """Deploy AgentiCraft applications to Kubernetes."""
    
    def __init__(self, config: KubernetesConfig):
        """
        Initialize Kubernetes deployer.
        
        Args:
            config: Kubernetes deployment configuration
        """
        self.config = config
        self.manifests = {}
        
    def generate_deployment(self) -> Dict[str, Any]:
        """Generate Kubernetes Deployment manifest."""
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{self.config.name}-deployment",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.name,
                    "component": "agenticraft",
                    **self.config.labels,
                },
                "annotations": self.config.annotations,
            },
            "spec": {
                "replicas": self.config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": self.config.name,
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": self.config.name,
                            "component": "agenticraft",
                            **self.config.labels,
                        },
                        "annotations": {
                            "prometheus.io/scrape": "true",
                            "prometheus.io/port": "9090",
                            "prometheus.io/path": self.config.metrics_path,
                            **self.config.annotations,
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "agenticraft",
                            "image": self.config.image,
                            "imagePullPolicy": "Always",
                            "ports": [
                                {
                                    "name": "http",
                                    "containerPort": 8000,
                                    "protocol": "TCP",
                                },
                                {
                                    "name": "metrics",
                                    "containerPort": 9090,
                                    "protocol": "TCP",
                                }
                            ],
                            "env": self._generate_env_vars(),
                            "resources": {
                                "requests": {
                                    "cpu": self.config.cpu_request,
                                    "memory": self.config.memory_request,
                                },
                                "limits": {
                                    "cpu": self.config.cpu_limit,
                                    "memory": self.config.memory_limit,
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": self.config.health_check_path,
                                    "port": "http",
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 30,
                                "timeoutSeconds": 10,
                                "failureThreshold": 3,
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": self.config.health_check_path,
                                    "port": "http",
                                },
                                "initialDelaySeconds": 10,
                                "periodSeconds": 10,
                                "timeoutSeconds": 5,
                                "failureThreshold": 3,
                            },
                            "volumeMounts": self._generate_volume_mounts(),
                        }],
                        "volumes": self._generate_volumes(),
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 1000,
                            "fsGroup": 1000,
                        }
                    }
                }
            }
        }
        
        return deployment
        
    def generate_service(self) -> Dict[str, Any]:
        """Generate Kubernetes Service manifest."""
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{self.config.name}-service",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.name,
                    "component": "agenticraft",
                    **self.config.labels,
                },
                "annotations": self.config.annotations,
            },
            "spec": {
                "type": self.config.service_type,
                "selector": {
                    "app": self.config.name,
                },
                "ports": [
                    {
                        "name": "http",
                        "port": 80,
                        "targetPort": "http",
                        "protocol": "TCP",
                    },
                    {
                        "name": "metrics",
                        "port": 9090,
                        "targetPort": "metrics",
                        "protocol": "TCP",
                    }
                ]
            }
        }
        
        return service
        
    def generate_ingress(self) -> Optional[Dict[str, Any]]:
        """Generate Kubernetes Ingress manifest."""
        if not self.config.ingress_enabled:
            return None
            
        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{self.config.name}-ingress",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.name,
                    "component": "agenticraft",
                    **self.config.labels,
                },
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    **self.config.annotations,
                }
            },
            "spec": {
                "tls": [{
                    "hosts": [self.config.ingress_host],
                    "secretName": f"{self.config.name}-tls",
                }] if self.config.ingress_host else [],
                "rules": [{
                    "host": self.config.ingress_host,
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": f"{self.config.name}-service",
                                    "port": {
                                        "name": "http",
                                    }
                                }
                            }
                        }]
                    }
                }] if self.config.ingress_host else []
            }
        }
        
        return ingress
        
    def generate_configmap(self, name: str, data: Dict[str, str]) -> Dict[str, Any]:
        """Generate Kubernetes ConfigMap manifest."""
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{self.config.name}-{name}",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.name,
                    "component": "agenticraft",
                    **self.config.labels,
                },
            },
            "data": data,
        }
        
        return configmap
        
    def generate_hpa(self, min_replicas: int = 1, max_replicas: int = 10, cpu_target: int = 80) -> Dict[str, Any]:
        """Generate Horizontal Pod Autoscaler manifest."""
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": f"{self.config.name}-hpa",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.name,
                    "component": "agenticraft",
                    **self.config.labels,
                },
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": f"{self.config.name}-deployment",
                },
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": cpu_target,
                            }
                        }
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 80,
                            }
                        }
                    }
                ]
            }
        }
        
        return hpa
        
    def generate_pdb(self, min_available: int = 1) -> Dict[str, Any]:
        """Generate Pod Disruption Budget manifest."""
        pdb = {
            "apiVersion": "policy/v1",
            "kind": "PodDisruptionBudget",
            "metadata": {
                "name": f"{self.config.name}-pdb",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.name,
                    "component": "agenticraft",
                    **self.config.labels,
                },
            },
            "spec": {
                "minAvailable": min_available,
                "selector": {
                    "matchLabels": {
                        "app": self.config.name,
                    }
                }
            }
        }
        
        return pdb
        
    def generate_network_policy(self) -> Dict[str, Any]:
        """Generate NetworkPolicy manifest for security."""
        network_policy = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": f"{self.config.name}-netpol",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.name,
                    "component": "agenticraft",
                    **self.config.labels,
                },
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {
                        "app": self.config.name,
                    }
                },
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [
                    {
                        "from": [
                            {
                                "namespaceSelector": {
                                    "matchLabels": {
                                        "name": "ingress-nginx",
                                    }
                                }
                            },
                            {
                                "podSelector": {
                                    "matchLabels": {
                                        "app": "prometheus",
                                    }
                                }
                            }
                        ],
                        "ports": [
                            {
                                "port": 8000,
                                "protocol": "TCP",
                            },
                            {
                                "port": 9090,
                                "protocol": "TCP",
                            }
                        ]
                    }
                ],
                "egress": [
                    {
                        "to": [
                            {
                                "namespaceSelector": {},
                            }
                        ],
                        "ports": [
                            {
                                "port": 53,
                                "protocol": "UDP",
                            },
                            {
                                "port": 443,
                                "protocol": "TCP",
                            },
                            {
                                "port": 6379,
                                "protocol": "TCP",
                            },
                            {
                                "port": 5432,
                                "protocol": "TCP",
                            }
                        ]
                    }
                ]
            }
        }
        
        return network_policy
        
    def _generate_env_vars(self) -> List[Dict[str, Any]]:
        """Generate environment variables for container."""
        env_vars = []
        
        # Add standard env vars
        env_vars.extend([
            {
                "name": "AGENTICRAFT_ENV",
                "value": "kubernetes",
            },
            {
                "name": "POD_NAME",
                "valueFrom": {
                    "fieldRef": {
                        "fieldPath": "metadata.name",
                    }
                }
            },
            {
                "name": "POD_NAMESPACE",
                "valueFrom": {
                    "fieldRef": {
                        "fieldPath": "metadata.namespace",
                    }
                }
            },
            {
                "name": "POD_IP",
                "valueFrom": {
                    "fieldRef": {
                        "fieldPath": "status.podIP",
                    }
                }
            }
        ])
        
        # Add custom env vars
        for key, value in self.config.env_vars.items():
            env_vars.append({
                "name": key,
                "value": value,
            })
            
        # Add secrets
        for secret_name in self.config.secrets:
            env_vars.append({
                "name": secret_name.upper(),
                "valueFrom": {
                    "secretKeyRef": {
                        "name": f"{self.config.name}-secrets",
                        "key": secret_name,
                    }
                }
            })
            
        return env_vars
        
    def _generate_volumes(self) -> List[Dict[str, Any]]:
        """Generate volumes for pod."""
        volumes = []
        
        # Add ConfigMap volumes
        for cm_name in self.config.config_maps:
            volumes.append({
                "name": f"config-{cm_name}",
                "configMap": {
                    "name": f"{self.config.name}-{cm_name}",
                }
            })
            
        # Add custom volumes
        volumes.extend(self.config.volumes)
        
        return volumes
        
    def _generate_volume_mounts(self) -> List[Dict[str, Any]]:
        """Generate volume mounts for container."""
        mounts = []
        
        # Mount ConfigMaps
        for cm_name in self.config.config_maps:
            mounts.append({
                "name": f"config-{cm_name}",
                "mountPath": f"/config/{cm_name}",
                "readOnly": True,
            })
            
        return mounts
        
    def generate_all_manifests(self) -> Dict[str, Dict[str, Any]]:
        """Generate all Kubernetes manifests."""
        manifests = {
            "deployment": self.generate_deployment(),
            "service": self.generate_service(),
        }
        
        # Add optional manifests
        if self.config.ingress_enabled:
            manifests["ingress"] = self.generate_ingress()
            
        # Add ConfigMaps
        for cm_name, cm_data in self.config.config_maps.items():
            manifests[f"configmap-{cm_name}"] = self.generate_configmap(cm_name, cm_data)
            
        # Add HPA
        if self.config.replicas > 1:
            manifests["hpa"] = self.generate_hpa()
            manifests["pdb"] = self.generate_pdb()
            
        # Add NetworkPolicy
        manifests["networkpolicy"] = self.generate_network_policy()
        
        return manifests
        
    def save_manifests(self, output_dir: str = "./k8s"):
        """Save all manifests to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        manifests = self.generate_all_manifests()
        
        for name, manifest in manifests.items():
            file_path = output_path / f"{name}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)
                
        # Create kustomization.yaml
        kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": self.config.namespace,
            "resources": [f"{name}.yaml" for name in manifests.keys()],
            "commonLabels": {
                "app": self.config.name,
                "managed-by": "agenticraft",
            }
        }
        
        with open(output_path / "kustomization.yaml", "w") as f:
            yaml.dump(kustomization, f, default_flow_style=False)
            
        logger.info(f"Saved Kubernetes manifests to {output_path}")
        
    def apply(self, kubectl_context: Optional[str] = None, dry_run: bool = False) -> bool:
        """
        Apply manifests to Kubernetes cluster.
        
        Args:
            kubectl_context: Kubernetes context to use
            dry_run: Whether to perform a dry run
            
        Returns:
            True if successful
        """
        # Save manifests first
        self.save_manifests()
        
        cmd = ["kubectl", "apply", "-k", "./k8s"]
        
        if kubectl_context:
            cmd.extend(["--context", kubectl_context])
            
        if dry_run:
            cmd.append("--dry-run=client")
            
        logger.info(f"Applying manifests: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Successfully applied manifests")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Apply failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error applying manifests: {e}")
            return False
            
    def delete(self, kubectl_context: Optional[str] = None) -> bool:
        """
        Delete resources from Kubernetes cluster.
        
        Args:
            kubectl_context: Kubernetes context to use
            
        Returns:
            True if successful
        """
        cmd = ["kubectl", "delete", "-k", "./k8s"]
        
        if kubectl_context:
            cmd.extend(["--context", kubectl_context])
            
        logger.info(f"Deleting resources: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Successfully deleted resources")
                return True
            else:
                logger.error(f"Delete failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error deleting resources: {e}")
            return False
            
    def get_status(self, kubectl_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get deployment status from Kubernetes.
        
        Args:
            kubectl_context: Kubernetes context to use
            
        Returns:
            Status dictionary
        """
        cmd = [
            "kubectl", "get", "all",
            "-n", self.config.namespace,
            "-l", f"app={self.config.name}",
            "-o", "json"
        ]
        
        if kubectl_context:
            cmd.extend(["--context", kubectl_context])
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                import json
                resources = json.loads(result.stdout)
                
                status = {
                    "deployment": "unknown",
                    "replicas": 0,
                    "ready_replicas": 0,
                    "pods": [],
                    "service": "unknown",
                }
                
                for item in resources.get("items", []):
                    kind = item.get("kind", "")
                    
                    if kind == "Deployment":
                        spec = item.get("spec", {})
                        status_info = item.get("status", {})
                        status["deployment"] = "ready" if status_info.get("readyReplicas", 0) > 0 else "not ready"
                        status["replicas"] = spec.get("replicas", 0)
                        status["ready_replicas"] = status_info.get("readyReplicas", 0)
                        
                    elif kind == "Pod":
                        pod_status = item.get("status", {})
                        status["pods"].append({
                            "name": item.get("metadata", {}).get("name", ""),
                            "phase": pod_status.get("phase", ""),
                            "ready": all(c.get("ready", False) for c in pod_status.get("containerStatuses", [])),
                        })
                        
                    elif kind == "Service":
                        status["service"] = "active"
                        
                return status
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}


# Kubernetes deployment presets
K8S_PRESETS = {
    "minimal": KubernetesConfig(
        name="agenticraft",
        namespace="default",
        replicas=1,
        cpu_request="100m",
        cpu_limit="500m",
        memory_request="256Mi",
        memory_limit="512Mi",
    ),
    "standard": KubernetesConfig(
        name="agenticraft",
        namespace="agenticraft",
        replicas=3,
        cpu_request="250m",
        cpu_limit="1000m",
        memory_request="512Mi",
        memory_limit="1Gi",
        service_type="LoadBalancer",
        ingress_enabled=True,
        ingress_host="agenticraft.example.com",
    ),
    "production": KubernetesConfig(
        name="agenticraft",
        namespace="agenticraft-prod",
        replicas=5,
        cpu_request="500m",
        cpu_limit="2000m",
        memory_request="1Gi",
        memory_limit="2Gi",
        service_type="ClusterIP",
        ingress_enabled=True,
        ingress_host="api.agenticraft.com",
        config_maps={
            "app": {
                "config.yaml": "production configuration here",
            }
        },
        secrets=["api_key", "database_password"],
        env_vars={
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "WARNING",
        }
    ),
}


# Helper function to generate Kubernetes files
def generate_k8s_files(preset: str = "standard", output_dir: str = "./k8s"):
    """Generate Kubernetes deployment files."""
    config = K8S_PRESETS.get(preset, K8S_PRESETS["standard"])
    deployer = KubernetesDeployer(config)
    deployer.save_manifests(output_dir)
    
    # Also generate a README
    readme_content = f"""# AgentiCraft Kubernetes Deployment

Generated on: {datetime.now().isoformat()}
Preset: {preset}

## Quick Start

1. Create namespace (if needed):
   ```bash
   kubectl create namespace {config.namespace}
   ```

2. Create secrets:
   ```bash
   kubectl create secret generic {config.name}-secrets \\
     --from-literal=api_key=YOUR_API_KEY \\
     --from-literal=database_password=YOUR_DB_PASSWORD \\
     -n {config.namespace}
   ```

3. Apply manifests:
   ```bash
   kubectl apply -k ./
   ```

4. Check status:
   ```bash
   kubectl get all -n {config.namespace} -l app={config.name}
   ```

## Configuration

- **Replicas**: {config.replicas}
- **CPU**: {config.cpu_request} - {config.cpu_limit}
- **Memory**: {config.memory_request} - {config.memory_limit}
- **Service Type**: {config.service_type}
- **Ingress**: {"Enabled" if config.ingress_enabled else "Disabled"}

## Monitoring

Access metrics at: http://<service-ip>:9090/metrics

## Scaling

Manual scaling:
```bash
kubectl scale deployment/{config.name}-deployment --replicas=10 -n {config.namespace}
```

The HPA will automatically scale between 1-10 replicas based on CPU usage.
"""
    
    output_path = Path(output_dir)
    with open(output_path / "README.md", "w") as f:
        f.write(readme_content)
        
    logger.info(f"Generated Kubernetes files in {output_path}")
