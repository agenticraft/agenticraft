#!/usr/bin/env python3
"""ReAct pattern examples using handler approach.

This example demonstrates the ReAct pattern without @tool decorator issues,
using handlers and mock tools for reliable operation.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
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


# Tool implementations as regular functions (no decorators)
def web_search(query: str) -> str:
    """Search the web for information."""
    # Simulated search results
    results = {
        "weather": f"Weather search for '{query}': Current conditions show 72°F, partly cloudy with 10% chance of rain.",
        "restaurant": f"Restaurant search for '{query}': Found 15 highly-rated options within 1 mile. Top pick: 'The Garden Bistro' (4.8★)",
        "market": f"Market analysis for '{query}': Industry growing at 12% annually, key players include A, B, and C.",
        "tech": f"Technology search for '{query}': Latest developments include AI advances and cloud adoption trends.",
        "price": f"Price check for '{query}': Current market price ranges from $45-$65 depending on specifications.",
    }

    # Match query to result type
    query_lower = query.lower()
    for key in results:
        if key in query_lower:
            return results[key]

    return f"Search results for '{query}': Found relevant information across multiple sources."


def analyze_data(data: str, metric: str = "general") -> str:
    """Analyze data and provide insights."""
    analyses = {
        "performance": f"Performance analysis of {data}: Efficiency at 87%, with optimization opportunities in areas X and Y.",
        "financial": f"Financial analysis of {data}: ROI of 23%, break-even in 14 months, strong growth indicators.",
        "user": f"User analysis of {data}: Engagement up 34%, retention at 78%, satisfaction score 4.2/5.",
        "market": f"Market analysis of {data}: 15% market share, positioned #3 in segment, growth potential high.",
        "general": f"Analysis of {data}: Key insights reveal positive trends with actionable improvements identified.",
    }

    return analyses.get(metric, analyses["general"])


def calculate(expression: str) -> str:
    """Perform calculations safely."""
    try:
        # Safe evaluation
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "len": len,
        }
        # Clean the expression
        expr_clean = expression.strip()
        result = eval(expr_clean, {"__builtins__": {}}, allowed_names)
        return f"Calculation result: {expression} = {result}"
    except Exception as e:
        return f"Calculation error: Could not evaluate '{expression}' - {str(e)}"


def check_database(query: str, table: str = "data") -> str:
    """Query database for information."""
    mock_data = {
        "users": "Database query result: 1,247 active users, 89% retention rate, average session 12 minutes.",
        "sales": "Database query result: Total sales $458K this quarter, up 23% YoY, 342 transactions.",
        "inventory": "Database query result: 1,893 items in stock, 12 items low stock alert, 98.5% availability.",
        "metrics": "Database query result: System uptime 99.9%, response time 145ms avg, error rate 0.02%.",
    }

    for key in mock_data:
        if key in query.lower() or key in table.lower():
            return mock_data[key]

    return f"Database query on table '{table}': Returned 42 rows matching criteria '{query}'."


# Tool wrapper for handler approach
class ToolHandler:
    """Handler for tool execution in ReAct pattern."""

    def __init__(self):
        self.tools = {
            "web_search": web_search,
            "analyze_data": analyze_data,
            "calculate": calculate,
            "check_database": check_database,
        }
        self.execution_history = []

    def execute(self, tool_name: str, **kwargs) -> str:
        """Execute a tool with given parameters."""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"

        try:
            result = self.tools[tool_name](**kwargs)
            self.execution_history.append(
                {
                    "tool": tool_name,
                    "params": kwargs,
                    "result": result,
                    "timestamp": datetime.now(),
                }
            )
            return result
        except Exception as e:
            return f"Tool error: {str(e)}"

    def get_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions of available tools."""
        return {
            "web_search": "Search the web for any information",
            "analyze_data": "Analyze data and provide insights",
            "calculate": "Perform mathematical calculations",
            "check_database": "Query database for specific information",
        }


