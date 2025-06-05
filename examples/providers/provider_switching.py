"""Example: Provider Switching in AgentiCraft.

This example demonstrates how easy it is to switch between different
LLM providers while keeping the same agent code.

Requirements:
    pip install agenticraft openai anthropic
    export OPENAI_API_KEY="your-openai-key"
    export ANTHROPIC_API_KEY="your-anthropic-key"
    # For Ollama: Install from https://ollama.ai and run: ollama serve
"""

import asyncio
import os
from typing import List

from agenticraft import Agent
from agenticraft.tools import Tool


# Define a reusable tool
@Tool.create
async def word_count(text: str) -> int:
    """Count the number of words in the given text.
    
    Args:
        text: The text to count words in
        
    Returns:
        The number of words
    """
    return len(text.split())


async def compare_providers():
    """Compare responses from different providers."""
    print("🔄 Provider Comparison Example")
    print("=" * 50)
    
    # The same prompt for all providers
    prompt = "Write a 3-line poem about artificial intelligence"
    
    # Test with OpenAI
    if os.getenv("OPENAI_API_KEY"):
        print("\n📘 OpenAI (GPT-4):")
        openai_agent = Agent(
            name="OpenAI Poet",
            model="gpt-4",
            tools=[word_count]
        )
        response = await openai_agent.run(prompt)
        print(response)
        word_response = await openai_agent.run(f"Count the words in this poem: {response}")
        print(f"Analysis: {word_response}")
    else:
        print("\n⚠️  OpenAI skipped (no API key)")
    
    # Test with Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n📙 Anthropic (Claude 3):")
        anthropic_agent = Agent(
            name="Claude Poet",
            model="claude-3-sonnet-20240229",
            tools=[word_count]
        )
        response = await anthropic_agent.run(prompt)
        print(response)
        word_response = await anthropic_agent.run(f"Count the words in this poem: {response}")
        print(f"Analysis: {word_response}")
    else:
        print("\n⚠️  Anthropic skipped (no API key)")
    
    # Test with Ollama (local)
    try:
        print("\n📗 Ollama (Llama 2):")
        ollama_agent = Agent(
            name="Llama Poet",
            model="ollama/llama2",
            tools=[word_count]
        )
        response = await ollama_agent.run(prompt)
        print(response)
        word_response = await ollama_agent.run(f"Count the words in this poem: {response}")
        print(f"Analysis: {word_response}")
    except Exception as e:
        print(f"⚠️  Ollama skipped: {e}")
        print("   Make sure Ollama is running: ollama serve")


async def unified_interface_example():
    """Show how the same code works with any provider."""
    print("\n\n🎯 Unified Interface Example")
    print("=" * 50)
    
    async def analyze_text(agent: Agent, text: str):
        """Analyze text with any agent, regardless of provider."""
        print(f"\nUsing {agent.name}:")
        
        # All agents work the same way
        summary = await agent.run(f"Summarize this in one sentence: {text}")
        print(f"Summary: {summary}")
        
        sentiment = await agent.run(f"What's the sentiment of this text: {text}")
        print(f"Sentiment: {sentiment}")
        
        keywords = await agent.run(f"Extract 3 keywords from: {text}")
        print(f"Keywords: {keywords}")
    
    sample_text = """
    Artificial Intelligence is revolutionizing how we interact with technology.
    From voice assistants to autonomous vehicles, AI is becoming an integral
    part of our daily lives, bringing both exciting opportunities and
    important ethical considerations.
    """
    
    # Create agents with different providers
    agents = []
    
    if os.getenv("OPENAI_API_KEY"):
        agents.append(Agent("GPT Analyst", model="gpt-3.5-turbo"))
    
    if os.getenv("ANTHROPIC_API_KEY"):
        agents.append(Agent("Claude Analyst", model="claude-3-haiku-20240307"))
    
    # Try Ollama
    try:
        from agenticraft.providers.ollama import OllamaProvider
        provider = OllamaProvider()
        provider.validate_auth()  # Check if Ollama is running
        agents.append(Agent("Llama Analyst", model="ollama/llama2"))
    except:
        pass
    
    if not agents:
        print("⚠️  No providers available. Please set API keys or start Ollama.")
        return
    
    # Run the same analysis with each agent
    for agent in agents:
        await analyze_text(agent, sample_text)
        print("-" * 40)


