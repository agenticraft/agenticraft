"""Tests for plugin registry."""

from unittest.mock import MagicMock, Mock

import pytest

from agenticraft.core.tool import BaseTool
from agenticraft.core.types import ToolDefinition
from agenticraft.plugins.base import BasePlugin, PluginInfo
from agenticraft.plugins.registry import (
    PluginDependencyError,
    PluginRegistry,
    get_all_plugin_tools,
    get_plugin_registry,
    register_plugin,
)


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, name: str):
        super().__init__(name=name, description=f"Mock {name} tool")

    async def arun(self, **kwargs):
        return {"tool": self.name}

    def get_definition(self):
        return ToolDefinition(
            name=self.name, description=self.description, parameters=[]
        )


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        provides_tools=None,
        provides_agents=None,
        provides_providers=None,
        depends_on=None,
    ):
        super().__init__()
        self.name = name
        self.version = version
        self._provides_tools = provides_tools or []
        self._provides_agents = provides_agents or []
        self._provides_providers = provides_providers or []
        self._depends_on = depends_on or []

    def get_info(self) -> PluginInfo:
        info = PluginInfo(
            name=self.name,
            version=self.version,
            provides_tools=self._provides_tools,
            provides_agents=self._provides_agents,
            provides_providers=self._provides_providers,
        )
        # Add custom dependency attribute
        if self._depends_on:
            info.depends_on = self._depends_on
        return info

    def get_tools(self):
        return [MockTool(name) for name in self._provides_tools]


