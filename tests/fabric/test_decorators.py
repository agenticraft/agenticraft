"""
Tests for Fast-Agent Style Decorators.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import yaml
import asyncio

from agenticraft.fabric.decorators import (
    agent,
    workflow,
    step,
    chain,
    parallel,
    AgentConfig,
    DecoratedAgent,
    ToolProxy,
    load_agent_config,
    from_config,
    register_agent,
    get_agent,
    _agent_registry
)
from agenticraft import Agent, ReasoningAgent


class TestAgentDecorator:
    """Test @agent decorator functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_agent_decorator(self):
        """Test basic agent creation with decorator."""
        
        @agent("test_agent", servers=["http://localhost:3000/mcp"])
        async def my_agent(self, prompt: str):
            return f"Processed: {prompt}"
        
        assert isinstance(my_agent, DecoratedAgent)
        assert my_agent.config.name == "test_agent"
        assert my_agent.config.servers == ["http://localhost:3000/mcp"]
    
    @pytest.mark.asyncio
    async def test_agent_with_all_options(self):
        """Test agent with all configuration options."""
        
        @agent(
            "advanced_agent",
            servers=["http://localhost:3000/mcp"],
            tools=["tool1", "tool2"],
            model="gpt-4",
            provider="openai",
            reasoning="chain_of_thought",
            temperature=0.7,
            max_tokens=2000,
            sandbox=True,
            memory=True,
            custom_field="custom_value"
        )
        async def advanced(self, query: str):
            return query
        
        config = advanced.config
        assert config.name == "advanced_agent"
        assert config.model == "gpt-4"
        assert config.provider == "openai"
        assert config.reasoning_pattern == "chain_of_thought"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.sandbox_enabled is True
        assert config.memory_enabled is True
        assert config.metadata["custom_field"] == "custom_value"
    
    @pytest.mark.asyncio
    async def test_reasoning_agent_selection(self):
        """Test that reasoning pattern selects ReasoningAgent class."""
        
        @agent("reasoner", reasoning="chain_of_thought")
        async def reasoning_agent(self, problem: str):
            return problem
        
        assert reasoning_agent.agent_class == ReasoningAgent
        
        @agent("normal")
        async def normal_agent(self, prompt: str):
            return prompt
        
        assert normal_agent.agent_class == Agent
    
    @pytest.mark.asyncio
    async def test_decorated_agent_execution(self):
        """Test executing a decorated agent function."""
        mock_fabric = Mock()
        mock_fabric.initialize = AsyncMock()
        mock_fabric.create_unified_agent = AsyncMock(return_value=Mock(spec=Agent))
        mock_fabric.get_tools = Mock(return_value=[])
        
        with patch('agenticraft.fabric.decorators.get_global_fabric', return_value=mock_fabric):
            @agent("executor", servers=["http://localhost:3000/mcp"])
            async def test_executor(self, value: str):
                return f"Executed: {value}"
            
            result = await test_executor("test")
            assert result == "Executed: test"
            
            # Check initialization was called
            mock_fabric.initialize.assert_called_once()
            mock_fabric.create_unified_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_function_wrapper(self):
        """Test that sync functions work with decorator."""
        mock_fabric = Mock()
        mock_fabric.initialize = AsyncMock()
        mock_fabric.create_unified_agent = AsyncMock(return_value=Mock(spec=Agent))
        mock_fabric.get_tools = Mock(return_value=[])
        
        with patch('agenticraft.fabric.decorators.get_global_fabric', return_value=mock_fabric):
            @agent("sync_agent")
            def sync_function(self, x: int):
                return x * 2
            
            # Should still work even though it's sync
            result = await sync_function(21)
            assert result == 42


