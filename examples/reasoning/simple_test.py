#!/usr/bin/env python3
"""
Simple test script for reasoning patterns.
Start with this to verify your setup is working.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from agenticraft.agents.reasoning import ReasoningAgent


async def test_chain_of_thought():
    """Simple Chain of Thought test."""
    print("\n=== Testing Chain of Thought ===\n")

    # Select provider NAME (not object)
    if os.getenv("OPENAI_API_KEY"):
        provider_name = "openai"
        print("Using OpenAI")
    elif os.getenv("ANTHROPIC_API_KEY"):
        provider_name = "anthropic"
        print("Using Anthropic")
    else:
        provider_name = "ollama"
        print("Using Ollama (local)")

    # Create agent with provider name
    agent = ReasoningAgent(
        name="TestAgent",
        reasoning_pattern="chain_of_thought",
        provider=provider_name,  # Pass provider NAME, not object
        model=(
            "gpt-4"
            if provider_name == "openai"
            else "claude-3-opus-20240229" if provider_name == "anthropic" else "llama2"
        ),
    )

    # Simple problem
    problem = "If I have 5 apples and buy 3 more, then give away 2, how many do I have?"

    print(f"Problem: {problem}\n")
    print("Thinking...")

    # Get response
    response = await agent.think_and_act(problem)

    # Show reasoning steps
    if response.reasoning_steps:
        print("\nReasoning Steps:")
        for step in response.reasoning_steps:
            print(f"{step.number}. {step.description}")

    print(f"\nAnswer: {response.content}")

    return response


async def test_tree_of_thoughts():
    """Simple Tree of Thoughts test."""
    print("\n=== Testing Tree of Thoughts ===\n")

    # Select provider NAME
    if os.getenv("OPENAI_API_KEY"):
        provider_name = "openai"
        model = "gpt-4"
    elif os.getenv("ANTHROPIC_API_KEY"):
        provider_name = "anthropic"
        model = "claude-3-opus-20240229"
    else:
        provider_name = "ollama"
        model = "llama2"

    # Create agent
    agent = ReasoningAgent(
        name="CreativeAgent",
        reasoning_pattern="tree_of_thoughts",
        pattern_config={"max_depth": 2, "beam_width": 2},
        provider=provider_name,  # Pass provider NAME
        model=model,
    )

    # Creative problem
    problem = "Come up with 3 creative uses for a paperclip besides holding paper."

    print(f"Problem: {problem}\n")
    print("Exploring ideas...")

    # Get response
    response = await agent.think_and_act(problem)

    print(f"\nBest Solution: {response.content}")

    return response


async def test_react():
    """Simple ReAct test with mock tools."""
    print("\n=== Testing ReAct Pattern ===\n")

    # Import from correct location
    from agenticraft.core.tool import BaseTool, ToolDefinition

    # Create a simple mock tool
    class SimpleCalculator(BaseTool):
        name = "calculator"
        description = "Basic calculator"

        async def arun(self, expression: str) -> str:
            try:
                result = eval(expression, {"__builtins__": {}})
                return f"Result: {result}"
            except:
                return "Error in calculation"

        def get_definition(self):
            return ToolDefinition(
                name=self.name,
                description=self.description,
                parameters={
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
            )

    # Select provider NAME
    if os.getenv("OPENAI_API_KEY"):
        provider_name = "openai"
        model = "gpt-4"
    elif os.getenv("ANTHROPIC_API_KEY"):
        provider_name = "anthropic"
        model = "claude-3-opus-20240229"
    else:
        provider_name = "ollama"
        model = "llama2"

    # Create agent with tool
    agent = ReasoningAgent(
        name="CalculatorAgent",
        reasoning_pattern="react",
        tools=[SimpleCalculator()],
        provider=provider_name,  # Pass provider NAME
        model=model,
    )

    # Problem requiring tool use
    problem = "What is 15% of 80?"

    print(f"Problem: {problem}\n")
    print("Thinking and acting...")

    # Get response
    response = await agent.think_and_act(problem)

    print(f"\nAnswer: {response.content}")

    return response


async def main():
    """Run all tests."""
    print("AgentiCraft Reasoning Patterns Test")
    print("=" * 50)

    # Check environment
    if not any(
        [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("AGENTICRAFT_OPENAI_API_KEY"),
            os.getenv("AGENTICRAFT_ANTHROPIC_API_KEY"),
        ]
    ):
        print("\n⚠️  No API keys found in environment.")
        print("Will attempt to use Ollama (local).")
        print("Make sure Ollama is running: ollama serve")
        print("And you have a model: ollama pull llama2\n")

        # Quick Ollama check
        try:
            import httpx

            response = httpx.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code != 200:
                print("❌ Ollama is not running properly!")
                return
        except:
            print("❌ Cannot connect to Ollama!")
            print("Please run: ollama serve")
            return

    # Run tests
    tests = [
        ("Chain of Thought", test_chain_of_thought),
        ("Tree of Thoughts", test_tree_of_thoughts),
        ("ReAct Pattern", test_react),
    ]

    for name, test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback

            traceback.print_exc()

        print("\n" + "-" * 50)

    print("\n✅ Tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
