"""
Hello World example for AgentiCraft
"""

import asyncio
from agenticraft import Agent


async def main():
    # Create a simple agent
    agent = Agent(name="HelloBot", model="gpt-3.5-turbo")
    
    # Run the agent
    response = await agent.run("Hello, world!")
    print(f"Agent says: {response}")


if __name__ == "__main__":
    asyncio.run(main())
