"""
Cloud deployment utilities for AgentiCraft.
"""

import os
import json
import yaml
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud providers."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    DIGITALOCEAN = "digitalocean"


@dataclass
class CloudConfig:
    """Cloud deployment configuration."""
    provider: CloudProvider
    project_name: str
    region: str
    instance_type: str = ""  # Provider-specific
    min_instances: int = 1
    max_instances: int = 10
    environment: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    enable_https: bool = True
    domain: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


class CloudDeployer:
    """Deploy AgentiCraft to various cloud providers."""
    
    def __init__(self, config: CloudConfig):
        """
        Initialize cloud deployer.
        
        Args:
            config: Cloud deployment configuration
        """
        self.config = config
        self.deployer = self._get_provider_deployer()
        
    def _get_provider_deployer(self):
        """Get appropriate deployer for cloud provider."""
        if self.config.provider == CloudProvider.AWS:
            return AWSDeployer(self.config)
        elif self.config.provider == CloudProvider.GCP:
            return GCPDeployer(self.config)
        elif self.config.provider == CloudProvider.AZURE:
            return AzureDeployer(self.config)
        elif self.config.provider == CloudProvider.DIGITALOCEAN:
            return DigitalOceanDeployer(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
            
    def deploy(self) -> bool:
        """Deploy to cloud provider."""
        return self.deployer.deploy()
        
    def destroy(self) -> bool:
        """Destroy cloud resources."""
        return self.deployer.destroy()
        
    def get_status(self) -> Dict[str, Any]:
        """Get deployment status."""
        return self.deployer.get_status()
        
    def get_logs(self, lines: int = 100) -> str:
        """Get application logs."""
        return self.deployer.get_logs(lines)


class AWSDeployer:
    """Deploy to AWS using various services."""
    
    def __init__(self, config: CloudConfig):
        """Initialize AWS deployer."""
        self.config = config
        # Set defaults for AWS
        if not self.config.instance_type:
            self.config.instance_type = "t3.medium"
            
    def generate_cloudformation_template(self) -> Dict[str, Any]:
        """Generate CloudFormation template for ECS Fargate deployment."""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"AgentiCraft deployment for {self.config.project_name}",
            "Parameters": {
                "ImageUri": {
                    "Type": "String",
                    "Description": "Docker image URI",
                    "Default": "agenticraft:latest",
                }
            },
            "Resources": {
                # VPC Configuration
                "VPC": {
                    "Type": "AWS::EC2::VPC",
                    "Properties": {
                        "CidrBlock": "10.0.0.0/16",
                        "EnableDnsSupport": True,
                        "EnableDnsHostnames": True,
                        "Tags": [
                            {
                                "Key": "Name",
                                "Value": f"{self.config.project_name}-vpc"
                            }
                        ]
                    }
                },
                # ECS Cluster
                "ECSCluster": {
                    "Type": "AWS::ECS::Cluster",
                    "Properties": {
                        "ClusterName": f"{self.config.project_name}-cluster",
                        "CapacityProviders": ["FARGATE", "FARGATE_SPOT"],
                        "DefaultCapacityProviderStrategy": [
                            {
                                "CapacityProvider": "FARGATE_SPOT",
                                "Weight": 2,
                            },
                            {
                                "CapacityProvider": "FARGATE",
                                "Weight": 1,
                            }
                        ]
                    }
                },
                # Task Definition
                "TaskDefinition": {
                    "Type": "AWS::ECS::TaskDefinition",
                    "Properties": {
                        "Family": f"{self.config.project_name}-task",
                        "NetworkMode": "awsvpc",
                        "RequiresCompatibilities": ["FARGATE"],
                        "Cpu": "1024",
                        "Memory": "2048",
                        "TaskRoleArn": {"Ref": "TaskRole"},
                        "ExecutionRoleArn": {"Ref": "ExecutionRole"},
                        "ContainerDefinitions": [{
                            "Name": "agenticraft",
                            "Image": {"Ref": "ImageUri"},
                            "PortMappings": [
                                {
                                    "ContainerPort": 8000,
                                    "Protocol": "tcp"
                                },
                                {
                                    "ContainerPort": 9090,
                                    "Protocol": "tcp"
                                }
                            ],
                            "Environment": [
                                {
                                    "Name": key,
                                    "Value": value
                                } for key, value in self.config.environment.items()
                            ],
                            "Secrets": [
                                {
                                    "Name": secret,
                                    "ValueFrom": f"arn:aws:secretsmanager:{self.config.region}:{{AWS::AccountId}}:secret:{self.config.project_name}-{secret}"
                                } for secret in self.config.secrets
                            ],
                            "LogConfiguration": {
                                "LogDriver": "awslogs",
                                "Options": {
                                    "awslogs-group": {"Ref": "LogGroup"},
                                    "awslogs-region": self.config.region,
                                    "awslogs-stream-prefix": "agenticraft",
                                }
                            },
                            "HealthCheck": {
                                "Command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                                "Interval": 30,
                                "Timeout": 5,
                                "Retries": 3,
                                "StartPeriod": 60,
                            }
                        }]
                    }
                },
                # ECS Service
                "ECSService": {
                    "Type": "AWS::ECS::Service",
                    "DependsOn": ["ALBListener"],
                    "Properties": {
                        "ServiceName": f"{self.config.project_name}-service",
                        "Cluster": {"Ref": "ECSCluster"},
                        "TaskDefinition": {"Ref": "TaskDefinition"},
                        "DesiredCount": self.config.min_instances,
                        "LaunchType": "FARGATE",
                        "NetworkConfiguration": {
                            "AwsvpcConfiguration": {
                                "Subnets": [{"Ref": "PrivateSubnet1"}, {"Ref": "PrivateSubnet2"}],
                                "SecurityGroups": [{"Ref": "ServiceSecurityGroup"}],
                                "AssignPublicIp": "DISABLED",
                            }
                        },
                        "LoadBalancers": [{
                            "TargetGroupArn": {"Ref": "TargetGroup"},
                            "ContainerName": "agenticraft",
                            "ContainerPort": 8000,
                        }],
                        "HealthCheckGracePeriodSeconds": 60,
                    }
                },
                # Auto Scaling
                "ServiceScalingTarget": {
                    "Type": "AWS::ApplicationAutoScaling::ScalableTarget",
                    "Properties": {
                        "MaxCapacity": self.config.max_instances,
                        "MinCapacity": self.config.min_instances,
                        "ResourceId": {
                            "Fn::Join": [
                                "/",
                                [
                                    "service",
                                    {"Ref": "ECSCluster"},
                                    {"Fn::GetAtt": ["ECSService", "Name"]}
                                ]
                            ]
                        },
                        "RoleARN": {"Fn::Sub": "arn:aws:iam::${AWS::AccountId}:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService"},
                        "ScalableDimension": "ecs:service:DesiredCount",
                        "ServiceNamespace": "ecs",
                    }
                },
                # CloudWatch Log Group
                "LogGroup": {
                    "Type": "AWS::Logs::LogGroup",
                    "Properties": {
                        "LogGroupName": f"/ecs/{self.config.project_name}",
                        "RetentionInDays": 30,
                    }
                },
                # IAM Roles
                "TaskRole": {
                    "Type": "AWS::IAM::Role",
                    "Properties": {
                        "AssumeRolePolicyDocument": {
                            "Statement": [{
                                "Effect": "Allow",
                                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                                "Action": "sts:AssumeRole",
                            }]
                        },
                        "ManagedPolicyArns": [
                            "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
                        ],
                    }
                },
                "ExecutionRole": {
                    "Type": "AWS::IAM::Role",
                    "Properties": {
                        "AssumeRolePolicyDocument": {
                            "Statement": [{
                                "Effect": "Allow",
                                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                                "Action": "sts:AssumeRole",
                            }]
                        },
                        "ManagedPolicyArns": [
                            "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
                        ],
                    }
                },
            },
            "Outputs": {
                "LoadBalancerUrl": {
                    "Description": "URL of the load balancer",
                    "Value": {"Fn::GetAtt": ["ALB", "DNSName"]},
                    "Export": {"Name": f"{self.config.project_name}-alb-url"},
                }
            }
        }
        
        return template
        
    def generate_terraform_config(self) -> str:
        """Generate Terraform configuration for AWS deployment."""
        terraform = f"""# AgentiCraft AWS Deployment
# Generated on {datetime.now().isoformat()}

terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{self.config.region}"
  
  default_tags {{
    tags = {{
      Project     = "{self.config.project_name}"
      ManagedBy   = "Terraform"
      Environment = "{self.config.environment.get('ENVIRONMENT', 'production')}"
    }}
  }}
}}

# ECR Repository
resource "aws_ecr_repository" "agenticraft" {{
  name                 = "{self.config.project_name}"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {{
    scan_on_push = true
  }}
}}

# ECS Cluster
resource "aws_ecs_cluster" "main" {{
  name = "{self.config.project_name}-cluster"
  
  setting {{
    name  = "containerInsights"
    value = "enabled"
  }}
}}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {{
  family                   = "{self.config.project_name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn
  
  container_definitions = jsonencode([{{
    name  = "agenticraft"
    image = "${{aws_ecr_repository.agenticraft.repository_url}}:latest"
    
    portMappings = [
      {{
        containerPort = 8000
        protocol      = "tcp"
      }},
      {{
        containerPort = 9090
        protocol      = "tcp"
      }}
    ]
    
    environment = [
      for k, v in {{
        ENVIRONMENT = "{self.config.environment.get('ENVIRONMENT', 'production')}"
      }} : {{
        name  = k
        value = v
      }}
    ]
    
    logConfiguration = {{
      logDriver = "awslogs"
      options = {{
        "awslogs-group"         = aws_cloudwatch_log_group.app.name
        "awslogs-region"        = "{self.config.region}"
        "awslogs-stream-prefix" = "ecs"
      }}
    }}
    
    healthCheck = {{
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }}
  }}])
}}

# ECS Service
resource "aws_ecs_service" "app" {{
  name            = "{self.config.project_name}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = {self.config.min_instances}
  launch_type     = "FARGATE"
  
  network_configuration {{
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = false
  }}
  
  load_balancer {{
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "agenticraft"
    container_port   = 8000
  }}
  
  depends_on = [aws_lb_listener.app]
}}

# Auto Scaling
resource "aws_appautoscaling_target" "ecs_target" {{
  max_capacity       = {self.config.max_instances}
  min_capacity       = {self.config.min_instances}
  resource_id        = "service/${{aws_ecs_cluster.main.name}}/${{aws_ecs_service.app.name}}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}}

resource "aws_appautoscaling_policy" "ecs_policy_cpu" {{
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  
  target_tracking_scaling_policy_configuration {{
    predefined_metric_specification {{
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }}
    target_value = 70.0
  }}
}}
"""
        return terraform
        
    def deploy(self) -> bool:
        """Deploy to AWS."""
        # This would typically:
        # 1. Build and push Docker image to ECR
        # 2. Deploy CloudFormation stack or run Terraform
        # 3. Configure Route53 if domain is specified
        
        logger.info(f"Deploying to AWS in region {self.config.region}")
        
        # For now, just save the templates
        output_dir = Path("./aws-deployment")
        output_dir.mkdir(exist_ok=True)
        
        # Save CloudFormation template
        cf_template = self.generate_cloudformation_template()
        with open(output_dir / "cloudformation.yaml", "w") as f:
            yaml.dump(cf_template, f, default_flow_style=False)
            
        # Save Terraform config
        tf_config = self.generate_terraform_config()
        with open(output_dir / "main.tf", "w") as f:
            f.write(tf_config)
            
        # Generate deployment script
        deploy_script = f"""#!/bin/bash
# AWS Deployment Script for {self.config.project_name}

set -e

echo "Building Docker image..."
docker build -t {self.config.project_name}:latest .

echo "Logging into ECR..."
aws ecr get-login-password --region {self.config.region} | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.{self.config.region}.amazonaws.com

echo "Tagging image..."
docker tag {self.config.project_name}:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.{self.config.region}.amazonaws.com/{self.config.project_name}:latest

echo "Pushing image to ECR..."
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.{self.config.region}.amazonaws.com/{self.config.project_name}:latest

echo "Deploying with Terraform..."
terraform init
terraform plan -out=tfplan
terraform apply tfplan

echo "Deployment complete!"
"""
        
        with open(output_dir / "deploy.sh", "w") as f:
            f.write(deploy_script)
            
        os.chmod(output_dir / "deploy.sh", 0o755)
        
        logger.info(f"AWS deployment files generated in {output_dir}")
        return True
        
    def destroy(self) -> bool:
        """Destroy AWS resources."""
        logger.info("Destroying AWS resources")
        # Would run: terraform destroy or delete CloudFormation stack
        return True
        
    def get_status(self) -> Dict[str, Any]:
        """Get deployment status from AWS."""
        # Would query ECS service status
        return {
            "provider": "AWS",
            "region": self.config.region,
            "status": "unknown",
            "message": "Status check not implemented",
        }
        
    def get_logs(self, lines: int = 100) -> str:
        """Get logs from CloudWatch."""
        # Would query CloudWatch logs
        return "AWS logs not implemented"


