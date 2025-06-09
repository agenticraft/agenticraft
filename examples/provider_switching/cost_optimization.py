"""Example: Dynamic provider switching for cost optimization.

This example demonstrates how to switch between providers based on
task complexity to optimize costs while maintaining quality.
"""

import asyncio
import os

from agenticraft import Agent, tool
from agenticraft.core.exceptions import ProviderError


# Simple calculator tool for demonstrations
@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    # In production, use a proper expression parser
    allowed_chars = "0123456789+-*/(). "
    if all(c in allowed_chars for c in expression):
        return eval(expression)
    raise ValueError("Invalid expression")


class SmartAgent:
    """An agent that intelligently switches providers based on task complexity."""

    def __init__(self, name: str = "SmartAgent"):
        # Start with a fast, cheap model
        self.agent = Agent(
            name=name,
            instructions="""You are a helpful AI assistant that can handle various tasks.
            For simple queries, provide direct answers.
            For complex tasks, think step by step.""",
            model="gpt-3.5-turbo",  # Start with cheaper model
            tools=[calculate],
        )

        # Track usage for cost estimation
        self.usage_stats = {
            "openai": {"calls": 0, "tokens": 0},
            "anthropic": {"calls": 0, "tokens": 0},
            "ollama": {"calls": 0, "tokens": 0},
        }

    def estimate_complexity(self, prompt: str) -> str:
        """Estimate task complexity to choose appropriate provider."""
        # Simple heuristic based on prompt characteristics
        prompt_lower = prompt.lower()

        # High complexity indicators
        if any(
            word in prompt_lower
            for word in [
                "analyze",
                "comprehensive",
                "detailed",
                "research",
                "compare",
                "evaluate",
                "design",
                "architect",
            ]
        ):
            return "high"

        # Low complexity indicators
        if any(
            word in prompt_lower
            for word in [
                "what is",
                "define",
                "hello",
                "simple",
                "basic",
                "calculate",
                "convert",
            ]
        ):
            return "low"

        # Check prompt length
        if len(prompt.split()) > 50:
            return "high"
        elif len(prompt.split()) < 10:
            return "low"

        return "medium"

    async def run(self, prompt: str) -> str:
        """Run the agent with automatic provider selection."""
        complexity = self.estimate_complexity(prompt)

        # Choose provider based on complexity
        if complexity == "high":
            # Use most capable model for complex tasks
            provider, model = "anthropic", "claude-3-opus-20240229"
        elif complexity == "medium":
            # Use balanced model
            provider, model = "openai", "gpt-4"
        else:
            # Use cheap/fast model for simple tasks
            if self._is_ollama_available():
                provider, model = "ollama", "llama2"
            else:
                provider, model = "openai", "gpt-3.5-turbo"

        # Switch to appropriate provider
        print(f"Task complexity: {complexity}")
        print(f"Switching to {provider} with model {model}")

        try:
            self.agent.set_provider(provider, model=model)
        except ProviderError as e:
            print(f"Failed to switch to {provider}: {e}")
            # Fallback to OpenAI
            self.agent.set_provider("openai", model="gpt-3.5-turbo")
            provider = "openai"

        # Run the task
        response = await self.agent.arun(prompt)

        # Track usage
        self.usage_stats[provider]["calls"] += 1
        if "usage" in response.metadata:
            self.usage_stats[provider]["tokens"] += response.metadata.get(
                "total_tokens", 0
            )

        return response.content

    def _is_ollama_available(self) -> bool:
        """Check if Ollama is running locally."""
        import httpx

        try:
            response = httpx.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_usage_report(self) -> str:
        """Get a report of provider usage."""
        report = "Provider Usage Report:\n"
        report += "-" * 40 + "\n"

        for provider, stats in self.usage_stats.items():
            if stats["calls"] > 0:
                report += f"{provider.capitalize()}:\n"
                report += f"  Calls: {stats['calls']}\n"
                report += f"  Tokens: {stats['tokens']}\n"

                # Estimate costs (example rates)
                if provider == "openai":
                    cost = stats["tokens"] * 0.00002  # $0.02 per 1K tokens
                elif provider == "anthropic":
                    cost = stats["tokens"] * 0.00003  # $0.03 per 1K tokens
                else:
                    cost = 0  # Local Ollama is free

                report += f"  Estimated Cost: ${cost:.4f}\n"
                report += "\n"

        return report


async def main():
    """Demonstrate dynamic provider switching."""
    # Set up API keys (in production, use environment variables)
    os.environ["OPENAI_API_KEY"] = "your-openai-key"
    os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key"

    # Create smart agent
    agent = SmartAgent()

    # Test various complexity tasks
    tasks = [
        # Low complexity - should use cheap/fast model
        "Hello! How are you?",
        "Calculate 42 * 17",
        "What is the capital of France?",
        # Medium complexity - should use GPT-4
        "Explain the concept of recursion in programming with an example",
        "What are the main differences between Python and JavaScript?",
        # High complexity - should use Claude
        "Analyze the potential impact of quantum computing on current encryption methods and propose strategies for post-quantum cryptography",
        "Design a comprehensive architecture for a real-time collaborative document editing system with conflict resolution",
    ]

    print("Running tasks with automatic provider selection...\n")

    for i, task in enumerate(tasks, 1):
        print(f"\nTask {i}: {task[:50]}...")
        print("-" * 60)

        response = await agent.run(task)
        print(f"Response: {response[:200]}...")
        print()

    # Show usage report
    print("\n" + "=" * 60)
    print(agent.get_usage_report())


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
