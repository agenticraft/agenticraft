#!/usr/bin/env python3
"""Performance monitoring example.

This example shows how to use telemetry to monitor and optimize performance.
"""

import asyncio
import statistics
from typing import Any

from agenticraft import Agent
from agenticraft.agents import ReasoningAgent, WorkflowAgent
from agenticraft.telemetry import LatencyTimer, create_span
from agenticraft.telemetry.integration import TelemetryConfig


class PerformanceMonitor:
    """Monitor and analyze performance metrics."""

    def __init__(self):
        self.latencies: dict[str, list[float]] = {}
        self.token_usage: dict[str, int] = {}
        self.error_counts: dict[str, int] = {}

    def record_latency(self, operation: str, latency_ms: float):
        """Record latency for an operation."""
        if operation not in self.latencies:
            self.latencies[operation] = []
        self.latencies[operation].append(latency_ms)

    def record_tokens(self, provider: str, tokens: int):
        """Record token usage."""
        if provider not in self.token_usage:
            self.token_usage[provider] = 0
        self.token_usage[provider] += tokens

    def record_error(self, operation: str):
        """Record an error."""
        if operation not in self.error_counts:
            self.error_counts[operation] = 0
        self.error_counts[operation] += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get performance statistics."""
        stats = {
            "latency_stats": {},
            "token_usage": self.token_usage,
            "error_rates": {},
        }

        # Calculate latency statistics
        for operation, latencies in self.latencies.items():
            if latencies:
                stats["latency_stats"][operation] = {
                    "count": len(latencies),
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "p90": self._percentile(latencies, 90),
                    "p99": self._percentile(latencies, 99),
                    "min": min(latencies),
                    "max": max(latencies),
                }

        # Calculate error rates
        for operation in set(
            list(self.latencies.keys()) + list(self.error_counts.keys())
        ):
            total = len(self.latencies.get(operation, []))
            errors = self.error_counts.get(operation, 0)
            if total > 0:
                stats["error_rates"][operation] = errors / total * 100

        return stats

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


async def performance_test_agents(monitor: PerformanceMonitor):
    """Test performance of different agent configurations."""

    print("\n🧪 Testing Agent Performance...")

    # Test different models
    models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

    for model in models:
        print(f"\n📊 Testing model: {model}")

        agent = Agent(
            name=f"PerfTest_{model}", instructions="Answer concisely.", model=model
        )

        # Run multiple queries
        queries = [
            "What is 2+2?",
            "Name the capital of France.",
            "What color is the sky?",
        ]

        for query in queries:
            with LatencyTimer(f"agent.{model}") as timer:
                try:
                    response = await agent.arun(query)

                    # Record metrics
                    monitor.record_latency(f"agent.{model}", timer.duration_ms)

                    # Simulate token counting
                    tokens = len(query.split()) * 2 + len(response.content.split()) * 3
                    monitor.record_tokens(model, tokens)

                except Exception as e:
                    monitor.record_error(f"agent.{model}")
                    print(f"  ❌ Error: {e}")


async def performance_test_reasoning(monitor: PerformanceMonitor):
    """Test reasoning performance with different strategies."""

    print("\n🧠 Testing Reasoning Performance...")

    strategies = ["simple", "chain_of_thought", "tree_of_thoughts"]

    for strategy in strategies:
        print(f"\n📊 Testing strategy: {strategy}")

        agent = ReasoningAgent(name=f"Reasoning_{strategy}", model="gpt-4o-mini")

        # Complex reasoning task
        task = "If all roses are flowers, and some flowers fade quickly, can we conclude that some roses fade quickly?"

        with create_span(f"reasoning.{strategy}") as span:
            span.set_attribute("strategy", strategy)

            start_time = asyncio.get_event_loop().time()

            try:
                response = await agent.arun(f"Using {strategy} reasoning: {task}")

                elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                monitor.record_latency(f"reasoning.{strategy}", elapsed_ms)

                # Analyze reasoning depth
                reasoning_steps = response.content.count(
                    "therefore"
                ) + response.content.count("because")
                span.set_attribute("reasoning_depth", reasoning_steps)

                print(
                    f"  ✅ Completed in {elapsed_ms:.0f}ms with {reasoning_steps} reasoning steps"
                )

            except Exception as e:
                monitor.record_error(f"reasoning.{strategy}")
                print(f"  ❌ Error: {e}")


async def performance_test_workflows(monitor: PerformanceMonitor):
    """Test workflow performance with different patterns."""

    print("\n🔄 Testing Workflow Performance...")

    workflow_agent = WorkflowAgent(name="WorkflowPerf", model="gpt-4o-mini")

    # Test sequential vs parallel workflows
    patterns = ["sequential", "parallel"]

    for pattern in patterns:
        print(f"\n📊 Testing pattern: {pattern}")

        workflow = workflow_agent.create_workflow(f"{pattern}_test")

        if pattern == "sequential":
            # Sequential steps
            workflow.add_step("step1", "First step")
            workflow.add_step("step2", "Second step", depends_on=["step1"])
            workflow.add_step("step3", "Third step", depends_on=["step2"])
            workflow.add_step("step4", "Fourth step", depends_on=["step3"])
        else:
            # Parallel steps
            workflow.add_step("step1", "First parallel step")
            workflow.add_step("step2", "Second parallel step")
            workflow.add_step("step3", "Third parallel step")
            workflow.add_step(
                "final", "Combine results", depends_on=["step1", "step2", "step3"]
            )

        with LatencyTimer(f"workflow.{pattern}") as timer:
            try:
                result = await workflow_agent.execute_workflow(workflow)
                monitor.record_latency(f"workflow.{pattern}", timer.duration_ms)

                print(f"  ✅ Completed in {timer.duration_ms:.0f}ms")

            except Exception as e:
                monitor.record_error(f"workflow.{pattern}")
                print(f"  ❌ Error: {e}")


async def analyze_performance_impact():
    """Analyze the performance impact of telemetry."""

    print("\n🔍 Analyzing Telemetry Overhead...")

    # Test with telemetry disabled
    agent_no_telemetry = Agent(
        name="NoTelemetry", instructions="Answer quickly.", model="gpt-4o-mini"
    )

    # Warm up
    await agent_no_telemetry.arun("Hello")

    # Measure without telemetry
    iterations = 10
    no_telemetry_times = []

    for i in range(iterations):
        start = asyncio.get_event_loop().time()
        await agent_no_telemetry.arun(f"Count to {i}")
        elapsed = (asyncio.get_event_loop().time() - start) * 1000
        no_telemetry_times.append(elapsed)

    # Now with telemetry (already enabled)
    agent_with_telemetry = Agent(
        name="WithTelemetry", instructions="Answer quickly.", model="gpt-4o-mini"
    )

    with_telemetry_times = []

    for i in range(iterations):
        start = asyncio.get_event_loop().time()
        await agent_with_telemetry.arun(f"Count to {i}")
        elapsed = (asyncio.get_event_loop().time() - start) * 1000
        with_telemetry_times.append(elapsed)

    # Calculate overhead
    avg_no_telemetry = statistics.mean(no_telemetry_times)
    avg_with_telemetry = statistics.mean(with_telemetry_times)
    overhead_ms = avg_with_telemetry - avg_no_telemetry
    overhead_percent = (overhead_ms / avg_no_telemetry) * 100

    print("\n📊 Telemetry Overhead Analysis:")
    print(f"  Average without telemetry: {avg_no_telemetry:.2f}ms")
    print(f"  Average with telemetry: {avg_with_telemetry:.2f}ms")
    print(f"  Overhead: {overhead_ms:.2f}ms ({overhead_percent:.1f}%)")

    if overhead_percent < 1:
        print("  ✅ Telemetry overhead is negligible (<1%)")
    else:
        print(f"  ⚠️ Telemetry overhead is {overhead_percent:.1f}%")


async def main():
    """Run performance monitoring example."""
    print("⚡ AgentiCraft Performance Monitoring Example")
    print("=" * 50)

    # Initialize telemetry
    telemetry = TelemetryConfig(
        enabled=True,
        traces_enabled=True,
        metrics_enabled=True,
        exporter_type="console",
        service_name="performance_monitor",
        auto_instrument=True,
    )
    telemetry.initialize()

    print("\n✅ Telemetry initialized for performance monitoring")

    # Create performance monitor
    monitor = PerformanceMonitor()

    # Run performance tests
    await performance_test_agents(monitor)
    await performance_test_reasoning(monitor)
    await performance_test_workflows(monitor)
    await analyze_performance_impact()

    # Get final statistics
    stats = monitor.get_statistics()

    # Display performance report
    print("\n" + "=" * 50)
    print("📊 Performance Report")
    print("=" * 50)

    print("\n⏱️ Latency Statistics (ms):")
    for operation, latency_stats in stats["latency_stats"].items():
        print(f"\n{operation}:")
        print(f"  Count: {latency_stats['count']}")
        print(f"  Mean: {latency_stats['mean']:.2f}")
        print(f"  Median: {latency_stats['median']:.2f}")
        print(f"  P90: {latency_stats['p90']:.2f}")
        print(f"  P99: {latency_stats['p99']:.2f}")
        print(f"  Min: {latency_stats['min']:.2f}")
        print(f"  Max: {latency_stats['max']:.2f}")

    print("\n🪙 Token Usage:")
    for provider, tokens in stats["token_usage"].items():
        estimated_cost = tokens * 0.00002  # Rough estimate
        print(f"  {provider}: {tokens} tokens (≈${estimated_cost:.4f})")

    print("\n❌ Error Rates:")
    for operation, rate in stats["error_rates"].items():
        print(f"  {operation}: {rate:.1f}%")

    # Performance recommendations
    print("\n" + "=" * 50)
    print("💡 Performance Recommendations")
    print("=" * 50)

    # Find slowest operations
    if stats["latency_stats"]:
        slowest = max(stats["latency_stats"].items(), key=lambda x: x[1]["p99"])
        print(f"\n🐌 Slowest operation: {slowest[0]} (P99: {slowest[1]['p99']:.0f}ms)")
        print("  → Consider caching or optimization")

    # Check error rates
    high_error_ops = [op for op, rate in stats["error_rates"].items() if rate > 5]
    if high_error_ops:
        print(f"\n⚠️ High error rate operations: {', '.join(high_error_ops)}")
        print("  → Investigate error handling and retry logic")

    # Token usage
    total_tokens = sum(stats["token_usage"].values())
    if total_tokens > 1000:
        print(f"\n💰 High token usage: {total_tokens} tokens")
        print("  → Consider prompt optimization or caching")

    print("\n✅ Use telemetry data to:")
    print("  1. Set performance SLIs/SLOs")
    print("  2. Identify optimization opportunities")
    print("  3. Monitor production performance")
    print("  4. Track cost per operation")
    print("  5. Detect performance regressions")

    # Shutdown
    from agenticraft.telemetry.metrics import shutdown_metrics
    from agenticraft.telemetry.tracer import shutdown_tracer

    print("\n🔚 Shutting down telemetry...")
    shutdown_tracer()
    shutdown_metrics()

    print("✅ Performance monitoring example complete!")


if __name__ == "__main__":
    asyncio.run(main())
