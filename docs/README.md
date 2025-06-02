# AgentiCraft Documentation

Welcome to the AgentiCraft documentation!

## Quick Links

- [Quickstart Guide](quickstart.md) - Get started in 5 minutes
- [API Reference](https://docs.agenticraft.ai/api) - Detailed API documentation
- [Examples](https://github.com/agenticraft/agenticraft-examples) - Code examples

## Overview

AgentiCraft is an open-source framework for building production-ready AI agents. It provides:

- **Simple API** - Easy to use, hard to misuse
- **Extensible** - Plugin system for custom tools and capabilities
- **Production Ready** - Built-in monitoring, logging, and error handling
- **Multi-LLM Support** - Works with all major LLM providers

## Getting Started

```bash
pip install agenticraft
```

```python
from agenticraft import Agent

agent = Agent("MyAgent")
response = await agent.run("Hello, world!")
print(response)
```

## Learn More

Visit our [documentation site](https://docs.agenticraft.ai) for comprehensive guides and tutorials.
