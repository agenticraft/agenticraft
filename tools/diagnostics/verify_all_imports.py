#!/usr/bin/env python3
"""Test that all fixed imports work correctly."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing all fixed imports...")

errors = []

# Test 1: fabric imports (refactored)
try:
    from agenticraft.fabric import (
        ACPAdapter,
        ANPAdapter,
        EnhancedUnifiedProtocolFabric,
        ProtocolType,
        IProtocolAdapter,
        UnifiedProtocolFabric,
        get_global_fabric,
        initialize_fabric
    )
    print("✅ fabric imports successful")
except ImportError as e:
    errors.append(f"fabric: {e}")
    print(f"❌ fabric import failed: {e}")

# Test 2: protocol_types imports
try:
    from agenticraft.fabric.protocol_types import (
        ProtocolType,
        ProtocolCapability,
        UnifiedTool,
        IProtocolAdapter
    )
    print("✅ protocol_types imports successful")
except ImportError as e:
    errors.append(f"protocol_types: {e}")
    print(f"❌ protocol_types import failed: {e}")

# Test 3: test_enhanced_fabric imports
try:
    from agenticraft.core.exceptions import ToolError
    print("✅ core.exceptions imports successful")
except ImportError as e:
    errors.append(f"core.exceptions: {e}")
    print(f"❌ core.exceptions import failed: {e}")

if not errors:
    print("\n✅ All imports working correctly!")
else:
    print(f"\n❌ {len(errors)} import errors found:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
