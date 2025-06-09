#!/usr/bin/env python3
"""
Example plugin for AgentiCraft.

This example demonstrates how to create a custom plugin that provides
tools, enhances agents, and integrates with the telemetry system.
"""

import asyncio
import random
from typing import Any

from agenticraft.core.tool import BaseTool
from agenticraft.core.types import ToolDefinition, ToolParameter
from agenticraft.plugins import BasePlugin, PluginConfig, PluginInfo
from agenticraft.telemetry import track_metrics


class WeatherTool(BaseTool):
    """Mock weather tool for demonstration."""

    name = "get_weather"
    description = "Get current weather for a location"

    async def arun(self, location: str) -> dict[str, Any]:
        """Get weather for a location."""
        # Mock weather data
        weather_conditions = ["sunny", "cloudy", "rainy", "snowy"]

        return {
            "location": location,
            "temperature": random.randint(0, 35),
            "condition": random.choice(weather_conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
        }

    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="location",
                    type="string",
                    description="The city or location to get weather for",
                    required=True,
                )
            ],
        )


class ForecastTool(BaseTool):
    """Mock forecast tool for demonstration."""

    name = "get_forecast"
    description = "Get weather forecast for a location"

    async def arun(self, location: str, days: int = 5) -> dict[str, Any]:
        """Get weather forecast."""
        forecast = []

        for i in range(days):
            forecast.append(
                {
                    "day": i + 1,
                    "high": random.randint(15, 30),
                    "low": random.randint(5, 15),
                    "condition": random.choice(["sunny", "cloudy", "rainy"]),
                }
            )

        return {"location": location, "days": days, "forecast": forecast}

    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="location",
                    type="string",
                    description="The city or location to get forecast for",
                    required=True,
                ),
                ToolParameter(
                    name="days",
                    type="integer",
                    description="Number of days to forecast (default: 5)",
                    required=False,
                    default=5,
                ),
            ],
        )


class WeatherPlugin(BasePlugin):
    """Example weather plugin for AgentiCraft.

    This plugin demonstrates:
    - Providing multiple tools
    - Using configuration
    - Enhancing agents with new capabilities
    - Integration with telemetry
    """

    name = "weather"
    version = "1.0.0"
    description = "Provides weather information capabilities"
    author = "AgentiCraft Team"

    def get_info(self) -> PluginInfo:
        """Get plugin information."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            author_email="team@agenticraft.ai",
            homepage="https://github.com/agenticraft/weather-plugin",
            provides_tools=["get_weather", "get_forecast"],
            config_schema={
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "Weather API key (optional)",
                    },
                    "cache_ttl": {
                        "type": "integer",
                        "default": 300,
                        "description": "Cache TTL in seconds",
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "default": "metric",
                    },
                },
            },
        )

    def initialize(self) -> None:
        """Initialize the plugin."""
        super().initialize()

        # Setup any connections or resources
        print(
            f"Weather plugin initialized with units: {self.config.config.get('units', 'metric')}"
        )

        # In a real plugin, you might:
        # - Connect to weather API
        # - Set up caching
        # - Load historical data

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        # Close any connections
        print("Weather plugin cleaned up")
        super().cleanup()

    def get_tools(self) -> list[BaseTool]:
        """Get weather tools."""
        # Tools can be configured based on plugin config
        tools = [WeatherTool(), ForecastTool()]

        # Apply configuration to tools
        units = self.config.config.get("units", "metric")
        # Store units in each tool's instance (they can use it if needed)
        # Note: In a real plugin, you might pass units to tool constructors
        for tool in tools:
            # Add units as a dynamic attribute (tools can access if needed)
            tool.units = units

        return tools

    def enhance_agent(self, agent):
        """Enhance agent with weather awareness."""
        # Add weather-specific reasoning patterns
        if hasattr(agent, "add_capability"):
            agent.add_capability("weather_aware")

        # Add weather context to agent's system prompt
        weather_context = """
        You have access to weather information tools. When users ask about weather,
        use the get_weather tool for current conditions and get_forecast for future
        predictions. Always specify the location clearly.
        """

        if hasattr(agent, "add_context"):
            agent.add_context(weather_context)

        # Add tools
        for tool in self.get_tools():
            if hasattr(agent, "add_tool"):
                agent.add_tool(tool)

        return agent

    @track_metrics(name="weather_plugin.api_calls")
    async def _call_weather_api(
        self, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Internal method to demonstrate metrics tracking."""
        # In a real plugin, this would call an actual API
        await asyncio.sleep(0.1)  # Simulate API latency
        return {"status": "success", "data": {}}


# Example of a more complex plugin that provides agents too


class WeatherAgent:
    """A specialized weather assistant agent."""

    def __init__(self, tools: list[BaseTool]):
        self.tools = tools
        self.name = "WeatherAgent"

    async def analyze_weather_trends(self, locations: list[str]) -> dict[str, Any]:
        """Analyze weather trends across multiple locations."""
        results = {}

        for location in locations:
            # Use tools to get weather data
            weather_tool = next(
                (t for t in self.tools if t.name == "get_weather"), None
            )
            if weather_tool:
                weather = await weather_tool.arun(location)
                results[location] = weather

        # Analyze trends
        avg_temp = sum(r["temperature"] for r in results.values()) / len(results)

        return {
            "locations": results,
            "analysis": {
                "average_temperature": avg_temp,
                "coldest": min(results.items(), key=lambda x: x[1]["temperature"])[0],
                "warmest": max(results.items(), key=lambda x: x[1]["temperature"])[0],
            },
        }


class AdvancedWeatherPlugin(WeatherPlugin):
    """Extended weather plugin that also provides agents."""

    name = "advanced_weather"
    version = "2.0.0"
    description = "Advanced weather plugin with analysis agents"

    def get_info(self) -> PluginInfo:
        """Get extended plugin info."""
        info = super().get_info()
        info.provides_agents = ["WeatherAgent"]
        return info

    def get_agents(self) -> list[type]:
        """Provide weather analysis agents."""
        return [WeatherAgent]


# Example usage
if __name__ == "__main__":
    try:
        print("[DEBUG] Starting weather plugin example...")

        # Create plugin with configuration
        print("[DEBUG] Creating plugin config...")
        config = PluginConfig(
            enabled=True,
            config={"api_key": "demo_key", "units": "metric", "cache_ttl": 600},
        )
        print(f"[DEBUG] Config created: {config}")

        # Initialize plugin
        print("[DEBUG] Creating WeatherPlugin instance...")
        plugin = WeatherPlugin(config)
        print("[DEBUG] Plugin instance created")

        print("[DEBUG] Initializing plugin...")
        plugin.initialize()
        print("[DEBUG] Plugin initialized")

        # Get plugin info
        print("[DEBUG] Getting plugin info...")
        info = plugin.get_info()
        print(f"Plugin: {info.name} v{info.version}")
        print(f"Provides tools: {', '.join(info.provides_tools)}")

        # Get tools
        print("[DEBUG] Getting tools...")
        tools = plugin.get_tools()
        print(f"[DEBUG] Got {len(tools)} tools")
        print(f"\nAvailable tools: {[t.name for t in tools]}")

        # Test a tool
        async def test_weather():
            weather_tool = tools[0]
            result = await weather_tool.arun("San Francisco")
            print(f"\nWeather in San Francisco: {result}")

        print("[DEBUG] Testing weather tool...")
        asyncio.run(test_weather())

        # Cleanup
        print("[DEBUG] Cleaning up...")
        plugin.cleanup()
        print("[DEBUG] Done!")

    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
