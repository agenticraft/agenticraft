"""Example: Multi-provider streaming with AgentiCraft.

This example demonstrates streaming across different LLM providers
and compares their streaming behavior.
"""

import asyncio
import os
import sys
import time
from typing import Any

# Add the parent directory to the path so we can import agenticraft
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from agenticraft import Agent
from agenticraft.core.streaming import StreamInterruptedError


class StreamingMetrics:
    """Track metrics for streaming performance."""

    def __init__(self):
        self.first_token_time: Optional[float] = None
        self.total_tokens: int = 0
        self.total_chunks: int = 0
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None

    def record_chunk(self):
        """Record a chunk received."""
        if self.first_token_time is None:
            self.first_token_time = time.time() - self.start_time
        self.total_chunks += 1

    def record_tokens(self, count: int):
        """Record tokens received."""
        self.total_tokens += count

    def finish(self):
        """Mark streaming as finished."""
        self.end_time = time.time()

    @property
    def total_time(self) -> float:
        """Total streaming time."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        if self.total_time > 0:
            return self.total_tokens / self.total_time
        return 0.0

    def summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        return {
            "first_token_latency": (
                f"{self.first_token_time:.3f}s" if self.first_token_time else "N/A"
            ),
            "total_time": f"{self.total_time:.2f}s",
            "total_chunks": self.total_chunks,
            "total_tokens": self.total_tokens,
            "tokens_per_second": f"{self.tokens_per_second:.1f}",
        }


async def stream_with_metrics(agent: Agent, prompt: str) -> StreamingMetrics:
    """Stream a response and collect metrics."""
    metrics = StreamingMetrics()

    try:
        async for chunk in agent.stream(prompt):
            metrics.record_chunk()

            # Count tokens (approximate by splitting on spaces)
            if chunk.content:
                tokens = len(chunk.content.split())
                metrics.record_tokens(tokens)
                print(chunk.content, end="", flush=True)

        metrics.finish()

    except StreamInterruptedError as e:
        print(f"\n[Stream interrupted: {e}]")
        metrics.finish()

    return metrics


async def compare_provider_streaming():
    """Compare streaming across different providers."""
    print("=== Multi-Provider Streaming Comparison ===\n")

    # Test prompt
    prompt = """Explain the concept of machine learning in exactly 3 sentences.
    Make it simple enough for a beginner to understand."""

    # Provider configurations
    providers = [
        {
            "name": "OpenAI GPT-4",
            "provider": "openai",
            "model": "gpt-4",
            "available": bool(os.getenv("OPENAI_API_KEY")),
        },
        {
            "name": "OpenAI GPT-3.5",
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "available": bool(os.getenv("OPENAI_API_KEY")),
        },
        {
            "name": "Anthropic Claude",
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "available": bool(os.getenv("ANTHROPIC_API_KEY")),
        },
        {
            "name": "Local Ollama",
            "provider": "ollama",
            "model": "llama2",
            "available": True,  # Assume available if configured
        },
    ]

    print(f"Test Prompt: {prompt}\n")
    print("=" * 60 + "\n")

    results = {}

    for config in providers:
        if not config["available"]:
            print(f"\n{config['name']}: ⚠️  Skipped (no API key)")
            continue

        print(f"\n{config['name']}:")
        print("-" * 40)

        try:
            # Create agent with specific provider
            agent = Agent(
                name=f"StreamTest-{config['provider']}",
                provider=config["provider"],
                model=config["model"],
            )

            # Check if streaming is supported
            info = agent.get_provider_info()
            if not info["supports_streaming"]:
                print("❌ Provider doesn't support streaming")
                continue

            # Stream and collect metrics
            print("Response: ", end="", flush=True)
            metrics = await stream_with_metrics(agent, prompt)

            # Store results
            results[config["name"]] = metrics.summary()

            # Print metrics
            print("\n\nMetrics:")
            for key, value in metrics.summary().items():
                print(f"  {key}: {value}")

        except Exception as e:
            print(f"❌ Error: {e}")
            results[config["name"]] = {"error": str(e)}

    # Print comparison summary
    print("\n\n" + "=" * 60)
    print("STREAMING COMPARISON SUMMARY")
    print("=" * 60)

    for provider, metrics in results.items():
        print(f"\n{provider}:")
        if "error" in metrics:
            print(f"  Error: {metrics['error']}")
        else:
            print(f"  First Token: {metrics.get('first_token_latency', 'N/A')}")
            print(f"  Total Time: {metrics.get('total_time', 'N/A')}")
            print(f"  Speed: {metrics.get('tokens_per_second', 'N/A')} tokens/sec")


async def parallel_streaming_demo():
    """Demonstrate parallel streaming from multiple agents."""
    print("\n\n=== Parallel Streaming Demo ===\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skipping (requires OPENAI_API_KEY)")
        return

    # Create multiple agents
    agents = [
        Agent(
            name="Scientist",
            instructions="You are a scientist. Be precise and factual.",
        ),
        Agent(
            name="Poet", instructions="You are a poet. Be creative and metaphorical."
        ),
        Agent(
            name="Child",
            instructions="You are a 5-year-old child. Be simple and curious.",
        ),
    ]

    prompt = "What is rain?"

    print(f"Asking 3 different agents: {prompt}\n")

    # Define async function to stream from one agent
    async def stream_agent(agent: Agent, prompt: str):
        print(f"\n{agent.name}:")
        print("-" * 30)

        response = ""
        async for chunk in agent.stream(prompt):
            print(chunk.content, end="", flush=True)
            response += chunk.content

        print("\n")
        return response

    # Stream from all agents in parallel
    tasks = [stream_agent(agent, prompt) for agent in agents]
    responses = await asyncio.gather(*tasks)

    print("\n✅ All agents completed!")


async def streaming_with_tools_demo():
    """Demonstrate streaming when tools are involved."""
    print("\n\n=== Streaming with Tools ===\n")

    from agenticraft import tool

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a city."""
        # Mock weather data
        return f"The weather in {city} is sunny and 72°F (22°C)."

    @tool
    def calculate(expression: str) -> float:
        """Evaluate a mathematical expression."""
        try:
            # Simple eval for demo - use ast.literal_eval in production
            return eval(expression)
        except:
            return "Error: Invalid expression"

    # Create agent with tools
    agent = Agent(
        name="ToolStreamAgent",
        instructions="You are a helpful assistant with access to weather and calculation tools.",
        tools=[get_weather, calculate],
    )

    # Test streaming with tool use
    prompts = [
        "What's the weather in Paris?",
        "Calculate 42 * 17 and tell me if it's a big number.",
        "Compare the weather in London and Tokyo.",
    ]

    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        print("Response: ", end="", flush=True)

        async for chunk in agent.stream(prompt):
            print(chunk.content, end="", flush=True)

        print("\n" + "-" * 40)


async def main():
    """Run all multi-provider streaming examples."""
    try:
        # Run comparison
        await compare_provider_streaming()

        # Run parallel demo
        await parallel_streaming_demo()

        # Run tools demo
        await streaming_with_tools_demo()

    except KeyboardInterrupt:
        print("\n\n✋ Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ Multi-provider streaming examples completed!")


if __name__ == "__main__":
    # Check for at least one API key
    if not any(
        [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("OLLAMA_HOST"),
        ]
    ):
        print("⚠️  Please set at least one of these environment variables:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - OLLAMA_HOST (for local models)")
    else:
        asyncio.run(main())
