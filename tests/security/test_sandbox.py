"""Tests for security sandbox integration."""

import pytest
import asyncio
from agenticraft.core import Agent
from agenticraft.security import SandboxManager, SecurityContext, SandboxType
from agenticraft.security.exceptions import SecurityException


class TestSandboxSecurity:
    """Test sandbox security features."""
    
    @pytest.mark.asyncio
    async def test_basic_sandbox_execution(self):
        """Test basic code execution in sandbox."""
        manager = SandboxManager()
        await manager.initialize()
        
        # Get sandbox
        sandbox = await manager.get_sandbox(SandboxType.RESTRICTED)
        
        # Create security context
        context = SecurityContext(
            user_id="test",
            permissions=["execute"],
            resource_limits={"memory_mb": 128, "timeout_seconds": 5}
        )
        
        # Execute simple code
        code = """
result = 2 + 2
message = "Hello from sandbox"
"""
        result = await sandbox.execute_code(code, context)
        
        assert result.success
        assert result.result["result"] == 4
        assert result.result["message"] == "Hello from sandbox"
    
    @pytest.mark.asyncio
    async def test_code_isolation(self):
        """Test that malicious code cannot escape sandbox."""
        manager = SandboxManager()
        await manager.initialize()
        
        sandbox = await manager.get_sandbox(SandboxType.RESTRICTED)
        context = SecurityContext(user_id="test", permissions=["execute"])
        
        # Try to import dangerous modules
        malicious_code = """
import os
import subprocess
import sys
"""
        result = await sandbox.execute_code(malicious_code, context)
        
        # Should fail or have restricted imports
        assert not result.success or "os" not in result.result
    
    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test resource limit enforcement."""
        manager = SandboxManager()
        await manager.initialize()
        
        sandbox = await manager.get_sandbox(SandboxType.RESTRICTED)
        context = SecurityContext(
            user_id="test",
            permissions=["execute"],
            resource_limits={"timeout_seconds": 1}
        )
        
        # Code that exceeds timeout
        timeout_code = """
# Infinite loop to trigger timeout
while True:
    x = 1 + 1
"""
        result = await sandbox.execute_code(timeout_code, context)
        
        assert not result.success
        assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_agent_secure_execution(self):
        """Test agent with secure execution enabled."""
        # Create agent with sandbox enabled
        agent = Agent(
            name="SecureAgent",
            instructions="You are a secure assistant.",
            sandbox_enabled=True,
            sandbox_type="restricted",
            memory_limit=256
        )
        
        # Test secure code execution
        code = "result = sum([1, 2, 3, 4, 5])"
        result = await agent.execute_secure(code)
        
        assert result == {"result": 15}
    
    @pytest.mark.asyncio
    async def test_agent_secure_tool_execution(self):
        """Test secure tool execution."""
        agent = Agent(
            name="SecureAgent",
            sandbox_enabled=True
        )
        
        # Add a simple tool
        def calculate_sum(numbers: list[int]) -> int:
            """Calculate sum of numbers."""
            return sum(numbers)
        
        agent._tool_registry.register_function(calculate_sum)
        
        # Execute tool securely
        result = await agent.execute_tool_secure(
            "calculate_sum",
            numbers=[10, 20, 30]
        )
        
        assert result == 60
    
    @pytest.mark.asyncio
    async def test_sandbox_manager_availability(self):
        """Test sandbox manager detects available sandbox types."""
        manager = SandboxManager()
        await manager.initialize()
        
        available_types = manager.get_available_types()
        
        # Should at least have restricted sandbox
        assert SandboxType.RESTRICTED in available_types
        
        # Process sandbox depends on platform
        if hasattr(asyncio, "create_subprocess_exec"):
            assert SandboxType.PROCESS in available_types
