"""Tests for plugin loader."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

from agenticraft.plugins.loader import (
    PluginLoader,
    PluginLoadError,
    get_plugin_loader,
    load_plugin,
    discover_plugins
)
from agenticraft.plugins.base import BasePlugin, PluginInfo, PluginConfig


class MockPluginForLoading(BasePlugin):
    """Mock plugin for loader tests."""
    name = "test_plugin"
    version = "1.0.0"
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name=self.name,
            version=self.version,
            description="Test plugin for loading"
        )


class TestPluginLoader:
    """Test PluginLoader functionality."""
    
    def test_loader_creation(self):
        """Test creating a plugin loader."""
        loader = PluginLoader(auto_discover=False)
        
        assert loader.plugin_dirs == []
        assert loader._loaded_plugins == {}
        assert loader._plugin_classes == {}
    
    def test_loader_with_directories(self, tmp_path):
        """Test loader with plugin directories."""
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        
        loader = PluginLoader(
            plugin_dirs=[str(plugin_dir)],
            auto_discover=False
        )
        
        assert len(loader.plugin_dirs) > 0
        assert plugin_dir in loader.plugin_dirs
    
    def test_add_plugin_directory(self, tmp_path):
        """Test adding plugin directory."""
        loader = PluginLoader(auto_discover=False)
        
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        
        loader.add_plugin_directory(plugin_dir)
        
        assert plugin_dir in loader.plugin_dirs
    
    def test_add_nonexistent_directory(self):
        """Test adding non-existent directory."""
        loader = PluginLoader(auto_discover=False)
        
        loader.add_plugin_directory("/nonexistent/path")
        
        # Should not be added
        assert Path("/nonexistent/path") not in loader.plugin_dirs
    
    def test_discover_from_file(self, tmp_path):
        """Test discovering plugins from Python file."""
        loader = PluginLoader(auto_discover=False)
        
        # Create plugin file
        plugin_file = tmp_path / "my_plugin.py"
        plugin_file.write_text("""
from agenticraft.plugins.base import BasePlugin, PluginInfo

class FilePlugin(BasePlugin):
    name = "file_plugin"
    version = "1.0.0"
    
    def get_info(self):
        return PluginInfo(name=self.name, version=self.version)
""")
        
        # Discover in directory
        discovered = loader.discover_in_directory(tmp_path)
        
        assert "file_plugin" in discovered
        assert "file_plugin" in loader._plugin_classes
    
    def test_discover_from_package(self, tmp_path):
        """Test discovering plugins from package."""
        loader = PluginLoader(auto_discover=False)
        
        # Create package structure
        package_dir = tmp_path / "my_package"
        package_dir.mkdir()
        
        init_file = package_dir / "__init__.py"
        init_file.write_text("""
from agenticraft.plugins.base import BasePlugin, PluginInfo

class PackagePlugin(BasePlugin):
    name = "package_plugin"
    version = "1.0.0"
    
    def get_info(self):
        return PluginInfo(name=self.name, version=self.version)

