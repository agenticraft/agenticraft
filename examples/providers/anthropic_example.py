"""Example: Using Anthropic provider with AgentiCraft.

This example demonstrates how to use the Anthropic provider with Claude models
for various tasks including basic chat, tool calling, system prompts, and
advanced features.

Requirements:
    pip install agenticraft anthropic
    export ANTHROPIC_API_KEY="your-api-key"
"""

import asyncio
import os

from dotenv import load_dotenv

from agenticraft import Agent

# Load environment variables from .env file
load_dotenv()


# Example 1: Basic Usage
async def basic_example():
    """Basic example using Anthropic provider."""
    print("=== Basic Anthropic Example ===")

    # Create agent with provider configuration
    agent = Agent(
        "Claude Assistant",
        provider="anthropic",
        model="claude-3-opus-20240229",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Simple query
    response = await agent.arun(
        "Explain the difference between machine learning and deep learning."
    )
    print(f"Claude: {response.content}")


# Example 2: Using Different Claude Models
async def model_selection_example():
    """Example showing different Claude models."""
    print("\n=== Model Selection Example ===")

    # Using Claude 3 Opus (most capable)
    opus_agent = Agent(provider="anthropic", model="claude-3-opus-20240229")
    response = await opus_agent.arun("Write a haiku about programming")
    print(f"Opus: {response.content}")

    # Using Claude 3 Sonnet (balanced)
    sonnet_agent = Agent(provider="anthropic", model="claude-3-sonnet-20240229")
    response = await sonnet_agent.arun("Write a haiku about programming")
    print(f"\nSonnet: {response.content}")

    # Using Claude 3 Haiku (fastest)
    haiku_agent = Agent(provider="anthropic", model="claude-3-haiku-20240307")
    response = await haiku_agent.arun("Write a haiku about programming")
    print(f"\nHaiku: {response.content}")


# Example 3: System Prompts and Roles
async def system_prompt_example():
    """Example using system prompts with Anthropic."""
    print("\n=== System Prompt Example ===")

    agent = Agent(
        "Python Expert",
        provider="anthropic",
        model="claude-3-haiku-20240307",  # Using faster model to avoid timeouts
        instructions="""You are an expert Python developer with 20 years of experience.
        You follow PEP 8 style guidelines and write clean, efficient, well-documented code.
        Always include type hints and docstrings.""",
        timeout=30,  # Increase timeout if needed
    )

    # Simpler prompt to reduce response time
    response = await agent.arun("Write a simple Python hello world function")
    print(f"Response:\n{response.content}")


# Example 4: Tool Usage with Wrapper Pattern (Reliable Approach)
async def tool_calling_example():
    """Example of tool usage with Anthropic using the reliable wrapper pattern."""
    print("\n=== Tool Usage Example (Wrapper Pattern) ===")
    print("Using WorkflowAgent with tool wrappers for reliable tool usage\n")

    from agenticraft.agents import WorkflowAgent

    # Define a simple tool wrapper
    class SimpleToolWrapper:
        def __init__(self, name: str, func):
            self.name = name
            self.func = func

        def create_handler(self):
            def handler(agent, step, context):
                params = context.get(f"{self.name}_params", {})
                try:
                    result = self.func(**params)
                    context[f"{self.name}_result"] = result
                    return f"Calculated: {result}"
                except Exception as e:
                    return f"Error: {e}"

            return handler

    # Define calculation function
    def calculate(expression: str) -> float:
        """Safely evaluate a mathematical expression."""
        try:
            # Only allow safe operations
            allowed = {"__builtins__": {}, "sqrt": lambda x: x**0.5}
            result = eval(expression, allowed)
            return float(result)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")

    # Create workflow agent
    agent = WorkflowAgent(
        name="Calculator",
        instructions="You perform calculations using the provided tools.",
        provider="anthropic",
        model="claude-3-haiku-20240307",  # Using cheaper model
    )

    # Create and register tool
    calc_tool = SimpleToolWrapper("calculate", calculate)
    agent.register_handler("calc", calc_tool.create_handler())

    # Example 1: Simple calculation
    workflow = agent.create_workflow("math_demo")
    workflow.add_step(name="calc1", handler="calc", action="Calculating square root")
    workflow.add_step(name="calc2", handler="calc", action="Calculating percentage")

    # Execute calculations
    context = {"calculate_params": {"expression": "144 ** 0.5"}}
    result = await agent.execute_workflow(workflow, context=context)
    print(f"Square root of 144: {context.get('calculate_result', 'N/A')}")

    # Second calculation
    context["calculate_params"] = {"expression": "850 * 0.15"}
    workflow2 = agent.create_workflow("percentage")
    workflow2.add_step(name="calc", handler="calc")
    result = await agent.execute_workflow(workflow2, context=context)
    print(f"15% of 850: {context.get('calculate_result', 'N/A')}")

    print("\n✅ Tool usage working correctly with wrapper pattern!")
    print("This approach is reliable and recommended for production use.")


# Example 5: Conversation with Context
async def conversation_example():
    """Example of a multi-turn conversation."""
    print("\n=== Conversation Example ===")

    agent = Agent(
        "Conversational Claude",
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        temperature=0.7,
    )

    # Simulate a conversation about a coding project
    messages = [
        "I'm building a web scraper in Python. What libraries would you recommend?",
        "I chose BeautifulSoup. How do I handle dynamic content?",
        "Great! Now how do I handle rate limiting to be respectful to the server?",
        "Can you show me a simple example combining all these concepts?",
    ]

    for message in messages:
        print(f"\nUser: {message}")
        response = await agent.arun(message)
        print(f"Assistant: {response.content}")


# Example 6: Advanced Parameters
async def advanced_parameters_example():
    """Example using advanced Anthropic parameters."""
    print("\n=== Advanced Parameters Example ===")

    # NOTE: AgentiCraft doesn't support passing parameters in arun() calls
    # Instead, create different agents with different parameters
    # Low temperature for factual responses
    factual_agent = Agent(
        "Factual Claude",
        provider="anthropic",
        model="claude-3-haiku-20240307",
        temperature=0.1,
        max_tokens=100,
    )

    response = await factual_agent.arun(
        "List the planets in our solar system in order from the sun"
    )
    print(f"Factual (low temp): {response.content}")

    # High temperature for creative responses
    creative_agent = Agent(
        "Creative Claude",
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        temperature=0.9,
        max_tokens=150,
    )

    response = await creative_agent.arun("Write a creative story opening about a robot")
    print(f"\nCreative (high temp): {response.content}")

    # Agent with stop sequences
    list_agent = Agent(
        "List Claude",
        provider="anthropic",
        model="claude-3-haiku-20240307",
        temperature=0.5,
        stop=["\n4."],  # Stop after 3 items
    )

    response = await list_agent.arun("List 3 programming languages:\n1.")
    print(f"\nWith stop sequence: {response.content}")


# Example 7: Error Handling
async def error_handling_example():
    """Example of proper error handling."""
    print("\n=== Error Handling Example ===")

    # Test with invalid API key
    try:
        agent = Agent("Test Agent", provider="anthropic", api_key="invalid-key")
        response = await agent.arun("Hello")
    except Exception as e:
        print(f"Expected error: {e}")

    # Test with missing API key
    try:
        import os

        original_key = os.environ.get("ANTHROPIC_API_KEY")
        if original_key:
            del os.environ["ANTHROPIC_API_KEY"]

        agent = Agent(provider="anthropic", model="claude-3-haiku-20240307")
        response = await agent.arun("Hello")
    except Exception as e:
        print(f"Missing key error: {e}")
    finally:
        # Restore key if it existed
        if "original_key" in locals() and original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key

    # Test with valid key
    if os.getenv("ANTHROPIC_API_KEY"):
        agent = Agent(
            "Test Agent", provider="anthropic", model="claude-3-haiku-20240307"
        )
        response = await agent.arun("Say hello!")
        print(f"Success: {response.content}")
    else:
        print("Please set ANTHROPIC_API_KEY environment variable")


# Example 8: Streaming Responses (Future)
async def streaming_example():
    """Example of streaming responses (coming soon)."""
    print("\n=== Streaming Example ===")
    print("Note: Streaming support coming in v0.2.0!")

    # This is how streaming will work:
    # provider = AnthropicProvider()
    # agent = Agent("Streaming Claude", provider=provider)
    #
    # async for chunk in agent.stream("Tell me a long story"):
    #     print(chunk, end="", flush=True)
    # print()


# Example 9: Structured Output
async def structured_output_example():
    """Example requesting structured output from Claude."""
    print("\n=== Structured Output Example ===")

    agent = Agent(
        "JSON Generator",
        provider="anthropic",
        model="claude-3-opus-20240229",
        instructions="Always respond with valid JSON when asked for structured data.",
    )

    response = await agent.arun(
        "Create a JSON object for a user profile with name, age, interests (array), "
        "and address (nested object with street, city, country)."
    )
    print(f"Structured Response:\n{response.content}")


# Example 10: Complex Reasoning Tasks
async def reasoning_example():
    """Example of complex reasoning with Claude."""
    print("\n=== Complex Reasoning Example ===")

    agent = Agent(
        "Reasoning Expert",
        provider="anthropic",
        model="claude-3-opus-20240229",
        instructions="Think step by step through complex problems.",
    )

    response = await agent.arun(
        "A farmer has 17 sheep. All but 9 die. How many sheep does the farmer have left? "
        "Explain your reasoning step by step."
    )
    print(f"Reasoning Response:\n{response.content}")


# Example 11: Cost Optimization
async def cost_optimization_example():
    """Example showing cost optimization strategies."""
    print("\n=== Cost Optimization Example ===")

    # Use Haiku for simple tasks
    cheap_agent = Agent(
        provider="anthropic",
        model="claude-3-haiku-20240307",
        max_tokens=50,  # Limit response length
    )

    # Use Opus only for complex tasks (with token limit)
    expensive_agent = Agent(
        provider="anthropic",
        model="claude-3-opus-20240229",
        max_tokens=200,  # Limit tokens to control cost
    )

    # Simple task - use cheaper model
    simple_response = await cheap_agent.arun("What's 2+2?")
    print(f"Simple task (Haiku): {simple_response.content}")

    # Complex task - use better model
    complex_response = await expensive_agent.arun(
        "Explain the philosophical implications of Gödel's incompleteness theorems"
    )
    print(f"\nComplex task (Opus): {complex_response.content[:200]}...")


# Example 12: Multi-Language Support
async def multilingual_example():
    """Example showing Claude's multilingual capabilities."""
    print("\n=== Multi-Language Example ===")

    agent = Agent(
        "Polyglot Claude", provider="anthropic", model="claude-3-sonnet-20240229"
    )

    # Ask in different languages
    languages = [
        ("English", "Hello, how are you?"),
        ("Spanish", "¿Cómo estás?"),
        ("French", "Comment allez-vous?"),
        ("Japanese", "こんにちは、元気ですか？"),
    ]

    for lang, greeting in languages:
        response = await agent.arun(
            f"Respond to this greeting in the same language: {greeting}"
        )
        print(f"\n{lang}: {greeting}")
        print(f"Response: {response.content}")


# Example 13: Code Analysis and Review
async def code_review_example():
    """Example of using Claude for code review."""
    print("\n=== Code Review Example ===")

    agent = Agent(
        "Code Reviewer",
        provider="anthropic",
        model="claude-3-opus-20240229",
        instructions="""You are a senior software engineer conducting code reviews.
        Focus on: code quality, potential bugs, performance issues, and best practices.""",
    )

    code_snippet = """
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    else:
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[i-1] + fib[i-2])
        return fib
    """

    response = await agent.arun(
        f"Review this Python function:\n```python{code_snippet}```"
    )
    print(f"Code Review:\n{response.content}")


async def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Please set ANTHROPIC_API_KEY environment variable")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        print("   Get your API key from: https://console.anthropic.com/")
        return

    print("🤖 AgentiCraft Anthropic Provider Examples")
    print("=" * 50)

    # Run examples
    try:
        await basic_example()
        await model_selection_example()
        await system_prompt_example()
        await tool_calling_example()
        await conversation_example()
        await advanced_parameters_example()
        await error_handling_example()
        await streaming_example()
        await structured_output_example()
        await reasoning_example()
        await cost_optimization_example()
        await multilingual_example()
        await code_review_example()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have a valid Anthropic API key set")


if __name__ == "__main__":
    asyncio.run(main())
