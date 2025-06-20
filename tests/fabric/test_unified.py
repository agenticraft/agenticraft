"""
Tests for Unified Protocol Fabric.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from agenticraft.fabric import (
    UnifiedProtocolFabric,
    MCPAdapter,
    A2AAdapter,
    ProtocolType,
    UnifiedTool,
    ProtocolCapability,
    get_global_fabric,
    initialize_fabric
)
from agenticraft.fabric.legacy import UnifiedToolWrapper
from agenticraft.core.exceptions import ToolError


class TestUnifiedProtocolFabric:
    """Test UnifiedProtocolFabric functionality."""
    
    @pytest.fixture
    def fabric(self):
        """Create a test fabric instance."""
        return UnifiedProtocolFabric()
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client."""
        client = Mock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.get_tools = Mock(return_value=[
            Mock(
                name="test_tool",
                description="Test tool",
                get_definition=Mock(return_value=Mock(model_dump=Mock(return_value={})))
            )
        ])
        client.call_tool = AsyncMock(return_value={"result": "success"})
        client.server_info = Mock(
            name="Test Server",
            version="1.0.0",
            capabilities={"tools": True}
        )
        return client
    
    @pytest.fixture
    def mock_a2a_client(self):
        """Create mock A2A client."""
        client = Mock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.discover_agents = AsyncMock(return_value=[
            Mock(
                id="test_agent",
                skills=[
                    Mock(
                        name="analyze",
                        description="Analyze data",
                        parameters={}
                    )
                ]
            )
        ])
        client.send_task = AsyncMock(return_value={"analysis": "complete"})
        return client
    
    def test_fabric_initialization(self, fabric):
        """Test fabric initializes with default adapters."""
        assert ProtocolType.MCP in fabric.adapters
        assert ProtocolType.A2A in fabric.adapters
        assert isinstance(fabric.adapters[ProtocolType.MCP], MCPAdapter)
        assert isinstance(fabric.adapters[ProtocolType.A2A], A2AAdapter)
    
    @pytest.mark.asyncio
    async def test_initialize_empty_config(self, fabric):
        """Test initialization with empty config."""
        await fabric.initialize()
        assert fabric._initialized
        assert len(fabric.unified_tools) == 0
    
    @pytest.mark.asyncio
    async def test_initialize_with_mcp(self, fabric, mock_mcp_client):
        """Test initialization with MCP configuration."""
        # Mock the MCP adapter
        with patch('agenticraft.protocols.mcp.MCPClient', return_value=mock_mcp_client):
            config = {
                "mcp": {
                    "servers": [{"url": "http://localhost:3000"}]
                }
            }
            
            await fabric.initialize(config)
            
            assert fabric._initialized
            assert "mcp:test_tool" in fabric.unified_tools
            assert mock_mcp_client.connect.called
    
    @pytest.mark.asyncio
    async def test_get_tools_all_protocols(self, fabric):
        """Test getting tools from all protocols."""
        # Add some test tools
        fabric.unified_tools = {
            "mcp:tool1": UnifiedTool("mcp:tool1", "MCP Tool", ProtocolType.MCP, Mock()),
            "a2a:tool2": UnifiedTool("a2a:tool2", "A2A Tool", ProtocolType.A2A, Mock()),
        }
        
        tools = fabric.get_tools()
        assert len(tools) == 2
        assert any(t.name == "mcp:tool1" for t in tools)
        assert any(t.name == "a2a:tool2" for t in tools)
    
    @pytest.mark.asyncio
    async def test_get_tools_filtered_by_protocol(self, fabric):
        """Test getting tools filtered by protocol."""
        # Add test tools
        fabric.unified_tools = {
            "mcp:tool1": UnifiedTool("mcp:tool1", "MCP Tool 1", ProtocolType.MCP, Mock()),
            "mcp:tool2": UnifiedTool("mcp:tool2", "MCP Tool 2", ProtocolType.MCP, Mock()),
            "a2a:tool3": UnifiedTool("a2a:tool3", "A2A Tool", ProtocolType.A2A, Mock()),
        }
        
        mcp_tools = fabric.get_tools(protocol=ProtocolType.MCP)
        assert len(mcp_tools) == 2
        assert all(t.protocol == ProtocolType.MCP for t in mcp_tools)
        
        a2a_tools = fabric.get_tools(protocol=ProtocolType.A2A)
        assert len(a2a_tools) == 1
        assert a2a_tools[0].protocol == ProtocolType.A2A
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_prefix(self, fabric):
        """Test executing tool with protocol prefix."""
        mock_adapter = Mock()
        mock_adapter.execute_tool = AsyncMock(return_value={"result": "success"})
        fabric.adapters[ProtocolType.MCP] = mock_adapter
        
        fabric.unified_tools["mcp:test_tool"] = UnifiedTool(
            "mcp:test_tool",
            "Test tool",
            ProtocolType.MCP,
            Mock()
        )
        
        result = await fabric.execute_tool("mcp:test_tool", param="value")
        
        assert result == {"result": "success"}
        mock_adapter.execute_tool.assert_called_once_with("test_tool", param="value")
    
    @pytest.mark.asyncio
    async def test_execute_tool_without_prefix(self, fabric):
        """Test executing tool without protocol prefix."""
        mock_adapter = Mock()
        mock_adapter.execute_tool = AsyncMock(return_value={"result": "success"})
        fabric.adapters[ProtocolType.MCP] = mock_adapter
        
        fabric.unified_tools["mcp:search"] = UnifiedTool(
            "mcp:search",
            "Search tool",
            ProtocolType.MCP,
            Mock()
        )
        
        # Should find tool even without prefix
        result = await fabric.execute_tool("search", query="test")
        
        assert result == {"result": "success"}
        mock_adapter.execute_tool.assert_called_once_with("search", query="test")
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, fabric):
        """Test executing non-existent tool raises error."""
        with pytest.raises(ToolError, match="Tool not found"):
            await fabric.execute_tool("nonexistent_tool")
    
    @pytest.mark.asyncio
    async def test_create_unified_agent(self, fabric):
        """Test creating unified agent with fabric tools."""
        # Add test tools
        fabric.unified_tools = {
            "mcp:tool1": UnifiedTool("mcp:tool1", "Tool 1", ProtocolType.MCP, Mock()),
            "a2a:tool2": UnifiedTool("a2a:tool2", "Tool 2", ProtocolType.A2A, Mock()),
        }
        
        agent = await fabric.create_unified_agent(
            name="test_agent",
            model="gpt-4"
        )
        
        assert agent.name == "test_agent"
        assert len(agent.tools) == 2
        assert all(isinstance(tool, UnifiedToolWrapper) for tool in agent.tools)
    
    @pytest.mark.asyncio
    async def test_shutdown(self, fabric):
        """Test fabric shutdown."""
        # Mock adapters
        mock_mcp = Mock()
        mock_mcp.disconnect = AsyncMock()
        mock_a2a = Mock()
        mock_a2a.disconnect = AsyncMock()
        
        fabric.adapters[ProtocolType.MCP] = mock_mcp
        fabric.adapters[ProtocolType.A2A] = mock_a2a
        fabric._initialized = True
        
        await fabric.shutdown()
        
        assert not fabric._initialized
        assert len(fabric.unified_tools) == 0
        assert len(fabric.capabilities) == 0
        mock_mcp.disconnect.assert_called_once()
        mock_a2a.disconnect.assert_called_once()


