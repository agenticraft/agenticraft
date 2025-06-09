#!/usr/bin/env python3
"""
Working reasoning pattern examples for AgentiCraft v0.2.0
These examples demonstrate all three reasoning patterns with proper tool integration.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print("⚠️  No .env file found. Please create one from .env.example")

# Import AgentiCraft components
# Rich console for better output
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from agenticraft.agents.reasoning import ReasoningAgent
from agenticraft.core.tool import BaseTool, ToolDefinition

console = Console()


# === Tool Implementations for ReAct Pattern ===


class WebSearchTool(BaseTool):
    """Web search tool for ReAct pattern."""

    name = "web_search"
    description = "Search the web for information"

    async def arun(self, query: str) -> str:
        """Simulate web search."""
        # In production, this would use a real search API
        await asyncio.sleep(0.5)  # Simulate API delay

        # Return contextual results based on query
        if "population" in query.lower():
            return f"Search results for '{query}': Tokyo has a population of 13.96 million (2021) in the city proper, with a metropolitan area population of 37.4 million, making it the world's largest urban agglomeration."
        elif "climate" in query.lower():
            return f"Search results for '{query}': Global average temperature has risen by 1.1°C since pre-industrial times. Current projections show 2.7°C warming by 2100 without additional action."
        elif "technology" in query.lower():
            return f"Search results for '{query}': Latest developments include GPT-4, quantum computing breakthroughs, and advances in renewable energy storage."
        else:
            return f"Search results for '{query}': Found relevant information about {query}. Multiple sources confirm the topic's importance and provide detailed analysis."

    def get_definition(self) -> ToolDefinition:
        """Tool definition for LLM."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"],
            },
        )


class CalculatorTool(BaseTool):
    """Calculator tool for ReAct pattern."""

    name = "calculator"
    description = "Perform mathematical calculations"

    async def arun(self, expression: str) -> str:
        """Evaluate mathematical expression."""
        try:
            # Safe evaluation with limited scope
            allowed_names = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "len": len,
                "int": int,
                "float": float,
            }

            # Add math functions
            import math

            for func in ["sqrt", "sin", "cos", "tan", "pi", "e", "log", "exp"]:
                if hasattr(math, func):
                    allowed_names[func] = getattr(math, func)

            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Calculation result: {expression} = {result}"
        except Exception as e:
            return f"Calculation error: {str(e)}"

    def get_definition(self) -> ToolDefinition:
        """Tool definition for LLM."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate",
                    }
                },
                "required": ["expression"],
            },
        )


class DataAnalysisTool(BaseTool):
    """Data analysis tool for ReAct pattern."""

    name = "analyze_data"
    description = "Analyze data and provide statistics"

    async def arun(self, data_type: str, metric: str = "summary") -> str:
        """Analyze data based on type and metric."""
        await asyncio.sleep(0.3)  # Simulate processing

        if data_type == "sales":
            return "Sales Analysis: Q4 revenue up 23% YoY, driven by strong holiday sales. Top products: Electronics (45%), Clothing (30%), Home (25%)."
        elif data_type == "weather":
            return "Weather Analysis: Average temperature 72°F, humidity 65%, precipitation 2.3 inches. Trend: warming by 0.5°F per decade."
        elif data_type == "traffic":
            return "Traffic Analysis: Peak hours 7-9 AM and 5-7 PM. Average delay 12 minutes. Congestion index: 1.4x normal flow."
        else:
            return f"Analysis of {data_type}: Data shows normal distribution with mean at center. Standard deviation within expected range."

    def get_definition(self) -> ToolDefinition:
        """Tool definition for LLM."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to analyze",
                    },
                    "metric": {
                        "type": "string",
                        "description": "Specific metric to calculate",
                        "default": "summary",
                    },
                },
                "required": ["data_type"],
            },
        )


# === Example Functions ===


