"""Tests for Agent functionality"""

import pytest
from agenticraft import Agent, Tool


class TestAgent:
    """Test Agent class"""
    
    def test_agent_creation(self):
        """Test agent creation"""
        agent = Agent(name="TestAgent", model="gpt-4")
        assert agent.config.name == "TestAgent"
        assert agent.config.model == "gpt-4"
        assert agent.config.temperature == 0.7
    
    def test_add_tool(self, agent, calculator_tool):
        """Test adding tools to agent"""
        agent.add_tool(calculator_tool)
        assert "calculator" in agent.tools
        assert agent.tools["calculator"] == calculator_tool
    
    @pytest.mark.asyncio
    async def test_agent_run(self, agent):
        """Test agent run"""
        response = await agent.run("Hello")
        assert "TestAgent" in response
        assert "Hello" in response
    
    @pytest.mark.asyncio
    async def test_agent_think(self, agent):
        """Test agent thinking process"""
        thoughts = await agent.think("Calculate 2+2")
        assert "understanding" in thoughts
        assert "tools_needed" in thoughts
        assert "approach" in thoughts
