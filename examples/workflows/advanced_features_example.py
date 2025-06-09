#!/usr/bin/env python3
"""Advanced workflow features example.

This example demonstrates advanced WorkflowAgent features:
- Visual workflow planning
- Dynamic workflow modification
- Checkpoint/resume capabilities
- Progress streaming
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from agenticraft import tool
from agenticraft.agents.workflow import WorkflowAgent


# Example tools
@tool
async def research_topic(topic: str) -> str:
    """Research a topic."""
    await asyncio.sleep(1)
    return f"Research findings for {topic}: Found 10 relevant sources"


@tool
async def analyze_data(research_result: str) -> dict[str, Any]:
    """Analyze research data."""
    await asyncio.sleep(1.5)
    return {
        "insights": ["Key insight 1", "Key insight 2", "Key insight 3"],
        "confidence": 0.85,
    }


@tool
async def generate_report(analysis_result: dict[str, Any]) -> str:
    """Generate final report."""
    await asyncio.sleep(1)
    insights = analysis_result.get("insights", [])
    return f"Report generated with {len(insights)} key insights"


async def visual_planning_example():
    """Demonstrate visual workflow planning."""
    print("\n🎨 Visual Workflow Planning")
    print("-" * 50)

    # Create workflow agent
    agent = WorkflowAgent(
        name="PlanningAgent",
        instructions="You are an expert at planning and executing workflows.",
    )

    # Plan a workflow visually
    goal = "Create a comprehensive market analysis report for AI tools"
    constraints = {
        "time_limit": "2 hours",
        "resources": ["web_search", "database_access", "llm_analysis"],
        "output_format": "PDF report with charts",
    }

    print(f"Goal: {goal}")
    print(f"Constraints: {json.dumps(constraints, indent=2)}")

    # Create workflow through visual planning
    workflow = await agent.plan_workflow_visually(goal, constraints)

    # Visualize the planned workflow
    print("\nPlanned Workflow:")
    viz = agent.visualize_workflow(workflow, format="ascii")
    print(viz)

    # Save as HTML
    html_viz = agent.visualize_workflow(workflow, format="html")
    with open("planned_workflow.html", "w") as f:
        f.write(html_viz)
    print("\n💾 Visual plan saved to: planned_workflow.html")


async def dynamic_modification_example():
    """Demonstrate dynamic workflow modification."""
    print("\n🔧 Dynamic Workflow Modification")
    print("-" * 50)

    agent = WorkflowAgent(name="DynamicAgent")

    # Create initial workflow
    workflow = agent.create_workflow(
        "research_project", "Research and analysis workflow"
    )

    # Add initial steps
    workflow.add_step("research", "Research the topic", handler="research_handler")
    workflow.add_step("analyze", "Analyze findings", depends_on=["research"])

    print("Initial workflow:")
    print(agent.visualize_workflow(workflow, format="ascii"))

    # Start execution in background
    execution_task = asyncio.create_task(
        agent.execute_workflow(workflow, context={"topic": "AI Ethics"})
    )

    # Wait a bit then modify
    await asyncio.sleep(0.5)

    # Dynamically add new steps
    print("\n🔄 Adding validation step dynamically...")
    agent.modify_workflow_dynamically(
        workflow.id,
        {
            "add_steps": [
                {
                    "name": "validate",
                    "action": "Validate analysis results",
                    "depends_on": ["analyze"],
                }
            ],
            "modify_steps": {"analyze": {"timeout": 5.0}},  # Add timeout
        },
    )

    print("\nModified workflow:")
    print(agent.visualize_workflow(workflow, format="ascii"))

    # Wait for completion
    try:
        result = await execution_task
        print(f"\n✅ Workflow completed: {result.status}")
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")


async def checkpoint_resume_example():
    """Demonstrate checkpoint and resume capabilities."""
    print("\n💾 Checkpoint & Resume Example")
    print("-" * 50)

    agent = WorkflowAgent(name="CheckpointAgent")

    # Register tools
    agent.register_handler("research_handler", research_topic)
    agent.register_handler("analyze_handler", analyze_data)
    agent.register_handler("report_handler", generate_report)

    # Create workflow
    workflow = agent.create_workflow(
        "long_running_analysis", "Long-running analysis that can be checkpointed"
    )

    workflow.add_step("step1_research", handler="research_handler", timeout=2.0)
    workflow.add_step(
        "step2_analyze",
        handler="analyze_handler",
        depends_on=["step1_research"],
        timeout=3.0,
    )
    workflow.add_step(
        "step3_report", handler="report_handler", depends_on=["step2_analyze"]
    )

    print("Workflow created:")
    print(agent.visualize_workflow(workflow, format="ascii"))

    # Start execution
    print("\n🚀 Starting workflow execution...")
    execution_task = asyncio.create_task(
        agent.execute_workflow(workflow, context={"topic": "AI Safety"})
    )

    # Wait for first step to complete
    await asyncio.sleep(1.5)

    # Save checkpoint
    print("\n💾 Saving checkpoint...")
    checkpoint_file = await agent.save_checkpoint(workflow.id)
    print(f"Checkpoint saved to: {checkpoint_file}")

    # Cancel execution (simulate interruption)
    execution_task.cancel()
    try:
        await execution_task
    except asyncio.CancelledError:
        print("⚠️  Workflow execution interrupted!")

    # Show current state
    print("\nWorkflow state at interruption:")
    for step in workflow.steps:
        print(f"  - {step.name}: {step.status}")

    # Load from checkpoint
    print("\n🔄 Loading from checkpoint...")
    loaded_workflow = await agent.load_checkpoint(checkpoint_file)

    # Resume execution
    print("📍 Resuming workflow...")
    result = await agent.resume_workflow(loaded_workflow)

    print("\n✅ Workflow resumed and completed!")
    print(result.format_summary())

    # Clean up checkpoint
    Path(checkpoint_file).unlink()


async def progress_streaming_example():
    """Demonstrate progress streaming."""
    print("\n📊 Progress Streaming Example")
    print("-" * 50)

    agent = WorkflowAgent(name="StreamingAgent")

    # Create workflow with multiple parallel steps
    workflow = agent.create_workflow(
        "parallel_processing", "Workflow with parallel steps to show progress"
    )

    # Add steps that take different amounts of time
    workflow.add_step("quick_task", "Complete quickly", timeout=1.0)
    workflow.add_step("medium_task", "Takes medium time", timeout=2.0)
    workflow.add_step("slow_task", "Takes longer", timeout=3.0)
    workflow.add_step(
        "final_task",
        "Combine all results",
        depends_on=["quick_task", "medium_task", "slow_task"],
    )

    print("Workflow structure:")
    print(agent.visualize_workflow(workflow, format="ascii"))

    # Progress callback
    def progress_callback(update: dict[str, Any]):
        """Print progress updates."""
        if update.get("completed"):
            print(f"\n✅ Workflow completed in {update.get('duration', 0):.1f}s")
        else:
            steps_completed = update.get("steps_completed", 0)
            steps_total = update.get("steps_total", 0)
            current_steps = update.get("current_steps", [])
            print(
                f"\r⏳ Progress: {steps_completed}/{steps_total} steps | "
                f"Running: {', '.join(current_steps) or 'None'}",
                end="",
                flush=True,
            )

    # Start execution
    print("\n🚀 Starting workflow with progress tracking...")

    # Execute workflow in background
    execution_task = asyncio.create_task(
        agent.execute_workflow(workflow, parallel=True)
    )

    # Stream progress with callback
    async def track_progress():
        async for update in agent.stream_workflow_progress(workflow.id):
            progress_callback(update)

    # Run progress tracking
    progress_task = asyncio.create_task(track_progress())

    # Wait for both to complete
    try:
        result = await execution_task
        await progress_task
    except Exception:
        # Progress task might fail if workflow completes first
        pass

    # Show final visualization with progress
    print("\n\nFinal workflow state:")
    viz = agent.visualize_workflow(workflow, format="mermaid", include_progress=True)
    print(viz)


async def main():
    """Run all enhanced WorkflowAgent examples."""
    print("🚀 Enhanced WorkflowAgent Examples")
    print("=" * 60)

    try:
        # Run examples
        await visual_planning_example()
        await dynamic_modification_example()
        await checkpoint_resume_example()
        await progress_streaming_example()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error in examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Import required for type hints
    # from typing import Dict, Any

    asyncio.run(main())
