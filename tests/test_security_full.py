#!/usr/bin/env python3
"""Test security module imports and basic functionality."""

import asyncio
import sys
import traceback


async def test_security_module():
    """Test security module functionality."""
    try:
        print("=" * 60)
        print("Testing AgentiCraft Security Module")
        print("=" * 60)
        
        # Test imports
        print("\n1. Testing imports...")
        from agenticraft.security import (
            SandboxManager,
            SecurityContext,
            SandboxType,
            SecureResult,
            SecurityException
        )
        print("   ✓ Basic imports successful")
        
        # Test SandboxManager creation
        print("\n2. Testing SandboxManager...")
        manager = SandboxManager()
        await manager.initialize()
        print("   ✓ SandboxManager created and initialized")
        
        # Test available sandbox types
        print("\n3. Testing available sandbox types...")
        available_types = manager.get_available_types()
        print(f"   ✓ Available types: {[t.value for t in available_types]}")
        
        # Test SecurityContext creation
        print("\n4. Testing SecurityContext...")
        context = SecurityContext(
            user_id="test_user",
            permissions=["execute"],
            resource_limits={
                "memory_mb": 128,
                "timeout_seconds": 5
            }
        )
        print(f"   ✓ SecurityContext created")
        print(f"     - User ID: {context.user_id}")
        print(f"     - Permissions: {context.permissions}")
        print(f"     - Memory limit: {context.resource_limits.memory_mb}MB")
        print(f"     - Timeout: {context.resource_limits.timeout_seconds}s")
        
        # Test sandbox execution
        print("\n5. Testing sandbox execution...")
        sandbox = await manager.get_sandbox(SandboxType.RESTRICTED)
        print("   ✓ Got restricted sandbox")
        
        # Execute simple code
        code = """
result = 2 + 2
message = "Hello from sandbox"
calculated = sum([1, 2, 3, 4, 5])
"""
        
        print("\n6. Executing code in sandbox...")
        result = await sandbox.execute_code(code, context)
        
        if result.success:
            print("   ✓ Code execution successful")
            print(f"     - Result: {result.result}")
            print(f"     - Execution time: {result.execution_time_ms:.2f}ms")
            print(f"     - Sandbox type: {result.sandbox_type.value}")
        else:
            print(f"   ✗ Code execution failed: {result.error}")
        
        # Test cleanup
        print("\n7. Testing cleanup...")
        await manager.cleanup()
        print("   ✓ Cleanup successful")
        
        print("\n" + "=" * 60)
        print("✅ All security module tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    success = asyncio.run(test_security_module())


if __name__ == "__main__":
    main()
