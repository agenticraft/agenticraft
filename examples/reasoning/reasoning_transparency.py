#!/usr/bin/env python3
"""Reasoning Transparency - Understanding How Agents Think

This example showcases AgentiCraft's reasoning transparency features,
allowing you to see and understand the agent's thought process.
"""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

console = Console()

# Load environment variables
try:
    from dotenv import find_dotenv, load_dotenv

    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
except ImportError:
    pass


# Mock tools for demonstration
def search_knowledge(query: str) -> str:
    """Search internal knowledge base for information."""
    knowledge = {
        "renewable energy": {
            "types": ["solar", "wind", "hydro", "geothermal", "biomass"],
            "benefits": "Clean, sustainable, reduces carbon emissions",
            "challenges": "Intermittency, storage, initial costs",
        },
        "building efficiency": {
            "strategies": [
                "insulation",
                "smart HVAC",
                "LED lighting",
                "energy monitoring",
            ],
            "savings": "20-40% energy reduction possible",
            "roi": "Typically 3-7 years",
        },
        "sustainability metrics": {
            "kpis": ["energy use intensity", "carbon footprint", "water usage"],
            "standards": ["LEED", "Energy Star", "BREEAM"],
        },
    }

    for key, data in knowledge.items():
        if key in query.lower():
            return str(data)
    return "No specific data found, using general knowledge."


def calculate_savings(
    current_usage: float, reduction_percent: float, cost_per_kwh: float = 0.12
) -> dict:
    """Calculate energy and cost savings."""
    savings_kwh = current_usage * (reduction_percent / 100)
    new_usage = current_usage - savings_kwh
    cost_savings = savings_kwh * cost_per_kwh

    return {
        "current_usage_kwh": current_usage,
        "reduction_percent": reduction_percent,
        "savings_kwh": savings_kwh,
        "new_usage_kwh": new_usage,
        "annual_cost_savings": cost_savings,
        "payback_years": None,  # Would need investment cost
    }


def environmental_impact(kwh_saved: float) -> dict:
    """Calculate environmental impact of energy savings."""
    # EPA estimates: 0.92 lbs CO2 per kWh
    co2_reduced_lbs = kwh_saved * 0.92
    co2_reduced_tons = co2_reduced_lbs / 2000

    # Equivalencies
    trees_equivalent = co2_reduced_tons * 16.5  # Trees needed to absorb same CO2
    cars_removed = co2_reduced_tons / 4.6  # Average car emits 4.6 tons/year

    return {
        "co2_reduced_lbs": co2_reduced_lbs,
        "co2_reduced_tons": co2_reduced_tons,
        "equivalent_trees": round(trees_equivalent),
        "equivalent_cars_removed": round(cars_removed, 1),
    }


async def chain_of_thought_transparency():
    """Demonstrate Chain of Thought reasoning transparency."""
    console.print("\n[bold cyan]Example 1: Chain of Thought Transparency[/bold cyan]")
    console.print("-" * 60)

    query = """
    My office building uses 50,000 kWh annually. 
    What efficiency improvements should I prioritize, and what would be 
    the environmental impact of a 30% reduction?
    """

    console.print(Panel(query.strip(), title="Query", border_style="yellow"))

    # Simulate reasoning trace
    reasoning_steps = [
        {
            "step": 1,
            "description": "Understanding the problem",
            "thought": "Building uses 50,000 kWh/year, need efficiency improvements and impact of 30% reduction",
            "confidence": 0.95,
        },
        {
            "step": 2,
            "description": "Searching for efficiency strategies",
            "action": "search_knowledge('building efficiency')",
            "observation": str(search_knowledge("building efficiency")),
            "confidence": 0.88,
        },
        {
            "step": 3,
            "description": "Calculating potential savings",
            "action": "calculate_savings(50000, 30)",
            "observation": str(calculate_savings(50000, 30)),
            "confidence": 0.92,
        },
        {
            "step": 4,
            "description": "Assessing environmental impact",
            "action": "environmental_impact(15000)",
            "observation": str(environmental_impact(15000)),
            "confidence": 0.90,
        },
    ]

    # Display reasoning trace
    console.print("\n[bold green]🧠 Reasoning Trace:[/bold green]")

    for step in reasoning_steps:
        console.print(f"\n[cyan]Step {step['step']}:[/cyan] {step['description']}")
        if "thought" in step:
            console.print(f"💭 Thought: {step['thought']}")
        if "action" in step:
            console.print(f"⚡ Action: [yellow]{step['action']}[/yellow]")
        if "observation" in step:
            console.print(f"👁️  Observation: [dim]{step['observation'][:100]}...[/dim]")
        console.print(f"📊 Confidence: {step['confidence']:.0%}")

    # Show how to access reasoning programmatically
    console.print("\n[bold]Accessing Reasoning Programmatically:[/bold]")
    code = """
# With AgentiCraft agent
response = agent.run(query)

# Access reasoning trace
for step in response.reasoning_trace.steps:
    print(f"Step {step.number}: {step.description}")
    print(f"Confidence: {step.confidence}")
    if step.tool_used:
        print(f"Tool: {step.tool_used}")
"""
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)


