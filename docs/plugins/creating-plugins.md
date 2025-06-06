# Plugin Development Guide

This guide explains how to create custom plugins for AgentiCraft to extend its functionality with new tools, agents, providers, and capabilities.

## Overview

AgentiCraft's plugin system allows you to:

- Add custom tools and capabilities
- Create specialized agents
- Integrate new LLM providers
- Enhance existing agents with new features
- Hook into the agent lifecycle
- Add telemetry and monitoring

## Quick Start

Here's a minimal plugin example:

```python
from agenticraft.plugins import BasePlugin, PluginInfo

class HelloPlugin(BasePlugin):
    name = "hello"
    version = "1.0.0"
    description = "A simple greeting plugin"
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description
        )
```

## Plugin Structure

### Basic Plugin Class

Every plugin must inherit from `BasePlugin` and implement required methods:

```python
from agenticraft.plugins import BasePlugin, PluginInfo, PluginConfig
from typing import List, Dict, Any

class MyPlugin(BasePlugin):
    # Required metadata
    name = "my_plugin"
    version = "1.0.0"
    description = "Does amazing things"
    author = "Your Name"
    
    def __init__(self, config: PluginConfig = None):
        super().__init__(config)
        # Initialize your plugin
    
    def get_info(self) -> PluginInfo:
        """Return plugin metadata and capabilities."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            provides_tools=["tool1", "tool2"],
            provides_agents=["CustomAgent"],
            provides_providers=["custom_llm"]
        )
    
    def initialize(self):
        """Set up resources, connections, etc."""
        super().initialize()
        # Your initialization code
    
    def cleanup(self):
        """Clean up resources."""
        # Your cleanup code
        super().cleanup()
```

### Providing Tools

Plugins can provide tools that agents can use:

```python
from agenticraft.core.tool import Tool

class CalculatorTool(Tool):
    name = "calculator"
    description = "Performs mathematical calculations"
    
    async def execute(self, expression: str) -> float:
        # Safely evaluate math expression
        return eval(expression, {"__builtins__": {}})

class MathPlugin(BasePlugin):
    name = "math"
    version = "1.0.0"
    
    def get_tools(self) -> List[Tool]:
        return [CalculatorTool()]
```

### Providing Agents

Plugins can provide complete agent implementations:

```python
from agenticraft.core.agent import Agent

class ResearchAgent(Agent):
    """Specialized agent for research tasks."""
    
    async def process(self, query: str) -> str:
        # Research implementation
        return f"Research results for: {query}"

class ResearchPlugin(BasePlugin):
    name = "research"
    version = "1.0.0"
    
    def get_agents(self) -> List[type]:
        return [ResearchAgent]
```

### Enhancing Existing Agents

Plugins can modify or enhance agents:

```python
class EnhancerPlugin(BasePlugin):
    name = "enhancer"
    version = "1.0.0"
    
    def enhance_agent(self, agent):
        """Add capabilities to any agent."""
        # Add tools
        for tool in self.get_tools():
            agent.add_tool(tool)
        
        # Add context
        agent.add_context("You are enhanced with special abilities...")
        
        # Add capabilities
        agent.add_capability("enhanced_reasoning")
        
        return agent
```

## Configuration

### Plugin Configuration Schema

Define configuration options for your plugin:

```python
def get_config_schema(self) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "description": "API key for service"
            },
            "timeout": {
                "type": "integer",
                "default": 30,
                "description": "Request timeout in seconds"
            },
            "retry_count": {
                "type": "integer",
                "default": 3,
                "minimum": 0,
                "maximum": 10
            }
        },
        "required": ["api_key"]
    }
```

### Using Configuration

Access configuration in your plugin:

```python
def initialize(self):
    super().initialize()
    
    # Get config values
    api_key = self.config.config.get("api_key")
    timeout = self.config.config.get("timeout", 30)
    
    # Validate required config
    if not api_key:
        raise ValueError("API key is required")
    
    # Initialize with config
    self.client = APIClient(api_key=api_key, timeout=timeout)
```

## Lifecycle Hooks

Plugins can hook into various lifecycle events:

```python
from agenticraft.core.plugin import Plugin

class LifecyclePlugin(Plugin):
    """Example using core Plugin interface for lifecycle hooks."""
    
    def on_agent_created(self, agent):
        """Called when any agent is created."""
        print(f"Agent created: {agent.name}")
    
    def on_agent_run_start(self, agent, prompt, context):
        """Called before agent processes input."""
        print(f"Processing: {prompt[:50]}...")
    
    def on_agent_run_complete(self, agent, response):
        """Called after agent completes."""
        print(f"Completed with {len(response.content)} chars")
    
    def on_tool_execution_start(self, tool_name, arguments):
        """Called before tool execution."""
        print(f"Executing tool: {tool_name}")
    
    def on_response_generated(self, response):
        """Called to potentially modify responses."""
        # Add metadata
        response.metadata["plugin_processed"] = True
        return response
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def execute(self, **kwargs):
    try:
        result = await self.api_call(**kwargs)
        return result
    except APIError as e:
        logger.error(f"API error: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### 2. Resource Management

Use proper initialization and cleanup:

```python
def initialize(self):
    super().initialize()
    self.connection = self._connect()
    self.cache = {}

def cleanup(self):
    if hasattr(self, 'connection'):
        self.connection.close()
    self.cache.clear()
    super().cleanup()
```

### 3. Async Support

Make tools and methods async when possible:

```python
async def execute(self, query: str) -> Dict[str, Any]:
    # Async operations
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{self.api_url}?q={query}")
        return response.json()
