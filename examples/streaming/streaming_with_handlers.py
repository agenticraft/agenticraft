"""Streaming with WorkflowAgent and Tool Handlers - Proper Implementation.

This demonstrates the correct way to use tools with WorkflowAgent
in streaming contexts, following the handler pattern from the reference examples.
"""

import asyncio
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

from agenticraft.agents.workflow import StepStatus, WorkflowAgent
from agenticraft.core.streaming import create_mock_stream


class StreamingToolWrapper:
    """Wrapper to make tools work with WorkflowAgent in streaming contexts."""

    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
        self._results = {}

    async def execute(self, *args, **kwargs):
        """Execute the wrapped function."""
        try:
            result = self.func(*args, **kwargs)
            return result
        except Exception as e:
            return {"error": str(e)}

    def create_streaming_handler(self, step_name: str):
        """Create a streaming handler for workflow steps."""

        async def handler(agent, step, context):
            # Get parameters from context
            params = context.get(f"{step_name}_params", {})

            # Simulate streaming the execution
            status_msg = f"🔧 Executing {self.name}...\n"
            async for chunk in create_mock_stream(status_msg, chunk_size=5, delay=0.02):
                print(chunk.content, end="", flush=True)

            # Execute the tool
            result = await self.execute(**params)

            # Store result in context
            context[f"{step_name}_result"] = result
            self._results[step_name] = result

            # Stream the result
            if isinstance(result, dict):
                result_str = json.dumps(result, indent=2)
            else:
                result_str = str(result)

            result_msg = f"✅ Result: {result_str}\n"
            async for chunk in create_mock_stream(result_msg, chunk_size=5, delay=0.02):
                print(chunk.content, end="", flush=True)

            return result_str

        return handler


# Tool functions (not using @tool decorator)
def analyze_text(text: str) -> dict[str, Any]:
    """Analyze text and return statistics."""
    words = text.split()
    sentences = text.count(".") + text.count("!") + text.count("?")

    return {
        "text_length": len(text),
        "word_count": len(words),
        "sentence_count": sentences,
        "avg_word_length": (
            round(sum(len(w) for w in words) / len(words), 1) if words else 0
        ),
        "timestamp": datetime.now().isoformat(),
    }


def sentiment_analysis(text: str) -> dict[str, Any]:
    """Perform mock sentiment analysis."""
    # Simple mock sentiment based on keywords
    positive_words = ["good", "great", "excellent", "happy", "wonderful", "amazing"]
    negative_words = ["bad", "terrible", "awful", "sad", "horrible", "poor"]

    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    if positive_count > negative_count:
        sentiment = "positive"
        score = 0.7
    elif negative_count > positive_count:
        sentiment = "negative"
        score = 0.3
    else:
        sentiment = "neutral"
        score = 0.5

    return {
        "sentiment": sentiment,
        "confidence_score": score,
        "positive_indicators": positive_count,
        "negative_indicators": negative_count,
    }


def generate_summary(
    text: str, analysis: dict[str, Any], sentiment: dict[str, Any]
) -> str:
    """Generate a comprehensive summary report."""
    report = f"""
📊 TEXT ANALYSIS REPORT
{'=' * 50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 Original Text:
"{text[:100]}{'...' if len(text) > 100 else ''}"

📈 Statistical Analysis:
- Total Characters: {analysis.get('text_length', 0)}
- Word Count: {analysis.get('word_count', 0)}
- Sentence Count: {analysis.get('sentence_count', 0)}
- Average Word Length: {analysis.get('avg_word_length', 0)} characters

😊 Sentiment Analysis:
- Overall Sentiment: {sentiment.get('sentiment', 'unknown').upper()}
- Confidence Score: {sentiment.get('confidence_score', 0):.1%}
- Positive Indicators: {sentiment.get('positive_indicators', 0)}
- Negative Indicators: {sentiment.get('negative_indicators', 0)}

✨ Summary:
The text is {analysis.get('word_count', 0)} words long with a {sentiment.get('sentiment', 'neutral')} tone.
"""
    return report.strip()


