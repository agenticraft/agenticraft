# AgentiCraft Kubernetes Templates

Production-ready Kubernetes templates for deploying AgentiCraft's CodeReviewPipeline workflow.

## Structure

```
kubernetes/
├── base/                    # Base configurations
│   ├── namespace.yaml      # AgentiCraft namespace
│   ├── configmap.yaml      # Configuration settings
│   ├── secrets.yaml        # Sensitive data (API keys, etc.)
│   ├── codereview-deployment.yaml   # Main API deployment
│   ├── webhook-deployment.yaml      # GitHub webhook receiver
│   ├── redis-deployment.yaml        # Redis cache
│   ├── hpa.yaml           # Autoscaling policies
│   ├── ingress.yaml       # External access
│   ├── rbac.yaml          # Permissions
│   ├── monitoring.yaml    # Prometheus monitoring
│   └── kustomization.yaml # Base kustomization
└── overlays/              # Environment-specific configurations
    ├── development/       # Dev environment
    │   ├── kustomization.yaml
    │   ├── deployment-patch.yaml
    │   └── configmap-patch.yaml
    └── production/        # Production environment
        ├── kustomization.yaml
        ├── deployment-patch.yaml
        └── ingress-patch.yaml
```

## Quick Start

### Prerequisites

1. Kubernetes cluster (1.19+)
2. kubectl configured
3. Kustomize (or kubectl with kustomize support)
4. (Optional) cert-manager for TLS certificates
5. (Optional) Prometheus operator for monitoring

### Deploy to Development

```bash
# Apply development configuration
kubectl apply -k overlays/development/

# Check deployment status
kubectl -n agenticraft-dev get pods
kubectl -n agenticraft-dev get svc
```

### Deploy to Production

```bash
# First, update secrets with real values
kubectl -n agenticraft create secret generic agenticraft-secrets \
  --from-literal=OPENAI_API_KEY=your-key \
  --from-literal=ANTHROPIC_API_KEY=your-key \
  --from-literal=GITHUB_WEBHOOK_SECRET=your-secret \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply production configuration
kubectl apply -k overlays/production/

# Check deployment
kubectl -n agenticraft get all
```

## Configuration

### Environment Variables

Key configuration options in `configmap.yaml`:

- `ENVIRONMENT`: Deployment environment (development/production)
- `LOG_LEVEL`: Logging verbosity (DEBUG/INFO/WARNING/ERROR)
- `MAX_CONCURRENT_WORKFLOWS`: Number of concurrent code reviews
- `GITHUB_WEBHOOK_SECRET`: Secret for validating GitHub webhooks
- `REDIS_HOST/PORT`: Redis cache connection

### Secrets

Required secrets in `secrets.yaml`:

- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude models
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `GITHUB_APP_PRIVATE_KEY`: GitHub App private key for API access

### Resource Limits

Default resource allocations:

| Component | Dev Memory | Dev CPU | Prod Memory | Prod CPU |
|-----------|------------|---------|-------------|----------|
| Code Review API | 256Mi-512Mi | 100m-500m | 1Gi-4Gi | 1000m-4000m |
| Webhook Receiver | 128Mi-256Mi | 50m-250m | 512Mi-1Gi | 500m-1000m |
| Redis | 256Mi-512Mi | 100m-250m | 256Mi-512Mi | 100m-250m |

## Autoscaling

Horizontal Pod Autoscaler (HPA) configurations:

- **Code Review API**: 2-10 replicas (prod), scales on CPU (70%) and memory (80%)
- **Webhook Receiver**: 2-5 replicas (prod), scales on CPU (80%) and memory (80%)

## Monitoring

ServiceMonitor and PodMonitor are included for Prometheus integration:

- Metrics endpoint: `/metrics`
- Scrape interval: 30 seconds
- Available metrics:
  - Request rate and latency
  - Workflow execution time
  - Agent coordination metrics
  - Error rates

## Security

- All containers run as non-root user (UID 1000)
- Service accounts with minimal RBAC permissions
- Network policies for pod-to-pod communication (optional)
- Secrets management via Kubernetes secrets

## Ingress

The template includes Ingress configuration for:

- `api.agenticraft.io` → Code Review API
- `webhooks.agenticraft.io/github` → GitHub webhook endpoint

Update the hostnames in `ingress.yaml` for your domain.

## Customization

### Adding a New Environment

1. Create a new overlay directory:
   ```bash
   mkdir -p overlays/staging
   ```

2. Create `kustomization.yaml`:
   ```yaml
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   
   namespace: agenticraft-staging
   
   bases:
     - ../../base
   
   namePrefix: staging-
   ```

3. Add environment-specific patches as needed

### Modifying Resources

Use Kustomize patches to modify base resources without editing them directly:

```yaml
# Example: Increase replicas
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agenticraft-codereview-api
spec:
  replicas: 5
```

## Troubleshooting

### Check Pod Logs
```bash
kubectl -n agenticraft logs -l app=agenticraft,component=codereview-api
```

### Debug Webhook Issues
```bash
kubectl -n agenticraft logs -l component=webhook-receiver
```

### Monitor Redis
```bash
kubectl -n agenticraft exec -it deploy/redis -- redis-cli ping
```

## Production Checklist

- [ ] Update all secrets with production values
- [ ] Configure proper domain names in Ingress
- [ ] Set up cert-manager for TLS certificates
- [ ] Configure backup strategy for Redis
- [ ] Set up monitoring and alerting
- [ ] Configure proper resource limits
- [ ] Enable network policies if required
- [ ] Set up proper logging aggregation

## Support

For issues or questions:
- Check the [AgentiCraft documentation](https://docs.agenticraft.io)
- Review the [hero workflow guide](https://docs.agenticraft.io/heroes/code-review)
- Open an issue on GitHub
