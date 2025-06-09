#!/usr/bin/env python3
"""OTLP/Jaeger telemetry example.

This example shows how to export traces and metrics to Jaeger or any OTLP-compatible backend.

Prerequisites:
- Run Jaeger locally: docker run -d --name jaeger -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one:latest
- Or use your own OTLP endpoint
"""

import asyncio
import os

from agenticraft import Agent
from agenticraft.agents import ReasoningAgent, WorkflowAgent
from agenticraft.telemetry.integration import TelemetryConfig


async def main():
    """Run agents with OTLP telemetry export."""
    print("🔍 AgentiCraft Telemetry Example - OTLP/Jaeger Export")
    print("=" * 50)

    # Get OTLP endpoint from environment or use default
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", "localhost:4317")

    # Configure telemetry for OTLP export
    telemetry = TelemetryConfig(
        enabled=True,
        traces_enabled=True,
        metrics_enabled=True,
        exporter_type="otlp",
        otlp_endpoint=otlp_endpoint,
        service_name="agenticraft_demo",
        auto_instrument=True,
    )

    # Initialize telemetry
    telemetry.initialize()

    print(f"\n✅ Telemetry initialized with OTLP export to: {otlp_endpoint}")
    print("📊 View traces at: http://localhost:16686 (if using Jaeger)")
    print("🔗 Service name: agenticraft_demo\n")

    # Create multiple agents to show distributed tracing
    base_agent = Agent(
        name="Coordinator",
        instructions="You coordinate tasks between other agents.",
        model="gpt-4o-mini",
    )

    reasoning_agent = ReasoningAgent(name="Reasoner", model="gpt-4o-mini")

    # Create a workflow to show complex traces
    workflow_agent = WorkflowAgent(name="WorkflowExecutor", model="gpt-4o-mini")

    # Define a workflow
    workflow = workflow_agent.create_workflow("analysis_pipeline")
    workflow.add_step("gather_data", "Gather relevant data")
    workflow.add_step("analyze", "Analyze the data", depends_on=["gather_data"])
    workflow.add_step("reason", "Apply reasoning to findings", depends_on=["analyze"])
    workflow.add_step("summarize", "Summarize results", depends_on=["reason"])

    print("🤖 Running distributed agent operations...\n")

    # Run a complex operation that creates interesting traces
    task = "Analyze the impact of telemetry on software reliability"

    # Step 1: Coordinator plans the approach
    plan = await base_agent.arun(f"Create a plan to: {task}")
    print(f"📋 Plan created: {plan.content[:100]}...")

    # Step 2: Execute workflow
    print("\n🔄 Executing workflow...")
    workflow_result = await workflow_agent.execute_workflow(
        workflow, context={"task": task}
    )
    print(f"✅ Workflow completed with status: {workflow_result.status}")

    # Step 3: Apply reasoning
    print("\n🧠 Applying reasoning...")
    reasoning_result = await reasoning_agent.arun(
        f"Based on this workflow result, provide insights: {workflow_result.format_summary()}"
    )
    print(f"💡 Insights: {reasoning_result.content[:100]}...")

    # Run parallel operations to show concurrent traces
    print("\n🚀 Running parallel operations...")
    tasks = [
        base_agent.arun("What are the key metrics for observability?"),
        reasoning_agent.arun("Why is distributed tracing important?"),
        base_agent.arun("How does telemetry improve debugging?"),
    ]

    results = await asyncio.gather(*tasks)
    print(f"✅ Completed {len(results)} parallel operations")

    # Create an error to show error tracking
    print("\n❌ Triggering an error for demonstration...")
    try:
        await base_agent.arun(
            "Force an error by using an invalid tool: use_nonexistent_tool"
        )
    except Exception as e:
        print(f"Expected error: {e}")

    # Show where to view results
    print("\n" + "=" * 50)
    print("📈 Viewing Your Telemetry Data")
    print("=" * 50)
    print("\n1. Open Jaeger UI: http://localhost:16686")
    print("2. Select service: 'agenticraft_demo'")
    print("3. Click 'Find Traces' to see all operations")
    print("\n🔍 Look for:")
    print("- Trace waterfall showing operation hierarchy")
    print("- Span attributes with agent details")
    print("- Token usage in span tags")
    print("- Error spans marked in red")
    print("- Parallel operation visualization")

    # Example trace queries
    print("\n💡 Useful Jaeger queries:")
    print("- Service: agenticraft_demo")
    print("- Operation: agent.* (all agent operations)")
    print("- Tags: error=true (find errors)")
    print("- Tags: agent.name=Reasoner (specific agent)")

    # Shutdown telemetry
    from agenticraft.telemetry.metrics import shutdown_metrics
    from agenticraft.telemetry.tracer import shutdown_tracer

    print("\n🔚 Shutting down telemetry...")
    # Give some time for final exports
    await asyncio.sleep(2)

    shutdown_tracer()
    shutdown_metrics()

    print("✅ OTLP telemetry example complete!")
    print("\n📊 Check Jaeger UI for the complete trace visualization!")


if __name__ == "__main__":
    asyncio.run(main())