async def streaming_tool_workflow_demo():
    """Demonstrate streaming with proper tool handlers."""
    print("🌊 Streaming Text Analysis Workflow")
    print("=" * 60)

    # Create tool wrappers
    text_analyzer = StreamingToolWrapper(
        "analyze_text", "Analyze text statistics", analyze_text
    )
    sentiment_analyzer = StreamingToolWrapper(
        "sentiment_analysis", "Analyze sentiment", sentiment_analysis
    )
    summarizer = StreamingToolWrapper(
        "generate_summary", "Generate summary report", generate_summary
    )

    # Create workflow agent
    agent = WorkflowAgent(
        name="TextAnalysisBot",
        instructions="Analyze text through multiple stages with detailed feedback.",
    )

    # Register streaming handlers
    agent.register_handler("analyze", text_analyzer.create_streaming_handler("analyze"))
    agent.register_handler(
        "sentiment", sentiment_analyzer.create_streaming_handler("sentiment")
    )
    agent.register_handler(
        "summarize", summarizer.create_streaming_handler("summarize")
    )

    # Create workflow
    workflow = agent.create_workflow(
        name="text_analysis_pipeline",
        description="Complete text analysis with streaming feedback",
    )

    # Sample text for analysis
    sample_text = """
    AgentiCraft is an amazing framework for building AI agents. 
    It provides excellent tools for workflow automation and makes it easy to create powerful applications.
    The streaming capabilities are wonderful and the documentation is great!
    """

    # Set up context with parameters
    context = {
        "input_text": sample_text.strip(),
        "analyze_params": {"text": sample_text.strip()},
        "sentiment_params": {"text": sample_text.strip()},
    }

    # Define workflow steps
    workflow.add_step(
        name="analyze",
        handler="analyze",
        action="Performing statistical text analysis...",
    )

    workflow.add_step(
        name="sentiment",
        handler="sentiment",
        action="Analyzing sentiment and emotional tone...",
        depends_on=["analyze"],
    )

    # Summary step that combines results
    async def prepare_summary_handler(agent, step, context):
        """Prepare summary with all results."""
        text = context.get("input_text", "")
        analysis = context.get("analyze_result", {})
        sentiment = context.get("sentiment_result", {})

        # Stream the summary generation
        msg = "📋 Generating comprehensive report...\n"
        async for chunk in create_mock_stream(msg, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)

        summary = generate_summary(text, analysis, sentiment)

        # Stream the final report
        async for chunk in create_mock_stream(
            summary + "\n", chunk_size=10, delay=0.01
        ):
            print(chunk.content, end="", flush=True)

        return summary

    agent.register_handler("prepare_summary", prepare_summary_handler)

    workflow.add_step(
        name="prepare_summary",
        handler="prepare_summary",
        action="Creating final analysis report...",
        depends_on=["sentiment"],
    )

    # Execute workflow with streaming
    print(f'\n📝 Analyzing text: "{sample_text.strip()[:50]}..."\n')
    print("Starting workflow execution with streaming feedback:")
    print("-" * 60)

    try:
        # Simulate streaming the workflow status
        async for chunk in create_mock_stream(
            "\n🚀 Initializing workflow...\n\n", chunk_size=5, delay=0.02
        ):
            print(chunk.content, end="", flush=True)

        result = await agent.execute_workflow(workflow, context=context)

        # Stream success message
        success_msg = "\n✅ Workflow completed successfully!\n"
        async for chunk in create_mock_stream(success_msg, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)

        # Show execution summary
        print("\n📊 Execution Summary:")
        print("-" * 40)
        for step_name, step_result in result.step_results.items():
            status_icon = "✅" if step_result.status == StepStatus.COMPLETED else "❌"
            print(f"{status_icon} {step_name}: {step_result.status}")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")


