"""
Basic AgentiCraft Example.

This is a minimal example showing how to create and use an agent.
"""

import asyncio

from agenticraft import Agent, ReasoningAgent
from agenticraft.providers import get_provider
from agenticraft.tools.core import calculator_tool, search_tool


async def main():
    """Run a simple agent example."""
    # Create a provider (defaults to OpenAI)
    provider = get_provider("openai")

    # Create a simple agent
    agent = Agent("Assistant", provider=provider)

    # Add some tools
    agent.add_tool(calculator_tool)
    agent.add_tool(search_tool)

    # Run the agent
    print("Simple Agent Example")
    print("-" * 50)

    result = await agent.run("What is 123 * 456?")
    print("Question: What is 123 * 456?")
    print(f"Answer: {result.answer}")
    print()

    # Create a reasoning agent
    reasoning_agent = ReasoningAgent("Reasoning Assistant", provider=provider)
    reasoning_agent.add_tool(calculator_tool)

    print("Reasoning Agent Example")
    print("-" * 50)

    result = await reasoning_agent.think_and_act(
        "If I save $500 per month for 2 years with 5% annual interest, how much will I have?"
    )

    print(
        "Question: If I save $500 per month for 2 years with 5% annual interest, how much will I have?"
    )
    print(f"Answer: {result.answer}")
    print(f"\nReasoning Steps: {len(result.reasoning.steps)}")

    for i, step in enumerate(result.reasoning.steps, 1):
        print(f"  Step {i}: {step.description}")
        print(f"    Confidence: {step.confidence:.2f}")
        if step.tools:
            print(f"    Tools used: {', '.join(step.tools)}")


# For the CLI to find and run this agent
agent = Agent("CLI Agent", provider=get_provider("openai"))
agent.add_tool(calculator_tool)
agent.add_tool(search_tool)


if __name__ == "__main__":
    asyncio.run(main())
