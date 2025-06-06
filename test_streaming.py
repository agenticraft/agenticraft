#!/usr/bin/env python3
"""Quick test of streaming functionality."""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenticraft import Agent
from agenticraft.core.streaming import create_mock_stream, collect_stream


async def test_mock_streaming():
    """Test mock streaming functionality."""
    print("=== Testing Mock Streaming ===\n")
    
    # Test mock stream
    print("Creating mock stream...")
    async for chunk in create_mock_stream("Hello, this is a test message!", chunk_size=5):
        print(f"Chunk: '{chunk.content}'", end=" ")
        print(f"(final: {chunk.is_final})")
    
    print("\n✅ Mock streaming works!\n")


async def test_agent_streaming():
    """Test agent streaming with OpenAI."""
    print("=== Testing Agent Streaming ===\n")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skipping agent streaming test (no OPENAI_API_KEY)")
        return
    
    try:
        # Create agent
        agent = Agent(
            name="StreamBot",
            instructions="You are a helpful assistant. Be concise.",
            model="gpt-3.5-turbo"  # Cheaper model for testing
        )
        
        # Check if streaming is supported
        info = agent.get_provider_info()
        print(f"Provider: {info['provider']}")
        print(f"Model: {info['model']}")
        print(f"Supports streaming: {info['supports_streaming']}")
        
        if not info['supports_streaming']:
            print("❌ Provider doesn't support streaming!")
            return
        
        # Test streaming
        print("\nStreaming response for: 'Tell me a haiku about streaming data'\n")
        print("Response: ", end="", flush=True)
        
        chunk_count = 0
        async for chunk in agent.stream("Tell me a haiku about streaming data"):
            print(chunk.content, end="", flush=True)
            chunk_count += 1
        
        print(f"\n\n✅ Streaming successful! Received {chunk_count} chunks\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_provider_comparison():
    """Compare streaming across providers (if available)."""
    print("=== Testing Provider Comparison ===\n")
    
    providers_to_test = []
    
    # Check available providers
    if os.getenv("OPENAI_API_KEY"):
        providers_to_test.append(("openai", "gpt-3.5-turbo", "OpenAI"))
    
    if os.getenv("ANTHROPIC_API_KEY"):
        providers_to_test.append(("anthropic", "claude-3-sonnet-20240229", "Anthropic"))
    
    # Always try Ollama (might be running locally)
    providers_to_test.append(("ollama", "llama2", "Ollama (local)"))
    
    if not providers_to_test:
        print("⚠️  No providers available for testing")
        return
    
    prompt = "Count from 1 to 5"
    
    for provider_name, model, display_name in providers_to_test:
        print(f"\n{display_name}:")
        print("-" * 30)
        
        try:
            agent = Agent(
                name=f"Test-{provider_name}",
                provider=provider_name,
                model=model
            )
            
            print(f"Response: ", end="", flush=True)
            
            start_time = asyncio.get_event_loop().time()
            chunk_count = 0
            
            async for chunk in agent.stream(prompt):
                print(chunk.content, end="", flush=True)
                chunk_count += 1
            
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"\n[{chunk_count} chunks in {elapsed:.2f}s]")
            
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Run all tests."""
    print("🚀 AgentiCraft Streaming Test\n")
    
    await test_mock_streaming()
    await test_agent_streaming()
    await test_provider_comparison()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
