# Tool Marketplace Documentation

AgentiCraft's Tool Marketplace provides a plugin ecosystem for discovering, installing, and managing tools for your agents.

## Overview

The Tool Marketplace enables:
- **Plugin Discovery**: Search and browse available tools
- **Version Management**: Semantic versioning with dependency resolution
- **Easy Installation**: One-command install with automatic dependency handling
- **Plugin Development**: Create and publish your own tools
- **Registry Support**: Connect to public or private registries

## Quick Start

### Installing a Plugin

```python
from agenticraft.marketplace import RegistryClient

# Initialize registry client
registry = RegistryClient()

# Search for plugins
results = await registry.search("weather")
for plugin in results:
    print(f"{plugin.name} v{plugin.version} - {plugin.description}")

# Install a plugin
await registry.install("weather-tool", version="^1.0.0")

# Use the installed tool
from agenticraft import Agent
agent = Agent(name="Assistant")
response = await agent.arun("What's the weather in San Francisco?")
```

### Creating a Plugin

```python
from agenticraft.marketplace import PluginManifest

# Create plugin manifest
manifest = PluginManifest(
    name="my-custom-tool",
    version="1.0.0",
    description="A custom tool for AgentiCraft",
    author="Your Name",
    license="MIT",
    tools=[
        {
            "name": "CustomTool",
            "module": "my_custom_tool.tool",
            "class": "CustomTool"
        }
    ],
    dependencies={
        "agenticraft": ">=0.2.0",
        "requests": ">=2.28.0"
    }
)

# Save manifest
manifest.save("plugin.yaml")
```

## Core Concepts

### Plugin Structure

A typical plugin structure:

```
my-plugin/
├── plugin.yaml          # Plugin manifest
├── README.md           # Documentation
├── src/
│   └── my_plugin/
│       ├── __init__.py
│       ├── tool.py     # Tool implementation
│       └── utils.py
├── tests/
│   └── test_tool.py
└── examples/
    └── example.py
```

### Manifest Schema

The `plugin.yaml` manifest defines your plugin:

```yaml
name: weather-tool
version: 1.2.0
description: Real-time weather data for agents
author: AgentiCraft Community
license: MIT

metadata:
  homepage: https://github.com/agenticraft/weather-tool
  repository: https://github.com/agenticraft/weather-tool
  documentation: https://weather-tool.readthedocs.io
  tags:
    - weather
    - api
    - real-time

tools:
  - name: WeatherTool
    module: weather_tool.main
    class: WeatherTool
    description: Get current weather and forecasts

dependencies:
  agenticraft: ">=0.2.0"
  requests: ">=2.28.0"
  
configuration:
  api_key:
    type: string
    description: Weather API key
    required: true
    env_var: WEATHER_API_KEY
    
  default_units:
    type: string
    description: Temperature units
    default: celsius
    choices: [celsius, fahrenheit]
```

### Version Management

The marketplace uses semantic versioning (semver):

```python
from agenticraft.marketplace import Version

# Parse versions
v1 = Version("1.2.3")
v2 = Version("2.0.0-beta.1")

# Compare versions
print(v1 < v2)  # True
print(v1.is_compatible_with("^1.0.0"))  # True

# Version ranges
range_spec = ">=1.0.0,<2.0.0"
print(v1.satisfies(range_spec))  # True
```

## Plugin Development

### Creating a Tool Plugin

```python
# src/my_plugin/tool.py
from agenticraft.tools import BaseTool
from typing import Dict, Any

class MyCustomTool(BaseTool):
    """A custom tool for demonstration."""
    
    name = "my_custom_tool"
    description = "Performs custom operations"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.api_key = config.get("api_key")
        
    async def execute(self, query: str) -> str:
        """Execute the tool with the given query."""
        # Your implementation here
        return f"Processed: {query}"
```

### Plugin Manifest

```python
# Create manifest programmatically
from agenticraft.marketplace import PluginManifest, ToolDefinition

manifest = PluginManifest(
    name="my-plugin",
    version="1.0.0",
    description="My custom AgentiCraft plugin",
    author="John Doe <john@example.com>",
    license="MIT",
    
    # Metadata
    homepage="https://example.com/my-plugin",
    repository="https://github.com/username/my-plugin",
    
    # Tools provided
    tools=[
        ToolDefinition(
            name="MyCustomTool",
            module="my_plugin.tool",
            class_name="MyCustomTool",
            description="A custom tool"
        )
    ],
    
    # Dependencies
    dependencies={
        "agenticraft": ">=0.2.0",
        "aiohttp": ">=3.8.0"
    },
    
    # Configuration schema
    configuration={
        "api_key": {
            "type": "string",
            "description": "API key for the service",
            "required": True,
            "env_var": "MY_PLUGIN_API_KEY"
        }
    }
)

# Validate manifest
if manifest.is_valid():
    manifest.save("plugin.yaml")
```

### Testing Your Plugin

```python
# tests/test_tool.py
import pytest
from my_plugin.tool import MyCustomTool

@pytest.mark.asyncio
async def test_tool_execution():
    """Test tool execution."""
    tool = MyCustomTool({"api_key": "test-key"})
    result = await tool.execute("test query")
    assert "Processed: test query" in result

def test_tool_metadata():
    """Test tool metadata."""
    assert MyCustomTool.name == "my_custom_tool"
    assert MyCustomTool.description
```

## Registry Operations

### Searching Plugins

```python
from agenticraft.marketplace import RegistryClient

registry = RegistryClient()

# Simple search
results = await registry.search("weather")

# Advanced search with filters
results = await registry.search(
    query="data",
    tags=["api", "real-time"],
    author="AgentiCraft",
    min_version="1.0.0"
)

# Get plugin details
plugin = await registry.get_plugin("weather-tool")
print(f"Latest version: {plugin.latest_version}")
print(f"Downloads: {plugin.downloads}")
print(f"Rating: {plugin.rating}/5")
```

