# AgentiCraft FastAPI Template

A production-ready FastAPI template for building AI agent APIs with AgentiCraft.

## 🚀 Features

- **Multiple Agent Types**: Simple, Reasoning, and Workflow agents
- **Production Middleware**: Authentication, rate limiting, CORS, request tracking
- **Observability**: Built-in health checks, metrics, and OpenTelemetry tracing
- **Docker Ready**: Multi-stage Dockerfile and docker-compose setup
- **Kubernetes Ready**: Full K8s manifests with ingress, configmaps, and secrets
- **Monitoring Stack**: Prometheus, Grafana, and OpenTelemetry Collector
- **Type Safety**: Full Pydantic models for requests/responses
- **Async First**: Built on FastAPI's async capabilities

## 📦 Quick Start

### Local Development

1. **Clone and setup:**
```bash
# Create a new project from template
agenticraft new my-api --template fastapi
cd my-api

# Copy environment variables
cp .env.example .env

# Edit .env with your API keys
```

2. **Install dependencies:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Run the application:**
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Or use the Python module
python -m app.main
```

4. **Access the API:**
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### Docker Deployment

1. **Build and run with Docker:**
```bash
# Build the image
docker build -f docker/Dockerfile -t agenticraft-api .

# Run the container
docker run -p 8000:8000 --env-file .env agenticraft-api
```

2. **Use Docker Compose for full stack:**
```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f api

# Stop services
docker-compose -f docker/docker-compose.yml down
```

Services included:
- **API**: The AgentiCraft FastAPI application
- **Redis**: For caching and rate limiting
- **PostgreSQL**: For persistent storage (optional)
- **OpenTelemetry Collector**: For trace collection
- **Prometheus**: For metrics storage
- **Grafana**: For visualization (http://localhost:3001)

### Kubernetes Deployment

1. **Create namespace:**
```bash
kubectl create namespace agenticraft
```

2. **Create secrets:**
```bash
# Edit k8s/secrets.yaml.example with your values
cp k8s/secrets.yaml.example k8s/secrets.yaml
kubectl apply -f k8s/secrets.yaml
```

3. **Deploy the application:**
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n agenticraft
kubectl get svc -n agenticraft
```

4. **Access the application:**
```bash
# Port forward for local access
kubectl port-forward -n agenticraft svc/agenticraft-api 8000:80

# Or use the NodePort
# http://your-node-ip:30080
```

## 🔧 Configuration

### Environment Variables

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `SERVICE_NAME` | Service identifier | `agenticraft-api` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `ENABLE_TELEMETRY` | Enable OpenTelemetry | `true` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `RATE_LIMIT_CALLS` | Rate limit calls | `100` |
| `RATE_LIMIT_PERIOD` | Rate limit period (seconds) | `60` |

See `.env.example` for the complete list.

### API Authentication

The template includes simple API key authentication. In production, consider:
- JWT tokens for user authentication
- OAuth2 for third-party integrations
- mTLS for service-to-service communication

Default demo API key: `demo-key-123`

Example request:
```bash
curl -H "X-API-Key: demo-key-123" http://localhost:8000/agents/simple \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?"}'
```

## 📚 API Endpoints

### Agent Endpoints

- `POST /agents/simple` - Simple conversational agent
- `POST /agents/reasoning` - Agent with reasoning traces
- `POST /agents/workflow` - Multi-step workflow execution
- `GET /agents` - List available agents
- `GET /agents/health` - Agent health status

### Monitoring Endpoints

- `GET /health` - Service health check
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe
- `GET /metrics` - Prometheus metrics
- `GET /info` - Service information

### Example Requests

**Simple Agent:**
```json
POST /agents/simple
{
  "prompt": "What's the weather in New York?",
  "context": {
    "user_id": "123",
    "session_id": "abc"
  }
}
```

**Reasoning Agent:**
```json
POST /agents/reasoning
{
  "prompt": "Plan a sustainable city",
  "options": {
    "max_steps": 5,
    "include_confidence": true
  }
}
```

**Workflow Agent:**
```json
POST /agents/workflow
{
  "prompt": "Research and write an article about AI safety",
  "options": {
    "workflow_config": {
      "steps": ["research", "outline", "write", "review"],
      "parallel": false
    }
  }
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_agents.py
```

## 📊 Monitoring

### Prometheus Metrics

The application exposes Prometheus metrics at `/metrics`:

- `agenticraft_requests_total` - Total requests by endpoint
- `agenticraft_request_duration_seconds` - Request duration histogram
- `agenticraft_active_agents` - Number of active agents
- `agenticraft_system_info` - System information

### OpenTelemetry Traces

Traces are automatically sent to the configured OTLP endpoint. View them in:
- Jaeger UI: http://localhost:16686
- Grafana Tempo
- Your preferred APM tool

### Grafana Dashboards

Pre-configured dashboards are available in `docker/grafana/dashboards/`:
- API Overview
- Agent Performance
- System Resources
- Error Analysis

## 🔒 Security Considerations

1. **API Keys**: Store securely, rotate regularly
2. **CORS**: Configure specific origins in production
3. **Rate Limiting**: Adjust limits based on your needs
4. **HTTPS**: Always use TLS in production
5. **Secrets**: Use Kubernetes secrets or cloud KMS
6. **Dependencies**: Keep updated with security patches

## 🚀 Production Checklist

- [ ] Set strong API keys and secrets
- [ ] Configure CORS for your domains
- [ ] Set appropriate rate limits
- [ ] Enable HTTPS with valid certificates
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Configure autoscaling policies
- [ ] Set up backup for persistent data
- [ ] Review and adjust resource limits
- [ ] Enable security scanning in CI/CD

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── agents/              # Agent endpoints
│   ├── middleware/          # Custom middleware
│   └── monitoring/          # Health and metrics
├── docker/
│   ├── Dockerfile           # Multi-stage build
│   └── docker-compose.yml   # Full stack setup
├── k8s/
│   ├── deployment.yaml      # Kubernetes deployment
│   ├── service.yaml         # Service definition
│   ├── ingress.yaml         # Ingress rules
│   ├── configmap.yaml       # Configuration
│   └── secrets.yaml.example # Secret template
├── tests/
│   ├── test_agents.py       # Agent tests
│   ├── test_middleware.py   # Middleware tests
│   └── test_monitoring.py   # Monitoring tests
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## 🤝 Contributing

This is a template - feel free to modify and extend it for your needs!

## 📄 License

This template is part of the AgentiCraft project and is licensed under the Apache 2.0 License.
