"""Visual streaming example with rich formatting.

This example demonstrates streaming with visual enhancements like
colors, progress bars, and formatted output (if terminal supports it).
"""

import asyncio
import sys
import time

from agenticraft import Agent
from agenticraft.core.streaming import StreamChunk, create_mock_stream


class VisualStreamPrinter:
    """Helper class for visual streaming output."""

    # ANSI color codes (basic colors that work in most terminals)
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "green": "\033[32m",
        "blue": "\033[34m",
        "yellow": "\033[33m",
        "cyan": "\033[36m",
        "magenta": "\033[35m",
    }

    def __init__(self, use_colors: bool = True):
        """Initialize the visual printer."""
        self.use_colors = use_colors and sys.stdout.isatty()
        self.chunk_count = 0
        self.start_time = None
        self.total_chars = 0

    def color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_colors and color in self.COLORS:
            return f"{self.COLORS[color]}{text}{self.COLORS['reset']}"
        return text

    def print_header(self, title: str):
        """Print a formatted header."""
        print(self.color(f"\n{'='*60}", "blue"))
        print(self.color(f"🌊 {title}", "bold"))
        print(self.color(f"{'='*60}", "blue"))

    def print_prompt(self, prompt: str):
        """Print the prompt nicely."""
        print(self.color("\n📝 Prompt:", "yellow"))
        print(f"   {prompt}")
        print(self.color("\n💬 Response:", "green"))

    def start_streaming(self):
        """Mark the start of streaming."""
        self.start_time = time.time()
        self.chunk_count = 0
        self.total_chars = 0

    def print_chunk(self, chunk: StreamChunk):
        """Print a chunk with visual feedback."""
        self.chunk_count += 1
        self.total_chars += len(chunk.content)

        # Print the actual content
        print(chunk.content, end="", flush=True)

        # If it's the final chunk, print stats
        if chunk.is_final and self.start_time:
            elapsed = time.time() - self.start_time
            self.print_stats(elapsed)

    def print_stats(self, elapsed: float):
        """Print streaming statistics."""
        print(self.color("\n\n📊 Streaming Stats:", "cyan"))
        print(f"   • Chunks: {self.chunk_count}")
        print(f"   • Characters: {self.total_chars}")
        print(f"   • Duration: {elapsed:.2f}s")
        print(f"   • Speed: {self.total_chars/elapsed:.0f} chars/sec")

    def print_progress_bar(self, progress: float, width: int = 40):
        """Print a progress bar."""
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        percentage = progress * 100

        # Use carriage return to update the same line
        print(
            f"\r{self.color('[', 'dim')}{self.color(bar, 'green')}{self.color(']', 'dim')} "
            f"{percentage:5.1f}%",
            end="",
            flush=True,
        )


