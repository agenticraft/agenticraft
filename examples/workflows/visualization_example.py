#!/usr/bin/env python3
"""Basic workflow visualization example.

This example demonstrates:
- Creating workflows
- Visualizing in different formats (Mermaid, ASCII, JSON, HTML)
- Showing execution progress
"""

import asyncio

from agenticraft import tool
from agenticraft.core.workflow import Step, Workflow
from agenticraft.workflows import save_workflow_visualization, visualize_workflow


# Create dummy tools for visualization
@tool
def load_data_tool(source: str) -> str:
    """Load data from source."""
    return f"Loaded data from {source}"


@tool
def process_tool(data: str = "") -> str:
    """Generic processing tool."""
    return "Processed data"


async def main():
    """Run workflow visualization examples."""
    print("🎨 AgentiCraft Workflow Visualization Example")
    print("=" * 50)

    # Create a sample workflow
    workflow = Workflow(
        name="data_analysis_pipeline",
        description="Analyze customer data and generate insights",
    )

    # Add workflow steps
    workflow.add_step(
        Step(
            name="load_data",
            tool=load_data_tool,
            inputs={"source": "customer_database"},
        )
    )

    workflow.add_step(
        Step(name="clean_data", tool=process_tool, depends_on=["load_data"])
    )

    # Parallel analysis steps
    workflow.add_step(
        Step(name="analyze_demographics", tool=process_tool, depends_on=["clean_data"])
    )

    workflow.add_step(
        Step(name="analyze_behavior", tool=process_tool, depends_on=["clean_data"])
    )

    workflow.add_step(
        Step(name="analyze_sentiment", tool=process_tool, depends_on=["clean_data"])
    )

    # Merge results
    workflow.add_step(
        Step(
            name="merge_insights",
            tool=process_tool,
            depends_on=[
                "analyze_demographics",
                "analyze_behavior",
                "analyze_sentiment",
            ],
        )
    )

    workflow.add_step(
        Step(name="generate_report", tool=process_tool, depends_on=["merge_insights"])
    )

    # 1. Mermaid Visualization
    print("\n📊 Mermaid Diagram:")
    print("-" * 40)
    mermaid = visualize_workflow(workflow, format="mermaid")
    print(mermaid)

    # 2. ASCII Visualization
    print("\n📝 ASCII Visualization:")
    print("-" * 40)
    ascii_viz = visualize_workflow(workflow, format="ascii")
    print(ascii_viz)

    # 3. JSON Export
    print("\n📄 JSON Export (truncated):")
    print("-" * 40)
    json_export = visualize_workflow(workflow, format="json")
    print(json_export[:500] + "..." if len(json_export) > 500 else json_export)

    # 4. Save HTML Visualization
    html_file = "workflow_visualization.html"
    save_workflow_visualization(workflow, html_file, format="html")
    print(f"\n💾 HTML visualization saved to: {html_file}")

    # 5. Simulate execution for progress visualization
    print("\n🚀 Simulating workflow execution with progress...")
    print("-" * 40)

    # Create mock execution result
    from datetime import datetime, timedelta

    from agenticraft.core.workflow import StepResult, WorkflowResult

    # Simulate some completed steps
    mock_result = WorkflowResult(
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        success=True,
        steps={
            "load_data": StepResult(
                step_name="load_data",
                success=True,
                output="Data loaded: 10,000 records",
                started_at=datetime.now() - timedelta(seconds=30),
                completed_at=datetime.now() - timedelta(seconds=25),
            ),
            "clean_data": StepResult(
                step_name="clean_data",
                success=True,
                output="Data cleaned: 9,500 valid records",
                started_at=datetime.now() - timedelta(seconds=25),
                completed_at=datetime.now() - timedelta(seconds=20),
            ),
            "analyze_demographics": StepResult(
                step_name="analyze_demographics",
                success=True,
                output="Demographics analyzed",
                started_at=datetime.now() - timedelta(seconds=20),
                completed_at=datetime.now() - timedelta(seconds=15),
            ),
            "analyze_behavior": StepResult(
                step_name="analyze_behavior",
                success=False,
                output=None,
                error="Timeout analyzing behavior patterns",
                started_at=datetime.now() - timedelta(seconds=20),
                completed_at=datetime.now() - timedelta(seconds=10),
            ),
            "analyze_sentiment": StepResult(
                step_name="analyze_sentiment",
                success=True,
                output="Sentiment: 78% positive",
                started_at=datetime.now() - timedelta(seconds=20),
                completed_at=datetime.now() - timedelta(seconds=12),
            ),
        },
        started_at=datetime.now() - timedelta(seconds=30),
        completed_at=datetime.now(),
    )

    # Visualize with progress
    print("\nMermaid with Progress:")
    mermaid_progress = visualize_workflow(
        workflow, format="mermaid", include_progress=True, result=mock_result
    )
    print(mermaid_progress)

    print("\nASCII with Progress:")
    ascii_progress = visualize_workflow(
        workflow, format="ascii", include_progress=True, result=mock_result
    )
    print(ascii_progress)

    # Save progress visualization
    progress_html = "workflow_progress.html"
    save_workflow_visualization(
        workflow,
        progress_html,
        format="html",
        include_progress=True,
        result=mock_result,
    )
    print(f"\n💾 Progress visualization saved to: {progress_html}")

    print("\n✅ Visualization examples complete!")
    print("\nTip: Open the HTML files in a browser to see interactive diagrams!")


if __name__ == "__main__":
    asyncio.run(main())
