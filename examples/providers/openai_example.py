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
from typing import List, Dict, Any

from agenticraft import Agent
from agenticraft.providers.openai import OpenAIProvider
from agenticraft.tools import Tool


# Example 1: Basic Usage
async def basic_example():
    """Basic example using OpenAI provider."""
    print("=== Basic OpenAI Example ===")
    
    # Create provider explicitly
    provider = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4"
    )
    
    # Create agent with provider
    agent = Agent("GPT Assistant", provider=provider)
    
    # Simple query
    response = await agent.run("Explain the difference between machine learning and deep learning.")
    print(f"GPT-4: {response}")


# Example 2: Using Different GPT Models
async def model_selection_example():
    """Example showing different OpenAI models."""
    print("\n=== Model Selection Example ===")
    
    # Using GPT-4 (most capable)
    gpt4_agent = Agent(model="gpt-4")
    response = await gpt4_agent.run("Write a haiku about programming")
    print(f"GPT-4: {response}")
    
    # Using GPT-3.5 Turbo (faster and cheaper)
    gpt35_agent = Agent(model="gpt-3.5-turbo")
    response = await gpt35_agent.run("Write a haiku about programming")
    print(f"\nGPT-3.5: {response}")
    
    # Using GPT-4 Turbo (faster GPT-4)
    gpt4_turbo_agent = Agent(model="gpt-4-turbo-preview")
    response = await gpt4_turbo_agent.run("Write a haiku about programming")
    print(f"\nGPT-4 Turbo: {response}")


# Example 3: System Prompts and Roles
async def system_prompt_example():
    """Example using system prompts with OpenAI."""
    print("\n=== System Prompt Example ===")
    
    provider = OpenAIProvider()
    agent = Agent(
        "Python Expert",
        provider=provider,
        system_prompt="""You are an expert Python developer with 20 years of experience.
        You follow PEP 8 style guidelines and write clean, efficient, well-documented code.
        Always include type hints and docstrings."""
    )
    
    response = await agent.run("Write a function to find prime numbers up to n")
    print(f"Response:\n{response}")


# Example 4: Tool Calling with Function Calling
async def tool_calling_example():
    """Example of tool calling with OpenAI's function calling."""
    print("\n=== Tool Calling Example ===")
    
    # Define tools
    @Tool.create
    async def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
        """Get the current weather for a location.
        
        Args:
            location: The city and state/country
            unit: Temperature unit (celsius or fahrenheit)
        
        Returns:
            Weather information
        """
        # Simulated weather data
        return {
            "location": location,
            "temperature": 22,
            "unit": unit,
            "conditions": "Partly cloudy",
            "humidity": 65
        }
    
    @Tool.create
    async def calculate(expression: str) -> float:
        """Evaluate a mathematical expression.
        
        Args:
            expression: Math expression to evaluate
        
        Returns:
            The result
        """
        try:
            # Simple eval for demo - use a safe parser in production!
            result = eval(expression, {"__builtins__": {}}, {})
            return float(result)
        except:
            return 0.0
    
    # Create agent with tools
    provider = OpenAIProvider(model="gpt-4")
    agent = Agent("Assistant with Tools", provider=provider)
    agent.add_tool(get_weather)
    agent.add_tool(calculate)
    
    # Test weather query
    response = await agent.run("What's the weather like in San Francisco?")
    print(f"Weather query: {response}")
    
    # Test calculation
    response = await agent.run("What's the square root of 144?")
    print(f"\nMath query: {response}")
    
    # Test combined query
    response = await agent.run(
        "If it's 22°C in Paris, what would that be in Fahrenheit? "
        "Also, what's the weather there?"
    )
    print(f"\nCombined query: {response}")


