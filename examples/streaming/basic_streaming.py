"""Example: Basic streaming with AgentiCraft.

This example demonstrates how to stream responses from agents token by token
for a better user experience with long responses.
"""

import asyncio
import os
import sys
from typing import Optional

# Add the parent directory to the path so we can import agenticraft
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agenticraft import Agent
from agenticraft.core.streaming import StreamInterruptedError


async def basic_streaming_example():
    """Demonstrate basic streaming functionality."""
    print("=== Basic Streaming Example ===\n")
    
    # Create an agent
    agent = Agent(
        name="StreamingAssistant",
        instructions="You are a helpful AI assistant that provides detailed explanations.",
        model="gpt-4"
    )
    
    # Check if the provider supports streaming
    info = agent.get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Model: {info['model']}")
    print(f"Supports streaming: {info['supports_streaming']}\n")
    
    if not info['supports_streaming']:
        print("⚠️  Current provider doesn't support streaming!")
        print("Streaming is supported by: OpenAI, Anthropic")
        return
    
    # Example 1: Simple streaming
    print("1. Simple Streaming Response")
    print("-" * 40)
    print("Prompt: Tell me a short story about a robot learning to paint.\n")
    print("Response: ", end="", flush=True)
    
    async for chunk in agent.stream(
        "Tell me a short story about a robot learning to paint. Keep it under 100 words."
    ):
        print(chunk.content, end="", flush=True)
    
    print("\n\n")
    
    # Example 2: Streaming with progress indicator
    print("2. Streaming with Progress Tracking")
    print("-" * 40)
    print("Prompt: Explain quantum computing in simple terms.\n")
    print("Response:\n")
    
    chunk_count = 0
    async for chunk in agent.stream(
        "Explain quantum computing in simple terms. Include an analogy."
    ):
        chunk_count += 1
        print(chunk.content, end="", flush=True)
    
    print(f"\n\n[Received {chunk_count} chunks]\n")
    
    # Example 3: Collecting streamed response
    print("3. Collecting Streamed Response")
    print("-" * 40)
    print("Prompt: List 3 benefits of exercise.\n")
    
    from agenticraft.core.streaming import StreamingResponse
    
    response = StreamingResponse()
    async for chunk in agent.stream("List 3 benefits of regular exercise."):
        response.add_chunk(chunk)
        print(".", end="", flush=True)  # Progress indicator
    
    print(f"\n\nComplete response ({response.chunk_count} chunks):")
    print(response.complete_text)
    print(f"\nStreaming duration: {response.duration:.2f} seconds\n")


async def streaming_with_interruption():
    """Demonstrate stream interruption handling."""
    print("\n=== Streaming with Interruption ===\n")
    
    agent = Agent(
        name="InterruptibleAssistant",
        instructions="You are a helpful AI assistant.",
        model="gpt-4"
    )
    
    print("Streaming a long response (will interrupt after 50 characters)...\n")
    
    try:
        char_count = 0
        async for chunk in agent.stream(
            "Write a detailed explanation of the water cycle, "
            "including evaporation, condensation, precipitation, and collection."
        ):
            print(chunk.content, end="", flush=True)
            char_count += len(chunk.content)
            
            # Interrupt after 50 characters
            if char_count > 50:
                print("\n\n[Interrupting stream...]")
                break
                
    except StreamInterruptedError as e:
        print(f"\nStream interrupted: {e}")
        if e.partial_response:
            print(f"Partial response: {e.partial_response}")


async def streaming_with_different_models():
    """Compare streaming across different models."""
    print("\n=== Streaming with Different Models ===\n")
    
    models = [
        ("gpt-4", "OpenAI GPT-4"),
        ("gpt-3.5-turbo", "OpenAI GPT-3.5 Turbo"),
    ]
    
    prompt = "What is the meaning of life in one sentence?"
    
    for model, display_name in models:
        try:
            agent = Agent(name=f"Agent-{model}", model=model)
            
            print(f"\n{display_name}:")
            print("-" * 30)
            
            start_time = asyncio.get_event_loop().time()
            
            async for chunk in agent.stream(prompt):
                print(chunk.content, end="", flush=True)
            
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"\n[Streaming time: {elapsed:.2f}s]\n")
            
        except Exception as e:
            print(f"Error with {display_name}: {e}\n")


async def streaming_with_temperature():
    """Demonstrate how temperature affects streaming."""
    print("\n=== Streaming with Different Temperatures ===\n")
    
    agent = Agent(
        name="TemperatureTest",
        instructions="You are a creative writer.",
        model="gpt-3.5-turbo"
    )
    
    prompt = "Write a creative opening line for a science fiction story."
    temperatures = [0.0, 0.7, 1.5]
    
    for temp in temperatures:
        print(f"\nTemperature {temp}:")
        print("-" * 30)
        
        async for chunk in agent.stream(prompt, temperature=temp):
            print(chunk.content, end="", flush=True)
        
        print("\n")


async def main():
    """Run all streaming examples."""
    # Set up API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return
    
    try:
        # Run examples
        await basic_streaming_example()
        await streaming_with_interruption()
        await streaming_with_different_models()
        await streaming_with_temperature()
        
    except KeyboardInterrupt:
        print("\n\n✋ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n✅ All streaming examples completed!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