async def chain_of_thought_example():
    """Demonstrate Chain of Thought reasoning pattern."""
    console.print("\n[bold cyan]🔗 Chain of Thought Example[/bold cyan]")
    console.print("This pattern breaks down complex problems step-by-step\n")

    # Get provider configuration
    provider_name, model = get_provider_config()

    # Create agent with CoT pattern
    agent = ReasoningAgent(
        name="MathTutor",
        instructions="You are a patient math tutor who explains concepts clearly.",
        reasoning_pattern="chain_of_thought",
        pattern_config={"min_confidence": 0.7, "max_steps": 10},
        provider=provider_name,
        model=model,
    )

    problem = """
    A train travels from City A to City B at 60 mph. On the return journey,
    it travels at 40 mph due to bad weather. What is the average speed
    for the entire round trip?
    """

    console.print(Panel(problem, title="Problem", border_style="yellow"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Thinking step by step...", total=None)

        response = await agent.think_and_act(
            problem, context={"subject": "physics", "topic": "average_speed"}
        )

        progress.update(task, completed=True)

    # Display reasoning steps
    if response.reasoning_steps:
        console.print("\n[bold green]Reasoning Steps:[/bold green]")
        for step in response.reasoning_steps:
            console.print(f"\n[cyan]Step {step.number}:[/cyan] {step.description}")
            if step.details:
                for detail in step.details:
                    console.print(f"  • {detail}")
            console.print(f"  [dim]Confidence: {step.confidence:.0%}[/dim]")

    # Display final answer
    console.print(Panel(response.content, title="Solution", border_style="green"))

    # Show reasoning summary if available
    if hasattr(agent, "advanced_reasoning") and agent.advanced_reasoning:
        summary = agent.advanced_reasoning.get_reasoning_summary()
        console.print(
            f"\n[dim]Problem complexity: {summary.get('problem_complexity', 'N/A')}[/dim]"
        )
        console.print(f"[dim]Total steps: {summary.get('total_steps', 0)}[/dim]")


async def tree_of_thoughts_example():
    """Demonstrate Tree of Thoughts reasoning pattern."""
    console.print("\n[bold cyan]🌳 Tree of Thoughts Example[/bold cyan]")
    console.print("This pattern explores multiple solution paths\n")

    provider_name, model = get_provider_config()

    agent = ReasoningAgent(
        name="ProductDesigner",
        instructions="You are a creative product designer who explores multiple innovative approaches.",
        reasoning_pattern="tree_of_thoughts",
        pattern_config={
            "max_depth": 3,
            "beam_width": 3,
            "evaluation_strategy": "balanced",
        },
        provider=provider_name,
        model=model,
    )

    problem = """
    Design a mobile app that helps people reduce their screen time
    while still staying connected with friends and family.
    Consider user engagement, health benefits, and social aspects.
    """

    console.print(Panel(problem, title="Design Challenge", border_style="yellow"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exploring design alternatives...", total=None)

        response = await agent.think_and_act(
            problem,
            context={"target_audience": "adults", "platform": "iOS and Android"},
        )

        progress.update(task, completed=True)

    # Display exploration tree
    if response.reasoning_steps:
        console.print("\n[bold green]Exploration Tree:[/bold green]")

        tree = Tree("🎯 Design Challenge")

        # Group steps by depth (approximation based on step number)
        current_branch = tree
        for step in response.reasoning_steps[:9]:  # Show first 9 steps
            if step.number % 3 == 1:  # New branch every 3 steps
                current_branch = tree.add(f"💡 Path {(step.number // 3) + 1}")

            step_node = current_branch.add(
                f"[cyan]Option:[/cyan] {step.description[:60]}..."
            )
            if step.confidence:
                step_node.add(f"[green]Score: {step.confidence:.2f}[/green]")

        console.print(tree)

    # Display best solution
    console.print(
        Panel(response.content, title="Best Design Approach", border_style="green")
    )


async def react_example():
    """Demonstrate ReAct reasoning pattern with tools."""
    console.print("\n[bold cyan]⚡ ReAct Pattern Example[/bold cyan]")
    console.print("This pattern combines reasoning with tool usage\n")

    provider_name, model = get_provider_config()

    # Create tools
    tools = [WebSearchTool(), CalculatorTool(), DataAnalysisTool()]

    agent = ReasoningAgent(
        name="DataScientist",
        instructions="You are a data scientist who uses tools to gather and analyze information.",
        reasoning_pattern="react",
        pattern_config={"max_steps": 15, "reflection_frequency": 5},
        tools=tools,
        provider=provider_name,
        model=model,
    )

    problem = """
    What is the population density of Tokyo, and how does it compare
    to the average population density of major world cities?
    Calculate the percentage difference.
    """

    console.print(Panel(problem, title="Research Question", border_style="yellow"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Reasoning and acting...", total=None)

        response = await agent.think_and_act(problem)

        progress.update(task, completed=True)

    # Display ReAct process
    if response.reasoning_steps:
        console.print("\n[bold green]ReAct Process:[/bold green]")

        for step in response.reasoning_steps:
            step_type = step.details[0].split(": ")[1] if step.details else "unknown"

            # Use appropriate emoji for step type
            emoji = {
                "thought": "💭",
                "action": "⚡",
                "observation": "👁️",
                "reflection": "🔄",
                "conclusion": "✅",
            }.get(step_type, "•")

            console.print(
                f"\n{emoji} [cyan]Step {step.number}:[/cyan] {step.description}"
            )

            # Show tool usage
            if len(step.details) > 1 and "Tool:" in step.details[1]:
                console.print(f"   🔧 {step.details[1]}")

            console.print(f"   [dim]Confidence: {step.confidence:.0%}[/dim]")

    # Display final answer
    console.print(
        Panel(response.content, title="Research Findings", border_style="green")
    )


async def pattern_comparison_example():
    """Compare all three patterns on the same problem."""
    console.print("\n[bold magenta]🔍 Pattern Comparison[/bold magenta]")
    console.print("Solving the same problem with all three patterns\n")

    provider_name, model = get_provider_config()

    problem = "How can we reduce carbon emissions in urban transportation?"

    console.print(Panel(problem, title="Challenge", border_style="yellow"))

    patterns = [
        ("chain_of_thought", "🔗 Chain of Thought", {}),
        ("tree_of_thoughts", "🌳 Tree of Thoughts", {"max_depth": 2, "beam_width": 2}),
        ("react", "⚡ ReAct", {}),
    ]

    results = []

    for pattern_name, pattern_label, config in patterns:
        console.print(f"\n[bold cyan]{pattern_label}[/bold cyan]")

        # Add tools for ReAct
        tools = [WebSearchTool(), DataAnalysisTool()] if pattern_name == "react" else []

        agent = ReasoningAgent(
            name=f"{pattern_name}_agent",
            reasoning_pattern=pattern_name,
            pattern_config=config,
            tools=tools,
            provider=provider_name,
            model=model,
        )

        start_time = asyncio.get_event_loop().time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Processing with {pattern_label}...", total=None)

            response = await agent.think_and_act(problem)

            progress.update(task, completed=True)

        elapsed = asyncio.get_event_loop().time() - start_time

        # Extract key points
        content_preview = (
            response.content[:150] + "..."
            if len(response.content) > 150
            else response.content
        )

        results.append(
            {
                "pattern": pattern_label,
                "time": elapsed,
                "steps": len(response.reasoning_steps),
                "preview": content_preview,
            }
        )

        console.print(
            f"✓ Completed in {elapsed:.2f}s with {len(response.reasoning_steps)} steps"
        )

    # Display comparison table
    console.print("\n[bold green]Results Comparison:[/bold green]")

    table = Table(title="Pattern Performance")
    table.add_column("Pattern", style="cyan")
    table.add_column("Time (s)", style="yellow")
    table.add_column("Steps", style="green")
    table.add_column("Approach", style="white")

    for result in results:
        table.add_row(
            result["pattern"],
            f"{result['time']:.2f}",
            str(result["steps"]),
            result["preview"],
        )

    console.print(table)


def get_provider_config():
    """Get the best available provider configuration."""
    # Try providers in order of preference
    if os.getenv("OPENAI_API_KEY") or os.getenv("AGENTICRAFT_OPENAI_API_KEY"):
        console.print("[dim]Using OpenAI provider[/dim]")
        return "openai", "gpt-4"
    elif os.getenv("ANTHROPIC_API_KEY") or os.getenv("AGENTICRAFT_ANTHROPIC_API_KEY"):
        console.print("[dim]Using Anthropic provider[/dim]")
        return "anthropic", "claude-3-opus-20240229"
    else:
        # Default to Ollama
        console.print("[dim]Using Ollama provider (local)[/dim]")
        return "ollama", "llama2"


async def main():
    """Run all reasoning pattern examples."""
    console.print(
        "[bold magenta]AgentiCraft Reasoning Patterns Examples[/bold magenta]"
    )
    console.print(
        "Demonstrating Chain of Thought, Tree of Thoughts, and ReAct patterns"
    )
    console.print("=" * 60)

    # Check for API keys
    has_api_key = bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("AGENTICRAFT_OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("AGENTICRAFT_ANTHROPIC_API_KEY")
    )

    if not has_api_key:
        console.print(
            "\n[yellow]⚠️  No API keys found. Will use Ollama (local) provider.[/yellow]"
        )
        console.print("[yellow]   Make sure Ollama is running: ollama serve[/yellow]")
        console.print("[yellow]   And you have a model: ollama pull llama2[/yellow]\n")

        # Check if Ollama is available
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:11434/api/tags", timeout=2.0
                )
                if response.status_code == 200:
                    console.print("[green]✅ Ollama is running[/green]\n")
                else:
                    console.print("[red]❌ Ollama is not responding properly[/red]")
                    return
        except Exception:
            console.print("[red]❌ Ollama is not running. Please start it first.[/red]")
            return

    # Run examples
    examples = [
        ("Chain of Thought", chain_of_thought_example),
        ("Tree of Thoughts", tree_of_thoughts_example),
        ("ReAct Pattern", react_example),
        ("Pattern Comparison", pattern_comparison_example),
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            console.print(f"\n[red]Error in {name}: {str(e)}[/red]")
            import traceback

            if os.getenv("DEBUG"):
                traceback.print_exc()

        # Pause between examples
        if name != examples[-1][0]:
            console.print("\n" + "-" * 60)
            await asyncio.sleep(1)

    console.print("\n" + "=" * 60)
    console.print("[bold green]✨ All examples completed![/bold green]")

    # Show pattern recommendations
    console.print("\n[bold cyan]When to use each pattern:[/bold cyan]")
    console.print(
        "• [cyan]Chain of Thought[/cyan]: Step-by-step problems, calculations, analysis"
    )
    console.print(
        "• [cyan]Tree of Thoughts[/cyan]: Creative tasks, design, multiple solutions"
    )
    console.print("• [cyan]ReAct[/cyan]: Research, data gathering, tool usage required")


if __name__ == "__main__":
    asyncio.run(main())
