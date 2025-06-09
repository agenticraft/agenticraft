"""Advanced Streaming with WorkflowAgent - Handler Pattern.

This is the proper way to do streaming with tools in AgentiCraft,
using handlers and tool wrappers instead of @tool decorators.
"""

import asyncio
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from agenticraft.agents.workflow import StepStatus, WorkflowAgent
from agenticraft.core.streaming import (
    create_mock_stream,
)


class AdvancedStreamingToolWrapper:
    """Advanced tool wrapper with streaming capabilities."""

    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
        self.execution_history = []

    async def execute_with_streaming(self, *args, **kwargs):
        """Execute function with simulated streaming output."""
        start_time = time.time()

        # Stream execution start
        start_msg = f"\n🔧 {self.name}: Starting execution...\n"
        async for chunk in create_mock_stream(start_msg, chunk_size=5, delay=0.01):
            print(chunk.content, end="", flush=True)

        # Execute the actual function
        try:
            result = self.func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Record execution
            self.execution_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "args": args,
                    "kwargs": kwargs,
                    "result": result,
                    "execution_time": execution_time,
                }
            )

            # Stream result
            if isinstance(result, dict):
                result_str = f"   Result: {result}\n"
            else:
                result_str = f"   Result: {result}\n"

            async for chunk in create_mock_stream(result_str, chunk_size=5, delay=0.01):
                print(chunk.content, end="", flush=True)

            return result

        except Exception as e:
            error_msg = f"   ❌ Error: {str(e)}\n"
            async for chunk in create_mock_stream(error_msg, chunk_size=5, delay=0.01):
                print(chunk.content, end="", flush=True)
            raise

    def create_advanced_handler(
        self, step_name: str, progress_callback: Callable | None = None
    ):
        """Create an advanced handler with progress tracking."""

        async def handler(agent, step, context):
            # Get parameters
            params = context.get(f"{step_name}_params", {})

            # Progress tracking
            if progress_callback:
                await progress_callback(step_name, "started", 0)

            # Execute with streaming
            result = await self.execute_with_streaming(**params)

            # Store result
            context[f"{step_name}_result"] = result

            # Progress complete
            if progress_callback:
                await progress_callback(step_name, "completed", 100)

            return str(result)

        return handler


# Tool functions (regular functions, not decorated)
def get_current_time() -> str:
    """Get the current time."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def calculate_expression(expression: str) -> dict[str, Any]:
    """Calculate a mathematical expression safely."""
    try:
        # Safe evaluation with limited scope
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": lambda x: x**0.5,
        }

        # Clean the expression
        clean_expr = expression.replace("×", "*").replace("÷", "/")

        result = eval(clean_expr, {"__builtins__": {}}, allowed_names)

        return {
            "expression": expression,
            "result": float(result),
            "calculated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "calculated_at": datetime.now().isoformat(),
        }


def analyze_data_stream(data: list) -> dict[str, Any]:
    """Analyze a stream of data points."""
    if not data:
        return {"error": "No data provided"}

    values = [float(d) for d in data if isinstance(d, (int, float))]

    return {
        "count": len(values),
        "sum": sum(values),
        "average": sum(values) / len(values) if values else 0,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "range": max(values) - min(values) if values else 0,
    }


def generate_insights(time_data: str, calc_data: dict, analysis_data: dict) -> str:
    """Generate insights from multiple data sources."""
    insights = f"""
🎯 ADVANCED ANALYSIS INSIGHTS
{'=' * 50}
Generated at: {time_data}

📊 Calculation Results:
{'-' * 30}"""

    if "error" not in calc_data:
        insights += f"""
Expression: {calc_data.get('expression', 'N/A')}
Result: {calc_data.get('result', 'N/A')}
"""
    else:
        insights += f"""
Expression: {calc_data.get('expression', 'N/A')}
Error: {calc_data.get('error', 'Unknown error')}
"""

    insights += f"""
📈 Data Stream Analysis:
{'-' * 30}
Total Points: {analysis_data.get('count', 0)}
Sum: {analysis_data.get('sum', 0):.2f}
Average: {analysis_data.get('average', 0):.2f}
Range: {analysis_data.get('range', 0):.2f} (Min: {analysis_data.get('min', 0)}, Max: {analysis_data.get('max', 0)})

