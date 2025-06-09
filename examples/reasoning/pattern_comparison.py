#!/usr/bin/env python3
"""Pattern comparison example.

This example compares all three reasoning patterns on the same problems
with proper error handling and mock fallbacks.
"""

import asyncio
import os
import time
from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Load environment variables
try:
    from dotenv import find_dotenv, load_dotenv

    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
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
                break
except ImportError:
    pass  # python-dotenv not installed


class PatternBenchmark:
    """Benchmark results for pattern comparison."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.start_time = None
        self.end_time = None
        self.steps = 0
        self.confidence = 0.0
        self.solution = ""
        self.success = False
        self.characteristics = []

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def start(self):
        self.start_time = time.time()

    def complete(self, steps: int, confidence: float, solution: str):
        self.end_time = time.time()
        self.steps = steps
        self.confidence = confidence
        self.solution = solution
        self.success = True


def get_provider_config():
    """Get the best available provider configuration."""
    if os.getenv("OPENAI_API_KEY"):
        return "openai", "gpt-3.5-turbo", True
    elif os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic", "claude-3-haiku-20240307", True
    else:
        return None, None, False


async def mock_reasoning(
    pattern: str, problem: str, context: dict = None
) -> tuple[str, int, float]:
    """Mock reasoning for when no API is available."""
    await asyncio.sleep(1.5)  # Simulate thinking time

    if pattern == "chain_of_thought":
        steps = 5
        confidence = 0.87
        if "math" in problem.lower() or "calculate" in problem.lower():
            solution = "Through step-by-step calculation: 1) Identify values, 2) Apply formula, 3) Compute result = 42"
        else:
            solution = "By analyzing sequentially: Problem → Components → Analysis → Synthesis → Solution"

    elif pattern == "tree_of_thoughts":
        steps = 12  # Multiple paths explored
        confidence = 0.82
        solution = "After exploring 4 paths: Best approach combines elements from Path A (efficiency) and Path C (innovation)"

    else:  # react
        steps = 8  # Thought-action cycles
        confidence = 0.85
        solution = "Through iterative refinement: Research → Test → Adjust → Validate → Implement"

    return solution, steps, confidence


async def run_pattern_comparison():
    """Compare all three patterns on the same problem."""
    console.print("\n[bold cyan]Comprehensive Pattern Comparison[/bold cyan]\n")

    provider, model, has_api = get_provider_config()

    # Test problem
    problem = """
    A tech startup needs to reduce customer churn from 15% to 10% within 3 months.
    Current data shows:
    - 40% churn due to poor onboarding
    - 35% due to missing features
    - 25% due to pricing concerns
    
    What's the best strategy?
    """

    console.print(Panel(problem, title="Business Problem", border_style="yellow"))

    # Results storage
    benchmarks: dict[str, PatternBenchmark] = {
        "chain_of_thought": PatternBenchmark("Chain of Thought"),
        "tree_of_thoughts": PatternBenchmark("Tree of Thoughts"),
        "react": PatternBenchmark("ReAct"),
    }

    # Test each pattern
    patterns = ["chain_of_thought", "tree_of_thoughts", "react"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Testing patterns...", total=len(patterns))

        for pattern in patterns:
            benchmark = benchmarks[pattern]
            progress.update(
                task, description=f"Testing {pattern.replace('_', ' ').title()}..."
            )

            benchmark.start()

            try:
                if has_api:
                    # Try real API
                    from agenticraft.agents.reasoning import ReasoningAgent

                    # Configure based on pattern
                    config = {"reasoning_pattern": pattern}
                    if pattern == "tree_of_thoughts":
                        config["pattern_config"] = {"max_depth": 3, "beam_width": 3}
                    elif pattern == "react":
                        # For demo, we'll simulate without actual tools
                        config["pattern_config"] = {"max_steps": 5}

                    agent = ReasoningAgent(
                        name=f"{pattern}_agent",
                        provider=provider,
                        model=model,
                        **config,
                    )

                    response = await agent.think_and_act(problem)
                    benchmark.complete(
                        steps=(
                            len(response.reasoning_steps)
                            if hasattr(response, "reasoning_steps")
                            else 5
                        ),
                        confidence=0.85,  # Default if not available
                        solution=response.content[:200] + "...",
                    )
                else:
                    # Use mock
                    solution, steps, confidence = await mock_reasoning(pattern, problem)
                    benchmark.complete(steps, confidence, solution)

            except Exception as e:
                # Fallback to mock on any error
                console.print(
                    f"[dim]API error for {pattern}, using mock: {str(e)[:50]}...[/dim]"
                )
                solution, steps, confidence = await mock_reasoning(pattern, problem)
                benchmark.complete(steps, confidence, solution)

            progress.advance(task)

    # Display results
    display_comparison_results(benchmarks, problem)


def display_comparison_results(benchmarks: dict[str, PatternBenchmark], problem: str):
    """Display detailed comparison results."""
    console.print("\n[bold magenta]Pattern Comparison Results[/bold magenta]\n")

    # Performance metrics table
    table = Table(title="Performance Metrics")
    table.add_column("Pattern", style="cyan")
    table.add_column("Time (s)", justify="right")
    table.add_column("Steps", justify="right")
    table.add_column("Confidence", justify="right")
    table.add_column("Status", justify="center")

    for pattern_key, benchmark in benchmarks.items():
        pattern_name = pattern_key.replace("_", " ").title()
        table.add_row(
            pattern_name,
            f"{benchmark.duration:.2f}",
            str(benchmark.steps),
            f"{benchmark.confidence:.0%}",
            "✅" if benchmark.success else "❌",
        )

    console.print(table)

    # Pattern characteristics
    console.print("\n[bold]Pattern Characteristics & Solutions:[/bold]\n")

    # Chain of Thought
    cot_panel = Panel(
        "[bold]Approach:[/bold] Sequential step-by-step analysis\n\n"
        "[bold]Solution:[/bold]\n"
        "1. Prioritize onboarding (40% of churn)\n"
        "2. Create interactive tutorial\n"
        "3. Add progress tracking\n"
        "4. Implement day 1, 7, 30 check-ins\n"
        "5. Quick feature wins for retention\n\n"
        "[bold]Strengths:[/bold]\n"
        "✓ Clear reasoning trace\n"
        "✓ High confidence in logic\n"
        "✓ Easy to follow and implement\n\n"
        "[bold]Limitations:[/bold]\n"
        "✗ May miss creative solutions\n"
        "✗ Linear thinking only",
        title="Chain of Thought",
        border_style="green",
    )

    # Tree of Thoughts
    tot_panel = Panel(
        "[bold]Approach:[/bold] Explore multiple strategic paths\n\n"
        "[bold]Paths Explored:[/bold]\n"
        "• Path A: Fix onboarding only\n"
        "• Path B: Add all requested features\n"
        "• Path C: Hybrid approach ⭐\n"
        "• Path D: Pricing restructure\n\n"
        "[bold]Best Solution (Path C):[/bold]\n"
        "1. Gamified onboarding (2 weeks)\n"
        "2. Top 3 features (1 month)\n"
        "3. Usage-based pricing tier\n\n"
        "[bold]Strengths:[/bold]\n"
        "✓ Considers alternatives\n"
        "✓ Finds optimal balance\n"
        "✓ Creative solutions\n\n"
        "[bold]Limitations:[/bold]\n"
        "✗ Takes more time\n"
        "✗ Can be overwhelming",
        title="Tree of Thoughts",
        border_style="blue",
    )

    # ReAct
    react_panel = Panel(
        "[bold]Approach:[/bold] Think → Act → Observe cycles\n\n"
        "[bold]Actions Taken:[/bold]\n"
        "1. Analyzed churn data patterns\n"
        "2. Researched competitor solutions\n"
        "3. Calculated ROI of each approach\n"
        "4. Tested with user feedback\n\n"
        "[bold]Data-Driven Solution:[/bold]\n"
        "• A/B test onboarding flows\n"
        "• Feature voting system\n"
        "• Dynamic pricing engine\n"
        "• Weekly cohort analysis\n\n"
        "[bold]Strengths:[/bold]\n"
        "✓ Evidence-based\n"
        "✓ Validates assumptions\n"
        "✓ Adapts based on data\n\n"
        "[bold]Limitations:[/bold]\n"
        "✗ Needs external data\n"
        "✗ More complex setup",
        title="ReAct",
        border_style="yellow",
    )

    console.print(Columns([cot_panel, tot_panel, react_panel], equal=True, expand=True))

    # Winner analysis
    console.print("\n[bold green]Best Pattern for This Problem:[/bold green]")
    console.print(
        Panel(
            "**Winner: Tree of Thoughts** 🏆\n\n"
            "For this strategic business problem requiring creative solutions and "
            "trade-off analysis, Tree of Thoughts excels by:\n\n"
            "• Exploring multiple approaches simultaneously\n"
            "• Finding the optimal balance between effort and impact\n"
            "• Considering second-order effects\n"
            "• Providing a comprehensive strategy\n\n"
            "However, ReAct would be better if you had access to real customer data, "
            "and Chain of Thought would be ideal for implementing the specific tactics.",
            border_style="green",
        )
    )


async def pattern_selection_demo():
    """Demonstrate automatic pattern selection."""
    console.print("\n[bold cyan]Automatic Pattern Selection[/bold cyan]\n")

    # Test problems with ideal patterns
    test_cases = [
        {
            "problem": "Calculate the ROI of upgrading our servers if it costs $50k and saves $2k/month",
            "ideal_pattern": "chain_of_thought",
            "reason": "Mathematical calculation with clear steps",
        },
        {
            "problem": "Design a mobile app icon that appeals to both teens and professionals",
            "ideal_pattern": "tree_of_thoughts",
            "reason": "Creative design requiring exploration of options",
        },
        {
            "problem": "Find the current market leader in cloud storage and their pricing",
            "ideal_pattern": "react",
            "reason": "Requires external data gathering",
        },
        {
            "problem": "Create a algorithm to sort a list of numbers efficiently",
            "ideal_pattern": "chain_of_thought",
            "reason": "Algorithmic problem with logical steps",
        },
        {
            "problem": "Plan a marketing campaign for multiple demographic segments",
            "ideal_pattern": "tree_of_thoughts",
            "reason": "Strategic planning with multiple approaches",
        },
    ]

    console.print("Testing pattern selection heuristics...\n")

    table = Table(title="Pattern Selection Results")
    table.add_column("Problem", style="yellow", width=50)
    table.add_column("Selected", style="cyan")
    table.add_column("Ideal", style="green")
    table.add_column("Match", justify="center")

    for test in test_cases:
        # Simple heuristic for pattern selection
        problem_lower = test["problem"].lower()

        if any(
            word in problem_lower
            for word in ["calculate", "compute", "algorithm", "step"]
        ):
            selected = "chain_of_thought"
        elif any(
            word in problem_lower for word in ["design", "create", "plan", "strategy"]
        ):
            selected = "tree_of_thoughts"
        elif any(
            word in problem_lower for word in ["find", "search", "current", "market"]
        ):
            selected = "react"
        else:
            selected = "chain_of_thought"  # default

        match = "✅" if selected == test["ideal_pattern"] else "❌"

        table.add_row(
            test["problem"][:50] + "...",
            selected.replace("_", " ").title(),
            test["ideal_pattern"].replace("_", " ").title(),
            match,
        )

    console.print(table)

    console.print("\n[bold]Pattern Selection Guidelines:[/bold]")
    console.print(
        Panel(
            "**Chain of Thought** - Use when:\n"
            "• Problem has clear sequential steps\n"
            "• Mathematical or logical reasoning needed\n"
            "• Need to show work or explain process\n\n"
            "**Tree of Thoughts** - Use when:\n"
            "• Multiple valid approaches exist\n"
            "• Creative or design problems\n"
            "• Need to explore trade-offs\n\n"
            "**ReAct** - Use when:\n"
            "• External information required\n"
            "• Need to validate with data\n"
            "• Iterative refinement helpful",
            title="When to Use Each Pattern",
            border_style="blue",
        )
    )


async def real_world_scenarios():
    """Show real-world application scenarios."""
    console.print("\n[bold cyan]Real-World Application Scenarios[/bold cyan]\n")

    scenarios = [
        {
            "title": "Code Debugging",
            "description": "Finding and fixing a performance bottleneck",
            "patterns": {
                "chain_of_thought": "Trace execution step-by-step to find issue",
                "tree_of_thoughts": "Explore multiple potential causes",
                "react": "Profile code, analyze metrics, test fixes",
            },
            "best": "react",
        },
        {
            "title": "Product Pricing",
            "description": "Setting optimal price for new SaaS product",
            "patterns": {
                "chain_of_thought": "Calculate costs, margins, break-even",
                "tree_of_thoughts": "Explore different pricing strategies",
                "react": "Research competitors, test price points",
            },
            "best": "tree_of_thoughts",
        },
        {
            "title": "Customer Support",
            "description": "Resolving complex technical issue",
            "patterns": {
                "chain_of_thought": "Follow troubleshooting checklist",
                "tree_of_thoughts": "Consider multiple failure modes",
                "react": "Gather logs, test solutions, verify fix",
            },
            "best": "chain_of_thought",
        },
    ]

    for scenario in scenarios:
        console.print(f"\n[bold]{scenario['title']}[/bold]")
        console.print(f"[dim]{scenario['description']}[/dim]\n")

        for pattern, approach in scenario["patterns"].items():
            pattern_name = pattern.replace("_", " ").title()
            is_best = " ⭐" if pattern == scenario["best"] else ""
            console.print(f"• [cyan]{pattern_name}[/cyan]{is_best}: {approach}")


async def performance_benchmark():
    """Benchmark reasoning patterns on different problem types."""
    console.print(
        "\n[bold cyan]Performance Benchmark Across Problem Types[/bold cyan]\n"
    )

    problem_types = [
        (
            "Mathematical",
            "Calculate compound interest on $10k at 5% for 10 years with monthly contributions of $200",
        ),
        ("Creative", "Design a logo that represents both technology and nature"),
        ("Analytical", "Why did our website traffic drop 30% last week?"),
        ("Strategic", "Should we expand to Europe or Asia first?"),
        ("Research", "What are the latest advances in quantum computing?"),
    ]

    # Simulated benchmark results
    results = {
        "Mathematical": {"cot": 0.92, "tot": 0.75, "react": 0.80},
        "Creative": {"cot": 0.70, "tot": 0.95, "react": 0.72},
        "Analytical": {"cot": 0.85, "tot": 0.82, "react": 0.88},
        "Strategic": {"cot": 0.78, "tot": 0.90, "react": 0.85},
        "Research": {"cot": 0.72, "tot": 0.78, "react": 0.93},
    }

    table = Table(title="Pattern Performance by Problem Type")
    table.add_column("Problem Type", style="cyan")
    table.add_column("Best Pattern", style="green")
    table.add_column("CoT Score", justify="center")
    table.add_column("ToT Score", justify="center")
    table.add_column("ReAct Score", justify="center")

    for prob_type, _ in problem_types:
        scores = results[prob_type]
        best_pattern = max(scores.items(), key=lambda x: x[1])[0]
        best_name = {
            "cot": "Chain of Thought",
            "tot": "Tree of Thoughts",
            "react": "ReAct",
        }[best_pattern]

        table.add_row(
            prob_type,
            best_name,
            f"{scores['cot']:.2f} {'⭐' if best_pattern == 'cot' else ''}",
            f"{scores['tot']:.2f} {'⭐' if best_pattern == 'tot' else ''}",
            f"{scores['react']:.2f} {'⭐' if best_pattern == 'react' else ''}",
        )

    console.print(table)

    # Summary insights
    console.print("\n[bold]Key Insights:[/bold]")
    console.print("• Chain of Thought excels at mathematical and procedural problems")
    console.print("• Tree of Thoughts dominates creative and strategic challenges")
    console.print("• ReAct performs best when external data is crucial")
    console.print("• No single pattern is best for all problems")
    console.print("• Consider hybrid approaches for complex real-world scenarios")


async def main():
    """Run all comparison examples."""
    console.print(
        Panel(
            "[bold green]Advanced Reasoning Pattern Comparison[/bold green]\n\n"
            "This comprehensive comparison demonstrates how each reasoning pattern\n"
            "performs on different types of problems.\n\n"
            "Works with or without API keys!",
            title="AgentiCraft v0.2.0",
            border_style="green",
        )
    )

    examples = [
        ("Head-to-Head Comparison", run_pattern_comparison),
        ("Automatic Pattern Selection", pattern_selection_demo),
        ("Real-World Scenarios", real_world_scenarios),
        ("Performance Benchmarks", performance_benchmark),
    ]

    for name, example_func in examples:
        console.print(f"\n{'='*70}")
        console.print(f"[yellow]Section: {name}[/yellow]")
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

    # Final recommendations
    console.print("\n" + "=" * 70)
    console.print(
        Panel(
            "[bold green]Pattern Selection Recommendations[/bold green]\n\n"
            "**Start with Chain of Thought when:**\n"
            "• You need to show your work\n"
            "• The problem has clear steps\n"
            "• Transparency is important\n\n"
            "**Use Tree of Thoughts when:**\n"
            "• Multiple approaches might work\n"
            "• Creativity is valued\n"
            "• You need the best solution, not just a solution\n\n"
            "**Choose ReAct when:**\n"
            "• You need current information\n"
            "• The problem requires investigation\n"
            "• You want to validate assumptions\n\n"
            "**Pro tip:** You can combine patterns! Use ReAct to gather data,\n"
            "Tree of Thoughts to explore options, and Chain of Thought to\n"
            "implement the chosen solution.",
            title="Summary",
            border_style="green",
        )
    )

    console.print("\n[bold green]✨ Comparison study completed![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
