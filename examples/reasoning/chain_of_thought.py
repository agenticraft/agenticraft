#!/usr/bin/env python3
"""Chain of Thought reasoning examples.

This example demonstrates Chain of Thought pattern with proper provider handling
and graceful fallback when APIs are unavailable.
"""

import asyncio
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Load environment variables
try:
    from dotenv import find_dotenv, load_dotenv

    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
        console.print(f"[dim]Loaded .env from: {dotenv_path}[/dim]")
    else:
        # Try parent directories
        for i in range(5):
            env_path = (
                Path(__file__).parents[i] / ".env"
                if i < len(Path(__file__).parents)
                else None
            )
            if env_path and env_path.exists():
                load_dotenv(env_path)
                console.print(f"[dim]Loaded .env from: {env_path}[/dim]")
                break
except ImportError:
    pass  # python-dotenv not installed


def get_provider_config():
    """Get the best available provider configuration."""
    if os.getenv("OPENAI_API_KEY"):
        console.print("[dim]Using OpenAI provider[/dim]")
        return "openai", "gpt-3.5-turbo"
    elif os.getenv("ANTHROPIC_API_KEY"):
        console.print("[dim]Using Anthropic provider[/dim]")
        return "anthropic", "claude-3-haiku-20240307"
    else:
        console.print("[dim]Using mock mode (no API keys found)[/dim]")
        return None, None


async def mock_chain_of_thought(problem: str, context: dict = None) -> dict:
    """Mock Chain of Thought reasoning when no API is available."""
    # Simulate thinking delay
    await asyncio.sleep(1)

    # Generate mock steps based on problem type
    steps = []

    if "calculate" in problem.lower() or "math" in problem.lower():
        steps = [
            {
                "step": 1,
                "thought": "Identify the mathematical operation needed",
                "confidence": 0.95,
            },
            {
                "step": 2,
                "thought": "Extract the relevant numbers from the problem",
                "confidence": 0.90,
            },
            {
                "step": 3,
                "thought": "Apply the appropriate formula or calculation",
                "confidence": 0.88,
            },
            {"step": 4, "thought": "Verify the result makes sense", "confidence": 0.85},
            {"step": 5, "thought": "Express the answer clearly", "confidence": 0.92},
        ]
        answer = "Based on step-by-step calculation, the answer is 42 (mocked result)"

    elif "analyze" in problem.lower():
        steps = [
            {
                "step": 1,
                "thought": "Break down the problem into components",
                "confidence": 0.88,
            },
            {
                "step": 2,
                "thought": "Identify key factors and relationships",
                "confidence": 0.85,
            },
            {
                "step": 3,
                "thought": "Consider multiple perspectives",
                "confidence": 0.82,
            },
            {
                "step": 4,
                "thought": "Synthesize findings into insights",
                "confidence": 0.87,
            },
            {"step": 5, "thought": "Form actionable conclusions", "confidence": 0.90},
        ]
        answer = "Analysis reveals multiple factors at play, with primary drivers being X and Y (mocked result)"

    else:
        steps = [
            {"step": 1, "thought": "Understand the core question", "confidence": 0.90},
            {"step": 2, "thought": "Gather relevant information", "confidence": 0.85},
            {"step": 3, "thought": "Apply logical reasoning", "confidence": 0.88},
            {"step": 4, "thought": "Consider implications", "confidence": 0.83},
            {
                "step": 5,
                "thought": "Formulate comprehensive answer",
                "confidence": 0.87,
            },
        ]
        answer = "Through systematic reasoning, the solution involves considering A, B, and C (mocked result)"

    return {
        "steps": steps,
        "answer": answer,
        "confidence": sum(s["confidence"] for s in steps) / len(steps),
    }


