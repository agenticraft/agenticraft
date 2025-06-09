#!/usr/bin/env python3
"""Prometheus metrics example.

This example shows how to expose metrics for Prometheus scraping.

Prerequisites:
- Prometheus installed locally or via Docker
- Configure Prometheus to scrape localhost:8000/metrics
"""

import asyncio

from agenticraft import Agent
from agenticraft.agents import ReasoningAgent, WorkflowAgent
from agenticraft.telemetry.exporters.prometheus import save_grafana_dashboard
from agenticraft.telemetry.integration import TelemetryConfig


async def main():
    """Run agents with Prometheus metrics export."""
    print("📊 AgentiCraft Telemetry Example - Prometheus Metrics")
    print("=" * 50)

    # Configure telemetry for Prometheus export
    telemetry = TelemetryConfig(
        enabled=True,
        traces_enabled=False,  # Focus on metrics for this example
        metrics_enabled=True,
        exporter_type="prometheus",
        service_name="agenticraft_metrics",
        auto_instrument=True,
    )

    # Initialize telemetry
    telemetry.initialize()

    print("\n✅ Prometheus metrics server started!")
    print("📊 Metrics available at: http://localhost:8000/metrics")
    print("📈 Configure Prometheus to scrape this endpoint\n")

    # Save Grafana dashboard
    save_grafana_dashboard("agenticraft_dashboard.json")
    print("💾 Grafana dashboard saved to: agenticraft_dashboard.json\n")

    # Create agents
    agent = Agent(
        name="MetricsDemo",
        instructions="You help demonstrate metrics collection.",
        model="gpt-4o-mini",
    )

    reasoning_agent = ReasoningAgent(name="ReasoningMetrics", model="gpt-4o-mini")

    workflow_agent = WorkflowAgent(name="WorkflowMetrics", model="gpt-4o-mini")

    print("🤖 Running operations to generate metrics...\n")

    # Generate diverse metrics
    providers = ["openai", "anthropic", "ollama"]
    models = ["gpt-4", "claude-3", "llama2"]

    # Simulate operations over time
    for minute in range(3):
        print(f"\n⏱️ Minute {minute + 1}/3")

        # Regular operations
        tasks = []
        for i in range(5):
            # Vary the agent and prompt
            if i % 3 == 0:
                prompt = f"Generate a short fact about metric {i+1}"
                tasks.append(agent.arun(prompt))
            elif i % 3 == 1:
                prompt = f"Reason about why metric {i+1} is important"
                tasks.append(reasoning_agent.arun(prompt))
            else:
                # Create a simple workflow
                workflow = workflow_agent.create_workflow(f"metric_{i+1}_analysis")
                workflow.add_step("analyze", f"Analyze metric {i+1}")
                tasks.append(workflow_agent.execute_workflow(workflow))

        # Execute tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and errors
        successes = sum(1 for r in results if not isinstance(r, Exception))
        errors = sum(1 for r in results if isinstance(r, Exception))

        print(f"  ✅ Successful operations: {successes}")
        print(f"  ❌ Failed operations: {errors}")

        # Additional operations
        for i in range(3):
            await agent.arun(f"Explain the importance of metric {i+1}")

        # Show some example metrics queries
        if minute == 0:
            print("\n📊 Example Prometheus queries:")
            print("  - rate(agenticraft_tokens_total[5m])")
            print("  - histogram_quantile(0.99, agenticraft_latency)")
            print("  - sum(agenticraft_errors_total) by (operation)")
            print("  - rate(agenticraft_agent_operations_total[1m])")

        # Wait before next iteration
        if minute < 2:
            print("\n⏳ Waiting 30 seconds before next batch...")
            await asyncio.sleep(30)

    # Show final metrics summary
    print("\n" + "=" * 50)
    print("📈 Metrics Collection Summary")
    print("=" * 50)
    print("\n🔍 To view your metrics:")
    print("1. Open: http://localhost:8000/metrics")
    print("2. You'll see metrics like:")
    print("   - agenticraft_tokens_total")
    print("   - agenticraft_latency")
    print("   - agenticraft_errors_total")
    print("   - agenticraft_agent_operations")
    print("   - agenticraft_workflow_steps")

    print("\n🔧 Prometheus configuration:")
    print("```yaml")
    print("scrape_configs:")
    print("  - job_name: 'agenticraft'")
    print("    static_configs:")
    print("      - targets: ['localhost:8000']")
    print("```")

    print("\n📊 Grafana setup:")
    print("1. Import agenticraft_dashboard.json")
    print("2. Configure Prometheus data source")
    print("3. View real-time metrics!")

    # Keep server running for a bit
    print("\n⏳ Keeping metrics server running for 60 seconds...")
    print("📊 Check http://localhost:8000/metrics now!")
    await asyncio.sleep(60)

    # Shutdown
    from agenticraft.telemetry.metrics import shutdown_metrics

    print("\n🔚 Shutting down metrics server...")
    shutdown_metrics()

    print("✅ Prometheus metrics example complete!")


if __name__ == "__main__":
    asyncio.run(main())
