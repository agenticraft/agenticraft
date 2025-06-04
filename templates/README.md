# AgentiCraft Templates

Production-ready templates for building applications with AgentiCraft.

## Available Templates

### 🚀 FastAPI Template

A full-featured REST API template with:
- Multiple agent types (Simple, Reasoning, Workflow)
- Production middleware (auth, rate limiting, CORS)
- Docker and Kubernetes deployment configs
- Monitoring with Prometheus and Grafana
- OpenTelemetry integration
- Comprehensive test suite

**Quick Start:**
```bash
agenticraft new my-api --template fastapi
cd my-api
docker-compose up
```

### 🖥️ CLI Template (Coming Soon)

Build command-line applications with agents:
- Interactive agent conversations
- Batch processing capabilities
- Configuration management
- Plugin support

### 🤖 Bot Template (Coming Soon)

Create bots for various platforms:
- Discord bot
- Slack bot
- Telegram bot
- Generic webhook bot

### 🌐 MCP Server Template (Coming Soon)

Standalone Model Context Protocol server:
- Tool registry
- WebSocket and HTTP transports
- Authentication
- Tool versioning

## Using Templates

### With AgentiCraft CLI

The easiest way to use templates is with the AgentiCraft CLI:

```bash
# Install AgentiCraft
pip install agenticraft

# Create a new project from template
agenticraft new my-project --template fastapi

# List available templates
agenticraft templates list
```

### Manual Usage

You can also copy templates manually:

```bash
# Copy the template
cp -r templates/fastapi my-project

# Install dependencies
cd my-project
pip install -r requirements.txt
```

## Template Structure

Each template follows a consistent structure:

```
template-name/
├── README.md           # Template documentation
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── docker/            # Docker configuration
├── tests/             # Test suite
└── src/ or app/       # Application code
```

## Creating Custom Templates

To create your own template:

1. Follow the structure above
2. Include comprehensive documentation
3. Add working examples
4. Include tests
5. Submit a PR to share with the community

## Best Practices

All templates follow these best practices:

1. **Production-Ready**: Include Docker, monitoring, and deployment configs
2. **Well-Documented**: Comprehensive README with examples
3. **Tested**: Include unit and integration tests
4. **Configurable**: Use environment variables for configuration
5. **Secure**: Include authentication and security best practices

## Contributing

We welcome new templates! Please ensure your template:
- Works out of the box
- Includes clear documentation
- Follows AgentiCraft best practices
- Has proper error handling
- Includes monitoring/observability

## License

All templates are part of the AgentiCraft project and licensed under Apache 2.0.
