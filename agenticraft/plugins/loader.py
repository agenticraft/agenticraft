"""Dynamic plugin loader for AgentiCraft.

This module provides functionality for discovering, loading, and
managing plugins at runtime. It supports loading plugins from:
- Python packages
- Plugin directories
- Individual plugin files
- Remote plugin repositories (future)

Example:
    Loading plugins::

        from agenticraft.plugins import PluginLoader

        loader = PluginLoader()

        # Load from directory
        loader.load_from_directory("~/.agenticraft/plugins")

        # Load specific plugin
        plugin = loader.load_plugin("weather_plugin")

        # Get all loaded plugins
        plugins = loader.get_loaded_plugins()
"""

import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Any

from .base import BasePlugin, PluginConfig, PluginInfo
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin fails to load."""

    pass


class PluginLoader:
    """Manages dynamic loading of AgentiCraft plugins."""

    def __init__(
        self,
        plugin_dirs: list[str | Path] | None = None,
        auto_discover: bool = True,
    ):
        """Initialize plugin loader.

        Args:
            plugin_dirs: Directories to search for plugins
            auto_discover: Whether to auto-discover plugins on init
        """
        self.plugin_dirs = []
        if plugin_dirs:
            for dir_path in plugin_dirs:
                self.add_plugin_directory(dir_path)

        # Add default plugin directories
        self._add_default_directories()

        # Plugin storage
        self._loaded_plugins: dict[str, BasePlugin] = {}
        self._plugin_classes: dict[str, type[BasePlugin]] = {}
        self._plugin_modules: dict[str, Any] = {}

        # Registry for plugin management
        self.registry = PluginRegistry()

        # Auto-discover if requested
        if auto_discover:
            self.discover_all()

    def _add_default_directories(self) -> None:
        """Add default plugin directories."""
        # User plugins directory
        user_plugins = Path.home() / ".agenticraft" / "plugins"
        if user_plugins.exists():
            self.plugin_dirs.append(user_plugins)

        # Built-in plugins
        builtin_plugins = Path(__file__).parent / "builtin"
        if builtin_plugins.exists():
            self.plugin_dirs.append(builtin_plugins)

        # Environment variable
        import os

        if env_dirs := os.getenv("AGENTICRAFT_PLUGIN_PATH"):
            for dir_path in env_dirs.split(":"):
                if Path(dir_path).exists():
                    self.plugin_dirs.append(Path(dir_path))

    def add_plugin_directory(self, directory: str | Path) -> None:
        """Add a directory to search for plugins.

        Args:
            directory: Path to plugin directory
        """
        path = Path(directory).expanduser().resolve()
        if path.exists() and path.is_dir():
            if path not in self.plugin_dirs:
                self.plugin_dirs.append(path)
                logger.info(f"Added plugin directory: {path}")
        else:
            logger.warning(f"Plugin directory does not exist: {path}")

    def discover_all(self) -> list[str]:
        """Discover all plugins in configured directories.

        Returns:
            List of discovered plugin names
        """
        discovered = []

        for plugin_dir in self.plugin_dirs:
            plugins = self.discover_in_directory(plugin_dir)
            discovered.extend(plugins)

        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered

    def discover_in_directory(self, directory: str | Path) -> list[str]:
        """Discover plugins in a specific directory.

        Args:
            directory: Directory to search

        Returns:
            List of discovered plugin names
        """
        path = Path(directory)
        discovered = []

        if not path.exists() or not path.is_dir():
            return discovered

        # Look for Python files and packages
        for item in path.iterdir():
            if (
                item.is_file()
                and item.suffix == ".py"
                and not item.name.startswith("_")
            ):
                # Single file plugin
                try:
                    plugin_classes = self._load_plugin_from_file(item)
                    for plugin_class in plugin_classes:
                        self._plugin_classes[plugin_class.name] = plugin_class
                        discovered.append(plugin_class.name)
                except Exception as e:
                    logger.error(f"Failed to load plugin from {item}: {e}")

            elif item.is_dir() and not item.name.startswith("_"):
                # Package plugin
                init_file = item / "__init__.py"
                if init_file.exists():
                    try:
                        plugin_classes = self._load_plugin_from_package(item)
                        for plugin_class in plugin_classes:
                            self._plugin_classes[plugin_class.name] = plugin_class
                            discovered.append(plugin_class.name)
                    except Exception as e:
                        logger.error(f"Failed to load plugin from {item}: {e}")

        return discovered

    def _load_plugin_from_file(self, file_path: Path) -> list[type[BasePlugin]]:
        """Load plugin classes from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of plugin classes found
        """
        # Create module spec
        module_name = f"agenticraft_plugin_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if not spec or not spec.loader:
            raise PluginLoadError(f"Cannot create module spec for {file_path}")

        # Load module
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find plugin classes
        plugin_classes = []
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, BasePlugin)
                and obj != BasePlugin
                and obj.__module__ == module_name
            ):
                plugin_classes.append(obj)
                self._plugin_modules[obj.name] = module

        return plugin_classes

    def _load_plugin_from_package(self, package_path: Path) -> list[type[BasePlugin]]:
        """Load plugin classes from a Python package.

        Args:
            package_path: Path to package directory

        Returns:
            List of plugin classes found
        """
        # Add to sys.path temporarily
        parent_dir = str(package_path.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            added_to_path = True
        else:
            added_to_path = False

        try:
            # Import the package
            module_name = package_path.name
            if module_name in sys.modules:
                # Reload if already imported
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            # Find plugin classes
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BasePlugin)
                    and obj != BasePlugin
                ):
                    plugin_classes.append(obj)
                    self._plugin_modules[obj.name] = module

            # Also check for a 'plugin' attribute
            if hasattr(module, "plugin") and inspect.isclass(module.plugin):
                if issubclass(module.plugin, BasePlugin):
                    plugin_classes.append(module.plugin)
                    self._plugin_modules[module.plugin.name] = module

            return plugin_classes

        finally:
            # Clean up sys.path
            if added_to_path:
                sys.path.remove(parent_dir)

    def load_plugin(
        self, plugin_name: str, config: PluginConfig | None = None
    ) -> BasePlugin:
        """Load and initialize a specific plugin.

        Args:
            plugin_name: Name of the plugin to load
            config: Plugin configuration

        Returns:
            Initialized plugin instance

        Raises:
            PluginLoadError: If plugin cannot be loaded
        """
        # Check if already loaded
        if plugin_name in self._loaded_plugins:
            return self._loaded_plugins[plugin_name]

        # Check if plugin class is available
        if plugin_name not in self._plugin_classes:
            # Try to discover it
            self.discover_all()
            if plugin_name not in self._plugin_classes:
                raise PluginLoadError(f"Plugin '{plugin_name}' not found")

        # Create plugin instance
        plugin_class = self._plugin_classes[plugin_name]
        try:
            plugin = plugin_class(config)

            # Validate configuration
            plugin.validate_config()

            # Initialize plugin
            plugin.initialize()

            # Store loaded plugin
            self._loaded_plugins[plugin_name] = plugin

            # Register with registry
            self.registry.register(plugin)

            logger.info(f"Loaded plugin: {plugin_name} v{plugin.version}")
            return plugin

        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin '{plugin_name}': {e}")

    def load_all_discovered(
        self, configs: dict[str, PluginConfig] | None = None
    ) -> dict[str, BasePlugin]:
        """Load all discovered plugins.

        Args:
            configs: Optional configurations for plugins

        Returns:
            Dict mapping plugin names to loaded instances
        """
        configs = configs or {}
        loaded = {}

        for plugin_name in self._plugin_classes:
            try:
                config = configs.get(plugin_name)
                plugin = self.load_plugin(plugin_name, config)
                loaded[plugin_name] = plugin
            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin_name}': {e}")

        return loaded

    def unload_plugin(self, plugin_name: str) -> None:
        """Unload a plugin and clean up its resources.

        Args:
            plugin_name: Name of plugin to unload
        """
        if plugin_name not in self._loaded_plugins:
            return

        plugin = self._loaded_plugins[plugin_name]

        # Cleanup plugin
        try:
            plugin.cleanup()
        except Exception as e:
            logger.error(f"Error during plugin cleanup: {e}")

        # Unregister from registry
        self.registry.unregister(plugin)

        # Remove from loaded plugins
        del self._loaded_plugins[plugin_name]

        logger.info(f"Unloaded plugin: {plugin_name}")

    def reload_plugin(
        self, plugin_name: str, config: PluginConfig | None = None
    ) -> BasePlugin:
        """Reload a plugin (unload and load again).

        Args:
            plugin_name: Name of plugin to reload
            config: New configuration

        Returns:
            Reloaded plugin instance
        """
        # Unload if loaded
        if plugin_name in self._loaded_plugins:
            self.unload_plugin(plugin_name)

        # Reload module if available
        if plugin_name in self._plugin_modules:
            module = self._plugin_modules[plugin_name]
            importlib.reload(module)

            # Re-discover classes from reloaded module
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BasePlugin)
                    and obj != BasePlugin
                    and obj.name == plugin_name
                ):
                    plugin_classes.append(obj)

            if plugin_classes:
                self._plugin_classes[plugin_name] = plugin_classes[0]

        # Load plugin
        return self.load_plugin(plugin_name, config)

    def get_loaded_plugins(self) -> dict[str, BasePlugin]:
        """Get all currently loaded plugins.

        Returns:
            Dict mapping plugin names to instances
        """
        return self._loaded_plugins.copy()

    def get_discovered_plugins(self) -> dict[str, type[BasePlugin]]:
        """Get all discovered plugin classes.

        Returns:
            Dict mapping plugin names to classes
        """
        return self._plugin_classes.copy()

    def get_plugin_info(self, plugin_name: str) -> PluginInfo | None:
        """Get information about a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin info or None if not found
        """
        # Check loaded plugins first
        if plugin_name in self._loaded_plugins:
            return self._loaded_plugins[plugin_name].get_info()

        # Check discovered plugins
        if plugin_name in self._plugin_classes:
            # Create temporary instance to get info
            try:
                plugin = self._plugin_classes[plugin_name]()
                return plugin.get_info()
            except Exception:
                pass

        return None

    def list_plugins(self, loaded_only: bool = False) -> list[dict[str, Any]]:
        """List all plugins with their status.

        Args:
            loaded_only: Only list loaded plugins

        Returns:
            List of plugin information dicts
        """
        plugins = []

        if loaded_only:
            # Only loaded plugins
            for name, plugin in self._loaded_plugins.items():
                info = plugin.get_info()
                plugins.append(
                    {
                        "name": name,
                        "version": info.version,
                        "description": info.description,
                        "loaded": True,
                        "provides": {
                            "tools": info.provides_tools,
                            "agents": info.provides_agents,
                            "providers": info.provides_providers,
                        },
                    }
                )
        else:
            # All discovered plugins
            for name, plugin_class in self._plugin_classes.items():
                loaded = name in self._loaded_plugins

                if loaded:
                    info = self._loaded_plugins[name].get_info()
                else:
                    try:
                        # Create temporary instance
                        plugin = plugin_class()
                        info = plugin.get_info()
                    except Exception:
                        # Minimal info if can't instantiate
                        info = PluginInfo(
                            name=name,
                            version=getattr(plugin_class, "version", "unknown"),
                            description=getattr(plugin_class, "description", ""),
                        )

                plugins.append(
                    {
                        "name": name,
                        "version": info.version,
                        "description": info.description,
                        "loaded": loaded,
                        "provides": {
                            "tools": info.provides_tools,
                            "agents": info.provides_agents,
                            "providers": info.provides_providers,
                        },
                    }
                )

        return plugins


# Global plugin loader instance
_global_loader: PluginLoader | None = None


def get_plugin_loader() -> PluginLoader:
    """Get the global plugin loader instance.

    Returns:
        Global PluginLoader instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = PluginLoader()
    return _global_loader


def load_plugin(name: str, config: PluginConfig | None = None) -> BasePlugin:
    """Load a plugin using the global loader.

    Args:
        name: Plugin name
        config: Plugin configuration

    Returns:
        Loaded plugin instance
    """
    loader = get_plugin_loader()
    return loader.load_plugin(name, config)


def discover_plugins() -> list[str]:
    """Discover all available plugins.

    Returns:
        List of discovered plugin names
    """
    loader = get_plugin_loader()
    return loader.discover_all()
