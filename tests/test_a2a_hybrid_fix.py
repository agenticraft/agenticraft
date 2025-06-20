#!/usr/bin/env python3
"""Test the A2AHybridAdapter fix"""

import sys
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

import asyncio
from agenticraft.fabric.adapters import SDKPreference, AdapterFactory
from agenticraft.fabric.protocol_types import ProtocolType

async def test_a2a_hybrid_adapter_fix():
    """Test that A2AHybridAdapter has the get_capabilities method."""
    print("🧪 Testing A2AHybridAdapter Fix")
    print("=" * 50)
    
    # Test creating the adapter
    print("\n1️⃣ Testing A2AHybridAdapter creation:")
    try:
        adapter = AdapterFactory.create_adapter(
            ProtocolType.A2A,
            SDKPreference.HYBRID
        )
        print("✅ Created A2AHybridAdapter successfully")
        
        # Test that it has the get_capabilities method
        print("\n2️⃣ Testing get_capabilities method:")
        capabilities = await adapter.get_capabilities()
        print(f"✅ get_capabilities returned: {capabilities}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(test_a2a_hybrid_adapter_fix())
    
    if success:
        print("\n✅ The A2AHybridAdapter fix is working correctly!")
        print("You can now run the failing test.")
    else:
        print("\n❌ The fix needs more work.")
    

    sys.exit(0 if success else 1)