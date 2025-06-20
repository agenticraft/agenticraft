#!/usr/bin/env python3
"""Example: Using AgentiCraft with Security Sandbox"""

import asyncio
import sys

sys.path.insert(0, '/Users/zahere/Desktop/TLV/agenticraft')

from agenticraft import Agent
from agenticraft.security import SecurityContext, SandboxType
from agenticraft.security.sandbox import get_sandbox_manager


async def example_direct_sandbox():
    """Example of using sandbox directly."""
    print("\n🔐 Example 1: Direct Sandbox Usage")
    print("-" * 40)
    
    # Get sandbox manager
    manager = get_sandbox_manager()
    
    # Show available types
    available = manager.get_available_types()
    print(f"Available sandbox types: {[t.value for t in available]}")
    
    # Use process sandbox
    sandbox = await manager.get_sandbox(SandboxType.PROCESS)
    
    # Create security context
    context = SecurityContext(
        user_id="alice",
        permissions=["execute"],
        resource_limits={
            "memory_mb": 128,
            "cpu_percent": 25.0,
            "timeout_seconds": 5
        }
    )
    
    # Execute safe code
    code = """
# Calculate Fibonacci sequence
def fib(n):
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result

fibonacci = fib(10)
print(f"Fibonacci: {fibonacci}")
"""
    
    print("\nExecuting Fibonacci calculation...")
    result = await sandbox.execute_code(code, context)
    
    if result.success:
        print(f"✅ Success! Result: {result.result}")
        print(f"   Execution time: {result.execution_time_ms:.2f}ms")
    else:
        print(f"❌ Failed: {result.error}")


async def example_secure_agent():
    """Example of using secure agent."""
    print("\n\n🤖 Example 2: Secure Agent")
    print("-" * 40)
    
    # Create a secure agent
    agent = Agent(
        name="SecureCalculator",
        instructions="You are a secure calculator that can execute Python code safely.",
        model="gpt-4",  # or any model
        sandbox_enabled=True,
        sandbox_type="process",
        memory_limit=256,
        cpu_limit=50.0
    )
    
    print(f"Created secure agent: {agent.name}")
    print(f"Sandbox enabled: {agent.config.sandbox_enabled}")
    print(f"Memory limit: {agent.config.memory_limit}MB")
    
    # Execute some calculations
    code = """
import math

# Safe calculations
results = {
    'sqrt_2': math.sqrt(2),
    'pi': math.pi,
    'factorial_5': math.factorial(5),
    'powers_of_2': [2**i for i in range(10)]
}
"""
    
    print("\nExecuting mathematical calculations...")
    try:
        result = await agent.execute_secure(code)
        print(f"✅ Calculations completed: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_security_violations():
    """Example showing security violations being blocked."""
    print("\n\n🛡️ Example 3: Security Violations")
    print("-" * 40)
    
    manager = get_sandbox_manager()
    sandbox = await manager.get_sandbox(SandboxType.PROCESS)
    
    context = SecurityContext(
        user_id="hacker",
        permissions=["execute"],
        resource_limits={"memory_mb": 128, "timeout_seconds": 2}
    )
    
    # Test various violations
    violations = [
        ("File System Access", """
import os
files = os.listdir('/')
"""),
        ("Network Access", """
import urllib.request
data = urllib.request.urlopen('http://example.com').read()
"""),
        ("System Commands", """
import subprocess
output = subprocess.check_output(['whoami'])
"""),
        ("Resource Exhaustion", """
# Try to use too much memory
huge_list = ['x' * 1000000 for _ in range(1000)]
"""),
        ("Infinite Loop", """
while True:
    pass
"""),
    ]
    
    for name, code in violations:
        print(f"\nTesting: {name}")
        result = await sandbox.execute_code(code, context)
        
        if result.success:
            print(f"  ❌ SECURITY ISSUE: {name} was not blocked!")
        else:
            print(f"  ✅ Blocked successfully: {result.error[:100]}...")


async def example_docker_sandbox():
    """Example using Docker sandbox if available."""
    print("\n\n🐳 Example 4: Docker Sandbox (if available)")
    print("-" * 40)
    
    manager = get_sandbox_manager()
    available = manager.get_available_types()
    
    if SandboxType.DOCKER not in available:
        print("Docker sandbox not available. Install with: pip install docker")
        return
    
    print("Docker sandbox is available!")
    sandbox = await manager.get_sandbox(SandboxType.DOCKER)
    
    context = SecurityContext(
        user_id="docker_user",
        permissions=["execute"],
        resource_limits={
            "memory_mb": 256,
            "cpu_percent": 50.0,
            "timeout_seconds": 10,
            "network_disabled": True
        }
    )
    
    code = """
import platform
import sys

info = {
    'platform': platform.platform(),
    'python_version': sys.version,
    'container': 'Docker',
    'isolation': 'Full container isolation'
}

print("Running in Docker container!")
for key, value in info.items():
    print(f"{key}: {value}")
"""
    
    print("\nExecuting in Docker container...")
    result = await sandbox.execute_code(code, context)
    
    if result.success:
        print(f"✅ Success! Container output:")
        print(f"{result.result}")
    else:
        print(f"❌ Failed: {result.error}")


async def main():
    """Run all examples."""
    print("🔐 AgentiCraft Security Sandbox Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await example_direct_sandbox()
        await example_secure_agent()
        await example_security_violations()
        await example_docker_sandbox()
        
        print("\n" + "=" * 50)
        print("✅ Examples completed!")
        print("\nTo use in your code:")
        print("1. Enable sandbox in Agent: sandbox_enabled=True")
        print("2. Use execute_secure() for sandboxed execution")
        print("3. Set appropriate resource limits")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