async def tree_of_thoughts_transparency():
    """Demonstrate Tree of Thoughts reasoning transparency."""
    console.print("\n\n[bold cyan]Example 2: Tree of Thoughts Transparency[/bold cyan]")
    console.print("-" * 60)

    query = "We need to reduce our carbon footprint by 50% in 5 years. What are the possible strategies?"

    console.print(Panel(query, title="Query", border_style="yellow"))

    # Create tree visualization
    console.print("\n[bold green]🌳 Thought Tree Exploration:[/bold green]\n")

    tree = Tree("🎯 Reduce Carbon Footprint 50%")

    # Branch 1: Energy
    energy = tree.add("⚡ Energy Efficiency (Score: 8.5/10)")
    energy.add("LED lighting conversion")
    energy.add("HVAC optimization")
    energy.add("Smart building systems")
    energy.add("[green]✓ HIGH IMPACT[/green]")

    # Branch 2: Renewable
    renewable = tree.add("☀️ Renewable Energy (Score: 9.2/10)")
    renewable.add("Solar panel installation")
    renewable.add("Green energy contracts")
    renewable.add("On-site generation")
    renewable.add("[green]✓ BEST PATH[/green]")

    # Branch 3: Operations
    operations = tree.add("🏢 Operational Changes (Score: 7.0/10)")
    operations.add("Remote work policies")
    operations.add("Supply chain optimization")
    operations.add("Waste reduction")
    operations.add("[yellow]○ MODERATE IMPACT[/yellow]")

    console.print(tree)

    # Show branch evaluation
    console.print("\n[bold]Branch Evaluation Details:[/bold]")

    branches = [
        {
            "name": "Energy Efficiency",
            "score": 8.5,
            "cost": "Medium",
            "timeline": "1-2 years",
            "selected": False,
        },
        {
            "name": "Renewable Energy",
            "score": 9.2,
            "cost": "High",
            "timeline": "2-3 years",
            "selected": True,
        },
        {
            "name": "Operational Changes",
            "score": 7.0,
            "cost": "Low",
            "timeline": "6 months",
            "selected": False,
        },
    ]

    table = Table(title="Strategy Evaluation")
    table.add_column("Strategy", style="cyan")
    table.add_column("Score", justify="center")
    table.add_column("Cost", justify="center")
    table.add_column("Timeline", justify="center")
    table.add_column("Selected", justify="center")

    for branch in branches:
        table.add_row(
            branch["name"],
            f"{branch['score']}/10",
            branch["cost"],
            branch["timeline"],
            "✓" if branch["selected"] else "",
        )

    console.print(table)


async def react_transparency():
    """Demonstrate ReAct reasoning transparency."""
    console.print("\n\n[bold cyan]Example 3: ReAct Pattern Transparency[/bold cyan]")
    console.print("-" * 60)

    query = "Create an action plan to achieve net-zero emissions for our 500,000 kWh/year facility"

    console.print(Panel(query, title="Query", border_style="yellow"))

    # ReAct cycles
    cycles = [
        {
            "cycle": 1,
            "thought": "Need to understand current energy usage patterns",
            "action": "search_knowledge('sustainability metrics')",
            "observation": "Key metrics: energy use intensity, carbon footprint",
            "reflection": "Should calculate baseline carbon footprint first",
        },
        {
            "cycle": 2,
            "thought": "Calculate current carbon footprint",
            "action": "environmental_impact(500000)",
            "observation": "460,000 lbs CO2/year (230 tons)",
            "reflection": "Need strategies to eliminate 230 tons CO2",
        },
        {
            "cycle": 3,
            "thought": "Find renewable energy options",
            "action": "search_knowledge('renewable energy')",
            "observation": "Solar, wind, hydro options available",
            "reflection": "Solar seems most feasible for facility",
        },
        {
            "cycle": 4,
            "thought": "Calculate solar requirements",
            "action": "calculate_savings(500000, 100)",
            "observation": "Need to offset entire 500,000 kWh",
            "reflection": "Will need ~3,000 solar panels or PPA",
        },
    ]

    console.print("\n[bold green]🔄 ReAct Cycles:[/bold green]")

    for cycle in cycles:
        console.print(f"\n[yellow]Cycle {cycle['cycle']}:[/yellow]")
        console.print(f"💭 Thought: {cycle['thought']}")
        console.print(f"⚡ Action: [cyan]{cycle['action']}[/cyan]")
        console.print(f"👁️  Observation: {cycle['observation']}")
        console.print(f"🔍 Reflection: [dim]{cycle['reflection']}[/dim]")


