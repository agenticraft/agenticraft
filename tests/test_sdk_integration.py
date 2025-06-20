"""Test the SDK integration and unified protocol fabric."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from agenticraft.fabric import (
    UnifiedProtocolFabric,
    ProtocolType,
    get_global_fabric,
    initialize_fabric
)
from agenticraft.fabric.decorators import agent
from agenticraft.fabric.protocol_adapters import MCPAdapter, A2AAdapter
from agenticraft.fabric.protocol_types import UnifiedTool


class TestUnifiedProtocolFabric:
    """Test the unified protocol fabric."""
    
    @pytest.mark.asyncio
    async def test_fabric_initialization(self):
        """Test basic fabric initialization."""
        fabric = UnifiedProtocolFabric()
        assert not fabric._initialized
        
        # Initialize with empty config
        await fabric.initialize({})
        assert fabric._initialized
        
        # Check default adapters registered
        assert ProtocolType.MCP in fabric.adapters
        assert ProtocolType.A2A in fabric.adapters
    
    @pytest.mark.asyncio
    async def test_mcp_adapter_connection(self):
        """Test MCP adapter connection."""
        adapter = MCPAdapter()
        
        # Mock MCPClient
        with patch('agenticraft.fabric.protocol_adapters.MCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.connect = AsyncMock()
            mock_client.get_tools = Mock(return_value=[])
            
            config = {"url": "http://localhost:3000"}
            await adapter.connect(config)
            
            assert adapter.client is not None
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tool_discovery(self):
        """Test tool discovery across protocols."""
        fabric = UnifiedProtocolFabric()
        
        # Mock adapters
        mock_mcp_adapter = AsyncMock()
        mock_mcp_adapter.protocol_type = ProtocolType.MCP
        mock_mcp_adapter.discover_tools = AsyncMock(return_value=[
            UnifiedTool(
                name="web_search",
                description="Search the web",
                protocol=ProtocolType.MCP,
                original_tool=Mock()
            )
        ])
        
        mock_a2a_adapter = AsyncMock()
        mock_a2a_adapter.protocol_type = ProtocolType.A2A
        mock_a2a_adapter.discover_tools = AsyncMock(return_value=[
            UnifiedTool(
                name="agent1.analyze",
                description="Analyze data",
                protocol=ProtocolType.A2A,
                original_tool=Mock()
            )
        ])
        
        fabric.adapters = {
            ProtocolType.MCP: mock_mcp_adapter,
            ProtocolType.A2A: mock_a2a_adapter
        }
        
        await fabric._discover_all_tools()
        
        # Check tools are prefixed
        assert "mcp:web_search" in fabric.unified_tools
        assert "a2a:agent1.analyze" in fabric.unified_tools
        
        # Check tool count
        assert len(fabric.unified_tools) == 2
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution through fabric."""
        fabric = UnifiedProtocolFabric()
        
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_adapter.execute_tool = AsyncMock(return_value="search results")
        
        # Add tool
        tool = UnifiedTool(
            name="mcp:web_search",
            description="Search",
            protocol=ProtocolType.MCP,
            original_tool=Mock()
        )
        fabric.unified_tools["mcp:web_search"] = tool
        fabric.adapters[ProtocolType.MCP] = mock_adapter
        
        # Execute tool
        result = await fabric.execute_tool("mcp:web_search", query="test")
        
        assert result == "search results"
        mock_adapter.execute_tool.assert_called_once_with("web_search", query="test")
    
    @pytest.mark.asyncio
    async def test_decorator_agent_creation(self):
        """Test creating agents with decorators."""
        # Create decorated agent
        @agent(
            "test_agent",
            servers=["http://localhost:3000/mcp"],
            model="gpt-4"
        )
        async def my_agent(self, prompt: str):
            return f"Processed: {prompt}"
        
        # Check agent properties
        assert my_agent.config.name == "test_agent"
        assert my_agent.config.servers == ["http://localhost:3000/mcp"]
        assert my_agent.config.model == "gpt-4"
        
        # Mock fabric initialization
        with patch('agenticraft.fabric.decorators.get_global_fabric') as mock_get_fabric:
            mock_fabric = AsyncMock()
            mock_fabric.initialize = AsyncMock()
            mock_fabric.create_unified_agent = AsyncMock()
            mock_get_fabric.return_value = mock_fabric
            
            # Call agent
            result = await my_agent("test prompt")
            assert result == "Processed: test prompt"
    
    @pytest.mark.asyncio
    async def test_tool_proxy(self):
        """Test natural tool access via proxy."""
        from agenticraft.fabric.decorators import ToolProxy
        
        # Mock fabric
        mock_fabric = Mock()
        mock_fabric.get_tools = Mock(return_value=[
            UnifiedTool(
                name="mcp:web_search",
                description="Search",
                protocol=ProtocolType.MCP,
                original_tool=Mock()
            )
        ])
        mock_fabric.execute_tool = AsyncMock(return_value="results")
        
        # Create proxy
        proxy = ToolProxy(Mock(), mock_fabric)
        
        # Access tool
        web_search = proxy.web_search
        assert callable(web_search)
        
        # Execute tool
        result = await web_search(query="test")
        assert result == "results"
        mock_fabric.execute_tool.assert_called_once_with("mcp:web_search", query="test")
    
    @pytest.mark.asyncio 
    async def test_protocol_capabilities(self):
        """Test getting protocol capabilities."""
        fabric = UnifiedProtocolFabric()
        
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_capability = Mock()
        mock_capability.name = "tool_execution"
        mock_capability.description = "Execute tools"
        mock_adapter.get_capabilities = AsyncMock(return_value=[mock_capability])
        
        fabric.adapters[ProtocolType.MCP] = mock_adapter
        
        await fabric._discover_all_capabilities()
        
        caps = fabric.get_capabilities(ProtocolType.MCP)
        assert ProtocolType.MCP in caps
        assert len(caps[ProtocolType.MCP]) == 1
        assert caps[ProtocolType.MCP][0].name == "tool_execution"


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(test_basic_functionality())


async def test_basic_functionality():
    """Basic functionality test without pytest."""
    print("Testing Unified Protocol Fabric...")
    
    # Test 1: Create fabric
    fabric = UnifiedProtocolFabric()
    print("✓ Created fabric")
    
    # Test 2: Initialize
    await fabric.initialize({})
    print("✓ Initialized fabric")
    
    # Test 3: Check protocols
    protocols = fabric.get_available_protocols()
    assert ProtocolType.MCP in protocols
    assert ProtocolType.A2A in protocols
    print(f"✓ Available protocols: {[p.value for p in protocols]}")
    
    # Test 4: Shutdown
    await fabric.shutdown()
    print("✓ Shutdown complete")
    
    print("\nAll tests passed!")