async def research_task_example():
    """Research using ReAct pattern with tool handlers."""
    console.print("\n[bold cyan]ReAct Pattern: Research Assistant[/bold cyan]\n")

    task = "Find the best laptop for data science work under $2000"
    console.print(Panel(task, title="Research Task", border_style="yellow"))

    tool_handler = ToolHandler()

    # Simulate ReAct cycles
    cycles = []

    console.print("\n[yellow]Starting ReAct reasoning cycles...[/yellow]\n")

    # Cycle 1: Initial search
    console.print("[bold]Cycle 1:[/bold]")
    console.print(
        "💭 [cyan]Thought:[/cyan] I need to search for data science laptop recommendations"
    )
    await asyncio.sleep(0.5)

    console.print(
        "⚡ [yellow]Action:[/yellow] web_search('best laptops data science 2024 under $2000')"
    )
    result1 = tool_handler.execute(
        "web_search", query="best laptops data science 2024 under $2000"
    )
    await asyncio.sleep(0.5)

    console.print(f"👁️  [green]Observation:[/green] {result1}\n")
    cycles.append(("search", result1))

    # Cycle 2: Check specifications
    console.print("[bold]Cycle 2:[/bold]")
    console.print(
        "💭 [cyan]Thought:[/cyan] I should check specific requirements for data science work"
    )
    await asyncio.sleep(0.5)

    console.print(
        "⚡ [yellow]Action:[/yellow] analyze_data('laptop specs for data science', 'performance')"
    )
    result2 = tool_handler.execute(
        "analyze_data", data="laptop specs for data science", metric="performance"
    )
    await asyncio.sleep(0.5)

    console.print(f"👁️  [green]Observation:[/green] {result2}\n")
    cycles.append(("analyze", result2))

    # Cycle 3: Calculate value
    console.print("[bold]Cycle 3:[/bold]")
    console.print(
        "💭 [cyan]Thought:[/cyan] Let me calculate price-performance ratio for top options"
    )
    await asyncio.sleep(0.5)

    console.print(
        "⚡ [yellow]Action:[/yellow] calculate('1800 / 16')"
    )  # Price per GB RAM
    result3 = tool_handler.execute("calculate", expression="1800 / 16")
    await asyncio.sleep(0.5)

    console.print(f"👁️  [green]Observation:[/green] {result3}\n")
    cycles.append(("calculate", result3))

    # Cycle 4: Final check
    console.print("[bold]Cycle 4:[/bold]")
    console.print("💭 [cyan]Thought:[/cyan] I should verify availability and reviews")
    await asyncio.sleep(0.5)

    console.print(
        "⚡ [yellow]Action:[/yellow] check_database('laptop reviews', 'products')"
    )
    result4 = tool_handler.execute(
        "check_database", query="laptop reviews", table="products"
    )
    await asyncio.sleep(0.5)

    console.print(f"👁️  [green]Observation:[/green] {result4}\n")
    cycles.append(("database", result4))

    # Final recommendation
    console.print(
        Panel(
            "🎯 **Recommendation: Dell XPS 15 (2024 Model)**\n\n"
            "Based on my research:\n"
            "• Price: $1,799 (within budget)\n"
            "• Specs: Intel i7, 16GB RAM, 512GB SSD, NVIDIA GPU\n"
            "• Perfect for: Python, R, machine learning workloads\n"
            "• Battery: 10+ hours for coding\n"
            '• Display: 15.6" 4K, great for data visualization\n\n'
            "Alternative: ThinkPad P15 Gen 2 at $1,899 for better Linux support",
            title="Research Conclusion",
            border_style="green",
        )
    )

    # Summary
    console.print("\n[bold]ReAct Summary:[/bold]")
    console.print(f"• Total cycles: {len(cycles)}")
    console.print(f"• Tools used: {', '.join(set(c[0] for c in cycles))}")
    console.print("• Confidence: High (multiple data sources consulted)")