async def math_problem_example():
    """Solve a math word problem using Chain of Thought."""
    console.print("\n[bold cyan]Chain of Thought: Math Problem Solver[/bold cyan]\n")

    provider, model = get_provider_config()

    problem = """
    A bakery produces 150 loaves of bread daily. Each loaf costs $2.50 to make 
    and sells for $4.00. If 12% of loaves are unsold and donated, what is the 
    bakery's daily profit?
    """

    console.print(Panel(problem, title="Problem", border_style="yellow"))

    if provider:
        try:
            # Import only if we have a provider
            from agenticraft.agents.reasoning import ReasoningAgent

            agent = ReasoningAgent(
                name="MathTutor",
                instructions="Break down math problems step by step with clear reasoning.",
                reasoning_pattern="chain_of_thought",
                pattern_config={"min_confidence": 0.8, "max_steps": 10},
                provider=provider,
                model=model,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Solving step by step...", total=None)
                response = await agent.think_and_act(problem)
                progress.update(task, completed=True)

            # Display reasoning steps
            console.print("\n[bold green]Reasoning Steps:[/bold green]")
            for i, step in enumerate(response.reasoning_steps, 1):
                console.print(f"\n[cyan]Step {i}:[/cyan] {step.description}")
                if hasattr(step, "details") and step.details:
                    for detail in step.details:
                        console.print(f"  • {detail}")
                if hasattr(step, "confidence"):
                    console.print(f"  [dim]Confidence: {step.confidence:.2%}[/dim]")

            console.print(
                Panel(response.content, title="Solution", border_style="green")
            )

        except Exception as e:
            console.print(f"[yellow]API Error: {e}. Using mock mode.[/yellow]")
            provider = None

    if not provider:
        # Use mock mode
        result = await mock_chain_of_thought(problem)

        console.print("\n[bold green]Reasoning Steps:[/bold green]")
        for step in result["steps"]:
            console.print(f"\n[cyan]Step {step['step']}:[/cyan] {step['thought']}")
            console.print(f"  [dim]Confidence: {step['confidence']:.2%}[/dim]")

        # Provide actual solution in mock mode
        console.print(
            Panel(
                "Let me solve this step by step:\n\n"
                "1. Daily production: 150 loaves\n"
                "2. Sold loaves: 150 × (1 - 0.12) = 150 × 0.88 = 132 loaves\n"
                "3. Revenue: 132 × $4.00 = $528\n"
                "4. Total cost: 150 × $2.50 = $375\n"
                "5. Daily profit: $528 - $375 = $153\n\n"
                "The bakery's daily profit is $153.",
                title="Solution",
                border_style="green",
            )
        )


async def analysis_example():
    """Analyze a complex situation using Chain of Thought."""
    console.print("\n[bold cyan]Chain of Thought: Business Analysis[/bold cyan]\n")

    provider, model = get_provider_config()

    problem = """
    A software company has seen user churn increase from 5% to 8% monthly. 
    Customer surveys show: 40% cite bugs, 30% cite missing features, 
    20% cite price, and 10% cite support. What should be the priority?
    """

    console.print(Panel(problem, title="Analysis Task", border_style="yellow"))

    if provider:
        try:
            from agenticraft.agents.reasoning import ReasoningAgent

            agent = ReasoningAgent(
                name="BusinessAnalyst",
                instructions="Analyze business problems systematically, considering multiple factors.",
                reasoning_pattern="chain_of_thought",
                pattern_config={"min_confidence": 0.7, "max_steps": 12},
                provider=provider,
                model=model,
            )

            response = await agent.think_and_act(problem)

            # Show confidence progression
            if response.reasoning_steps:
                console.print("\n[bold]Confidence Progression:[/bold]")
                for i, step in enumerate(response.reasoning_steps, 1):
                    if hasattr(step, "confidence"):
                        bars = "█" * int(step.confidence * 20)
                        console.print(f"Step {i}: [{bars:<20}] {step.confidence:.2%}")

            console.print(
                Panel(
                    response.content,
                    title="Analysis & Recommendation",
                    border_style="green",
                )
            )

        except Exception as e:
            console.print(f"[yellow]API Error: {e}. Using mock mode.[/yellow]")
            provider = None

    if not provider:
        # Mock analysis
        result = await mock_chain_of_thought(problem)

        console.print("\n[bold green]Analysis Steps:[/bold green]")
        steps = [
            "Calculate impact: 3% increase = 60% more churn",
            "Bug issues (40%) are the largest complaint category",
            "Revenue impact: Higher churn costs more than feature development",
            "Quick wins: Fix bugs first (faster than new features)",
            "Long-term: Address features after stabilization",
        ]

        for i, (step_info, step_desc) in enumerate(
            zip(result["steps"], steps, strict=False), 1
        ):
            console.print(f"\n[cyan]Step {i}:[/cyan] {step_desc}")
            console.print(f"  [dim]Confidence: {step_info['confidence']:.2%}[/dim]")

        console.print(
            Panel(
                "Priority Recommendation:\n\n"
                "1. **Immediate: Fix Bugs** (40% of complaints)\n"
                "   - Highest impact on churn reduction\n"
                "   - Faster to implement than new features\n"
                "   - Improves overall product stability\n\n"
                "2. **Next: Key Features** (30% of complaints)\n"
                "   - Focus on most requested features\n"
                "   - Can justify price for some users\n\n"
                "3. **Ongoing: Support & Price**\n"
                "   - Improve support response times\n"
                "   - Consider pricing tiers\n\n"
                "Estimated impact: Could reduce churn back to 5-6% within 3 months",
                title="Analysis & Recommendation",
                border_style="green",
            )
        )


async def decision_making_example():
    """Make a decision using Chain of Thought reasoning."""
    console.print("\n[bold cyan]Chain of Thought: Decision Making[/bold cyan]\n")

    provider, model = get_provider_config()

    problem = """
    Should our startup accept a $2M acquisition offer? Context:
    - Current revenue: $500K/year, growing 50% annually
    - Team: 8 people, all with equity
    - Runway: 18 months remaining
    - Acquirer: Large tech company, good cultural fit
    - Alternative: Raise Series A ($5M target)
    """

    console.print(Panel(problem, title="Decision Problem", border_style="yellow"))

    # Create decision matrix
    console.print("\n[bold]Decision Framework:[/bold]")

    table = Table(title="Key Factors Analysis")
    table.add_column("Factor", style="cyan")
    table.add_column("Acquisition", style="green")
    table.add_column("Series A", style="yellow")
    table.add_column("Weight", justify="right")

    factors = [
        ("Financial Outcome", "Certain $2M", "Potential $10M+", "30%"),
        ("Team Retention", "Some may leave", "Full control", "20%"),
        ("Growth Potential", "Limited", "Unlimited", "25%"),
        ("Risk Level", "Low", "High", "15%"),
        ("Time to Exit", "Immediate", "3-5 years", "10%"),
    ]

    for factor, acq, series, weight in factors:
        table.add_row(factor, acq, series, weight)

    console.print(table)

    if provider:
        try:
            from agenticraft.agents.reasoning import ReasoningAgent

            agent = ReasoningAgent(
                name="DecisionMaker",
                instructions="Make strategic decisions by weighing multiple factors systematically.",
                reasoning_pattern="chain_of_thought",
                provider=provider,
                model=model,
            )

            response = await agent.think_and_act(problem)

            console.print(
                Panel(
                    response.content,
                    title="Decision Recommendation",
                    border_style="green",
                )
            )

        except Exception as e:
            console.print(f"[yellow]API Error: {e}. Using mock mode.[/yellow]")
            provider = None

    if not provider:
        # Mock decision process
        console.print("\n[bold green]Decision Analysis:[/bold green]")

        steps = [
            ("Evaluate financial certainty vs. potential", 0.85),
            ("Consider team impact and retention", 0.80),
            ("Analyze market timing and growth trajectory", 0.88),
            ("Assess acquirer fit and integration risk", 0.82),
            ("Calculate risk-adjusted returns", 0.87),
            ("Form final recommendation", 0.90),
        ]

        for i, (step, conf) in enumerate(steps, 1):
            console.print(f"\n[cyan]Step {i}:[/cyan] {step}")
            console.print(f"  [dim]Confidence: {conf:.2%}[/dim]")

        console.print(
            Panel(
                "**Recommendation: Raise Series A**\n\n"
                "Reasoning:\n"
                "• 50% annual growth suggests strong product-market fit\n"
                "• $2M acquisition undervalues growth potential\n"
                "• 18-month runway provides negotiating leverage\n"
                "• Team equity worth more with continued growth\n"
                "• Cultural fit reduces integration benefits\n\n"
                "However, consider acquisition if:\n"
                "• Series A fundraising fails\n"
                "• Key team members want early exit\n"
                "• Market conditions deteriorate\n\n"
                "Confidence: 85%",
                title="Decision Recommendation",
                border_style="green",
            )
        )


async def pattern_showcase():
    """Showcase different aspects of Chain of Thought."""
    console.print("\n[bold cyan]Chain of Thought: Pattern Showcase[/bold cyan]\n")

    examples = [
        {
            "title": "Sequential Logic",
            "problem": "If A → B, B → C, and C → D, and we know A is true, what can we conclude?",
            "characteristics": [
                "Clear logical flow",
                "Build on previous steps",
                "High certainty",
            ],
        },
        {
            "title": "Process Analysis",
            "problem": "How can we optimize a checkout process that takes 5 minutes?",
            "characteristics": [
                "Break down steps",
                "Identify bottlenecks",
                "Systematic improvement",
            ],
        },
        {
            "title": "Root Cause Analysis",
            "problem": "Website traffic dropped 30% last week. Why?",
            "characteristics": [
                "Investigate systematically",
                "Test hypotheses",
                "Evidence-based",
            ],
        },
    ]

    for example in examples:
        console.print(f"\n[bold]{example['title']}[/bold]")
        console.print(f"Problem: {example['problem']}")
        console.print("Characteristics:")
        for char in example["characteristics"]:
            console.print(f"  • {char}")

    console.print(
        Panel(
            "Chain of Thought excels at:\n"
            "✓ Problems with clear logical structure\n"
            "✓ Step-by-step procedures\n"
            "✓ Mathematical calculations\n"
            "✓ Systematic analysis\n"
            "✓ Building complex arguments\n\n"
            "Less suitable for:\n"
            "✗ Highly creative tasks\n"
            "✗ Problems with many valid approaches\n"
            "✗ Tasks requiring external data",
            title="When to Use Chain of Thought",
            border_style="blue",
        )
    )


async def main():
    """Run all Chain of Thought examples."""
    console.print(
        Panel(
            "[bold green]Chain of Thought Reasoning Examples[/bold green]\n\n"
            "These examples demonstrate step-by-step reasoning with confidence tracking.\n"
            "Works with OpenAI, Anthropic, or in mock mode without any API.",
            title="AgentiCraft v0.2.0",
            border_style="green",
        )
    )

    examples = [
        ("Math Problem Solving", math_problem_example),
        ("Business Analysis", analysis_example),
        ("Decision Making", decision_making_example),
        ("Pattern Showcase", pattern_showcase),
    ]

    for name, example_func in examples:
        console.print(f"\n{'='*70}")
        console.print(f"[yellow]Example: {name}[/yellow]")
        console.print("=" * 70)

        try:
            await example_func()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error in {name}: {e}[/red]")
            if os.getenv("DEBUG"):
                import traceback

                console.print(f"[dim]{traceback.format_exc()}[/dim]")

    console.print("\n[bold green]✨ Examples completed![/bold green]")

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        console.print(
            "\n[yellow]Tip:[/yellow] Set OPENAI_API_KEY or ANTHROPIC_API_KEY for real AI responses"
        )


if __name__ == "__main__":
    asyncio.run(main())
