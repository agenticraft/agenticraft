"""Plugin registry for AgentiCraft.

This module provides a centralized registry for managing plugins,
their dependencies, and lifecycle. It ensures plugins are loaded
in the correct order and handles plugin interactions.

Example:
    Using the plugin registry::

        from agenticraft.plugins import PluginRegistry

        registry = PluginRegistry()

        # Register a plugin
        registry.register(weather_plugin)

        # Get tools from all plugins
        all_tools = registry.get_all_tools()

        # Get plugins by capability
        tool_plugins = registry.get_plugins_by_capability("tools")
"""

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from .base import BasePlugin, PluginInfo

if TYPE_CHECKING:
    from ..core.agent import Agent
    from ..core.tool import Tool

logger = logging.getLogger(__name__)


class PluginDependencyError(Exception):
    """Raised when plugin dependencies cannot be resolved."""

    pass


class PluginRegistry:
    """Central registry for managing AgentiCraft plugins."""

    def __init__(self):
        """Initialize plugin registry."""
        # Registered plugins by name
        self._plugins: dict[str, BasePlugin] = {}

        # Plugin metadata cache
        self._plugin_info: dict[str, PluginInfo] = {}

        # Capability indexes
        self._tools_index: dict[str, list[BasePlugin]] = defaultdict(list)
        self._agents_index: dict[str, list[BasePlugin]] = defaultdict(list)
        self._providers_index: dict[str, list[BasePlugin]] = defaultdict(list)

        # Plugin dependencies
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._dependents: dict[str, set[str]] = defaultdict(set)

        # Lifecycle tracking
        self._initialized_plugins: set[str] = set()
        self._load_order: list[str] = []

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin with the registry.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If plugin with same name already registered
        """
        info = plugin.get_info()

        if info.name in self._plugins:
            raise ValueError(f"Plugin '{info.name}' already registered")

        # Store plugin and info
        self._plugins[info.name] = plugin
        self._plugin_info[info.name] = info

        # Update capability indexes
        self._update_indexes(plugin, info)

        # Track dependencies
        self._update_dependencies(info)

        # Add to load order
        self._load_order.append(info.name)

        logger.info(f"Registered plugin: {info.name} v{info.version}")

    def unregister(self, plugin: BasePlugin) -> None:
        """Unregister a plugin from the registry.

        Args:
            plugin: Plugin instance to unregister
        """
        info = plugin.get_info()

        if info.name not in self._plugins:
            return

        # Check dependents
        if info.name in self._dependents and self._dependents[info.name]:
            dependents = ", ".join(self._dependents[info.name])
            logger.warning(
                f"Unregistering plugin '{info.name}' which has dependents: {dependents}"
            )

        # Remove from indexes
        self._remove_from_indexes(plugin, info)

        # Remove from tracking
        del self._plugins[info.name]
        del self._plugin_info[info.name]

        if info.name in self._initialized_plugins:
            self._initialized_plugins.remove(info.name)

        if info.name in self._load_order:
            self._load_order.remove(info.name)

        # Clean up dependencies
        if info.name in self._dependencies:
            del self._dependencies[info.name]

        for deps in self._dependents.values():
            deps.discard(info.name)

        logger.info(f"Unregistered plugin: {info.name}")

    def _update_indexes(self, plugin: BasePlugin, info: PluginInfo) -> None:
        """Update capability indexes for a plugin."""
        # Tool index
        for tool_name in info.provides_tools:
            self._tools_index[tool_name].append(plugin)

        # Agent index
        for agent_name in info.provides_agents:
            self._agents_index[agent_name].append(plugin)

        # Provider index
        for provider_name in info.provides_providers:
            self._providers_index[provider_name].append(plugin)

    def _remove_from_indexes(self, plugin: BasePlugin, info: PluginInfo) -> None:
        """Remove plugin from capability indexes."""
        # Tool index
        for tool_name in info.provides_tools:
            if plugin in self._tools_index[tool_name]:
                self._tools_index[tool_name].remove(plugin)

        # Agent index
        for agent_name in info.provides_agents:
            if plugin in self._agents_index[agent_name]:
                self._agents_index[agent_name].remove(plugin)

        # Provider index
        for provider_name in info.provides_providers:
            if plugin in self._providers_index[provider_name]:
                self._providers_index[provider_name].remove(plugin)

    def _update_dependencies(self, info: PluginInfo) -> None:
        """Update dependency tracking for a plugin."""
        # Parse dependencies from info
        deps = set()
        if hasattr(info, "depends_on"):
            deps.update(info.depends_on)

        self._dependencies[info.name] = deps

        # Update dependents
        for dep in deps:
            self._dependents[dep].add(info.name)

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get a registered plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        return self._plugins.get(name)

    def get_plugin_info(self, name: str) -> PluginInfo | None:
        """Get plugin information by name.

        Args:
            name: Plugin name

        Returns:
            Plugin info or None
        """
        return self._plugin_info.get(name)

    def list_plugins(self) -> list[PluginInfo]:
        """List all registered plugins.

        Returns:
            List of plugin information
        """
        return list(self._plugin_info.values())

    def get_plugins_by_capability(self, capability: str) -> list[BasePlugin]:
        """Get plugins that provide a specific capability.

        Args:
            capability: Capability type ("tools", "agents", "providers")

        Returns:
            List of plugins with the capability
        """
        plugins = []

        if capability == "tools":
            for plugin_list in self._tools_index.values():
                for plugin in plugin_list:
                    if plugin not in plugins:
                        plugins.append(plugin)

        elif capability == "agents":
            for plugin_list in self._agents_index.values():
                for plugin in plugin_list:
                    if plugin not in plugins:
                        plugins.append(plugin)

        elif capability == "providers":
            for plugin_list in self._providers_index.values():
                for plugin in plugin_list:
                    if plugin not in plugins:
                        plugins.append(plugin)

        return plugins

    def get_all_tools(self) -> dict[str, "Tool"]:
        """Get all tools from registered plugins.

        Returns:
            Dict mapping tool names to tool instances
        """
        tools = {}

        for plugin in self._plugins.values():
            try:
                plugin_tools = plugin.get_tools()
                for tool in plugin_tools:
                    if hasattr(tool, "name"):
                        tools[tool.name] = tool
            except Exception as e:
                logger.error(f"Error getting tools from plugin '{plugin.name}': {e}")

        return tools

    def get_all_agents(self) -> dict[str, type]:
        """Get all agent classes from registered plugins.

        Returns:
            Dict mapping agent names to agent classes
        """
        agents = {}

        for plugin in self._plugins.values():
            try:
                plugin_agents = plugin.get_agents()
                for agent_class in plugin_agents:
                    agents[agent_class.__name__] = agent_class
            except Exception as e:
                logger.error(f"Error getting agents from plugin '{plugin.name}': {e}")

        return agents

    def get_all_providers(self) -> dict[str, type]:
        """Get all providers from registered plugins.

        Returns:
            Dict mapping provider names to provider classes
        """
        providers = {}

        for plugin in self._plugins.values():
            try:
                plugin_providers = plugin.get_providers()
                providers.update(plugin_providers)
            except Exception as e:
                logger.error(
                    f"Error getting providers from plugin '{plugin.name}': {e}"
                )

        return providers

    def enhance_agent(self, agent: "Agent") -> "Agent":
        """Apply all plugin enhancements to an agent.

        Args:
            agent: Agent to enhance

        Returns:
            Enhanced agent
        """
        for plugin in self._plugins.values():
            try:
                agent = plugin.enhance_agent(agent)
            except Exception as e:
                logger.error(f"Error enhancing agent with plugin '{plugin.name}': {e}")

        return agent

    def initialize_all(self) -> None:
        """Initialize all registered plugins in dependency order."""
        # Get initialization order
        init_order = self._get_initialization_order()

        for plugin_name in init_order:
            if plugin_name in self._initialized_plugins:
                continue

            plugin = self._plugins[plugin_name]

            try:
                plugin.initialize()
                self._initialized_plugins.add(plugin_name)
                logger.info(f"Initialized plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin '{plugin_name}': {e}")
                raise

    def cleanup_all(self) -> None:
        """Clean up all plugins in reverse dependency order."""
        # Clean up in reverse order
        cleanup_order = list(reversed(self._get_initialization_order()))

        for plugin_name in cleanup_order:
            if plugin_name not in self._initialized_plugins:
                continue

            plugin = self._plugins[plugin_name]

            try:
                plugin.cleanup()
                self._initialized_plugins.remove(plugin_name)
                logger.info(f"Cleaned up plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error cleaning up plugin '{plugin_name}': {e}")

    def _get_initialization_order(self) -> list[str]:
        """Get plugin initialization order based on dependencies.

        Returns:
            List of plugin names in initialization order

        Raises:
            PluginDependencyError: If circular dependencies detected
        """
        # Topological sort
        visited = set()
        temp_visited = set()
        order = []

        def visit(name: str):
            if name in temp_visited:
                raise PluginDependencyError(
                    f"Circular dependency detected involving '{name}'"
                )

            if name in visited:
                return

            temp_visited.add(name)

            # Visit dependencies first
            if name in self._dependencies:
                for dep in self._dependencies[name]:
                    if dep in self._plugins:  # Only if dependency is registered
                        visit(dep)

            temp_visited.remove(name)
            visited.add(name)
            order.append(name)

        # Visit all plugins
        for plugin_name in self._plugins:
            if plugin_name not in visited:
                visit(plugin_name)

        return order

    def validate_dependencies(self) -> list[str]:
        """Validate all plugin dependencies are satisfied.

        Returns:
            List of missing dependencies
        """
        missing = []

        for plugin_name, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._plugins:
                    missing.append(f"{plugin_name} requires {dep}")

        return missing

    def get_plugin_stats(self) -> dict[str, Any]:
        """Get statistics about registered plugins.

        Returns:
            Dictionary of statistics
        """
        total_tools = sum(
            len(info.provides_tools) for info in self._plugin_info.values()
        )
        total_agents = sum(
            len(info.provides_agents) for info in self._plugin_info.values()
        )
        total_providers = sum(
            len(info.provides_providers) for info in self._plugin_info.values()
        )

        return {
            "total_plugins": len(self._plugins),
            "initialized_plugins": len(self._initialized_plugins),
            "total_tools": total_tools,
            "total_agents": total_agents,
            "total_providers": total_providers,
            "unique_tools": len(self._tools_index),
            "unique_agents": len(self._agents_index),
            "unique_providers": len(self._providers_index),
            "plugins_with_dependencies": len(
                [d for d in self._dependencies.values() if d]
            ),
            "missing_dependencies": len(self.validate_dependencies()),
        }

    def clear(self) -> None:
        """Clear all registered plugins."""
        # Clean up first
        self.cleanup_all()

        # Clear all data
        self._plugins.clear()
        self._plugin_info.clear()
        self._tools_index.clear()
        self._agents_index.clear()
        self._providers_index.clear()
        self._dependencies.clear()
        self._dependents.clear()
        self._initialized_plugins.clear()
        self._load_order.clear()

        logger.info("Cleared plugin registry")


# Global registry instance
_global_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry.

    Returns:
        Global PluginRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry


def register_plugin(plugin: BasePlugin) -> None:
    """Register a plugin with the global registry.

    Args:
        plugin: Plugin to register
    """
    registry = get_plugin_registry()
    registry.register(plugin)


def get_all_plugin_tools() -> dict[str, "Tool"]:
    """Get all tools from registered plugins.

    Returns:
        Dict of tool name to tool instance
    """
    registry = get_plugin_registry()
    return registry.get_all_tools()
