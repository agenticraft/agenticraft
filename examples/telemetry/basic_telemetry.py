#!/usr/bin/env python3
"""Basic telemetry example with console export.

This example shows how to enable telemetry and see traces/metrics in the console.
Uses the handler pattern for tool-like functionality.
"""

import asyncio

from agenticraft import Agent
from agenticraft.telemetry.integration import TelemetryConfig


async def main():
    """Run agent with telemetry enabled."""
    print("🔍 AgentiCraft Telemetry Example - Console Export")
    print("=" * 50)

    # Configure telemetry for console output
    telemetry = TelemetryConfig(
        enabled=True,
        traces_enabled=True,
        metrics_enabled=True,
        exporter_type="console",
        service_name="telemetry_example",
        auto_instrument=True,
    )

    # Initialize telemetry
    telemetry.initialize()

    print("\n✅ Telemetry initialized with console exporters")
    print("📊 You'll see traces and metrics printed below\n")

    # Create an agent
    agent = Agent(
        name="TelemetryDemoAgent",
        instructions="""You are a helpful assistant demonstrating telemetry features.
        
        When asked to count words, analyze the text and provide the count.
        When asked about observability, provide clear explanations.""",
        model="gpt-4o-mini",
    )

    # Run some operations
    print("🤖 Running agent operations...\n")

    # Simple query
    response1 = await agent.arun("What is observability in software?")
    print(f"\nResponse 1: {response1.content[:100]}...")

    # Query that demonstrates analysis capability
    response2 = await agent.arun(
        "Count the words in this sentence: 'Telemetry helps monitor distributed systems'. "
        "Please provide the exact count."
    )
    print(f"\nResponse 2: {response2.content}")

    # Multiple queries to show metrics aggregation
    tasks = []
    for i in range(3):
        prompt = f"Generate a random fact about observability (query {i+1})"
        tasks.append(agent.arun(prompt))

    responses = await asyncio.gather(*tasks)
    print(f"\n✅ Completed {len(responses)} parallel queries")

    # Show telemetry summary
    print("\n" + "=" * 50)
    print("📈 Telemetry Summary")
    print("=" * 50)
    print("Check the console output above for:")
    print("- Trace spans showing operation hierarchy")
    print("- Token usage metrics per provider")
    print("- Latency measurements")
    print("- Error tracking (if any)")

    # Shutdown telemetry
    from agenticraft.telemetry.metrics import shutdown_metrics
    from agenticraft.telemetry.tracer import shutdown_tracer

    print("\n🔚 Shutting down telemetry...")
    shutdown_tracer()
    shutdown_metrics()

    print("✅ Telemetry example complete!")


if __name__ == "__main__":
    asyncio.run(main())
