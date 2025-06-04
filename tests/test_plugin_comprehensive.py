"""Comprehensive tests for plugin module to achieve >95% coverage."""

from typing import Any, Dict, Optional
from unittest.mock import Mock, MagicMock

import pytest

from agenticraft.core.plugin import (
    BasePlugin, PluginInfo, PluginRegistry,
    register_plugin, get_global_registry,
    LoggingPlugin, MetricsPlugin,
    PluginConfig, PluginLifecycle
)


class TestPluginInfo:
    """Test PluginInfo."""
    
    def test_plugin_info_basic(self):
        """Test basic plugin info."""
        info = PluginInfo(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin"
        )
        
        assert info.name == "test-plugin"
        assert info.version == "1.0.0"
        assert info.description == "Test plugin"
        assert info.author is None
        assert info.requires_plugins == []
        assert info.requires_packages == []
    
    def test_plugin_info_full(self):
        """Test full plugin info."""
        info = PluginInfo(
            name="advanced-plugin",
            version="2.1.0",
            description="An advanced plugin",
            author="Test Author",
            author_email="test@example.com",
            requires_packages=["agenticraft>=0.1.0", "requests>=2.0"],
            config_schema={"api_key": "string", "timeout": "integer"}
        )
        
        assert info.name == "advanced-plugin"
        assert info.version == "2.1.0"
        assert info.description == "An advanced plugin"
        assert info.author == "Test Author"
        assert info.author_email == "test@example.com"
        assert len(info.requires_packages) == 2
        assert info.config_schema["timeout"] == "integer"


class TestBasePlugin:
    """Test BasePlugin base class."""
    
    def test_plugin_initialization(self):
        """Test basic plugin initialization."""
        class TestPlugin(BasePlugin):
            name = "test_plugin"
            version = "1.0.0"
            description = "Test plugin"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(name=self.name, version=self.version, description=self.description)
        
        plugin = TestPlugin()
        
        assert plugin.config.enabled is True
        assert plugin.state == PluginLifecycle.CREATED
        assert plugin.context is None
    
    def test_plugin_with_config(self):
        """Test plugin with configuration."""
        config = PluginConfig(enabled=False, config={"api_key": "test", "debug": True})
        
        class TestPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestPlugin(config=config)
        
        assert plugin.config.enabled is False
        assert plugin.config.config["api_key"] == "test"
        assert plugin.config.config["debug"] is True
    
    def test_plugin_lifecycle(self):
        """Test plugin lifecycle methods."""
        class TestPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestPlugin()
        
        assert plugin.state == PluginLifecycle.CREATED
        
        plugin.initialize()
        assert plugin.state == PluginLifecycle.INITIALIZED
        
        plugin.start()
        assert plugin.state == PluginLifecycle.STARTED
        
        plugin.stop()
        assert plugin.state == PluginLifecycle.STOPPED
        
        plugin.cleanup()
        assert plugin.state == PluginLifecycle.DESTROYED
    
    def test_plugin_hooks_default_implementation(self):
        """Test that hook methods have default no-op implementations."""
        class TestPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestPlugin()
        
        # All hooks should exist and do nothing
        plugin.on_agent_created(Mock())
        plugin.on_agent_run_start(Mock(), "prompt", {})
        plugin.on_agent_run_complete(Mock(), Mock())
        plugin.on_agent_error(Mock(), Exception())
        plugin.on_tool_registered("tool", Mock())
        plugin.on_tool_execution_start("tool", {})
        plugin.on_tool_execution_complete("tool", "result")
        plugin.on_tool_error("tool", Exception())
        plugin.on_workflow_created(Mock())
        plugin.on_workflow_start(Mock(), {})
        plugin.on_workflow_complete(Mock(), Mock())
        plugin.on_workflow_step_complete(Mock(), "step", "result")
        
        # Response hooks
        response = Mock(content="test")
        assert plugin.on_response_generated(response) == response
        assert plugin.on_reasoning_complete("reasoning") == "reasoning"
    
    def test_custom_plugin_implementation(self):
        """Test creating a custom plugin."""
        class CustomPlugin(BasePlugin):
            name = "custom"
            version = "2.0.0"
            description = "Custom plugin"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            def on_agent_created(self, agent):
                self.agent_created = True
                self.created_agent = agent
            
            def on_response_generated(self, response):
                # Modify response
                response.modified = True
                return response
        
        plugin = CustomPlugin()
        
        # Test metadata
        info = plugin.get_info()
        assert info.name == "custom"
        assert info.version == "2.0.0"
        
        # Test hooks
        mock_agent = Mock()
        plugin.on_agent_created(mock_agent)
        assert plugin.agent_created is True
        assert plugin.created_agent == mock_agent
        
        # Test response modification
        response = Mock()
        modified = plugin.on_response_generated(response)
        assert modified.modified is True


