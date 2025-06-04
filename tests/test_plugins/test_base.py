"""Tests for plugin base classes."""

import pytest
from pathlib import Path
from typing import List, Dict

from agenticraft.plugins.base import (
    BasePlugin,
    PluginInfo,
    PluginConfig,
    ToolPlugin,
    AgentPlugin,
    CompositePlugin
)
from agenticraft.core.tool import BaseTool
from agenticraft.core.types import ToolDefinition, ToolParameter


# Mock implementations for testing

class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str = "mock_tool"):
        super().__init__(name=name, description=f"Mock {name} tool")
    
    async def arun(self, **kwargs):
        return {"result": "mock"}
    
    def get_definition(self):
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[]
        )


class MockAgent:
    """Mock agent for testing."""
    name = "MockAgent"
    
    def __init__(self):
        self.capabilities = []
        self.tools = []
    
    def add_capability(self, capability):
        self.capabilities.append(capability)
    
    def add_tool(self, tool):
        self.tools.append(tool)


class SimplePlugin(BasePlugin):
    """Simple test plugin."""
    name = "simple"
    version = "1.0.0"
    description = "A simple test plugin"
    author = "Test Author"
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author
        )


class TestPluginInfo:
    """Test PluginInfo model."""
    
    def test_plugin_info_minimal(self):
        """Test creating minimal plugin info."""
        info = PluginInfo(
            name="test",
            version="1.0.0"
        )
        
        assert info.name == "test"
        assert info.version == "1.0.0"
        assert info.description == ""
        assert info.requires_python == ">=3.8"
        assert info.requires_agenticraft == ">=0.1.0"
    
    def test_plugin_info_full(self):
        """Test creating full plugin info."""
        info = PluginInfo(
            name="advanced",
            version="2.0.0",
            description="Advanced plugin",
            author="John Doe",
            author_email="john@example.com",
            homepage="https://example.com",
            license="MIT",
            requires_python=">=3.9",
            requires_agenticraft=">=0.2.0",
            dependencies=["httpx>=0.25", "pydantic>=2.0"],
            provides_tools=["tool1", "tool2"],
            provides_agents=["Agent1"],
            provides_providers=["custom_llm"],
            config_schema={"type": "object"}
        )
        
        assert info.name == "advanced"
        assert info.version == "2.0.0"
        assert len(info.dependencies) == 2
        assert "tool1" in info.provides_tools
        assert "Agent1" in info.provides_agents
        assert info.config_schema["type"] == "object"


class TestPluginConfig:
    """Test PluginConfig model."""
    
    def test_plugin_config_default(self):
        """Test default plugin config."""
        config = PluginConfig()
        
        assert config.enabled is True
        assert config.config == {}
    
    def test_plugin_config_custom(self):
        """Test custom plugin config."""
        config = PluginConfig(
            enabled=False,
            config={"api_key": "secret", "timeout": 30}
        )
        
        assert config.enabled is False
        assert config.config["api_key"] == "secret"
        assert config.config["timeout"] == 30


class TestBasePlugin:
    """Test BasePlugin functionality."""
    
    def test_plugin_creation(self):
        """Test creating a plugin."""
        plugin = SimplePlugin()
        
        assert plugin.name == "simple"
        assert plugin.version == "1.0.0"
        assert not plugin.is_initialized
    
    def test_plugin_with_config(self):
        """Test creating plugin with config."""
        config = PluginConfig(config={"setting": "value"})
        plugin = SimplePlugin(config)
        
        assert plugin.config == config
        assert plugin.config.config["setting"] == "value"
    
    def test_plugin_initialize(self):
        """Test plugin initialization."""
        plugin = SimplePlugin()
        
        plugin.initialize()
        
        assert plugin.is_initialized
    
    def test_plugin_cleanup(self):
        """Test plugin cleanup."""
        plugin = SimplePlugin()
        plugin.initialize()
        
        plugin.cleanup()
        
        assert not plugin.is_initialized
    
    def test_plugin_get_info(self):
        """Test getting plugin info."""
        plugin = SimplePlugin()
        info = plugin.get_info()
        
        assert info.name == "simple"
        assert info.version == "1.0.0"
        assert info.author == "Test Author"
    
    def test_plugin_default_methods(self):
        """Test default method implementations."""
        plugin = SimplePlugin()
        
        # Default implementations should return empty
        assert plugin.get_tools() == []
        assert plugin.get_agents() == []
        assert plugin.get_providers() == {}
        
        # Enhance should return agent unchanged
        agent = MockAgent()
        enhanced = plugin.enhance_agent(agent)
        assert enhanced is agent
        
        # Config validation should pass
        assert plugin.validate_config() is True
        
        # No config schema by default
        assert plugin.get_config_schema() is None
    
    def test_plugin_discover(self, tmp_path):
        """Test plugin discovery."""
        # Create a test plugin file
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from agenticraft.plugins.base import BasePlugin, PluginInfo

