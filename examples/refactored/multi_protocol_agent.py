"""
Multi-Protocol Agent Example - Refactored Architecture

This example demonstrates creating an agent that supports both
MCP and A2A protocols using the new builder pattern.
"""
import asyncio
import logging

from agenticraft.fabric import AgentBuilder
from agenticraft.core.auth import AuthConfig
from agenticraft.core.registry import InMemoryRegistry

# Enable logging
logging.basicConfig(level=logging.INFO)


async def main():
    """Create and use a multi-protocol agent."""
    
    # Create a service registry
    registry = InMemoryRegistry()
    
    # Build agent with multiple protocols
    agent = await (AgentBuilder("multi-agent")
        # Add MCP protocol for tool calling
        .with_mcp(
            url="http://localhost:8080",
            auth=AuthConfig.bearer("mcp-token")
        )
        # Add A2A protocol for peer communication
        .with_a2a(
            pattern="mesh",
            peers=["ws://localhost:9001/peer1", "ws://localhost:9002/peer2"]
        )
        # Add service registry
        .with_registry(registry)
        # Set MCP as primary protocol
        .set_primary("mcp")
        # Build and start
        .build_and_start())
    
    try:
        print(f"Multi-protocol agent '{agent.name}' started")
        print(f"Protocols: {agent.list_protocols()}")
        
        # Use MCP protocol to call a tool
        print("\nCalling MCP tool...")
        tool_result = await agent.call(
            method="tools/call",
            params={
                "name": "weather",
                "arguments": {"location": "San Francisco"}
            },
            protocol="mcp"  # Explicitly use MCP
        )
        print(f"Weather: {tool_result}")
        
        # Use A2A protocol to broadcast to peers
        print("\nBroadcasting to A2A network...")
        await agent.send(
            {
                "type": "weather_update",
                "data": tool_result,
                "source": agent.name
            },
            protocol="a2a"  # Explicitly use A2A
        )
        
        # Discover all services across protocols
        print("\nDiscovering services...")
        all_services = await agent.discover_services()
        for service in all_services:
            print(f"- {service['name']} ({service['type']})")
        
        # Bridge protocols - A2A agent requests MCP tool
        print("\nBridging protocols...")
        
        # Simulate A2A peer requesting tool execution
        tool_request = {
            "type": "tool_request",
            "tool": "calculator",
            "args": {"operation": "multiply", "a": 7, "b": 8}
        }
        
        # Agent receives A2A request and forwards to MCP
        mcp_response = await agent.call(
            method="tools/call",
            params={
                "name": tool_request["tool"],
                "arguments": tool_request["args"]
            },
            protocol="mcp"
        )
        
        # Send result back via A2A
        await agent.send(
            {
                "type": "tool_response",
                "result": mcp_response,
                "original_request": tool_request
            },
            protocol="a2a"
        )
        
        # Check health of all protocols
        print("\nHealth check:")
        health = await agent.health_check()
        for proto, status in health["protocols"].items():
            print(f"- {proto}: {'✓' if status['connected'] else '✗'}")
            
    finally:
        # Stop the agent
        await agent.stop()
        print(f"\nMulti-protocol agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