class TestPluginRegistry:
    """Test PluginRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create a fresh plugin registry."""
        registry = PluginRegistry()
        registry.clear()
        return registry
    
    def make_test_plugin(self, name="test"):
        """Helper to create a test plugin."""
        class TestPlugin(BasePlugin):
            plugin_name = name
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.plugin_name,
                    version="1.0.0",
                    description="Test plugin"
                )
        
        return TestPlugin()
    
    def test_registry_initialization(self, registry):
        """Test registry is initialized empty."""
        assert registry.get_plugins() == []
    
    def test_register_plugin(self, registry):
        """Test registering a plugin."""
        class TestPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestPlugin()
        registry.register(plugin)
        
        plugins = registry.get_plugins()
        assert len(plugins) == 1
        assert plugin in plugins
    
    def test_register_multiple_plugins(self, registry):
        """Test registering multiple plugins."""
        plugin1 = self.make_test_plugin("plugin1")
        plugin2 = LoggingPlugin()
        plugin3 = MetricsPlugin()
        
        registry.register(plugin1)
        registry.register(plugin2)
        registry.register(plugin3)
        
        plugins = registry.get_plugins()
        assert len(plugins) == 3
        assert all(p in plugins for p in [plugin1, plugin2, plugin3])
    
    def test_unregister_plugin(self, registry):
        """Test unregistering a plugin."""
        plugin = self.make_test_plugin()
        registry.register(plugin)
        
        assert plugin in registry.get_plugins()
        
        registry.unregister(plugin)
        assert plugin not in registry.get_plugins()
    
    def test_unregister_nonexistent(self, registry):
        """Test unregistering non-existent plugin doesn't error."""
        plugin = self.make_test_plugin()
        # Should not raise
        registry.unregister(plugin)
    
    def test_get_plugins_returns_copy(self, registry):
        """Test get_plugins returns a copy of the list."""
        plugin = self.make_test_plugin()
        registry.register(plugin)
        
        plugins = registry.get_plugins()
        plugins.append(self.make_test_plugin("another"))  # Modify returned list
        
        # Original should be unchanged
        assert len(registry.get_plugins()) == 1
    
    def test_clear_registry(self, registry):
        """Test clearing all plugins."""
        registry.register(self.make_test_plugin("plugin1"))
        registry.register(LoggingPlugin())
        
        assert len(registry.get_plugins()) == 2
        
        registry.clear()
        assert len(registry.get_plugins()) == 0
    
    def test_emit_agent_created(self, registry):
        """Test emitting agent created event."""
        class TrackingPlugin(BasePlugin):
            def __init__(self):
                super().__init__()
                self.agents = []
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="tracking", version="1.0.0", description="Test")
            
            def on_agent_created(self, agent):
                self.agents.append(agent)
        
        plugin = TrackingPlugin()
        registry.register(plugin)
        
        mock_agent = Mock()
        registry.emit_agent_created(mock_agent)
        
        assert len(plugin.agents) == 1
        assert plugin.agents[0] == mock_agent
    
    def test_emit_agent_run_start(self, registry):
        """Test emitting agent run start event."""
        class TrackingPlugin(BasePlugin):
            def __init__(self):
                super().__init__()
                self.runs = []
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="tracking", version="1.0.0", description="Test")
            
            def on_agent_run_start(self, agent, prompt, context):
                self.runs.append((agent, prompt, context))
        
        plugin = TrackingPlugin()
        registry.register(plugin)
        
        mock_agent = Mock()
        registry.emit_agent_run_start(mock_agent, "test prompt", {"key": "value"})
        
        assert len(plugin.runs) == 1
        assert plugin.runs[0] == (mock_agent, "test prompt", {"key": "value"})
    
    def test_emit_agent_run_complete(self, registry):
        """Test emitting agent run complete event."""
        class TrackingPlugin(BasePlugin):
            def __init__(self):
                super().__init__()
                self.completions = []
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="tracking", version="1.0.0", description="Test")
            
            def on_agent_run_complete(self, agent, response):
                self.completions.append((agent, response))
        
        plugin = TrackingPlugin()
        registry.register(plugin)
        
        mock_agent = Mock()
        mock_response = Mock()
        registry.emit_agent_run_complete(mock_agent, mock_response)
        
        assert len(plugin.completions) == 1
        assert plugin.completions[0] == (mock_agent, mock_response)
    
    def test_emit_response_generated(self, registry):
        """Test emitting response generated event with modification."""
        class ModifyingPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="modifier1", version="1.0.0", description="Test")
            
            def on_response_generated(self, response):
                response.modified_by_1 = True
                return response
        
        class AnotherModifyingPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="modifier2", version="1.0.0", description="Test")
            
            def on_response_generated(self, response):
                response.modified_by_2 = True
                return response
        
        registry.register(ModifyingPlugin())
        registry.register(AnotherModifyingPlugin())
        
        response = Mock()
        modified = registry.emit_response_generated(response)
        
        # Both plugins should have modified it
        assert modified.modified_by_1 is True
        assert modified.modified_by_2 is True
    
    def test_exception_handling_in_hooks(self, registry):
        """Test that exceptions in plugins don't break the system."""
        class FailingPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="failing", version="1.0.0", description="Test")
            
            def on_agent_created(self, agent):
                raise ValueError("Plugin error")
        
        class WorkingPlugin(BasePlugin):
            def __init__(self):
                super().__init__()
                self.called = False
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="working", version="1.0.0", description="Test")
            
            def on_agent_created(self, agent):
                self.called = True
        
        failing = FailingPlugin()
        working = WorkingPlugin()
        
        registry.register(failing)
        registry.register(working)
        
        # Should not raise
        registry.emit_agent_created(Mock())
        
        # Working plugin should still be called
        assert working.called is True


