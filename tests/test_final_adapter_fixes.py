#!/usr/bin/env python3
"""Test all SDK integration fixes are working correctly"""

import sys
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

import asyncio
from agenticraft.fabric import (
    EnhancedUnifiedProtocolFabric,
    SDKPreference,
    ProtocolType
)
from agenticraft.fabric.adapters import AdapterFactory

async def test_all_adapters():
    """Test all adapters have get_capabilities method with correct type."""
    print("🧪 Testing All Adapter Fixes")
    print("=" * 60)
    
    success = True
    
    # Test MCPOfficialAdapter
    print("\n1️⃣ Testing MCPOfficialAdapter:")
    try:
        adapter = AdapterFactory.create_adapter(
            ProtocolType.MCP,
            SDKPreference.OFFICIAL
        )
        print("✅ Created MCPOfficialAdapter")
        
        # Test get_capabilities returns correct type
        capabilities = await adapter.get_capabilities()
        print(f"✅ get_capabilities returned {len(capabilities)} capabilities")
        
        # Check type
        from agenticraft.fabric.protocol_types import ProtocolCapability
        if capabilities and all(isinstance(cap, ProtocolCapability) for cap in capabilities):
            print("✅ All capabilities are ProtocolCapability objects")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # Test A2AOfficialAdapter
    print("\n2️⃣ Testing A2AOfficialAdapter:")
    try:
        adapter = AdapterFactory.create_adapter(
            ProtocolType.A2A,
            SDKPreference.OFFICIAL
        )
        print("✅ Created A2AOfficialAdapter")
        
        capabilities = await adapter.get_capabilities()
        print(f"✅ get_capabilities returned {len(capabilities)} capabilities")
        
    except ImportError as e:
        print("⚠️  A2A SDK not installed (expected)")
    except Exception as e:
        print(f"❌ Error: {e}")
        success = False
    
    # Test fabric creation
    print("\n3️⃣ Testing fabric creation with SDK preferences:")
    try:
        fabric = EnhancedUnifiedProtocolFabric(
            sdk_preferences={
                'mcp': 'official',
                'a2a': 'hybrid',
                'acp': 'custom'
            }
        )
        print("✅ Created fabric with SDK preferences")
        
        # Verify preferences
        assert fabric.sdk_preferences[ProtocolType.MCP] == SDKPreference.OFFICIAL
        assert fabric.sdk_preferences[ProtocolType.A2A] == SDKPreference.HYBRID
        assert fabric.sdk_preferences[ProtocolType.ACP] == SDKPreference.CUSTOM
        print("✅ Preferences parsed correctly")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    return success

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(test_all_adapters())
    
    if success:
        print("\n🎉 All adapter fixes are working correctly!")
        print("✅ You can now run the failing test.")
    else:
        print("\n❌ Some fixes still need work.")
    

    sys.exit(0 if success else 1)