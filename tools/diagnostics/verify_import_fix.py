#!/usr/bin/env python3
"""Test that the import fix works."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing fixed imports...")

try:
    # Import from refactored locations
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
    
    print("✅ Successfully imported all classes from refactored modules!")
    print(f"  - ACPAdapter: {ACPAdapter}")
    print(f"  - ANPAdapter: {ANPAdapter}")
    print(f"  - EnhancedUnifiedProtocolFabric: {EnhancedUnifiedProtocolFabric}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print("\n✅ Import fix successful! The test file should now work.")
