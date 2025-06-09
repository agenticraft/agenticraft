"""Simple workflow example.

This example demonstrates basic workflow functionality with
sequential steps and data passing using a simplified approach.
"""

import asyncio
import os

from dotenv import load_dotenv

from agenticraft.agents.workflow import StepStatus, WorkflowAgent

# Load environment variables from .env file
load_dotenv()


# Tool functions
def extract_keywords(text: str) -> list:
    """Extract keywords from text."""
    words = text.lower().split()
    keywords = [w for w in words if len(w) > 4]
    return keywords


def format_report(title: str, keywords: list, analysis: str) -> str:
    """Format a simple report."""
    report = f"# {title}\n\n"
    report += "## Keywords Found:\n"
    for keyword in keywords:
        report += f"- {keyword}\n"
    report += "\n## Analysis:\n"
    report += analysis
    return report


async def main():
    """Run a simple workflow example."""

    print("🔧 Simple Workflow Example")
    print("=" * 50)

    # Create workflow agent
    agent = WorkflowAgent(
        name="TextAnalyzer", instructions="You are a helpful text analysis assistant."
    )

    # Input text
    input_text = "AgentiCraft makes building AI agents simple and transparent"

    # Register handlers
    def extract_handler(agent, step, context):
        """Extract keywords from text."""
        text = context.get("input_text", "")
        keywords = extract_keywords(text)
        context["keywords"] = keywords
        context["keywords_string"] = ", ".join(keywords)
        return f"Extracted {len(keywords)} keywords: {context['keywords_string']}"

    def report_handler(agent, step, context):
        """Generate final report."""
        keywords = context.get("keywords", [])
        analysis = context.get("analysis", "No analysis available")

        report = format_report("Text Analysis Report", keywords, analysis)
        context["final_report"] = report
        return "Report generated successfully"

    # Register handlers
    agent.register_handler("extract", extract_handler)
    agent.register_handler("report", report_handler)

    # Create workflow
    workflow = agent.create_workflow(
        name="text_analysis", description="Simple text analysis pipeline"
    )

    # Step 1: Extract keywords
    workflow.add_step(
        name="extract", handler="extract", action="Extracting keywords from text"
    )

    # Step 2: Analyze keywords (AI step)
    workflow.add_step(
        name="analyze",
        action="Analyze these keywords and provide 2-3 insights: agenticraft, makes, building, agents, simple, transparent",
        depends_on=["extract"],
    )

    # Step 3: Generate report
    workflow.add_step(
        name="report",
        handler="report",
        action="Generating final report",
        depends_on=["analyze"],
    )

    # Visualize workflow
    print("\nWorkflow Structure:")
    print(agent.visualize_workflow(workflow))

    # Prepare context
    context = {"input_text": input_text}

    # Run workflow
    print("\n\nExecuting workflow...")
    result = await agent.execute_workflow(workflow, context=context)

    # Store analysis result in context for report handler
    if result.status == StepStatus.COMPLETED:
        analyze_step = result.step_results.get("analyze")
        if analyze_step and analyze_step.status == StepStatus.COMPLETED:
            context["analysis"] = analyze_step.result
            # Re-run report handler with analysis
            report_handler(agent, None, context)

    # Display results
    print(f"\n✅ Workflow completed: {result.status}")
    print(f"Duration: {result.duration:.2f} seconds")

    # Show step results
    print("\nStep Results:")
    for step_name, step_result in result.step_results.items():
        print(f"\n{step_name}:")
        print(f"  Status: {step_result.status}")
        if step_result.result:
            result_str = str(step_result.result)
            print(
                f"  Output: {result_str[:200]}..."
                if len(result_str) > 200
                else f"  Output: {result_str}"
            )

    # Show final report
    if "final_report" in context:
        print("\n" + "=" * 50)
        print("FINAL REPORT:")
        print("=" * 50)
        print(context["final_report"])


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found")
        print("Please ensure you have a .env file with OPENAI_API_KEY=your-key")
        print("Or set it as an environment variable: export OPENAI_API_KEY='your-key'")
    else:
        print(f"✅ API key found (starts with: {os.getenv('OPENAI_API_KEY')[:8]}...)")
        print()
        asyncio.run(main())