class GCPDeployer:
    """Deploy to Google Cloud Platform."""
    
    def __init__(self, config: CloudConfig):
        """Initialize GCP deployer."""
        self.config = config
        # Set defaults for GCP
        if not self.config.instance_type:
            self.config.instance_type = "n1-standard-1"
            
    def generate_app_yaml(self) -> str:
        """Generate app.yaml for Google App Engine."""
        return f"""runtime: python39
service: {self.config.project_name}

automatic_scaling:
  min_instances: {self.config.min_instances}
  max_instances: {self.config.max_instances}
  target_cpu_utilization: 0.7
  target_throughput_utilization: 0.7

instance_class: F4

env_variables:
  AGENTICRAFT_ENV: "gcp"
{chr(10).join(f'  {k}: "{v}"' for k, v in self.config.environment.items())}

handlers:
- url: /.*
  script: auto
  secure: always

readiness_check:
  path: "/health"
  check_interval_sec: 30
  timeout_sec: 10
  failure_threshold: 3
  success_threshold: 1

liveness_check:
  path: "/health"
  check_interval_sec: 30
  timeout_sec: 10
  failure_threshold: 3
  success_threshold: 1
"""
        
    def generate_cloud_run_config(self) -> str:
        """Generate configuration for Cloud Run deployment."""
        # Build the environment variables part separately
        env_vars = []
        for k, v in self.config.environment.items():
            env_vars.append(f'    --set-env-vars {k}={v} \\')
        env_vars_str = chr(10).join(env_vars)
        
        return f"""# Cloud Run Deployment Script
gcloud run deploy {self.config.project_name} \\
    --image gcr.io/${{PROJECT_ID}}/{self.config.project_name}:latest \\
    --platform managed \\
    --region {self.config.region} \\
    --allow-unauthenticated \\
    --min-instances {self.config.min_instances} \\
    --max-instances {self.config.max_instances} \\
    --memory 2Gi \\
    --cpu 2 \\
    --timeout 300 \\
    --concurrency 100 \\
    --port 8000 \\
    --set-env-vars AGENTICRAFT_ENV=gcp \\
{env_vars_str if env_vars_str else ''}
"""
        
    def deploy(self) -> bool:
        """Deploy to GCP."""
        logger.info(f"Deploying to GCP in region {self.config.region}")
        
        output_dir = Path("./gcp-deployment")
        output_dir.mkdir(exist_ok=True)
        
        # Save App Engine config
        with open(output_dir / "app.yaml", "w") as f:
            f.write(self.generate_app_yaml())
            
        # Save Cloud Run script
        with open(output_dir / "deploy-cloud-run.sh", "w") as f:
            f.write(self.generate_cloud_run_config())
            
        os.chmod(output_dir / "deploy-cloud-run.sh", 0o755)
        
        logger.info(f"GCP deployment files generated in {output_dir}")
        return True
        
    def destroy(self) -> bool:
        """Destroy GCP resources."""
        return True
        
    def get_status(self) -> Dict[str, Any]:
        """Get deployment status from GCP."""
        return {
            "provider": "GCP",
            "region": self.config.region,
            "status": "unknown",
        }
        
    def get_logs(self, lines: int = 100) -> str:
        """Get logs from Cloud Logging."""
        return "GCP logs not implemented"


