"""Example: Secure Agent Execution with Sandbox

This example demonstrates how to use AgentiCraft's security features
to run agents and workflows in a sandboxed environment.
"""

import asyncio
from agenticraft import Agent
from agenticraft.workflows import ResearchTeam
from agenticraft.security import SecurityContext, SandboxType


async def basic_secure_agent():
    """Basic example of secure agent execution."""
    print("=== Basic Secure Agent Example ===\n")
    
    # Create an agent with sandbox enabled
    agent = Agent(
        name="SecureAssistant",
        instructions="You are a helpful assistant that can execute code safely.",
        model="gpt-4",
        sandbox_enabled=True,
        sandbox_type="restricted",  # Use restricted Python sandbox
        memory_limit=256,  # 256MB memory limit
        cpu_limit=25.0     # 25% CPU limit
    )
    
    # Execute code securely
    print("Executing safe code in sandbox...")
    safe_code = """
# Calculate fibonacci sequence
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = [fibonacci(i) for i in range(10)]
"""
    
    try:
        result = await agent.execute_secure(safe_code)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Try malicious code (will be blocked)
    print("\nTrying malicious code (should fail)...")
    malicious_code = """
import os
os.system('ls /')  # Try to access filesystem
"""
    
    try:
        result = await agent.execute_secure(malicious_code)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Blocked: {e}")


async def secure_workflow_example():
    """Example of secure workflow execution with user context."""
    print("\n=== Secure Workflow Example ===\n")
    
    # Create a research team
    team = ResearchTeam(
        size=3,
        name="SecureResearchTeam"
    )
    
    # Create user context with permissions
    user_context = {
        "user_id": "alice@example.com",
        "permissions": ["execute_workflow", "read_results"],
        "resource_limits": {
            "memory_mb": 512,
            "timeout_seconds": 60
        }
    }
    
    # Execute research with security context
    print("Executing research workflow with user context...")
    try:
        report = await team.research(
            topic="Best practices for secure AI systems",
            depth="standard",
            user_context=user_context
        )
        
        print(f"Research completed by user: {user_context['user_id']}")
        print(f"Executive Summary: {report['executive_summary'][:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Try with insufficient permissions
    print("\nTrying with insufficient permissions...")
    limited_context = {
        "user_id": "guest@example.com",
        "permissions": ["read_results"],  # Missing execute_workflow
    }
    
    try:
        report = await team.research(
            topic="Another topic",
            user_context=limited_context
        )
    except Exception as e:
        print(f"Blocked: {e}")


async def sandbox_types_example():
    """Example showing different sandbox types."""
    print("\n=== Sandbox Types Example ===\n")
    
    from agenticraft.security import SandboxManager
    
    # Initialize sandbox manager
    manager = SandboxManager()
    await manager.initialize()
    
    # Check available sandbox types
    available_types = manager.get_available_types()
    print(f"Available sandbox types: {[t.value for t in available_types]}")
    
    # Test each available sandbox
    for sandbox_type in available_types:
        print(f"\nTesting {sandbox_type.value} sandbox...")
        
        sandbox = await manager.get_sandbox(sandbox_type)
        context = SecurityContext(
            user_id="test",
            permissions=["execute"]
        )
        
        # Simple test code
        test_code = "result = 'Hello from ' + '" + sandbox_type.value + "'"
        result = await sandbox.execute_code(test_code, context)
        
        if result.success:
            print(f"Success: {result.result}")
            print(f"Execution time: {result.execution_time_ms:.2f}ms")
        else:
            print(f"Failed: {result.error}")
    
    # Cleanup
    await manager.cleanup()


async def main():
    """Run all examples."""
    await basic_secure_agent()
    await secure_workflow_example()
    await sandbox_types_example()


if __name__ == "__main__":
    asyncio.run(main())
