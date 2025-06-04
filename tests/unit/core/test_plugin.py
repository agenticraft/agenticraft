"""Unit tests for plugin module.

This module tests the plugin functionality including:
- Plugin base class
- Plugin lifecycle
- Plugin registry
- Plugin loading
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from agenticraft.core.plugin import (
    BasePlugin,
    PluginInfo,
    PluginConfig,
    PluginContext,
    PluginLifecycle,
    PluginCapability,
)
from agenticraft.core.tool import tool
from agenticraft.core.agent import Agent


class TestPluginInfo:
    """Test PluginInfo model."""
    
    def test_plugin_info_basic(self):
        """Test basic plugin info."""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin"
        )
        
        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        assert info.description == "A test plugin"
        assert info.author is None
        assert info.provides_tools == []
        assert info.provides_agents == []
    
    def test_plugin_info_complete(self):
        """Test complete plugin info."""
        info = PluginInfo(
            name="weather_plugin",
            version="2.1.0",
            description="Weather information plugin",
            author="Test Author",
            author_email="test@example.com",
            homepage="https://example.com/weather-plugin",
            license="MIT",
            provides_tools=["get_weather", "get_forecast"],
            provides_agents=["WeatherAgent"],
            requires_plugins=["location_plugin>=1.0"],
            tags=["weather", "api", "tools"]
        )
        
        assert info.author == "Test Author"
        assert info.author_email == "test@example.com"
        assert len(info.provides_tools) == 2
        assert "get_weather" in info.provides_tools
        assert len(info.tags) == 3
    
    def test_plugin_info_config_schema(self):
        """Test plugin info with config schema."""
        schema = {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["api_key"]
        }
        
        info = PluginInfo(
            name="api_plugin",
            version="1.0.0",
            description="API plugin",
            config_schema=schema
        )
        
        assert info.config_schema == schema
        assert info.config_schema["required"] == ["api_key"]


class TestPluginConfig:
    """Test PluginConfig model."""
    
    def test_plugin_config_default(self):
        """Test default plugin config."""
        config = PluginConfig()
        
        assert config.enabled is True
        assert config.config == {}
        assert config.priority == 0
    
    def test_plugin_config_custom(self):
        """Test custom plugin config."""
        config = PluginConfig(
            enabled=True,
            config={
                "api_key": "test-key",
                "region": "us-east-1",
                "cache_ttl": 300
            },
            priority=10
        )
        
        assert config.config["api_key"] == "test-key"
        assert config.config["region"] == "us-east-1"
        assert config.priority == 10
    
    def test_plugin_config_disabled(self):
        """Test disabled plugin config."""
        config = PluginConfig(enabled=False)
        
        assert config.enabled is False


class TestPluginContext:
    """Test PluginContext model."""
    
    def test_plugin_context_creation(self):
        """Test creating plugin context."""
        context = PluginContext(
            plugin_dir=Path("/plugins/test"),
            data_dir=Path("/data/test"),
            cache_dir=Path("/cache/test")
        )
        
        assert context.plugin_dir == Path("/plugins/test")
        assert context.data_dir == Path("/data/test")
        assert context.cache_dir == Path("/cache/test")
        assert context.shared_data == {}
    
    def test_plugin_context_with_shared_data(self):
        """Test plugin context with shared data."""
        shared = {
            "api_client": MagicMock(),
            "database": MagicMock()
        }
        
        context = PluginContext(
            plugin_dir=Path("."),
            data_dir=Path("."),
            cache_dir=Path("."),
            shared_data=shared
        )
        
        assert "api_client" in context.shared_data
        assert "database" in context.shared_data


class TestBasePlugin:
    """Test BasePlugin abstract class."""
    
    def test_base_plugin_cannot_be_instantiated(self):
        """Test that BasePlugin is abstract."""
        with pytest.raises(TypeError):
            BasePlugin()
    
    def test_custom_plugin_implementation(self):
        """Test creating custom plugin."""
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
            
            def initialize(self) -> None:
                self.initialized = True
            
            def cleanup(self) -> None:
                self.cleaned_up = True
        
        plugin = TestPlugin()
        
        assert plugin.name == "test_plugin"
        assert plugin.version == "1.0.0"
        
        # Test lifecycle
        plugin.initialize()
        assert plugin.initialized is True
        
        plugin.cleanup()
        assert plugin.cleaned_up is True
    
    def test_plugin_with_config(self):
        """Test plugin with configuration."""
        class ConfigurablePlugin(BasePlugin):
            name = "configurable"
            version = "1.0.0"
            description = "Configurable plugin"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    config_schema={
                        "type": "object",
                        "properties": {
                            "setting": {"type": "string"}
                        }
                    }
                )
            
            def initialize(self) -> None:
                self.setting = self.config.config.get("setting", "default")
        
        config = PluginConfig(
            enabled=True,
            config={"setting": "custom_value"}
        )
        
        plugin = ConfigurablePlugin(config)
        plugin.initialize()
        
        assert plugin.setting == "custom_value"


class TestPluginWithTools:
    """Test plugins that provide tools."""
    
    def test_plugin_providing_tools(self):
        """Test plugin that provides tools."""
        class ToolPlugin(BasePlugin):
            name = "tool_plugin"
            version = "1.0.0"
            description = "Plugin with tools"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    provides_tools=["custom_tool", "another_tool"]
                )
            
            def get_tools(self) -> List[Any]:
                @tool
                def custom_tool(text: str) -> str:
                    """Custom tool from plugin."""
                    return text.upper()
                
                @tool
                def another_tool(n: int) -> int:
                    """Another tool from plugin."""
                    return n * 2
                
                return [custom_tool, another_tool]
        
        plugin = ToolPlugin()
        tools = plugin.get_tools()
        
        assert len(tools) == 2
        assert tools[0].name == "custom_tool"
        assert tools[1].name == "another_tool"
        
        # Test tool execution
        result = tools[0].run(text="hello")
        assert result == "HELLO"


class TestPluginWithAgents:
    """Test plugins that provide agents."""
    
    def test_plugin_providing_agents(self):
        """Test plugin that provides agent classes."""
        class AgentPlugin(BasePlugin):
            name = "agent_plugin"
            version = "1.0.0"
            description = "Plugin with agents"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    provides_agents=["CustomAgent"]
                )
            
            def get_agents(self) -> List[type]:
                class CustomAgent(Agent):
                    """Custom agent from plugin."""
                    def __init__(self, **kwargs):
                        super().__init__(
                            name="CustomAgent",
                            instructions="I am a custom agent from a plugin",
                            **kwargs
                        )
                
                return [CustomAgent]
        
        plugin = AgentPlugin()
        agents = plugin.get_agents()
        
        assert len(agents) == 1
        assert agents[0].__name__ == "CustomAgent"
        
        # Test agent creation
        agent_instance = agents[0]()
        assert agent_instance.name == "CustomAgent"


class TestPluginLifecycle:
    """Test plugin lifecycle management."""
    
    def test_plugin_lifecycle_states(self):
        """Test plugin lifecycle states."""
        class LifecyclePlugin(BasePlugin):
            name = "lifecycle"
            version = "1.0.0"
            description = "Lifecycle test"
            
            def __init__(self, config=None):
                super().__init__(config)
                self.state = PluginLifecycle.CREATED
                self.events = []
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            def initialize(self) -> None:
                self.events.append("initialize")
                self.state = PluginLifecycle.INITIALIZED
            
            def start(self) -> None:
                self.events.append("start")
                self.state = PluginLifecycle.STARTED
            
            def stop(self) -> None:
                self.events.append("stop")
                self.state = PluginLifecycle.STOPPED
            
            def cleanup(self) -> None:
                self.events.append("cleanup")
                self.state = PluginLifecycle.DESTROYED
        
        plugin = LifecyclePlugin()
        assert plugin.state == PluginLifecycle.CREATED
        
        # Go through lifecycle
        plugin.initialize()
        assert plugin.state == PluginLifecycle.INITIALIZED
        
        plugin.start()
        assert plugin.state == PluginLifecycle.STARTED
        
        plugin.stop()
        assert plugin.state == PluginLifecycle.STOPPED
        
        plugin.cleanup()
        assert plugin.state == PluginLifecycle.DESTROYED
        
        # Check events
        assert plugin.events == ["initialize", "start", "stop", "cleanup"]
    
    @pytest.mark.asyncio
    async def test_async_plugin_lifecycle(self):
        """Test plugin with async lifecycle methods."""
        class AsyncPlugin(BasePlugin):
            name = "async_plugin"
            version = "1.0.0"
            description = "Async plugin"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            async def initialize_async(self) -> None:
                await asyncio.sleep(0.01)
                self.async_initialized = True
            
            async def cleanup_async(self) -> None:
                await asyncio.sleep(0.01)
                self.async_cleaned_up = True
        
        plugin = AsyncPlugin()
        
        await plugin.initialize_async()
        assert plugin.async_initialized is True
        
        await plugin.cleanup_async()
        assert plugin.async_cleaned_up is True


class TestPluginEnhancement:
    """Test plugin agent enhancement."""
    
    def test_enhance_agent(self):
        """Test plugin enhancing an agent."""
        class EnhancerPlugin(BasePlugin):
            name = "enhancer"
            version = "1.0.0"
            description = "Agent enhancer"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            def enhance_agent(self, agent):
                """Add capabilities to agent."""
                # Add a tool
                @tool
                def plugin_tool() -> str:
                    return "Enhanced!"
                
                if hasattr(agent, 'add_tool'):
                    agent.add_tool(plugin_tool)
                
                # Add context
                if hasattr(agent, 'add_context'):
                    agent.add_context("You have been enhanced by a plugin!")
                
                # Mark as enhanced
                agent._enhanced = True
                
                return agent
        
        plugin = EnhancerPlugin()
        
        # Mock agent
        mock_agent = MagicMock()
        mock_agent.add_tool = MagicMock()
        mock_agent.add_context = MagicMock()
        
        enhanced = plugin.enhance_agent(mock_agent)
        
        assert enhanced._enhanced is True
        mock_agent.add_tool.assert_called_once()
        mock_agent.add_context.assert_called_once()


class TestPluginCapabilities:
    """Test plugin capability declarations."""
    
    def test_plugin_capabilities(self):
        """Test plugin declaring capabilities."""
        class CapablePlugin(BasePlugin):
            name = "capable"
            version = "1.0.0"
            description = "Capable plugin"
            
            def get_capabilities(self) -> List[PluginCapability]:
                return [
                    PluginCapability.TOOLS,
                    PluginCapability.AGENTS,
                    PluginCapability.MEMORY,
                    PluginCapability.ENHANCEMENT
                ]
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    capabilities=[cap.value for cap in self.get_capabilities()]
                )
        
        plugin = CapablePlugin()
        capabilities = plugin.get_capabilities()
        
        assert PluginCapability.TOOLS in capabilities
        assert PluginCapability.AGENTS in capabilities
        assert PluginCapability.MEMORY in capabilities
        assert PluginCapability.ENHANCEMENT in capabilities
        
        info = plugin.get_info()
        assert "tools" in info.capabilities
        assert "agents" in info.capabilities


class TestPluginDependencies:
    """Test plugin dependency management."""
    
    def test_plugin_with_dependencies(self):
        """Test plugin declaring dependencies."""
        class DependentPlugin(BasePlugin):
            name = "dependent"
            version = "1.0.0"
            description = "Plugin with dependencies"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    requires_plugins=[
                        "base_plugin>=1.0.0",
                        "auth_plugin>=2.0,<3.0",
                        "utils_plugin"
                    ],
                    requires_packages=[
                        "requests>=2.28.0",
                        "aiohttp>=3.8.0"
                    ]
                )
            
            def check_dependencies(self) -> bool:
                """Check if dependencies are satisfied."""
                # In real implementation, would check installed plugins
                return True
        
        plugin = DependentPlugin()
        info = plugin.get_info()
        
        assert len(info.requires_plugins) == 3
        assert "base_plugin>=1.0.0" in info.requires_plugins
        assert len(info.requires_packages) == 2
        assert "requests>=2.28.0" in info.requires_packages


class TestPluginContext:
    """Test plugin context usage."""
    
    def test_plugin_using_context(self):
        """Test plugin using provided context."""
        class ContextAwarePlugin(BasePlugin):
            name = "context_aware"
            version = "1.0.0"
            description = "Context aware plugin"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            def initialize(self) -> None:
                if self.context:
                    # Create plugin-specific directories
                    self.data_file = self.context.data_dir / "plugin_data.json"
                    self.cache_file = self.context.cache_dir / "plugin_cache.db"
                    
                    # Use shared resources
                    self.shared_client = self.context.shared_data.get("api_client")
        
        context = PluginContext(
            plugin_dir=Path("/plugins/context_aware"),
            data_dir=Path("/data/context_aware"),
            cache_dir=Path("/cache/context_aware"),
            shared_data={"api_client": MagicMock()}
        )
        
        plugin = ContextAwarePlugin()
        plugin.context = context
        plugin.initialize()
        
        assert plugin.data_file == Path("/data/context_aware/plugin_data.json")
        assert plugin.cache_file == Path("/cache/context_aware/plugin_cache.db")
        assert plugin.shared_client is not None


class TestPluginErrors:
    """Test plugin error handling."""
    
    def test_plugin_initialization_error(self):
        """Test handling plugin initialization errors."""
        class FailingPlugin(BasePlugin):
            name = "failing"
            version = "1.0.0"
            description = "Plugin that fails"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            def initialize(self) -> None:
                raise RuntimeError("Initialization failed!")
        
        plugin = FailingPlugin()
        
        with pytest.raises(RuntimeError, match="Initialization failed"):
            plugin.initialize()
    
    def test_plugin_tool_error(self):
        """Test handling plugin tool errors."""
        class ErrorToolPlugin(BasePlugin):
            name = "error_tool"
            version = "1.0.0"
            description = "Plugin with error tool"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name=self.name,
                    version=self.version,
                    description=self.description
                )
            
            def get_tools(self) -> List[Any]:
                @tool
                def error_tool() -> str:
                    """Tool that always fails."""
                    raise ValueError("Tool error!")
                
                return [error_tool]
        
        plugin = ErrorToolPlugin()
        tools = plugin.get_tools()
        
        with pytest.raises(Exception):  # Will be wrapped in ToolExecutionError
            tools[0].run()
