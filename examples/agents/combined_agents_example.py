"""Example: Combining ReasoningAgent and WorkflowAgent.

This example shows how ReasoningAgent and WorkflowAgent can work together
to create sophisticated AI applications.
"""

import asyncio

from agenticraft import ReasoningAgent, WorkflowAgent


async def research_workflow_example():
    """Example: Research workflow with reasoning transparency."""
    print("=== Research Workflow with Transparent Reasoning ===\n")

    # Create our agents
    reasoning_agent = ReasoningAgent(
        name="Researcher",
        instructions="You are a thorough researcher who explains your thinking clearly.",
    )

    workflow_agent = WorkflowAgent(
        name="WorkflowOrchestrator",
        instructions="You orchestrate research workflows efficiently.",
    )

    # Create the research workflow
    workflow = workflow_agent.create_workflow(
        name="research_workflow",
        description="Comprehensive research process with reasoning transparency",
    )

    # Define custom handlers that use the reasoning agent
    async def analyze_topic(agent, step, context):
        """Use ReasoningAgent to analyze the topic."""
        topic = context.get("research_topic", "Unknown topic")

        # Use reasoning agent for transparent analysis
        response = await reasoning_agent.think_and_act(
            f"Analyze this research topic and identify key areas to investigate: {topic}"
        )

        # Store both the analysis and reasoning
        context["topic_analysis"] = response.content
        context["analysis_reasoning"] = response.format_reasoning()

        return f"Topic analyzed with {response.step_count} reasoning steps"

    async def research_perspectives(agent, step, context):
        """Research from multiple perspectives."""
        topic = context.get("research_topic", "Unknown topic")

        # Use reasoning agent for multi-perspective analysis
        analysis = await reasoning_agent.analyze(
            f"Research this topic from multiple perspectives: {topic}",
            perspectives=["scientific", "practical", "ethical", "future implications"],
        )

        context["perspectives"] = analysis.perspectives
        context["synthesis"] = analysis.synthesis

        return "Multi-perspective research completed"

    # Register handlers
    workflow_agent.register_handler("analyze_topic", analyze_topic)
    workflow_agent.register_handler("research_perspectives", research_perspectives)

    # Build the workflow
    workflow.add_step(
        name="define_scope",
        action="Define the scope and objectives of researching artificial general intelligence (AGI)",
    )

    workflow.add_step(
        name="analyze_topic", handler="analyze_topic", depends_on=["define_scope"]
    )

    workflow.add_step(
        name="research_perspectives",
        handler="research_perspectives",
        depends_on=["analyze_topic"],
    )

    workflow.add_step(
        name="synthesize_findings",
        action="Synthesize all findings into a coherent research summary",
        depends_on=["research_perspectives"],
    )

    workflow.add_step(
        name="create_recommendations",
        action="Create actionable recommendations based on the research",
        depends_on=["synthesize_findings"],
    )

    # Execute the workflow
    print("Starting research workflow on AGI...")
    print("-" * 60)

    context = {"research_topic": "Artificial General Intelligence (AGI)"}
    result = await workflow_agent.execute_workflow(workflow, context=context)

    # Display results
    print("\n✅ WORKFLOW COMPLETED!")
    print(result.format_summary())

    # Show the reasoning transparency
    print("\n\n📊 REASONING TRANSPARENCY")
    print("=" * 60)

    if "analysis_reasoning" in result.context:
        print("\nTopic Analysis Reasoning:")
        print("-" * 40)
        print(result.context["analysis_reasoning"])

    if "perspectives" in result.context:
        print("\n\nMulti-Perspective Insights:")
        print("-" * 40)
        for perspective, content in result.context["perspectives"].items():
            print(f"\n{perspective.upper()}:")
            print(content[:300] + "..." if len(content) > 300 else content)

    # Show final recommendations
    recommendations = result.get_step_result("create_recommendations")
    if recommendations:
        print("\n\n💡 FINAL RECOMMENDATIONS")
        print("=" * 60)
        print(recommendations)


async def decision_making_example():
    """Example: Decision-making with reasoning and workflow."""
    print("\n\n=== Decision-Making Process ===\n")

    # Create specialized agents
    analyst = ReasoningAgent(
        name="DecisionAnalyst",
        instructions="You analyze decisions thoroughly and explain trade-offs clearly.",
    )

    orchestrator = WorkflowAgent(
        name="DecisionOrchestrator",
        instructions="You guide decision-making processes systematically.",
    )

    # Quick decision workflow
    workflow = orchestrator.create_workflow("decision_process")

    # Decision scenario
    decision = "Should a startup pivot from B2C to B2B SaaS model?"

    # Define workflow steps
    workflow.add_step(
        name="identify_factors",
        action=f"Identify key factors to consider for this decision: {decision}",
    )

    workflow.add_step(
        name="analyze_options",
        action="Analyze the pros and cons of staying B2C vs pivoting to B2B",
        depends_on=["identify_factors"],
    )

    workflow.add_step(
        name="risk_assessment",
        action="Assess the risks associated with each option",
        depends_on=["analyze_options"],
    )

    workflow.add_step(
        name="recommendation",
        action="Make a recommendation with clear reasoning",
        depends_on=["risk_assessment"],
    )

    # Execute workflow
    print(f"Decision to analyze: {decision}")
    print("-" * 60)

    result = await orchestrator.execute_workflow(workflow)

    # Get the analyst's perspective
    print("\n\n🤔 ANALYST'S DETAILED REASONING")
    print("=" * 60)

    analysis = await analyst.analyze(
        f"Analyze this business decision: {decision}",
        perspectives=["financial", "market", "operational", "strategic"],
    )

    print(analysis.format_analysis())

    # Combine workflow results with reasoning
    print("\n\n📋 DECISION SUMMARY")
    print("=" * 60)

    recommendation = result.get_step_result("recommendation")
    if recommendation:
        print("Workflow Recommendation:")
        print(recommendation)

    print(f"\n\nReasoning Transparency: {len(analysis.reasoning_steps)} detailed steps")
    print(f"Perspectives Analyzed: {len(analysis.perspectives)}")
    print(
        f"Workflow Steps Completed: {len([r for r in result.step_results.values() if r.status == 'completed'])}"
    )


async def main():
    """Run the combined examples."""
    print("Advanced Agents Working Together")
    print("=" * 60)
    print("\nThis example demonstrates how ReasoningAgent and WorkflowAgent")
    print("can be combined to create sophisticated AI applications with both")
    print("structured workflows and transparent reasoning.\n")

    await research_workflow_example()
    await decision_making_example()

    print("\n\n" + "=" * 60)
    print("✅ Examples completed!")
    print("\nKey Takeaways:")
    print("- ReasoningAgent provides transparency and explainability")
    print("- WorkflowAgent provides structure and orchestration")
    print("- Together they enable sophisticated, trustworthy AI applications")
    print("- Both agents inherit all base Agent capabilities (tools, providers, etc.)")


if __name__ == "__main__":
    # Note: Requires API keys to be set
    import os

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key'")
    else:
        asyncio.run(main())
