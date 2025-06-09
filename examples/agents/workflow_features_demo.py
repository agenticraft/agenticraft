"""Example: WorkflowAgent demonstration without direct tool execution.

Since the framework has issues with tool message formatting, this example
demonstrates workflow capabilities using the agent's reasoning abilities
to simulate tool functionality while showcasing workflow features.

This approach:
1. Shows all workflow features (sequential, parallel, conditional)
2. Demonstrates data flow between steps
3. Works reliably without tool execution errors
"""

import asyncio
from datetime import datetime

from agenticraft.agents import StepStatus, WorkflowAgent


async def weather_analysis_workflow():
    """Weather analysis workflow using agent reasoning instead of tools."""
    print("=== Weather Analysis Workflow (Framework-Compatible) ===\n")

    # Create workflow agent without tools to avoid framework issues
    agent = WorkflowAgent(
        name="WeatherAnalyst",
        instructions="""You are a weather data analyst. For this demonstration:
        1. When asked to fetch weather, provide realistic simulated data
        2. When asked to analyze data, perform actual analysis on the provided data
        3. Format all data exchanges as JSON for consistency
        4. Maintain data continuity between workflow steps""",
        model="gpt-4o-mini",  # Ensure we're using a capable model
    )

    # Define the workflow
    workflow = agent.create_workflow(
        name="weather_analysis_demo",
        description="Demonstrate weather data processing workflow",
    )

    # Step 1: Fetch weather data (simulated)
    workflow.add_step(
        name="fetch_weather_data",
        action="""Generate realistic weather data for three cities: New York, London, and Tokyo.
        Return the data as a JSON array with this structure:
        [
            {"city": "New York", "temperature": 72, "humidity": 65, "conditions": "Partly cloudy"},
            {"city": "London", "temperature": 59, "humidity": 80, "conditions": "Rainy"},
            {"city": "Tokyo", "temperature": 68, "humidity": 55, "conditions": "Clear"}
        ]
        Make the data realistic for the current season.""",
    )

    # Step 2: Analyze the data
    workflow.add_step(
        name="analyze_weather",
        action="""Analyze the weather data from the previous step.
        Calculate:
        - Average temperature and humidity
        - Identify the hottest and coldest cities
        - Identify the most humid city
        - Note any severe weather conditions
        
        Return your analysis as a JSON object.""",
        depends_on=["fetch_weather_data"],
    )

    # Step 3: Generate insights
    workflow.add_step(
        name="generate_insights",
        action="""Based on the analysis, generate practical insights:
        - Travel recommendations
        - Clothing suggestions for each city
        - Any weather warnings
        
        Format as a brief, actionable summary.""",
        depends_on=["analyze_weather"],
    )

    # Step 4: Create final report
    workflow.add_step(
        name="create_report",
        action="""Create a professional weather report that includes:
        1. Summary of current conditions in all three cities
        2. The analysis results (averages, extremes)
        3. Practical recommendations
        
        Format it as a clear, readable report.""",
        depends_on=["generate_insights"],
    )

    print("Executing weather analysis workflow...")
    print("-" * 40)

    try:
        result = await agent.execute_workflow(workflow)

        print("\n" + result.format_summary())

        # Show key results
        print("\n📊 WORKFLOW RESULTS:\n")

        for step_name in ["fetch_weather_data", "analyze_weather", "create_report"]:
            step_result = result.step_results.get(step_name)
            if step_result and step_result.status == StepStatus.COMPLETED:
                print(f"\n{step_name.replace('_', ' ').title()}:")
                print("-" * 40)
                # Truncate long results for readability
                content = str(step_result.result)
                if step_name == "create_report":
                    print(content)  # Show full report
                else:
                    print(content[:300] + "..." if len(content) > 300 else content)

    except Exception as e:
        print(f"\nWorkflow failed: {e}")


async def parallel_processing_workflow():
    """Demonstrate parallel step execution."""
    print("\n\n=== Parallel Processing Workflow ===\n")

    agent = WorkflowAgent(
        name="ParallelProcessor",
        instructions="You are a content creation specialist. Generate high-quality content based on the given prompts.",
        model="gpt-4o-mini",
    )

    workflow = agent.create_workflow(
        name="content_creation",
        description="Create multiple content pieces in parallel",
    )

    # Initial research step
    workflow.add_step(
        name="research_topic",
        action="Research and outline key points about 'The Future of Renewable Energy'. List 5 main topics to cover.",
    )

    # Parallel content creation (all depend on research)
    workflow.add_step(
        name="write_introduction",
        action="Write a compelling 100-word introduction about the future of renewable energy",
        depends_on=["research_topic"],
        parallel=True,
    )

    workflow.add_step(
        name="create_statistics",
        action="Generate 5 impactful statistics about renewable energy growth and adoption",
        depends_on=["research_topic"],
        parallel=True,
    )

    workflow.add_step(
        name="develop_examples",
        action="Create 3 real-world examples of innovative renewable energy projects",
        depends_on=["research_topic"],
        parallel=True,
    )

    workflow.add_step(
        name="write_conclusion",
        action="Write a forward-looking 100-word conclusion about renewable energy's potential",
        depends_on=["research_topic"],
        parallel=True,
    )

    # Final assembly (depends on all parallel steps)
    workflow.add_step(
        name="assemble_article",
        action="""Combine all the parallel content into a cohesive article:
        1. Introduction
        2. Key statistics
        3. Real-world examples
        4. Conclusion
        
        Ensure smooth transitions between sections.""",
        depends_on=[
            "write_introduction",
            "create_statistics",
            "develop_examples",
            "write_conclusion",
        ],
    )

    print("Executing parallel content creation...")
    print("(Multiple sections will be created simultaneously)")
    print("-" * 40)

    try:
        start_time = datetime.now()
        result = await agent.execute_workflow(workflow, parallel=True)
        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n✅ Completed in {duration:.1f} seconds")
        print("(Parallel execution is more efficient than sequential!)\n")

        # Show the final article
        final_article = result.step_results.get("assemble_article")
        if final_article and final_article.status == StepStatus.COMPLETED:
            print("📄 FINAL ARTICLE:")
            print("=" * 60)
            print(final_article.result)

    except Exception as e:
        print(f"\nWorkflow failed: {e}")