class TestLoggingPlugin:
    """Test LoggingPlugin built-in plugin."""
    
    def test_logging_plugin_metadata(self):
        """Test LoggingPlugin metadata."""
        plugin = LoggingPlugin()
        info = plugin.get_info()
        
        assert info.name == "logging_plugin"
        assert info.version == "1.0.0"
        assert "debugging" in info.description
    
    def test_logging_plugin_hooks(self, capsys):
        """Test LoggingPlugin hooks print output."""
        plugin = LoggingPlugin()
        
        # Test agent created
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent.id = "123"
        plugin.on_agent_created(mock_agent)
        
        captured = capsys.readouterr()
        assert "[LoggingPlugin] Agent created: TestAgent (ID: 123)" in captured.out
        
        # Test agent run start
        plugin.on_agent_run_start(mock_agent, "This is a long prompt that should be truncated", {})
        
        captured = capsys.readouterr()
        assert "[LoggingPlugin] Agent TestAgent starting with prompt:" in captured.out
        assert "This is a long prompt that should be truncated..." in captured.out
        
        # Test tool execution
        plugin.on_tool_execution_start("calculator", {"a": 1, "b": 2})
        
        captured = capsys.readouterr()
        assert "[LoggingPlugin] Executing tool calculator" in captured.out
        assert "{'a': 1, 'b': 2}" in captured.out


class TestMetricsPlugin:
    """Test MetricsPlugin built-in plugin."""
    
    def test_metrics_plugin_initialization(self):
        """Test MetricsPlugin initialization."""
        plugin = MetricsPlugin()
        
        assert plugin.metrics["agent_runs"] == 0
        assert plugin.metrics["tool_executions"] == 0
        assert plugin.metrics["errors"] == 0
        assert plugin.metrics["total_response_length"] == 0
    
    def test_metrics_plugin_metadata(self):
        """Test MetricsPlugin metadata."""
        plugin = MetricsPlugin()
        info = plugin.get_info()
        
        assert info.name == "metrics_plugin"
        assert info.version == "1.0.0"
        assert "metrics" in info.description
    
    def test_metrics_plugin_tracks_agent_runs(self):
        """Test tracking agent runs."""
        plugin = MetricsPlugin()
        
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.content = "Hello world"
        
        plugin.on_agent_run_complete(mock_agent, mock_response)
        
        assert plugin.metrics["agent_runs"] == 1
        assert plugin.metrics["total_response_length"] == len("Hello world")
        
        # Another run
        mock_response2 = Mock()
        mock_response2.content = "Longer response text"
        plugin.on_agent_run_complete(mock_agent, mock_response2)
        
        assert plugin.metrics["agent_runs"] == 2
        assert plugin.metrics["total_response_length"] == len("Hello world") + len("Longer response text")
    
    def test_metrics_plugin_tracks_tool_executions(self):
        """Test tracking tool executions."""
        plugin = MetricsPlugin()
        
        plugin.on_tool_execution_complete("calculator", {"result": 42})
        plugin.on_tool_execution_complete("web_search", ["result1", "result2"])
        
        assert plugin.metrics["tool_executions"] == 2
    
    def test_metrics_plugin_tracks_errors(self):
        """Test tracking errors."""
        plugin = MetricsPlugin()
        
        mock_agent = Mock()
        plugin.on_agent_error(mock_agent, ValueError("Test error"))
        plugin.on_agent_error(mock_agent, RuntimeError("Another error"))
        
        assert plugin.metrics["errors"] == 2
    
    def test_get_metrics_returns_copy(self):
        """Test get_metrics returns a copy."""
        plugin = MetricsPlugin()
        
        mock_resp = Mock()
        mock_resp.content = "test"
        plugin.on_agent_run_complete(Mock(), mock_resp)
        
        metrics = plugin.get_metrics()
        metrics["agent_runs"] = 999  # Modify returned dict
        
        # Original should be unchanged
        assert plugin.metrics["agent_runs"] == 1


