"""Performance benchmarks for reasoning patterns.

Run with: python -m pytest tests/reasoning/test_benchmarks.py -v
"""

import asyncio
import statistics
import time
from unittest.mock import MagicMock

import pytest

# Handle imports for not-yet-implemented modules
try:
    from agenticraft.reasoning.patterns import (
        ChainOfThoughtReasoning,
        ReActReasoning,
        TreeOfThoughtsReasoning,
    )

    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False
    # Create dummy classes to prevent syntax errors
    ChainOfThoughtReasoning = None
    TreeOfThoughtsReasoning = None
    ReActReasoning = None

try:
    from agenticraft.core.tool import BaseTool
except ImportError:
    from unittest.mock import MagicMock

    BaseTool = MagicMock

# Skip all tests if module not implemented
pytestmark = pytest.mark.skipif(
    not REASONING_AVAILABLE, reason="Reasoning patterns not yet implemented"
)


class BenchmarkTool(BaseTool):
    """Fast tool for benchmarking."""

    name = "benchmark_tool"
    description = "Benchmark tool"

    async def arun(self, **kwargs):
        # Simulate minimal tool execution time
        await asyncio.sleep(0.001)
        return "Result"

    def get_definition(self):
        """Get tool definition."""
        from agenticraft.core.types import ToolDefinition

        return ToolDefinition(
            name=self.name, description=self.description, parameters=[]
        )


