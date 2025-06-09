"""Research workflow example.

This example shows a multi-agent research pipeline that:
1. Researches a topic
2. Fact-checks the information
3. Writes a summary
4. Reviews and edits the content

Using a simplified handler pattern approach.
"""

import asyncio
import os

from dotenv import load_dotenv

from agenticraft.agents.workflow import StepStatus, WorkflowAgent

# Load environment variables from .env file
load_dotenv()


def save_to_file(filename: str, content: str) -> str:
    """Save content to a file."""
    # In a real implementation, this would save to disk
    # For demo purposes, we'll just return a confirmation
    return f"Content saved to {filename} ({len(content)} characters)"


async def main():
    """Run a research workflow example."""

    print("📚 Research Workflow Example")
    print("=" * 50)

    # Create workflow agent
    coordinator = WorkflowAgent(
        name="ResearchCoordinator",
        model="gpt-4",
        instructions="""You are a research coordinator. Help execute each step 
        of the research process effectively.""",
    )

    # The topic to research
    topic = "The future of AI agent frameworks"

    # Register handlers
    def save_handler(agent, step, context):
        """Save the final article."""
        article = context.get("final_article", "")
        if not article and "edited_article" in context:
            article = context["edited_article"]

        filename = context.get("filename", "research_output.md")
        result = save_to_file(filename, article)
        context["save_result"] = result
        return result

    # Register handler
    coordinator.register_handler("save", save_handler)

    # Create workflow
    workflow = coordinator.create_workflow(
        name="research_pipeline",
        description="Multi-stage research and writing pipeline",
    )

    # Step 1: Research
    workflow.add_step(
        name="research",
        action=f"""Research the topic: '{topic}'
        
        Provide:
        1. Key facts and current state
        2. Recent developments and trends
        3. Future predictions
        4. Important considerations
        
        Be comprehensive but concise (aim for 300-400 words).""",
    )

    # Step 2: Fact-check
    workflow.add_step(
        name="fact_check",
        action="""Review the research above for accuracy. 
        
        Identify:
        1. Any claims that might need verification
        2. Missing important information
        3. Suggestions for improvement
        
        Provide a brief fact-check summary.""",
        depends_on=["research"],
    )

    # Step 3: Write article
    workflow.add_step(
        name="write",
        action="""Based on the research and fact-check above, write a clear, 
        engaging article about the topic.
        
        Structure:
        - Compelling introduction
        - 2-3 main sections with headers
        - Conclusion with key takeaways
        
        Target length: 400-500 words. Use markdown formatting.""",
        depends_on=["research", "fact_check"],
    )

    # Step 4: Edit
    workflow.add_step(
        name="edit",
        action="""Edit the article above for:
        1. Clarity and flow
        2. Grammar and style
        3. Engagement and readability
        
        Provide the polished final version.""",
        depends_on=["write"],
    )

    # Step 5: Save
    workflow.add_step(
        name="save",
        handler="save",
        action="Saving the final article",
        depends_on=["edit"],
    )

    # Show workflow structure
    print("\nWorkflow Structure:")
    print(coordinator.visualize_workflow(workflow))

    # Prepare context
    context = {"topic": topic, "filename": "ai_frameworks_article.md"}

    # Run workflow
    print("\n\nExecuting research workflow...")
    print(f"Topic: {topic}")
    print("-" * 40)

    try:
        result = await coordinator.execute_workflow(workflow, context=context)

        # Store results in context for save handler
        if result.status == StepStatus.COMPLETED:
            edit_step = result.step_results.get("edit")
            if edit_step and edit_step.status == StepStatus.COMPLETED:
                context["edited_article"] = edit_step.result
                context["final_article"] = edit_step.result
                # Re-run save handler
                save_handler(coordinator, None, context)

        print("\n✅ Research completed successfully!")
        print(f"Duration: {result.duration:.2f} seconds")

        # Show step summaries
        print("\nWorkflow Steps:")
        for step_name, step_result in result.step_results.items():
            status_icon = "✓" if step_result.status == StepStatus.COMPLETED else "✗"
            print(f"  {status_icon} {step_name}: {step_result.status}")

        # Show save result
        if "save_result" in context:
            print(f"\n{context['save_result']}")

        # Show article preview
        if "final_article" in context:
            article = context["final_article"]
            print("\nArticle Preview (first 500 chars):")
            print("-" * 40)
            print(article[:500] + "..." if len(article) > 500 else article)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found")
        print("Please ensure you have a .env file with OPENAI_API_KEY=your-key")
        print("Or set it as an environment variable: export OPENAI_API_KEY='your-key'")
    else:
        print(f"✅ API key found (starts with: {os.getenv('OPENAI_API_KEY')[:8]}...)")
        print()
        asyncio.run(main())
