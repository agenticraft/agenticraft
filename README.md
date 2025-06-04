# AgentiCraft

<div align="center">
  <img src="docs/assets/logo/cover.png" alt="AgentiCraft Logo" width="200">
  
  **Build AI agents as simple as writing Python**

  ![Version](https://img.shields.io/badge/version-0.1.0-blue)
  [![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/github/license/agenticraft/agenticraft.svg)](https://github.com/agenticraft/agenticraft/blob/main/LICENSE)
  [![Tests](https://github.com/agenticraft/agenticraft/actions/workflows/test.yml/badge.svg)](https://github.com/agenticraft/agenticraft/actions)
  [![Documentation](https://img.shields.io/badge/docs-available-green.svg)](https://github.com/agenticraft/agenticraft/tree/main/docs)
  
  [Documentation](https://github.com/agenticraft/agenticraft/tree/main/docs) | [Examples](examples/) | [Discussions](https://github.com/agenticraft/agenticraft/discussions) | [Issues](https://github.com/agenticraft/agenticraft/issues)
</div>

## 📌 Project Status

**Current Version**: v0.1.0 (Beta)  
**Status**: Active Development  
**Released**: June 2025  

This is the initial public release. We're actively working on additional features and welcome community feedback!

## 🎯 Why AgentiCraft?

Building AI agents should be as simple as writing Python. We focus on intuitive design and clear abstractions that scale with your needs.

**AgentiCraft** is a production-ready AI agent framework that prioritizes:

- 🚀 **5-minute quickstart** - Build your first agent faster than making coffee
- 🧠 **Transparent reasoning** - See how your agents think, not just what they output
- 🔌 **MCP-native** - First-class Model Context Protocol support
- 📊 **Built-in observability** - OpenTelemetry integration from day one
- 🎯 **Production templates** - Deploy to production, not just demos
- 🔧 **Intuitive abstractions** - Complex capabilities through simple, composable interfaces

## 🚀 5-Minute Quickstart

### Installation

```bash
# Install from GitHub (available now)
pip install git+https://github.com/agenticraft/agenticraft.git

# Also install OpenAI provider
pip install openai>=1.0.0

# Coming soon: pip install agenticraft
```

### Create Your First Agent

Set your API key:
```bash
# Set your API key (or use .env file)
export OPENAI_API_KEY="your-key-here"
```

Create your first agent in `hello_agent.py`:

```python
from agenticraft import Agent, tool

# Define a simple tool
@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    return eval(expression, {"__builtins__": {}}, {})

# Create an agent with the tool
agent = Agent(
    name="MathAssistant",
    instructions="You are a helpful math assistant.",
    tools=[calculate]
)

# Run the agent
response = agent.run("What's 42 * 17 + 238?")
print(response.content)
# Output: "Let me calculate that for you: 42 * 17 + 238 = 952"

# See the reasoning process
print(response.reasoning)
# Output: "I need to calculate the expression 42 * 17 + 238..."
```

**That's it!** You've just created a working AI agent with reasoning transparency and tool integration.

## 📚 Core Concepts

### Agents
The heart of AgentiCraft. Agents combine LLMs with tools and reasoning patterns.

```python
from agenticraft import Agent, ChainOfThought

agent = Agent(
    name="ResearchAssistant",
    instructions="You help users research topics thoroughly.",
    reasoning_pattern=ChainOfThought(),  # Make thinking visible
    model="gpt-4",  # or "claude-3", "gemini-pro", etc.
)
```

### Tools
Give your agents capabilities with simple Python functions.

```python
from agenticraft import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Your implementation here
    return results

@tool
def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email."""
    # Your implementation here
    return success
```

### Workflows
Chain agents and tools together with simple, dependency-based workflows.

```python
from agenticraft import Workflow, Step

workflow = Workflow(name="content_pipeline")

# Simple step-based approach with dependencies
workflow.add_steps([
    Step("research", agent=researcher, inputs=["topic"]),
    Step("write", agent=writer, depends_on=["research"]),
    Step("review", agent=reviewer, depends_on=["write"]),
])

result = await workflow.run(topic="AI Agent Frameworks")
```

### Memory
Persistent context for your agents with two focused types:

```python
from agenticraft import Agent, ConversationMemory, KnowledgeMemory

agent = Agent(
    name="PersonalAssistant",
    memory=[
        ConversationMemory(max_turns=10),  # Remember recent conversation
        KnowledgeMemory(persist=True),      # Long-term knowledge storage
    ]
)
```

### Observability
See what's happening inside your agents with built-in OpenTelemetry support.

```python
from agenticraft import Agent, Telemetry

# Enable observability
telemetry = Telemetry(
    service_name="my-agent-app",
    export_to="http://localhost:4317"  # Jaeger, Datadog, etc.
)

# All agent operations are automatically traced
agent = Agent(name="MonitoredAgent", telemetry=telemetry)
```

## 🛠️ Features

### Model Context Protocol (MCP) Support
First-class support for MCP tools and servers.

```python
from agenticraft import Agent, MCPTool

# Use any MCP tool
mcp_browser = MCPTool("@browserbase/browser")
agent = Agent(tools=[mcp_browser])

# Or connect to MCP servers
agent.connect_mcp_server("github.com/owner/mcp-server")
```

### Multiple LLM Providers
Switch between providers with a single line.

```python
# OpenAI (currently supported)
agent = Agent(model="gpt-4", api_key=openai_key)

# Coming in v0.1.1:
# Anthropic
agent = Agent(model="claude-3-opus", api_key=anthropic_key)

# Google
agent = Agent(model="gemini-pro", api_key=google_key)

# Open source via Ollama
agent = Agent(model="ollama/llama2", base_url="http://localhost:11434")
```

### Production Templates
Get to production faster with built-in templates.

```bash
# Create a customer support agent
agenticraft create support-agent my-support-bot

# Create a data analysis pipeline
agenticraft create data-pipeline my-analyzer

# Create a content generation workflow
agenticraft create content-system my-writer
```

### Plugin Architecture
Extend AgentiCraft without modifying the core.

```python
from agenticraft import Plugin

class MyPlugin(Plugin):
    def on_agent_created(self, agent):
        # Add custom functionality
        pass
    
    def on_response_generated(self, response):
        # Process responses
        pass

# Register plugin
agent = Agent(plugins=[MyPlugin()])
```

## 🏗️ Architecture

AgentiCraft's architecture is intentionally simple:

```
┌─────────────────┐
│      Agent      │  ← Your code interacts here
├─────────────────┤
│    Reasoning    │  ← Transparent thinking process  
├─────────────────┤
│  Tools & MCP    │  ← Capabilities and integrations
├─────────────────┤
│     Memory      │  ← Conversation + Knowledge only
├─────────────────┤
│   LLM Provider  │  ← Swappable backends
├─────────────────┤
│   Telemetry     │  ← Built-in observability
└─────────────────┘
```

**Core framework: <2000 lines of code.** If we can't build it simply, we don't build it.

## 📖 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Quickstart Guide](docs/quickstart.md)** - Get running in 5 minutes
- **[Core Concepts](docs/concepts/)** - Understand the basics
- **[API Reference](docs/reference/)** - Detailed API documentation
- **[Examples](examples/)** - Real-world usage examples
- **[Philosophy](docs/philosophy.md)** - Our design principles
- **[MCP Integration](docs/guides/mcp-integration.md)** - Model Context Protocol guide

Documentation website coming soon at docs.agenticraft.ai!

## 🎯 Examples

Check out the [`examples/`](examples/) directory for complete, working examples:

- **[Hello World](examples/01_hello_world.py)** - Your first agent
- **[Tools & Functions](examples/02_tools.py)** - Adding capabilities
- **[Configuration](examples/03_configuration.py)** - Agent configuration
- **[Workflow](examples/04_workflow_research.py)** - Multi-step processes
- **[Tools Showcase](examples/05_tools_showcase.py)** - Advanced tool usage

## 🚀 Installation

### From GitHub (Available Now)

```bash
# Install AgentiCraft
pip install git+https://github.com/agenticraft/agenticraft.git

# Install with development dependencies
pip install -e ".[dev]"

# Install with all optional dependencies
pip install -e ".[all]"
```

### Requirements
- Python 3.10+
- OpenAI API key (or other LLM provider credentials)
- For OpenAI: `pip install openai>=1.0.0`

### Coming Soon
```bash
# From PyPI (coming soon)
pip install agenticraft
```

## 🤝 Contributing

We believe in quality over quantity. Every line of code matters.

```bash
# Clone the repository
git clone https://github.com/agenticraft/agenticraft.git
cd agenticraft

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black .

# Build documentation
mkdocs serve -f mkdocs-simple.yml
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 🗺️ Roadmap

### v0.1.0 (Current Release)
- ✅ Core framework (<2000 LOC)
- ✅ Base Agent with reasoning patterns
- ✅ Tool system with decorators
- ✅ MCP protocol support
- ✅ Simple workflow engine
- ✅ Conversation + Knowledge memory
- ✅ OpenTelemetry integration
- ✅ CLI tool
- ✅ Production templates

### v0.1.1 (Next Week)
- [ ] Complete Anthropic provider
- [ ] Complete Ollama provider
- [ ] PyPI package release
- [ ] Documentation website

### v0.2.0
- [ ] Streaming responses
- [ ] Advanced reasoning patterns
- [ ] Tool marketplace
- [ ] More MCP integrations
- [ ] Performance optimizations

### v1.0.0
- [ ] Stable API guarantee
- [ ] Enterprise features
- [ ] Cloud deployment helpers
- [ ] GUI for agent building

## 📊 Benchmarks

> *Benchmarks based on initial testing. Community validation welcome!*

| Framework | Setup Time | Core Size | Time to First Agent | Documentation |
|-----------|------------|-----------|-------------------|---------------|
| **AgentiCraft** | 1 min | <2k LOC | 5 min | 100% |
| LangChain | 5 min | >100k LOC | 30 min | 70% |
| AutoGen | 3 min | >50k LOC | 20 min | 60% |
| Custom | ∞ | Varies | Days | Varies |

## 🤔 Philosophy

1. **Simplicity First** - If it's not simple, it's not in core
2. **Transparency Default** - Show reasoning, not magic
3. **Production Ready** - Built for deployment, not demos
4. **Developer Joy** - APIs that spark creativity
5. **Documentation Driven** - If it's not documented, it doesn't exist

## 🤝 Getting Help

- 📖 Check the [documentation](docs/)
- 💬 Ask in [GitHub Discussions](https://github.com/agenticraft/agenticraft/discussions)
- 🐛 Report bugs in [GitHub Issues](https://github.com/agenticraft/agenticraft/issues)
- ⭐ Star the repo to show support!

## 📝 License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with inspiration from the AI agent community and a desire to make agent development accessible to everyone.

Special thanks to all contributors and early testers who helped shape AgentiCraft.

---

<div align="center">
  <strong>Ready to build?</strong>
  
  ```bash
  pip install git+https://github.com/agenticraft/agenticraft.git
  ```
  
  **Build your first agent in 5 minutes.**
  
  [Get Started](docs/quickstart.md) | [Join Discussion](https://github.com/agenticraft/agenticraft/discussions) | [Star on GitHub](https://github.com/agenticraft/agenticraft)
</div>