class TestPluginRegistry:
    """Test PluginRegistry functionality."""

    def test_registry_creation(self):
        """Test creating a plugin registry."""
        registry = PluginRegistry()

        assert registry._plugins == {}
        assert registry._plugin_info == {}
        assert len(registry._tools_index) == 0
        assert len(registry._agents_index) == 0
        assert len(registry._providers_index) == 0

    def test_register_plugin(self):
        """Test registering a plugin."""
        registry = PluginRegistry()
        plugin = MockPlugin("test", provides_tools=["tool1", "tool2"])

        registry.register(plugin)

        assert "test" in registry._plugins
        assert registry._plugins["test"] == plugin
        assert "test" in registry._plugin_info
        assert "test" in registry._load_order

    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin."""
        registry = PluginRegistry()
        plugin1 = MockPlugin("test")
        plugin2 = MockPlugin("test")

        registry.register(plugin1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(plugin2)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        plugin = MockPlugin("test", provides_tools=["tool1"])

        registry.register(plugin)
        assert "test" in registry._plugins

        registry.unregister(plugin)

        assert "test" not in registry._plugins
        assert "test" not in registry._plugin_info
        assert "test" not in registry._load_order

    def test_capability_indexes(self):
        """Test capability indexing."""
        registry = PluginRegistry()

        plugin1 = MockPlugin(
            "plugin1",
            provides_tools=["tool1", "tool2"],
            provides_agents=["Agent1"],
            provides_providers=["provider1"],
        )

        plugin2 = MockPlugin(
            "plugin2",
            provides_tools=["tool2", "tool3"],
            provides_agents=["Agent2"],
            provides_providers=["provider2"],
        )

        registry.register(plugin1)
        registry.register(plugin2)

        # Check tool index
        assert len(registry._tools_index["tool1"]) == 1
        assert len(registry._tools_index["tool2"]) == 2
        assert len(registry._tools_index["tool3"]) == 1

        # Check agent index
        assert len(registry._agents_index["Agent1"]) == 1
        assert len(registry._agents_index["Agent2"]) == 1

        # Check provider index
        assert len(registry._providers_index["provider1"]) == 1
        assert len(registry._providers_index["provider2"]) == 1

    def test_get_plugin(self):
        """Test getting a plugin by name."""
        registry = PluginRegistry()
        plugin = MockPlugin("test")
        registry.register(plugin)

        retrieved = registry.get_plugin("test")
        assert retrieved == plugin

        none_plugin = registry.get_plugin("nonexistent")
        assert none_plugin is None

    def test_get_plugin_info(self):
        """Test getting plugin info."""
        registry = PluginRegistry()
        plugin = MockPlugin("test", version="2.0.0")
        registry.register(plugin)

        info = registry.get_plugin_info("test")
        assert info is not None
        assert info.name == "test"
        assert info.version == "2.0.0"

    def test_list_plugins(self):
        """Test listing all plugins."""
        registry = PluginRegistry()

        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")

        registry.register(plugin1)
        registry.register(plugin2)

        plugins = registry.list_plugins()

        assert len(plugins) == 2
        names = [p.name for p in plugins]
        assert "plugin1" in names
        assert "plugin2" in names

    def test_get_plugins_by_capability(self):
        """Test getting plugins by capability."""
        registry = PluginRegistry()

        tool_plugin = MockPlugin("tools", provides_tools=["t1", "t2"])
        agent_plugin = MockPlugin("agents", provides_agents=["A1"])
        both_plugin = MockPlugin("both", provides_tools=["t3"], provides_agents=["A2"])

        registry.register(tool_plugin)
        registry.register(agent_plugin)
        registry.register(both_plugin)

        # Get tool plugins
        tool_plugins = registry.get_plugins_by_capability("tools")
        assert len(tool_plugins) == 2
        assert tool_plugin in tool_plugins
        assert both_plugin in tool_plugins

        # Get agent plugins
        agent_plugins = registry.get_plugins_by_capability("agents")
        assert len(agent_plugins) == 2
        assert agent_plugin in agent_plugins
        assert both_plugin in agent_plugins

    def test_get_all_tools(self):
        """Test getting all tools from plugins."""
        registry = PluginRegistry()

        plugin1 = MockPlugin("p1", provides_tools=["tool1", "tool2"])
        plugin2 = MockPlugin("p2", provides_tools=["tool3"])

        registry.register(plugin1)
        registry.register(plugin2)

        tools = registry.get_all_tools()

        assert len(tools) == 3
        assert "tool1" in tools
        assert "tool2" in tools
        assert "tool3" in tools
        assert all(isinstance(t, BaseTool) for t in tools.values())

    def test_get_all_agents(self):
        """Test getting all agents from plugins."""
        registry = PluginRegistry()

        # Create mock agent classes
        Agent1 = type("Agent1", (), {})
        Agent2 = type("Agent2", (), {})

        plugin1 = MockPlugin("p1", provides_agents=["Agent1"])
        plugin1.get_agents = lambda: [Agent1]

        plugin2 = MockPlugin("p2", provides_agents=["Agent2"])
        plugin2.get_agents = lambda: [Agent2]

        registry.register(plugin1)
        registry.register(plugin2)

        agents = registry.get_all_agents()

        assert len(agents) == 2
        assert "Agent1" in agents
        assert "Agent2" in agents
        assert agents["Agent1"] == Agent1
        assert agents["Agent2"] == Agent2

    def test_enhance_agent(self):
        """Test enhancing agent with all plugins."""
        registry = PluginRegistry()

        # Create mock agent
        agent = MagicMock()
        agent.name = "TestAgent"

        # Create plugins that enhance agents
        plugin1 = MockPlugin("enhancer1")
        plugin1.enhance_agent = Mock(return_value=agent)

        plugin2 = MockPlugin("enhancer2")
        plugin2.enhance_agent = Mock(return_value=agent)

        registry.register(plugin1)
        registry.register(plugin2)

        # Enhance agent
        enhanced = registry.enhance_agent(agent)

        assert enhanced == agent
        plugin1.enhance_agent.assert_called_once_with(agent)
        plugin2.enhance_agent.assert_called_once_with(agent)

    def test_plugin_dependencies(self):
        """Test plugin dependency tracking."""
        registry = PluginRegistry()

        # Create plugins with dependencies
        plugin1 = MockPlugin("base")
        plugin2 = MockPlugin("dependent", depends_on=["base"])
        plugin3 = MockPlugin("multi_dep", depends_on=["base", "dependent"])

        registry.register(plugin1)
        registry.register(plugin2)
        registry.register(plugin3)

        # Check dependencies
        assert "base" in registry._dependencies["dependent"]
        assert "base" in registry._dependencies["multi_dep"]
        assert "dependent" in registry._dependencies["multi_dep"]

        # Check dependents
        assert "dependent" in registry._dependents["base"]
        assert "multi_dep" in registry._dependents["base"]
        assert "multi_dep" in registry._dependents["dependent"]

    def test_initialization_order(self):
        """Test getting initialization order with dependencies."""
        registry = PluginRegistry()

        # Create dependency chain: p3 -> p2 -> p1
        plugin1 = MockPlugin("p1")
        plugin2 = MockPlugin("p2", depends_on=["p1"])
        plugin3 = MockPlugin("p3", depends_on=["p2"])

        # Register in reverse order
        registry.register(plugin3)
        registry.register(plugin2)
        registry.register(plugin1)

        order = registry._get_initialization_order()

        # p1 should come before p2, p2 before p3
        assert order.index("p1") < order.index("p2")
        assert order.index("p2") < order.index("p3")

    def test_circular_dependency(self):
        """Test detecting circular dependencies."""
        registry = PluginRegistry()

        # Create circular dependency: p1 -> p2 -> p3 -> p1
        plugin1 = MockPlugin("p1", depends_on=["p3"])
        plugin2 = MockPlugin("p2", depends_on=["p1"])
        plugin3 = MockPlugin("p3", depends_on=["p2"])

        registry.register(plugin1)
        registry.register(plugin2)
        registry.register(plugin3)

        with pytest.raises(PluginDependencyError, match="Circular dependency"):
            registry._get_initialization_order()

    def test_validate_dependencies(self):
        """Test validating plugin dependencies."""
        registry = PluginRegistry()

        # Register plugin with unmet dependency
        plugin = MockPlugin("dependent", depends_on=["missing"])
        registry.register(plugin)

        missing = registry.validate_dependencies()

        assert len(missing) == 1
        assert "dependent requires missing" in missing[0]

    def test_initialize_all(self):
        """Test initializing all plugins."""
        registry = PluginRegistry()

        plugin1 = MockPlugin("p1")
        plugin1.initialize = Mock()

        plugin2 = MockPlugin("p2", depends_on=["p1"])
        plugin2.initialize = Mock()

        registry.register(plugin1)
        registry.register(plugin2)

        registry.initialize_all()

        # Both should be initialized
        plugin1.initialize.assert_called_once()
        plugin2.initialize.assert_called_once()

        # Check tracking
        assert "p1" in registry._initialized_plugins
        assert "p2" in registry._initialized_plugins

    def test_cleanup_all(self):
        """Test cleaning up all plugins."""
        registry = PluginRegistry()

        plugin1 = MockPlugin("p1")
        plugin1.cleanup = Mock()

        plugin2 = MockPlugin("p2")
        plugin2.cleanup = Mock()

        registry.register(plugin1)
        registry.register(plugin2)
        registry.initialize_all()

        registry.cleanup_all()

        # Both should be cleaned up
        plugin1.cleanup.assert_called_once()
        plugin2.cleanup.assert_called_once()

        # Check tracking
        assert "p1" not in registry._initialized_plugins
        assert "p2" not in registry._initialized_plugins

    def test_get_plugin_stats(self):
        """Test getting plugin statistics."""
        registry = PluginRegistry()

        plugin1 = MockPlugin("p1", provides_tools=["t1", "t2"], provides_agents=["A1"])

        plugin2 = MockPlugin(
            "p2", provides_tools=["t3"], provides_providers=["prov1"], depends_on=["p1"]
        )

        registry.register(plugin1)
        registry.register(plugin2)
        registry.initialize_all()

        stats = registry.get_plugin_stats()

        assert stats["total_plugins"] == 2
        assert stats["initialized_plugins"] == 2
        assert stats["total_tools"] == 3
        assert stats["total_agents"] == 1
        assert stats["total_providers"] == 1
        assert stats["plugins_with_dependencies"] == 1
        assert stats["missing_dependencies"] == 0

    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = PluginRegistry()

        plugin = MockPlugin("test")
        plugin.cleanup = Mock()

        registry.register(plugin)
        registry.initialize_all()

        registry.clear()

        # Everything should be cleared
        assert len(registry._plugins) == 0
        assert len(registry._plugin_info) == 0
        assert len(registry._initialized_plugins) == 0
        plugin.cleanup.assert_called_once()


class TestGlobalRegistryFunctions:
    """Test global registry functions."""

    def test_get_plugin_registry(self):
        """Test getting global registry."""
        registry1 = get_plugin_registry()
        registry2 = get_plugin_registry()

        assert registry1 is registry2  # Singleton

    def test_register_plugin_global(self):
        """Test registering plugin globally."""
        plugin = MockPlugin("global_test")

        register_plugin(plugin)

        registry = get_plugin_registry()
        assert registry.get_plugin("global_test") == plugin

    def test_get_all_plugin_tools_global(self):
        """Test getting all tools globally."""
        plugin = MockPlugin("tool_provider", provides_tools=["global_tool"])

        registry = get_plugin_registry()
        registry.clear()  # Clear any existing plugins
        registry.register(plugin)

        tools = get_all_plugin_tools()

        assert "global_tool" in tools
