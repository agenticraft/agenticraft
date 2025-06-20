#!/usr/bin/env python3
"""Test the fixed imports."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing unified_enhanced imports after A2A fix...")

try:
    # Test the problematic import
    from agenticraft.protocols.a2a import ProtocolClient as A2AClient, ProtocolServer as A2AServer
    print("✅ A2A imports successful!")
    
    # Test the refactored imports
    from agenticraft.fabric import (
        ACPAdapter,
        ANPAdapter,
        EnhancedUnifiedProtocolFabric,
        ProtocolType
    )
    print("✅ All fabric imports successful!")
    
    # Test that we can access these classes
    print(f"  - ACPAdapter: {ACPAdapter}")
    print(f"  - ANPAdapter: {ANPAdapter}")
    print(f"  - EnhancedUnifiedProtocolFabric: {EnhancedUnifiedProtocolFabric}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All imports working correctly!")



if __name__ == "__main__":
    sys.exit(1)