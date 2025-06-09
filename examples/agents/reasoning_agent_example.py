"""Example: Using ReasoningAgent for transparent problem solving.

This example demonstrates how ReasoningAgent exposes its thinking process
step-by-step, making it ideal for education and building trust.
"""

import asyncio

from agenticraft.agents import ReasoningAgent


async def math_tutoring_example():
    """Use ReasoningAgent as a math tutor."""
    print("=== Math Tutoring with ReasoningAgent ===\n")

    # Create a reasoning agent configured as a math tutor
    tutor = ReasoningAgent(
        name="MathTutor",
        instructions="""You are a patient math tutor who helps students understand 
        problems step-by-step. Always show your work and explain each step clearly.""",
        model="gpt-3.5-turbo",  # Can use any model
    )

    # Example 1: Basic algebra
    print("Example 1: Solving an equation")
    print("-" * 40)

    response = await tutor.think_and_act("How do I solve the equation 3x + 7 = 22?")

    print("ANSWER:")
    print(response.content)
    print("\nDETAILED REASONING STEPS:")
    for step in response.reasoning_steps:
        print(f"\n{step.number}. {step.description}")
        for detail in step.details:
            print(f"   • {detail}")
        if step.conclusion:
            print(f"   → {step.conclusion}")

    # Example 2: Word problem
    print("\n\nExample 2: Word problem")
    print("-" * 40)

    response = await tutor.think_and_act(
        """
    A store sells apples for $0.50 each and oranges for $0.75 each. 
    If Sarah buys 6 apples and 4 oranges, and pays with a $10 bill, 
    how much change will she receive?
    """
    )

    print("FORMATTED REASONING:")
    print(response.format_reasoning())

    print("\nFINAL ANSWER:")
    # Extract just the answer portion
    if "ANSWER:" in response.content:
        answer = response.content.split("ANSWER:")[-1].strip()
        print(answer)


async def multi_perspective_analysis_example():
    """Use ReasoningAgent for multi-perspective analysis."""
    print("\n\n=== Multi-Perspective Analysis Example ===\n")

    analyst = ReasoningAgent(
        name="PolicyAnalyst",
        instructions="You are a thoughtful policy analyst who considers multiple viewpoints.",
        model="gpt-4",  # Better for complex analysis
    )

    # Analyze a policy proposal from multiple angles
    analysis = await analyst.analyze(
        prompt="""
        Should cities implement congestion pricing for downtown areas 
        during peak hours to reduce traffic and pollution?
        """,
        perspectives=[
            "economic",
            "environmental",
            "social equity",
            "practical implementation",
        ],
    )

    print("COMPLETE ANALYSIS:")
    print(analysis.format_analysis())

    print("\n\nINDIVIDUAL PERSPECTIVES:")
    for perspective, content in analysis.perspectives.items():
        print(f"\n{perspective.upper()}:")
        print(content[:200] + "..." if len(content) > 200 else content)

    print(f"\n\nSYNTHESIS: {analysis.synthesis}")


async def debugging_example():
    """Use ReasoningAgent to debug code with transparent reasoning."""
    print("\n\n=== Code Debugging Example ===\n")

    debugger = ReasoningAgent(
        name="CodeDebugger",
        instructions="""You are an expert programmer who helps debug code. 
        Analyze the code step-by-step and explain what might be wrong.""",
    )

    buggy_code = """
    def calculate_average(numbers):
        total = 0
        for num in numbers:
            total += num
        average = total / len(numbers)
        return average
    
    # This crashes sometimes
    result = calculate_average([])
    """

    response = await debugger.think_and_act(
        f"Why does this code crash? How can I fix it?\n\n{buggy_code}"
    )

    print("DEBUGGING ANALYSIS:")
    print(response.content)

    # Show the reasoning history
    print("\n\nREASONING HISTORY:")
    history = debugger.get_reasoning_history(limit=1)
    if history:
        print(debugger.explain_last_response())


async def main():
    """Run all examples."""
    print("ReasoningAgent Examples")
    print("=" * 60)
    print("\nReasoningAgent provides transparent, step-by-step thinking")
    print("perfect for education, debugging, and building trust.\n")

    await math_tutoring_example()
    await multi_perspective_analysis_example()
    await debugging_example()

    print("\n" + "=" * 60)
    print("✅ ReasoningAgent examples completed!")
    print("\nKey benefits demonstrated:")
    print("- Step-by-step problem solving with clear explanations")
    print("- Multi-perspective analysis for complex decisions")
    print("- Transparent debugging with reasoning traces")
    print("- Educational applications with detailed thinking process")


if __name__ == "__main__":
    # Note: Requires API keys to be set
    import os

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key'")
    else:
        asyncio.run(main())
