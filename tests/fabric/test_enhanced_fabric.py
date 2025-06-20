"""
Tests for Enhanced Unified Protocol Fabric with ACP and ANP.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp
import json
from typing import Dict, Any

from agenticraft.fabric import (
    ACPAdapter,
    ANPAdapter,
    EnhancedUnifiedProtocolFabric,
    ProtocolType,
    UnifiedTool,
    ProtocolCapability
)
from agenticraft.fabric.extensions import (
    MeshNetworkingExtension,
    ConsensusExtension,
    ReasoningTraceExtension
)
from agenticraft.fabric.protocol_adapters import WebDIDResolver
from agenticraft.core.exceptions import ToolError


class TestACPAdapter:
    """Test IBM ACP adapter functionality."""
    
    @pytest.fixture
    def adapter(self):
        """Create ACP adapter instance."""
        return ACPAdapter()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock aiohttp response."""
        mock = Mock()
        mock.status = 200
        mock.json = AsyncMock(return_value={})
        mock.text = AsyncMock(return_value="")
        return mock
    
    def test_protocol_type(self, adapter):
        """Test adapter returns correct protocol type."""
        assert adapter.protocol_type == ProtocolType.ACP
    
    @pytest.mark.asyncio
    async def test_connect(self, adapter):
        """Test connecting to ACP server."""
        config = {
            "url": "http://localhost:9000",
            "timeout": 60,
            "auth": {"token": "test-token"}
        }
        
        # Mock aiohttp session
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # Mock agent discovery
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=[
                {
                    "id": "agent1",
                    "capabilities": [
                        {"name": "process", "description": "Process data"},
                        {"name": "analyze", "description": "Analyze input"}
                    ]
                }
            ])
            
            mock_session.get = Mock(return_value=AsyncMock().__aenter__.return_value)
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock()
            
            await adapter.connect(config)
            
            assert adapter.base_url == "http://localhost:9000"
            assert adapter.session is not None
            assert len(adapter._agents) == 1
            assert len(adapter._tools) == 2
    
    @pytest.mark.asyncio
    async def test_discover_tools(self, adapter):
        """Test discovering ACP tools."""
        # Set up test data
        adapter._tools = {
            "agent1.process": UnifiedTool(
                name="agent1.process",
                description="Process data",
                protocol=ProtocolType.ACP,
                original_tool={}
            )
        }
        
        tools = await adapter.discover_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "agent1.process"
        assert tools[0].protocol == ProtocolType.ACP
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, adapter):
        """Test executing ACP tool."""
        adapter.session = Mock()
        adapter._sessions["agent1"] = "session-123"
        
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})
        
        adapter.session.post = Mock(return_value=AsyncMock().__aenter__.return_value)
        adapter.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        adapter.session.post.return_value.__aexit__ = AsyncMock()
        
        result = await adapter.execute_tool("agent1.process", data="test")
        
        assert result == {"result": "success"}
        
        # Verify the call
        adapter.session.post.assert_called_once()
        call_args = adapter.session.post.call_args
        assert "agents/agent1/execute" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_execute_tool_invalid_format(self, adapter):
        """Test executing tool with invalid name format."""
        adapter.session = Mock()
        
        with pytest.raises(ToolError, match="Invalid ACP tool name format"):
            await adapter.execute_tool("invalid_format")
    
    @pytest.mark.asyncio
    async def test_session_management(self, adapter):
        """Test ACP session creation and management."""
        adapter.session = Mock()
        
        # Mock session creation
        mock_response = Mock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={"session_id": "new-session-456"})
        
        adapter.session.post = Mock(return_value=AsyncMock().__aenter__.return_value)
        adapter.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        adapter.session.post.return_value.__aexit__ = AsyncMock()
        
        session_id = await adapter._get_or_create_session("agent2")
        
        assert session_id == "new-session-456"
        assert adapter._sessions["agent2"] == "new-session-456"
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, adapter):
        """Test getting ACP capabilities."""
        adapter._agents = {"agent1": {}, "agent2": {}}
        adapter._tools = {f"tool{i}": Mock() for i in range(5)}
        
        capabilities = await adapter.get_capabilities()
        
        assert len(capabilities) == 3
        cap_names = [c.name for c in capabilities]
        assert "rest_communication" in cap_names
        assert "session_management" in cap_names
        assert "multipart_messages" in cap_names
        
        # Check metadata
        rest_cap = next(c for c in capabilities if c.name == "rest_communication")
        assert rest_cap.metadata["agent_count"] == 2
        assert rest_cap.metadata["capability_count"] == 5