async def provider_specific_features():
    """Demonstrate provider-specific features."""
    print("\n\n🔧 Provider-Specific Features")
    print("=" * 50)
    
    # OpenAI-specific: JSON mode (GPT-4 Turbo)
    if os.getenv("OPENAI_API_KEY"):
        print("\n📘 OpenAI - JSON Mode:")
        try:
            agent = Agent(model="gpt-4-turbo-preview")
            response = await agent.run(
                "Generate a JSON object with name, age, and hobbies array",
                response_format={"type": "json_object"}
            )
            print(response)
        except Exception as e:
            print(f"JSON mode not available: {e}")
    
    # Anthropic-specific: Longer context
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n📙 Anthropic - Long Context:")
        agent = Agent(model="claude-3-opus-20240229")
        response = await agent.run(
            "What are the key advantages of Claude's 200K token context window?"
        )
        print(response)
    
    # Ollama-specific: Model management
    try:
        print("\n📗 Ollama - Local Models:")
        from agenticraft.providers.ollama import OllamaProvider
        provider = OllamaProvider()
        models = await provider.list_models()
        print(f"Available local models: {[m['name'] for m in models]}")
    except Exception as e:
        print(f"Ollama not available: {e}")


async def performance_comparison():
    """Compare performance characteristics of providers."""
    print("\n\n⚡ Performance Comparison")
    print("=" * 50)
    
    import time
    
    prompt = "List 5 interesting facts about space exploration."
    
    async def measure_response_time(agent: Agent, provider_name: str):
        """Measure response time for a provider."""
        start = time.time()
        try:
            response = await agent.run(prompt)
            elapsed = time.time() - start
            print(f"\n{provider_name}:")
            print(f"Time: {elapsed:.2f} seconds")
            print(f"Response length: {len(response)} chars")
            return elapsed
        except Exception as e:
            print(f"\n{provider_name}: Failed - {e}")
            return None
    
    # Test each provider
    times = {}
    
    if os.getenv("OPENAI_API_KEY"):
        agent = Agent(model="gpt-3.5-turbo")  # Fast model
        times["OpenAI GPT-3.5"] = await measure_response_time(agent, "OpenAI GPT-3.5")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        agent = Agent(model="claude-3-haiku-20240307")  # Fast model
        times["Anthropic Haiku"] = await measure_response_time(agent, "Anthropic Haiku")
    
    try:
        agent = Agent(model="ollama/llama2")
        times["Ollama Llama2"] = await measure_response_time(agent, "Ollama Llama2")
    except:
        pass
    
    # Summary
    if times:
        print("\n📊 Summary:")
        valid_times = {k: v for k, v in times.items() if v is not None}
        if valid_times:
            fastest = min(valid_times.items(), key=lambda x: x[1])
            print(f"Fastest: {fastest[0]} ({fastest[1]:.2f}s)")


async def main():
    """Run all provider comparison examples."""
    print("🤖 AgentiCraft Provider Switching Examples")
    print("=" * 50)
    print("\nThis example shows how easy it is to switch between providers")
    print("while keeping your agent code exactly the same!\n")
    
    # Check what's available
    providers_available = []
    if os.getenv("OPENAI_API_KEY"):
        providers_available.append("OpenAI ✓")
    else:
        providers_available.append("OpenAI ✗ (set OPENAI_API_KEY)")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        providers_available.append("Anthropic ✓")
    else:
        providers_available.append("Anthropic ✗ (set ANTHROPIC_API_KEY)")
    
    try:
        from agenticraft.providers.ollama import OllamaProvider
        provider = OllamaProvider()
        provider.validate_auth()
        providers_available.append("Ollama ✓")
    except:
        providers_available.append("Ollama ✗ (run: ollama serve)")
    
    print("Available providers:")
    for p in providers_available:
        print(f"  - {p}")
    
    if not any("✓" in p for p in providers_available):
        print("\n⚠️  No providers available! Please:")
        print("   - Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY")
        print("   - Or install and run Ollama")
        return
    
    # Run examples
    await compare_providers()
    await unified_interface_example()
    await provider_specific_features()
    await performance_comparison()
    
    print("\n\n✅ Key Takeaways:")
    print("1. Same Agent API works with all providers")
    print("2. Easy to switch providers with just model parameter")
    print("3. Each provider has unique strengths:")
    print("   - OpenAI: Most features, JSON mode")
    print("   - Anthropic: Long context, strong reasoning")
    print("   - Ollama: Local, private, free")


if __name__ == "__main__":
    asyncio.run(main())
