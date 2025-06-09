"""Test the example weather plugin."""

import pytest

from agenticraft.plugins import PluginConfig
from examples.plugins.weather_plugin import (
    AdvancedWeatherPlugin,
    ForecastTool,
    WeatherAgent,
    WeatherPlugin,
    WeatherTool,
)


class TestWeatherTools:
    """Test weather tools."""

    @pytest.mark.asyncio
    async def test_weather_tool(self):
        """Test weather tool execution."""
        tool = WeatherTool()

        result = await tool.arun("San Francisco")

        assert result["location"] == "San Francisco"
        assert "temperature" in result
        assert "condition" in result
        assert "humidity" in result
        assert "wind_speed" in result

    @pytest.mark.asyncio
    async def test_forecast_tool(self):
        """Test forecast tool execution."""
        tool = ForecastTool()

        result = await tool.arun("New York", days=3)

        assert result["location"] == "New York"
        assert result["days"] == 3
        assert len(result["forecast"]) == 3

        for day in result["forecast"]:
            assert "day" in day
            assert "high" in day
            assert "low" in day
            assert "condition" in day


class TestWeatherPlugin:
    """Test weather plugin functionality."""

    def test_plugin_creation(self):
        """Test creating weather plugin."""
        config = PluginConfig(config={"api_key": "test_key", "units": "metric"})

        plugin = WeatherPlugin(config)

        assert plugin.name == "weather"
        assert plugin.version == "1.0.0"
        assert plugin.config.config["api_key"] == "test_key"

    def test_plugin_info(self):
        """Test plugin info."""
        plugin = WeatherPlugin()
        info = plugin.get_info()

        assert info.name == "weather"
        assert info.version == "1.0.0"
        assert "get_weather" in info.provides_tools
        assert "get_forecast" in info.provides_tools
        assert info.config_schema is not None

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = WeatherPlugin()

        plugin.initialize()

        assert plugin.is_initialized

    def test_plugin_cleanup(self):
        """Test plugin cleanup."""
        plugin = WeatherPlugin()
        plugin.initialize()

        plugin.cleanup()

        assert not plugin.is_initialized

    def test_get_tools(self):
        """Test getting tools from plugin."""
        config = PluginConfig(config={"units": "imperial"})
        plugin = WeatherPlugin(config)

        tools = plugin.get_tools()

        assert len(tools) == 2
        assert any(t.name == "get_weather" for t in tools)
        assert any(t.name == "get_forecast" for t in tools)

        # Check that units were applied
        for tool in tools:
            assert hasattr(tool, "units")
            assert tool.units == "imperial"

    def test_enhance_agent(self):
        """Test agent enhancement."""
        plugin = WeatherPlugin()

        # Mock agent
        class MockAgent:
            def __init__(self):
                self.capabilities = []
                self.context = []
                self.tools = []

            def add_capability(self, cap):
                self.capabilities.append(cap)

            def add_context(self, ctx):
                self.context.append(ctx)

            def add_tool(self, tool):
                self.tools.append(tool)

        agent = MockAgent()
        enhanced = plugin.enhance_agent(agent)

        assert "weather_aware" in enhanced.capabilities
        assert len(enhanced.context) == 1
        assert len(enhanced.tools) == 2


class TestAdvancedWeatherPlugin:
    """Test advanced weather plugin."""

    def test_advanced_plugin_info(self):
        """Test advanced plugin info."""
        plugin = AdvancedWeatherPlugin()
        info = plugin.get_info()

        assert info.name == "advanced_weather"
        assert info.version == "2.0.0"
        assert "WeatherAgent" in info.provides_agents

    def test_get_agents(self):
        """Test getting agents from plugin."""
        plugin = AdvancedWeatherPlugin()

        agents = plugin.get_agents()

        assert len(agents) == 1
        assert agents[0] == WeatherAgent


class TestWeatherAgent:
    """Test weather agent functionality."""

    @pytest.mark.asyncio
    async def test_analyze_weather_trends(self):
        """Test weather trend analysis."""
        # Create tools
        weather_tool = WeatherTool()
        forecast_tool = ForecastTool()

        # Create agent
        agent = WeatherAgent([weather_tool, forecast_tool])

        # Analyze trends
        result = await agent.analyze_weather_trends(["NYC", "LA", "Chicago"])

        assert "locations" in result
        assert "analysis" in result
        assert len(result["locations"]) == 3

        analysis = result["analysis"]
        assert "average_temperature" in analysis
        assert "coldest" in analysis
        assert "warmest" in analysis


class TestPluginConfiguration:
    """Test plugin configuration handling."""

    def test_config_validation(self):
        """Test configuration validation."""
        plugin = WeatherPlugin()

        # Default config should be valid
        assert plugin.validate_config() is True

    def test_config_schema(self):
        """Test configuration schema."""
        plugin = WeatherPlugin()
        schema = plugin.get_config_schema()

        assert schema is None  # Base method returns None

        # But info contains schema
        info = plugin.get_info()
        assert info.config_schema is not None
        assert "properties" in info.config_schema
        assert "api_key" in info.config_schema["properties"]
        assert "units" in info.config_schema["properties"]