class TestMCPAdapter:
    """Test MCP adapter functionality."""
    
    @pytest.fixture
    def adapter(self):
        """Create MCP adapter instance."""
        return MCPAdapter()
    
    @pytest.fixture
    def mock_client(self):
        """Create mock MCP client."""
        client = Mock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.get_tools = Mock(return_value=[
            Mock(
                name="web_search",
                description="Search the web",
                get_definition=Mock(return_value=Mock(model_dump=Mock(return_value={"type": "tool"})))
            )
        ])
        client.call_tool = AsyncMock(return_value={"results": ["result1", "result2"]})
        client.server_info = Mock(
            name="Test MCP Server",
            version="1.0.0",
            capabilities={"tools": True, "resources": True}
        )
        return client
    
    def test_protocol_type(self, adapter):
        """Test adapter returns correct protocol type."""
        assert adapter.protocol_type == ProtocolType.MCP
    
    @pytest.mark.asyncio
    async def test_connect(self, adapter, mock_client):
        """Test connecting to MCP server."""
        with patch('agenticraft.protocols.mcp.MCPClient', return_value=mock_client):
            config = {"url": "http://localhost:3000"}
            await adapter.connect(config)
            
            assert adapter.client == mock_client
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_without_url(self, adapter):
        """Test connect fails without URL."""
        with pytest.raises(ValueError, match="MCP adapter requires 'url'"):
            await adapter.connect({})
    
    @pytest.mark.asyncio
    async def test_discover_tools(self, adapter, mock_client):
        """Test discovering MCP tools."""
        adapter.client = mock_client
        
        tools = await adapter.discover_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "web_search"
        assert tools[0].description == "Search the web"
        assert tools[0].protocol == ProtocolType.MCP
        assert "web_search" in adapter._tools
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, adapter, mock_client):
        """Test executing MCP tool."""
        adapter.client = mock_client
        
        result = await adapter.execute_tool("web_search", query="test")
        
        mock_client.call_tool.assert_called_once_with("web_search", {"query": "test"})
        assert result == {"results": ["result1", "result2"]}
    
    @pytest.mark.asyncio
    async def test_execute_tool_not_connected(self, adapter):
        """Test executing tool when not connected."""
        with pytest.raises(ToolError, match="MCP client not connected"):
            await adapter.execute_tool("any_tool")
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, adapter, mock_client):
        """Test getting MCP capabilities."""
        adapter.client = mock_client
        adapter._tools = {"tool1": Mock(), "tool2": Mock()}
        
        capabilities = await adapter.get_capabilities()
        
        assert len(capabilities) == 2
        assert capabilities[0].name == "tool_execution"
        assert capabilities[0].protocol == ProtocolType.MCP
        assert capabilities[1].name == "resource_access"