```

### 4. Telemetry Integration

Add telemetry to track plugin usage:

```python
from agenticraft.telemetry import track_metrics

class TelemetryPlugin(BasePlugin):
    @track_metrics(
        name="plugin.api_calls",
        labels=["endpoint", "status"]
    )
    async def call_api(self, endpoint: str):
        # Your API call
        return result
```

### 5. Documentation

Document your plugin thoroughly:

```python
class WellDocumentedPlugin(BasePlugin):
    """
    My Amazing Plugin
    
    This plugin provides X, Y, and Z capabilities for AgentiCraft.
    
    Configuration:
        api_key (str): Required. Your API key
        region (str): Optional. API region (default: "us")
    
    Provides:
        Tools: search, analyze, summarize
        Agents: ResearchAgent, AnalysisAgent
    
    Example:
        plugin = WellDocumentedPlugin(PluginConfig(
            config={"api_key": "xxx", "region": "eu"}
        ))
    """
```

## Plugin Types

### Tool Plugin

For plugins that only provide tools:

```python
from agenticraft.plugins import ToolPlugin

class UtilityPlugin(ToolPlugin):
    name = "utilities"
    version = "1.0.0"
    
    def create_tools(self) -> List[Tool]:
        return [
            DateTool(),
            RandomTool(),
            HashTool()
        ]
```

### Agent Plugin

For plugins that provide agents:

```python
from agenticraft.plugins import AgentPlugin

class SpecialistPlugin(AgentPlugin):
    name = "specialists"
    version = "1.0.0"
    
    def create_agents(self) -> List[type]:
        return [
            CodeReviewAgent,
            DocumentationAgent,
            TestingAgent
        ]
```

### Composite Plugin

For comprehensive plugins:

```python
from agenticraft.plugins import CompositePlugin

class FullFeaturePlugin(CompositePlugin):
    name = "full_feature"
    version = "1.0.0"
    
    def get_tools(self) -> List[Tool]:
        return [Tool1(), Tool2()]
    
    def get_agents(self) -> List[type]:
        return [Agent1, Agent2]
    
    def get_providers(self) -> Dict[str, type]:
        return {"custom": CustomProvider}
```

## Testing Your Plugin

### Unit Tests

```python
import pytest
from agenticraft.plugins import PluginConfig

@pytest.fixture
def plugin():
    config = PluginConfig(config={"api_key": "test"})
    return MyPlugin(config)

def test_plugin_info(plugin):
    info = plugin.get_info()
    assert info.name == "my_plugin"
    assert "tool1" in info.provides_tools

async def test_tool_execution(plugin):
    tools = plugin.get_tools()
    result = await tools[0].execute("test input")
    assert result is not None
```

### Integration Tests

```python
async def test_plugin_with_agent():
    # Load plugin
    plugin = MyPlugin()
    plugin.initialize()
    
    # Create agent and enhance
    agent = Agent("Test")
    enhanced = plugin.enhance_agent(agent)
    
    # Test enhanced agent
    response = await enhanced.run("test query")
    assert response.success
    
    # Cleanup
    plugin.cleanup()
```

## Distribution

### Package Structure

```
my-plugin/
├── pyproject.toml
├── README.md
├── LICENSE
├── my_plugin/
│   ├── __init__.py
│   ├── plugin.py
│   ├── tools.py
│   └── agents.py
└── tests/
    └── test_plugin.py
```

### pyproject.toml

```toml
[project]
name = "agenticraft-my-plugin"
version = "1.0.0"
description = "My plugin for AgentiCraft"
dependencies = [
    "agenticraft>=0.1.0",
    "httpx>=0.25.0"
]

[project.entry-points."agenticraft.plugins"]
my_plugin = "my_plugin:MyPlugin"
```

### Installation

Users can install your plugin with:

```bash
pip install agenticraft-my-plugin
```

Or from a directory:

```bash
agenticraft plugin install ./my-plugin
```

## Examples

Plugin examples demonstrate common patterns:

- **Weather Plugin** - Basic tool plugin for weather data
- **Research Plugin** - Agent plugin for research capabilities
- **Telemetry Plugin** - Monitoring and metrics integration
- **Composite Plugin** - Full-featured plugin with tools, agents, and providers

## Plugin Discovery

Plugins are discovered from:

1. Built-in plugins directory
2. `~/.agenticraft/plugins/`
3. Directories in `AGENTICRAFT_PLUGIN_PATH`
4. Installed Python packages with entry points

## Debugging

Enable debug logging to troubleshoot plugins:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("agenticraft.plugins")

# In your plugin
logger.debug(f"Loading plugin: {self.name}")
```

## Security Considerations

1. **Validate all inputs** from configuration and users
2. **Sanitize outputs** before returning to agents
3. **Use minimal permissions** for external services
4. **Don't store secrets** in code or configs
5. **Follow secure coding** practices

## FAQ

### Q: Can plugins depend on other plugins?

Yes, use the `depends_on` field in PluginInfo:

```python
def get_info(self):
    return PluginInfo(
        name="my_plugin",
        depends_on=["base_plugin", "auth_plugin"]
    )
```

### Q: How do I version my plugin?

Use semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features, backwards compatible
- PATCH: Bug fixes

### Q: Can I use external libraries?

Yes, declare them in your plugin's dependencies. Users will need to install them.

### Q: How do I handle async vs sync tools?

AgentiCraft supports both. Use async when possible for better performance.

## Getting Help

- Check plugin examples in the repository
- Join our [Discord](https://discord.gg/agenticraft)
- Open an [issue](https://github.com/agenticraft/agenticraft/issues)
- Read the [API Reference](../reference/index.md)