class TestPlugin(BasePlugin):
    name = "discovered"
    
    def get_info(self):
        return PluginInfo(name=self.name, version="1.0.0")
""")
        
        # Discover plugins
        plugins = BasePlugin.discover_plugins(tmp_path)
        
        assert len(plugins) == 1
        assert plugins[0].name == "discovered"


class TestToolPlugin:
    """Test ToolPlugin specialization."""
    
    def test_tool_plugin(self):
        """Test tool plugin functionality."""
        
        class MyToolPlugin(ToolPlugin):
            name = "tools"
            version = "1.0.0"
            
            def create_tools(self) -> List[BaseTool]:
                return [MockTool()]
        
        plugin = MyToolPlugin()
        
        # Get tools
        tools = plugin.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "mock_tool"
        
        # Info should include tools
        info = plugin.get_info()
        assert "mock_tool" in info.provides_tools
        assert "mock_tool" in info.description


class TestAgentPlugin:
    """Test AgentPlugin specialization."""
    
    def test_agent_plugin(self):
        """Test agent plugin functionality."""
        
        class MyAgentPlugin(AgentPlugin):
            name = "agents"
            version = "1.0.0"
            
            def create_agents(self) -> List[type]:
                return [MockAgent]
        
        plugin = MyAgentPlugin()
        
        # Get agents
        agents = plugin.get_agents()
        assert len(agents) == 1
        assert agents[0].__name__ == "MockAgent"
        
        # Info should include agents
        info = plugin.get_info()
        assert "MockAgent" in info.provides_agents
        assert "MockAgent" in info.description


class TestCompositePlugin:
    """Test CompositePlugin functionality."""
    
    def test_composite_plugin(self):
        """Test composite plugin with multiple capabilities."""
        
        class MyCompositePlugin(CompositePlugin):
            name = "composite"
            version = "1.0.0"
            description = "A plugin that does everything"
            
            def get_tools(self) -> List[BaseTool]:
                return [MockTool()]
            
            def get_agents(self) -> List[type]:
                return [MockAgent]
            
            def get_providers(self) -> Dict[str, type]:
                return {"custom": type("CustomProvider", (), {})}
            
            def get_config_schema(self) -> Dict[str, any]:
                return {"type": "object", "properties": {"key": {"type": "string"}}}
        
        plugin = MyCompositePlugin()
        
        # Test all capabilities
        assert len(plugin.get_tools()) == 1
        assert len(plugin.get_agents()) == 1
        assert len(plugin.get_providers()) == 1
        
        # Info should include everything
        info = plugin.get_info()
        assert "mock_tool" in info.provides_tools
        assert "MockAgent" in info.provides_agents
        assert "custom" in info.provides_providers
        assert info.config_schema is not None


class TestPluginEnhancement:
    """Test agent enhancement functionality."""
    
    def test_enhance_agent(self):
        """Test enhancing an agent with plugin capabilities."""
        
        class EnhancerPlugin(BasePlugin):
            name = "enhancer"
            version = "1.0.0"
            
            def get_info(self) -> PluginInfo:
                return PluginInfo(name=self.name, version=self.version)
            
            def get_tools(self) -> List[BaseTool]:
                return [MockTool()]
            
            def enhance_agent(self, agent):
                # Add capability
                if hasattr(agent, 'add_capability'):
                    agent.add_capability('enhanced')
                
                # Add tools
                for tool in self.get_tools():
                    if hasattr(agent, 'add_tool'):
                        agent.add_tool(tool)
                
                return agent
        
        plugin = EnhancerPlugin()
        agent = MockAgent()
        
        # Enhance agent
        enhanced = plugin.enhance_agent(agent)
        
        assert 'enhanced' in enhanced.capabilities
        assert len(enhanced.tools) == 1
        assert enhanced.tools[0].name == "mock_tool"
