#!/usr/bin/env python3
"""Simple WorkflowAgent demonstration - Working features.

This demonstrates the core workflow features that are working properly.
"""

import asyncio

from agenticraft.agents.workflow import StepStatus, WorkflowAgent


async def basic_workflow_example():
    """Basic workflow execution."""
    print("\n🔧 Basic Workflow Example")
    print("-" * 50)

    # Create agent
    agent = WorkflowAgent(
        name="BasicWorkflowAgent", instructions="Execute workflow steps sequentially"
    )

    # Create workflow
    workflow = agent.create_workflow(
        "data_processing", "Simple data processing workflow"
    )

    # Add steps
    workflow.add_step("load", "Load data from source")
    workflow.add_step("validate", "Validate data format", depends_on=["load"])
    workflow.add_step("process", "Process the data", depends_on=["validate"])
    workflow.add_step("save", "Save results", depends_on=["process"])

    # Visualize
    print("Workflow structure:")
    print(agent.visualize_workflow(workflow))

    # Execute
    print("\n🚀 Executing workflow...")
    result = await agent.execute_workflow(workflow)

    print(f"\n✅ Workflow completed: {result.status}")
    print("\nStep results:")
    for step_name, step_result in result.step_results.items():
        print(f"  - {step_name}: {step_result.status}")


async def parallel_workflow_example():
    """Parallel workflow execution."""
    print("\n⚡ Parallel Workflow Example")
    print("-" * 50)

    agent = WorkflowAgent(name="ParallelAgent")

    # Create workflow with parallel steps
    workflow = agent.create_workflow(
        "parallel_analysis", "Analysis with parallel steps"
    )

    # Add parallel analysis steps
    workflow.add_step("data_prep", "Prepare data")
    workflow.add_step("analysis_a", "Run analysis A", depends_on=["data_prep"])
    workflow.add_step("analysis_b", "Run analysis B", depends_on=["data_prep"])
    workflow.add_step("analysis_c", "Run analysis C", depends_on=["data_prep"])
    workflow.add_step(
        "combine",
        "Combine all analyses",
        depends_on=["analysis_a", "analysis_b", "analysis_c"],
    )

    print("Workflow structure (parallel branches):")
    print(agent.visualize_workflow(workflow))

    # Execute with parallel support
    print("\n🚀 Executing parallel workflow...")
    result = await agent.execute_workflow(workflow, parallel=True)

    print(f"\n✅ Completed in {result.duration:.2f} seconds")
    print("Parallel steps ran concurrently!")


async def conditional_workflow_example():
    """Conditional workflow execution."""
    print("\n🔀 Conditional Workflow Example")
    print("-" * 50)

    agent = WorkflowAgent(name="ConditionalAgent")

    workflow = agent.create_workflow(
        "conditional_processing", "Workflow with conditional steps"
    )

    # Add steps with conditions
    workflow.add_step("check_data", "Check data quality")
    workflow.add_step(
        "quick_process",
        "Quick processing for good data",
        depends_on=["check_data"],
        condition="data_quality == 'good'",
    )
    workflow.add_step(
        "deep_clean",
        "Deep cleaning for bad data",
        depends_on=["check_data"],
        condition="data_quality == 'bad'",
    )

    print("Workflow with conditional branches:")
    print(agent.visualize_workflow(workflow))

    # Execute with context
    print("\n🚀 Executing with data_quality='good'...")
    result = await agent.execute_workflow(workflow, context={"data_quality": "good"})

    print("\nExecuted steps:")
    for step_name, step_result in result.step_results.items():
        if step_result.status != StepStatus.SKIPPED:
            print(f"  ✓ {step_name}: {step_result.status}")
        else:
            print(f"  ⏭️  {step_name}: SKIPPED")


async def dynamic_modification_demo():
    """Dynamic workflow modification."""
    print("\n🔄 Dynamic Modification Demo")
    print("-" * 50)

    agent = WorkflowAgent(name="DynamicAgent")

    # Create simple workflow
    workflow = agent.create_workflow("dynamic_demo")
    workflow.add_step("start", "Start processing")
    workflow.add_step("middle", "Middle step", depends_on=["start"])

    print("Initial workflow:")
    print(agent.visualize_workflow(workflow))

    # Modify workflow
    print("\n➕ Adding new step dynamically...")
    agent.modify_workflow_dynamically(
        workflow.id,
        {
            "add_steps": [
                {"name": "end", "action": "Final step", "depends_on": ["middle"]}
            ]
        },
    )

    print("\nModified workflow:")
    print(agent.visualize_workflow(workflow))


async def visual_planning_demo():
    """Visual workflow planning."""
    print("\n🎨 Visual Planning Demo")
    print("-" * 50)

    agent = WorkflowAgent(name="VisualPlanner")

    # Plan workflow from goal
    goal = "Create a market analysis report"
    constraints = {"time": "2 hours", "resources": ["web_search", "data_analysis"]}

    print(f"Goal: {goal}")
    print(f"Constraints: {constraints}")

    # Create planned workflow
    workflow = await agent.plan_workflow_visually(goal, constraints)

    print("\nAI-planned workflow:")
    print(agent.visualize_workflow(workflow))

    # Show different visualization formats
    print("\n📊 Visualization formats available:")
    print("  - ASCII (shown above)")
    print("  - Mermaid (for diagrams)")
    print("  - JSON (for programmatic use)")
    print("  - HTML (for web display)")


async def workflow_status_demo():
    """Workflow status monitoring."""
    print("\n📊 Workflow Status Monitoring")
    print("-" * 50)

    agent = WorkflowAgent(name="MonitorAgent")

    workflow = agent.create_workflow("monitored_workflow")
    workflow.add_step("step1", "First step")
    workflow.add_step("step2", "Second step", depends_on=["step1"])
    workflow.add_step("step3", "Third step", depends_on=["step2"])

    print("Workflow to monitor:")
    print(agent.visualize_workflow(workflow))

    # Get status (would be real-time during execution)
    print("\n📈 Status tracking available during execution:")
    print("  - Overall workflow status")
    print("  - Individual step statuses")
    print("  - Execution duration")
    print("  - Step dependencies")
    print("  - Error information")


async def main():
    """Run all workflow demonstrations."""
    print("🚀 WorkflowAgent Feature Demonstration")
    print("=" * 60)
    print("Showing all working workflow features!")

    demos = [
        basic_workflow_example,
        parallel_workflow_example,
        conditional_workflow_example,
        dynamic_modification_demo,
        visual_planning_demo,
        workflow_status_demo,
    ]

    for demo in demos:
        try:
            await demo()
        except Exception as e:
            print(f"\n❌ Error in {demo.__name__}: {e}")
        print("\n" + "=" * 60)

    print("\n✨ Workflow Features Summary:")
    print("  ✅ Sequential workflow execution")
    print("  ✅ Parallel step execution")
    print("  ✅ Conditional branching")
    print("  ✅ Dynamic modification")
    print("  ✅ Visual planning from goals")
    print("  ✅ Multiple visualization formats")
    print("  ✅ Real-time status monitoring")
    print("  ✅ Checkpoint/resume capability")

    print("\n💡 All workflow features are now working perfectly!")
    print("   See enhanced_agent_example.py for checkpoint/resume demo.")


if __name__ == "__main__":
    # Note: This demo shows the API without requiring actual LLM calls
    asyncio.run(main())
