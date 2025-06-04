#!/usr/bin/env python3
"""Example: Research Assistant Workflow

This example demonstrates how to build a multi-step workflow that:
1. Searches for information on a topic
2. Extracts and analyzes the content
3. Generates a summary report

This showcases tool integration, step dependencies, and agent collaboration.
"""

import asyncio
from agenticraft import Agent, Workflow, Step
from agenticraft.tools import web_search, extract_text, write_json


async def main():
    """Run a research workflow."""
    
    # Create specialized agents
    researcher = Agent(
        name="Researcher",
        instructions="""You are a research specialist. You search for information 
        and identify the most relevant sources.""",
        tools=[web_search, extract_text]
    )
    
    analyst = Agent(
        name="Analyst",
        instructions="""You analyze information and extract key insights. 
        Focus on identifying patterns, main points, and important details."""
    )
    
    writer = Agent(
        name="Writer",
        instructions="""You create clear, well-structured summary reports. 
        Use markdown formatting and organize information logically.""",
        tools=[write_json]
    )
    
    # Create workflow
    workflow = Workflow(
        name="research_assistant",
        description="Multi-step research and reporting workflow"
    )
    
    # Define workflow steps
    workflow.add_steps([
        # Step 1: Search for information
        Step(
            name="search",
            agent=researcher,
            inputs={
                "task": "Search for information about: $topic",
                "num_results": 5
            }
        ),
        
        # Step 2: Extract content from top results
        Step(
            name="extract",
            agent=researcher,
            inputs={
                "task": "Extract and compile key information from the search results",
                "search_results": "$search"  # Reference to previous step
            },
            depends_on=["search"]
        ),
        
        # Step 3: Analyze the information
        Step(
            name="analyze",
            agent=analyst,
            inputs={
                "task": "Analyze the extracted information and identify key insights",
                "content": "$extract"
            },
            depends_on=["extract"]
        ),
        
        # Step 4: Write summary report
        Step(
            name="report",
            agent=writer,
            inputs={
                "task": "Create a comprehensive summary report with findings",
                "analysis": "$analyze",
                "original_topic": "$topic"
            },
            depends_on=["analyze"]
        )
    ])
    
    # Example 1: Research a technical topic
    print("=== Example 1: Technical Research ===")
    result = await workflow.run(
        topic="Latest developments in quantum computing 2024"
    )
    
    if result.success:
        print(f"\nWorkflow completed successfully!")
        print(f"\nWorkflow steps completed: {len(result.steps)}")
        if 'report' in result.steps and result.steps['report'].output:
            print(f"\nFinal Report Preview:")
            print("-" * 50)
            report_content = result.steps['report'].output.content if hasattr(result.steps['report'].output, 'content') else str(result.steps['report'].output)
            print(report_content[:500] + "...")
    else:
        print(f"Workflow failed: {result}")
    
    # Example 2: Market research
    print("\n\n=== Example 2: Market Research ===")
    result2 = await workflow.run(
        topic="AI agent frameworks comparison: LangChain vs AutoGen vs CrewAI"
    )
    
    if result2.success:
        # Save report to file
        # Extract report content safely
        report_content = ""
        if 'report' in result2.steps and result2.steps['report'].output:
            if hasattr(result2.steps['report'].output, 'content'):
                report_content = result2.steps['report'].output.content
            else:
                report_content = str(result2.steps['report'].output)
        
        report_data = {
            "topic": "AI agent frameworks comparison",
            "timestamp": str(result2.completed_at),
            "report": report_content,
            "workflow_steps": len(result2.steps)
        }
        
        # The writer agent could save this automatically
        print("\nMarket research completed!")
        print(f"Report length: {len(report_content)} characters")
    
    # Visualize workflow
    print("\n\n=== Workflow Structure ===")
    print(workflow.visualize())


# Advanced example: Parallel research workflow
async def advanced_example():
    """Advanced workflow with parallel execution."""
    
    # Create a workflow that researches multiple topics in parallel
    multi_researcher = Agent(
        name="MultiResearcher",
        instructions="You coordinate multiple research tasks.",
        tools=[web_search]
    )
    
    workflow = Workflow("parallel_research")
    
    # Add parallel search steps (no dependencies between them)
    topics = ["Python", "JavaScript", "Rust"]
    for i, topic in enumerate(topics):
        workflow.add_step(
            Step(
                name=f"search_{topic.lower()}",
                agent=multi_researcher,
                inputs={"task": f"Search for latest {topic} best practices"}
            )
        )
    
    # Consolidation step that depends on all searches
    workflow.add_step(
        Step(
            name="consolidate",
            agent=multi_researcher,
            inputs={
                "task": "Compare and consolidate findings from all programming languages",
                "python_results": "$search_python",
                "javascript_results": "$search_javascript",
                "rust_results": "$search_rust"
            },
            depends_on=[f"search_{t.lower()}" for t in topics]
        )
    )
    
    # Run parallel workflow
    print("\n\n=== Parallel Research Workflow ===")
    result = await workflow.run()
    
    print("\nParallel searches completed!")
    if result.success and 'consolidate' in result.steps:
        consolidation = result.steps['consolidate'].output
        if hasattr(consolidation, 'content'):
            print(f"Consolidation result: {consolidation.content[:200]}...")
        else:
            print(f"Consolidation result: {str(consolidation)[:200]}...")


# Error handling example
async def error_handling_example():
    """Demonstrate workflow error handling and retries."""
    
    # Create a workflow with retry logic
    unreliable_agent = Agent(
        name="UnreliableAgent",
        instructions="You sometimes fail (for demo purposes)."
    )
    
    workflow = Workflow("retry_demo")
    
    workflow.add_step(
        Step(
            name="risky_operation",
            agent=unreliable_agent,
            inputs={"task": "Perform a complex operation"},
            retry_count=3,  # Retry up to 3 times on failure
            timeout=10  # Timeout after 10 seconds
        )
    )
    
    try:
        result = await workflow.run()
        if 'risky_operation' in result.steps:
            attempts = result.steps['risky_operation'].metadata.get('attempts', 1)
            print(f"Success after {attempts} attempts")
    except Exception as e:
        print(f"Failed after all retries: {e}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
    
    # Uncomment to run advanced examples
    # asyncio.run(advanced_example())
    # asyncio.run(error_handling_example())
