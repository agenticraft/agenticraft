"""Example: Using Anthropic provider with AgentiCraft.

This example demonstrates how to use the Anthropic provider with Claude models
for various tasks including basic chat, tool calling, and system prompts.

Requirements:
    pip install agenticraft anthropic
    export ANTHROPIC_API_KEY="your-api-key"
"""

import asyncio
import os
from typing import List, Dict, Any

from agenticraft import Agent
from agenticraft.providers.anthropic import AnthropicProvider
from agenticraft.tools import Tool


# Example 1: Basic Usage
async def basic_example():
    """Basic example using Anthropic provider."""
    print("=== Basic Anthropic Example ===")
    
    # Create provider explicitly
    provider = AnthropicProvider(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229"
    )
    
    # Create agent with provider
    agent = Agent("Claude Assistant", provider=provider)
    
    # Simple query
    response = await agent.run("Explain quantum computing in simple terms.")
    print(f"Claude: {response}")


# Example 2: Using Different Claude Models
async def model_selection_example():
    """Example showing different Claude models."""
    print("\n=== Model Selection Example ===")
    
    # Using Claude 3 Opus (most capable)
    opus_agent = Agent(model="claude-3-opus-20240229")
    response = await opus_agent.run("Write a haiku about AI")
    print(f"Opus: {response}")
    
    # Using Claude 3 Sonnet (balanced)
    sonnet_agent = Agent(model="claude-3-sonnet-20240229")
    response = await sonnet_agent.run("Write a haiku about AI")
    print(f"Sonnet: {response}")
    
    # Using Claude 3 Haiku (fastest)
    haiku_agent = Agent(model="claude-3-haiku-20240307")
    response = await haiku_agent.run("Write a haiku about AI")
    print(f"Haiku: {response}")


# Example 3: System Prompts
async def system_prompt_example():
    """Example using system prompts with Anthropic."""
    print("\n=== System Prompt Example ===")
    
    provider = AnthropicProvider()
    agent = Agent(
        "Code Expert",
        provider=provider,
        system_prompt="You are an expert Python developer. Provide clean, well-documented code with best practices."
    )
    
    response = await agent.run("Write a function to calculate fibonacci numbers")
    print(f"Response:\n{response}")


# Example 4: Tool Calling
async def tool_calling_example():
    """Example of tool calling with Anthropic."""
    print("\n=== Tool Calling Example ===")
    
    # Define a simple calculator tool
    @Tool.create
    async def calculator(expression: str) -> float:
        """Evaluate a mathematical expression.
        
        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 2")
        
        Returns:
            The result of the calculation
        """
        # In production, use a safe expression evaluator
        try:
            # Simple eval for demo - DO NOT use in production!
            result = eval(expression, {"__builtins__": {}}, {})
            return float(result)
        except:
            return 0.0
    
    # Create agent with tool
    provider = AnthropicProvider()
    agent = Agent("Math Assistant", provider=provider)
    agent.add_tool(calculator)
    
    response = await agent.run("What's 42 multiplied by 17?")
    print(f"Response: {response}")


# Example 5: Conversation with Memory
async def conversation_example():
    """Example of a conversation with context."""
    print("\n=== Conversation Example ===")
    
    provider = AnthropicProvider(
        model="claude-3-sonnet-20240229",  # Using Sonnet for balanced performance
        temperature=0.7
    )
    
    agent = Agent("Conversational Claude", provider=provider)
    
    # Simulate a conversation
    messages = [
        "My name is Alice and I love astronomy.",
        "What's the closest star to Earth?",
        "How far away is it?",
        "What did I tell you my name was?"
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        response = await agent.run(message)
        print(f"Claude: {response}")


# Example 6: Streaming Responses (if implemented)
async def streaming_example():
    """Example of streaming responses."""
    print("\n=== Streaming Example ===")
    print("Note: Streaming support coming soon!")
    
    # This is how streaming would work once implemented:
    # provider = AnthropicProvider()
    # agent = Agent("Streaming Claude", provider=provider)
    # 
    # async for chunk in agent.stream("Tell me a story about a robot"):
    #     print(chunk, end="", flush=True)
    # print()


# Example 7: Error Handling
async def error_handling_example():
    """Example of proper error handling."""
    print("\n=== Error Handling Example ===")
    
    try:
        # This will fail if no API key is set
        provider = AnthropicProvider(api_key="invalid-key")
        agent = Agent("Test Agent", provider=provider)
        await agent.run("Hello")
    except Exception as e:
        print(f"Expected error: {e}")
    
    # Proper way with environment variable
    if os.getenv("ANTHROPIC_API_KEY"):
        provider = AnthropicProvider()
        agent = Agent("Working Agent", provider=provider)
        response = await agent.run("Say hello!")
        print(f"Success: {response}")
    else:
        print("Please set ANTHROPIC_API_KEY environment variable")


# Example 8: Custom Parameters
async def custom_parameters_example():
    """Example using custom parameters."""
    print("\n=== Custom Parameters Example ===")
    
    provider = AnthropicProvider(
        model="claude-3-opus-20240229",
        temperature=0.3,  # Lower temperature for more focused responses
        max_tokens=500,   # Limit response length
    )
    
    agent = Agent("Precise Claude", provider=provider)
    
    # You can also override parameters per call
    response = await agent.run(
        "List 3 benefits of exercise",
        temperature=0.1,  # Even more focused for this specific query
        max_tokens=200
    )
    print(f"Response: {response}")


async def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Please set ANTHROPIC_API_KEY environment variable")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return
    
    # Run examples
    try:
        await basic_example()
        await model_selection_example()
        await system_prompt_example()
        await tool_calling_example()
        await conversation_example()
        await streaming_example()
        await error_handling_example()
        await custom_parameters_example()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have a valid Anthropic API key set")


if __name__ == "__main__":
    print("🤖 AgentiCraft Anthropic Provider Examples")
    print("=" * 50)
    asyncio.run(main())