class TestA2AAdapter:
    """Test A2A adapter functionality."""
    
    @pytest.fixture
    def adapter(self):
        """Create A2A adapter instance."""
        return A2AAdapter()
    
    @pytest.fixture
    def mock_client(self):
        """Create mock A2A client."""
        client = Mock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.discover_agents = AsyncMock(return_value=[
            Mock(
                id="agent1",
                skills=[
                    Mock(name="analyze", description="Analyze data", parameters={}),
                    Mock(name="summarize", description="Summarize text", parameters={})
                ]
            ),
            Mock(
                id="agent2", 
                skills=[
                    Mock(name="translate", description="Translate text", parameters={})
                ]
            )
        ])
        client.send_task = AsyncMock(return_value={"status": "completed"})
        return client
    
    def test_protocol_type(self, adapter):
        """Test adapter returns correct protocol type."""
        assert adapter.protocol_type == ProtocolType.A2A
    
    @pytest.mark.asyncio
    async def test_connect_http(self, adapter, mock_client):
        """Test connecting via HTTP."""
        with patch('agenticraft.protocols.a2a.ProtocolClient', return_value=mock_client):
            config = {
                "connection_type": "http",
                "url": "http://localhost:8080"
            }
            await adapter.connect(config)
            
            assert adapter.client == mock_client
            mock_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discover_tools(self, adapter, mock_client):
        """Test discovering A2A tools (agent skills)."""
        adapter.client = mock_client
        
        # Discover agents first
        await adapter._discover_agents()
        
        tools = await adapter.discover_tools()
        
        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "agent1.analyze" in tool_names
        assert "agent1.summarize" in tool_names
        assert "agent2.translate" in tool_names
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, adapter, mock_client):
        """Test executing A2A tool."""
        adapter.client = mock_client
        
        result = await adapter.execute_tool("agent1.analyze", data="test data")
        
        mock_client.send_task.assert_called_once_with(
            "agent1",
            "analyze",
            {"data": "test data"}
        )
        assert result == {"status": "completed"}
    
    @pytest.mark.asyncio
    async def test_execute_tool_invalid_format(self, adapter, mock_client):
        """Test executing tool with invalid name format."""
        adapter.client = mock_client
        
        with pytest.raises(ToolError, match="Invalid A2A tool name format"):
            await adapter.execute_tool("invalid_format")
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, adapter):
        """Test getting A2A capabilities."""
        adapter._agents = {"agent1": Mock(), "agent2": Mock()}
        adapter._tools = {f"tool{i}": Mock() for i in range(5)}
        
        capabilities = await adapter.get_capabilities()
        
        assert len(capabilities) == 3
        cap_names = [c.name for c in capabilities]
        assert "agent_collaboration" in cap_names
        assert "bidirectional_communication" in cap_names
        assert "agent_discovery" in cap_names
        
        # Check metadata
        collab_cap = next(c for c in capabilities if c.name == "agent_collaboration")
        assert collab_cap.metadata["agent_count"] == 2
        assert collab_cap.metadata["skill_count"] == 5


class TestGlobalFabric:
    """Test global fabric functions."""
    
    def test_get_global_fabric(self):
        """Test getting global fabric instance."""
        fabric1 = get_global_fabric()
        fabric2 = get_global_fabric()
        
        assert fabric1 is fabric2  # Same instance
        assert isinstance(fabric1, UnifiedProtocolFabric)
    
    @pytest.mark.asyncio
    async def test_initialize_fabric(self):
        """Test initializing global fabric."""
        config = {"mcp": {"servers": []}}
        
        fabric = await initialize_fabric(config)
        
        assert fabric._initialized
        assert fabric is get_global_fabric()
