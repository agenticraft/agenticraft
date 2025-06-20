"""Plugin architecture for AgentiCraft.

This module provides the plugin system that allows extending AgentiCraft
without modifying the core framework. Plugins can hook into various
lifecycle events and add custom functionality.

Example:
    Creating a custom plugin::

        from agenticraft import BasePlugin, PluginInfo

        class LoggingPlugin(BasePlugin):
            name = "logging_plugin"
            version = "1.0.0"
            description = "Logs agent events"

            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )

            def on_agent_created(self, agent: Agent) -> None:
                print(f"Agent created: {agent.name}")
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .agent import Agent, AgentResponse
    from .workflow import Workflow, WorkflowResult


class PluginInfo(BaseModel):
    """Information about a plugin."""

    name: str
    version: str
    description: str
    author: str | None = None
    author_email: str | None = None
    homepage: str | None = None
    license: str | None = None
    provides_tools: list[str] = Field(default_factory=list)
    provides_agents: list[str] = Field(default_factory=list)
    requires_plugins: list[str] = Field(default_factory=list)
    requires_packages: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    config_schema: dict[str, Any] | None = None
    capabilities: list[str] = Field(default_factory=list)


class PluginConfig(BaseModel):
    """Configuration for a plugin instance."""

    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0


class PluginContext(BaseModel):
    """Context provided to plugins."""

    model_config = {"arbitrary_types_allowed": True}

    plugin_dir: Path
    data_dir: Path
    cache_dir: Path
    shared_data: dict[str, Any] = Field(default_factory=dict)


class PluginLifecycle(str, Enum):
    """Plugin lifecycle states."""

    CREATED = "created"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    DESTROYED = "destroyed"


class PluginCapability(str, Enum):
    """Plugin capabilities."""

    TOOLS = "tools"
    AGENTS = "agents"
    MEMORY = "memory"
    ENHANCEMENT = "enhancement"
    WORKFLOW = "workflow"
    PROVIDER = "provider"


class BasePlugin(ABC):
    """Base class for AgentiCraft plugins.

    Plugins can hook into various lifecycle events to extend
    functionality without modifying core code.
    """

    # Plugin metadata (to be overridden)
    name: str = "base_plugin"
    version: str = "1.0.0"
    description: str = "Base plugin"

    def __init__(self, config: PluginConfig | None = None):
        """Initialize plugin with optional configuration."""
        self.config = config or PluginConfig()
        self.context: PluginContext | None = None
        self.state = PluginLifecycle.CREATED

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Get plugin information.

        Returns:
            PluginInfo describing the plugin
        """
        pass

    def initialize(self) -> None:
        """Initialize the plugin.

        Called when the plugin is first loaded.
        """
        self.state = PluginLifecycle.INITIALIZED

    def start(self) -> None:
        """Start the plugin.

        Called when the plugin should begin operation.
        """
        self.state = PluginLifecycle.STARTED

    def stop(self) -> None:
        """Stop the plugin.

        Called when the plugin should cease operation.
        """
        self.state = PluginLifecycle.STOPPED

    def cleanup(self) -> None:
        """Clean up plugin resources.

        Called when the plugin is being unloaded.
        """
        self.state = PluginLifecycle.DESTROYED

    # Async lifecycle methods

    async def initialize_async(self) -> None:
        """Async initialization."""
        pass

    async def cleanup_async(self) -> None:
        """Async cleanup."""
        pass

    # Tool and agent providers

    def get_tools(self) -> list[Any]:
        """Get tools provided by this plugin.

        Returns:
            List of tool instances
        """
        return []

    def get_agents(self) -> list[type]:
        """Get agent classes provided by this plugin.

        Returns:
            List of agent classes
        """
        return []

    def get_capabilities(self) -> list[PluginCapability]:
        """Get plugin capabilities.

        Returns:
            List of capabilities this plugin provides
        """
        return []

    # Enhancement methods

    def enhance_agent(self, agent: "Agent") -> "Agent":
        """Enhance an agent with plugin functionality.

        Args:
            agent: Agent to enhance

        Returns:
            Enhanced agent
        """
        return agent

    # Dependency checking

    def check_dependencies(self) -> bool:
        """Check if plugin dependencies are satisfied.

        Returns:
            True if all dependencies are met
        """
        return True

    # Lifecycle hooks

    def on_agent_created(self, agent: "Agent") -> None:
        """Called when an agent is created.

        Args:
            agent: The newly created agent
        """
        pass

    def on_agent_run_start(
        self, agent: "Agent", prompt: str, context: dict[str, Any] | None
    ) -> None:
        """Called before an agent starts processing.

        Args:
            agent: The agent about to run
            prompt: The user prompt
            context: Optional context
        """
        pass

    def on_agent_run_complete(self, agent: "Agent", response: "AgentResponse") -> None:
        """Called after an agent completes processing.

        Args:
            agent: The agent that completed
            response: The generated response
        """
        pass

    def on_agent_error(self, agent: "Agent", error: Exception) -> None:
        """Called when an agent encounters an error.

        Args:
            agent: The agent that errored
            error: The exception that occurred
        """
        pass

    # Tool lifecycle hooks

    def on_tool_registered(self, tool_name: str, tool: Any) -> None:
        """Called when a tool is registered.

        Args:
            tool_name: Name of the tool
            tool: The tool instance
        """
        pass

    def on_tool_execution_start(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> None:
        """Called before a tool is executed.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
        """
        pass

    def on_tool_execution_complete(self, tool_name: str, result: Any) -> None:
        """Called after a tool completes execution.

        Args:
            tool_name: Name of the tool
            result: Tool execution result
        """
        pass

    def on_tool_error(self, tool_name: str, error: Exception) -> None:
        """Called when a tool encounters an error.

        Args:
            tool_name: Name of the tool
            error: The exception that occurred
        """
        pass

    # Workflow lifecycle hooks

    def on_workflow_created(self, workflow: "Workflow") -> None:
        """Called when a workflow is created.

        Args:
            workflow: The newly created workflow
        """
        pass

    def on_workflow_start(self, workflow: "Workflow", inputs: dict[str, Any]) -> None:
        """Called before a workflow starts.

        Args:
            workflow: The workflow about to run
            inputs: Workflow inputs
        """
        pass

    def on_workflow_complete(
        self, workflow: "Workflow", result: "WorkflowResult"
    ) -> None:
        """Called after a workflow completes.

        Args:
            workflow: The completed workflow
            result: Workflow execution result
        """
        pass

    def on_workflow_step_complete(
        self, workflow: "Workflow", step_name: str, result: Any
    ) -> None:
        """Called after each workflow step completes.

        Args:
            workflow: The workflow
            step_name: Name of the completed step
            result: Step result
        """
        pass

    # Response modification hooks

    def on_response_generated(self, response: "AgentResponse") -> "AgentResponse":
        """Called when a response is generated, allows modification.

        Args:
            response: The generated response

        Returns:
            Modified response (or original if no changes)
        """
        return response

    def on_reasoning_complete(self, reasoning: str) -> str:
        """Called when reasoning is formatted, allows modification.

        Args:
            reasoning: The formatted reasoning

        Returns:
            Modified reasoning (or original if no changes)
        """
        return reasoning


class PluginRegistry:
    """Registry for managing plugins."""

    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: list[BasePlugin] = []

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin instance to register
        """
        self._plugins.append(plugin)

    def unregister(self, plugin: BasePlugin) -> None:
        """Unregister a plugin.

        Args:
            plugin: Plugin instance to remove
        """
        if plugin in self._plugins:
            self._plugins.remove(plugin)

    def get_plugins(self) -> list[BasePlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    # Hook execution methods

    def emit_agent_created(self, agent: "Agent") -> None:
        """Emit agent created event to all plugins."""
        for plugin in self._plugins:
            try:
                plugin.on_agent_created(agent)
            except Exception:
                pass  # Plugins shouldn't break core functionality

    def emit_agent_run_start(
        self, agent: "Agent", prompt: str, context: dict[str, Any] | None
    ) -> None:
        """Emit agent run start event."""
        for plugin in self._plugins:
            try:
                plugin.on_agent_run_start(agent, prompt, context)
            except Exception:
                pass

    def emit_agent_run_complete(
        self, agent: "Agent", response: "AgentResponse"
    ) -> None:
        """Emit agent run complete event."""
        for plugin in self._plugins:
            try:
                plugin.on_agent_run_complete(agent, response)
            except Exception:
                pass

    def emit_response_generated(self, response: "AgentResponse") -> "AgentResponse":
        """Emit response generated event, allowing modification."""
        for plugin in self._plugins:
            try:
                response = plugin.on_response_generated(response)
            except Exception:
                pass
        return response

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()


# Global plugin registry
_global_registry = PluginRegistry()


def register_plugin(plugin: BasePlugin) -> None:
    """Register a plugin globally.

    Args:
        plugin: Plugin to register
    """
    _global_registry.register(plugin)


def get_global_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    return _global_registry


# Example built-in plugins


class LoggingPlugin(BasePlugin):
    """Simple logging plugin for debugging."""

    name = "logging_plugin"
    version = "1.0.0"
    description = "Logs agent and tool events for debugging"

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            provides_tools=[],
            capabilities=[PluginCapability.ENHANCEMENT.value],
        )

    def on_agent_created(self, agent: "Agent") -> None:
        """Log agent creation."""
        print(f"[LoggingPlugin] Agent created: {agent.name} (ID: {agent.id})")

    def on_agent_run_start(
        self, agent: "Agent", prompt: str, context: dict[str, Any] | None
    ) -> None:
        """Log agent run start."""
        print(
            f"[LoggingPlugin] Agent {agent.name} starting with prompt: {prompt[:50]}..."
        )

    def on_tool_execution_start(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> None:
        """Log tool execution."""
        print(f"[LoggingPlugin] Executing tool {tool_name} with args: {arguments}")


class MetricsPlugin(BasePlugin):
    """Plugin for collecting metrics about agent usage."""

    name = "metrics_plugin"
    version = "1.0.0"
    description = "Collects metrics about agent and tool usage"

    def __init__(self, config: PluginConfig | None = None):
        """Initialize metrics plugin."""
        super().__init__(config)
        self.metrics = {
            "agent_runs": 0,
            "tool_executions": 0,
            "errors": 0,
            "total_response_length": 0,
        }

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            capabilities=[PluginCapability.ENHANCEMENT.value],
        )

    def on_agent_run_complete(self, agent: "Agent", response: "AgentResponse") -> None:
        """Track agent runs."""
        self.metrics["agent_runs"] += 1
        self.metrics["total_response_length"] += len(response.content)

    def on_tool_execution_complete(self, tool_name: str, result: Any) -> None:
        """Track tool executions."""
        self.metrics["tool_executions"] += 1

    def on_agent_error(self, agent: "Agent", error: Exception) -> None:
        """Track errors."""
        self.metrics["errors"] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics."""
        return self.metrics.copy()
