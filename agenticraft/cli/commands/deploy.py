"""
Deploy command for AgentiCraft CLI.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from agenticraft.production.deploy import DockerDeployer, KubernetesDeployer, CloudDeployer
from agenticraft.production.deploy.docker import DockerConfig, DOCKER_PRESETS, generate_docker_files
from agenticraft.production.deploy.kubernetes import KubernetesConfig, K8S_PRESETS, generate_k8s_files
from agenticraft.production.deploy.cloud import CloudProvider, CloudConfig, generate_cloud_deployment_files


@click.group()
def deploy():
    """Deploy AgentiCraft applications to various platforms."""
    pass


@deploy.command()
@click.option("--preset", type=click.Choice(["minimal", "standard", "production"]), default="standard", help="Deployment preset")
@click.option("--image", default="agenticraft", help="Docker image name")
@click.option("--tag", default="latest", help="Docker image tag")
@click.option("--registry", help="Docker registry URL")
@click.option("--build/--no-build", default=True, help="Build image before deploying")
@click.option("--push/--no-push", default=False, help="Push image to registry")
@click.option("--output-dir", default="./docker-deployment", help="Output directory for generated files")
def docker(preset: str, image: str, tag: str, registry: Optional[str], build: bool, push: bool, output_dir: str):
    """Deploy using Docker."""
    click.echo(f"🐳 Deploying with Docker (preset: {preset})")
    
    # Generate Docker files
    generate_docker_files(output_dir)
    
    # Get preset config
    config = DOCKER_PRESETS[preset]
    config.image_name = image
    config.tag = tag
    if registry:
        config.registry = registry
        
    deployer = DockerDeployer(config)
    
    # Build image
    if build:
        click.echo("Building Docker image...")
        if deployer.build():
            click.echo("✅ Image built successfully")
        else:
            click.echo("❌ Failed to build image", err=True)
            sys.exit(1)
            
    # Push to registry
    if push:
        if not registry:
            click.echo("❌ Registry required for push", err=True)
            sys.exit(1)
            
        click.echo(f"Pushing image to {registry}...")
        if deployer.push():
            click.echo("✅ Image pushed successfully")
        else:
            click.echo("❌ Failed to push image", err=True)
            sys.exit(1)
            
    # Run container
    click.echo("Starting container...")
    container_id = deployer.run()
    if container_id:
        click.echo(f"✅ Container started: {container_id[:12]}")
        
        # Show health status
        health = deployer.health_check()
        click.echo(f"Health: {health}")
    else:
        click.echo("❌ Failed to start container", err=True)
        sys.exit(1)
        
    click.echo(f"\n📁 Deployment files saved to: {output_dir}")
    click.echo("📖 See docker-compose.yml for full stack deployment")


@deploy.command()
@click.option("--preset", type=click.Choice(["minimal", "standard", "production"]), default="standard", help="Deployment preset")
@click.option("--name", default="agenticraft", help="Application name")
@click.option("--namespace", default="agenticraft", help="Kubernetes namespace")
@click.option("--replicas", type=int, help="Number of replicas")
@click.option("--output-dir", default="./k8s", help="Output directory for manifests")
@click.option("--apply/--no-apply", default=False, help="Apply manifests to cluster")
@click.option("--context", help="Kubernetes context to use")
def kubernetes(preset: str, name: str, namespace: str, replicas: Optional[int], output_dir: str, apply: bool, context: Optional[str]):
    """Deploy to Kubernetes."""
    click.echo(f"☸️  Deploying to Kubernetes (preset: {preset})")
    
    # Generate K8s files
    generate_k8s_files(preset, output_dir)
    
    # Get preset config
    config = K8S_PRESETS[preset]
    config.name = name
    config.namespace = namespace
    if replicas:
        config.replicas = replicas
        
    deployer = KubernetesDeployer(config)
    
    # Save manifests
    deployer.save_manifests(output_dir)
    click.echo(f"✅ Manifests generated in {output_dir}")
    
    # Apply to cluster
    if apply:
        click.echo("Applying manifests to cluster...")
        if deployer.apply(kubectl_context=context):
            click.echo("✅ Manifests applied successfully")
            
            # Show status
            status = deployer.get_status(kubectl_context=context)
            click.echo(f"\nDeployment status:")
            click.echo(f"  Deployment: {status.get('deployment', 'unknown')}")
            click.echo(f"  Replicas: {status.get('ready_replicas', 0)}/{status.get('replicas', 0)}")
            click.echo(f"  Service: {status.get('service', 'unknown')}")
        else:
            click.echo("❌ Failed to apply manifests", err=True)
            sys.exit(1)
    else:
        click.echo("\nTo apply manifests:")
        click.echo(f"  kubectl apply -k {output_dir}")


@deploy.command()
@click.option("--provider", type=click.Choice(["aws", "gcp", "azure", "digitalocean"]), required=True, help="Cloud provider")
@click.option("--project", required=True, help="Project name")
@click.option("--region", required=True, help="Deployment region")
@click.option("--instance-type", help="Instance type (provider-specific)")
@click.option("--min-instances", type=int, default=1, help="Minimum instances")
@click.option("--max-instances", type=int, default=10, help="Maximum instances")
@click.option("--domain", help="Custom domain")
@click.option("--output-dir", help="Output directory for deployment files")
def cloud(provider: str, project: str, region: str, instance_type: Optional[str], 
         min_instances: int, max_instances: int, domain: Optional[str], output_dir: Optional[str]):
    """Deploy to cloud providers."""
    click.echo(f"☁️  Deploying to {provider.upper()}")
    
    # Set output directory
    if not output_dir:
        output_dir = f"./{provider}-deployment"
        
    # Generate deployment files
    generate_cloud_deployment_files(provider, output_dir)
    
    click.echo(f"✅ Deployment files generated in {output_dir}")
    
    # Provider-specific instructions
    if provider == "aws":
        click.echo("\nNext steps for AWS:")
        click.echo("  1. Configure AWS credentials: aws configure")
        click.echo(f"  2. Deploy: cd {output_dir} && ./deploy.sh")
        click.echo("  3. Or use Terraform: terraform init && terraform apply")
        
    elif provider == "gcp":
        click.echo("\nNext steps for GCP:")
        click.echo("  1. Configure GCP: gcloud auth login")
        click.echo("  2. Set project: gcloud config set project YOUR_PROJECT")
        click.echo(f"  3. Deploy to App Engine: cd {output_dir} && gcloud app deploy")
        click.echo(f"  4. Or Cloud Run: ./deploy-cloud-run.sh")
        
    elif provider == "azure":
        click.echo("\nNext steps for Azure:")
        click.echo("  1. Login: az login")
        click.echo("  2. Create resource group: az group create --name myResourceGroup --location eastus")
        click.echo(f"  3. Deploy: az deployment group create --resource-group myResourceGroup --template-file {output_dir}/azuredeploy.json")
        
    elif provider == "digitalocean":
        click.echo("\nNext steps for DigitalOcean:")
        click.echo("  1. Install doctl and authenticate")
        click.echo(f"  2. Create app: doctl apps create --spec {output_dir}/app.yaml")


@deploy.command()
@click.argument("deployment_type", type=click.Choice(["docker", "kubernetes", "cloud"]))
def status(deployment_type: str):
    """Check deployment status."""
    click.echo(f"Checking {deployment_type} deployment status...")
    
    if deployment_type == "docker":
        config = DockerConfig(image_name="agenticraft")
        deployer = DockerDeployer(config)
        health = deployer.health_check()
        
        if "error" in health:
            click.echo(f"❌ {health['error']}")
        else:
            click.echo(f"Status: {health.get('status', 'unknown')}")
            click.echo(f"Running: {health.get('running', False)}")
            click.echo(f"Health: {health.get('health', 'unknown')}")
            
    elif deployment_type == "kubernetes":
        config = KubernetesConfig(name="agenticraft")
        deployer = KubernetesDeployer(config)
        status = deployer.get_status()
        
        if "error" in status:
            click.echo(f"❌ {status['error']}")
        else:
            click.echo(f"Deployment: {status.get('deployment', 'unknown')}")
            click.echo(f"Replicas: {status.get('ready_replicas', 0)}/{status.get('replicas', 0)}")
            click.echo(f"Service: {status.get('service', 'unknown')}")
            
    else:
        click.echo("Cloud deployment status not implemented")


@deploy.command()
@click.argument("deployment_type", type=click.Choice(["docker", "kubernetes"]))
@click.option("--lines", type=int, default=100, help="Number of log lines")
def logs(deployment_type: str, lines: int):
    """View deployment logs."""
    click.echo(f"Fetching {deployment_type} logs...")
    
    if deployment_type == "docker":
        config = DockerConfig(image_name="agenticraft")
        deployer = DockerDeployer(config)
        logs = deployer.logs(lines=lines)
        
        if logs:
            click.echo(logs)
        else:
            click.echo("No logs available")
            
    else:
        click.echo("Kubernetes logs: kubectl logs -l app=agenticraft")


@deploy.command()
@click.option("--all", is_flag=True, help="Generate all deployment types")
@click.option("--docker", is_flag=True, help="Generate Docker files")
@click.option("--kubernetes", is_flag=True, help="Generate Kubernetes manifests")
@click.option("--cloud", type=click.Choice(["aws", "gcp", "azure", "digitalocean"]), help="Generate cloud deployment files")
def generate(all: bool, docker: bool, kubernetes: bool, cloud: Optional[str]):
    """Generate deployment files."""
    if all:
        docker = kubernetes = True
        cloud = "aws"  # Default to AWS for --all
        
    generated = []
    
    if docker:
        generate_docker_files()
        generated.append("Docker (./docker-deployment)")
        
    if kubernetes:
        generate_k8s_files()
        generated.append("Kubernetes (./k8s)")
        
    if cloud:
        generate_cloud_deployment_files(cloud)
        generated.append(f"{cloud.upper()} (./{cloud}-deployment)")
        
    if generated:
        click.echo("✅ Generated deployment files:")
        for item in generated:
            click.echo(f"  • {item}")
    else:
        click.echo("No deployment type specified. Use --docker, --kubernetes, or --cloud")
