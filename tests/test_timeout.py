#!/usr/bin/env python3
"""Test timeout functionality in RestrictedPythonSandbox."""

import asyncio
from agenticraft.security import SandboxManager, SecurityContext, SandboxType


async def test_timeout():
    """Test that timeout works correctly."""
    print("Testing sandbox timeout functionality...")
    
    # Create manager and get sandbox
    manager = SandboxManager()
    await manager.initialize()
    sandbox = await manager.get_sandbox(SandboxType.RESTRICTED)
    
    # Create context with 1 second timeout
    context = SecurityContext(
        user_id="test",
        permissions=["execute"],
        resource_limits={"timeout_seconds": 1}
    )
    
    # Code that should timeout
    timeout_code = """
# Infinite loop to trigger timeout
while True:
    x = 1 + 1
"""
    
    print("Executing infinite loop with 1 second timeout...")
    result = await sandbox.execute_code(timeout_code, context)
    
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
    
    if not result.success and "timeout" in result.error.lower():
        print("✅ Timeout worked correctly!")
    else:
        print("❌ Timeout did not work as expected")
    
    await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(test_timeout())
