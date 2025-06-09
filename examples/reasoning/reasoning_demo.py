#!/usr/bin/env python3
"""Simple reasoning patterns demo - Works without API keys.

This demonstrates all three reasoning patterns conceptually without requiring
any external API calls. Perfect for understanding how each pattern works.
"""

import asyncio
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

console = Console()


class MockReasoningStep:
    """Mock reasoning step for demonstration."""

    def __init__(
        self,
        number: int,
        description: str,
        confidence: float = 0.8,
        details: list[str] = None,
    ):
        self.number = number
        self.description = description
        self.confidence = confidence
        self.details = details or []
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"Step {self.number}: {self.description} (confidence: {self.confidence:.0%})"


class MockResponse:
    """Mock agent response."""

    def __init__(self, content: str, reasoning_steps: list[MockReasoningStep]):
        self.content = content
        self.reasoning_steps = reasoning_steps
        self.reasoning_trace = type("obj", (object,), {"confidence": 0.85})()


async def demo_chain_of_thought():
    """Demonstrate Chain of Thought reasoning pattern."""
    console.print("\n[bold cyan]🔗 Chain of Thought Pattern Demo[/bold cyan]\n")

    problem = "If a bakery sells 120 cupcakes per day at $3 each, and costs are 60% of revenue, what's the daily profit?"

    console.print(Panel(problem, title="Problem", border_style="yellow"))

    # Simulate reasoning steps
    steps = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Thinking step by step...", total=5)

        # Step 1
        await asyncio.sleep(0.5)
        steps.append(
            MockReasoningStep(
                1,
                "Calculate daily revenue",
                0.95,
                ["Revenue = 120 cupcakes × $3 = $360"],
            )
        )
        progress.update(task, advance=1)

        # Step 2
        await asyncio.sleep(0.5)
        steps.append(
            MockReasoningStep(
                2,
                "Calculate daily costs",
                0.90,
                ["Costs = 60% of $360 = 0.6 × $360 = $216"],
            )
        )
        progress.update(task, advance=1)

        # Step 3
        await asyncio.sleep(0.5)
        steps.append(
            MockReasoningStep(
                3,
                "Calculate daily profit",
                0.92,
                ["Profit = Revenue - Costs = $360 - $216 = $144"],
            )
        )
        progress.update(task, advance=1)

        # Step 4
        await asyncio.sleep(0.5)
        steps.append(
            MockReasoningStep(
                4,
                "Verify calculation",
                0.88,
                ["Check: $144 is 40% of $360 ✓", "Profit margin: 40%"],
            )
        )
        progress.update(task, advance=1)

        # Step 5
        await asyncio.sleep(0.5)
        steps.append(
            MockReasoningStep(
                5,
                "Form conclusion",
                0.95,
                ["Daily profit is $144", "Profit margin is 40%"],
            )
        )
        progress.update(task, advance=1)

    # Display steps
    console.print("\n[bold green]Reasoning Steps:[/bold green]")
    for step in steps:
        console.print(f"\n[cyan]Step {step.number}:[/cyan] {step.description}")
        for detail in step.details:
            console.print(f"  → {detail}")
        console.print(f"  [dim]Confidence: {step.confidence:.0%}[/dim]")

    # Final answer
    response = MockResponse(
        "The bakery's daily profit is $144, with a profit margin of 40%.", steps
    )

    console.print(Panel(response.content, title="Final Answer", border_style="green"))

    # Show confidence progression
    console.print("\n[bold]Confidence Progression:[/bold]")
    conf_chart = ""
    for step in steps:
        bars = "█" * int(step.confidence * 20)
        conf_chart += f"Step {step.number}: [{bars:<20}] {step.confidence:.0%}\n"
    console.print(conf_chart)