async def parallel_streaming_workflow():
    """Demonstrate parallel execution with streaming feedback."""
    print("\n\n⚡ Parallel Processing Workflow with Streaming")
    print("=" * 60)

    # Data processing functions
    def process_dataset_a(data: str) -> dict[str, Any]:
        """Process dataset A."""
        return {
            "dataset": "A",
            "records_processed": 1000,
            "processing_time": 2.5,
            "status": "success",
        }

    def process_dataset_b(data: str) -> dict[str, Any]:
        """Process dataset B."""
        return {
            "dataset": "B",
            "records_processed": 1500,
            "processing_time": 3.2,
            "status": "success",
        }

    def process_dataset_c(data: str) -> dict[str, Any]:
        """Process dataset C."""
        return {
            "dataset": "C",
            "records_processed": 800,
            "processing_time": 1.8,
            "status": "success",
        }

    def merge_results(results: list) -> dict[str, Any]:
        """Merge results from all datasets."""
        total_records = sum(r["records_processed"] for r in results)
        total_time = sum(r["processing_time"] for r in results)

        return {
            "total_records": total_records,
            "total_processing_time": total_time,
            "average_time_per_dataset": round(total_time / len(results), 2),
            "all_successful": all(r["status"] == "success" for r in results),
        }

    # Create streaming wrappers
    processor_a = StreamingToolWrapper(
        "process_a", "Process dataset A", process_dataset_a
    )
    processor_b = StreamingToolWrapper(
        "process_b", "Process dataset B", process_dataset_b
    )
    processor_c = StreamingToolWrapper(
        "process_c", "Process dataset C", process_dataset_c
    )

    # Create workflow
    agent = WorkflowAgent(
        name="ParallelProcessor",
        instructions="Process multiple datasets in parallel with streaming feedback",
    )

    # Register handlers
    agent.register_handler(
        "process_a", processor_a.create_streaming_handler("process_a")
    )
    agent.register_handler(
        "process_b", processor_b.create_streaming_handler("process_b")
    )
    agent.register_handler(
        "process_c", processor_c.create_streaming_handler("process_c")
    )

    # Merge handler with streaming
    async def merge_handler(agent, step, context):
        """Merge results with streaming feedback."""
        msg = "🔀 Merging results from all processors...\n"
        async for chunk in create_mock_stream(msg, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)

        # Collect results
        results = []
        for dataset in ["a", "b", "c"]:
            result = context.get(f"process_{dataset}_result")
            if result:
                results.append(result)

        # Merge
        merged = merge_results(results)
        context["merged_result"] = merged

        # Stream merged results
        result_msg = (
            f"✅ Merged {len(results)} results: {json.dumps(merged, indent=2)}\n"
        )
        async for chunk in create_mock_stream(result_msg, chunk_size=8, delay=0.02):
            print(chunk.content, end="", flush=True)

        return json.dumps(merged, indent=2)

    agent.register_handler("merge", merge_handler)

    # Create workflow
    workflow = agent.create_workflow(
        name="parallel_processing", description="Process datasets in parallel"
    )

    # Set up context
    context = {
        "process_a_params": {"data": "dataset_a.csv"},
        "process_b_params": {"data": "dataset_b.csv"},
        "process_c_params": {"data": "dataset_c.csv"},
    }

    # Add parallel steps
    workflow.add_step(
        name="process_a", handler="process_a", action="Processing dataset A..."
    )

    workflow.add_step(
        name="process_b", handler="process_b", action="Processing dataset B..."
    )

    workflow.add_step(
        name="process_c", handler="process_c", action="Processing dataset C..."
    )

    workflow.add_step(
        name="merge",
        handler="merge",
        action="Merging all results...",
        depends_on=["process_a", "process_b", "process_c"],
    )

    print("\nExecuting parallel workflow with streaming feedback:")
    print("-" * 60)

    try:
        # Note: In real parallel execution, these would run concurrently
        # This demo shows them sequentially for clarity
        result = await agent.execute_workflow(workflow, context=context, parallel=True)

        msg = "\n🎉 Parallel processing complete!\n"
        async for chunk in create_mock_stream(msg, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")


async def main():
    """Run streaming workflow examples with proper tool handlers."""
    print("🌊 AgentiCraft Streaming with Tool Handlers")
    print("=" * 80)
    print("Using the proper handler pattern for reliable tool integration\n")

    # Run examples
    await streaming_tool_workflow_demo()
    await parallel_streaming_workflow()

    print("\n" + "=" * 80)
    print("✅ Streaming examples completed!")
    print("\nKey takeaways:")
    print("  • Use handlers instead of @tool decorators for reliability")
    print("  • StreamingToolWrapper provides clean streaming integration")
    print("  • Data flows through workflow context")
    print("  • Works perfectly with current AgentiCraft implementation")
    print("  • No framework modifications needed!")


if __name__ == "__main__":
    asyncio.run(main())
