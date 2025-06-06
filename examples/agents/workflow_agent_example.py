"""Example: Using WorkflowAgent for multi-step processes.

This example demonstrates how WorkflowAgent orchestrates complex workflows
with dependencies, parallel execution, and error handling.
"""

import asyncio
from datetime import datetime

from agenticraft.agents import WorkflowAgent, Workflow, StepStatus
from agenticraft import tool


# Define some tools for the workflow to use
@tool
def fetch_weather(city: str) -> dict:
    """Fetch weather data for a city (simulated)."""
    # Simulated weather data
    return {
        "city": city,
        "temperature": 72,
        "conditions": "Partly cloudy",
        "humidity": 65,
        "forecast": "Mild with occasional clouds"
    }


@tool 
def analyze_data(data: dict) -> dict:
    """Analyze data and return insights (simulated)."""
    return {
        "summary": f"Analysis of {len(data)} data points",
        "trend": "stable",
        "recommendation": "No action needed"
    }


async def data_pipeline_example():
    """Example: Data processing pipeline with sequential steps."""
    print("=== Data Pipeline Workflow ===\n")
    
    # Create workflow agent
    agent = WorkflowAgent(
        name="DataProcessor",
        instructions="You are a data processing agent. Execute each step precisely.",
        tools=[fetch_weather, analyze_data]
    )
    
    # Define the workflow
    workflow = agent.create_workflow(
        name="weather_analysis_pipeline",
        description="Fetch and analyze weather data for multiple cities"
    )
    
    # Add workflow steps
    workflow.add_step(
        name="fetch_data",
        action="Use the fetch_weather tool to get weather data for New York, London, and Tokyo. Store the results.",
    )
    
    workflow.add_step(
        name="validate_data",
        action="Check that we received valid weather data for all three cities. List what we have.",
        depends_on=["fetch_data"]
    )
    
    workflow.add_step(
        name="analyze_patterns",
        action="Analyze the weather patterns across the three cities. What are the similarities and differences?",
        depends_on=["validate_data"]
    )
    
    workflow.add_step(
        name="generate_report",
        action="Create a brief weather report summarizing the conditions in all three cities.",
        depends_on=["analyze_patterns"]
    )
    
    # Execute the workflow
    print("Starting workflow execution...")
    print("-" * 40)
    
    result = await agent.execute_workflow(workflow)
    
    # Display results
    print("\nWORKFLOW COMPLETED!")
    print(result.format_summary())
    
    print("\n\nDETAILED RESULTS:")
    for step_name, step_result in result.step_results.items():
        print(f"\n{step_name}:")
        print(f"  Status: {step_result.status}")
        if step_result.result:
            print(f"  Result: {step_result.result[:200]}...")


async def parallel_workflow_example():
    """Example: Parallel task execution."""
    print("\n\n=== Parallel Task Execution ===\n")
    
    agent = WorkflowAgent(name="ParallelProcessor")
    
    # Create workflow with parallel steps
    workflow = agent.create_workflow(
        name="content_generation",
        description="Generate multiple content pieces in parallel"
    )
    
    # Add parallel content generation steps
    workflow.add_step(
        name="write_intro",
        action="Write a compelling introduction for an article about AI",
        parallel=True
    )
    
    workflow.add_step(
        name="create_examples",
        action="Create 3 practical examples of AI in everyday life",
        parallel=True
    )
    
    workflow.add_step(
        name="write_conclusion",
        action="Write a thought-provoking conclusion about the future of AI",
        parallel=True
    )
    
    # Final step depends on all parallel steps
    workflow.add_step(
        name="combine_content",
        action="Combine the introduction, examples, and conclusion into a cohesive article",
        depends_on=["write_intro", "create_examples", "write_conclusion"]
    )
    
    print("Executing parallel workflow...")
    print("(Notice how intro, examples, and conclusion are generated simultaneously)")
    print("-" * 40)
    
    start_time = datetime.now()
    result = await agent.execute_workflow(workflow, parallel=True)
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\nCompleted in {duration:.2f} seconds")
    print("(Parallel execution is faster than sequential!)")
    
    # Show the final combined content
    final_content = result.get_step_result("combine_content")
    if final_content:
        print("\nFINAL ARTICLE:")
        print("-" * 40)
        print(final_content)