async def demo_tree_of_thoughts():
    """Demonstrate Tree of Thoughts reasoning pattern."""
    console.print("\n[bold cyan]🌳 Tree of Thoughts Pattern Demo[/bold cyan]\n")

    problem = "Design a mobile app to help people reduce screen time"

    console.print(Panel(problem, title="Design Challenge", border_style="yellow"))

    # Simulate tree exploration
    console.print("\n[yellow]Exploring solution paths...[/yellow]")

    # Create visual tree
    tree = Tree("🌳 App Design Exploration")

    # Path 1: Gamification
    path1 = tree.add("[green]Path 1: Gamification Approach[/green] (score: 0.82)")
    path1.add("↳ Points for time away from phone")
    path1.add("↳ Achievements and badges")
    path1.add("↳ Social competition")
    path1_eval = path1.add("[dim]Evaluation: High engagement, risk of addiction[/dim]")

    # Path 2: Mindfulness
    path2 = tree.add("[cyan]Path 2: Mindfulness Approach[/cyan] (score: 0.78)")
    path2.add("↳ Meditation timers")
    path2.add("↳ Breathing exercises")
    path2.add("↳ Digital wellness tips")
    path2_eval = path2.add("[dim]Evaluation: Healthy but lower engagement[/dim]")

    # Path 3: Practical Tools
    path3 = tree.add("[yellow]Path 3: Practical Tools[/yellow] (score: 0.75)")
    path3.add("↳ App usage analytics")
    path3.add("↳ Smart notifications")
    path3.add("↳ Focus mode scheduling")
    path3_eval = path3.add("[dim]Evaluation: Useful but less innovative[/dim]")

    # Path 4: Hybrid
    path4 = tree.add("[magenta]Path 4: Hybrid Solution[/magenta] (score: 0.88)")
    path4.add("↳ Gamified wellness challenges")
    path4.add("↳ Mindful moment reminders")
    path4.add("↳ Usage insights dashboard")
    path4_eval = path4.add("[dim]Evaluation: Best of all approaches[/dim]")

    # Show exploration
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exploring paths...", total=4)

        for i in range(4):
            await asyncio.sleep(0.5)
            progress.update(task, advance=1)

    console.print(tree)

    # Show path evaluation
    console.print("\n[bold green]Path Evaluation:[/bold green]")

    paths = [
        ("Gamification", 0.82, "High engagement but addiction risk"),
        ("Mindfulness", 0.78, "Healthy but might lack appeal"),
        ("Practical Tools", 0.75, "Useful but conventional"),
        ("Hybrid Solution", 0.88, "Balanced and innovative"),
    ]

    table = Table(title="Solution Paths Comparison")
    table.add_column("Path", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Analysis", style="white")

    for path, score, analysis in paths:
        table.add_row(path, f"{score:.2f}", analysis)

    console.print(table)

    # Best solution
    console.print(
        Panel(
            "The hybrid approach combining gamified wellness challenges, "
            "mindful moment reminders, and usage insights provides the best "
            "balance of engagement and health benefits. Key features:\n\n"
            "• Wellness challenges (not screen time competition)\n"
            "• Gentle mindfulness prompts\n"
            "• Insightful analytics without judgment\n"
            "• Positive reinforcement for healthy habits",
            title="Recommended Solution",
            border_style="green",
        )
    )


async def demo_react_pattern():
    """Demonstrate ReAct reasoning pattern."""
    console.print("\n[bold cyan]⚡ ReAct Pattern Demo[/bold cyan]\n")

    problem = "Find the best coffee shop near Times Square with good wifi"

    console.print(Panel(problem, title="Research Task", border_style="yellow"))

    # Simulate ReAct cycles
    cycles = []

    console.print("\n[yellow]Thought → Action → Observation cycles:[/yellow]\n")

    # Cycle 1
    console.print("[bold]Cycle 1:[/bold]")
    console.print(
        "💭 [cyan]Thought:[/cyan] I need to search for coffee shops near Times Square"
    )
    await asyncio.sleep(0.5)
    console.print(
        "⚡ [yellow]Action:[/yellow] search_locations('coffee shops Times Square NYC')"
    )
    await asyncio.sleep(0.5)
    console.print(
        "👁️  [green]Observation:[/green] Found 15 coffee shops within 0.5 miles\n"
    )

    # Cycle 2
    console.print("[bold]Cycle 2:[/bold]")
    console.print("💭 [cyan]Thought:[/cyan] I need to filter for ones with good wifi")
    await asyncio.sleep(0.5)
    console.print(
        "⚡ [yellow]Action:[/yellow] check_amenities(['Blue Bottle', 'Starbucks Reserve', 'Gregory's'], 'wifi')"
    )
    await asyncio.sleep(0.5)
    console.print(
        "👁️  [green]Observation:[/green] All 3 have wifi, Blue Bottle and Gregory's have dedicated work areas\n"
    )

    # Cycle 3
    console.print("[bold]Cycle 3:[/bold]")
    console.print(
        "💭 [cyan]Thought:[/cyan] I should check reviews for wifi quality and ambiance"
    )
    await asyncio.sleep(0.5)
    console.print(
        "⚡ [yellow]Action:[/yellow] get_reviews(['Blue Bottle', 'Gregory's'], focus='wifi workspace')"
    )
    await asyncio.sleep(0.5)
    console.print(
        "👁️  [green]Observation:[/green] Blue Bottle: 4.5★ 'Great wifi, quiet atmosphere'\n"
        "                     Gregory's: 4.2★ 'Fast wifi, can get crowded'\n"
    )

    # Cycle 4
    console.print("[bold]Cycle 4:[/bold]")
    console.print(
        "💭 [cyan]Thought:[/cyan] Blue Bottle seems best, let me get specific location"
    )
    await asyncio.sleep(0.5)
    console.print(
        "⚡ [yellow]Action:[/yellow] get_details('Blue Bottle Coffee Times Square')"
    )
    await asyncio.sleep(0.5)
    console.print(
        "👁️  [green]Observation:[/green] Address: 1450 Broadway, Open until 8 PM, 2 min walk\n"
    )

    # Final answer
    console.print(
        Panel(
            "🎯 Blue Bottle Coffee at 1450 Broadway is your best option:\n\n"
            "• 2-minute walk from Times Square\n"
            "• Excellent wifi (verified by reviews)\n"
            "• Quiet atmosphere good for work\n"
            "• Dedicated seating area\n"
            "• Open until 8 PM\n"
            "• Rating: 4.5★ based on 200+ reviews",
            title="Final Recommendation",
            border_style="green",
        )
    )

    # Show action summary
    console.print("\n[bold]ReAct Summary:[/bold]")
    console.print("• Total cycles: 4")
    console.print("• Actions taken: search, filter, review, details")
    console.print("• Information gathered: location, amenities, reviews, hours")
    console.print("• Confidence: High (multiple data sources)")


async def pattern_comparison():
    """Compare all three patterns on the same problem."""
    console.print("\n[bold magenta]📊 Pattern Comparison[/bold magenta]\n")

    problem = "How can a small restaurant increase revenue by 20%?"

    console.print(Panel(problem, title="Business Problem", border_style="yellow"))

    # Results for each pattern
    results = []

    # Chain of Thought
    console.print("\n[bold]1. Chain of Thought Approach:[/bold]")
    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), transient=True
    ) as progress:
        task = progress.add_task("Analyzing step by step...", total=None)
        await asyncio.sleep(1)

    console.print("   → Analyzed current revenue: $50k/month")
    console.print("   → Calculated target: $60k/month")
    console.print("   → Identified key levers: prices, customers, frequency")
    console.print("   → Computed scenarios for 20% increase")
    console.print("   [green]✓ Systematic analysis completed[/green]")
    results.append(("Chain of Thought", 0.85, 1.2, "Raise prices 10% + add delivery"))

    # Tree of Thoughts
    console.print("\n[bold]2. Tree of Thoughts Approach:[/bold]")
    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), transient=True
    ) as progress:
        task = progress.add_task("Exploring multiple strategies...", total=None)
        await asyncio.sleep(1.5)

    console.print("   → Path A: Premium menu items (score: 0.75)")
    console.print("   → Path B: Catering services (score: 0.82)")
    console.print("   → Path C: Extended hours (score: 0.68)")
    console.print("   → Path D: Loyalty program (score: 0.78)")
    console.print("   [green]✓ Best path identified: Catering[/green]")
    results.append(("Tree of Thoughts", 0.82, 1.8, "Launch catering + loyalty program"))

    # ReAct
    console.print("\n[bold]3. ReAct Approach:[/bold]")
    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), transient=True
    ) as progress:
        task = progress.add_task("Researching and analyzing...", total=None)
        await asyncio.sleep(1.3)

    console.print("   → Researched competitor strategies")
    console.print("   → Analyzed local market data")
    console.print("   → Calculated demand elasticity")
    console.print("   → Tested assumptions with data")
    console.print("   [green]✓ Data-driven solution found[/green]")
    results.append(("ReAct", 0.88, 1.5, "Delivery + dynamic pricing + events"))

    # Comparison table
    console.print("\n[bold]Pattern Comparison Results:[/bold]")

    table = Table(title="Performance Metrics")
    table.add_column("Pattern", style="cyan")
    table.add_column("Confidence", justify="right", style="green")
    table.add_column("Time (s)", justify="right")
    table.add_column("Solution", style="yellow")

    for pattern, conf, time, solution in results:
        table.add_row(pattern, f"{conf:.0%}", f"{time:.1f}", solution)

    console.print(table)

    # Pattern characteristics
    console.print("\n[bold]Pattern Characteristics:[/bold]")

    characteristics = {
        "Chain of Thought": "✓ Systematic, ✓ Reliable, ✗ May miss creative options",
        "Tree of Thoughts": "✓ Explores options, ✓ Creative, ✗ Takes longer",
        "ReAct": "✓ Data-driven, ✓ Adaptive, ✗ Needs external info",
    }

    for pattern, chars in characteristics.items():
        console.print(f"\n[cyan]{pattern}:[/cyan] {chars}")


