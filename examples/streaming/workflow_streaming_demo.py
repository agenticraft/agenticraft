#!/usr/bin/env python3
"""Quick demo of WorkflowAgent with streaming and tool wrappers.

This is a minimal example showing how streaming works with WorkflowAgent.
"""

import asyncio

from agenticraft import tool
from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.core.streaming import create_mock_stream


# Define a simple tool
@tool
def analyze_text(text: str) -> dict:
    """Analyze text and return statistics."""
    return {
        "length": len(text),
        "words": len(text.split()),
        "sentences": text.count(".") + text.count("!") + text.count("?"),
    }


async def demo_workflow_streaming():
    """Demonstrate WorkflowAgent with streaming."""
    print("🌊 WorkflowAgent Streaming Demo")
    print("=" * 50)

    # Create WorkflowAgent
    workflow = WorkflowAgent(
        name="TextAnalyzer", instructions="Analyze text with streaming progress updates"
    )

    # Register analyze handler
    def analyze_handler(agent, step, context):
        text = context.get("input_text", "")
        result = analyze_text(text)
        context["analyze_result"] = result
        return f"Analysis complete: {result['words']} words, {result['sentences']} sentences"

    workflow.register_handler("analyze", analyze_handler)

    # Create a workflow
    workflow_def = workflow.create_workflow(
        name="text_analysis", description="Analyze text and generate report"
    )

    # Add workflow steps
    workflow_def.add_step(name="collect_input", action="Collect text input from user")
    workflow_def.add_step(
        name="analyze",
        action="Analyze the text using analyze_text tool",
        handler="analyze",
        depends_on=["collect_input"],
    )
    workflow_def.add_step(
        name="generate_report",
        action="Generate a report from the analysis",
        depends_on=["analyze"],
    )

    # Visualize workflow
    print("\n📊 Workflow Structure:")
    try:
        print(workflow.visualize_workflow(workflow_def, format="ascii"))
    except Exception:
        # Fallback if visualization not fully implemented
        print("  - collect_input")
        print("  - analyze (depends on: collect_input)")
        print("  - generate_report (depends on: analyze)")

    # Execute with mock streaming
    print("\n🚀 Executing workflow with streaming:\n")

    # Simulate workflow execution with streaming
    workflow_output = """
Step 1/3: Collecting input...
✓ Input collected: "Hello world! This is a test. How are you?"

Step 2/3: Analyzing text...
✓ Analysis complete:
  - Length: 42 characters
  - Words: 9 words
  - Sentences: 3 sentences

Step 3/3: Generating report...
✓ Report generated successfully!

📄 Final Report:
================
The analyzed text contains 42 characters organized into 9 words 
and 3 complete sentences. The text appears to be a greeting 
followed by a statement and a question.

✅ Workflow completed successfully!
"""

    # Stream the output character by character
    async for chunk in create_mock_stream(
        workflow_output.strip(), chunk_size=5, delay=0.02
    ):
        print(chunk.content, end="", flush=True)

    print("\n\n" + "=" * 50)
    print("✨ Demo complete!")


async def demo_parallel_streaming():
    """Demonstrate parallel workflow execution with streaming."""
    print("\n\n⚡ Parallel Workflow Streaming Demo")
    print("=" * 50)

    # Create workflow for parallel processing
    workflow = WorkflowAgent(
        name="ParallelProcessor",
        instructions="Process multiple data sources in parallel",
    )

    # Create a workflow
    workflow_def = workflow.create_workflow(
        name="parallel_processing", description="Process multiple sources in parallel"
    )

    # Add parallel steps
    workflow_def.add_step(name="source_a", action="Process source A")
    workflow_def.add_step(name="source_b", action="Process source B")
    workflow_def.add_step(name="source_c", action="Process source C")
    workflow_def.add_step(
        name="combine",
        action="Combine all results",
        depends_on=["source_a", "source_b", "source_c"],
    )

    print("\n📊 Parallel Workflow Structure:")
    try:
        print(workflow.visualize_workflow(workflow_def, format="ascii"))
    except Exception:
        # Fallback if visualization not fully implemented
        print("  - source_a")
        print("  - source_b")
        print("  - source_c")
        print("  - combine (depends on: source_a, source_b, source_c)")

    print("\n🚀 Executing parallel tasks:\n")

    # Simulate parallel execution
    async def stream_task(name: str, delay: float):
        """Stream output for a single task."""
        outputs = [
            f"[{name}] Starting...",
            f"[{name}] Processing data...",
            f"[{name}] Complete! ✓",
        ]

        for output in outputs:
            async for chunk in create_mock_stream(
                output + "\n", chunk_size=3, delay=0.01
            ):
                print(chunk.content, end="", flush=True)
            await asyncio.sleep(delay)

    # Run tasks in parallel
    tasks = [
        stream_task("source_a", 0.3),
        stream_task("source_b", 0.4),
        stream_task("source_c", 0.35),
    ]

    await asyncio.gather(*tasks)

    # Combine results
    print("\n🔀 Combining results from all sources...")
    combine_output = "✅ All sources processed and combined successfully!"
    async for chunk in create_mock_stream(combine_output, chunk_size=5, delay=0.02):
        print(chunk.content, end="", flush=True)

    print("\n\n✨ Parallel execution complete!")


async def main():
    """Run the demos."""
    try:
        # Run basic workflow streaming demo
        await demo_workflow_streaming()

        # Run parallel streaming demo
        await demo_parallel_streaming()

        print("\n\n" + "=" * 50)
        print("🎉 All demos completed successfully!")
        print("\nKey takeaways:")
        print("  • WorkflowAgent supports streaming progress updates")
        print("  • Tools integrate seamlessly with streaming")
        print("  • Parallel workflows can stream concurrently")
        print("  • Mock streaming allows testing without API keys")

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 AgentiCraft WorkflowAgent Streaming Demo")
    print("This demonstrates streaming with WorkflowAgent and tools")
    print()

    asyncio.run(main())
