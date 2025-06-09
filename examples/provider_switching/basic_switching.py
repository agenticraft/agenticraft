"""Example: Basic provider switching.

This example demonstrates the simplest use cases for switching between
different LLM providers in AgentiCraft.
"""

import asyncio
import os

from agenticraft import Agent, tool


# Define a simple tool for testing
@tool
def word_count(text: str) -> int:
    """Count the number of words in a text."""
    return len(text.split())


async def basic_switching_example():
    """Demonstrate basic provider switching."""

    # Create an agent with OpenAI (default)
    agent = Agent(
        name="MultiProviderAgent",
        instructions="You are a helpful assistant that works with multiple LLM providers.",
        tools=[word_count],
    )

    print("=== Basic Provider Switching Example ===\n")

    # 1. Start with OpenAI
    print("1. Using OpenAI (GPT-4)")
    print("-" * 40)
    response = await agent.arun("Hello! What model are you using?")
    print(f"Response: {response.content}\n")

    # Show provider info
    info = agent.get_provider_info()
    print(f"Provider Info: {info}\n")

    # 2. Switch to Anthropic
    print("2. Switching to Anthropic (Claude)")
    print("-" * 40)
    agent.set_provider("anthropic", model="claude-3-sonnet-20240229")

    response = await agent.arun("Hello! What model are you using now?")
    print(f"Response: {response.content}\n")

    # 3. Switch to Ollama (local)
    print("3. Switching to Ollama (Local)")
    print("-" * 40)
    try:
        agent.set_provider("ollama", model="llama2")
        response = await agent.arun("Hello! Are you running locally?")
        print(f"Response: {response.content}\n")
    except Exception as e:
        print(f"Note: Ollama not available ({e})")
        print("Make sure Ollama is running: ollama serve\n")

    # 4. Test that tools still work after switching
    print("4. Testing Tools After Provider Switch")
    print("-" * 40)
    agent.set_provider("openai", model="gpt-3.5-turbo")  # Use cheaper model

    response = await agent.arun(
        "Count the words in this sentence: 'The quick brown fox jumps over the lazy dog'"
    )
    print(f"Response: {response.content}")
    print(f"Tool calls: {response.tool_calls}\n")


async def model_comparison_example():
    """Compare responses from different models on the same prompt."""

    print("\n=== Model Comparison Example ===\n")

    agent = Agent(
        name="ComparativeAgent",
        instructions="You are an AI assistant. Be concise and clear.",
    )

    # Test prompt
    prompt = "Explain the concept of recursion in programming in 2-3 sentences."

    # Models to compare
    models = [
        ("openai", "gpt-4", "GPT-4"),
        ("openai", "gpt-3.5-turbo", "GPT-3.5"),
        ("anthropic", "claude-3-opus-20240229", "Claude Opus"),
        ("anthropic", "claude-3-sonnet-20240229", "Claude Sonnet"),
        ("ollama", "llama2", "Llama 2 (Local)"),
    ]

    print(f"Prompt: {prompt}\n")
    print("Comparing responses from different models:")
    print("=" * 60)

    for provider, model, display_name in models:
        try:
            # Switch to the model
            agent.set_provider(provider, model=model)

            # Get response
            start_time = asyncio.get_event_loop().time()
            response = await agent.arun(prompt)
            elapsed = asyncio.get_event_loop().time() - start_time

            print(f"\n{display_name}:")
            print(f"Response: {response.content}")
            print(f"Time: {elapsed:.2f}s")

            # Show token usage if available
            if "usage" in response.metadata:
                usage = response.metadata["usage"]
                print(f"Tokens: {usage.get('total_tokens', 'N/A')}")

        except Exception as e:
            print(f"\n{display_name}: Not available ({e})")

    print("\n" + "=" * 60)


async def conversation_preservation_example():
    """Show that conversation history is preserved when switching providers."""

    print("\n=== Conversation Preservation Example ===\n")

    agent = Agent(
        name="MemoryAgent",
        instructions="You are a helpful assistant with a good memory.",
    )

    # Start a conversation with OpenAI
    print("Starting conversation with OpenAI...")
    response = await agent.arun("My name is Alice and I love Python programming.")
    print(f"OpenAI: {response.content}\n")

    response = await agent.arun("I'm working on a web scraping project.")
    print(f"OpenAI: {response.content}\n")

    # Switch to Anthropic
    print("Switching to Anthropic...")
    agent.set_provider("anthropic", model="claude-3-sonnet-20240229")

    # Continue the conversation
    response = await agent.arun("What's my name and what am I working on?")
    print(f"Anthropic: {response.content}\n")

    # The agent should remember the conversation despite switching providers
    print("✅ Conversation history preserved across provider switch!")


async def provider_specific_features_example():
    """Demonstrate provider-specific features."""

    print("\n=== Provider-Specific Features Example ===\n")

    agent = Agent(name="FeatureAgent")

    # OpenAI-specific: JSON mode
    print("1. OpenAI JSON Mode")
    print("-" * 40)
    agent.set_provider("openai", model="gpt-3.5-turbo")

    try:
        response = await agent.arun(
            "List 3 programming languages with their year of creation",
            response_format={"type": "json_object"},
        )
        print(f"JSON Response: {response.content}\n")
    except Exception:
        print("Note: JSON mode requires specific prompt formatting\n")

    # Anthropic-specific: System message handling
    print("2. Anthropic System Messages")
    print("-" * 40)
    agent.set_provider("anthropic")
    agent.config.instructions = "You are Claude, an AI assistant created by Anthropic."

    response = await agent.arun("Who created you?")
    print(f"Response: {response.content}\n")

    # Ollama-specific: Local model parameters
    print("3. Ollama Local Parameters")
    print("-" * 40)
    try:
        agent.set_provider("ollama", model="llama2")
        response = await agent.arun(
            "Generate a random number",
            temperature=1.0,
            seed=42,  # Reproducible generation
        )
        print(f"Response: {response.content}\n")
    except Exception as e:
        print(f"Ollama not available: {e}\n")


async def main():
    """Run all examples."""
    # Set up API keys (replace with your actual keys)
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-key")
    os.environ["ANTHROPIC_API_KEY"] = os.getenv(
        "ANTHROPIC_API_KEY", "your-anthropic-key"
    )

    # Run examples
    await basic_switching_example()
    await model_comparison_example()
    await conversation_preservation_example()
    await provider_specific_features_example()

    print("\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
