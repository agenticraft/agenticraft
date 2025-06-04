#!/usr/bin/env python3
"""Tool usage example for AgentiCraft.

This example demonstrates how to create and use tools with agents.
"""

from agenticraft import Agent, tool


# Define some simple tools
@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    try:
        # Safe evaluation with limited scope
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool(name="get_time", description="Get the current time")
def current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%I:%M %p")


@tool
def word_count(text: str) -> int:
    """Count the number of words in a text."""
    return len(text.split())


def main():
    """Run an agent with tools example."""
    # Create an agent with tools
    agent = Agent(
        name="ToolAgent",
        instructions="You are a helpful assistant with calculation and utility tools.",
        tools=[calculate, current_time, word_count]
    )
    
    print("AgentiCraft Tool Usage Example")
    print("=" * 40)
    print(f"Created agent: {agent}")
    print()
    
    # Show registered tools
    print("Registered tools:")
    for tool_name in agent._tool_registry.list_tools():
        tool_obj = agent._tool_registry.get(tool_name)
        print(f"  - {tool_name}: {tool_obj.description}")
    print()
    
    # Test tools directly
    print("Testing tools directly:")
    print(f"  calculate('42 * 17 + 238') = {calculate('42 * 17 + 238')}")
    print(f"  current_time() = {current_time()}")
    print(f"  word_count('Hello world from AgentiCraft') = {word_count('Hello world from AgentiCraft')}")
    print()
    
    print("In a real implementation, the agent would:")
    print('  1. Receive a prompt like "What is 42 * 17 + 238?"')
    print('  2. Recognize it needs the calculate tool')
    print('  3. Call the tool with the expression')
    print('  4. Return the result in natural language')


if __name__ == "__main__":
    main()
