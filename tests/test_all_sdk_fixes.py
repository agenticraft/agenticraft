#!/usr/bin/env python3
"""Final test for all SDK integration fixes"""

import sys
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

import asyncio
from agenticraft.fabric import (
    EnhancedUnifiedProtocolFabric,
    SDKPreference,
    ProtocolType
)

def test_all_sdk_fixes():
    """Test all SDK integration fixes."""
    print("🧪 Testing All SDK Integration Fixes")
    print("=" * 60)
    
    success = True
    
    # Test 1: Creating fabric with SDK preferences
    print("\n1️⃣ Testing fabric creation with SDK preferences:")
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
    
    # Test 2: Test A2AHybridAdapter
    print("\n2️⃣ Testing A2AHybridAdapter:")
    try:
        from agenticraft.fabric.adapters import AdapterFactory
        adapter = AdapterFactory.create_adapter(
            ProtocolType.A2A,
            SDKPreference.HYBRID
        )
        print("✅ Created A2AHybridAdapter")
        
        # Test that it has get_capabilities
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        capabilities = loop.run_until_complete(adapter.get_capabilities())
        print(f"✅ get_capabilities works: {capabilities}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # Test 3: Test SDK info
    print("\n3️⃣ Testing SDK info:")
    try:
        info = fabric.get_sdk_info()
        print(f"✅ Got SDK info with keys: {list(info.keys())}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        success = False
    
    return success

if __name__ == "__main__":
    success = test_all_sdk_fixes()
    
    if success:
        print("\n🎉 All SDK integration fixes are working!")
        print("✅ You can now run the full test suite.")
    else:
        print("\n❌ Some fixes still need work.")
    

    sys.exit(0 if success else 1)