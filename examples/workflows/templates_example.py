#!/usr/bin/env python3
"""Workflow templates example.

This example demonstrates pre-built workflow templates:
- Research workflows
- Content pipelines
- Data processing
- Multi-agent collaboration
"""

import asyncio
from typing import Any

from agenticraft import tool
from agenticraft.workflows import visualize_workflow
from agenticraft.workflows.templates import WorkflowTemplates


# Mock tools for demonstration
@tool
async def define_research_scope(**kwargs) -> dict[str, Any]:
    """Define research scope and questions."""
    await asyncio.sleep(0.5)
    topic = kwargs.get("topic", "Unknown Topic")
    sources = kwargs.get("sources", ["academic", "industry", "news"])
    return {
        "scope": f"Comprehensive analysis of {topic}",
        "questions": [
            f"What are the key aspects of {topic}?",
            f"What are current trends in {topic}?",
            "What are future implications?",
        ],
        "sources_to_search": sources,
    }


@tool
async def search_source(**kwargs) -> dict[str, Any]:
    """Search a specific source."""
    await asyncio.sleep(1)
    source = kwargs.get("source", "unknown")
    define_scope = kwargs.get("define_scope", {})
    return {
        "source": source,
        "findings": [
            f"Finding 1 from {source}",
            f"Finding 2 from {source}",
            f"Finding 3 from {source}",
        ],
        "relevance": 0.85,
    }


@tool
async def analyze_findings(**kwargs) -> dict[str, Any]:
    """Analyze research findings."""
    await asyncio.sleep(0.8)
    all_findings = []
    # Look for search results in kwargs
    for key, value in kwargs.items():
        if (
            key.startswith("search_")
            and isinstance(value, dict)
            and "findings" in value
        ):
            all_findings.extend(value["findings"])

    return {
        "total_findings": len(all_findings),
        "key_insights": [
            "Primary insight from analysis",
            "Secondary insight from analysis",
            "Tertiary insight from analysis",
        ],
        "confidence": 0.9,
    }


@tool
async def generate_output(**kwargs) -> str:
    """Generate final output."""
    await asyncio.sleep(0.5)
    format = kwargs.get("format", "report")
    analyze_findings = kwargs.get("analyze_findings", {})
    insights = (
        analyze_findings.get("key_insights", [])
        if isinstance(analyze_findings, dict)
        else []
    )

    if format == "report":
        return "# Research Report\n\n## Key Insights\n" + "\n".join(
            f"- {i}" for i in insights
        )
    elif format == "summary":
        return f"Executive Summary: Found {len(insights)} key insights"
    else:
        return f"Output generated with {len(insights)} insights"


@tool
async def quality_check(**kwargs) -> dict[str, Any]:
    """Check quality of output."""
    await asyncio.sleep(0.3)
    generate_output = kwargs.get("generate_output", "")
    has_output = bool(generate_output)
    return {
        "quality_score": 0.92 if has_output else 0.0,
        "issues": [] if has_output else ["No output generated"],
        "approved": has_output,
    }


async def research_workflow_example():
    """Demonstrate research workflow template."""
    print("\n📚 Research Workflow Template")
    print("-" * 50)

    # Create research workflow
    template = WorkflowTemplates.research_workflow(
        topic="Quantum Computing Applications",
        sources=["academic", "industry", "news"],
        output_format="report",
    )

    workflow = template["workflow"]

    # Assign tools to steps
    workflow._steps["define_scope"].tool = define_research_scope
    workflow._steps["search_academic"].tool = search_source
    workflow._steps["search_industry"].tool = search_source
    workflow._steps["search_news"].tool = search_source
    workflow._steps["analyze_findings"].tool = analyze_findings
    workflow._steps["generate_output"].tool = generate_output
    workflow._steps["quality_check"].tool = quality_check

    print("Template Configuration:")
    print(f"  Type: {template['template_type']}")
    print(f"  Topic: {template['configuration']['topic']}")
    print(f"  Sources: {template['configuration']['sources']}")
    print(f"  Output: {template['configuration']['output_format']}")

    print("\nWorkflow Structure:")
    print(visualize_workflow(workflow, format="ascii"))

    print("\nExecuting research workflow...")
    result = await workflow.run(topic="Quantum Computing Applications")

    print("\n✅ Research Results:")
    for step_name, step_result in result.steps.items():
        if step_result.success:
            print(f"  - {step_name}: ✓ Completed")
        else:
            print(f"  - {step_name}: ✗ Failed - {step_result.error}")

    # Show final output if available
    if "generate_output" in result.steps and result.steps["generate_output"].success:
        final_output = result.steps["generate_output"].output
        print("\nFinal Output Preview:")
        print(final_output[:200] + "..." if len(final_output) > 200 else final_output)
    else:
        print("\n⚠️  Workflow did not complete all steps")


async def content_pipeline_example():
    """Demonstrate content pipeline template."""
    print("\n✍️ Content Pipeline Template")
    print("-" * 50)

    # Create blog content pipeline
    template = WorkflowTemplates.content_pipeline(
        content_type="blog", review_required=True
    )

    workflow = template["workflow"]

    print("Template Configuration:")
    print(f"  Type: {template['template_type']}")
    print(f"  Content Type: {template['configuration']['content_type']}")
    print(f"  Review Required: {template['configuration']['review_required']}")

    print("\nPipeline Stages:")
    for step in workflow._steps.values():
        deps = f" (depends on: {', '.join(step.depends_on)})" if step.depends_on else ""
        print(f"  - {step.name}{deps}")

    # Visualize
    print("\nWorkflow Visualization:")
    viz = visualize_workflow(workflow, format="mermaid")
    print(viz)


