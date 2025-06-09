"""Example: Provider Switching in AgentiCraft.

This example demonstrates how easy it is to switch between different
LLM providers while keeping the same agent code.

Requirements:
    pip install agenticraft openai anthropic python-dotenv

    Create a .env file with:
    OPENAI_API_KEY=your-openai-key
    ANTHROPIC_API_KEY=your-anthropic-key

    For Ollama: Install from https://ollama.ai and run: ollama serve
"""

import asyncio
import os
import time

from dotenv import load_dotenv

from agenticraft import Agent
from agenticraft.agents import WorkflowAgent

# Load environment variables from .env file
load_dotenv()


# Define a simple tool wrapper (following the pattern from examples)
class SimpleToolWrapper:
    def __init__(self, name: str, func):
        self.name = name
        self.func = func

    def create_handler(self):
        def handler(agent, step, context):
            params = context.get(f"{self.name}_params", {})
            try:
                result = self.func(**params)
                context[f"{self.name}_result"] = result
                return f"Result: {result}"
            except Exception as e:
                return f"Error: {e}"

        return handler


# Define tool functions
def word_count(text: str) -> int:
    """Count the number of words in the given text."""
    return len(text.split())


def analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis based on keywords."""
    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic"]
    negative_words = ["bad", "terrible", "awful", "horrible", "poor", "worst"]

    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def extract_keywords(text: str, num_keywords: int = 3) -> list:
    """Extract keywords from text (simple implementation)."""
    # Simple keyword extraction based on word frequency
    words = text.lower().split()
    # Filter out common words
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "is",
        "are",
        "was",
        "were",
    }
    words = [w.strip(".,!?;:") for w in words if w not in stop_words and len(w) > 3]

    # Count frequencies
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    # Get top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:num_keywords]]


def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow safe operations
        allowed = {"__builtins__": {}, "sqrt": lambda x: x**0.5}
        result = eval(expression, allowed)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


# Create global tool wrappers
word_count_tool = SimpleToolWrapper("word_count", word_count)
sentiment_tool = SimpleToolWrapper("sentiment", analyze_sentiment)
keyword_tool = SimpleToolWrapper("extract_keywords", extract_keywords)
calc_tool = SimpleToolWrapper("calculate", calculate)


async def compare_providers_with_tools():
    """Compare responses from different providers using tools."""
    print("🔄 Provider Comparison with Tools Example")
    print("=" * 50)

    # The same prompt for all providers
    poem_prompt = "Write a 3-line poem about artificial intelligence"

    # Test with OpenAI
    if os.getenv("OPENAI_API_KEY"):
        print("\n📘 OpenAI (GPT-3.5):")
        agent = WorkflowAgent(
            name="OpenAI Poet",
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7,
        )

        # Register tools
        agent.register_handler("count_words", word_count_tool.create_handler())
        agent.register_handler("analyze_sentiment", sentiment_tool.create_handler())

        # Generate poem
        response = await agent.arun(poem_prompt)
        print(f"Poem:\n{response.content}")

        # Create workflow to analyze the poem
        workflow = agent.create_workflow("analyze_poem")
        workflow.add_step(name="count", handler="count_words", action="Counting words")
        workflow.add_step(
            name="sentiment", handler="analyze_sentiment", action="Analyzing sentiment"
        )

        # Execute analysis
        context = {
            "word_count_params": {"text": response.content},
            "sentiment_params": {"text": response.content},
        }
        await agent.execute_workflow(workflow, context=context)
        print(f"Word count: {context.get('word_count_result', 'N/A')}")
        print(f"Sentiment: {context.get('sentiment_result', 'N/A')}")
    else:
        print("\n⚠️  OpenAI skipped (no API key)")

    # Test with Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n📙 Anthropic (Claude Haiku):")
        agent = WorkflowAgent(
            name="Claude Poet",
            provider="anthropic",
            model="claude-3-haiku-20240307",
            temperature=0.7,
            timeout=60,
        )

        # Register the same tools
        agent.register_handler("count_words", word_count_tool.create_handler())
        agent.register_handler("analyze_sentiment", sentiment_tool.create_handler())

        # Generate poem
        response = await agent.arun(poem_prompt)
        print(f"Poem:\n{response.content}")

        # Same workflow, different provider
        workflow = agent.create_workflow("analyze_poem")
        workflow.add_step(name="count", handler="count_words", action="Counting words")
        workflow.add_step(
            name="sentiment", handler="analyze_sentiment", action="Analyzing sentiment"
        )

        context = {
            "word_count_params": {"text": response.content},
            "sentiment_params": {"text": response.content},
        }
        await agent.execute_workflow(workflow, context=context)
        print(f"Word count: {context.get('word_count_result', 'N/A')}")
        print(f"Sentiment: {context.get('sentiment_result', 'N/A')}")
    else:
        print("\n⚠️  Anthropic skipped (no API key)")


async def unified_workflow_example():
    """Show how the same workflow works with any provider."""
    print("\n\n🎯 Unified Workflow Example")
    print("=" * 50)

    sample_text = """
    Artificial Intelligence is revolutionizing how we interact with technology.
    From voice assistants to autonomous vehicles, AI is becoming an integral
    part of our daily lives, bringing both exciting opportunities and
    important ethical considerations.
    """

    async def analyze_with_agent(agent_name: str, provider: str, model: str, **kwargs):
        """Analyze text with any provider using workflows."""
        print(f"\n{agent_name} ({provider}):")

        agent = WorkflowAgent(name=agent_name, provider=provider, model=model, **kwargs)

        # Register tools
        agent.register_handler("keywords", keyword_tool.create_handler())
        agent.register_handler("count", word_count_tool.create_handler())

        # Create analysis workflow
        workflow = agent.create_workflow("text_analysis")
        workflow.add_step(
            name="extract", handler="keywords", action="Extracting keywords"
        )
        workflow.add_step(name="count", handler="count", action="Counting words")

        # First, get a summary
        summary = await agent.arun(f"Summarize this in one sentence: {sample_text}")
        print(f"Summary: {summary.content}")

        # Then run the workflow
        context = {
            "extract_keywords_params": {"text": sample_text, "num_keywords": 5},
            "word_count_params": {"text": sample_text},
        }
        await agent.execute_workflow(workflow, context=context)

        keywords = context.get("extract_keywords_result", [])
        word_count = context.get("word_count_result", 0)

        print(f"Keywords: {', '.join(keywords)}")
        print(f"Word count: {word_count}")

    # Test with available providers
    if os.getenv("OPENAI_API_KEY"):
        await analyze_with_agent(
            "GPT Analyst", "openai", "gpt-3.5-turbo", temperature=0.3
        )

    if os.getenv("ANTHROPIC_API_KEY"):
        await analyze_with_agent(
            "Claude Analyst",
            "anthropic",
            "claude-3-haiku-20240307",
            temperature=0.3,
            timeout=60,
        )


async def performance_comparison_with_workflows():
    """Compare performance of workflow execution across providers."""
    print("\n\n⚡ Workflow Performance Comparison")
    print("=" * 50)

    async def measure_workflow_performance(provider: str, model: str, **kwargs):
        """Measure workflow execution time."""
        print(f"\n{provider} - {model}:")

        try:
            agent = WorkflowAgent(
                name=f"{provider} Calculator", provider=provider, model=model, **kwargs
            )

            # Register calculator tool
            agent.register_handler("calc", calc_tool.create_handler())

            # Time the execution
            start = time.time()

            # Execute calculations
            calculations = [
                ("25 * 4", "multiplication"),
                ("144 ** 0.5", "square root"),
                ("850 * 0.15", "percentage"),
            ]

            results = []
            for expr, desc in calculations:
                workflow = agent.create_workflow(f"calc_{desc}")
                workflow.add_step(
                    name="calculate", handler="calc", action=f"Calculate {desc}"
                )

                context = {"calculate_params": {"expression": expr}}
                await agent.execute_workflow(workflow, context=context)
                results.append(context.get("calculate_result"))

            elapsed = time.time() - start

            print(f"  Results: {results}")
            print(f"  Total time: {elapsed:.2f} seconds")

            return elapsed
        except Exception as e:
            print(f"  Failed: {e}")
            return None

    # Test each provider
    times = {}

    if os.getenv("OPENAI_API_KEY"):
        times["OpenAI"] = await measure_workflow_performance(
            "openai", "gpt-3.5-turbo", temperature=0.1
        )

    if os.getenv("ANTHROPIC_API_KEY"):
        times["Anthropic"] = await measure_workflow_performance(
            "anthropic", "claude-3-haiku-20240307", temperature=0.1, timeout=60
        )

    if times:
        print("\n📊 Summary:")
        valid_times = {k: v for k, v in times.items() if v is not None}
        for provider, time_taken in sorted(valid_times.items(), key=lambda x: x[1]):
            print(f"  {provider}: {time_taken:.2f}s")


async def cost_comparison():
    """Show cost differences between providers."""
    print("\n\n💰 Cost Comparison")
    print("=" * 50)

    prompt = "Explain quantum computing in 100 words"

    if os.getenv("OPENAI_API_KEY"):
        print("\n📘 OpenAI Pricing (approximate):")
        print("  GPT-4: $0.03 per 1K input tokens + $0.06 per 1K output tokens")
        print("  GPT-3.5: $0.0015 per 1K input tokens + $0.002 per 1K output tokens")

        agent = Agent(model="gpt-3.5-turbo", max_tokens=100)
        response = await agent.arun(prompt)
        # Rough token estimate
        tokens = len(prompt.split()) + len(response.content.split())
        cost = (tokens / 1000) * 0.002
        print(f"  This query (~{tokens} tokens): ${cost:.4f}")

    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n📙 Anthropic Pricing (approximate):")
        print("  Claude Opus: $0.015 per 1K input tokens + $0.075 per 1K output tokens")
        print(
            "  Claude Sonnet: $0.003 per 1K input tokens + $0.015 per 1K output tokens"
        )
        print(
            "  Claude Haiku: $0.00025 per 1K input tokens + $0.00125 per 1K output tokens"
        )

        agent = Agent(
            provider="anthropic", model="claude-3-haiku-20240307", max_tokens=100
        )
        response = await agent.arun(prompt)
        tokens = len(prompt.split()) + len(response.content.split())
        cost = (tokens / 1000) * 0.00125
        print(f"  This query (~{tokens} tokens): ${cost:.5f}")

    print("\n📗 Ollama (Local):")
    print("  All models: FREE (runs on your hardware)")
    print("  No API costs, no rate limits, complete privacy")


async def main():
    """Run all provider switching examples with WorkflowAgent."""
    print("🤖 AgentiCraft Provider Switching with WorkflowAgent")
    print("=" * 50)
    print("\nThis example shows the recommended approach using WorkflowAgent")
    print("with tool wrappers for reliable tool usage across providers!")
    print("\nLoading API keys from .env file...\n")

    # Check what's available
    providers_available = []
    if os.getenv("OPENAI_API_KEY"):
        providers_available.append("OpenAI ✓")
    else:
        providers_available.append("OpenAI ✗ (set OPENAI_API_KEY in .env)")

    if os.getenv("ANTHROPIC_API_KEY"):
        providers_available.append("Anthropic ✓")
    else:
        providers_available.append("Anthropic ✗ (set ANTHROPIC_API_KEY in .env)")

    # Skip Ollama check for now as requested
    providers_available.append("Ollama ⏭️  (skipped for now)")

    print("Available providers:")
    for p in providers_available:
        print(f"  - {p}")

    if not any("✓" in p for p in providers_available):
        print("\n⚠️  No providers available! Please:")
        print("   1. Create a .env file in the project root")
        print("   2. Add your API keys:")
        print("      OPENAI_API_KEY=sk-...")
        print("      ANTHROPIC_API_KEY=sk-ant-...")
        return

    # Run examples
    await compare_providers_with_tools()
    await unified_workflow_example()
    await performance_comparison_with_workflows()
    await cost_comparison()

    print("\n\n✅ Key Takeaways:")
    print("1. WorkflowAgent provides reliable tool usage across all providers")
    print("2. Same workflow code works with OpenAI, Anthropic, and Ollama")
    print("3. Tool wrappers ensure consistent behavior")
    print("4. Each provider has different characteristics:")
    print("   - OpenAI: Fast, reliable, good general purpose")
    print("   - Anthropic: Strong reasoning, safety, competitive pricing")
    print("   - Ollama: Free, private, but slower (CPU)")
    print("\n5. Best Practices:")
    print("   - Use WorkflowAgent for any tool usage")
    print("   - Create reusable tool wrappers")
    print("   - Set appropriate timeouts per provider")
    print("   - Use .env file for API keys")
    print("   - Choose providers based on task requirements")


if __name__ == "__main__":
    asyncio.run(main())
