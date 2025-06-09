"""Example: Provider failover and resilience.

This example demonstrates how to implement automatic failover between
providers to ensure high availability and resilience.
"""

import asyncio
import time
from datetime import datetime, timedelta

from agenticraft import Agent
from agenticraft.core.exceptions import AgentError


class ResilientAgent:
    """An agent with automatic provider failover capabilities."""

    def __init__(
        self,
        name: str = "ResilientAgent",
        providers: list[tuple[str, str]] | None = None,
    ):
        """Initialize with a list of provider fallback options.

        Args:
            name: Agent name
            providers: List of (provider_name, model) tuples in priority order
        """
        self.name = name

        # Default provider chain
        if providers is None:
            self.providers = [
                ("openai", "gpt-4"),
                ("anthropic", "claude-3-sonnet-20240229"),
                ("openai", "gpt-3.5-turbo"),  # Fallback to cheaper OpenAI
                ("ollama", "llama2"),  # Last resort: local model
            ]
        else:
            self.providers = providers

        # Initialize with first provider
        self.current_provider_index = 0
        provider, model = self.providers[0]

        self.agent = Agent(
            name=name,
            instructions="You are a resilient AI assistant that maintains service availability.",
            model=model,
        )

        # Track provider health
        self.provider_health = {
            provider: {"failures": 0, "last_failure": None, "blacklisted_until": None}
            for provider, _ in self.providers
        }

        # Configuration
        self.max_retries = 3
        self.blacklist_duration = timedelta(minutes=5)
        self.failure_threshold = 3

    async def run(self, prompt: str, **kwargs) -> str:
        """Run the agent with automatic failover on errors."""
        attempt = 0
        last_error = None

        while attempt < len(self.providers):
            provider, model = self._get_next_available_provider()

            if provider is None:
                # All providers are blacklisted
                raise AgentError(
                    "All providers are currently unavailable. "
                    f"Last error: {last_error}"
                )

            try:
                # Switch to the provider
                print(f"Attempting with {provider} ({model})...")
                self.agent.set_provider(provider, model=model)

                # Try to run the task
                start_time = time.time()
                response = await self.agent.arun(prompt, **kwargs)
                elapsed = time.time() - start_time

                # Success! Reset failure count for this provider
                self.provider_health[provider]["failures"] = 0

                print(f"Success with {provider} in {elapsed:.2f}s")
                return response.content

            except Exception as e:
                last_error = e
                print(f"Failed with {provider}: {e}")

                # Record failure
                self._record_failure(provider)

                # Try next provider
                attempt += 1
                continue

        # All providers failed
        raise AgentError(
            f"All providers failed after {attempt} attempts. "
            f"Last error: {last_error}"
        )

    def _get_next_available_provider(self) -> tuple[str, str] | None:
        """Get the next available provider that isn't blacklisted."""
        now = datetime.now()

        # Try each provider in order
        for provider, model in self.providers:
            health = self.provider_health[provider]

            # Check if blacklisted
            if health["blacklisted_until"] and health["blacklisted_until"] > now:
                print(f"{provider} is blacklisted until {health['blacklisted_until']}")
                continue

            # Clear blacklist if expired
            if health["blacklisted_until"] and health["blacklisted_until"] <= now:
                health["blacklisted_until"] = None
                health["failures"] = 0
                print(f"{provider} blacklist expired, available again")

            return provider, model

        return None, None

    def _record_failure(self, provider: str) -> None:
        """Record a provider failure and potentially blacklist it."""
        health = self.provider_health[provider]
        health["failures"] += 1
        health["last_failure"] = datetime.now()

        # Blacklist if too many failures
        if health["failures"] >= self.failure_threshold:
            health["blacklisted_until"] = datetime.now() + self.blacklist_duration
            print(
                f"{provider} blacklisted due to {health['failures']} failures. "
                f"Will retry after {health['blacklisted_until']}"
            )

    def get_health_report(self) -> str:
        """Get a report of provider health status."""
        report = f"Provider Health Report for {self.name}:\n"
        report += "=" * 50 + "\n"

        now = datetime.now()
        for provider, _ in self.providers:
            health = self.provider_health[provider]

            status = "Healthy"
            if health["blacklisted_until"] and health["blacklisted_until"] > now:
                remaining = health["blacklisted_until"] - now
                status = f"Blacklisted ({remaining.seconds}s remaining)"
            elif health["failures"] > 0:
                status = f"Degraded ({health['failures']} failures)"

            report += f"\n{provider.upper()}:\n"
            report += f"  Status: {status}\n"
            report += f"  Failures: {health['failures']}\n"

            if health["last_failure"]:
                report += f"  Last Failure: {health['last_failure'].strftime('%Y-%m-%d %H:%M:%S')}\n"

        return report


async def simulate_failures():
    """Simulate provider failures to demonstrate failover."""
    import random

    # Create resilient agent
    agent = ResilientAgent()

    # Simulate various scenarios
    print("Simulating provider failures and recoveries...\n")

    prompts = [
        "What's the weather like today?",
        "Explain quantum computing in simple terms",
        "Write a haiku about resilience",
        "Calculate the fibonacci sequence up to 10",
        "What are the benefits of microservices architecture?",
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"\n{'='*60}")
        print(f"Request {i}: {prompt}")
        print(f"{'='*60}")

        # Randomly simulate provider issues
        if random.random() < 0.3:  # 30% chance of issues
            # Temporarily break the current provider
            current_provider = agent.providers[0][0]
            print(f"⚠️  Simulating {current_provider} failure...")

            # This would be done by the actual provider in real scenarios
            # Here we're just demonstrating the failover mechanism

        try:
            response = await agent.run(prompt)
            print(f"\n✅ Response: {response[:100]}...")
        except AgentError as e:
            print(f"\n❌ Failed: {e}")

        # Show health status periodically
        if i % 3 == 0:
            print(f"\n{agent.get_health_report()}")

        # Small delay between requests
        await asyncio.sleep(1)

    # Final health report
    print(f"\n\nFinal {agent.get_health_report()}")


async def main():
    """Demonstrate resilient agent with provider failover."""
    import os

    # Set up API keys
    os.environ["OPENAI_API_KEY"] = "your-openai-key"
    os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key"

    # Example 1: Basic failover
    print("Example 1: Basic Failover")
    print("-" * 40)

    agent = ResilientAgent()

    try:
        # This will automatically failover if primary provider fails
        response = await agent.run("Tell me a joke about programming")
        print(f"Response: {response}")
    except AgentError as e:
        print(f"All providers failed: {e}")

    # Example 2: Custom provider chain
    print("\n\nExample 2: Custom Provider Chain")
    print("-" * 40)

    custom_agent = ResilientAgent(
        name="CustomFailover",
        providers=[
            ("anthropic", "claude-3-opus-20240229"),  # Primary: best quality
            (
                "anthropic",
                "claude-3-sonnet-20240229",
            ),  # Secondary: same provider, cheaper
            ("openai", "gpt-4"),  # Tertiary: different provider
            ("ollama", "mistral"),  # Quaternary: local fallback
        ],
    )

    response = await custom_agent.run(
        "What are the key principles of fault-tolerant system design?"
    )
    print(f"Response: {response[:200]}...")

    # Example 3: Simulate failures
    print("\n\nExample 3: Simulating Failures")
    print("-" * 40)

    await simulate_failures()


if __name__ == "__main__":
    asyncio.run(main())