class AzureDeployer:
    """Deploy to Microsoft Azure."""
    
    def __init__(self, config: CloudConfig):
        """Initialize Azure deployer."""
        self.config = config
        if not self.config.instance_type:
            self.config.instance_type = "B2s"
            
    def generate_azure_deploy_json(self) -> Dict[str, Any]:
        """Generate Azure Resource Manager template."""
        return {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "containerGroupName": {
                    "type": "string",
                    "defaultValue": self.config.project_name,
                }
            },
            "resources": [{
                "type": "Microsoft.ContainerInstance/containerGroups",
                "apiVersion": "2021-09-01",
                "name": "[parameters('containerGroupName')]",
                "location": self.config.region,
                "properties": {
                    "containers": [{
                        "name": "agenticraft",
                        "properties": {
                            "image": f"{self.config.project_name}:latest",
                            "ports": [
                                {"port": 8000, "protocol": "TCP"},
                                {"port": 9090, "protocol": "TCP"},
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": 1.0,
                                    "memoryInGB": 2.0,
                                }
                            },
                            "environmentVariables": [
                                {"name": k, "value": v}
                                for k, v in self.config.environment.items()
                            ],
                        }
                    }],
                    "osType": "Linux",
                    "ipAddress": {
                        "type": "Public",
                        "ports": [
                            {"port": 8000, "protocol": "TCP"},
                            {"port": 9090, "protocol": "TCP"},
                        ]
                    },
                    "restartPolicy": "OnFailure",
                }
            }]
        }
        
    def deploy(self) -> bool:
        """Deploy to Azure."""
        logger.info(f"Deploying to Azure in region {self.config.region}")
        
        output_dir = Path("./azure-deployment")
        output_dir.mkdir(exist_ok=True)
        
        # Save ARM template
        with open(output_dir / "azuredeploy.json", "w") as f:
            json.dump(self.generate_azure_deploy_json(), f, indent=2)
            
        logger.info(f"Azure deployment files generated in {output_dir}")
        return True
        
    def destroy(self) -> bool:
        """Destroy Azure resources."""
        return True
        
    def get_status(self) -> Dict[str, Any]:
        """Get deployment status from Azure."""
        return {
            "provider": "Azure",
            "region": self.config.region,
            "status": "unknown",
        }
        
    def get_logs(self, lines: int = 100) -> str:
        """Get logs from Azure Monitor."""
        return "Azure logs not implemented"


