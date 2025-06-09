"""AgentiCraft plugin system.

This package provides the plugin architecture that allows extending
AgentiCraft without modifying the core framework. Plugins can add
tools, agents, providers, and custom functionality.

Example:
    Using the plugin system::

        from agenticraft.plugins import BasePlugin, load_plugin, discover_plugins

        # Create a custom plugin
        class MyPlugin(BasePlugin):
            name = "my_plugin"
            version = "1.0.0"

            def get_tools(self):
                return [MyCustomTool()]

        # Discover available plugins
        plugins = discover_plugins()

        # Load a specific plugin
        plugin = load_plugin("weather_plugin")

        # Get all tools from plugins
        from agenticraft.plugins import get_all_plugin_tools
        tools = get_all_plugin_tools()
"""

from .base import (
    AgentPlugin,
    BasePlugin,
    CompositePlugin,
    PluginConfig,
    PluginInfo,
    ToolPlugin,
)
from .loader import (
    PluginLoader,
    PluginLoadError,
    discover_plugins,
    get_plugin_loader,
    load_plugin,
)
from .registry import (
    PluginDependencyError,
    PluginRegistry,
    get_all_plugin_tools,
    get_plugin_registry,
    register_plugin,
)

# Re-export from core for convenience
# Note: Commenting out to avoid conflicts with local BasePlugin
# from ..core.plugin import (
#     BasePlugin as Plugin,
#     PluginInfo as PluginMetadata,
#     LoggingPlugin,
#     MetricsPlugin
# )

__all__ = [
    # Base classes
    "BasePlugin",
    "PluginInfo",
    "PluginConfig",
    "ToolPlugin",
    "AgentPlugin",
    "CompositePlugin",
    # Loader
    "PluginLoader",
    "PluginLoadError",
    "get_plugin_loader",
    "load_plugin",
    "discover_plugins",
    # Registry
    "PluginRegistry",
    "PluginDependencyError",
    "get_plugin_registry",
    "register_plugin",
    "get_all_plugin_tools",
    # Core plugin interface
    # "Plugin",
    # "PluginMetadata",
    # "LoggingPlugin",
    # "MetricsPlugin",
]
