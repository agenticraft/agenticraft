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
        from agenticraft.core.plugin import PluginManager
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Create plugin manager
        manager = PluginManager()
        
        # Create and register plugin
        plugin = WeatherPlugin()
        manager.register(plugin)
        
        # Verify plugin is registered
        assert "weather" in manager.list_plugins()
        
        # Get plugin back
        loaded_plugin = manager.get_plugin("weather")
        assert loaded_plugin is not None
        assert loaded_plugin.name == "weather"
        assert loaded_plugin.version == "1.0.0"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weather_plugin_functionality(self):
        """Test weather plugin functionality."""
        from examples.plugins.weather_plugin import WeatherPlugin, WeatherTool
        
        # Create plugin
        plugin = WeatherPlugin()
        
        # Initialize plugin
        await plugin.initialize()
        
        # Get tools from plugin
        tools = plugin.get_tools()
        assert len(tools) > 0
        assert any(tool.name == "get_weather" for tool in tools)
        
        # Test the weather tool
        weather_tool = tools[0]
        
        # Mock the API call
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "temperature": 72,
                "condition": "sunny",
                "humidity": 65
            }
            mock_get.return_value = mock_response
            
            # Test tool execution
            result = await weather_tool.execute(location="San Francisco")
            
            assert result["temperature"] == 72
            assert result["condition"] == "sunny"
        
        # Cleanup
        await plugin.cleanup()
    
    @pytest.mark.integration
    def test_plugin_with_agent(self):
        """Test plugin integration with agent."""
        from agenticraft.core.agent import Agent
        from agenticraft.core.plugin import PluginManager
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Create agent
        agent = Agent(
            name="Weather Bot",
            role="Provide weather information"
        )
        
        # Create and register plugin
        manager = PluginManager()
        plugin = WeatherPlugin()
        manager.register(plugin)
        
        # Attach plugin manager to agent
        agent.use_plugins(manager)
        
        # Verify tools are available
        available_tools = agent.list_tools()
        assert any("weather" in tool for tool in available_tools)
    
    @pytest.mark.integration
    def test_plugin_configuration(self):
        """Test plugin configuration."""
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Test with custom config
        config = {
            "api_key": "test-key-123",
            "timeout": 30,
            "cache_ttl": 300
        }
        
        plugin = WeatherPlugin(config=config)
        
        # Verify configuration
        assert plugin.config["api_key"] == "test-key-123"
        assert plugin.config["timeout"] == 30
        assert plugin.config["cache_ttl"] == 300
    
    @pytest.mark.integration
    def test_plugin_events(self):
        """Test plugin event system."""
        from agenticraft.core.plugin import PluginManager, PluginEvent
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Track events
        events_fired = []
        
        def event_handler(event: PluginEvent):
            events_fired.append(event)
        
        # Create manager with event handler
        manager = PluginManager()
        manager.on_event(event_handler)
        
        # Register plugin
        plugin = WeatherPlugin()
        manager.register(plugin)
        
        # Verify registration event
        assert len(events_fired) > 0
        assert events_fired[0].type == "plugin_registered"
        assert events_fired[0].plugin_name == "weather"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_plugins(self):
        """Test multiple plugins working together."""
        from agenticraft.core.plugin import PluginManager
        from agenticraft.core.agent import Agent
        
        # Create custom test plugin
        class TestPlugin:
            name = "test_plugin"
            version = "1.0.0"
            
            async def initialize(self):
                pass
            
            def get_tools(self):
                return []
            
            async def cleanup(self):
                pass
        
        # Create manager and register multiple plugins
        manager = PluginManager()
        
        # Register weather plugin
        from examples.plugins.weather_plugin import WeatherPlugin
        weather_plugin = WeatherPlugin()
        manager.register(weather_plugin)
        
        # Register test plugin
        test_plugin = TestPlugin()
        manager.register(test_plugin)
        
        # Verify both registered
        plugins = manager.list_plugins()
        assert "weather" in plugins
        assert "test_plugin" in plugins
        
        # Initialize all plugins
        await manager.initialize_all()
        
        # Cleanup all plugins
        await manager.cleanup_all()


class TestPluginDevelopment:
    """Test plugin development utilities."""
    
    @pytest.mark.integration
    def test_plugin_template(self):
        """Test plugin template generation."""
        # This would test any plugin scaffolding tools
        # For now, verify the example follows the pattern
        
        from examples.plugins.weather_plugin import WeatherPlugin
        
        # Check required attributes
        assert hasattr(WeatherPlugin, 'name')
        assert hasattr(WeatherPlugin, 'version')
        assert hasattr(WeatherPlugin, 'initialize')
        assert hasattr(WeatherPlugin, 'get_tools')
        assert hasattr(WeatherPlugin, 'cleanup')
    
    @pytest.mark.integration
    def test_plugin_validation(self):
        """Test plugin validation."""
        from agenticraft.core.plugin import PluginManager
        
        # Test invalid plugin (missing required methods)
        class InvalidPlugin:
            name = "invalid"
            # Missing required methods
        
        manager = PluginManager()
        
        # Should raise error
        with pytest.raises(ValueError, match="Invalid plugin"):
            manager.register(InvalidPlugin())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