async def data_processing_example():
    """Demonstrate data processing template."""
    print("\n🔄 Data Processing Pipeline Template")
    print("-" * 50)

    # Create ETL pipeline
    template = WorkflowTemplates.data_processing_pipeline(
        input_format="csv",
        processing_steps=["clean", "transform", "enrich"],
        output_format="json",
        validation_required=True,
    )

    workflow = template["workflow"]

    print("Pipeline Configuration:")
    print(f"  Input: {template['configuration']['input_format']}")
    print(f"  Output: {template['configuration']['output_format']}")
    print(f"  Steps: {template['configuration']['processing_steps']}")
    print(f"  Validation: {template['configuration']['validation_required']}")

    print("\nWorkflow Structure:")
    print(visualize_workflow(workflow, format="ascii"))


async def multi_agent_example():
    """Demonstrate multi-agent collaboration template."""
    print("\n👥 Multi-Agent Collaboration Template")
    print("-" * 50)

    # Define agents
    agents = [
        {"name": "researcher", "role": "Gather and analyze information"},
        {"name": "writer", "role": "Create compelling content"},
        {"name": "editor", "role": "Review and refine output"},
        {"name": "publisher", "role": "Format and publish content"},
    ]

    # Create collaboration workflow
    template = WorkflowTemplates.multi_agent_collaboration(
        agents=agents, coordination_style="sequential", consensus_required=True
    )

    workflow = template["workflow"]
    agent = template["workflow_agent"]

    print("Collaboration Setup:")
    print(f"  Agents: {len(agents)}")
    print(f"  Style: {template['configuration']['coordination_style']}")
    print(f"  Consensus: {template['configuration']['consensus_required']}")

    print("\nAgent Roles:")
    for agent_def in agents:
        print(f"  - {agent_def['name']}: {agent_def['role']}")

    print("\nWorkflow Structure:")
    print(agent.visualize_workflow(workflow, format="ascii"))

    # Try different coordination styles
    print("\n🔄 Alternative: Parallel Coordination")
    parallel_template = WorkflowTemplates.multi_agent_collaboration(
        agents=agents[:3],  # Use fewer agents for clarity
        coordination_style="parallel",
        consensus_required=False,
    )

    parallel_workflow = parallel_template["workflow"]
    parallel_agent = parallel_template["workflow_agent"]

    print("\nParallel Workflow:")
    print(parallel_agent.visualize_workflow(parallel_workflow, format="ascii"))

    print("\n🔄 Alternative: Hierarchical Coordination")
    hierarchical_template = WorkflowTemplates.multi_agent_collaboration(
        agents=agents, coordination_style="hierarchical", consensus_required=False
    )

    hierarchical_workflow = hierarchical_template["workflow"]
    hierarchical_agent = hierarchical_template["workflow_agent"]

    print("\nHierarchical Workflow:")
    print(hierarchical_agent.visualize_workflow(hierarchical_workflow, format="ascii"))


async def iterative_refinement_example():
    """Demonstrate iterative refinement template."""
    print("\n🔁 Iterative Refinement Template")
    print("-" * 50)

    # Create refinement workflow
    template = WorkflowTemplates.iterative_refinement(
        task="Write a technical whitepaper",
        max_iterations=3,
        quality_threshold=0.85,
        reviewers=["technical_expert", "domain_expert", "editor"],
    )

    workflow = template["workflow"]
    agent = template["workflow_agent"]

    print("Refinement Configuration:")
    print(f"  Task: {template['configuration']['task']}")
    print(f"  Max Iterations: {template['configuration']['max_iterations']}")
    print(f"  Quality Threshold: {template['configuration']['quality_threshold']}")
    print(f"  Reviewers: {template['configuration']['reviewers']}")

    print("\nWorkflow Structure:")
    # The workflow is quite complex, so let's show a simplified view
    print("Steps in refinement cycle:")
    for step in workflow.steps[:10]:  # Show first 10 steps
        deps = f" <- {', '.join(step.depends_on)}" if step.depends_on else ""
        condition = f" [if {step.condition}]" if step.condition else ""
        print(f"  - {step.name}{deps}{condition}")
    print("  ... (additional steps for remaining iterations)")

    # Save full visualization
    html_content = agent.visualize_workflow(workflow, format="html")
    with open("iterative_refinement.html", "w") as f:
        f.write(html_content)
    print("\n💾 Full visualization saved to: iterative_refinement.html")


async def main():
    """Run workflow template examples."""
    print("📋 AgentiCraft Workflow Templates")
    print("=" * 60)

    try:
        # Demonstrate each template type
        await research_workflow_example()
        await content_pipeline_example()
        await data_processing_example()
        await multi_agent_example()
        await iterative_refinement_example()

        print("\n✅ All workflow templates demonstrated!")
        print("\n💡 Tips:")
        print("  - Templates provide starting points for common workflows")
        print("  - Customize by assigning your own tools/agents to steps")
        print("  - Modify step dependencies and add new steps as needed")
        print("  - Use visualizations to understand workflow structure")

    except Exception as e:
        print(f"\n❌ Error in examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