# Export plugin
plugin = PackagePlugin
""")
        
        # Discover in directory
        discovered = loader.discover_in_directory(tmp_path)
        
        assert "package_plugin" in discovered
        assert "package_plugin" in loader._plugin_classes
    
    def test_load_plugin(self):
        """Test loading a plugin."""
        loader = PluginLoader(auto_discover=False)
        
        # Manually add plugin class
        loader._plugin_classes["test_plugin"] = MockPluginForLoading
        
        # Load plugin
        plugin = loader.load_plugin("test_plugin")
        
        assert plugin is not None
        assert plugin.name == "test_plugin"
        assert plugin.is_initialized
        assert "test_plugin" in loader._loaded_plugins
    
    def test_load_plugin_with_config(self):
        """Test loading plugin with configuration."""
        loader = PluginLoader(auto_discover=False)
        loader._plugin_classes["test_plugin"] = MockPluginForLoading
        
        config = PluginConfig(config={"key": "value"})
        plugin = loader.load_plugin("test_plugin", config)
        
        assert plugin.config == config
        assert plugin.config.config["key"] == "value"
    
    def test_load_nonexistent_plugin(self):
        """Test loading non-existent plugin."""
        loader = PluginLoader(auto_discover=False)
        
        with pytest.raises(PluginLoadError, match="not found"):
            loader.load_plugin("nonexistent")
    
    def test_load_plugin_error(self):
        """Test plugin loading error."""
        
        class ErrorPlugin(BasePlugin):
            name = "error_plugin"
            
            def get_info(self):
                return PluginInfo(name=self.name, version="1.0.0")
            
            def initialize(self):
                raise RuntimeError("Initialization failed")
        
        loader = PluginLoader(auto_discover=False)
        loader._plugin_classes["error_plugin"] = ErrorPlugin
        
        with pytest.raises(PluginLoadError, match="Failed to load"):
            loader.load_plugin("error_plugin")
    
    def test_unload_plugin(self):
        """Test unloading a plugin."""
        loader = PluginLoader(auto_discover=False)
        loader._plugin_classes["test_plugin"] = MockPluginForLoading
        
        # Load plugin
        plugin = loader.load_plugin("test_plugin")
        assert "test_plugin" in loader._loaded_plugins
        
        # Unload plugin
        loader.unload_plugin("test_plugin")
        
        assert "test_plugin" not in loader._loaded_plugins
        assert not plugin.is_initialized
    
    def test_reload_plugin(self):
        """Test reloading a plugin."""
        loader = PluginLoader(auto_discover=False)
        loader._plugin_classes["test_plugin"] = MockPluginForLoading
        
        # Load plugin
        plugin1 = loader.load_plugin("test_plugin")
        
        # Reload plugin
        plugin2 = loader.reload_plugin("test_plugin")
        
        assert plugin2 is not plugin1
        assert plugin2.is_initialized
        assert "test_plugin" in loader._loaded_plugins
    
    def test_load_all_discovered(self):
        """Test loading all discovered plugins."""
        loader = PluginLoader(auto_discover=False)
        
        # Add multiple plugin classes
        loader._plugin_classes["plugin1"] = MockPluginForLoading
        loader._plugin_classes["plugin2"] = type(
            'Plugin2',
            (MockPluginForLoading,),
            {'name': 'plugin2'}
        )
        
        # Load all
        loaded = loader.load_all_discovered()
        
        assert len(loaded) == 2
        assert "plugin1" in loaded
        assert "plugin2" in loaded
    
    def test_get_plugin_info(self):
        """Test getting plugin info."""
        loader = PluginLoader(auto_discover=False)
        loader._plugin_classes["test_plugin"] = MockPluginForLoading
        
        # Get info for unloaded plugin
        info = loader.get_plugin_info("test_plugin")
        
        assert info is not None
        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        
        # Get info for loaded plugin
        loader.load_plugin("test_plugin")
        info2 = loader.get_plugin_info("test_plugin")
        
        assert info2 is not None
        assert info2.name == "test_plugin"
    
    def test_list_plugins(self):
        """Test listing plugins."""
        loader = PluginLoader(auto_discover=False)
        
        # Add plugin classes
        loader._plugin_classes["plugin1"] = MockPluginForLoading
        loader._plugin_classes["plugin2"] = type(
            'Plugin2',
            (MockPluginForLoading,),
            {'name': 'plugin2', 'version': '2.0.0'}
        )
        
        # Load one plugin
        loader.load_plugin("plugin1")
        
        # List all plugins
        all_plugins = loader.list_plugins()
        
        assert len(all_plugins) == 2
        
        plugin1_info = next(p for p in all_plugins if p["name"] == "plugin1")
        assert plugin1_info["loaded"] is True
        
        plugin2_info = next(p for p in all_plugins if p["name"] == "plugin2")
        assert plugin2_info["loaded"] is False
        
        # List loaded only
        loaded_only = loader.list_plugins(loaded_only=True)
        
        assert len(loaded_only) == 1
        assert loaded_only[0]["name"] == "plugin1"


class TestGlobalFunctions:
    """Test global plugin loader functions."""
    
    def test_get_plugin_loader(self):
        """Test getting global plugin loader."""
        loader1 = get_plugin_loader()
        loader2 = get_plugin_loader()
        
        assert loader1 is loader2  # Should be singleton
    
    def test_load_plugin_global(self):
        """Test loading plugin via global function."""
        # Add test plugin to global loader
        loader = get_plugin_loader()
        loader._plugin_classes["test_global"] = type(
            'GlobalPlugin',
            (MockPluginForLoading,),
            {'name': 'test_global'}
        )
        
        plugin = load_plugin("test_global")
        
        assert plugin is not None
        assert plugin.name == "test_global"
    
    def test_discover_plugins_global(self):
        """Test discovering plugins via global function."""
        # Just test that it runs without error
        discovered = discover_plugins()
        
        assert isinstance(discovered, list)


class TestPluginLoadingEdgeCases:
    """Test edge cases in plugin loading."""
    
    def test_plugin_with_dependencies(self, tmp_path):
        """Test loading plugin with module dependencies."""
        loader = PluginLoader(auto_discover=False)
        
        # Create a module that the plugin depends on
        dep_file = tmp_path / "dependency.py"
        dep_file.write_text("""
def helper_function():
    return "helper"
""")
        
        # Create plugin that uses the dependency
        plugin_file = tmp_path / "dependent_plugin.py"
        plugin_file.write_text("""
from dependency import helper_function
from agenticraft.plugins.base import BasePlugin, PluginInfo

class DependentPlugin(BasePlugin):
    name = "dependent"
    
    def get_info(self):
        return PluginInfo(
            name=self.name,
            version="1.0.0",
            description=f"Uses {helper_function()}"
        )
""")
        
        # Add directory to sys.path temporarily
        sys.path.insert(0, str(tmp_path))
        
        try:
            discovered = loader.discover_in_directory(tmp_path)
            assert "dependent" in discovered
            
            # Load and check
            plugin = loader.load_plugin("dependent")
            info = plugin.get_info()
            assert "helper" in info.description
            
        finally:
            # Clean up sys.path
            sys.path.remove(str(tmp_path))
    
    def test_plugin_name_collision(self):
        """Test handling plugin name collisions."""
        loader = PluginLoader(auto_discover=False)
        
        # Add first plugin
        loader._plugin_classes["collision"] = MockPluginForLoading
        
        # Try to add another with same name
        class CollisionPlugin(BasePlugin):
            name = "collision"
            
            def get_info(self):
                return PluginInfo(name=self.name, version="2.0.0")
        
        # Second one should overwrite first
        loader._plugin_classes["collision"] = CollisionPlugin
        
        plugin = loader.load_plugin("collision")
        info = plugin.get_info()
        assert info.version == "2.0.0"
