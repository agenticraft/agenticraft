#!/usr/bin/env python3
"""Test basic RestrictedPythonSandbox functionality."""

import asyncio
from agenticraft.security import SandboxManager, SecurityContext, SandboxType
from agenticraft.security.sandbox.process import RestrictedPythonSandbox


async def test_basic_sandbox():
    """Test basic sandbox execution."""
    print("Testing RestrictedPythonSandbox...")
    
    # Create sandbox directly
    sandbox = RestrictedPythonSandbox()
    await sandbox.initialize()
    
    # Create context
    context = SecurityContext(
        user_id="test",
        permissions=["execute"],
        resource_limits={"timeout_seconds": 5}
    )
    
    # Test 1: Simple execution
    print("\n1. Testing simple execution:")
    code1 = """
result = 2 + 2
message = "Hello"
"""
    result1 = await sandbox.execute_code(code1, context)
    print(f"   Success: {result1.success}")
    print(f"   Result: {result1.result}")
    print(f"   Error: {result1.error}")
    
    # Test 2: Print capture
    print("\n2. Testing print capture:")
    code2 = """
print("Hello from sandbox")
print("Line 2")
output = "done"
"""
    result2 = await sandbox.execute_code(code2, context)
    print(f"   Success: {result2.success}")
    print(f"   Result: {result2.result}")
    
    # Test 3: Timeout test
    print("\n3. Testing timeout (should fail):")
    context_timeout = SecurityContext(
        user_id="test",
        permissions=["execute"],
        resource_limits={"timeout_seconds": 1}
    )
    
    code3 = """
# This should timeout
count = 0
while True:
    count += 1
"""
    result3 = await sandbox.execute_code(code3, context_timeout)
    print(f"   Success: {result3.success}")
    print(f"   Error: {result3.error}")
    print(f"   Has 'timeout' in error: {'timeout' in result3.error.lower() if result3.error else False}")
    
    await sandbox.cleanup()


if __name__ == "__main__":
    asyncio.run(test_basic_sandbox())
