#!/usr/bin/env python3
"""Integration example showing auto-instrumentation.

This example demonstrates how telemetry auto-instrumentation works
across different AgentiCraft components, using the handler pattern
for tool-like functionality with WorkflowAgent.
"""

import asyncio
import json

from agenticraft import Agent
from agenticraft.agents import ReasoningAgent, WorkflowAgent
from agenticraft.telemetry.integration import TelemetryConfig


# Handler functions for workflow steps
def calculate_stats_handler(agent, step, context):
    """Calculate statistics from numbers in context."""
    numbers = context.get("numbers", [])

    if not numbers:
        return json.dumps({"error": "No numbers provided"})

    stats = {
        "count": len(numbers),
        "sum": sum(numbers),
        "mean": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
    }

    # Store result in context for next steps
    context["stats_result"] = stats

    return json.dumps(stats, indent=2)


def format_report_handler(agent, step, context):
    """Format statistics into a report."""
    stats = context.get("stats_result", {})
    title = context.get("report_title", "Statistics Report")

    report = f"# {title}\n\n"
    for key, value in stats.items():
        report += f"- **{key}**: {value}\n"

    context["formatted_report"] = report
    return report


async def main():
    """Run integration example with auto-instrumentation."""
    print("🔗 AgentiCraft Telemetry Integration Example")
    print("=" * 50)

    # Configure telemetry with auto-instrumentation
    telemetry = TelemetryConfig(
        enabled=True,
        traces_enabled=True,
        metrics_enabled=True,
        exporter_type="console",
        service_name="integration_demo",
        auto_instrument=True,  # This enables automatic instrumentation
    )

    # Initialize telemetry
    telemetry.initialize()

    print("\n✅ Auto-instrumentation enabled")
    print("📊 All agents, tools, and providers will be automatically traced\n")

    # Create various agents to show instrumentation
    base_agent = Agent(
        name="BaseAgent",
        instructions="You help coordinate between other agents and analyze data.",
        model="gpt-4o-mini",
    )

    reasoning_agent = ReasoningAgent(name="Reasoner", model="gpt-4o-mini")

    workflow_agent = WorkflowAgent(
        name="DataProcessor",
        instructions="You coordinate data processing workflows.",
        model="gpt-4o-mini",
    )

    # Register handlers for workflow agent
    workflow_agent.register_handler("calculate_stats", calculate_stats_handler)
    workflow_agent.register_handler("format_report", format_report_handler)

    print("🤖 Running integrated operations...\n")

    # 1. Basic agent operation (auto-traced)
    print("1️⃣ Basic Agent Operation")
    response = await base_agent.arun("What are the benefits of observability?")
    print(f"   Response: {response.content[:80]}...")

    # 2. Agent analyzing data (auto-traced)
    print("\n2️⃣ Data Analysis with Agent")
    analysis_response = await base_agent.arun(
        "Analyze these numbers and tell me what patterns you see: 23, 45, 67, 89, 12, 34, 56. "
        "Calculate the average and identify if they're mostly increasing."
    )
    print(f"   Analysis: {analysis_response.content[:80]}...")

    # 3. Reasoning (auto-traced)
    print("\n3️⃣ Reasoning Operation")
    reasoning_response = await reasoning_agent.arun(
        "Explain why distributed tracing is important for microservices"
    )
    print(f"   Reasoning: {reasoning_response.content[:80]}...")

    # 4. Workflow execution with handlers (auto-traced)
    print("\n4️⃣ Workflow Execution with Handlers")

    # Create workflow
    workflow = workflow_agent.create_workflow(
        name="data_analysis_pipeline", description="Process and analyze numerical data"
    )

    # Add steps using handlers
    workflow.add_step(
        name="calculate",
        handler="calculate_stats",
        action="Calculating statistics for the provided numbers",
    )

    workflow.add_step(
        name="format",
        handler="format_report",
        action="Formatting the results into a readable report",
        depends_on=["calculate"],
    )

    # Execute workflow with context
    context = {
        "numbers": [23, 45, 67, 89, 12, 34, 56],
        "report_title": "Telemetry Demo Statistics",
    }

    workflow_result = await workflow_agent.execute_workflow(workflow, context=context)
    print(f"   Workflow status: {workflow_result.status}")

    if context.get("formatted_report"):
        print("\n   Generated Report:")
        print("   " + "\n   ".join(context["formatted_report"].split("\n")[:5]))

    # 5. Parallel operations (auto-traced)
    print("\n5️⃣ Parallel Operations")
    parallel_tasks = [
        base_agent.arun("What is a trace?"),
        reasoning_agent.arun("Why are metrics important?"),
        base_agent.arun("What are the benefits of observability?"),
    ]

    parallel_results = await asyncio.gather(*parallel_tasks)
    print(f"   Completed {len(parallel_results)} parallel operations")

    # 6. Complex workflow with multiple handlers
    print("\n6️⃣ Complex Data Pipeline")

    # Additional handler for data transformation
    def transform_data_handler(agent, step, context):
        """Transform the statistics data."""
        stats = context.get("stats_result", {})

        # Add derived metrics
        if "mean" in stats and "min" in stats and "max" in stats:
            stats["range"] = stats["max"] - stats["min"]
            stats["normalized_mean"] = (stats["mean"] - stats["min"]) / (
                stats["range"] if stats["range"] > 0 else 1
            )

        context["transformed_stats"] = stats
        return f"Added derived metrics: range={stats.get('range', 'N/A')}"

    workflow_agent.register_handler("transform_data", transform_data_handler)

    # Create more complex workflow
    complex_workflow = workflow_agent.create_workflow("complex_analysis")
    complex_workflow.add_step(
        "calc", handler="calculate_stats", action="Calculate basic stats"
    )
    complex_workflow.add_step(
        "transform",
        handler="transform_data",
        action="Add derived metrics",
        depends_on=["calc"],
    )
    complex_workflow.add_step(
        "report",
        handler="format_report",
        action="Generate final report",
        depends_on=["transform"],
    )

    # Execute with new data
    complex_context = {
        "numbers": [10, 20, 30, 40, 50],
        "report_title": "Complex Analysis Report",
    }

    complex_result = await workflow_agent.execute_workflow(
        complex_workflow, context=complex_context
    )
    print(f"   Complex workflow completed: {complex_result.status}")

    # Show telemetry insights
    print("\n" + "=" * 50)
    print("📈 Auto-Instrumentation Benefits")
    print("=" * 50)
    print("\n✅ What was automatically traced:")
    print("1. All agent.run() and agent.arun() calls")
    print("2. Handler executions in workflows")
    print("3. Workflow step executions")
    print("4. LLM API calls with token counts")
    print("5. Error tracking and exceptions")
    print("6. Latency measurements for all operations")

    print("\n💡 Key Patterns Demonstrated:")
    print("- Basic Agent: Direct prompt-response interactions")
    print("- Workflow Agent: Orchestrated handlers for data processing")
    print("- All patterns are fully instrumented!")

    print("\n🔍 Check the console output above to see:")
    print("- Hierarchical span relationships")
    print("- Automatic attribute collection")
    print("- Token usage per provider/model")
    print("- Operation latencies")

    # Shutdown telemetry
    from agenticraft.telemetry import shutdown_metrics, shutdown_tracer

    print("\n🔚 Shutting down telemetry...")
    shutdown_tracer()
    shutdown_metrics()

    print("✅ Integration example complete!")


if __name__ == "__main__":
    asyncio.run(main())
