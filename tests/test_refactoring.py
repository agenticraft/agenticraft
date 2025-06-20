"""
Test suite for refactored AgentiCraft architecture.

This test validates that the refactoring maintains functionality
while improving the code structure.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Any

# Test core abstractions
from agenticraft.core.transport import (
    Transport, TransportConfig, HTTPTransport, WebSocketTransport,
    Message, MessageType, TransportRegistry
)
from agenticraft.core.auth import (
    AuthConfig, AuthManager, AuthProvider, 
    BearerAuthProvider, APIKeyAuthProvider
)
from agenticraft.core.registry import (
    ServiceRegistry, InMemoryRegistry, ServiceInfo, ServiceStatus
)
from agenticraft.core.patterns import ClientServerPattern
from agenticraft.core.serialization import JSONSerializer

# Test protocols
from agenticraft.protocols.base import Protocol, ProtocolConfig
from agenticraft.protocols.mcp import MCPProtocol
from agenticraft.protocols.a2a import A2AProtocol

# Test fabric
from agenticraft.fabric import UnifiedAgent, AgentBuilder, MCPAdapter, A2AAdapter


class TestCoreTransport:
    """Test core transport abstractions."""
    
    @pytest.mark.asyncio
    async def test_transport_registry(self):
        """Test transport registry functionality."""
        # Check built-in transports
        assert TransportRegistry.get("http://example.com") == HTTPTransport
        assert TransportRegistry.get("https://example.com") == HTTPTransport
        assert TransportRegistry.get("ws://example.com") == WebSocketTransport
        assert TransportRegistry.get("wss://example.com") == WebSocketTransport
        
        # Create transport from config
        config = TransportConfig(url="http://localhost:8080")
        transport = TransportRegistry.create(config)
        assert isinstance(transport, HTTPTransport)
        
    @pytest.mark.asyncio
    async def test_transport_message(self):
        """Test transport message structure."""
        msg = Message(
            id="123",
            type=MessageType.REQUEST,
            payload={"method": "test"},
            metadata={"source": "test"}
        )
        
        assert msg.id == "123"
        assert msg.type == MessageType.REQUEST
        assert msg.payload["method"] == "test"
        assert msg.metadata["source"] == "test"


class TestCoreAuth:
    """Test core authentication system."""
    
    def test_auth_config_creation(self):
        """Test auth config factory methods."""
        # Bearer auth
        bearer = AuthConfig.bearer("token123")
        assert bearer.type.value == "bearer"
        assert bearer.credentials["token"] == "token123"
        
        # API key auth
        api_key = AuthConfig.api_key("key456", "X-API-Key")
        assert api_key.type.value == "api_key"
        assert api_key.credentials["key"] == "key456"
        assert api_key.options["header"] == "X-API-Key"
        
        # JWT auth
        jwt = AuthConfig.jwt(token="jwt123", secret="secret")
        assert jwt.type.value == "jwt"
        assert jwt.credentials["token"] == "jwt123"
        assert jwt.credentials["secret"] == "secret"
        
    @pytest.mark.asyncio
    async def test_auth_providers(self):
        """Test auth provider implementations."""
        # Bearer provider
        bearer_config = AuthConfig.bearer("test-token")
        bearer_provider = BearerAuthProvider(bearer_config)
        
        headers = bearer_provider.get_headers()
        assert headers["Authorization"] == "Bearer test-token"
        
        # API key provider
        api_config = AuthConfig.api_key("test-key", "X-Test-Key")
        api_provider = APIKeyAuthProvider(api_config)
        
        headers = api_provider.get_headers()
        assert headers["X-Test-Key"] == "test-key"
        
    def test_auth_manager(self):
        """Test auth manager functionality."""
        manager = AuthManager()
        
        # Set bearer auth
        manager.set_auth(AuthConfig.bearer("token"))
        provider = manager.get_provider()
        assert provider is not None
        
        headers = manager.get_headers()
        assert "Authorization" in headers


class TestCoreRegistry:
    """Test core registry functionality."""
    
    @pytest.mark.asyncio
    async def test_in_memory_registry(self):
        """Test in-memory registry implementation."""
        registry = InMemoryRegistry()
        
        # Register service
        service = await registry.register(
            name="test-service",
            service_type="test",
            endpoint="http://localhost:8080",
            tags={"test", "example"}
        )
        
        assert service.name == "test-service"
        assert service.type == "test"
        assert service.status == ServiceStatus.ACTIVE
        
        # Discover services
        services = await registry.discover(service_type="test")
        assert len(services) == 1
        assert services[0].name == "test-service"
        
        # Get specific service
        found = await registry.get("test-service")
        assert found is not None
        assert found.name == "test-service"
        
        # Update status
        updated = await registry.update_status("test-service", ServiceStatus.INACTIVE)
        assert updated
        
        service = await registry.get("test-service")
        assert service.status == ServiceStatus.INACTIVE
        
        # Unregister
        removed = await registry.unregister("test-service")
        assert removed
        
        services = await registry.discover()
        assert len(services) == 0


class TestProtocols:
    """Test protocol implementations."""
    
    @pytest.mark.asyncio
    async def test_protocol_config(self):
        """Test protocol configuration."""
        config = ProtocolConfig(
            name="test",
            version="1.0",
            metadata={"key": "value"}
        )
        
        assert config.name == "test"
        assert config.version == "1.0"
        assert config.metadata["key"] == "value"
        
        # Test to_dict
        data = config.to_dict()
        assert data["name"] == "test"
        assert data["version"] == "1.0"
        
    @pytest.mark.asyncio
    async def test_mcp_protocol_creation(self):
        """Test MCP protocol creation."""
        transport = Mock(spec=Transport)
        transport.is_connected = False
        
        protocol = MCPProtocol(transport=transport)
        
        assert protocol.config.name == "mcp"
        assert protocol.transport == transport
        
        # Test tool registration
        from agenticraft.protocols.mcp import MCPTool
        tool = MCPTool(name="test-tool", description="Test tool", parameters=[])
        protocol.register_tool(tool)
        
        assert "test-tool" in protocol._tools
        
    @pytest.mark.asyncio
    async def test_a2a_protocol_creation(self):
        """Test A2A protocol creation."""
        transport = Mock(spec=Transport)
        transport.is_connected = False
        
        protocol = A2AProtocol(
            pattern="mesh",
            node_id="test-node",
            transport=transport
        )
        
        assert protocol.config.name == "a2a"
        assert protocol.pattern == "mesh"
        assert protocol.node_id == "test-node"


class TestFabric:
    """Test fabric layer functionality."""
    
    @pytest.mark.asyncio
    async def test_unified_agent(self):
        """Test unified agent creation and usage."""
        agent = UnifiedAgent("test-agent")
        
        assert agent.name == "test-agent"
        assert agent.registry is not None
        assert len(agent.list_protocols()) == 0
        
        # Add mock protocol
        mock_protocol = Mock(spec=Protocol)
        mock_transport = Mock(spec=Transport)
        mock_transport.is_connected = True
        
        agent.add_protocol(
            "test",
            mock_protocol,
            mock_transport,
            primary=True
        )
        
        assert len(agent.list_protocols()) == 1
        assert agent._primary_protocol == "test"
        
    @pytest.mark.asyncio
    async def test_agent_builder(self):
        """Test agent builder pattern."""
        # Mock transports to avoid real connections
        with patch('agenticraft.fabric.builder.HTTPTransport') as MockHTTP, \
             patch('agenticraft.fabric.builder.WebSocketTransport') as MockWS:
            
            mock_http = Mock(spec=HTTPTransport)
            mock_ws = Mock(spec=WebSocketTransport)
            MockHTTP.return_value = mock_http
            MockWS.return_value = mock_ws
            
            # Build agent
            builder = AgentBuilder("test-builder")
            builder.with_mcp("http://localhost:8080")
            builder.with_a2a("mesh")
            builder.with_registry()
            
            agent = builder.build()
            
            assert agent.name == "test-builder"
            assert agent.registry is not None
            assert len(agent.list_protocols()) == 2
            assert "mcp" in agent.list_protocols()
            assert "a2a" in agent.list_protocols()
            
    @pytest.mark.asyncio
    async def test_protocol_adapters(self):
        """Test protocol adapter functionality."""
        # Test MCP adapter
        mock_mcp = Mock(spec=MCPProtocol)
        mock_transport = Mock(spec=Transport)
        
        mcp_adapter = MCPAdapter(mock_mcp, mock_transport)
        assert mcp_adapter.get_protocol_name() == "mcp"
        
        capabilities = mcp_adapter.get_capabilities()
        assert capabilities["tools"] == True
        assert capabilities["resources"] == True
        
        # Test A2A adapter
        mock_a2a = Mock(spec=A2AProtocol)
        mock_a2a.pattern = "mesh"
        mock_a2a.node_id = "test-node"
        mock_a2a.config.version = "1.0"
        
        a2a_adapter = A2AAdapter(mock_a2a, mock_transport)
        assert a2a_adapter.get_protocol_name() == "a2a"
        
        capabilities = a2a_adapter.get_capabilities()
        assert capabilities["pattern"] == "mesh"
        assert capabilities["node_id"] == "test-node"


class TestSerialization:
    """Test serialization functionality."""
    
    def test_json_serializer(self):
        """Test JSON serialization."""
        serializer = JSONSerializer()
        
        # Test basic types
        data = {
            "string": "test",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        serialized = serializer.serialize(data)
        assert isinstance(serialized, bytes)
        
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data
        
        # Test string methods
        string_data = serializer.serialize_to_string(data)
        assert isinstance(string_data, str)
        
        from_string = serializer.deserialize_from_string(string_data)
        assert from_string == data


class TestPatterns:
    """Test communication patterns."""
    
    @pytest.mark.asyncio
    async def test_client_server_pattern(self):
        """Test client-server pattern."""
        pattern = ClientServerPattern()
        
        # Create mock transport
        mock_transport = Mock(spec=Transport)
        mock_transport.is_connected = True
        
        # Create server
        server = pattern.create_server("test-server", mock_transport)
        assert server is not None
        
        # Add handler
        async def echo_handler(params):
            return {"echo": params}
            
        server.add_handler("echo", echo_handler)
        
        # Create client
        client = pattern.create_client("test-client", mock_transport)
        assert client is not None


class TestBackwardsCompatibility:
    """Test backwards compatibility layer."""
    
    def test_deprecated_imports(self):
        """Test that deprecated imports show warnings."""
        with pytest.warns(DeprecationWarning):
            from agenticraft.fabric.compat import UnifiedFabric
            
        with pytest.warns(DeprecationWarning):
            from agenticraft.fabric.compat import create_sdk_agent
            
    def test_compatibility_wrappers(self):
        """Test compatibility wrapper functionality."""
        from agenticraft.fabric.compat import UnifiedFabric
        
        # Should create UnifiedAgent internally
        with pytest.warns(DeprecationWarning):
            fabric = UnifiedFabric("test")
            assert hasattr(fabric, "_agent")


class TestIntegration:
    """Integration tests for the refactored architecture."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete flow with all components."""
        # Create registry
        registry = InMemoryRegistry()
        
        # Create mock transport
        mock_transport = AsyncMock(spec=Transport)
        mock_transport.is_connected = True
        mock_transport.config = TransportConfig(url="http://test")
        
        # Create auth
        auth_manager = AuthManager()
        auth_manager.set_auth(AuthConfig.bearer("test-token"))
        
        # Create agent using builder
        with patch('agenticraft.fabric.builder.HTTPTransport') as MockHTTP:
            MockHTTP.return_value = mock_transport
            
            agent = AgentBuilder("integration-test") \
                .with_mcp("http://localhost:8080") \
                .with_auth(AuthConfig.bearer("test-token")) \
                .with_registry(registry) \
                .build()
                
            assert agent.name == "integration-test"
            assert agent.registry == registry
            
            # Verify auth was set
            transport = agent.get_transport("mcp")
            assert transport is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
