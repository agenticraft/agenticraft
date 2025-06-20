"""
Simple MCP Agent Example - Refactored Architecture

This example demonstrates creating a simple MCP agent using
the new refactored architecture.
"""
import asyncio
import logging

from agenticraft.fabric import create_mcp_agent
from agenticraft.core.auth import AuthConfig

# Enable logging
logging.basicConfig(level=logging.INFO)


async def main():
    """Create and use a simple MCP agent."""
    
    # Create agent with MCP protocol
    agent = create_mcp_agent(
        name="example-agent",
        url="http://localhost:8080",
        auth_config=AuthConfig.bearer("your-api-token")
    )
    
    # Start the agent
    async with agent:
        print(f"Agent '{agent.name}' started")
        
        # List available tools
        tools = await agent.call(
            method="tools/list",
            params={}
        )
        print(f"Available tools: {tools}")
        
        # Call a tool
        result = await agent.call(
            method="tools/call",
            params={
                "name": "calculator",
                "arguments": {
                    "operation": "add",
                    "a": 5,
                    "b": 3
                }
            }
        )
        print(f"Calculator result: {result}")
        
        # Read a resource
        resource = await agent.call(
            method="resources/read",
            params={
                "uri": "file:///example.txt"
            }
        )
        print(f"Resource content: {resource}")
        
        # Check agent health
        health = await agent.health_check()
        print(f"Agent health: {health}")


if __name__ == "__main__":
    asyncio.run(main())
