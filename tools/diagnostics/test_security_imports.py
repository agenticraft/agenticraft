#!/usr/bin/env python3
"""Quick test to verify security module imports work."""

import sys
import traceback

try:
    print("Testing security module imports...")
    
    # Test basic imports
    from agenticraft.security import (
        SandboxManager,
        SecurityContext,
        SandboxType,
        SecurityException
    )
    print("✓ Basic security imports successful")
    
    # Test creating instances
    manager = SandboxManager()
    print("✓ SandboxManager created")
    
    context = SecurityContext(
        user_id="test",
        permissions=["execute"],
        resource_limits={"memory_mb": 128, "timeout_seconds": 5}
    )
    print("✓ SecurityContext created")
    
    # Test sandbox types
    print(f"✓ Available sandbox types: {[t.value for t in SandboxType]}")
    
    print("\n✅ All security module imports working correctly!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