# Example 5: Conversation with Context
async def conversation_example():
    """Example of a multi-turn conversation."""
    print("\n=== Conversation Example ===")
    
    provider = OpenAIProvider(
        model="gpt-4",
        temperature=0.7
    )
    
    agent = Agent("Conversational GPT", provider=provider)
    
    # Simulate a conversation about a coding project
    messages = [
        "I'm building a web scraper in Python. What libraries would you recommend?",
        "I chose BeautifulSoup. How do I handle dynamic content?",
        "Great! Now how do I handle rate limiting to be respectful to the server?",
        "Can you show me a simple example combining all these concepts?"
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        response = await agent.run(message)
        print(f"Assistant: {response}")


# Example 6: Advanced Parameters
async def advanced_parameters_example():
    """Example using advanced OpenAI parameters."""
    print("\n=== Advanced Parameters Example ===")
    
    provider = OpenAIProvider(model="gpt-4")
    agent = Agent("Precise GPT", provider=provider)
    
    # Low temperature for factual responses
    response = await agent.run(
        "List the planets in our solar system in order from the sun",
        temperature=0.1,
        max_tokens=100
    )
    print(f"Factual (low temp): {response}")
    
    # High temperature for creative responses
    response = await agent.run(
        "Write a creative story opening about a robot",
        temperature=0.9,
        max_tokens=150,
        top_p=0.95
    )
    print(f"\nCreative (high temp): {response}")
    
    # Using frequency and presence penalties
    response = await agent.run(
        "Write about the benefits of exercise without repeating yourself",
        temperature=0.7,
        frequency_penalty=0.8,  # Reduce repetition
        presence_penalty=0.6    # Encourage new topics
    )
    print(f"\nWith penalties: {response}")


# Example 7: Error Handling
async def error_handling_example():
    """Example of proper error handling."""
    print("\n=== Error Handling Example ===")
    
    # Test with invalid API key
    try:
        provider = OpenAIProvider(api_key="invalid-key")
        provider.validate_auth()
    except Exception as e:
        print(f"Validation error: {e}")
    
    # Test with missing API key
    try:
        with patch.dict(os.environ, {}, clear=True):
            provider = OpenAIProvider()
    except Exception as e:
        print(f"Missing key error: {e}")
    
    # Test with valid key
    if os.getenv("OPENAI_API_KEY"):
        provider = OpenAIProvider()
        agent = Agent("Test Agent", provider=provider)
        response = await agent.run("Say hello!")
        print(f"Success: {response}")
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
    
    provider = OpenAIProvider(model="gpt-4-turbo-preview")
    agent = Agent(
        "JSON Generator",
        provider=provider,
        system_prompt="Always respond with valid JSON."
    )
    
    response = await agent.run(
        "Create a JSON object for a user profile with name, age, interests (array), "
        "and address (nested object with street, city, country).",
        response_format={"type": "json_object"}  # Only works with newer models
    )
    print(f"JSON Response:\n{response}")


# Example 10: Custom Base URL (for proxies/custom endpoints)
async def custom_endpoint_example():
    """Example using custom OpenAI-compatible endpoints."""
    print("\n=== Custom Endpoint Example ===")
    
    # This works with OpenAI-compatible APIs like Azure OpenAI, etc.
    try:
        provider = OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1",  # Default, but can be changed
            model="gpt-3.5-turbo"
        )
        
        agent = Agent("Custom Endpoint Agent", provider=provider)
        response = await agent.run("Hello from custom endpoint!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Custom endpoint example skipped: {e}")


# Example 11: Cost Optimization
async def cost_optimization_example():
    """Example showing cost optimization strategies."""
    print("\n=== Cost Optimization Example ===")
    
    # Use GPT-3.5 for simple tasks
    cheap_agent = Agent(
        model="gpt-3.5-turbo",
        provider=OpenAIProvider(max_tokens=50)  # Limit response length
    )
    
    # Use GPT-4 only for complex tasks
    expensive_agent = Agent(model="gpt-4")
    
    # Simple task - use cheaper model
    simple_response = await cheap_agent.run("What's 2+2?")
    print(f"Simple task (GPT-3.5): {simple_response}")
    
    # Complex task - use better model
    complex_response = await expensive_agent.run(
        "Explain the philosophical implications of Gödel's incompleteness theorems"
    )
    print(f"\nComplex task (GPT-4): {complex_response[:200]}...")


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
    # Need to import patch for error handling example
    from unittest.mock import patch
    asyncio.run(main())