async def visual_mock_example():
    """Run visual examples with mock streaming."""
    printer = VisualStreamPrinter()

    printer.print_header("Visual Mock Streaming Demo")

    # Example 1: Story with dramatic pauses
    printer.print_prompt("Tell me a very short story with suspense")

    story = """The door creaked open slowly...

A shadow moved in the darkness...

"Who's there?" she whispered...

Suddenly, a cat jumped out!

"Oh, it's just you, Whiskers!" she laughed."""

    printer.start_streaming()

    # Create mock stream with variable delays for dramatic effect
    async for chunk in create_mock_stream(story, chunk_size=1, delay=0.05):
        printer.print_chunk(chunk)

        # Add extra pauses for ellipsis
        if "..." in chunk.content:
            await asyncio.sleep(0.5)

    # Example 2: Code streaming with syntax
    printer.print_header("Code Streaming Example")
    printer.print_prompt("Show me a Python hello world")

    code = '''def hello_world():
    """A simple hello world function."""
    message = "Hello, World!"
    print(message)
    return message

# Call the function
hello_world()'''

    print(printer.color("\n```python", "magenta"))

    printer.start_streaming()
    async for chunk in create_mock_stream(code, chunk_size=5, delay=0.03):
        # Color Python keywords
        colored_chunk = chunk.content
        if printer.use_colors:
            keywords = ["def", "return", "print"]
            for keyword in keywords:
                if keyword in colored_chunk:
                    colored_chunk = colored_chunk.replace(
                        keyword, printer.color(keyword, "blue")
                    )

        print(colored_chunk, end="", flush=True)

        if chunk.is_final:
            print(printer.color("\n```", "magenta"))
            elapsed = time.time() - printer.start_time
            printer.print_stats(elapsed)

    # Example 3: List with progress
    printer.print_header("Streaming List with Progress")
    printer.print_prompt("List 5 benefits of streaming")

    items = [
        "1. ⚡ Real-time feedback - see responses as they're generated",
        "2. 🎯 Better UX - no waiting for complete response",
        "3. 🛑 Interruptible - can stop generation mid-stream",
        "4. 💾 Memory efficient - process chunks without storing all",
        "5. 📊 Progress tracking - monitor long generations",
    ]

    print()  # New line for progress bar
    total_chars = sum(len(item) for item in items)
    streamed_chars = 0

    for i, item in enumerate(items):
        # Show progress bar
        progress = i / len(items)
        printer.print_progress_bar(progress)
        await asyncio.sleep(0.5)

        # Clear progress bar and show item
        print("\r" + " " * 50 + "\r", end="")  # Clear line

        # Stream the item
        async for chunk in create_mock_stream(item + "\n", chunk_size=3, delay=0.02):
            print(chunk.content, end="", flush=True)
            streamed_chars += len(chunk.content)

        await asyncio.sleep(0.3)  # Pause between items

    # Final progress
    printer.print_progress_bar(1.0)
    print()  # New line after progress bar

    # Example 4: Thinking animation
    printer.print_header("Thinking Animation")
    printer.print_prompt("Solve a complex problem")

    thinking_phases = [
        "🤔 Analyzing the problem",
        "🧠 Processing information",
        "💡 Generating insights",
        "✍️  Formulating response",
        "✅ Complete!",
    ]

    print()
    for phase in thinking_phases:
        print(f"\r{phase}", end="", flush=True)

        # Animated dots
        for _ in range(3):
            await asyncio.sleep(0.3)
            print(".", end="", flush=True)

        # Clear the line
        print("\r" + " " * 50 + "\r", end="")

    # Final response
    response = (
        "\nThe answer is 42! After careful analysis of all factors involved, "
        "considering multiple perspectives and applying advanced reasoning, "
        "the solution becomes clear."
    )

    async for chunk in create_mock_stream(response, chunk_size=5, delay=0.03):
        print(chunk.content, end="", flush=True)

    print(printer.color("\n\n✨ Visual streaming demo complete!", "green"))


async def visual_real_example():
    """Run visual examples with real API (if available)."""
    printer = VisualStreamPrinter()

    try:
        agent = Agent(
            name="VisualAssistant",
            instructions="You are a helpful assistant with a flair for clear, well-structured responses.",
            model="gpt-4",
        )

        printer.print_header("Visual Real-Time Streaming")

        prompts = [
            "Write a haiku about streaming data",
            "List 3 benefits of async programming with emojis",
            "Explain recursion in one sentence",
        ]

        for prompt in prompts:
            printer.print_prompt(prompt)
            printer.start_streaming()

            try:
                async for chunk in agent.stream(prompt):
                    printer.print_chunk(chunk)

            except Exception as e:
                print(printer.color(f"\n❌ Error: {e}", "red"))

            await asyncio.sleep(1)  # Pause between examples

    except Exception as e:
        print(printer.color(f"\n⚠️  Skipping real examples: {e}", "yellow"))
        print("Set your API key to see real streaming!")


async def main():
    """Run visual streaming examples."""
    print("🎨 Visual Streaming Examples")
    print("Terminal colors:", "enabled" if sys.stdout.isatty() else "disabled")

    # Always run mock examples
    await visual_mock_example()

    # Try real examples if API key is available
    import os

    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        print("\n" + "=" * 60)
        await visual_real_example()
    else:
        print(
            "\n💡 Tip: Set OPENAI_API_KEY or ANTHROPIC_API_KEY for real streaming examples"
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
