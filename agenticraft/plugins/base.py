"""Base plugin functionality for AgentiCraft.

This module provides the base classes and interfaces for creating
AgentiCraft plugins. Plugins can extend agents, add tools, modify
behavior, and integrate with external systems.

Example:
    Creating a basic plugin::

        from agenticraft.plugins import BasePlugin

        class WeatherPlugin(BasePlugin):
            '''Adds weather capabilities to agents.'''

            name = "weather"
            version = "1.0.0"

            def get_tools(self):
                return [
                    WeatherTool(),
                    ForecastTool()
                ]

            def enhance_agent(self, agent):
                agent.add_capability("weather_aware")
                return agent
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..core.agent import Agent
    from ..core.tool import Tool


class PluginInfo(BaseModel):
    """Information about a plugin."""

    name: str = Field(..., description="Unique plugin name")
    version: str = Field(..., description="Plugin version (semantic)")
    description: str = Field("", description="Plugin description")
    author: str = Field("", description="Plugin author")
    author_email: str = Field("", description="Author email")
    homepage: str = Field("", description="Plugin homepage/docs")
    license: str = Field("Apache-2.0", description="Plugin license")

    # Dependencies
    requires_python: str = Field(">=3.8", description="Python version requirement")
    requires_agenticraft: str = Field(
        ">=0.1.0", description="AgentiCraft version requirement"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Python dependencies"
    )

    # Capabilities
    provides_tools: list[str] = Field(
        default_factory=list, description="Tool names provided"
    )
    provides_agents: list[str] = Field(
        default_factory=list, description="Agent types provided"
    )
    provides_providers: list[str] = Field(
        default_factory=list, description="LLM providers"
    )

    # Configuration
    config_schema: dict[str, Any] | None = Field(
        None, description="Configuration schema"
    )

    class Config:
        extra = "allow"


class PluginConfig(BaseModel):
    """Base configuration for plugins."""

    enabled: bool = Field(True, description="Whether plugin is enabled")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Plugin-specific config"
    )


class BasePlugin(ABC):
    """Base class for all AgentiCraft plugins.

    Plugins must inherit from this class and implement required methods.
    They can optionally override lifecycle hooks to customize behavior.
    """

    # Plugin metadata (should be overridden by subclasses)
    name: str = "unnamed_plugin"
    version: str = "0.0.0"
    description: str = ""
    author: str = ""

    def __init__(self, config: PluginConfig | None = None):
        """Initialize plugin with configuration.

        Args:
            config: Plugin configuration
        """
        self.config = config or PluginConfig()
        self._initialized = False

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Get plugin information.

        Returns:
            Plugin metadata and capabilities

        Example:
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name="my_plugin",
                    version="1.0.0",
                    description="Does amazing things",
                    provides_tools=["calculator", "converter"]
                )
        """
        pass

    # Initialization and cleanup

    def initialize(self) -> None:
        """Initialize the plugin.

        Called once when the plugin is loaded. Use this for:
        - Setting up connections
        - Loading resources
        - Validating configuration

        Raises:
            Exception: If initialization fails
        """
        self._initialized = True

    def cleanup(self) -> None:
        """Clean up plugin resources.

        Called when the plugin is being unloaded. Use this for:
        - Closing connections
        - Releasing resources
        - Saving state
        """
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized

    # Tool provision

    def get_tools(self) -> list["Tool"]:
        """Get tools provided by this plugin.

        Returns:
            List of tool instances

        Example:
            def get_tools(self):
                return [
                    SearchTool(api_key=self.config.config["api_key"]),
                    CalculatorTool()
                ]
        """
        return []

    # Agent enhancement

    def get_agents(self) -> list[type]:
        """Get agent classes provided by this plugin.

        Returns:
            List of agent classes (not instances)

        Example:
            def get_agents(self):
                return [ResearchAgent, AnalysisAgent]
        """
        return []

    def enhance_agent(self, agent: "Agent") -> "Agent":
        """Enhance an existing agent with plugin capabilities.

        Args:
            agent: Agent to enhance

        Returns:
            Enhanced agent (can be same instance)

        Example:
            def enhance_agent(self, agent):
                # Add tools
                for tool in self.get_tools():
                    agent.add_tool(tool)

                # Add custom reasoning
                agent.add_reasoning_pattern("research_mode")

                return agent
        """
        return agent

    # Provider support

    def get_providers(self) -> dict[str, type]:
        """Get LLM providers offered by this plugin.

        Returns:
            Dict mapping provider name to provider class

        Example:
            def get_providers(self):
                return {
                    "custom_llm": CustomLLMProvider,
                    "local_model": LocalModelProvider
                }
        """
        return {}

    # Configuration

    def validate_config(self) -> bool:
        """Validate plugin configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        return True

    def get_config_schema(self) -> dict[str, Any] | None:
        """Get JSON schema for plugin configuration.

        Returns:
            JSON schema dict or None

        Example:
            def get_config_schema(self):
                return {
                    "type": "object",
                    "properties": {
                        "api_key": {"type": "string"},
                        "timeout": {"type": "integer", "default": 30}
                    },
                    "required": ["api_key"]
                }
        """
        return None

    # Plugin discovery

    @classmethod
    def discover_plugins(cls, path: Path) -> list[type]:
        """Discover plugin classes in a directory.

        Args:
            path: Directory to search

        Returns:
            List of plugin classes found
        """
        plugins = []

        if not path.exists() or not path.is_dir():
            return plugins

        # Import all Python files and look for BasePlugin subclasses
        import importlib.util
        import inspect

        for file_path in path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            # Load the module
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find plugin classes
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BasePlugin)
                        and obj != BasePlugin
                    ):
                        plugins.append(obj)

        return plugins


class ToolPlugin(BasePlugin):
    """Specialized base class for tool-only plugins.

    Simplifies creating plugins that only provide tools.
    """

    @abstractmethod
    def create_tools(self) -> list["Tool"]:
        """Create and return tool instances.

        Returns:
            List of configured tools
        """
        pass

    def get_tools(self) -> list["Tool"]:
        """Get tools from create_tools method."""
        return self.create_tools()

    def get_info(self) -> PluginInfo:
        """Generate info from tools."""
        tools = self.create_tools()
        tool_names = [tool.name for tool in tools]

        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description or f"Provides tools: {', '.join(tool_names)}",
            author=self.author,
            provides_tools=tool_names,
        )


class AgentPlugin(BasePlugin):
    """Specialized base class for agent-providing plugins.

    Simplifies creating plugins that provide custom agents.
    """

    @abstractmethod
    def create_agents(self) -> list[type]:
        """Create and return agent classes.

        Returns:
            List of agent classes
        """
        pass

    def get_agents(self) -> list[type]:
        """Get agents from create_agents method."""
        return self.create_agents()

    def get_info(self) -> PluginInfo:
        """Generate info from agents."""
        agents = self.create_agents()
        agent_names = [agent.__name__ for agent in agents]

        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description
            or f"Provides agents: {', '.join(agent_names)}",
            author=self.author,
            provides_agents=agent_names,
        )


class CompositePlugin(BasePlugin):
    """Base class for plugins that combine multiple capabilities.

    Useful for creating comprehensive plugins that provide tools,
    agents, providers, and enhancements.
    """

    def get_info(self) -> PluginInfo:
        """Generate comprehensive plugin info."""
        tools = self.get_tools()
        agents = self.get_agents()
        providers = self.get_providers()

        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            provides_tools=[t.name for t in tools],
            provides_agents=[a.__name__ for a in agents],
            provides_providers=list(providers.keys()),
            config_schema=self.get_config_schema(),
        )