💡 Key Insights:
{'-' * 30}"""

    # Generate some insights
    if analysis_data.get("count", 0) > 0:
        avg = analysis_data.get("average", 0)
        if avg > 100:
            insights += "• Data shows high average values (>100)\n"
        elif avg < 10:
            insights += "• Data shows low average values (<10)\n"

        range_val = analysis_data.get("range", 0)
        if range_val > avg:
            insights += "• High variability detected (range > average)\n"
        else:
            insights += "• Data shows consistent values (low variability)\n"

    insights += "\n✅ Analysis complete!"

    return insights


async def advanced_streaming_example():
    """Advanced example with streaming, progress tracking, and error handling."""
    print("🚀 Advanced Streaming Workflow Example")
    print("=" * 60)

    # Create tool wrappers
    time_tool = AdvancedStreamingToolWrapper(
        "get_time", "Get current time", get_current_time
    )
    calc_tool = AdvancedStreamingToolWrapper(
        "calculate", "Calculate expression", calculate_expression
    )
    analyze_tool = AdvancedStreamingToolWrapper(
        "analyze", "Analyze data", analyze_data_stream
    )
    insights_tool = AdvancedStreamingToolWrapper(
        "insights", "Generate insights", generate_insights
    )

    # Progress tracking
    progress_tracker = {}

    async def update_progress(step_name: str, status: str, percent: int):
        """Update progress for a step."""
        progress_tracker[step_name] = {"status": status, "percent": percent}

        # Display progress bar
        bar_width = 30
        filled = int(bar_width * percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        print(f"\r   Progress [{bar}] {percent}%", end="", flush=True)
        if percent == 100:
            print()  # New line after completion

    # Create workflow agent
    agent = WorkflowAgent(
        name="AdvancedAnalyzer",
        instructions="Perform advanced analysis with detailed streaming feedback",
    )

    # Register handlers with progress tracking
    agent.register_handler(
        "get_time", time_tool.create_advanced_handler("get_time", update_progress)
    )
    agent.register_handler(
        "calculate", calc_tool.create_advanced_handler("calculate", update_progress)
    )
    agent.register_handler(
        "analyze", analyze_tool.create_advanced_handler("analyze", update_progress)
    )

    # Custom insights handler with interruption support
    async def insights_handler(agent, step, context):
        """Generate insights with interruption support."""
        time_data = context.get("get_time_result", "")
        calc_data = context.get("calculate_result", {})
        analysis_data = context.get("analyze_result", {})

        # Stream the insights generation
        msg = "\n🧠 Generating comprehensive insights...\n"
        async for chunk in create_mock_stream(msg, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)

        insights = generate_insights(time_data, calc_data, analysis_data)

        # Stream insights with interruption check
        interrupted = False
        partial_output = ""

        for i, char in enumerate(insights):
            partial_output += char

            # Check for interruption condition (e.g., specific keyword)
            if "high variability" in partial_output.lower() and not interrupted:
                interrupted = True
                print("\n\n⚠️ Detected high variability - flagging for review!")
                await asyncio.sleep(0.5)

            # Stream character
            if i % 5 == 0:  # Stream in small chunks
                chunk_text = insights[max(0, i - 4) : i + 1]
                print(chunk_text, end="", flush=True)
                await asyncio.sleep(0.01)

        # Print remaining characters
        remaining = len(insights) % 5
        if remaining > 0:
            print(insights[-remaining:], end="", flush=True)

        return insights

    agent.register_handler("generate_insights", insights_handler)

    # Create workflow
    workflow = agent.create_workflow(
        name="advanced_analysis",
        description="Advanced analysis with streaming and progress tracking",
    )

    # Set up context
    sample_data = [42, 156, 89, 234, 67, 190, 45, 178, 92, 201]

    context = {
        "get_time_params": {},
        "calculate_params": {"expression": "123 * 456 + 789"},
        "analyze_params": {"data": sample_data},
    }

    # Define workflow steps
    workflow.add_step(
        name="get_time", handler="get_time", action="Getting current timestamp..."
    )

    workflow.add_step(
        name="calculate",
        handler="calculate",
        action="Performing calculations...",
        depends_on=["get_time"],
    )

    workflow.add_step(
        name="analyze",
        handler="analyze",
        action="Analyzing data stream...",
        depends_on=["calculate"],
    )

    workflow.add_step(
        name="generate_insights",
        handler="generate_insights",
        action="Generating comprehensive insights...",
        depends_on=["analyze"],
    )

    print("\nStarting advanced workflow with streaming feedback:")
    print("-" * 60)

    try:
        # Execute workflow
        result = await agent.execute_workflow(workflow, context=context)

        # Stream completion message
        complete_msg = "\n\n✅ Advanced workflow completed successfully!\n"
        async for chunk in create_mock_stream(complete_msg, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)

        # Show execution summary
        print("\n📊 Execution Summary:")
        print("-" * 40)
        total_duration = 0
        for step_name, step_result in result.step_results.items():
            duration = step_result.duration or 0
            total_duration += duration
            status_icon = "✅" if step_result.status == StepStatus.COMPLETED else "❌"
            print(f"{status_icon} {step_name}: {duration:.2f}s")

        print(f"\nTotal execution time: {total_duration:.2f}s")

        # Show tool execution history
        print("\n🔧 Tool Execution History:")
        print("-" * 40)
        for tool in [time_tool, calc_tool, analyze_tool]:
            if tool.execution_history:
                print(f"\n{tool.name}:")
                for exec_record in tool.execution_history:
                    print(f"  • Executed at {exec_record['timestamp']}")
                    print(f"    Time: {exec_record['execution_time']:.3f}s")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback

        traceback.print_exc()


async def streaming_with_retry_example():
    """Example showing retry logic with streaming feedback."""
    print("\n\n🔄 Streaming with Retry Logic")
    print("=" * 60)

    # Simulated unreliable service
    call_count = 0

    def unreliable_api_call(query: str) -> dict[str, Any]:
        """Simulated API that fails sometimes."""
        nonlocal call_count
        call_count += 1

        # Fail first 2 attempts
        if call_count <= 2:
            raise Exception(f"API temporarily unavailable (attempt {call_count})")

        return {
            "query": query,
            "response": f"Success on attempt {call_count}",
            "data": {"value": 42},
        }

    # Create wrapper with retry logic
    class RetryableToolWrapper(AdvancedStreamingToolWrapper):
        """Tool wrapper with retry capabilities."""

        async def execute_with_retry(self, max_retries: int = 3, *args, **kwargs):
            """Execute with retry logic and streaming feedback."""
            for attempt in range(1, max_retries + 1):
                try:
                    # Stream attempt message
                    attempt_msg = f"\n🔄 Attempt {attempt}/{max_retries}...\n"
                    async for chunk in create_mock_stream(
                        attempt_msg, chunk_size=5, delay=0.02
                    ):
                        print(chunk.content, end="", flush=True)

                    # Try execution
                    result = await self.execute_with_streaming(*args, **kwargs)

                    # Success message
                    success_msg = f"✅ Success on attempt {attempt}!\n"
                    async for chunk in create_mock_stream(
                        success_msg, chunk_size=5, delay=0.02
                    ):
                        print(chunk.content, end="", flush=True)

                    return result

                except Exception as e:
                    if attempt < max_retries:
                        # Stream retry message
                        retry_msg = (
                            f"⚠️ Failed: {e}\n   Retrying in {attempt} seconds...\n"
                        )
                        async for chunk in create_mock_stream(
                            retry_msg, chunk_size=5, delay=0.02
                        ):
                            print(chunk.content, end="", flush=True)

                        await asyncio.sleep(attempt)
                    else:
                        # Final failure
                        fail_msg = f"❌ Failed after {max_retries} attempts: {e}\n"
                        async for chunk in create_mock_stream(
                            fail_msg, chunk_size=5, delay=0.02
                        ):
                            print(chunk.content, end="", flush=True)
                        raise

    # Create retryable tool
    api_tool = RetryableToolWrapper(
        "api_call", "Call unreliable API", unreliable_api_call
    )

    # Simple test
    print("Testing API with retry logic:")
    print("-" * 40)

    try:
        call_count = 0  # Reset counter
        result = await api_tool.execute_with_retry(3, query="test query")
        print(f"\nFinal result: {result}")
    except Exception as e:
        print(f"\nFailed to get result: {e}")


async def main():
    """Run advanced streaming examples."""
    print("🌊 Advanced Streaming with WorkflowAgent")
    print("=" * 80)
    print("Using handler pattern for reliable tool integration with streaming\n")

    # Run examples
    await advanced_streaming_example()
    await streaming_with_retry_example()

    print("\n" + "=" * 80)
    print("✅ Advanced streaming examples completed!")
    print("\nKey features demonstrated:")
    print("  • StreamingToolWrapper for clean tool integration")
    print("  • Progress tracking with visual feedback")
    print("  • Interruption detection and handling")
    print("  • Retry logic with streaming status")
    print("  • Tool execution history tracking")
    print("  • No @tool decorator issues!")


if __name__ == "__main__":
    asyncio.run(main())
