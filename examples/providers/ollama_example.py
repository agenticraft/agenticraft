"""Example: Using Ollama provider with AgentiCraft.

This example demonstrates how to use the Ollama provider for running
local LLMs with AgentiCraft. Ollama enables running open-source models
like Llama 2, Mistral, and CodeLlama on your own hardware.

Requirements:
    1. Install Ollama: https://ollama.ai
    2. Start Ollama: ollama serve
    3. Pull Llama2: ollama pull llama2
    4. Install AgentiCraft: pip install agenticraft
"""

import asyncio

from agenticraft import Agent


# Example 1: Basic Usage with Llama2 7B
async def basic_example():
    """Basic example using Ollama provider with Llama2 7B."""
    print("=== Basic Ollama Example (Llama2 7B) ===")

    # Create agent with Ollama configuration
    agent = Agent(
        "Local Llama2",
        provider="ollama",
        model="llama2",  # Uses llama2:latest
        base_url="http://localhost:11434",  # Default Ollama URL
    )

    # Simple query
    response = await agent.arun("What are the benefits of running LLMs locally?")
    print(f"Response: {response.content}")


# Example 2: Different Model Sizes
async def model_sizes_example():
    """Example showing different Llama2 model sizes."""
    print("\n=== Model Sizes Example ===")

    # Llama2 7B (default, good balance)
    agent_7b = Agent(
        provider="ollama", model="llama2", base_url="http://localhost:11434"
    )

    print("Testing Llama2 7B...")
    response = await agent_7b.arun("Explain what a neural network is in one sentence.")
    print(f"Llama2 7B: {response.content}")

    # You can also test other sizes if available
    # Llama2 13B (more capable but slower)
    try:
        agent_13b = Agent(
            provider="ollama", model="llama2:13b", base_url="http://localhost:11434"
        )
        response = await agent_13b.arun(
            "Explain what a neural network is in one sentence."
        )
        print(f"\nLlama2 13B: {response.content}")
    except Exception:
        print("\nLlama2 13B not available: Pull with 'ollama pull llama2:13b'")


# Example 3: System Prompts with Llama2
async def system_prompt_example():
    """Example using system prompts with Llama2."""
    print("\n=== System Prompt Example ===")

    agent = Agent(
        "Python Expert",
        provider="ollama",
        model="llama2",
        instructions="""You are an expert Python developer. 
        Provide clean, efficient code with explanations.""",
    )

    response = await agent.arun("Write a function to check if a number is prime")
    print(f"Response:\n{response.content}")


# Example 4: Temperature Control
async def temperature_example():
    """Example showing temperature effects on Llama2 responses."""
    print("\n=== Temperature Control Example ===")

    # Low temperature for consistent responses
    factual_agent = Agent(provider="ollama", model="llama2", temperature=0.1)

    # High temperature for creative responses
    creative_agent = Agent(provider="ollama", model="llama2", temperature=0.9)

    prompt = "Complete this story: The robot looked at the painting and"

    print("Low temperature (0.1) - More predictable:")
    response = await factual_agent.arun(prompt)
    print(f"{response.content}\n")

    print("High temperature (0.9) - More creative:")
    response = await creative_agent.arun(prompt)
    print(f"{response.content}")


# Example 5: Token Limits
async def token_limit_example():
    """Example showing how to control response length."""
    print("\n=== Token Limit Example ===")

    # Short responses
    brief_agent = Agent(provider="ollama", model="llama2", max_tokens=50)

    # Longer responses
    detailed_agent = Agent(provider="ollama", model="llama2", max_tokens=200)

    prompt = "Explain the concept of machine learning"

    print("Brief response (50 tokens):")
    response = await brief_agent.arun(prompt)
    print(f"{response.content}\n")

    print("Detailed response (200 tokens):")
    response = await detailed_agent.arun(prompt)
    print(f"{response.content}")


# Example 6: Conversation Example
async def conversation_example():
    """Example of multi-turn conversation with Llama2."""
    print("\n=== Conversation Example ===")

    agent = Agent(
        "Conversational Llama", provider="ollama", model="llama2", temperature=0.7
    )

    # Simulate a conversation about programming
    messages = [
        "What programming language should I learn first?",
        "Why is Python good for beginners?",
        "What can I build with Python as a beginner?",
        "How long does it typically take to learn Python basics?",
    ]

    for message in messages:
        print(f"\nUser: {message}")
        response = await agent.arun(message)
        print(f"Llama2: {response.content}")


