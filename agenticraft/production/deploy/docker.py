"""
Docker deployment utilities for AgentiCraft.
"""

import os
import json
import yaml
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DockerConfig:
    """Docker deployment configuration."""
    image_name: str
    tag: str = "latest"
    registry: Optional[str] = None
    build_args: Dict[str, str] = None
    environment: Dict[str, str] = None
    ports: Dict[int, int] = None  # container_port: host_port
    volumes: Dict[str, str] = None  # host_path: container_path
    network: str = "bridge"
    restart_policy: str = "unless-stopped"
    memory_limit: str = "2g"
    cpu_limit: float = 2.0


class DockerDeployer:
    """Deploy AgentiCraft applications using Docker."""
    
    def __init__(self, config: DockerConfig):
        """
        Initialize Docker deployer.
        
        Args:
            config: Docker deployment configuration
        """
        self.config = config
        self.full_image_name = self._get_full_image_name()
        
    def _get_full_image_name(self) -> str:
        """Get full image name including registry."""
        if self.config.registry:
            return f"{self.config.registry}/{self.config.image_name}:{self.config.tag}"
        return f"{self.config.image_name}:{self.config.tag}"
        
    def generate_dockerfile(self, base_image: str = "python:3.9-slim") -> str:
        """
        Generate Dockerfile for AgentiCraft application.
        
        Args:
            base_image: Base Docker image
            
        Returns:
            Dockerfile content
        """
        dockerfile = f"""# AgentiCraft Dockerfile
# Generated on {datetime.now().isoformat()}

FROM {base_image}

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install AgentiCraft
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 agenticraft && \\
    chown -R agenticraft:agenticraft /app

# Switch to non-root user
USER agenticraft

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["agenticraft", "run", "--host", "0.0.0.0", "--port", "8000"]
"""
        return dockerfile
        
    def generate_docker_compose(self, services: Dict[str, Any] = None) -> str:
        """
        Generate docker-compose.yml for AgentiCraft stack.
        
        Args:
            services: Additional services to include
            
        Returns:
            docker-compose.yml content
        """
        compose = {
            "version": "3.8",
            "services": {
                "agenticraft": {
                    "image": self.full_image_name,
                    "container_name": "agenticraft-app",
                    "restart": self.config.restart_policy,
                    "ports": [
                        f"{host}:{container}" 
                        for container, host in (self.config.ports or {}).items()
                    ] or ["8000:8000"],
                    "environment": self.config.environment or {},
                    "volumes": [
                        f"{host}:{container}"
                        for host, container in (self.config.volumes or {}).items()
                    ],
                    "networks": ["agenticraft"],
                    "depends_on": ["redis", "postgres"],
                    "deploy": {
                        "resources": {
                            "limits": {
                                "memory": self.config.memory_limit,
                                "cpus": str(self.config.cpu_limit),
                            }
                        }
                    }
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "container_name": "agenticraft-redis",
                    "restart": "unless-stopped",
                    "ports": ["6379:6379"],
                    "volumes": ["redis-data:/data"],
                    "networks": ["agenticraft"],
                },
                "postgres": {
                    "image": "postgres:15-alpine",
                    "container_name": "agenticraft-db",
                    "restart": "unless-stopped",
                    "ports": ["5432:5432"],
                    "environment": {
                        "POSTGRES_DB": "agenticraft",
                        "POSTGRES_USER": "agenticraft",
                        "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-changeme}",
                    },
                    "volumes": ["postgres-data:/var/lib/postgresql/data"],
                    "networks": ["agenticraft"],
                },
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "agenticraft-prometheus",
                    "restart": "unless-stopped",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "./prometheus.yml:/etc/prometheus/prometheus.yml",
                        "prometheus-data:/prometheus",
                    ],
                    "networks": ["agenticraft"],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                    ],
                },
            },
            "networks": {
                "agenticraft": {
                    "driver": "bridge",
                }
            },
            "volumes": {
                "redis-data": {},
                "postgres-data": {},
                "prometheus-data": {},
            }
        }
        
        # Add additional services
        if services:
            compose["services"].update(services)
            
        return yaml.dump(compose, default_flow_style=False)
        
    def build(self, dockerfile_path: str = "./Dockerfile", no_cache: bool = False) -> bool:
        """
        Build Docker image.
        
        Args:
            dockerfile_path: Path to Dockerfile
            no_cache: Whether to build without cache
            
        Returns:
            True if successful
        """
        cmd = ["docker", "build", "-t", self.full_image_name, "-f", dockerfile_path]
        
        # Add build args
        if self.config.build_args:
            for key, value in self.config.build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])
                
        if no_cache:
            cmd.append("--no-cache")
            
        cmd.append(".")
        
        logger.info(f"Building Docker image: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Successfully built image: {self.full_image_name}")
                return True
            else:
                logger.error(f"Build failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error building image: {e}")
            return False
            
    def push(self) -> bool:
        """
        Push Docker image to registry.
        
        Returns:
            True if successful
        """
        if not self.config.registry:
            logger.warning("No registry configured, skipping push")
            return True
            
        cmd = ["docker", "push", self.full_image_name]
        
        logger.info(f"Pushing image: {self.full_image_name}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Successfully pushed image")
                return True
            else:
                logger.error(f"Push failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error pushing image: {e}")
            return False
            
    def run(self, container_name: str = "agenticraft", detach: bool = True) -> Optional[str]:
        """
        Run Docker container.
        
        Args:
            container_name: Name for the container
            detach: Whether to run in detached mode
            
        Returns:
            Container ID if successful
        """
        cmd = ["docker", "run"]
        
        if detach:
            cmd.append("-d")
            
        cmd.extend(["--name", container_name])
        cmd.extend(["--restart", self.config.restart_policy])
        
        # Add ports
        if self.config.ports:
            for container_port, host_port in self.config.ports.items():
                cmd.extend(["-p", f"{host_port}:{container_port}"])
                
        # Add environment variables
        if self.config.environment:
            for key, value in self.config.environment.items():
                cmd.extend(["-e", f"{key}={value}"])
                
        # Add volumes
        if self.config.volumes:
            for host_path, container_path in self.config.volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])
                
        # Add resource limits
        cmd.extend(["--memory", self.config.memory_limit])
        cmd.extend(["--cpus", str(self.config.cpu_limit)])
        
        # Add network
        if self.config.network != "bridge":
            cmd.extend(["--network", self.config.network])
            
        cmd.append(self.full_image_name)
        
        logger.info(f"Running container: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                container_id = result.stdout.strip()
                logger.info(f"Started container: {container_id[:12]}")
                return container_id
            else:
                logger.error(f"Run failed: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error running container: {e}")
            return None
            
    def stop(self, container_name: str = "agenticraft") -> bool:
        """
        Stop Docker container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            True if successful
        """
        cmd = ["docker", "stop", container_name]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Stopped container: {container_name}")
                return True
            else:
                logger.error(f"Stop failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False
            
    def remove(self, container_name: str = "agenticraft") -> bool:
        """
        Remove Docker container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            True if successful
        """
        cmd = ["docker", "rm", "-f", container_name]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Removed container: {container_name}")
                return True
            else:
                logger.error(f"Remove failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error removing container: {e}")
            return False
            
    def logs(self, container_name: str = "agenticraft", lines: int = 100) -> Optional[str]:
        """
        Get container logs.
        
        Args:
            container_name: Name of the container
            lines: Number of lines to retrieve
            
        Returns:
            Logs or None
        """
        cmd = ["docker", "logs", "--tail", str(lines), container_name]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Logs failed: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return None
            
    def health_check(self, container_name: str = "agenticraft") -> Dict[str, Any]:
        """
        Check container health.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Health status dictionary
        """
        cmd = ["docker", "inspect", container_name]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info = json.loads(result.stdout)[0]
                
                health = {
                    "running": info["State"]["Running"],
                    "status": info["State"]["Status"],
                    "health": info.get("State", {}).get("Health", {}).get("Status", "none"),
                    "started_at": info["State"]["StartedAt"],
                    "restart_count": info["RestartCount"],
                }
                
                return health
            else:
                return {"error": "Container not found"}
        except Exception as e:
            return {"error": str(e)}
            
    def cleanup(self, remove_images: bool = False):
        """
        Clean up Docker resources.
        
        Args:
            remove_images: Whether to remove images as well
        """
        # Remove stopped containers
        subprocess.run(["docker", "container", "prune", "-f"], capture_output=True)
        
        # Remove unused networks
        subprocess.run(["docker", "network", "prune", "-f"], capture_output=True)
        
        # Remove unused volumes
        subprocess.run(["docker", "volume", "prune", "-f"], capture_output=True)
        
        if remove_images:
            # Remove unused images
            subprocess.run(["docker", "image", "prune", "-a", "-f"], capture_output=True)
            
        logger.info("Docker cleanup completed")


# Helper functions
def generate_docker_files(output_dir: str = "."):
    """Generate Docker files for AgentiCraft deployment."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate Dockerfile
    config = DockerConfig(image_name="agenticraft", tag="latest")
    deployer = DockerDeployer(config)
    
    dockerfile_content = deployer.generate_dockerfile()
    with open(output_path / "Dockerfile", "w") as f:
        f.write(dockerfile_content)
        
    # Generate docker-compose.yml
    compose_content = deployer.generate_docker_compose()
    with open(output_path / "docker-compose.yml", "w") as f:
        f.write(compose_content)
        
    # Generate .dockerignore
    dockerignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/

# Git
.git/
.gitignore

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
*.db
*.sqlite
.env
.env.*
!.env.example
secrets/
data/
temp/
"""
    
    with open(output_path / ".dockerignore", "w") as f:
        f.write(dockerignore_content)
        
    # Generate prometheus.yml
    prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agenticraft'
    static_configs:
      - targets: ['agenticraft:9090']
    metrics_path: '/metrics'
"""
    
    with open(output_path / "prometheus.yml", "w") as f:
        f.write(prometheus_config)
        
    logger.info(f"Generated Docker files in {output_path}")


# Docker deployment presets
DOCKER_PRESETS = {
    "minimal": DockerConfig(
        image_name="agenticraft",
        tag="latest",
        ports={8000: 8000},
        memory_limit="1g",
        cpu_limit=1.0,
    ),
    "standard": DockerConfig(
        image_name="agenticraft",
        tag="latest",
        ports={8000: 8000, 9090: 9090},
        memory_limit="2g",
        cpu_limit=2.0,
        volumes={
            "./data": "/app/data",
            "./logs": "/app/logs",
        }
    ),
    "production": DockerConfig(
        image_name="agenticraft",
        tag="latest",
        registry="registry.example.com",
        ports={8000: 8000, 9090: 9090},
        memory_limit="4g",
        cpu_limit=4.0,
        volumes={
            "/var/agenticraft/data": "/app/data",
            "/var/agenticraft/logs": "/app/logs",
            "/var/agenticraft/config": "/app/config",
        },
        environment={
            "AGENTICRAFT_ENV": "production",
            "LOG_LEVEL": "WARNING",
        }
    ),
}