async def transparency_benefits():
    """Explain the benefits of reasoning transparency."""
    console.print("\n\n[bold cyan]✨ Benefits of Reasoning Transparency[/bold cyan]")
    console.print("-" * 60)

    benefits = [
        {
            "benefit": "Trust & Verification",
            "description": "Users can verify the logic behind AI recommendations",
            "example": "See exactly why the AI recommended solar over wind energy",
        },
        {
            "benefit": "Debugging & Improvement",
            "description": "Identify where reasoning goes wrong and fix it",
            "example": "Notice if the AI misunderstood requirements or made calculation errors",
        },
        {
            "benefit": "Learning & Education",
            "description": "Understand how AI approaches different problems",
            "example": "Learn problem-solving strategies from the AI's approach",
        },
        {
            "benefit": "Compliance & Auditing",
            "description": "Document decision-making process for regulatory requirements",
            "example": "Show auditors how AI arrived at financial recommendations",
        },
        {
            "benefit": "Prompt Engineering",
            "description": "Refine prompts based on observed reasoning patterns",
            "example": "Adjust instructions when AI takes inefficient reasoning paths",
        },
    ]

    for item in benefits:
        console.print(f"\n[bold green]{item['benefit']}[/bold green]")
        console.print(f"{item['description']}")
        console.print(f"[dim]Example: {item['example']}[/dim]")


async def implementation_guide():
    """Show how to implement reasoning transparency."""
    console.print("\n\n[bold cyan]📚 Implementation Guide[/bold cyan]")
    console.print("-" * 60)

    console.print("\n[bold]1. Enable Reasoning in Your Agent:[/bold]")
    code1 = """
from agenticraft import Agent
from agenticraft.reasoning import ChainOfThoughtReasoning

agent = Agent(
    name="TransparentAgent",
    reasoning_strategy=ChainOfThoughtReasoning(
        show_steps=True,
        track_confidence=True
    )
)
"""
    console.print(Syntax(code1, "python", theme="monokai"))

    console.print("\n[bold]2. Access Reasoning Trace:[/bold]")
    code2 = """
response = agent.run("Your query here")

# Get full reasoning trace
reasoning = response.reasoning_trace

# Access specific steps
for step in reasoning.steps:
    print(f"Step {step.number}: {step.description}")
    print(f"Tools used: {step.tools}")
    print(f"Confidence: {step.confidence}")
"""
    console.print(Syntax(code2, "python", theme="monokai"))

    console.print("\n[bold]3. Visualize Reasoning:[/bold]")
    code3 = """
# For Tree of Thoughts
if hasattr(reasoning, 'tree'):
    for branch in reasoning.tree.branches:
        print(f"Branch: {branch.name} (Score: {branch.score})")
        
# For ReAct
if hasattr(reasoning, 'cycles'):
    for cycle in reasoning.cycles:
        print(f"Thought: {cycle.thought}")
        print(f"Action: {cycle.action}")
        print(f"Result: {cycle.observation}")
"""
    console.print(Syntax(code3, "python", theme="monokai"))


async def main():
    """Run all reasoning transparency examples."""
    console.print(
        Panel(
            "[bold green]Reasoning Transparency Examples[/bold green]\n\n"
            "See how agents think! These examples show how to access and\n"
            "understand the reasoning process behind AI decisions.\n\n"
            "This builds trust, enables debugging, and helps you understand\n"
            "how AI solves problems.",
            title="AgentiCraft v0.2.0 - Reasoning Transparency",
            border_style="green",
        )
    )

    examples = [
        ("Chain of Thought Transparency", chain_of_thought_transparency),
        ("Tree of Thoughts Transparency", tree_of_thoughts_transparency),
        ("ReAct Pattern Transparency", react_transparency),
        ("Benefits of Transparency", transparency_benefits),
        ("Implementation Guide", implementation_guide),
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            console.print(f"[red]Error in {name}: {e}[/red]")

    console.print("\n\n[bold green]✅ Key Takeaways:[/bold green]")
    console.print("• Reasoning transparency builds trust with users")
    console.print("• Access detailed step-by-step thought processes")
    console.print("• Debug and improve AI reasoning")
    console.print("• Enable compliance and auditing")
    console.print("• Learn from AI problem-solving approaches")

    console.print("\n[dim]Note: These examples show simulated reasoning traces.")
    console.print("With actual API keys, you'll see real AI reasoning in action![/dim]")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