@pytest.mark.benchmark
class TestReasoningBenchmarks:
    """Benchmark tests for reasoning patterns."""

    @pytest.fixture
    def problems(self):
        """Test problems of varying complexity."""
        return {
            "simple": "What is 2 + 2?",
            "moderate": "Explain the process of photosynthesis in plants and its importance.",
            "complex": """
                Design a distributed system that can handle 1 million concurrent users,
                with real-time data synchronization, 99.99% uptime, and compliance
                with GDPR regulations. Consider scalability, security, and cost.
            """,
        }

    async def measure_execution_time(
        self, reasoning, problem: str, iterations: int = 5
    ) -> dict[str, float]:
        """Measure execution time statistics."""
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            await reasoning.think(problem)
            end = time.perf_counter()
            times.append(end - start)

            # Reset for next iteration
            if hasattr(reasoning, "_reset"):
                reasoning._reset()
            elif hasattr(reasoning, "_reset_tree"):
                reasoning._reset_tree()

        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
        }

    @pytest.mark.asyncio
    async def test_chain_of_thought_performance(self, problems):
        """Benchmark Chain of Thought reasoning."""
        print("\n\nChain of Thought Performance:")
        print("-" * 50)

        for complexity, problem in problems.items():
            cot = ChainOfThoughtReasoning(max_steps=10)
            stats = await self.measure_execution_time(cot, problem)

            print(f"\n{complexity.upper()} problem:")
            print(f"  Mean time: {stats['mean']:.4f}s")
            print(f"  Median time: {stats['median']:.4f}s")
            print(f"  Std dev: {stats['stdev']:.4f}s")
            print(f"  Range: {stats['min']:.4f}s - {stats['max']:.4f}s")

            # Performance assertions
            if complexity == "simple":
                assert stats["mean"] < 0.1, "Simple problems should complete quickly"
            elif complexity == "moderate":
                assert (
                    stats["mean"] < 0.2
                ), "Moderate problems should complete reasonably fast"

    @pytest.mark.asyncio
    async def test_tree_of_thoughts_performance(self, problems):
        """Benchmark Tree of Thoughts reasoning."""
        print("\n\nTree of Thoughts Performance:")
        print("-" * 50)

        for complexity, problem in problems.items():
            tot = TreeOfThoughtsReasoning(
                max_depth=3, beam_width=3, pruning_threshold=0.4
            )
            stats = await self.measure_execution_time(tot, problem, iterations=3)

            print(f"\n{complexity.upper()} problem:")
            print(f"  Mean time: {stats['mean']:.4f}s")
            print(f"  Median time: {stats['median']:.4f}s")
            print(f"  Std dev: {stats['stdev']:.4f}s")
            print(f"  Nodes explored: ~{len(tot.nodes)}")

            # Tree of Thoughts is more expensive due to exploration
            if complexity == "simple":
                assert (
                    stats["mean"] < 0.3
                ), "Even simple problems explore multiple paths"

    @pytest.mark.asyncio
    async def test_react_performance(self, problems):
        """Benchmark ReAct reasoning."""
        print("\n\nReAct Performance:")
        print("-" * 50)

        tools = {"search": BenchmarkTool(), "analyze": BenchmarkTool()}

        for complexity, problem in problems.items():
            react = ReActReasoning(tools=tools, max_steps=10)
            stats = await self.measure_execution_time(react, problem, iterations=3)

            print(f"\n{complexity.upper()} problem:")
            print(f"  Mean time: {stats['mean']:.4f}s")
            print(f"  Median time: {stats['median']:.4f}s")
            print(f"  Steps taken: ~{len(react.steps)}")

            # ReAct timing depends on tool usage
            assert stats["mean"] < 0.5, "ReAct should complete in reasonable time"

    @pytest.mark.asyncio
    async def test_pattern_comparison(self, problems):
        """Compare all patterns on the same problem."""
        print("\n\nPattern Comparison:")
        print("-" * 50)

        problem = problems["moderate"]
        results = {}

        # Chain of Thought
        cot = ChainOfThoughtReasoning()
        results["Chain of Thought"] = await self.measure_execution_time(cot, problem)

        # Tree of Thoughts
        tot = TreeOfThoughtsReasoning(max_depth=3, beam_width=2)
        results["Tree of Thoughts"] = await self.measure_execution_time(tot, problem)

        # ReAct
        react = ReActReasoning(tools={"tool": BenchmarkTool()})
        results["ReAct"] = await self.measure_execution_time(react, problem)

        # Display comparison
        print(f"\nProblem: {problem[:50]}...")
        print("\nPattern Performance Comparison:")
        print(f"{'Pattern':<20} {'Mean (s)':<10} {'Median (s)':<10} {'Std Dev':<10}")
        print("-" * 50)

        for pattern, stats in results.items():
            print(
                f"{pattern:<20} {stats['mean']:<10.4f} {stats['median']:<10.4f} {stats['stdev']:<10.4f}"
            )

        # Verify relative performance
        assert (
            results["Chain of Thought"]["mean"] < results["Tree of Thoughts"]["mean"]
        ), "CoT should be faster than ToT due to linear vs tree exploration"

    @pytest.mark.asyncio
    async def test_scaling_performance(self):
        """Test how patterns scale with problem size."""
        print("\n\nScaling Performance Test:")
        print("-" * 50)

        # Create problems of increasing size
        base_problem = "Solve this step by step: "
        problem_sizes = [10, 50, 100, 200]

        for pattern_name, pattern_class in [
            ("Chain of Thought", ChainOfThoughtReasoning),
            (
                "Tree of Thoughts",
                lambda: TreeOfThoughtsReasoning(max_depth=2, beam_width=2),
            ),
        ]:
            print(f"\n{pattern_name} Scaling:")
            print(f"{'Size':<10} {'Time (s)':<10} {'Time/Size':<15}")
            print("-" * 35)

            for size in problem_sizes:
                problem = base_problem + " ".join(f"factor{i}" for i in range(size))
                reasoning = (
                    pattern_class() if callable(pattern_class) else pattern_class
                )

                start = time.perf_counter()
                await reasoning.think(problem)
                elapsed = time.perf_counter() - start

                print(f"{size:<10} {elapsed:<10.4f} {elapsed/size:<15.6f}")

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory efficiency of patterns."""
        import sys

        print("\n\nMemory Efficiency Test:")
        print("-" * 50)

        problem = "Analyze this complex scenario" + " with many details" * 10

        # Chain of Thought
        cot = ChainOfThoughtReasoning(max_steps=20)
        await cot.think(problem)
        cot_size = sys.getsizeof(cot.steps)
        print(f"Chain of Thought steps size: {cot_size} bytes")

        # Tree of Thoughts
        tot = TreeOfThoughtsReasoning(max_depth=3, beam_width=3)
        await tot.think(problem)
        tot_size = sys.getsizeof(tot.nodes)
        print(f"Tree of Thoughts nodes size: {tot_size} bytes")
        print(f"Nodes created: {len(tot.nodes)}")

        # ReAct
        react = ReActReasoning(max_steps=20)
        await react.think(problem)
        react_size = sys.getsizeof(react.steps)
        print(f"ReAct steps size: {react_size} bytes")

        # Memory assertions
        assert cot_size < 50000, "CoT should use reasonable memory"
        assert tot_size < 100000, "ToT uses more memory due to tree structure"
        assert react_size < 50000, "ReAct should use reasonable memory"

    @pytest.mark.asyncio
    async def test_concurrent_reasoning(self):
        """Test concurrent execution of reasoning patterns."""
        print("\n\nConcurrent Execution Test:")
        print("-" * 50)

        # Use more complex problems that take longer to process
        problems = [
            "Problem 1: Calculate the compound interest on $10,000 at 5% annually for 10 years, "
            + "considering monthly compounding and analyze the impact of different compounding frequencies.",
            "Problem 2: Design a microservices architecture for an e-commerce platform that handles "
            + "inventory management, order processing, payment processing, and user authentication.",
            "Problem 3: Analyze the environmental impact of electric vehicles vs traditional vehicles "
            + "considering manufacturing, usage, and disposal phases over a 10-year lifecycle.",
        ]

        # Test each pattern's concurrent performance
        for pattern_name, pattern_factory in [
            ("Chain of Thought", lambda: ChainOfThoughtReasoning(max_steps=5)),
            (
                "Tree of Thoughts",
                lambda: TreeOfThoughtsReasoning(max_depth=2, beam_width=2),
            ),
            (
                "ReAct",
                lambda: ReActReasoning(tools={"tool": BenchmarkTool()}, max_steps=5),
            ),
        ]:
            # Add small delay to simulate more realistic processing
            async def think_with_delay(reasoning, problem):
                await asyncio.sleep(0.01)  # Simulate network/processing delay
                return await reasoning.think(problem)

            # Sequential execution
            sequential_start = time.perf_counter()
            for problem in problems:
                reasoning = pattern_factory()
                await think_with_delay(reasoning, problem)
            sequential_time = time.perf_counter() - sequential_start

            # Concurrent execution
            concurrent_start = time.perf_counter()
            tasks = [
                think_with_delay(pattern_factory(), problem) for problem in problems
            ]
            await asyncio.gather(*tasks)
            concurrent_time = time.perf_counter() - concurrent_start

            speedup = sequential_time / concurrent_time
            print(f"\n{pattern_name}:")
            print(f"  Sequential: {sequential_time:.4f}s")
            print(f"  Concurrent: {concurrent_time:.4f}s")
            print(f"  Speedup: {speedup:.2f}x")

            # For very fast operations, concurrent might be slightly slower due to overhead
            # Only assert speedup for operations that take meaningful time
            if sequential_time > 0.01:  # Only check if operation takes > 10ms
                assert (
                    concurrent_time < sequential_time * 1.1
                ), f"{pattern_name} concurrent execution should not be significantly slower"

            # Always verify we get some benefit or at least no major penalty
            assert (
                speedup > 0.8
            ), f"{pattern_name} speedup should be at least 0.8x (got {speedup:.2f}x)"
