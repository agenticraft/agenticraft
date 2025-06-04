"""Simple workflow example.

This example demonstrates basic workflow functionality with
sequential steps and data passing.
"""

import asyncio
from agenticraft import Agent, Workflow, Step, tool


# Create a simple tool
@tool
def extract_keywords(text: str) -> list:
    """Extract keywords from text."""
    # Simple keyword extraction
    words = text.lower().split()
    keywords = [w for w in words if len(w) > 4]
    return keywords


@tool 
def format_report(title: str, keywords: list) -> str:
    """Format a simple report."""
    report = f"# {title}\n\n"
    report += "## Keywords Found:\n"
    for keyword in keywords:
        report += f"- {keyword}\n"
    return report


async def main():
    """Run a simple workflow example."""
    
    print("🔧 Simple Workflow Example")
    print("=" * 50)
    
    # Create agents
    analyzer = Agent(
        name="Analyzer",
        model="gpt-3.5-turbo",
        instructions="You analyze text and provide insights."
    )
    
    # Create workflow
    workflow = Workflow(
        name="text_analysis",
        description="Simple text analysis pipeline"
    )
    
    # Add steps
    workflow.add_steps([
        # Step 1: Extract keywords using tool
        Step(
            "extract",
            tool=extract_keywords,
            inputs={"text": "$input_text"}
        ),
        
        # Step 2: Analyze with agent
        Step(
            "analyze",
            agent=analyzer,
            inputs={
                "prompt": "Analyze these keywords and provide 2-3 insights",
                "keywords": "$extract"
            },
            depends_on=["extract"]
        ),
        
        # Step 3: Format report
        Step(
            "report",
            tool=format_report,
            inputs={
                "title": "Text Analysis Report",
                "keywords": "$extract"
            },
            depends_on=["analyze"]
        )
    ])
    
    # Visualize workflow
    print("\nWorkflow Structure:")
    print(workflow.visualize())
    
    # Run workflow
    print("\n\nExecuting workflow...")
    result = await workflow.run(
        input_text="AgentiCraft makes building AI agents simple and transparent"
    )
    
    # Display results
    print(f"\n✅ Workflow completed: {result.success}")
    print(f"\nKeywords extracted: {result['extract']}")
    print(f"\nAnalysis insights: {result['analyze'].content}")
    print(f"\nFinal report:\n{result['report']}")


if __name__ == "__main__":
    # Note: In a real scenario, ensure you have API keys configured
    print("Note: This example requires API keys to be configured.")
    print("Set OPENAI_API_KEY environment variable or update the example.\n")
    
    # Uncomment the following line to run:
    # asyncio.run(main())
