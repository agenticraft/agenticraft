#!/usr/bin/env python3
"""Tree of Thoughts reasoning examples.

This example demonstrates Tree of Thoughts pattern with proper error handling
and graceful fallback when APIs are unavailable.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

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


class ThoughtNode:
    """Represents a node in the thought tree."""

    def __init__(
        self, thought: str, score: float = 0.5, parent: Optional["ThoughtNode"] = None
    ):
        self.thought = thought
        self.score = score
        self.parent = parent
        self.children: list[ThoughtNode] = []
        self.depth = 0 if parent is None else parent.depth + 1

    def add_child(self, thought: str, score: float) -> "ThoughtNode":
        child = ThoughtNode(thought, score, self)
        self.children.append(child)
        return child

    def get_path(self) -> list["ThoughtNode"]:
        """Get path from root to this node."""
        path = []
        node = self
        while node:
            path.append(node)
            node = node.parent
        return list(reversed(path))


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


async def mock_tree_exploration(
    problem: str, max_depth: int = 3, beam_width: int = 3
) -> dict[str, Any]:
    """Mock tree exploration when no API is available."""
    # Create mock tree based on problem type
    root = ThoughtNode("Initial problem analysis", 1.0)

    # Simulate exploration
    await asyncio.sleep(1)

    if "design" in problem.lower() or "create" in problem.lower():
        # Creative problem tree
        path1 = root.add_child("User-centered approach", 0.85)
        path1.add_child("Research user needs", 0.88)
        path1.add_child("Iterative prototyping", 0.82)

        path2 = root.add_child("Technology-first approach", 0.72)
        path2.add_child("Leverage latest tech", 0.75)
        path2.add_child("Build MVP quickly", 0.70)

        path3 = root.add_child("Hybrid approach", 0.90)
        path3.add_child("Balance user needs and tech", 0.92)
        path3.add_child("Phased implementation", 0.88)

        best_path = path3.children[-1].get_path()

    elif "optimize" in problem.lower() or "improve" in problem.lower():
        # Optimization problem tree
        path1 = root.add_child("Incremental improvements", 0.75)
        path1.add_child("Fix immediate issues", 0.78)
        path1.add_child("Gradual optimization", 0.73)

        path2 = root.add_child("Complete redesign", 0.68)
        path2.add_child("Start from scratch", 0.65)
        path2.add_child("New architecture", 0.70)

        path3 = root.add_child("Targeted optimization", 0.88)
        path3.add_child("Identify bottlenecks", 0.90)
        path3.add_child("Focus on high impact", 0.85)

        best_path = path3.children[-1].get_path()

    else:
        # General problem tree
        path1 = root.add_child("Analytical approach", 0.80)
        path1.add_child("Break down components", 0.82)
        path1.add_child("Systematic solution", 0.78)

        path2 = root.add_child("Creative approach", 0.75)
        path2.add_child("Think outside the box", 0.77)
        path2.add_child("Novel solutions", 0.73)

        path3 = root.add_child("Practical approach", 0.83)
        path3.add_child("Focus on feasibility", 0.85)
        path3.add_child("Quick wins first", 0.81)

        best_path = path3.children[-1].get_path()

    return {
        "root": root,
        "best_path": best_path,
        "total_nodes": 12,
        "explored_nodes": 12,
        "max_score": best_path[-1].score,
    }


async def creative_design_example():
    """Design something creative using Tree of Thoughts."""
    console.print(
        "\n[bold cyan]Tree of Thoughts: Creative Design Explorer[/bold cyan]\n"
    )

    provider, model = get_provider_config()

    problem = """
    Design an innovative mobile app that helps people build better habits.
    Consider user engagement, behavior psychology, and long-term retention.
    """

    console.print(Panel(problem, title="Design Challenge", border_style="yellow"))

    if provider:
        try:
            from agenticraft.agents.reasoning import ReasoningAgent

            agent = ReasoningAgent(
                name="Designer",
                instructions="Explore creative solutions systematically.",
                reasoning_pattern="tree_of_thoughts",
                pattern_config={
                    "max_depth": 4,
                    "beam_width": 3,
                    "exploration_factor": 0.3,
                    "pruning_threshold": 0.5,
                },
                provider=provider,
                model=model,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Exploring design possibilities...", total=None
                )
                response = await agent.think_and_act(problem)
                progress.update(task, completed=True)

            console.print(
                Panel(
                    response.content,
                    title="Final Design Proposal",
                    border_style="green",
                )
            )

        except Exception as e:
            console.print(f"[yellow]API Error: {e}. Using mock mode.[/yellow]")
            provider = None

    if not provider:
        # Mock exploration
        result = await mock_tree_exploration(problem)

        # Visualize exploration tree
        console.print("\n[bold green]Design Exploration Tree:[/bold green]")
        tree = Tree("🌳 Habit App Design")

        # Add mock exploration paths
        approach1 = tree.add("[green]Gamification Focus[/green] (score: 0.82)")
        approach1.add("↳ Points & rewards system")
        approach1.add("↳ Social competitions")
        approach1.add("↳ Achievement unlocks")

        approach2 = tree.add("[cyan]Psychology-Based[/cyan] (score: 0.88)")
        approach2.add("↳ Habit stacking")
        approach2.add("↳ Trigger-action patterns")
        approach2.add("↳ Positive reinforcement")

        approach3 = tree.add("[yellow]Minimalist Design[/yellow] (score: 0.75)")
        approach3.add("↳ Simple tracking")
        approach3.add("↳ Focus on essentials")
        approach3.add("↳ Distraction-free")

        approach4 = tree.add("[magenta]AI-Powered Coach[/magenta] (score: 0.92) ⭐")
        approach4.add("↳ Personalized insights")
        approach4.add("↳ Adaptive challenges")
        approach4.add("↳ Smart reminders")

        console.print(tree)

        # Best solution
        console.print(
            Panel(
                "**Best Design: AI-Powered Habit Coach**\n\n"
                "Key Features:\n"
                "• **Smart Onboarding**: AI analyzes user goals and suggests optimal habit sequences\n"
                "• **Adaptive Difficulty**: Challenges adjust based on success rate\n"
                "• **Context-Aware Reminders**: Notifications based on location, time, and behavior\n"
                "• **Micro-Habits**: Break big goals into tiny, achievable actions\n"
                "• **Progress Insights**: ML-powered analytics show what works\n\n"
                "Unique Differentiators:\n"
                "• Combines psychology principles with machine learning\n"
                "• Focuses on habit formation science, not just tracking\n"
                "• Personalizes to individual behavior patterns\n\n"
                "Expected Retention: 65% at 6 months (industry avg: 25%)",
                title="Design Recommendation",
                border_style="green",
            )
        )


async def strategic_planning_example():
    """Strategic business planning using Tree of Thoughts."""
    console.print("\n[bold cyan]Tree of Thoughts: Strategic Planning[/bold cyan]\n")

    provider, model = get_provider_config()

    problem = """
    Our SaaS startup needs to expand internationally. We have:
    - $5M funding available
    - Strong product-market fit in the US
    - Team of 25 people
    - $3M ARR growing 100% YoY
    
    Which markets should we enter and how?
    """

    console.print(Panel(problem, title="Strategic Challenge", border_style="yellow"))

    # Strategy exploration paths
    console.print("\n[yellow]Exploring strategic options...[/yellow]\n")

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), transient=True
    ) as progress:
        task = progress.add_task("Analyzing market opportunities...", total=None)
        await asyncio.sleep(2)

    # Create strategy tree
    tree = Tree("🌍 International Expansion Strategy")

    # Region branches
    europe = tree.add("[blue]European Market[/blue] (score: 0.85)")
    europe_uk = europe.add("UK First (score: 0.88)")
    europe_uk.add("• English-speaking")
    europe_uk.add("• Similar regulations")
    europe_uk.add("• £2M investment needed")

    europe_multi = europe.add("Multi-country (score: 0.72)")
    europe_multi.add("• Higher complexity")
    europe_multi.add("• GDPR compliant")
    europe_multi.add("• £3.5M investment")

    asia = tree.add("[yellow]Asian Market[/yellow] (score: 0.78)")
    asia_sing = asia.add("Singapore Hub (score: 0.82)")
    asia_sing.add("• Regional headquarters")
    asia_sing.add("• English + Chinese")
    asia_sing.add("• $2.5M investment")

    asia_japan = asia.add("Japan Direct (score: 0.70)")
    asia_japan.add("• Large market")
    asia_japan.add("• Language barrier")
    asia_japan.add("• $3M investment")

    latam = tree.add("[green]Latin America[/green] (score: 0.73)")
    latam_mexico = latam.add("Mexico First (score: 0.75)")
    latam_mexico.add("• Growing tech scene")
    latam_mexico.add("• Lower costs")
    latam_mexico.add("• $1.5M investment")

    hybrid = tree.add("[magenta]Hybrid Approach[/magenta] (score: 0.91) ⭐")
    hybrid_plan = hybrid.add("UK + Singapore (score: 0.93)")
    hybrid_plan.add("• Cover 2 major regions")
    hybrid_plan.add("• Diversified risk")
    hybrid_plan.add("• $4M total investment")
    hybrid_plan.add("• Phased rollout")

    console.print(tree)

    # Analysis results
    console.print("\n[bold]Market Analysis Summary:[/bold]")

    table = Table()
    table.add_column("Market", style="cyan")
    table.add_column("Opportunity", style="green")
    table.add_column("Challenge", style="yellow")
    table.add_column("Investment", style="magenta")
    table.add_column("Timeline", style="blue")

    markets = [
        ("UK", "Similar market, easy entry", "Brexit complications", "£2M", "6 months"),
        ("Singapore", "APAC gateway", "Cultural adaptation", "$2.5M", "9 months"),
        ("Mexico", "Cost-effective", "Payment infrastructure", "$1.5M", "6 months"),
        ("Hybrid", "Best coverage", "Resource split", "$4M", "12 months"),
    ]

    for market in markets:
        table.add_row(*market)

    console.print(table)

    # Recommendation
    console.print(
        Panel(
            "**Recommended Strategy: Hybrid Approach (UK + Singapore)**\n\n"
            "Phase 1 (Months 1-6): UK Launch\n"
            "• Establish European presence\n"
            "• Hire local team (5-7 people)\n"
            "• Adapt product for UK market\n"
            "• Target £500K ARR by month 6\n\n"
            "Phase 2 (Months 7-12): Singapore Expansion\n"
            "• Set up APAC headquarters\n"
            "• Build regional team (8-10 people)\n"
            "• Localize for SEA markets\n"
            "• Target $750K ARR by month 12\n\n"
            "Success Metrics:\n"
            "• Combined international ARR: $2M+ by Year 1\n"
            "• Market presence in 2 continents\n"
            "• Foundation for further expansion\n\n"
            "Risk Mitigation:\n"
            "• Keep $1M reserve for adjustments\n"
            "• Monthly strategy reviews\n"
            "• Local advisor network",
            title="Strategic Recommendation",
            border_style="green",
        )
    )


async def optimization_example():
    """Optimize a system using Tree of Thoughts exploration."""
    console.print("\n[bold cyan]Tree of Thoughts: System Optimization[/bold cyan]\n")

    problem = """
    Our e-commerce site has performance issues:
    - Page load time: 6 seconds (target: 2 seconds)
    - Server costs: $15K/month
    - Conversion rate: 1.2% (industry avg: 2.5%)
    - Mobile experience rated 3/5 stars
    
    How should we optimize the system?
    """

    console.print(Panel(problem, title="Optimization Challenge", border_style="yellow"))

    console.print("\n[yellow]Exploring optimization paths...[/yellow]\n")

    # Simulate exploration with progress
    steps = [
        "Analyzing current architecture...",
        "Identifying performance bottlenecks...",
        "Evaluating optimization strategies...",
        "Calculating impact and effort...",
        "Selecting optimal approach...",
    ]

    for step in steps:
        console.print(f"→ {step}")
        await asyncio.sleep(0.4)

    # Show exploration results
    console.print("\n[bold green]Optimization Paths Explored:[/bold green]")

    # Create visual comparison
    paths = [
        {
            "name": "Frontend Optimization",
            "score": 0.82,
            "impact": "High",
            "effort": "Low",
            "time": "2 weeks",
            "actions": ["Lazy loading", "Image optimization", "Code splitting"],
        },
        {
            "name": "Backend Rewrite",
            "score": 0.65,
            "impact": "Very High",
            "effort": "Very High",
            "time": "3 months",
            "actions": ["Microservices", "New framework", "Database sharding"],
        },
        {
            "name": "Infrastructure Upgrade",
            "score": 0.78,
            "impact": "High",
            "effort": "Medium",
            "time": "1 month",
            "actions": ["CDN implementation", "Auto-scaling", "Caching layer"],
        },
        {
            "name": "Incremental Improvements",
            "score": 0.88,
            "impact": "High",
            "effort": "Medium",
            "time": "6 weeks",
            "actions": ["Query optimization", "API caching", "Mobile-first CSS"],
        },
    ]

    # Display as cards
    for path in paths:
        status = "⭐ BEST" if path["score"] == 0.88 else ""
        panel = Panel(
            f"Score: {path['score']:.2f} {status}\n"
            f"Impact: {path['impact']} | Effort: {path['effort']}\n"
            f"Timeline: {path['time']}\n\n"
            f"Actions:\n" + "\n".join(f"• {action}" for action in path["actions"]),
            title=path["name"],
            border_style="green" if status else "blue",
        )
        console.print(panel)

    # Final recommendation
    console.print(
        Panel(
            "**Optimization Plan: Incremental Improvements**\n\n"
            "Week 1-2: Quick Wins\n"
            "• Implement Redis caching (−2s load time)\n"
            "• Optimize database queries (−1s load time)\n"
            "• Enable compression (−0.5s load time)\n\n"
            "Week 3-4: Mobile Focus\n"
            "• Responsive redesign\n"
            "• Touch-optimized checkout\n"
            "• Progressive Web App features\n\n"
            "Week 5-6: Performance Polish\n"
            "• CDN for static assets\n"
            "• API response caching\n"
            "• Background job optimization\n\n"
            "Expected Results:\n"
            "✓ Load time: 6s → 2s (67% improvement)\n"
            "✓ Server costs: $15K → $10K (33% reduction)\n"
            "✓ Conversion: 1.2% → 2.0%+ (66% increase)\n"
            "✓ Mobile rating: 3★ → 4.5★\n\n"
            "ROI: 3-month payback period",
            title="Recommended Optimization Strategy",
            border_style="green",
        )
    )


async def comparison_example():
    """Compare multiple options using tree exploration."""
    console.print(
        "\n[bold cyan]Tree of Thoughts: Multi-Option Comparison[/bold cyan]\n"
    )

    problem = """
    Compare three technology stacks for our new project:
    1. Node.js + React + PostgreSQL
    2. Python + Vue + MongoDB  
    3. Go + Angular + MySQL
    
    Consider: performance, scalability, team expertise, and ecosystem.
    """

    console.print(Panel(problem, title="Comparison Task", border_style="yellow"))

    # Evaluation process
    console.print("\n[yellow]Evaluating technology stacks...[/yellow]\n")

    # Create comparison tree
    tree = Tree("🔧 Technology Stack Evaluation")

    # Node.js stack
    node_stack = tree.add("[green]Node.js + React + PostgreSQL[/green]")
    node_perf = node_stack.add("Performance (score: 0.85)")
    node_perf.add("✓ Fast for I/O operations")
    node_perf.add("✓ React virtual DOM")
    node_perf.add("✗ CPU-intensive tasks")

    node_scale = node_stack.add("Scalability (score: 0.88)")
    node_scale.add("✓ Horizontal scaling")
    node_scale.add("✓ Microservices ready")

    node_team = node_stack.add("Team Expertise (score: 0.92)")
    node_team.add("✓ 80% team familiar")
    node_team.add("✓ Large talent pool")

    # Python stack
    python_stack = tree.add("[blue]Python + Vue + MongoDB[/blue]")
    python_perf = python_stack.add("Performance (score: 0.78)")
    python_perf.add("✓ Good for data processing")
    python_perf.add("✗ Slower than compiled languages")

    python_scale = python_stack.add("Scalability (score: 0.82)")
    python_scale.add("✓ MongoDB sharding")
    python_scale.add("? Requires careful design")

    python_team = python_stack.add("Team Expertise (score: 0.75)")
    python_team.add("? 60% team familiar")
    python_team.add("✓ Easy to learn")

    # Go stack
    go_stack = tree.add("[yellow]Go + Angular + MySQL[/yellow]")
    go_perf = go_stack.add("Performance (score: 0.95)")
    go_perf.add("✓ Compiled, very fast")
    go_perf.add("✓ Great concurrency")

    go_scale = go_stack.add("Scalability (score: 0.90)")
    go_scale.add("✓ Built for scale")
    go_scale.add("✓ Efficient resource use")

    go_team = go_stack.add("Team Expertise (score: 0.65)")
    go_team.add("✗ Only 30% familiar")
    go_team.add("✗ Steeper learning curve")

    console.print(tree)

    # Scoring summary
    console.print("\n[bold]Comprehensive Scoring:[/bold]")

    table = Table(title="Technology Stack Comparison")
    table.add_column("Stack", style="cyan")
    table.add_column("Performance", justify="center")
    table.add_column("Scalability", justify="center")
    table.add_column("Team Expertise", justify="center")
    table.add_column("Overall", justify="center", style="green")

    stacks = [
        ("Node.js + React + PostgreSQL", 0.85, 0.88, 0.92, 0.88),
        ("Python + Vue + MongoDB", 0.78, 0.82, 0.75, 0.78),
        ("Go + Angular + MySQL", 0.95, 0.90, 0.65, 0.83),
    ]

    for stack, perf, scale, team, overall in stacks:
        table.add_row(
            stack,
            f"{perf:.2f}",
            f"{scale:.2f}",
            f"{team:.2f}",
            f"{overall:.2f} {'⭐' if overall == 0.88 else ''}",
        )

    console.print(table)

    # Recommendation
    console.print(
        Panel(
            "**Recommendation: Node.js + React + PostgreSQL**\n\n"
            "Rationale:\n"
            "• **Best overall score** (0.88) balancing all factors\n"
            "• **Team expertise** (92%) ensures fast development\n"
            "• **Proven scalability** with successful large-scale apps\n"
            "• **Strong ecosystem** with extensive libraries\n\n"
            "Risk Mitigation:\n"
            "• Use TypeScript for better type safety\n"
            "• Implement worker threads for CPU tasks\n"
            "• Consider Go microservices for performance-critical parts\n\n"
            "Alternative Consideration:\n"
            "If performance is absolutely critical and team can be trained,\n"
            "Go stack would be superior (but requires 2-3 month ramp-up).",
            title="Technology Stack Decision",
            border_style="green",
        )
    )


async def main():
    """Run all Tree of Thoughts examples."""
    console.print(
        Panel(
            "[bold green]Tree of Thoughts Reasoning Examples[/bold green]\n\n"
            "These examples demonstrate exploring multiple solution paths\n"
            "to find the best approach for complex problems.\n\n"
            "Works with real APIs or in mock mode!",
            title="AgentiCraft v0.2.0",
            border_style="green",
        )
    )

    examples = [
        ("Creative Design", creative_design_example),
        ("Strategic Planning", strategic_planning_example),
        ("System Optimization", optimization_example),
        ("Technology Comparison", comparison_example),
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
    console.print("\n[bold cyan]Tree of Thoughts Insights:[/bold cyan]")
    console.print("• Explores multiple solution paths simultaneously")
    console.print("• Evaluates and prunes less promising branches")
    console.print("• Finds optimal solutions through systematic exploration")
    console.print("• Best for: design, strategy, optimization, comparison")
    console.print("• Combines breadth and depth of thinking")


if __name__ == "__main__":
    asyncio.run(main())