async def main():
    """Run all demonstrations."""
    console.print(
        Panel(
            "[bold green]AgentiCraft Reasoning Patterns Demo[/bold green]\n\n"
            "This demo shows how each reasoning pattern works conceptually\n"
            "without requiring any API keys or external services.\n\n"
            "Watch how each pattern approaches problems differently!",
            title="Welcome to Reasoning Patterns v0.2.0",
            border_style="green",
        )
    )

    demos = [
        ("Chain of Thought", demo_chain_of_thought),
        ("Tree of Thoughts", demo_tree_of_thoughts),
        ("ReAct Pattern", demo_react_pattern),
        ("Pattern Comparison", pattern_comparison),
    ]

    for name, demo_func in demos:
        console.print(f"\n{'='*70}")
        await demo_func()

        if name != "Pattern Comparison":
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()

    # Summary
    console.print("\n" + "=" * 70)
    console.print(
        Panel(
            "[bold green]✨ Demo Complete![/bold green]\n\n"
            "You've seen how each reasoning pattern works:\n\n"
            "• [cyan]Chain of Thought[/cyan]: Step-by-step linear reasoning\n"
            "• [cyan]Tree of Thoughts[/cyan]: Explores multiple solution paths\n"
            "• [cyan]ReAct[/cyan]: Combines thinking with actions\n\n"
            "To see these patterns work with real LLMs:\n"
            "1. Set your API keys (OpenAI/Anthropic)\n"
            "2. Run the other examples in this directory\n\n"
            "Happy reasoning! 🎉",
            title="Next Steps",
            border_style="green",
        )
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
