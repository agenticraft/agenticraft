"""Integration tests for plugin system examples."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPluginIntegration:
    """Test plugin system integration."""
    
    @pytest.mark.integration
    def test_weather_plugin_loading(self):
        """Test loading the weather plugin example."""
        from agenticraft.core.plugin import PluginRegistry, register_plugin, get_global_registry
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Clear any existing plugins
        registry = get_global_registry()
        registry.clear()
        
        # Create and register plugin
        plugin = WeatherPlugin()
        register_plugin(plugin)
        
        # Verify plugin is registered
        plugins = registry.get_plugins()
        assert len(plugins) == 1
        assert plugins[0].name == "weather"
        
        # Get plugin info
        info = plugins[0].get_info()
        assert info.name == "weather"
        assert info.version == "1.0.0"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weather_plugin_functionality(self):
        """Test weather plugin functionality."""
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Create plugin
        plugin = WeatherPlugin()
        
        # Initialize plugin
        plugin.initialize()  # Use sync method instead of async
        
        # Get tools from plugin
        tools = plugin.get_tools()
        assert len(tools) > 0
        
        # Test the weather tool functionality
        # Note: The actual tool implementation depends on the weather_plugin.py
        # This test assumes it returns a list of tool instances
        if tools:
            weather_tool = tools[0]
            
            # Mock any external API calls if the tool makes them
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "temperature": 72,
                    "condition": "sunny",
                    "humidity": 65
                }
                mock_get.return_value = mock_response
                
                # Test tool execution
                if hasattr(weather_tool, 'arun'):
                    result = await weather_tool.arun(location="San Francisco")
                    assert "temperature" in result or "location" in result
        
        # Cleanup
        plugin.cleanup()  # Use sync method
    
    @pytest.mark.integration
    def test_plugin_with_agent(self):
        """Test plugin integration with agent."""
        from agenticraft.core.agent import Agent
        from agenticraft.core.plugin import get_global_registry, register_plugin
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Clear registry
        registry = get_global_registry()
        registry.clear()
        
        # Create agent
        agent = Agent(
            name="Weather Bot",
            instructions="Provide weather information"
        )
        
        # Create and register plugin
        plugin = WeatherPlugin()
        register_plugin(plugin)
        
        # Emit agent created event
        registry.emit_agent_created(agent)
        
        # Plugin should have received the event
        # (actual behavior depends on weather_plugin implementation)
    
    @pytest.mark.integration
    def test_plugin_configuration(self):
        """Test plugin configuration."""
        from agenticraft.plugins import PluginConfig  # Use the correct import
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Test with custom config
        config = PluginConfig(
            enabled=True,
            config={
                "api_key": "test-key-123",
                "timeout": 30,
                "cache_ttl": 300
            }
        )
        
        plugin = WeatherPlugin(config=config)
        
        # Verify configuration
        assert plugin.config.enabled is True
        assert plugin.config.config["api_key"] == "test-key-123"
        assert plugin.config.config["timeout"] == 30
    
    @pytest.mark.integration
    def test_plugin_events(self):
        """Test plugin event system."""
        from agenticraft.core.plugin import get_global_registry, register_plugin, BasePlugin, PluginInfo
        from agenticraft.core.agent import Agent, AgentResponse
        from uuid import uuid4
        
        # Track events
        events_received = []
        
        class EventTrackingPlugin(BasePlugin):
            name = "event_tracker"
            version = "1.0.0"
            description = "Tracks events"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            def on_agent_created(self, agent: Agent) -> None:
                events_received.append(("agent_created", agent.name))
            
            def on_agent_run_complete(self, agent: Agent, response: AgentResponse) -> None:
                events_received.append(("agent_run_complete", response.content))
        
        # Clear and setup
        registry = get_global_registry()
        registry.clear()
        
        # Register tracking plugin
        tracker = EventTrackingPlugin()
        register_plugin(tracker)
        
        # Create agent and emit events
        agent = Agent(name="Test Agent")
        registry.emit_agent_created(agent)
        
        # Create a mock response and emit completion
        response = AgentResponse(content="Test response", agent_id=uuid4())
        registry.emit_agent_run_complete(agent, response)
        
        # Verify events were tracked
        assert len(events_received) == 2
        assert events_received[0] == ("agent_created", "Test Agent")
        assert events_received[1] == ("agent_run_complete", "Test response")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_plugins(self):
        """Test multiple plugins working together."""
        from agenticraft.core.plugin import get_global_registry, register_plugin, BasePlugin, PluginInfo
        
        # Create custom test plugin
        class TestPlugin(BasePlugin):
            name = "test_plugin"
            version = "1.0.0"
            description = "Test plugin"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
        
        # Clear registry
        registry = get_global_registry()
        registry.clear()
        
        # Register multiple plugins
        from examples.plugins.weather_plugin import WeatherPlugin
        weather_plugin = WeatherPlugin()
        register_plugin(weather_plugin)
        
        # Register test plugin
        test_plugin = TestPlugin()
        register_plugin(test_plugin)
        
        # Verify both registered
        plugins = registry.get_plugins()
        plugin_names = [p.name for p in plugins]
        assert "weather" in plugin_names
        assert "test_plugin" in plugin_names
        
        # Initialize all plugins
        for plugin in plugins:
            plugin.initialize()  # Use sync method
        
        # Cleanup all plugins
        for plugin in plugins:
            plugin.cleanup()  # Use sync method


class TestPluginDevelopment:
    """Test plugin development utilities."""
    
    @pytest.mark.integration
    def test_plugin_template(self):
        """Test plugin template generation."""
        # This would test any plugin scaffolding tools
        # For now, verify the example follows the pattern
        
        from agenticraft.plugins import BasePlugin  # Use the correct import
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Check it's a proper plugin
        assert issubclass(WeatherPlugin, BasePlugin)
        
        # Check required attributes
        assert hasattr(WeatherPlugin, 'name')
        assert hasattr(WeatherPlugin, 'version')
        
        # Check required methods (inherited from BasePlugin)
        plugin = WeatherPlugin()
        assert hasattr(plugin, 'initialize')
        assert hasattr(plugin, 'get_tools')
        assert hasattr(plugin, 'cleanup')
        assert hasattr(plugin, 'get_info')
    
    @pytest.mark.integration
    def test_plugin_validation(self):
        """Test plugin validation."""
        from agenticraft.plugins import BasePlugin, PluginInfo  # Use the correct import
        
        # Test invalid plugin (missing required methods)
        class InvalidPlugin:
            name = "invalid"
            # Missing required methods
        
        # Should not be able to use as a plugin without inheriting from BasePlugin
        # In the current implementation, there's no explicit validation on registration
        # so we'll test that the plugin must inherit from BasePlugin
        assert not isinstance(InvalidPlugin(), BasePlugin)
        
        # Test valid plugin
        class ValidPlugin(BasePlugin):
            name = "valid"
            version = "1.0.0"
            description = "Valid plugin"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
        
        # Should be a valid plugin
        plugin = ValidPlugin()
        assert isinstance(plugin, BasePlugin)
        assert plugin.get_info().name == "valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
