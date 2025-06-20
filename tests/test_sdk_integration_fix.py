#!/usr/bin/env python3
"""Test the SDK integration fix"""

import sys
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

from agenticraft.fabric import (
    UnifiedProtocolFabric,
    EnhancedUnifiedProtocolFabric,
    SDKPreference,
    ProtocolType
)

def test_sdk_integration_fix():
    """Test that SDK integration is working correctly."""
    print("🧪 Testing SDK Integration Fix")
    print("=" * 50)
    
    # Test 1: Creating fabric with SDK preferences (string)
    print("\n1️⃣ Testing string SDK preferences:")
    try:
        fabric1 = EnhancedUnifiedProtocolFabric(
            sdk_preferences={
                'mcp': 'official',
                'a2a': 'hybrid',
                'acp': 'custom'
            }
        )
        print("✅ Created fabric with string preferences")
        
        # Check preferences were parsed correctly
        assert fabric1.sdk_preferences[ProtocolType.MCP] == SDKPreference.OFFICIAL
        assert fabric1.sdk_preferences[ProtocolType.A2A] == SDKPreference.HYBRID
        assert fabric1.sdk_preferences[ProtocolType.ACP] == SDKPreference.CUSTOM
        assert fabric1.sdk_preferences[ProtocolType.ANP] == SDKPreference.AUTO  # Default
        print("✅ Preferences parsed correctly")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Using SDKPreference enum directly
    print("\n2️⃣ Testing enum SDK preferences:")
    try:
        fabric2 = EnhancedUnifiedProtocolFabric(
            sdk_preferences={
                'mcp': SDKPreference.OFFICIAL,
                'a2a': SDKPreference.HYBRID
            }
        )
        print("✅ Created fabric with enum preferences")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Testing update_sdk_preference
    print("\n3️⃣ Testing update_sdk_preference:")
    try:
        fabric1.update_sdk_preference('mcp', 'custom')
        assert fabric1.sdk_preferences[ProtocolType.MCP] == SDKPreference.CUSTOM
        print("✅ Updated SDK preference successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 4: Testing get_sdk_info
    print("\n4️⃣ Testing get_sdk_info:")
    try:
        info = fabric1.get_sdk_info()
        print(f"✅ Got SDK info: {list(info.keys())}")
        assert 'preferences' in info
        assert 'availability' in info
        assert 'recommendations' in info
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 5: Test base UnifiedProtocolFabric also works
    print("\n5️⃣ Testing base UnifiedProtocolFabric:")
    try:
        base_fabric = UnifiedProtocolFabric(
            sdk_preferences={'mcp': 'official'}
        )
        print("✅ Base fabric also supports SDK preferences")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n🎉 All SDK integration tests passed!")
    return True

if __name__ == "__main__":
    success = test_sdk_integration_fix()
    if success:
        print("\n✅ The SDK integration fix is working correctly!")
        print("You can now run the failing test.")
    else:
        print("\n❌ The fix needs more work.")
    

    sys.exit(0 if success else 1)