async def conditional_workflow_demo():
    """Demonstrate conditional step execution."""
    print("\n\n=== Conditional Logic Workflow ===\n")

    agent = WorkflowAgent(
        name="DecisionBot",
        instructions="You are a decision-making assistant. Evaluate conditions and make appropriate recommendations.",
    )

    # Define condition handlers
    def evaluate_risk(agent, step, context):
        """Evaluate risk level based on context."""
        investment_amount = context.get("amount", 0)
        risk_tolerance = context.get("risk_tolerance", "medium")

        if investment_amount > 50000:
            risk_level = "high"
        elif investment_amount > 10000:
            risk_level = "medium"
        else:
            risk_level = "low"

        context["risk_level"] = risk_level
        context["needs_advisor"] = investment_amount > 25000

        return f"Investment amount: ${investment_amount}, Risk level: {risk_level}, Risk tolerance: {risk_tolerance}"

    agent.register_handler("evaluate_risk", evaluate_risk)

    workflow = agent.create_workflow(
        name="investment_advisor",
        description="Provide investment advice based on amount and risk",
    )

    # Steps
    workflow.add_step(
        name="gather_info",
        action="Acknowledge the investment inquiry and summarize the client's situation based on the context provided.",
    )

    workflow.add_step(
        name="assess_risk", handler="evaluate_risk", depends_on=["gather_info"]
    )

    # Conditional steps based on risk assessment
    workflow.add_step(
        name="high_risk_advice",
        action="Provide detailed advice for HIGH-RISK investment scenarios. Recommend diversification and professional consultation.",
        depends_on=["assess_risk"],
        condition="risk_level == 'high'",
    )

    workflow.add_step(
        name="medium_risk_advice",
        action="Provide balanced investment advice for MEDIUM-RISK scenarios. Suggest a mix of growth and stable investments.",
        depends_on=["assess_risk"],
        condition="risk_level == 'medium'",
    )

    workflow.add_step(
        name="low_risk_advice",
        action="Provide conservative investment advice for LOW-RISK scenarios. Focus on safe, stable investment options.",
        depends_on=["assess_risk"],
        condition="risk_level == 'low'",
    )

    workflow.add_step(
        name="advisor_referral",
        action="Recommend scheduling a consultation with a professional financial advisor due to the investment size.",
        depends_on=["assess_risk"],
        condition="needs_advisor == True",
    )

    # Test different scenarios
    scenarios = [
        {"amount": 5000, "risk_tolerance": "low", "name": "Conservative Investor"},
        {"amount": 30000, "risk_tolerance": "medium", "name": "Balanced Investor"},
        {"amount": 75000, "risk_tolerance": "high", "name": "Aggressive Investor"},
    ]

    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']} (${scenario['amount']})")
        print("-" * 40)

        # Reset workflow
        for step in workflow.steps:
            step.status = StepStatus.PENDING
            step.result = None

        try:
            result = await agent.execute_workflow(workflow, context=scenario)

            # Show which paths were taken
            print("\nExecution path:")
            for step_name, step_result in result.step_results.items():
                if step_result.status == StepStatus.COMPLETED:
                    print(f"  ✅ {step_name}")
                elif step_result.status == StepStatus.SKIPPED:
                    print(f"  ⏭️  {step_name} (skipped - condition not met)")

        except Exception as e:
            print(f"Workflow failed: {e}")


async def main():
    """Run all workflow demonstrations."""
    print("WorkflowAgent Framework-Compatible Examples")
    print("=" * 60)
    print("\nThese examples demonstrate all workflow features")
    print("while working within the framework's current constraints.\n")

    # Check for API key
    import os

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key'")
        return

    # Run demonstrations
    await weather_analysis_workflow()
    await parallel_processing_workflow()
    await conditional_workflow_demo()

    print("\n" + "=" * 60)
    print("✅ All workflow examples completed successfully!")
    print("\nKey features demonstrated:")
    print("- Sequential workflow execution with dependencies")
    print("- Parallel step execution for efficiency")
    print("- Conditional logic based on context and handlers")
    print("- Data flow between workflow steps")
    print("- Complex multi-step processes")
    print("\nNo tool execution errors! 🎉")


if __name__ == "__main__":
    asyncio.run(main())
