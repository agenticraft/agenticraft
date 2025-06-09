"""Basic streaming example for AgentiCraft.

This example shows how to stream responses token by token for better UX.
"""

import asyncio

from agenticraft import Agent
from agenticraft.core.streaming import collect_stream


async def basic_streaming_example():
    """Basic example of streaming responses."""
    print("🚀 Basic Streaming Example")
    print("=" * 60)

    # Create an agent
    agent = Agent(
        name="StreamingAssistant",
        instructions="You are a helpful assistant that provides detailed explanations.",
        model="gpt-4",  # You can change this to your preferred model
    )

    # Example 1: Stream a simple response
    print("\n📝 Example 1: Simple streaming")
    print("-" * 40)

    prompt = (
        "Explain what streaming is in the context of AI responses in 2-3 sentences."
    )

    print(f"Prompt: {prompt}")
    print("\nStreaming response:")

    try:
        async for chunk in agent.stream(prompt):
            # Print each chunk as it arrives
            print(chunk.content, end="", flush=True)

            # You can also access metadata
            if chunk.is_final:
                print("\n\n✅ Streaming complete!")
                if chunk.metadata:
                    print(f"Metadata: {chunk.metadata}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have set up your API keys!")

    # Example 2: Collect entire stream
    print("\n\n📝 Example 2: Collecting stream into response")
    print("-" * 40)

    prompt2 = "List 3 benefits of streaming AI responses."
    print(f"Prompt: {prompt2}")

    try:
        # Create a new stream and collect it
        stream = agent.stream(prompt2)
        response = await collect_stream(stream)

        print(f"\nComplete response ({response.chunk_count} chunks):")
        print(response.complete_text)

        if response.duration:
            print(f"\nStreaming duration: {response.duration:.2f} seconds")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    # Example 3: Stream with custom handling
    print("\n\n📝 Example 3: Custom chunk handling")
    print("-" * 40)

    prompt3 = "Count from 1 to 5 slowly, with a brief pause between each number."
    print(f"Prompt: {prompt3}")
    print("\nStreaming with chunk details:")

    try:
        chunk_count = 0
        total_length = 0

        async for chunk in agent.stream(prompt3):
            chunk_count += 1
            total_length += len(chunk.content)

            # Custom handling - show chunk details
            print(
                f"\nChunk {chunk_count}: '{chunk.content}' "
                f"(length: {len(chunk.content)}, "
                f"total: {total_length} chars)"
            )

            # You could add custom logic here, like:
            # - Update a progress bar
            # - Store partial results
            # - Check for specific content

            if chunk.is_final:
                print(f"\n✅ Received {chunk_count} chunks total")
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def main():
    """Run the examples."""
    try:
        await basic_streaming_example()
    except KeyboardInterrupt:
        print("\n\n👋 Streaming interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Note: Make sure you have set the appropriate API key
    # For OpenAI: export OPENAI_API_KEY="your-key"
    # For Anthropic: export ANTHROPIC_API_KEY="your-key"

    print("🌊 AgentiCraft Streaming Examples")
    print("Make sure you have set your API keys!")
    print()

    asyncio.run(main())
