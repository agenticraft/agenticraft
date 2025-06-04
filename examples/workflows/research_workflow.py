"""Research workflow example.

This example shows a multi-agent research pipeline that:
1. Researches a topic
2. Fact-checks the information  
3. Writes a summary
4. Reviews and edits the content
"""

import asyncio
from agenticraft import Agent, Workflow, Step, tool


@tool
def save_to_file(filename: str, content: str) -> str:
    """Save content to a file."""
    # In a real implementation, this would save to disk
    # For demo purposes, we'll just return a confirmation
    return f"Content saved to {filename}"


async def main():
    """Run a research workflow example."""
    
    print("📚 Research Workflow Example")
    print("=" * 50)
    
    # Create specialized agents
    researcher = Agent(
        name="Researcher",
        model="gpt-4",
        instructions="""You are an expert researcher. 
        Find accurate, relevant information on the given topic.
        Cite your sources when possible."""
    )
    
    fact_checker = Agent(
        name="FactChecker", 
        model="gpt-4",
        instructions="""You are a fact-checker.
        Review information for accuracy and identify any claims
        that need verification or correction."""
    )
    
    writer = Agent(
        name="Writer",
        model="gpt-4", 
        instructions="""You are a skilled technical writer.
        Create clear, engaging content based on the research provided.
        Structure the content with headings and sections."""
    )
    
    editor = Agent(
        name="Editor",
        model="gpt-4",
        instructions="""You are an editor. 
        Review content for clarity, grammar, and flow.
        Suggest improvements and polish the final text."""  
    )
    
    # Create research workflow
    workflow = Workflow(
        name="research_pipeline",
        description="Multi-agent research and writing pipeline"
    )
    
    # Define workflow steps
    workflow.add_steps([
        # Step 1: Initial research
        Step(
            "research",
            agent=researcher,
            inputs={
                "prompt": "Research the topic: $topic\nProvide comprehensive information."
            },
            retry_count=1,  # Retry once if it fails
            timeout=60     # 60 second timeout
        ),
        
        # Step 2: Fact-check the research
        Step(
            "fact_check",
            agent=fact_checker,
            inputs={
                "prompt": "Review this research for accuracy",
                "research": "$research"
            },
            depends_on=["research"]
        ),
        
        # Step 3: Write the article
        Step(
            "write",
            agent=writer,
            inputs={
                "prompt": "Write an article based on this verified research",
                "research": "$research",
                "fact_check_notes": "$fact_check"
            },
            depends_on=["research", "fact_check"]
        ),
        
        # Step 4: Edit and polish
        Step(
            "edit",
            agent=editor,
            inputs={
                "prompt": "Edit and improve this article",
                "draft": "$write"
            },
            depends_on=["write"]
        ),
        
        # Step 5: Save the final output
        Step(
            "save",
            tool=save_to_file,
            inputs={
                "filename": "research_output.md",
                "content": "$edit"
            },
            depends_on=["edit"]
        )
    ])
    
    # Show workflow structure
    print("\nWorkflow Structure:")
    print(workflow.visualize())
    
    # Run the workflow
    print("\n\nExecuting research workflow...")
    print("This would run the full pipeline with the topic provided.")
    
    # Example of how to run (requires API keys):
    """
    result = await workflow.run(
        topic="The future of AI agent frameworks"
    )
    
    if result.success:
        print(f"✅ Research completed successfully!")
        print(f"\nFinal article preview:")
        print(result['edit'].content[:500] + "...")
        print(f"\n{result['save']}")
    else:
        print(f"❌ Workflow failed at step: {list(result.steps.keys())[-1]}")
    """


if __name__ == "__main__":
    print("\nNote: This example requires API keys to be configured.")
    print("Set OPENAI_API_KEY environment variable to run the full workflow.")
    
    # Uncomment to run:
    # asyncio.run(main())