async def troubleshooting_example():
    """Troubleshoot issues using ReAct pattern."""
    console.print("\n[bold cyan]ReAct Pattern: System Troubleshooter[/bold cyan]\n")

    problem = "Website loading time increased from 2s to 8s since yesterday"
    console.print(Panel(problem, title="Problem Report", border_style="yellow"))

    tool_handler = ToolHandler()

    # Diagnostic process
    console.print("\n[yellow]Initiating diagnostic process...[/yellow]\n")

    steps = [
        {
            "thought": "I need to check current system metrics",
            "action": (
                "check_database",
                {"query": "system metrics", "table": "monitoring"},
            ),
            "insight": "High response times confirmed",
        },
        {
            "thought": "Let me analyze server performance data",
            "action": (
                "analyze_data",
                {"data": "server performance logs", "metric": "performance"},
            ),
            "insight": "CPU usage normal, possible I/O bottleneck",
        },
        {
            "thought": "I should search for similar issues and solutions",
            "action": (
                "web_search",
                {"query": "website slow loading database bottleneck solutions"},
            ),
            "insight": "Database query optimization needed",
        },
        {
            "thought": "Let me calculate the impact of unoptimized queries",
            "action": ("calculate", {"expression": "8 - 2"}),
            "insight": "6 second delay is critical",
        },
    ]

    for i, step in enumerate(steps, 1):
        console.print(f"[bold]Diagnostic Step {i}:[/bold]")
        console.print(f"💭 [cyan]Thought:[/cyan] {step['thought']}")

        action_name, params = step["action"]
        console.print(
            f"⚡ [yellow]Action:[/yellow] {action_name}({', '.join(f'{k}={v}' for k, v in params.items())})"
        )

        result = tool_handler.execute(action_name, **params)
        console.print(f"👁️  [green]Observation:[/green] {result}")
        console.print(f"💡 [magenta]Insight:[/magenta] {step['insight']}\n")

        await asyncio.sleep(0.5)

    # Diagnosis and solution
    console.print(
        Panel(
            "🔧 **Root Cause: Unoptimized Database Queries**\n\n"
            "Diagnosis:\n"
            "• Several queries missing indexes (detected in logs)\n"
            "• N+1 query problem in user dashboard\n"
            "• Cache invalidation causing repeated queries\n\n"
            "Immediate Actions:\n"
            "1. Add indexes to user_activities table\n"
            "2. Implement query result caching\n"
            "3. Batch dashboard queries\n\n"
            "Expected Result: Loading time back to 2-3 seconds",
            title="Diagnosis & Solution",
            border_style="green",
        )
    )


async def data_analysis_example():
    """Analyze business data using ReAct pattern."""
    console.print("\n[bold cyan]ReAct Pattern: Data Analyst[/bold cyan]\n")

    task = "Analyze our Q4 performance and identify growth opportunities"
    console.print(Panel(task, title="Analysis Task", border_style="yellow"))

    tool_handler = ToolHandler()

    # Analysis cycles
    console.print("\n[yellow]Performing data analysis...[/yellow]\n")

    # Create analysis flow
    analysis_flow = [
        (
            "Revenue Analysis",
            "check_database",
            {"query": "Q4 sales revenue", "table": "sales"},
        ),
        (
            "Market Comparison",
            "web_search",
            {"query": "SaaS industry Q4 2024 growth rates"},
        ),
        (
            "Performance Metrics",
            "analyze_data",
            {"data": "Q4 business metrics", "metric": "financial"},
        ),
        (
            "Growth Calculation",
            "calculate",
            {"expression": "458 * 1.23"},
        ),  # Next quarter projection
        (
            "User Insights",
            "analyze_data",
            {"data": "user behavior Q4", "metric": "user"},
        ),
    ]

    results = {}

    for step_name, tool, params in analysis_flow:
        console.print(f"[bold]{step_name}:[/bold]")
        result = tool_handler.execute(tool, **params)
        results[step_name] = result
        console.print(f"→ {result}\n")
        await asyncio.sleep(0.3)

    # Create summary table
    table = Table(title="Q4 Performance Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Trend", style="yellow")

    table.add_row("Revenue", "$458K", "↑ 23%")
    table.add_row("User Growth", "1,247 active", "↑ 34%")
    table.add_row("Retention", "89%", "↑ 5%")
    table.add_row("Market Position", "#3", "→ Stable")

    console.print(table)

    # Growth opportunities
    console.print(
        Panel(
            "📈 **Growth Opportunities Identified:**\n\n"
            "1. **Geographic Expansion** (High Impact)\n"
            "   - Current: 85% US-based\n"
            "   - Opportunity: European market entry\n"
            "   - Potential: +40% revenue\n\n"
            "2. **Product Upsell** (Medium Impact)\n"
            "   - Current: 23% on premium tier\n"
            "   - Opportunity: Feature bundling\n"
            "   - Potential: +$15K MRR\n\n"
            "3. **Partnership Channel** (Medium Impact)\n"
            "   - Current: 100% direct sales\n"
            "   - Opportunity: Integration partners\n"
            "   - Potential: +30% user acquisition\n\n"
            "Recommended Focus: Geographic expansion with localized features",
            title="Strategic Recommendations",
            border_style="green",
        )
    )


