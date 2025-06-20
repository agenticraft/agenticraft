# AgentiCraft Quick Reference Guide

## 🚀 Installation & Setup

```bash
# Install AgentiCraft
pip install -e .

# Create new project
agenticraft new my-agent-project

# Run a hero workflow
agenticraft run research-team --query "AI trends 2025"
```

## 🎯 Hero Workflows

### 1. Research Team
```python
from agenticraft.workflows import ResearchTeam

# Basic usage
team = ResearchTeam(size=5)
report = await team.research("quantum computing applications")

# With memory
team = ResearchTeam(size=5, memory_enabled=True)
report = await team.research("continue our AI analysis")
```

### 2. Customer Service Desk
```python
from agenticraft.workflows import CustomerServiceDesk

desk = CustomerServiceDesk(
    enable_escalation=True,
    sentiment_analysis=True,
    knowledge_base_path="./kb"
)
response = await desk.handle_inquiry("How do I reset my password?")
```

### 3. Code Review Pipeline
```python
from agenticraft.workflows import CodeReviewPipeline

pipeline = CodeReviewPipeline(
    enable_security_scan=True,
    check_style=True,
    suggest_improvements=True
)
review = await pipeline.review_pull_request("https://github.com/org/repo/pull/123")
```

## 🤖 Specialized Agents

```python
from agenticraft.agents.specialized import (
    SEOSpecialist,
    DevOpsEngineer,
    ProjectManager,
    BusinessAnalyst,
    QATester
)

# SEO optimization
seo = SEOSpecialist()
report = await seo.analyze_content("Your blog post content here")

# DevOps automation  
devops = DevOpsEngineer()
deployment = await devops.deploy(config)

# Project planning
pm = ProjectManager()
plan = await pm.plan_project("Build mobile app")

# Business analysis
analyst = BusinessAnalyst()
analysis = await analyst.analyze_requirements("Customer needs...")

# QA testing
tester = QATester()
test_suite = await tester.generate_tests(code_module)
```

## 🎨 Visual Workflow Builder

```python
# Start visual builder
python -m agenticraft.tools.builder

# Or via CLI
agenticraft builder --port 8080
```

## 🧠 Memory System

```python
from agenticraft.memory import MemorySystem

# Enable memory for any workflow
workflow = YourWorkflow(memory_enabled=True)

# Direct memory usage
memory = MemorySystem()
await memory.store("key", data)
retrieved = await memory.retrieve("key")
```

## 🔧 Error Handling & Decorators

```python
from agenticraft.utils.decorators import retry, timeout, cache, rate_limit

@retry(attempts=3, backoff="exponential")
@timeout(seconds=30)
@cache(ttl=3600)
@rate_limit(calls=100, period="minute")
async def reliable_operation():
    # Your code here
    pass
```

## 📊 Production Monitoring

### Health Checks
```python
from agenticraft.production.health import WorkflowHealth

health = WorkflowHealth("research-team")
result = await health.check_workflow_health(workflow_instance)
```

### Metrics Export
```python
from agenticraft.production.metrics import PrometheusExporter

exporter = PrometheusExporter()
exporter.collect_workflow_metrics("research-team", metrics)
prometheus_text = exporter.format_metrics()
```

## 🚀 Deployment

### Docker
```bash
# Generate Docker files
agenticraft deploy generate --docker

# Build and run
agenticraft deploy docker --build --preset production
```

### Kubernetes
```bash
# Generate K8s manifests
agenticraft deploy generate --kubernetes

# Deploy to cluster
agenticraft deploy kubernetes --preset production --apply
```

### Cloud Providers
```bash
# AWS
agenticraft deploy cloud --provider aws --region us-east-1

# GCP
agenticraft deploy cloud --provider gcp --region us-central1

# Azure
agenticraft deploy cloud --provider azure --region eastus

# DigitalOcean
agenticraft deploy cloud --provider digitalocean --region nyc3
```

## 📈 CLI Commands

### Core Commands
```bash
agenticraft new <project>          # Create new project
agenticraft run <workflow>         # Run a workflow
agenticraft templates              # List available templates
agenticraft plugin <command>       # Manage plugins
```

### Deployment Commands
```bash
agenticraft deploy docker          # Docker deployment
agenticraft deploy kubernetes      # K8s deployment
agenticraft deploy cloud          # Cloud deployment
agenticraft deploy status         # Check deployment status
agenticraft deploy logs           # View logs
```

### Monitoring Commands
```bash
agenticraft monitor health        # Health check
agenticraft monitor metrics       # Export metrics
agenticraft monitor watch         # Continuous monitoring
agenticraft monitor inspect       # Detailed inspection
agenticraft monitor setup         # Set up monitoring
```

## 🔧 Configuration

### Config File (agenticraft.yaml)
```yaml
workflows:
  default_timeout: 300
  max_retries: 3

agents:
  max_concurrent_tasks: 10

system:
  log_level: INFO
  metrics_enabled: true

providers:
  default: openai
  openai:
    model: gpt-4
    temperature: 0.7
```

### Environment Variables
```bash
export AGENTICRAFT_ENV=production
export AGENTICRAFT_LOG_LEVEL=INFO
export AGENTICRAFT_API_KEY=your-key
```

### Secrets Management
```python
from agenticraft.production.config import SecretManager

secrets = SecretManager()
api_key = secrets.get("openai_api_key")
```

## 📚 Project Structure

```
my-agent-project/
├── agents/           # Custom agents
├── workflows/        # Custom workflows  
├── config/          # Configuration files
├── data/            # Data storage
├── logs/            # Application logs
├── .env             # Environment variables
├── agenticraft.yaml # Main config
└── requirements.txt # Dependencies
```

## 🎯 Common Patterns

### Custom Workflow
```python
from agenticraft import Workflow, Agent

class MyWorkflow(Workflow):
    def __init__(self):
        super().__init__("my-workflow")
        self.add_agent(MyAgent())
        
    async def execute(self, task):
        result = await self.agents["my-agent"].process(task)
        return result
```

### Custom Agent
```python
from agenticraft import Agent

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="my-agent",
            description="Custom agent",
            tools=["web_search", "calculator"]
        )
        
    async def process(self, task):
        # Agent logic here
        return result
```

## 🔗 Useful Links

- Documentation: `/docs`
- Examples: `/examples`
- API Reference: `/docs/api`
- Tutorials: `/docs/tutorials`

---

**Need help?** Check the full documentation or run `agenticraft --help`