class DigitalOceanDeployer:
    """Deploy to DigitalOcean."""
    
    def __init__(self, config: CloudConfig):
        """Initialize DigitalOcean deployer."""
        self.config = config
        if not self.config.instance_type:
            self.config.instance_type = "s-2vcpu-4gb"
            
    def generate_app_spec(self) -> Dict[str, Any]:
        """Generate App Platform spec."""
        return {
            "name": self.config.project_name,
            "region": self.config.region,
            "services": [{
                "name": "agenticraft",
                "image": {
                    "registry_type": "DOCR",
                    "repository": self.config.project_name,
                    "tag": "latest",
                },
                "instance_count": self.config.min_instances,
                "instance_size_slug": self.config.instance_type,
                "http_port": 8000,
                "health_check": {
                    "http_path": "/health",
                    "initial_delay_seconds": 30,
                    "period_seconds": 30,
                    "timeout_seconds": 10,
                    "success_threshold": 1,
                    "failure_threshold": 3,
                },
                "envs": [
                    {"key": k, "value": v, "type": "GENERAL"}
                    for k, v in self.config.environment.items()
                ],
            }],
        }
        
    def deploy(self) -> bool:
        """Deploy to DigitalOcean."""
        logger.info(f"Deploying to DigitalOcean in region {self.config.region}")
        
        output_dir = Path("./do-deployment")
        output_dir.mkdir(exist_ok=True)
        
        # Save app spec
        with open(output_dir / "app.yaml", "w") as f:
            yaml.dump(self.generate_app_spec(), f, default_flow_style=False)
            
        logger.info(f"DigitalOcean deployment files generated in {output_dir}")
        return True
        
    def destroy(self) -> bool:
        """Destroy DigitalOcean resources."""
        return True
        
    def get_status(self) -> Dict[str, Any]:
        """Get deployment status from DigitalOcean."""
        return {
            "provider": "DigitalOcean",
            "region": self.config.region,
            "status": "unknown",
        }
        
    def get_logs(self, lines: int = 100) -> str:
        """Get logs from DigitalOcean."""
        return "DigitalOcean logs not implemented"


# Helper function to generate cloud deployment files
def generate_cloud_deployment_files(provider: str = "aws", output_dir: str = "./cloud-deployment"):
    """Generate deployment files for specified cloud provider."""
    configs = {
        "aws": CloudConfig(
            provider=CloudProvider.AWS,
            project_name="agenticraft",
            region="us-east-1",
            instance_type="t3.medium",
        ),
        "gcp": CloudConfig(
            provider=CloudProvider.GCP,
            project_name="agenticraft",
            region="us-central1",
        ),
        "azure": CloudConfig(
            provider=CloudProvider.AZURE,
            project_name="agenticraft",
            region="eastus",
        ),
        "digitalocean": CloudConfig(
            provider=CloudProvider.DIGITALOCEAN,
            project_name="agenticraft",
            region="nyc3",
        ),
    }
    
    config = configs.get(provider.lower())
    if not config:
        raise ValueError(f"Unsupported provider: {provider}")
        
    deployer = CloudDeployer(config)
    deployer.deploy()
    
    logger.info(f"Generated {provider} deployment files")
