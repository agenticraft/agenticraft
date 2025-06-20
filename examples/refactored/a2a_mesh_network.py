"""
A2A Mesh Network Example - Refactored Architecture

This example demonstrates creating A2A agents in a mesh network
using the new refactored architecture.
"""
import asyncio
import logging

from agenticraft.fabric import create_a2a_agent

# Enable logging
logging.basicConfig(level=logging.INFO)


async def create_mesh_node(name: str, port: int, peers: list = None):
    """Create a mesh network node."""
    agent = create_a2a_agent(
        name=name,
        pattern="mesh",
        peers=peers or [],
        url=f"ws://localhost:{port}/{name}"
    )
    
    return agent


async def main():
    """Create a mesh network with multiple agents."""
    
    # Create three agents in a mesh
    agent1 = await create_mesh_node("agent1", 8001)
    agent2 = await create_mesh_node("agent2", 8002, peers=[f"ws://localhost:8001/agent1"])
    agent3 = await create_mesh_node("agent3", 8003, peers=[
        f"ws://localhost:8001/agent1",
        f"ws://localhost:8002/agent2"
    ])
    
    # Start all agents
    agents = [agent1, agent2, agent3]
    
    try:
        # Start agents
        for agent in agents:
            await agent.start()
            print(f"Started {agent.name}")
        
        # Let network stabilize
        await asyncio.sleep(1)
        
        # Agent1 broadcasts a message
        print("\nAgent1 broadcasting message...")
        await agent1.send(
            {"type": "announcement", "message": "Hello mesh network!"},
            protocol="a2a"
        )
        
        # Agent2 sends direct message to Agent3
        print("\nAgent2 sending direct message to Agent3...")
        response = await agent2.send(
            {"type": "direct", "content": "Private message"},
            target="agent3",
            protocol="a2a"
        )
        print(f"Response: {response}")
        
        # Discover network topology
        print("\nNetwork topology:")
        for agent in agents:
            services = await agent.discover_services(service_type="a2a")
            print(f"{agent.name} sees: {[s['name'] for s in services]}")
        
        # Check health
        print("\nHealth check:")
        for agent in agents:
            health = await agent.health_check()
            print(f"{agent.name}: {health['protocols']['a2a']['connected']}")
            
    finally:
        # Stop all agents
        for agent in agents:
            await agent.stop()
            print(f"Stopped {agent.name}")


if __name__ == "__main__":
    asyncio.run(main())