async def conditional_workflow_example():
    """Example: Workflow with conditional logic."""
    print("\n\n=== Conditional Workflow ===\n")
    
    agent = WorkflowAgent(name="DecisionMaker")
    
    # Define custom handlers for decision logic
    def check_budget(agent, step, context):
        """Check if budget is sufficient."""
        budget = context.get("budget", 0)
        required = context.get("required_amount", 1000)
        context["budget_sufficient"] = budget >= required
        return f"Budget check: ${budget} vs ${required} required"
    
    async def approve_purchase(agent, step, context):
        """Approve the purchase."""
        item = context.get("item", "Unknown item")
        return f"Purchase approved for {item}"
    
    # Register handlers
    agent.register_handler("check_budget", check_budget)
    agent.register_handler("approve_purchase", approve_purchase)
    
    # Create workflow
    workflow = agent.create_workflow(
        name="purchase_approval",
        description="Automated purchase approval workflow"
    )
    
    # Add steps
    workflow.add_step(
        name="analyze_request",
        action="Analyze the purchase request for a new laptop costing $1200"
    )
    
    workflow.add_step(
        name="check_budget",
        handler="check_budget",
        depends_on=["analyze_request"]
    )
    
    workflow.add_step(
        name="get_approval",
        action="Get manager approval for the purchase",
        depends_on=["check_budget"],
        condition="budget_sufficient == True"  # Only run if budget is sufficient
    )
    
    workflow.add_step(
        name="notify_rejection",
        action="Notify that the purchase request is rejected due to insufficient budget",
        depends_on=["check_budget"],
        condition="budget_sufficient == False"  # Only run if budget insufficient
    )
    
    # Test with sufficient budget
    print("Test 1: With sufficient budget ($1500)")
    print("-" * 40)
    context = {
        "budget": 1500,
        "required_amount": 1200,
        "item": "laptop"
    }
    
    result = await agent.execute_workflow(workflow, context=context)
    
    for step_name, step_result in result.step_results.items():
        status_icon = "✅" if step_result.status == StepStatus.COMPLETED else "⏭️"
        print(f"{status_icon} {step_name}: {step_result.status}")
    
    # Reset workflow for second test
    for step in workflow.steps:
        step.status = StepStatus.PENDING
        step.result = None
    
    # Test with insufficient budget
    print("\n\nTest 2: With insufficient budget ($800)")
    print("-" * 40)
    context = {
        "budget": 800,
        "required_amount": 1200,
        "item": "laptop"
    }
    
    result = await agent.execute_workflow(workflow, context=context)
    
    for step_name, step_result in result.step_results.items():
        status_icon = "✅" if step_result.status == StepStatus.COMPLETED else "⏭️"
        print(f"{status_icon} {step_name}: {step_result.status}")


async def error_handling_example():
    """Example: Workflow with error handling and retries."""
    print("\n\n=== Error Handling Workflow ===\n")
    
    agent = WorkflowAgent(name="ResilientProcessor")
    
    # Create a handler that sometimes fails
    attempt_count = {"api_call": 0}
    
    async def flaky_api_call(agent, step, context):
        """Simulate a flaky API that fails sometimes."""
        attempt_count["api_call"] += 1
        if attempt_count["api_call"] < 2:
            raise Exception("API temporarily unavailable")
        return "API call successful with data: {'status': 'ok'}"
    
    agent.register_handler("flaky_api", flaky_api_call)
    
    # Create workflow
    workflow = agent.create_workflow(
        name="resilient_data_fetch",
        description="Workflow with error handling"
    )
    
    workflow.add_step(
        name="prepare_request",
        action="Prepare the API request parameters"
    )
    
    workflow.add_step(
        name="call_api",
        handler="flaky_api",
        depends_on=["prepare_request"],
        max_retries=3,
        timeout=5.0
    )
    
    workflow.add_step(
        name="process_response",
        action="Process the API response and extract key information",
        depends_on=["call_api"]
    )
    
    print("Executing workflow with flaky API...")
    print("(The API call will fail once then succeed)")
    print("-" * 40)
    
    try:
        result = await agent.execute_workflow(workflow)
        print("\nWorkflow completed successfully!")
        print(f"Final status: {result.status}")
        
        # Note: Current implementation doesn't fully support retries
        # This is a limitation to be addressed in future versions
        
    except Exception as e:
        print(f"\nWorkflow failed: {e}")


async def main():
    """Run all workflow examples."""
    print("WorkflowAgent Examples")
    print("=" * 60)
    print("\nWorkflowAgent orchestrates multi-step processes with")
    print("dependencies, parallel execution, and conditional logic.\n")
    
    await data_pipeline_example()
    await parallel_workflow_example()
    await conditional_workflow_example()
    await error_handling_example()
    
    print("\n" + "=" * 60)
    print("✅ WorkflowAgent examples completed!")
    print("\nKey capabilities demonstrated:")
    print("- Sequential workflow execution with dependencies")
    print("- Parallel task execution for efficiency")
    print("- Conditional step execution based on context")
    print("- Custom handlers for specialized logic")
    print("- Error handling and retry mechanisms")
    print("- Real-time workflow status tracking")


if __name__ == "__main__":
    # Note: Requires API keys to be set
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key'")
    else:
        asyncio.run(main())