class TestANPAdapter:
    """Test ANP adapter functionality."""
    
    @pytest.fixture
    def adapter(self):
        """Create ANP adapter instance."""
        return ANPAdapter()
    
    def test_protocol_type(self, adapter):
        """Test adapter returns correct protocol type."""
        assert adapter.protocol_type == ProtocolType.ANP
    
    @pytest.mark.asyncio
    async def test_connect(self, adapter):
        """Test connecting to ANP network."""
        config = {
            "ipfs_gateway": "https://ipfs.io",
            "did_method": "web",
            "create_did": True,
            "agent_name": "test-agent",
            "endpoint": "http://localhost:8000",
            "capabilities": ["search", "analyze"]
        }
        
        # Mock DID resolver
        with patch.object(adapter, '_create_agent_did', return_value="did:web:agenticraft.io:agents:test-agent"):
            await adapter.connect(config)
            
            assert adapter.ipfs_gateway == "https://ipfs.io"
            assert adapter.did_resolver is not None
            assert adapter._local_did == "did:web:agenticraft.io:agents:test-agent"
    
    @pytest.mark.asyncio
    async def test_connect_unsupported_did_method(self, adapter):
        """Test connecting with unsupported DID method."""
        config = {
            "did_method": "unsupported"
        }
        
        with pytest.raises(ValueError, match="Unsupported DID method"):
            await adapter.connect(config)
    
    @pytest.mark.asyncio
    async def test_discover_tools(self, adapter):
        """Test discovering ANP tools."""
        # Set up test data
        adapter._tools = {
            "researcher.search": UnifiedTool(
                name="researcher.search",
                description="Search the web",
                protocol=ProtocolType.ANP,
                original_tool={}
            ),
            "researcher.analyze": UnifiedTool(
                name="researcher.analyze",
                description="Analyze data",
                protocol=ProtocolType.ANP,
                original_tool={}
            )
        }
        
        tools = await adapter.discover_tools()
        
        assert len(tools) == 2
        assert all(t.protocol == ProtocolType.ANP for t in tools)
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, adapter):
        """Test executing ANP tool."""
        # Set up test agent
        adapter._agents = {
            "did:web:example.com:agents:researcher": {
                "did": "did:web:example.com:agents:researcher",
                "name": "researcher",
                "endpoint": "https://example.com/agents/researcher",
                "capabilities": [{"name": "search"}]
            }
        }
        
        result = await adapter.execute_tool("researcher.search", query="test")
        
        assert result["status"] == "success"
        assert result["capability"] == "search"
        assert "did:web:example.com:agents:researcher" in result["agent"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_agent_not_found(self, adapter):
        """Test executing tool when agent not found."""
        adapter._agents = {}
        
        with pytest.raises(ToolError, match="ANP agent not found"):
            await adapter.execute_tool("unknown.search", query="test")
    
    @pytest.mark.asyncio
    async def test_create_agent_did(self, adapter):
        """Test creating agent DID."""
        config = {
            "agent_name": "test-bot",
            "endpoint": "http://localhost:9999",
            "capabilities": ["chat", "analyze"]
        }
        
        did = await adapter._create_agent_did(config)
        
        assert did == "did:web:agenticraft.io:agents:test-bot"
        assert adapter._local_did is None  # Not set by this method
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, adapter):
        """Test getting ANP capabilities."""
        adapter._agents = {"did1": {}, "did2": {}}
        
        capabilities = await adapter.get_capabilities()
        
        assert len(capabilities) == 3
        cap_names = [c.name for c in capabilities]
        assert "decentralized_discovery" in cap_names
        assert "did_identity" in cap_names
        assert "trustless_verification" in cap_names


