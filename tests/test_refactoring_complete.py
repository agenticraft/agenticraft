#!/usr/bin/env python3
"""Test that all refactoring changes work correctly."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing refactored imports...")

errors = []

# Test 1: New imports from fabric package
try:
    from agenticraft.fabric import (
        UnifiedAgent,
        create_mcp_agent,
        create_a2a_agent,
        ProtocolType,
        ProtocolCapability,
        UnifiedTool,
        IProtocolAdapter,
        UnifiedProtocolFabric,
        EnhancedUnifiedProtocolFabric,
        MCPAdapter,
        A2AAdapter,
        ACPAdapter,
        ANPAdapter
    )
    print("✅ Fabric package imports successful")
except ImportError as e:
    errors.append(f"fabric imports: {e}")
    print(f"❌ Fabric import failed: {e}")

# Test 2: Protocol types module
try:
    from agenticraft.fabric.protocol_types import (
        ProtocolType,
        ProtocolCapability,
        UnifiedTool,
        IProtocolAdapter
    )
    print("✅ Protocol types imports successful")
except ImportError as e:
    errors.append(f"protocol_types: {e}")
    print(f"❌ Protocol types import failed: {e}")

# Test 3: Protocol adapters module
try:
    from agenticraft.fabric.protocol_adapters import (
        MCPAdapter,
        A2AAdapter,
        ACPAdapter,
        ANPAdapter,
        WebDIDResolver
    )
    print("✅ Protocol adapters imports successful")
except ImportError as e:
    errors.append(f"protocol_adapters: {e}")
    print(f"❌ Protocol adapters import failed: {e}")

# Test 4: Extensions module
try:
    from agenticraft.fabric.extensions import (
        IProtocolExtension,
        MeshNetworkingExtension,
        ConsensusExtension,
        ReasoningTraceExtension
    )
    print("✅ Extensions imports successful")
except ImportError as e:
    errors.append(f"extensions: {e}")
    print(f"❌ Extensions import failed: {e}")

# Test 5: Legacy module
try:
    from agenticraft.fabric.legacy import (
        UnifiedProtocolFabric,
        EnhancedUnifiedProtocolFabric,
        UnifiedToolWrapper,
        get_global_fabric,
        initialize_fabric
    )
    print("✅ Legacy imports successful")
except ImportError as e:
    errors.append(f"legacy: {e}")
    print(f"❌ Legacy import failed: {e}")

# Test 6: Backwards compatibility - imports from old locations should work
print("\nTesting backwards compatibility...")
try:
    # This should trigger deprecation warnings but still work
    from agenticraft.fabric.compat import (
        UnifiedProtocolFabric as CompatFabric,
        EnhancedUnifiedProtocolFabric as EnhancedCompat
    )
    print("✅ Compatibility layer working")
except ImportError as e:
    errors.append(f"compat layer: {e}")
    print(f"❌ Compatibility layer failed: {e}")

# Test 7: Check that old files don't exist
old_files = [
    "/Users/zahere/Desktop/TLV/agenticraft/agenticraft/fabric/unified.py",
    "/Users/zahere/Desktop/TLV/agenticraft/agenticraft/fabric/unified_enhanced.py"
]

for old_file in old_files:
    if os.path.exists(old_file):
        errors.append(f"Old file still exists: {old_file}")
        print(f"❌ Old file still exists: {old_file}")
    else:
        print(f"✅ Old file removed: {os.path.basename(old_file)}")

if not errors:
    print("\n✅ All refactoring changes successful!")
    print("   - New structure in place")
    print("   - Old files removed")
    print("   - Backwards compatibility maintained")
else:
    print(f"\n❌ {len(errors)} issues found:")
    for error in errors:
        print(f"  - {error}")



if __name__ == "__main__":
    sys.exit(1)