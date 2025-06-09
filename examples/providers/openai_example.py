"""Example: Using OpenAI provider with AgentiCraft.

This example demonstrates how to use the OpenAI provider with various
GPT models for different tasks including basic chat, tool calling,
and advanced features.

Requirements:
    pip install agenticraft openai
    export OPENAI_API_KEY="your-api-key"
"""

import asyncio
import os

from dotenv import load_dotenv

from agenticraft import Agent

# Load environment variables from .env file
load_dotenv()


# Example 1: Basic Usage
async def basic_example():
    """Basic example using OpenAI provider."""
    print("=== Basic OpenAI Example ===")

    # Create agent with provider configuration
    agent = Agent(
        "GPT Assistant",
        provider="openai",  # Specify provider as string
        model="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Simple query
    response = await agent.arun(
        "Explain the difference between machine learning and deep learning."
    )
    print(f"GPT-4: {response.content}")


# Example 2: Using Different GPT Models
async def model_selection_example():
    """Example showing different OpenAI models."""
    print("\n=== Model Selection Example ===")

    # Using GPT-4 (most capable)
    gpt4_agent = Agent(model="gpt-4")
    response = await gpt4_agent.arun("Write a haiku about programming")
    print(f"GPT-4: {response.content}")

    # Using GPT-3.5 Turbo (faster and cheaper)
    gpt35_agent = Agent(model="gpt-3.5-turbo")
    response = await gpt35_agent.arun("Write a haiku about programming")
    print(f"\nGPT-3.5: {response.content}")

    # Using GPT-4 Turbo (faster GPT-4)
    gpt4_turbo_agent = Agent(model="gpt-4-turbo-preview")
    response = await gpt4_turbo_agent.arun("Write a haiku about programming")
    print(f"\nGPT-4 Turbo: {response.content}")


# Example 3: System Prompts and Roles
async def system_prompt_example():
    """Example using system prompts with OpenAI."""
    print("\n=== System Prompt Example ===")

    agent = Agent(
        "Python Expert",
        provider="openai",
        instructions="""You are an expert Python developer with 20 years of experience.
        You follow PEP 8 style guidelines and write clean, efficient, well-documented code.
        Always include type hints and docstrings.""",
    )

    response = await agent.arun("Write a function to find prime numbers up to n")
    print(f"Response:\n{response.content}")


# Example 4: Tool Usage with Wrapper Pattern (Reliable Approach)
async def tool_calling_example():
    """Example of tool usage with OpenAI using the reliable wrapper pattern."""
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
        provider="openai",
        model="gpt-3.5-turbo",  # Using cheaper model
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

    # print("\n✅ Tool usage working correctly with wrapper pattern!")
    # print("This approach is reliable and recommended for production use.")


# Example 5: Conversation with Context
async def conversation_example():
    """Example of a multi-turn conversation."""
    print("\n=== Conversation Example ===")

    agent = Agent(
        "Conversational GPT", provider="openai", model="gpt-4", temperature=0.7
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
    """Example using advanced OpenAI parameters."""
    print("\n=== Advanced Parameters Example ===")

    agent_factual = Agent(
        "Precise GPT", provider="openai", model="gpt-4", temperature=0.1, max_tokens=100
    )
    # Low temperature for factual responses
    response = await agent_factual.arun(
        "List the planets in our solar system in order from the sun"
    )
    print(f"Factual (low temp): {response.content}")

    agent_creative = Agent(
        "Creative GPT",
        provider="openai",
        model="gpt-4",
        temperature=0.9,
        max_tokens=150,
        top_p=0.95,
    )

    # High temperature for creative responses
    response = await agent_creative.arun("Write a creative story opening about a robot")
    print(f"\nCreative (high temp): {response.content}")

    agent_with_penalties = Agent(
        "Penalized GPT",
        provider="openai",
        model="gpt-4",
        temperature=0.7,
        frequency_penalty=0.8,  # Reduce repetition
        presence_penalty=0.6,  # Encourage new topics
    )

    # Using frequency and presence penalties
    response = await agent_with_penalties.arun(
        "Write about the benefits of exercise without repeating yourself"
    )
    print(f"\nWith penalties: {response.content}")


# Example 7: Error Handling
async def error_handling_example():
    """Example of proper error handling."""
    print("\n=== Error Handling Example ===")

    # Test with invalid API key
    try:
        agent = Agent("Test Agent", provider="openai", api_key="invalid-key")
        response = await agent.arun("Hello")
    except Exception as e:
        print(f"Expected error: {e}")

    # Test with missing API key
    try:
        import os

        original_key = os.environ.get("OPENAI_API_KEY")
        if original_key:
            del os.environ["OPENAI_API_KEY"]

        agent = Agent(provider="openai")
        response = await agent.arun("Hello")
    except Exception as e:
        print(f"Missing key error: {e}")
    finally:
        # Restore key if it existed
        if "original_key" in locals() and original_key:
            os.environ["OPENAI_API_KEY"] = original_key

    # Test with valid key
    if os.getenv("OPENAI_API_KEY"):
        agent = Agent("Test Agent", provider="openai")
        response = await agent.arun("Say hello!")
        print(f"Success: {response.content}")
    else:
        print("Please set OPENAI_API_KEY environment variable")


# Example 8: Streaming Responses (Future)
async def streaming_example():
    """Example of streaming responses (coming soon)."""
    print("\n=== Streaming Example ===")
    print("Note: Streaming support coming in v0.2.0!")

    # This is how streaming will work:
    # provider = OpenAIProvider()
    # agent = Agent("Streaming GPT", provider=provider)
    #
    # async for chunk in agent.stream("Tell me a long story"):
    #     print(chunk, end="", flush=True)
    # print()


# Example 9: JSON Mode
async def json_mode_example():
    """Example using JSON mode for structured output."""
    print("\n=== JSON Mode Example ===")

    agent = Agent(
        "JSON Generator",
        provider="openai",
        model="gpt-4-turbo-preview",
        instructions="Always respond with valid JSON.",
    )

    response = await agent.arun(
        "Create a JSON object for a user profile with name, age, interests (array), "
        "and address (nested object with street, city, country).",
        response_format={"type": "json_object"},  # Only works with newer models
    )
    print(f"JSON Response:\n{response.content}")


# Example 10: Custom Base URL (for proxies/custom endpoints)
async def custom_endpoint_example():
    """Example using custom OpenAI-compatible endpoints."""
    print("\n=== Custom Endpoint Example ===")

    # This works with OpenAI-compatible APIs like Azure OpenAI, etc.
    try:
        agent = Agent(
            "Custom Endpoint Agent",
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1",  # Default, but can be changed
            model="gpt-3.5-turbo",
        )

        response = await agent.arun("Hello from custom endpoint!")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Custom endpoint example skipped: {e}")


# Example 11: Cost Optimization
async def cost_optimization_example():
    """Example showing cost optimization strategies."""
    print("\n=== Cost Optimization Example ===")

    # Use GPT-3.5 for simple tasks
    cheap_agent = Agent(
        model="gpt-3.5-turbo", provider="openai", max_tokens=50  # Limit response length
    )

    # Use GPT-4 only for complex tasks
    expensive_agent = Agent(model="gpt-4")

    # Simple task - use cheaper model
    simple_response = await cheap_agent.arun("What's 2+2?")
    print(f"Simple task (GPT-3.5): {simple_response.content}")

    # Complex task - use better model
    complex_response = await expensive_agent.arun(
        "Explain the philosophical implications of Gödel's incompleteness theorems"
    )
    print(f"\nComplex task (GPT-4): {complex_response.content[:200]}...")


async def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return

    print("🤖 AgentiCraft OpenAI Provider Examples")
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
        await json_mode_example()
        await custom_endpoint_example()
        await cost_optimization_example()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have a valid OpenAI API key set")


if __name__ == "__main__":
    asyncio.run(main())