class TestEnhancedUnifiedProtocolFabric:
    """Test enhanced fabric with all protocols and extensions."""
    
    @pytest.fixture
    def fabric(self):
        """Create enhanced fabric instance."""
        return EnhancedUnifiedProtocolFabric()
    
    def test_all_adapters_registered(self, fabric):
        """Test all 4 protocol adapters are registered."""
        assert ProtocolType.MCP in fabric.adapters
        assert ProtocolType.A2A in fabric.adapters
        assert ProtocolType.ACP in fabric.adapters
        assert ProtocolType.ANP in fabric.adapters
    
    def test_extensions_registered(self, fabric):
        """Test AgentiCraft extensions are registered."""
        assert "mesh_networking" in fabric.extensions
        assert "consensus" in fabric.extensions
        assert "reasoning_traces" in fabric.extensions
    
    @pytest.mark.asyncio
    async def test_create_mesh_network(self, fabric):
        """Test creating mesh network extension."""
        result = await fabric.create_mesh_network(
            agents=["agent1", "agent2", "agent3"],
            topology="ring"
        )
        
        assert "mesh_id" in result
        assert result["agents"] == ["agent1", "agent2", "agent3"]
        assert result["topology"] == "ring"
        assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_enable_consensus(self, fabric):
        """Test enabling consensus extension."""
        result = await fabric.enable_consensus(
            consensus_type="pbft",
            min_agents=5
        )
        
        assert "consensus_id" in result
        assert result["type"] == "pbft"
        assert result["min_agents"] == 5
        assert result["status"] == "ready"
    
    @pytest.mark.asyncio
    async def test_enable_reasoning_traces(self, fabric):
        """Test enabling reasoning trace extension."""
        result = await fabric.enable_reasoning_traces(level="verbose")
        
        assert "trace_id" in result
        assert result["level"] == "verbose"
        assert "chain_of_thought" in result["collectors"]
    
    @pytest.mark.asyncio
    async def test_enable_invalid_extension(self, fabric):
        """Test enabling non-existent extension."""
        with pytest.raises(ValueError, match="Extension not found"):
            await fabric.enable_extension("non_existent")


class TestProtocolExtensions:
    """Test individual protocol extensions."""
    
    def test_mesh_networking_extension(self):
        """Test mesh networking extension."""
        ext = MeshNetworkingExtension()
        assert ext.name == "mesh_networking"
    
    def test_consensus_extension(self):
        """Test consensus extension."""
        ext = ConsensusExtension()
        assert ext.name == "consensus"
    
    def test_reasoning_trace_extension(self):
        """Test reasoning trace extension."""
        ext = ReasoningTraceExtension()
        assert ext.name == "reasoning_traces"


class TestWebDIDResolver:
    """Test Web DID resolver."""
    
    @pytest.fixture
    def resolver(self):
        """Create DID resolver instance."""
        return WebDIDResolver()
    
    @pytest.mark.asyncio
    async def test_resolve_did(self, resolver):
        """Test resolving DID."""
        did_doc = await resolver.resolve("did:web:example.com:agents:test")
        
        assert "@context" in did_doc
        assert did_doc["id"] == "did:web:example.com:agents:test"
        assert "verificationMethod" in did_doc
        assert "service" in did_doc


class TestFullProtocolIntegration:
    """Integration tests with all protocols."""
    
    @pytest.mark.asyncio
    async def test_all_protocols_config(self):
        """Test initializing fabric with all protocols."""
        fabric = EnhancedUnifiedProtocolFabric()
        
        config = {
            "mcp": {
                "servers": [{"url": "http://localhost:3000"}]
            },
            "a2a": {
                "connection_type": "http",
                "url": "http://localhost:8080"
            },
            "acp": {
                "url": "http://localhost:9000",
                "auth": {"token": "test"}
            },
            "anp": {
                "did_method": "web",
                "ipfs_gateway": "https://ipfs.io"
            }
        }
        
        # Mock all protocol connections
        with patch.object(fabric.adapters[ProtocolType.MCP], 'connect', new_callable=AsyncMock):
            with patch.object(fabric.adapters[ProtocolType.A2A], 'connect', new_callable=AsyncMock):
                with patch.object(fabric.adapters[ProtocolType.ACP], 'connect', new_callable=AsyncMock):
                    with patch.object(fabric.adapters[ProtocolType.ANP], 'connect', new_callable=AsyncMock):
                        await fabric.initialize(config)
                        
                        assert fabric._initialized
                        
                        # Verify all protocols were connected
                        for protocol_type in [ProtocolType.MCP, ProtocolType.A2A, ProtocolType.ACP, ProtocolType.ANP]:
                            fabric.adapters[protocol_type].connect.assert_called()