# Example 7: Code Generation
async def code_generation_example():
    """Example of code generation with Llama2."""
    print("\n=== Code Generation Example ===")

    agent = Agent(
        "Code Generator",
        provider="ollama",
        model="llama2",
        instructions="You are a helpful coding assistant. Generate clean, commented code.",
        temperature=0.3,  # Lower temperature for more consistent code
    )

    response = await agent.arun(
        """
    Write a Python function that:
    1. Takes a list of numbers
    2. Returns the mean, median, and mode
    3. Handles edge cases
    """
    )
    print(f"Generated Code:\n{response.content}")


# Example 8: Comparison with Cloud Models
async def comparison_example():
    """Example comparing local Llama2 with cloud models."""
    print("\n=== Local vs Cloud Comparison ===")

    # Local Llama2
    local_agent = Agent(provider="ollama", model="llama2")

    prompt = "What are the advantages and disadvantages of quantum computing?"

    print("Local Llama2 7B response:")
    import time

    start = time.time()
    response = await local_agent.arun(prompt)
    end = time.time()
    print(f"Response time: {end - start:.2f} seconds")
    print(f"Response: {response.content}")

    print("\nBenefits of local execution:")
    print("- No API costs")
    print("- Complete privacy")
    print("- No rate limits")
    print("- Works offline")


# Example 9: Error Handling
async def error_handling_example():
    """Example of handling common Ollama errors."""
    print("\n=== Error Handling Example ===")

    # Check if Ollama is running
    try:
        agent = Agent(
            provider="ollama",
            model="llama2",
            base_url="http://localhost:11434",
            timeout=10,  # Short timeout for connection test
        )
        response = await agent.arun("Say hello")
        print(f"✅ Ollama is running: {response.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Is Ollama installed? Visit https://ollama.ai")
        print("2. Is Ollama running? Start with: ollama serve")
        print("3. Is Llama2 pulled? Pull with: ollama pull llama2")
        return

    # Test with non-existent model
    try:
        bad_agent = Agent(provider="ollama", model="non-existent-model")
        await bad_agent.arun("Hello")
    except Exception as e:
        print(f"\n✅ Correctly caught error for non-existent model: {e}")


# Example 10: Performance Tips
async def performance_tips_example():
    """Example showing performance optimization tips."""
    print("\n=== Performance Tips ===")

    agent = Agent(
        provider="ollama",
        model="llama2",
        temperature=0.1,  # Lower temperature = faster generation
        max_tokens=100,  # Limit tokens for faster responses
    )

    print("Performance optimization tips:")
    print("1. Use smaller models (7B vs 13B vs 70B)")
    print("2. Lower temperature for faster generation")
    print("3. Limit max_tokens for quicker responses")
    print("4. Run on GPU for significant speedup")

    print("\nTesting optimized settings...")
    import time

    start = time.time()
    response = await agent.arun("List 3 tips for writing clean code")
    end = time.time()

    print(f"\nResponse time: {end - start:.2f} seconds")
    print(f"Response: {response.content}")


# Example 11: Advanced Ollama Features
async def advanced_features_example():
    """Example of advanced Ollama features."""
    print("\n=== Advanced Ollama Features ===")

    # Custom model parameters
    agent = Agent(
        provider="ollama",
        model="llama2",
        # Ollama-specific parameters
        temperature=0.8,
        top_k=40,
        top_p=0.9,
        repeat_penalty=1.1,
        seed=42,  # For reproducible outputs
    )

    response = await agent.arun("Write a creative metaphor for artificial intelligence")
    print(f"Response with custom parameters: {response.content}")


async def main():
    """Run all examples."""
    print("🦙 AgentiCraft Ollama Provider Examples - Llama2")
    print("=" * 50)
    print("\n⚠️  Prerequisites:")
    print("1. Install Ollama: https://ollama.ai")
    print("2. Start Ollama: ollama serve")
    print("3. Pull Llama2: ollama pull llama2")
    print("\nPress Ctrl+C to skip slow examples\n")

    # Quick connectivity check
    print("Checking Ollama connection...")
    try:
        test_agent = Agent(provider="ollama", model="llama2")
        await test_agent.arun("test")
        print("✅ Ollama is running with Llama2!\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease ensure:")
        print("1. Ollama is running: ollama serve")
        print("2. Llama2 is pulled: ollama pull llama2")
        return

    # Run examples
    examples = [
        basic_example,
        model_sizes_example,
        system_prompt_example,
        temperature_example,
        token_limit_example,
        conversation_example,
        code_generation_example,
        comparison_example,
        error_handling_example,
        performance_tips_example,
        advanced_features_example,
    ]

    for example in examples:
        try:
            await example()
            print("\n" + "-" * 50)
            # Small delay between examples
            await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            print("\n⏭️  Skipping to next example...")
            continue
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())
