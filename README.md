<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/agenticraft/agenticraft/refs/heads/main/.github/main/assets/default-monochrome-white.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/agenticraft/agenticraft/refs/heads/main/.github/main/assets/default-monochrome-black.svg">
    <img alt="AgentiCraft" src="https://raw.githubusercontent.com/agenticraft/agenticraft/refs/heads/main/.github/main/assets/default-monochrome.svg" width="200">
  </picture>
  
  <!-- # AgentiCraft -->
  
  **Build production-ready AI agents with ease**
  
  [![PyPI version](https://badge.fury.io/py/agenticraft.svg)](https://pypi.org/project/agenticraft/)
  [![Python Version](https://img.shields.io/pypi/pyversions/agenticraft)](https://pypi.org/project/agenticraft/)
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
  [![CI](https://github.com/agenticraft/agenticraft/workflows/CI/badge.svg)](https://github.com/agenticraft/agenticraft/actions)
  [![codecov](https://codecov.io/gh/agenticraft/agenticraft/branch/main/graph/badge.svg)](https://codecov.io/gh/agenticraft/agenticraft)
  [![Discord](https://img.shields.io/discord/1234567890?color=7289da&label=Discord&logo=discord&logoColor=white)](https://discord.gg/agenticraft)
  [![Twitter Follow](https://img.shields.io/twitter/follow/agenticraft?style=social)](https://twitter.com/agenticraft)
</div>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-documentation">Docs</a> •
  <a href="#-examples">Examples</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-enterprise">Enterprise</a>
</p>

---

## ✨ Features

- 🏗️ **Modular Architecture** - Build agents with composable components
- 🔌 **Plugin System** - Extend functionality with custom tools and capabilities
- 🤖 **Multi-LLM Support** - Works with OpenAI, Anthropic, Ollama, and more
- 🛠️ **Rich Tool Ecosystem** - 20+ built-in tools, unlimited custom tools
- 🧠 **Advanced Memory Systems** - Short-term, long-term, and semantic memory
- 📊 **Production Ready** - Monitoring, logging, error handling, and rate limiting
- 🎨 **Developer Friendly** - Simple API, great documentation, type hints
- 🔒 **Secure by Default** - API authentication, rate limiting, audit logs

## 🚀 Quick Start

### Installation

```bash
pip install agenticraft
```

### Create Your First Agent

```python
from agenticraft import Agent, Tool

# Create an agent
agent = Agent(
    name="Assistant",
    model="gpt-4",  # or "claude-3", "llama2", etc.
    temperature=0.7
)

# Add tools
agent.add_tool(Tool.Calculator())
agent.add_tool(Tool.WebSearch())
agent.add_tool(Tool.FileReader())

# Run the agent
response = await agent.run("What's the weather in San Francisco?")
print(response)
```

### More Examples

```python
# Create a chatbot with memory
from agenticraft import ChatAgent

chatbot = ChatAgent("Helper", memory=True)
response = await chatbot.chat("My name is Alice")
response = await chatbot.chat("What's my name?")  # Remembers: "Alice"

# Create a custom tool
from agenticraft import Tool

@Tool.create("get_time")
async def get_current_time():
    """Get the current time"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

agent.add_tool(get_current_time)
```

## 📖 Documentation

- **[Getting Started](https://docs.agenticraft.ai/getting-started)** - Installation and first steps
- **[Core Concepts](https://docs.agenticraft.ai/concepts)** - Understand agents, tools, and memory
- **[API Reference](https://docs.agenticraft.ai/api)** - Detailed API documentation
- **[Examples](https://github.com/agenticraft/agenticraft-examples)** - Complete example projects
- **[Plugin Development](https://docs.agenticraft.ai/plugins)** - Create custom plugins

## 🎯 Use Cases

AgentiCraft is perfect for:

- 💬 **Conversational AI** - Chatbots, virtual assistants, customer support
- 🔍 **Research Assistants** - Information gathering, summarization, analysis
- 🛠️ **Task Automation** - Workflow automation, data processing, integrations
- 🎮 **Game AI** - NPCs, game masters, interactive storytelling
- 📊 **Data Analysis** - Data exploration, visualization, insights
- 🏢 **Enterprise Applications** - Internal tools, process automation, compliance

## 🗺️ Roadmap

- [x] Core agent framework
- [x] Tool system with 20+ built-in tools
- [x] Memory management (short-term, long-term)
- [x] Multi-LLM support
- [ ] Plugin marketplace (Coming soon)
- [ ] Visual workflow builder (Q2 2025)
- [ ] Multi-agent orchestration (Q2 2025)
- [ ] Enterprise features (Q3 2025)

## 🤝 Contributing

We love contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Clone the repository
git clone https://github.com/agenticraft/agenticraft.git
cd agenticraft

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
make lint
```

## 🏢 Enterprise Edition

Need advanced features for your organization?

**AgentiCraft Enterprise** includes:
- 🚀 Advanced reasoning agents (Tree of Thoughts, Graph of Thoughts)
- 👥 Multi-agent orchestration
- 🔐 Enterprise security (SSO, RBAC, audit logs)
- 📊 Advanced analytics and monitoring
- 🎯 Custom model fine-tuning
- 💼 Priority support and SLA
- 🏗️ On-premise deployment

[Learn more](https://agenticraft.ai/enterprise) or [contact sales](mailto:enterprise@agenticraft.ai).

## 📄 License

AgentiCraft is Apache 2.0 licensed. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with inspiration from:
- [LangChain](https://github.com/langchain-ai/langchain) - Pioneering the space
- [AutoGen](https://github.com/microsoft/autogen) - Multi-agent conversations
- [CrewAI](https://github.com/joaomdmoura/crewai) - Agent orchestration

---

<div align="center">
  <strong>⭐ Star us on GitHub to support the project!</strong>
  
  <p>
    <a href="https://agenticraft.ai">Website</a> •
    <a href="https://docs.agenticraft.ai">Documentation</a> •
    <a href="https://discord.gg/agenticraft">Discord</a> •
    <a href="https://twitter.com/agenticraft">Twitter</a>
  </p>
  
  <sub>Built with ❤️ by the AgentiCraft team and contributors</sub>
</div>
