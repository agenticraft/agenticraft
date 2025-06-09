"""Simple streaming demo without tools - works reliably with any provider.

This example focuses on basic streaming functionality without the complexity
of tool calls, making it more reliable across different API versions.
"""

import asyncio
import time

from agenticraft import Agent
from agenticraft.core.streaming import create_mock_stream


async def simple_streaming_demo():
    """Run simple streaming demonstrations."""
    print("🌊 Simple Streaming Demo")
    print("=" * 60)

    # Example 1: Mock streaming (no API needed)
    print("\n📝 Example 1: Mock Streaming (No API Key Required)")
    print("-" * 40)

    responses = {
        "greeting": "Hello! I'm demonstrating streaming by showing this text piece by piece. "
        "Notice how each word appears gradually, creating a more natural feeling "
        "of conversation. This is especially useful for longer responses!",
        "list": "Here are the benefits of streaming:\n\n"
        "1. Better user experience - see responses immediately\n"
        "2. Reduced perceived latency - no waiting for complete response\n"
        "3. Interruptible - users can stop generation if needed\n"
        "4. Memory efficient - process data as it arrives\n"
        "5. Natural conversation flow - like real-time typing",
        "story": "Once upon a time, in the land of asynchronous programming...\n\n"
        "There lived a developer who discovered the magic of streaming.\n"
        "Instead of waiting... and waiting... for complete responses,\n"
        "they could see words appear one by one, like magic!\n\n"
        "The end. ✨",
    }

    for name, text in responses.items():
        print(f"\n🎯 {name.title()} Example:")

        # Add typing indicator
        print("💭 ", end="", flush=True)
        for _ in range(3):
            print(".", end="", flush=True)
            await asyncio.sleep(0.3)
        print("\r" + " " * 10 + "\r", end="")  # Clear typing indicator

        # Stream the response
        start_time = time.time()
        char_count = 0

        async for chunk in create_mock_stream(text, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)
            char_count += len(chunk.content)

        elapsed = time.time() - start_time
        print(
            f"\n\n⏱️  Streamed {char_count} chars in {elapsed:.1f}s "
            f"({char_count/elapsed:.0f} chars/sec)"
        )

        await asyncio.sleep(1)  # Pause between examples

    # Example 2: Real API streaming (if available)
    print("\n\n📝 Example 2: Real API Streaming")
    print("-" * 40)

    try:
        agent = Agent(
            name="SimpleStreamer",
            instructions="You are a helpful assistant. Keep responses concise.",
            model="gpt-4",
        )

        prompts = [
            "In one sentence, what is streaming in AI?",
            "Give me a 3-line haiku about data streams.",
            "What's 2+2? (Just the number please)",
        ]

        for prompt in prompts:
            print(f"\n💬 Prompt: {prompt}")
            print("🤖 Response: ", end="", flush=True)

            try:
                char_count = 0
                start_time = time.time()

                async for chunk in agent.stream(prompt):
                    print(chunk.content, end="", flush=True)
                    char_count += len(chunk.content)

                elapsed = time.time() - start_time
                print(f"\n   (Streamed {char_count} chars in {elapsed:.1f}s)")

            except Exception as e:
                print(f"\n   ❌ Error: {e}")

            await asyncio.sleep(0.5)

    except Exception as e:
        print(f"⚠️  Skipping real API examples: {e}")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to see real streaming")

    # Example 3: Progress visualization
    print("\n\n📝 Example 3: Streaming with Progress Visualization")
    print("-" * 40)

    long_text = """
    Streaming is a powerful technique in AI applications that allows responses 
    to be delivered incrementally rather than all at once. This creates a more 
    natural and responsive user experience, similar to how humans communicate 
    in real-time conversations. By processing and displaying content as it's 
    generated, applications can provide immediate feedback and maintain user 
    engagement throughout the interaction.
    """.strip()

    print("Streaming with character counter:\n")

    total_chars = len(long_text)
    streamed_chars = 0

    async for chunk in create_mock_stream(long_text, chunk_size=10, delay=0.03):
        print(chunk.content, end="", flush=True)
        streamed_chars += len(chunk.content)

        # Update progress in terminal title (if supported)
        progress = (streamed_chars / total_chars) * 100
        print(f"\033]0;Streaming Progress: {progress:.0f}%\007", end="")

    print(f"\n\n✅ Streaming complete! ({total_chars} characters)")

    # Example 4: Comparison - Streaming vs Non-streaming
    print("\n\n📝 Example 4: Streaming vs Non-Streaming Comparison")
    print("-" * 40)

    comparison_text = (
        "This is a comparison of streaming versus non-streaming responses. "
        "Notice the difference in how the text appears!"
    )

    print("❌ Non-streaming (wait for complete response):")
    print("   Loading", end="")
    for _ in range(5):
        print(".", end="", flush=True)
        await asyncio.sleep(0.3)
    print(f"\n   {comparison_text}")
    print("   (User waited 1.5 seconds before seeing anything)")

    print("\n✅ Streaming (see response immediately):")
    print("   ", end="")
    start_time = time.time()
    async for chunk in create_mock_stream(comparison_text, chunk_size=5, delay=0.03):
        print(chunk.content, end="", flush=True)
        if time.time() - start_time < 0.1:
            print("\n   (User sees first content in <100ms!)", end="")
            print("\n   ", end="")

    print("\n\n🎉 Simple streaming demo complete!")


async def main():
    """Run the simple streaming demo."""
    try:
        await simple_streaming_demo()

        print("\n\n💡 Key Takeaways:")
        print("  • Streaming provides immediate feedback")
        print("  • Users see content as it's generated")
        print("  • Creates more natural interactions")
        print("  • Works great even without API keys (mock mode)")

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🌊 AgentiCraft Simple Streaming Demo")
    print("This demo focuses on basic streaming without complex features")
    print()

    asyncio.run(main())