class TestToolProxy:
    """Test ToolProxy for natural tool access."""
    
    def test_tool_access_by_name(self):
        """Test accessing tools by name."""
        mock_fabric = Mock()
        mock_tool = Mock()
        mock_tool.name = "mcp:search"
        mock_tool.description = "Search tool"
        mock_fabric.get_tools = Mock(return_value=[mock_tool])
        mock_fabric.execute_tool = AsyncMock(return_value={"results": []})
        
        proxy = ToolProxy(Mock(), mock_fabric)
        
        # Access tool
        tool_func = proxy.search
        assert tool_func is not None
        
        # Access same tool again (cached)
        tool_func2 = proxy.search
        assert tool_func2 is tool_func
    
    def test_tool_not_found(self):
        """Test accessing non-existent tool."""
        mock_fabric = Mock()
        mock_fabric.get_tools = Mock(return_value=[])
        
        proxy = ToolProxy(Mock(), mock_fabric)
        
        with pytest.raises(AttributeError, match="Tool 'nonexistent' not found"):
            _ = proxy.nonexistent
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test executing tool through proxy."""
        mock_fabric = Mock()
        mock_tool = Mock()
        mock_tool.name = "mcp:analyze"
        mock_fabric.get_tools = Mock(return_value=[mock_tool])
        mock_fabric.execute_tool = AsyncMock(return_value={"analysis": "complete"})
        
        proxy = ToolProxy(Mock(), mock_fabric)
        
        # Get and execute tool
        analyze = proxy.analyze
        result = await analyze(data="test data")
        
        assert result == {"analysis": "complete"}
        mock_fabric.execute_tool.assert_called_once_with("mcp:analyze", data="test data")
    
    def test_tool_dir(self):
        """Test listing available tools."""
        mock_fabric = Mock()
        mock_tool1 = Mock()
        mock_tool1.name = "mcp:tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "a2a:agent.tool2"
        mock_tool3 = Mock()
        mock_tool3.name = "tool3"
        mock_tools = [mock_tool1, mock_tool2, mock_tool3]
        mock_fabric.get_tools = Mock(return_value=mock_tools)
        
        proxy = ToolProxy(Mock(), mock_fabric)
        
        tools = dir(proxy)
        assert "mcp:tool1" in tools
        assert "a2a:agent.tool2" in tools
        assert "tool3" in tools
        # Simple names also included
        assert "tool1" in tools
        assert "tool2" in tools


class TestConfigurationLoading:
    """Test configuration loading functionality."""
    
    def test_load_agent_config(self):
        """Test loading configuration from YAML."""
        config_data = {
            "agents": {
                "researcher": {
                    "servers": ["http://localhost:3000/mcp"],
                    "model": "gpt-4",
                    "temperature": 0.7
                },
                "writer": {
                    "servers": ["http://localhost:3001/mcp"],
                    "model": "claude-3",
                    "reasoning": "chain_of_thought"
                }
            },
            "settings": {
                "default_model": "gpt-4",
                "retry_count": 3
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_agent_config(temp_path)
            
            assert config["agents"]["researcher"]["model"] == "gpt-4"
            assert config["agents"]["writer"]["reasoning"] == "chain_of_thought"
            assert config["settings"]["default_model"] == "gpt-4"
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_agent_config("nonexistent.yaml")
    
    def test_from_config_decorator(self):
        """Test @from_config decorator."""
        config_data = {
            "agents": {
                "test_agent": {
                    "servers": ["http://localhost:3000/mcp"],
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.5
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            @from_config(temp_path)
            class TestAgents:
                @agent("test_agent")
                async def test_method(self, prompt: str):
                    return prompt
            
            # Check that config was applied
            test_instance = TestAgents()
            agent_method = test_instance.test_method
            
            assert agent_method.config.model == "gpt-3.5-turbo"
            assert agent_method.config.temperature == 0.5
            assert agent_method.config.servers == ["http://localhost:3000/mcp"]
            
        finally:
            Path(temp_path).unlink()


class TestWorkflowDecorators:
    """Test workflow-related decorators."""
    
    def test_workflow_decorator(self):
        """Test @workflow decorator basic functionality."""
        
        @workflow("test_workflow", steps=["step1", "step2"])
        class TestWorkflow:
            @step(order=1)
            async def step1(self):
                return "Step 1"
            
            @step(order=2)
            async def step2(self):
                return "Step 2"
        
        # Should return the class as-is for now
        assert TestWorkflow.__name__ == "TestWorkflow"
    
    def test_step_decorator(self):
        """Test @step decorator marks methods."""
        
        class TestClass:
            @step(order=1)
            def method1(self):
                pass
            
            @step(order=2)
            def method2(self):
                pass
            
            def method3(self):
                pass
        
        assert hasattr(TestClass.method1, "_is_step")
        assert hasattr(TestClass.method1, "_step_order")
        assert TestClass.method1._step_order == 1
        assert TestClass.method2._step_order == 2
        assert not hasattr(TestClass.method3, "_is_step")


class TestAgentRegistry:
    """Test agent registry functionality."""
    
    def test_register_and_get_agent(self):
        """Test registering and retrieving agents."""
        # Clear registry first
        _agent_registry._agents.clear()
        
        @agent("registry_test")
        async def test_agent(self, x):
            return x
        
        register_agent(test_agent)
        
        retrieved = get_agent("registry_test")
        assert retrieved is test_agent
        
        # Non-existent agent
        assert get_agent("nonexistent") is None
    
    def test_registry_list(self):
        """Test listing registered agents."""
        # Clear registry
        _agent_registry._agents.clear()
        
        @agent("agent1")
        async def agent1(self, x):
            return x
        
        @agent("agent2")
        async def agent2(self, x):
            return x
        
        register_agent(agent1)
        register_agent(agent2)
        
        agents = _agent_registry.list()
        assert "agent1" in agents
        assert "agent2" in agents
        assert len(agents) == 2


class TestChainAndParallel:
    """Test chain and parallel decorators."""
    
    def test_chain_decorator(self):
        """Test @chain decorator basic structure."""
        
        @chain("agent1", "agent2")
        async def pipeline(x):
            return x
        
        # Should wrap the function
        assert asyncio.iscoroutinefunction(pipeline)
    
    def test_parallel_decorator(self):
        """Test @parallel decorator basic structure."""
        
        @parallel("agent1", "agent2", "agent3")
        async def multi_process(data):
            return data
        
        # Should wrap the function
        assert asyncio.iscoroutinefunction(multi_process)


class TestDecoratedAgentIntegration:
    """Integration tests for decorated agents."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization_flow(self):
        """Test complete agent initialization flow."""
        # Mock fabric
        mock_fabric = MagicMock()
        mock_fabric.initialize = AsyncMock()
        mock_test_tool = Mock()
        mock_test_tool.name = "mcp:test_tool"
        mock_test_tool.description = "Test"
        mock_fabric.get_tools = Mock(return_value=[mock_test_tool])
        mock_fabric.execute_tool = AsyncMock(return_value={"result": "success"})
        
        # Mock agent
        mock_agent = MagicMock(spec=Agent)
        mock_agent.name = "test"
        mock_agent.arun = AsyncMock(return_value="Agent response")
        
        mock_fabric.create_unified_agent = AsyncMock(return_value=mock_agent)
        
        with patch('agenticraft.fabric.decorators.get_global_fabric', return_value=mock_fabric):
            @agent("integration_test", servers=["http://localhost:3000/mcp"])
            async def test_agent(self, query: str):
                # Test tool access
                result = await self.tools.test_tool(param="value")
                return f"Query: {query}, Tool result: {result}"
            
            # Execute agent
            result = await test_agent("test query")
            
            # Verify initialization
            assert mock_fabric.initialize.called
            config_call = mock_fabric.initialize.call_args[0][0]
            assert "mcp" in config_call
            assert config_call["mcp"]["servers"][0]["url"] == "http://localhost:3000/mcp"
            
            # Verify agent creation
            mock_fabric.create_unified_agent.assert_called_once()
            call_kwargs = mock_fabric.create_unified_agent.call_args[1]
            assert call_kwargs["name"] == "integration_test"
            
            # Verify result
            assert "Tool result: {'result': 'success'}" in result
    
    @pytest.mark.asyncio
    async def test_arun_compatibility(self):
        """Test that decorated agents support arun method."""
        mock_fabric = Mock()
        mock_fabric.initialize = AsyncMock()
        mock_agent = Mock(spec=Agent)
        mock_agent.arun = AsyncMock(return_value="Response")
        mock_fabric.create_unified_agent = AsyncMock(return_value=mock_agent)
        mock_fabric.get_tools = Mock(return_value=[])
        
        with patch('agenticraft.fabric.decorators.get_global_fabric', return_value=mock_fabric):
            @agent("compat_test")
            async def test_agent(self, x):
                return x
            
            # Initialize
            await test_agent("init")
            
            # Use arun
            result = await test_agent.arun("Test prompt")
            assert result == "Response"
            mock_agent.arun.assert_called_with("Test prompt")