### Installing and Managing

```python
# Install specific version
await registry.install("weather-tool", version="1.2.0")

# Install with version range
await registry.install("weather-tool", version="^1.0.0")

# Update plugin
await registry.update("weather-tool")

# List installed plugins
installed = await registry.list_installed()
for plugin in installed:
    print(f"{plugin.name} v{plugin.version}")

# Uninstall plugin
await registry.uninstall("weather-tool")
```

### Publishing Plugins

```python
# Publish to registry
await registry.publish(
    manifest_path="./plugin.yaml",
    api_token="your-api-token"
)

# Update existing plugin
await registry.update_plugin(
    name="my-plugin",
    version="1.1.0",
    manifest_path="./plugin.yaml",
    api_token="your-api-token"
)
```

## Advanced Features

### Local Development

```python
# Install plugin from local directory
await registry.install_local("./path/to/my-plugin")

# Link plugin for development
await registry.link("./path/to/my-plugin")

# Test with local plugin
from agenticraft import Agent
agent = Agent(name="TestAgent")
agent.load_tool("my_custom_tool")
```

### Private Registries

```python
# Configure private registry
registry = RegistryClient(
    registry_url="https://registry.company.com",
    auth_token="private-token"
)

# Install from private registry
await registry.install("internal-tool")
```

### Dependency Resolution

```python
# Check dependencies before install
deps = await registry.check_dependencies("complex-plugin")
print("Required dependencies:")
for dep in deps:
    print(f"  {dep.name} {dep.version_spec}")

# Resolve conflicts
conflicts = await registry.find_conflicts()
if conflicts:
    print("Version conflicts detected:")
    for conflict in conflicts:
        print(f"  {conflict}")
```

## Configuration

### Registry Configuration

```python
# Configure registry client
from agenticraft.marketplace import RegistryConfig

config = RegistryConfig(
    registry_url="https://registry.agenticraft.com",
    cache_dir="~/.agenticraft/cache",
    timeout=30,
    max_retries=3
)

registry = RegistryClient(config=config)
```

### Plugin Configuration

```python
# Load plugin with configuration
from agenticraft.marketplace import load_plugin

plugin = load_plugin(
    "weather-tool",
    config={
        "api_key": "your-api-key",
        "default_units": "fahrenheit"
    }
)

# Use environment variables
# Set: export WEATHER_API_KEY="your-api-key"
plugin = load_plugin("weather-tool")
```

## Best Practices

### 1. Version Management

```python
# Use version ranges wisely
dependencies = {
    # Caret: Compatible with 1.x.x
    "agenticraft": "^1.0.0",
    
    # Tilde: Compatible with 1.2.x
    "requests": "~1.2.0",
    
    # Exact version (avoid unless necessary)
    "critical-lib": "2.1.0",
    
    # Range
    "flexible-lib": ">=1.0.0,<3.0.0"
}
```

### 2. Plugin Structure

```python
# Recommended plugin structure
class PluginStructure:
    """Standard plugin organization."""
    
    @staticmethod
    def create_structure(plugin_name: str):
        """Create standard plugin structure."""
        return {
            "plugin.yaml": "manifest",
            "README.md": "documentation",
            "LICENSE": "license file",
            "src/": {
                f"{plugin_name}/": {
                    "__init__.py": "package init",
                    "tool.py": "main tool implementation",
                    "utils.py": "utility functions"
                }
            },
            "tests/": {
                "test_tool.py": "tool tests",
                "test_integration.py": "integration tests"
            },
            "examples/": {
                "basic_usage.py": "basic example",
                "advanced_usage.py": "advanced example"
            }
        }
```

### 3. Error Handling

```python
# Robust plugin implementation
class RobustTool(BaseTool):
    """Example of robust tool implementation."""
    
    async def execute(self, query: str) -> str:
        """Execute with proper error handling."""
        try:
            # Validate input
            if not query:
                raise ValueError("Query cannot be empty")
            
            # Process query
            result = await self._process(query)
            
            # Validate output
            if not result:
                return "No results found"
                
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return f"Error: {e}"
        except Exception as e:
            logger.exception("Unexpected error")
            return "An error occurred processing your request"
```

## Troubleshooting

### Common Issues

**Plugin not found**:
```python
# Check registry URL
print(registry.registry_url)

# Search with partial name
results = await registry.search("weather", fuzzy=True)
```

**Version conflicts**:
```python
# Show dependency tree
tree = await registry.dependency_tree("my-plugin")
print(tree)

# Force specific versions
await registry.install("plugin", force=True)
```

**Installation fails**:
```python
# Check logs
import logging
logging.basicConfig(level=logging.DEBUG)

# Clear cache
await registry.clear_cache()

# Reinstall
await registry.install("plugin", clean=True)
```

## Examples

Complete examples are available in `/examples/marketplace/`:

- **marketplace_example.py** - Basic plugin usage
- **create_plugin.py** - Plugin creation guide
- **private_registry.py** - Private registry setup
- **advanced_search.py** - Advanced search features

## API Reference

- [PluginManifest](api-reference.md#pluginmanifest) - Manifest schema
- [RegistryClient](api-reference.md#registryclient) - Registry operations
- [Version](api-reference.md#version) - Version management
- [ToolDefinition](api-reference.md#tooldefinition) - Tool specification

## Next Steps

- [Plugin Development Guide](plugin-development.md) - Create your own plugins
- [Registry Setup](registry-setup.md) - Host your own registry
- [Version Management](version-management.md) - Advanced versioning
- [API Reference](api-reference.md) - Complete API docs