class TestGlobalRegistry:
    """Test global registry functions."""
    
    def test_register_plugin_globally(self):
        """Test registering plugin to global registry."""
        # Clear global registry first
        get_global_registry().clear()
        
        class TestPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestPlugin()
        register_plugin(plugin)
        
        global_registry = get_global_registry()
        assert plugin in global_registry.get_plugins()
    
    def test_get_global_registry_returns_same_instance(self):
        """Test global registry is singleton."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        
        assert registry1 is registry2


class TestPluginIntegration:
    """Integration tests for plugin system."""
    
    def test_multiple_plugins_interaction(self):
        """Test multiple plugins working together."""
        registry = PluginRegistry()
        registry.clear()
        
        # Add logging and metrics plugins
        logging_plugin = LoggingPlugin()
        metrics_plugin = MetricsPlugin()
        
        registry.register(logging_plugin)
        registry.register(metrics_plugin)
        
        # Simulate agent lifecycle
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent.id = "123"
        registry.emit_agent_created(mock_agent)
        
        registry.emit_agent_run_start(mock_agent, "Test prompt", {})
        
        mock_response = Mock()
        mock_response.content = "This is the response"
        registry.emit_agent_run_complete(mock_agent, mock_response)
        
        # Check metrics were updated
        assert metrics_plugin.metrics["agent_runs"] == 1
        assert metrics_plugin.metrics["total_response_length"] == len("This is the response")
    
    def test_plugin_response_modification_chain(self):
        """Test chaining response modifications."""
        registry = PluginRegistry()
        registry.clear()
        
        class PrefixPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="prefix", version="1.0.0", description="Test")
            
            def on_response_generated(self, response):
                response.content = "[PREFIX] " + response.content
                return response
        
        class SuffixPlugin(BasePlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(name="suffix", version="1.0.0", description="Test")
            
            def on_response_generated(self, response):
                response.content = response.content + " [SUFFIX]"
                return response
        
        registry.register(PrefixPlugin())
        registry.register(SuffixPlugin())
        
        response = Mock()
        response.content = "Original"
        modified = registry.emit_response_generated(response)
        
        assert modified.content == "[PREFIX] Original [SUFFIX]"
    
    def test_plugin_with_configuration(self):
        """Test plugin using configuration."""
        class ConfigurablePlugin(BasePlugin):
            def __init__(self, config_dict=None):
                # Create PluginConfig from dict
                if config_dict:
                    plugin_config = PluginConfig(config=config_dict)
                else:
                    plugin_config = PluginConfig(config={"threshold": 10, "enabled": True})
                super().__init__(config=plugin_config)
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name="configurable",
                    version="1.0.0",
                    description="Configurable plugin"
                )
            
            def on_agent_run_complete(self, agent, response):
                if self.config.config.get("enabled", True):
                    threshold = self.config.config.get("threshold", 10)
                    if len(response.content) > threshold:
                        response.flagged = True
        
        # Test with default config
        plugin1 = ConfigurablePlugin()
        response1 = Mock(spec=['content'])  # Use spec to control Mock attributes
        response1.content = "Short"
        plugin1.on_agent_run_complete(Mock(), response1)
        assert not hasattr(response1, "flagged")
        
        # Test with long content
        response1_long = Mock(spec=['content'])
        response1_long.content = "This is a longer text"
        plugin1.on_agent_run_complete(Mock(), response1_long)
        assert hasattr(response1_long, "flagged") and response1_long.flagged
        
        # Test with custom config
        plugin2 = ConfigurablePlugin(config_dict={"threshold": 5})
        response2 = Mock(spec=['content'])
        response2.content = "Longer text"
        plugin2.on_agent_run_complete(Mock(), response2)
        assert hasattr(response2, "flagged") and response2.flagged
        
        # Test with disabled
        plugin3 = ConfigurablePlugin(config_dict={"enabled": False})
        response3 = Mock(spec=['content'])
        response3.content = "Very long text that exceeds threshold"
        plugin3.on_agent_run_complete(Mock(), response3)
        assert not hasattr(response3, "flagged")
