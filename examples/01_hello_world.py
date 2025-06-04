#!/usr/bin/env python3
"""Hello World example for AgentiCraft.

This example demonstrates the simplest possible agent creation
and usage in AgentiCraft.
"""

from agenticraft import Agent


def main():
    """Run a simple agent example."""
    # Create a simple agent
    agent = Agent(
        name="HelloAgent",
        instructions="You are a friendly AI assistant who loves to help."
    )
    
    # Note: This is a mock example since we haven't fully implemented providers
    print("AgentiCraft Hello World Example")
    print("=" * 40)
    print(f"Created agent: {agent}")
    print(f"Agent ID: {agent.id}")
    print(f"Agent name: {agent.name}")
    print(f"Model: {agent.config.model}")
    print()
    
    # In a real implementation, this would call the LLM
    print("To run the agent, you would call:")
    print('  response = agent.run("Hello, how are you?")')
    print('  print(response.content)')
    print('  print(response.reasoning)')
    print()
    print("Note: Full LLM provider implementation is pending.")


if __name__ == "__main__":
    main()