async def decision_support_example():
    """Support decision making with ReAct pattern."""
    console.print("\n[bold cyan]ReAct Pattern: Decision Support System[/bold cyan]\n")

    decision = "Should we migrate from AWS to Google Cloud? Budget: $50K/month"
    console.print(Panel(decision, title="Decision Required", border_style="yellow"))

    tool_handler = ToolHandler()

    # Decision analysis process
    console.print("\n[yellow]Analyzing decision factors...[/yellow]\n")

    # Gather information
    factors = {
        "Cost Analysis": await mock_react_cycle(
            tool_handler,
            "I need to compare cloud provider costs",
            "calculate",
            {"expression": "50000 * 0.85"},  # Potential savings
            "15% cost reduction possible with GCP",
        ),
        "Technical Review": await mock_react_cycle(
            tool_handler,
            "I should analyze technical requirements",
            "analyze_data",
            {"data": "cloud migration requirements", "metric": "performance"},
            "Migration complexity: moderate",
        ),
        "Market Research": await mock_react_cycle(
            tool_handler,
            "Let me research migration experiences",
            "web_search",
            {"query": "AWS to GCP migration case studies 2024"},
            "Mixed results, 70% satisfaction rate",
        ),
        "Risk Assessment": await mock_react_cycle(
            tool_handler,
            "I need to check our current usage patterns",
            "check_database",
            {"query": "AWS service usage", "table": "infrastructure"},
            "Heavy reliance on AWS-specific services",
        ),
    }

    # Decision matrix
    console.print("\n[bold]Decision Analysis Matrix:[/bold]")

    table = Table()
    table.add_column("Factor", style="cyan")
    table.add_column("Stay with AWS", style="green")
    table.add_column("Migrate to GCP", style="yellow")
    table.add_column("Impact", style="magenta")

    matrix = [
        ("Cost", "$50K/month", "$42.5K/month", "High"),
        ("Migration Effort", "None", "3-6 months", "High"),
        ("Team Training", "None", "Required", "Medium"),
        ("Service Parity", "100%", "85%", "High"),
        ("Support Quality", "Excellent", "Good", "Medium"),
        ("Future Flexibility", "Limited", "Better", "Low"),
    ]

    for row in matrix:
        table.add_row(*row)

    console.print(table)

    # Recommendation
    console.print(
        Panel(
            "🎯 **Recommendation: Stay with AWS (for now)**\n\n"
            "Reasoning:\n"
            "• Cost savings (15%) don't justify migration risks\n"
            "• Heavy AWS service dependencies increase complexity\n"
            "• 3-6 month migration timeline impacts roadmap\n"
            "• Team retraining costs offset savings\n\n"
            "Alternative Approach:\n"
            "1. Optimize current AWS usage first (-10% possible)\n"
            "2. Gradually adopt cloud-agnostic services\n"
            "3. Revisit migration in 12 months\n"
            "4. Consider multi-cloud for specific workloads\n\n"
            "Confidence: 78% (based on data analysis)",
            title="Decision Recommendation",
            border_style="green",
        )
    )


async def mock_react_cycle(
    tool_handler: ToolHandler, thought: str, tool: str, params: dict, insight: str
) -> str:
    """Execute a single ReAct cycle."""
    console.print(f"💭 {thought}")
    result = tool_handler.execute(tool, **params)
    console.print(f"→ {insight}\n")
    await asyncio.sleep(0.3)
    return result


async def main():
    """Run all ReAct examples."""
    console.print(
        Panel(
            "[bold green]ReAct Pattern Examples[/bold green]\n\n"
            "These examples demonstrate the ReAct (Reason + Act) pattern\n"
            "using handler approach to avoid tool decorator issues.\n\n"
            "All examples work without API keys using mock tools!",
            title="AgentiCraft v0.2.0",
            border_style="green",
        )
    )

    examples = [
        ("Research Task", research_task_example),
        ("System Troubleshooting", troubleshooting_example),
        ("Data Analysis", data_analysis_example),
        ("Decision Support", decision_support_example),
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
    console.print("\n[bold cyan]Key Insights:[/bold cyan]")
    console.print("• ReAct combines reasoning with tool usage")
    console.print("• Handler approach avoids @tool decorator issues")
    console.print("• Cycles of Thought → Action → Observation")
    console.print("• Best for tasks requiring external information")
    console.print("• Works great for research, troubleshooting, analysis")


if __name__ == "__main__":
    asyncio.run(main())
