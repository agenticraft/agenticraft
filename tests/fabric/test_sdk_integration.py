"""
Tests for Official SDK Integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from agenticraft.fabric import (
    UnifiedProtocolFabric,
    ProtocolType
)
from agenticraft.fabric.legacy import (
    EnhancedUnifiedProtocolFabric as SDKEnabledUnifiedProtocolFabric
)
from agenticraft.fabric.adapters import (
    AdapterFactory,
    SDKPreference,
    MCPOfficialAdapter,
    A2AOfficialAdapter,
    ACPBeeAdapter
)


class TestSDKIntegration:
    """Test SDK integration and migration."""
    
    @pytest.fixture
    def fabric(self):
        """Create test fabric."""
        return SDKEnabledUnifiedProtocolFabric()
    
    def test_sdk_preference_parsing(self):
        """Test parsing of SDK preferences."""
        # String preferences
        fabric = SDKEnabledUnifiedProtocolFabric(
            sdk_preferences={
                'mcp': 'official',
                'a2a': 'hybrid',
                'acp': 'custom'
            }
        )
        
        assert fabric.sdk_preferences[ProtocolType.MCP] == SDKPreference.OFFICIAL
        assert fabric.sdk_preferences[ProtocolType.A2A] == SDKPreference.HYBRID
        assert fabric.sdk_preferences[ProtocolType.ACP] == SDKPreference.CUSTOM
        assert fabric.sdk_preferences[ProtocolType.ANP] == SDKPreference.AUTO  # Default
    
    def test_sdk_preference_enum(self):
        """Test using SDKPreference enum directly."""
        fabric = SDKEnabledUnifiedProtocolFabric(
            sdk_preferences={
                'mcp': SDKPreference.OFFICIAL,
                'a2a': SDKPreference.HYBRID
            }
        )
        
        assert fabric.sdk_preferences[ProtocolType.MCP] == SDKPreference.OFFICIAL
        assert fabric.sdk_preferences[ProtocolType.A2A] == SDKPreference.HYBRID
    
    @pytest.mark.asyncio
    async def test_register_server_with_sdk(self):
        """Test registering server with SDK preference."""
        fabric = SDKEnabledUnifiedProtocolFabric(
            sdk_preferences={'mcp': 'custom'}  # Force custom
        )
        
        # Mock the adapter
        with patch.object(AdapterFactory, 'create_adapter') as mock_create:
            mock_adapter = AsyncMock()
            mock_adapter.connect = AsyncMock()
            mock_adapter.discover_tools = AsyncMock(return_value=[])
            mock_create.return_value = mock_adapter
            
            server_id = await fabric.register_server(
                'mcp',
                {'url': 'http://localhost:3000'}
            )
            
            # Verify factory was called with correct preference
            mock_create.assert_called_once_with(
                ProtocolType.MCP,
                SDKPreference.CUSTOM
            )
            
            assert server_id.startswith('mcp_')
    
    def test_update_sdk_preference(self, fabric):
        """Test updating SDK preference."""
        # Initial preference
        fabric.update_sdk_preference('mcp', 'custom')
        assert fabric.sdk_preferences[ProtocolType.MCP] == SDKPreference.CUSTOM
        
        # Update preference
        fabric.update_sdk_preference('mcp', 'official')
        assert fabric.sdk_preferences[ProtocolType.MCP] == SDKPreference.OFFICIAL
    
    def test_get_sdk_info(self, fabric):
        """Test getting SDK information."""
        fabric.update_sdk_preference('mcp', 'official')
        info = fabric.get_sdk_info()
        
        assert 'preferences' in info
        assert 'availability' in info
        assert 'recommendations' in info
        assert info['preferences']['mcp'] == 'official'
    
    @pytest.mark.asyncio
    async def test_migrate_to_official_sdks(self, fabric):
        """Test migration to official SDKs."""
        with patch.object(AdapterFactory, '_is_sdk_available') as mock_available:
            # Mock MCP as available, others not
            def is_available(protocol):
                return protocol == ProtocolType.MCP
            
            mock_available.side_effect = is_available
            
            # Test migration
            results = await fabric.migrate_to_official_sdks(
                protocols=['mcp', 'a2a'],
                test_mode=True
            )
            
            assert results['mcp'] == True  # Available
            assert results['a2a'] == False  # Not available
    
    @pytest.mark.asyncio
    async def test_hybrid_adapter_fallback(self):
        """Test hybrid adapter fallback functionality."""
        fabric = SDKEnabledUnifiedProtocolFabric(
            sdk_preferences={'mcp': 'hybrid'}
        )
        
        # This would test actual fallback behavior
        # For now, just verify hybrid preference is set
        assert fabric.sdk_preferences[ProtocolType.MCP] == SDKPreference.HYBRID


class TestAdapterFactory:
    """Test the adapter factory."""
    
    def test_get_available_adapters(self):
        """Test checking adapter availability."""
        status = AdapterFactory.get_available_adapters()
        
        assert 'mcp' in status
        assert 'a2a' in status
        assert 'acp' in status
        assert 'anp' in status
        
        for protocol, availability in status.items():
            assert 'official' in availability
            assert 'custom' in availability
            assert 'hybrid' in availability
    
    def test_get_best_adapter(self):
        """Test adapter recommendation."""
        # Without features
        best = AdapterFactory.get_best_adapter(ProtocolType.MCP)
        assert best in ['official', 'custom', 'hybrid']
        
        # With features
        best = AdapterFactory.get_best_adapter(
            ProtocolType.MCP,
            features=['tools', 'streaming']
        )
        assert best in ['official', 'custom', 'hybrid']
    
    def test_create_adapter_auto(self):
        """Test automatic adapter selection."""
        with patch.object(AdapterFactory, '_is_sdk_available') as mock_available:
            mock_available.return_value = False  # No SDK available
            
            adapter = AdapterFactory.create_adapter(
                ProtocolType.MCP,
                SDKPreference.AUTO
            )
            
            # Should fall back to custom
            assert adapter is not None


class TestOfficialAdapters:
    """Test official SDK adapters (when SDKs are available)."""
    
    @pytest.mark.skipif(
        not AdapterFactory._is_sdk_available(ProtocolType.MCP),
        reason="MCP SDK not installed"
    )
    @pytest.mark.asyncio
    async def test_mcp_official_adapter(self):
        """Test MCP official adapter."""
        adapter = MCPOfficialAdapter()
        
        # Test basic properties
        assert adapter.protocol_type == ProtocolType.MCP
        assert adapter.supports_feature('tools')
        assert adapter.supports_feature('resources')
        assert adapter.supports_feature('prompts')
    
    @pytest.mark.skipif(
        not AdapterFactory._is_sdk_available(ProtocolType.A2A),
        reason="A2A SDK not installed"
    )
    @pytest.mark.asyncio
    async def test_a2a_official_adapter(self):
        """Test A2A official adapter."""
        adapter = A2AOfficialAdapter()
        
        # Test basic properties
        assert adapter.protocol_type == ProtocolType.A2A
        assert adapter.supports_feature('tools')
        assert adapter.supports_feature('discovery')
        assert adapter.supports_feature('trust')
    
    @pytest.mark.asyncio
    async def test_acp_bee_adapter(self):
        """Test ACP Bee framework adapter."""
        adapter = ACPBeeAdapter()
        
        # Test basic properties
        assert adapter.protocol_type == ProtocolType.ACP
        assert adapter.supports_feature('tools')
        assert adapter.supports_feature('workflows')
        assert adapter.supports_feature('sessions')


@pytest.mark.integration
class TestEndToEndSDKMigration:
    """End-to-end tests for SDK migration."""
    
    @pytest.mark.asyncio
    async def test_gradual_migration(self):
        """Test gradual migration strategy."""
        # Phase 1: Start with custom
        fabric = UnifiedProtocolFabric(
            sdk_preferences={
                'mcp': 'custom',
                'a2a': 'custom',
                'acp': 'custom',
                'anp': 'custom'
            }
        )
        
        # Phase 2: Move one to hybrid
        fabric.update_sdk_preference('mcp', 'hybrid')
        assert fabric.sdk_preferences[ProtocolType.MCP] == SDKPreference.HYBRID
        
        # Phase 3: Test official SDK
        with patch.object(AdapterFactory, '_is_sdk_available') as mock:
            mock.return_value = True
            
            results = await fabric.migrate_to_official_sdks(
                protocols=['mcp'],
                test_mode=True
            )
            
            assert results['mcp'] == True
    
    @pytest.mark.asyncio
    async def test_preserve_agenticraft_features(self):
        """Test that AgentiCraft features work with official SDKs."""
        fabric = UnifiedProtocolFabric(
            sdk_preferences={'mcp': 'official'}
        )
        
        # Enable extensions (should work regardless of SDK)
        mesh = await fabric.create_mesh_network(['agent1', 'agent2'])
        assert mesh['status'] == 'active'
        
        consensus = await fabric.enable_consensus(min_agents=3)
        assert consensus['status'] == 'ready'
        
        traces = await fabric.enable_reasoning_traces()
        assert 'chain_of_thought' in traces['collectors']
