#!/usr/bin/env python3
"""Production-ready reasoning with handler approach.

This example shows how to implement reasoning patterns in production
using the handler pattern that avoids tool decorator issues.
"""

import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import track
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


# Production-ready pattern selector
class ReasoningPattern(Enum):
    """Available reasoning patterns."""

    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    REACT = "react"


@dataclass
class ReasoningContext:
    """Context for reasoning operations."""

    problem: str
    pattern: ReasoningPattern
    max_steps: int = 10
    confidence_threshold: float = 0.7
    metadata: dict[str, Any] = None
    tools: dict[str, Callable] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tools is None:
            self.tools = {}


class ReasoningHandler:
    """Production handler for reasoning patterns."""

    def __init__(self, name: str = "ReasoningHandler"):
        self.name = name
        self.history: list[dict[str, Any]] = []
        self.context_store: dict[str, Any] = {}

    async def reason(self, context: ReasoningContext) -> dict[str, Any]:
        """Execute reasoning based on pattern."""
        start_time = datetime.now()

        # Select appropriate reasoning method
        if context.pattern == ReasoningPattern.CHAIN_OF_THOUGHT:
            result = await self._chain_of_thought(context)
        elif context.pattern == ReasoningPattern.TREE_OF_THOUGHTS:
            result = await self._tree_of_thoughts(context)
        elif context.pattern == ReasoningPattern.REACT:
            result = await self._react_pattern(context)
        else:
            raise ValueError(f"Unknown pattern: {context.pattern}")

        # Record in history
        self.history.append(
            {
                "timestamp": start_time,
                "pattern": context.pattern.value,
                "problem": context.problem,
                "result": result,
                "duration": (datetime.now() - start_time).total_seconds(),
            }
        )

        return result

    async def _chain_of_thought(self, context: ReasoningContext) -> dict[str, Any]:
        """Chain of Thought implementation."""
        steps = []
        current_confidence = 1.0

        # Simulate step-by-step reasoning
        reasoning_steps = [
            ("Understand the problem", 0.95),
            ("Identify key components", 0.90),
            ("Apply domain knowledge", 0.85),
            ("Develop solution approach", 0.88),
            ("Validate and conclude", 0.92),
        ]

        for i, (step_desc, confidence) in enumerate(reasoning_steps):
            if i >= context.max_steps:
                break

            current_confidence *= confidence

            steps.append(
                {
                    "step": i + 1,
                    "description": step_desc,
                    "confidence": confidence,
                    "cumulative_confidence": current_confidence,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Store intermediate state
            self.context_store[f"cot_step_{i}"] = step_desc

            await asyncio.sleep(0.1)  # Simulate processing

        return {
            "pattern": "chain_of_thought",
            "steps": steps,
            "final_confidence": current_confidence,
            "solution": "Step-by-step analysis completed with high confidence",
            "reasoning_trace": self._generate_cot_trace(steps),
        }

    async def _tree_of_thoughts(self, context: ReasoningContext) -> dict[str, Any]:
        """Tree of Thoughts implementation."""
        tree = {"root": {"thought": "Initial analysis", "score": 1.0, "children": []}}

        # Simulate tree exploration
        branches = [
            {"name": "Approach A", "score": 0.82, "depth": 1},
            {"name": "Approach B", "score": 0.78, "depth": 1},
            {"name": "Approach C", "score": 0.85, "depth": 1},
        ]

        best_score = 0
        best_path = []

        for branch in branches:
            # Explore deeper
            sub_branches = [
                {
                    "name": f"{branch['name']}.1",
                    "score": branch["score"] * 0.9,
                    "depth": 2,
                },
                {
                    "name": f"{branch['name']}.2",
                    "score": branch["score"] * 1.1,
                    "depth": 2,
                },
            ]

            for sub in sub_branches:
                if sub["score"] > best_score:
                    best_score = sub["score"]
                    best_path = [branch["name"], sub["name"]]

            await asyncio.sleep(0.1)

        return {
            "pattern": "tree_of_thoughts",
            "tree_stats": {
                "total_nodes": len(branches) * 3,
                "max_depth": 2,
                "branches_explored": len(branches),
            },
            "best_path": best_path,
            "best_score": best_score,
            "solution": f"Optimal approach found: {' → '.join(best_path)}",
            "alternatives": self._get_alternatives(branches),
        }

    async def _react_pattern(self, context: ReasoningContext) -> dict[str, Any]:
        """ReAct pattern implementation."""
        cycles = []
        observations = {}

        # Define available actions
        actions = {
            "analyze": self._analyze_action,
            "calculate": self._calculate_action,
            "research": self._research_action,
            "validate": self._validate_action,
        }

        # Execute ReAct cycles
        for i in range(min(5, context.max_steps)):
            # Thought phase
            thought = f"Analyzing aspect {i+1} of the problem"

            # Action selection (simplified)
            action_name = list(actions.keys())[i % len(actions)]
            action_func = actions[action_name]

            # Execute action
            observation = await action_func(context.problem)
            observations[action_name] = observation

            cycles.append(
                {
                    "cycle": i + 1,
                    "thought": thought,
                    "action": action_name,
                    "observation": observation,
                    "confidence": 0.8 + (i * 0.03),
                }
            )

            await asyncio.sleep(0.1)

        return {
            "pattern": "react",
            "cycles": cycles,
            "observations": observations,
            "total_actions": len(cycles),
            "solution": "Data-driven solution based on observations",
            "insights": self._synthesize_observations(observations),
        }

    # Helper methods for actions
    async def _analyze_action(self, data: str) -> str:
        """Analyze action for ReAct."""
        return f"Analysis reveals key patterns in: {data[:50]}..."

    async def _calculate_action(self, data: str) -> str:
        """Calculate action for ReAct."""
        return "Calculations show positive ROI with 85% confidence"

    async def _research_action(self, data: str) -> str:
        """Research action for ReAct."""
        return "Research indicates 3 viable approaches"

    async def _validate_action(self, data: str) -> str:
        """Validate action for ReAct."""
        return "Validation confirms initial hypothesis"

    # Utility methods
    def _generate_cot_trace(self, steps: list[dict]) -> str:
        """Generate a reasoning trace for Chain of Thought."""
        trace = []
        for step in steps:
            trace.append(
                f"{step['step']}. {step['description']} (confidence: {step['confidence']:.2f})"
            )
        return " → ".join(trace)

    def _get_alternatives(self, branches: list[dict]) -> list[dict]:
        """Get alternative paths from tree exploration."""
        return [
            {"path": b["name"], "score": b["score"], "rank": i + 1}
            for i, b in enumerate(
                sorted(branches, key=lambda x: x["score"], reverse=True)
            )
        ]

    def _synthesize_observations(self, observations: dict[str, str]) -> list[str]:
        """Synthesize insights from observations."""
        return [
            f"Key finding from {action}: {obs.split(':')[1] if ':' in obs else obs}"
            for action, obs in observations.items()
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get handler statistics."""
        if not self.history:
            return {"total_reasonings": 0}

        pattern_counts = {}
        total_duration = 0

        for entry in self.history:
            pattern = entry["pattern"]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            total_duration += entry["duration"]

        return {
            "total_reasonings": len(self.history),
            "patterns_used": pattern_counts,
            "average_duration": total_duration / len(self.history),
            "last_reasoning": self.history[-1]["timestamp"],
        }


class PatternSelector:
    """Intelligent pattern selector for production use."""

    def __init__(self):
        self.selection_rules = {
            "keywords": {
                ReasoningPattern.CHAIN_OF_THOUGHT: [
                    "calculate",
                    "compute",
                    "step",
                    "prove",
                    "derive",
                    "explain",
                    "analyze",
                    "break down",
                    "sequence",
                ],
                ReasoningPattern.TREE_OF_THOUGHTS: [
                    "design",
                    "create",
                    "optimize",
                    "compare",
                    "explore",
                    "alternatives",
                    "options",
                    "strategies",
                    "approaches",
                ],
                ReasoningPattern.REACT: [
                    "find",
                    "search",
                    "current",
                    "latest",
                    "research",
                    "investigate",
                    "gather",
                    "validate",
                    "check",
                ],
            },
            "problem_types": {
                "mathematical": ReasoningPattern.CHAIN_OF_THOUGHT,
                "creative": ReasoningPattern.TREE_OF_THOUGHTS,
                "research": ReasoningPattern.REACT,
                "analytical": ReasoningPattern.CHAIN_OF_THOUGHT,
                "strategic": ReasoningPattern.TREE_OF_THOUGHTS,
                "investigative": ReasoningPattern.REACT,
            },
        }

    def select_pattern(
        self, problem: str, hints: dict[str, Any] = None
    ) -> ReasoningPattern:
        """Select the best reasoning pattern for a problem."""
        problem_lower = problem.lower()
        scores = dict.fromkeys(ReasoningPattern, 0)

        # Score based on keywords
        for pattern, keywords in self.selection_rules["keywords"].items():
            for keyword in keywords:
                if keyword in problem_lower:
                    scores[pattern] += 1

        # Consider hints if provided
        if hints:
            if "problem_type" in hints:
                suggested = self.selection_rules["problem_types"].get(
                    hints["problem_type"]
                )
                if suggested:
                    scores[suggested] += 3

            if "preferred_pattern" in hints:
                try:
                    preferred = ReasoningPattern(hints["preferred_pattern"])
                    scores[preferred] += 5
                except ValueError:
                    pass

        # Select pattern with highest score
        best_pattern = max(scores, key=scores.get)

        # Default to Chain of Thought if no clear winner
        if scores[best_pattern] == 0:
            best_pattern = ReasoningPattern.CHAIN_OF_THOUGHT

        return best_pattern


# Example: Customer Support System
async def customer_support_example():
    """Production example: Intelligent customer support."""
    console.print(
        "\n[bold cyan]Production Example: Customer Support System[/bold cyan]\n"
    )

    handler = ReasoningHandler("CustomerSupport")
    selector = PatternSelector()

    # Customer queries
    queries = [
        {
            "id": "TICKET-001",
            "query": "My subscription payment failed but I was still charged. Please help!",
            "category": "billing",
            "priority": "high",
        },
        {
            "id": "TICKET-002",
            "query": "How can I optimize my workflow to be more productive with your tool?",
            "category": "usage",
            "priority": "medium",
        },
        {
            "id": "TICKET-003",
            "query": "What's the best plan for a team of 50 people with advanced needs?",
            "category": "sales",
            "priority": "high",
        },
    ]

    console.print("Processing customer queries...\n")

    for query_data in queries:
        console.print(f"[bold]Ticket {query_data['id']}:[/bold] {query_data['query']}")

        # Select appropriate pattern
        hints = {
            "problem_type": (
                "analytical" if query_data["category"] == "billing" else "strategic"
            )
        }
        pattern = selector.select_pattern(query_data["query"], hints)
        console.print(f"[dim]Selected pattern: {pattern.value}[/dim]")

        # Create context
        context = ReasoningContext(
            problem=query_data["query"], pattern=pattern, metadata=query_data
        )

        # Process with handler
        result = await handler.reason(context)

        # Display response
        console.print(
            Panel(
                f"Solution: {result['solution']}\n\n"
                f"Confidence: {result.get('final_confidence', result.get('best_score', 0.85)):.0%}\n"
                f"Pattern: {result['pattern']}",
                title=f"Response for {query_data['id']}",
                border_style="green",
            )
        )
        console.print()

    # Show statistics
    stats = handler.get_statistics()
    console.print("[bold]Support System Statistics:[/bold]")
    console.print(f"• Total tickets processed: {stats['total_reasonings']}")
    console.print(f"• Average response time: {stats['average_duration']:.2f}s")
    console.print(f"• Patterns used: {stats['patterns_used']}")


# Example: Code Review Assistant
async def code_review_example():
    """Production example: Automated code review."""
    console.print(
        "\n[bold cyan]Production Example: Code Review Assistant[/bold cyan]\n"
    )

    handler = ReasoningHandler("CodeReviewer")

    # Code changes to review
    code_changes = [
        {
            "file": "auth.py",
            "type": "security",
            "description": "Added new authentication endpoint",
            "lines_changed": 45,
            "complexity": "high",
        },
        {
            "file": "utils.py",
            "type": "refactor",
            "description": "Optimized data processing functions",
            "lines_changed": 120,
            "complexity": "medium",
        },
    ]

    for change in code_changes:
        console.print(f"\n[bold]Reviewing: {change['file']}[/bold]")
        console.print(f"Type: {change['type']} | Complexity: {change['complexity']}")

        # Select pattern based on review type
        if change["type"] == "security":
            pattern = (
                ReasoningPattern.CHAIN_OF_THOUGHT
            )  # Step-by-step security analysis
        elif change["complexity"] == "high":
            pattern = ReasoningPattern.TREE_OF_THOUGHTS  # Explore multiple concerns
        else:
            pattern = ReasoningPattern.REACT  # Quick validation checks

        context = ReasoningContext(
            problem=f"Review {change['description']} in {change['file']}",
            pattern=pattern,
            metadata=change,
        )

        result = await handler.reason(context)

        # Format review feedback
        review = {
            "status": (
                "approved"
                if result.get("final_confidence", 0.85) > 0.8
                else "needs_changes"
            ),
            "confidence": result.get(
                "final_confidence", result.get("best_score", 0.85)
            ),
            "pattern_used": pattern.value,
            "key_findings": result.get("insights", ["No major issues found"])[:3],
        }

        # Display review
        status_color = "green" if review["status"] == "approved" else "yellow"
        console.print(
            Panel(
                f"Status: [{status_color}]{review['status'].upper()}[/{status_color}]\n"
                f"Confidence: {review['confidence']:.0%}\n\n"
                f"Key Findings:\n"
                + "\n".join(f"• {f}" for f in review["key_findings"]),
                title=f"Code Review: {change['file']}",
                border_style=status_color,
            )
        )


# Example: Data Analysis Pipeline
async def data_analysis_example():
    """Production example: Intelligent data analysis."""
    console.print(
        "\n[bold cyan]Production Example: Data Analysis Pipeline[/bold cyan]\n"
    )

    handler = ReasoningHandler("DataAnalyst")
    selector = PatternSelector()

    # Analysis tasks
    tasks = [
        {
            "name": "Sales Trend Analysis",
            "question": "Calculate the month-over-month growth rate for Q4",
            "data_type": "time_series",
            "complexity": "low",
        },
        {
            "name": "Customer Segmentation",
            "question": "Design optimal customer segments for targeted marketing",
            "data_type": "clustering",
            "complexity": "high",
        },
        {
            "name": "Anomaly Detection",
            "question": "Find unusual patterns in recent transaction data",
            "data_type": "anomaly",
            "complexity": "medium",
        },
    ]

    results_summary = []

    for task in track(tasks, description="Analyzing data..."):
        # Select pattern
        pattern = selector.select_pattern(task["question"])

        # Override for specific data types
        if task["data_type"] == "clustering":
            pattern = ReasoningPattern.TREE_OF_THOUGHTS
        elif task["data_type"] == "anomaly":
            pattern = ReasoningPattern.REACT

        context = ReasoningContext(
            problem=task["question"], pattern=pattern, metadata=task
        )

        result = await handler.reason(context)

        results_summary.append(
            {
                "task": task["name"],
                "pattern": pattern.value,
                "confidence": result.get(
                    "final_confidence", result.get("best_score", 0.85)
                ),
                "key_insight": result["solution"],
            }
        )

    # Display analysis summary
    table = Table(title="Data Analysis Summary")
    table.add_column("Analysis", style="cyan")
    table.add_column("Pattern Used", style="yellow")
    table.add_column("Confidence", justify="right", style="green")
    table.add_column("Key Insight", style="white")

    for summary in results_summary:
        table.add_row(
            summary["task"],
            summary["pattern"].replace("_", " ").title(),
            f"{summary['confidence']:.0%}",
            summary["key_insight"][:40] + "...",
        )

    console.print(table)

    # Performance metrics
    stats = handler.get_statistics()
    console.print("\n[bold]Pipeline Performance:[/bold]")
    console.print(f"• Analyses completed: {stats['total_reasonings']}")
    console.print(f"• Average time per analysis: {stats['average_duration']:.2f}s")
    console.print(f"• Pattern distribution: {stats['patterns_used']}")


# Example: Strategic Decision Support
async def decision_support_example():
    """Production example: Executive decision support."""
    console.print(
        "\n[bold cyan]Production Example: Strategic Decision Support[/bold cyan]\n"
    )

    handler = ReasoningHandler("DecisionSupport")

    decision = {
        "title": "Market Expansion Decision",
        "question": "Should we expand to the European market next quarter?",
        "factors": [
            "Current US market share: 15%",
            "Available budget: $5M",
            "Competition: 3 major players in EU",
            "Regulatory compliance: GDPR ready",
        ],
        "timeline": "Decision needed by end of month",
    }

    console.print(
        Panel(
            f"{decision['question']}\n\n"
            + "Factors:\n"
            + "\n".join(f"• {f}" for f in decision["factors"])
            + f"\n\n{decision['timeline']}",
            title=decision["title"],
            border_style="yellow",
        )
    )

    # Use Tree of Thoughts for strategic decisions
    context = ReasoningContext(
        problem=decision["question"],
        pattern=ReasoningPattern.TREE_OF_THOUGHTS,
        metadata=decision,
        max_steps=10,
    )

    console.print("\n[yellow]Analyzing strategic options...[/yellow]\n")

    result = await handler.reason(context)

    # Display decision tree
    console.print("[bold]Strategic Options Explored:[/bold]")
    for i, alt in enumerate(result["alternatives"], 1):
        console.print(f"{i}. {alt['path']} (score: {alt['score']:.2f})")

    # Final recommendation
    console.print(
        Panel(
            f"**Recommendation:** {result['solution']}\n\n"
            f"**Confidence:** {result['best_score']:.0%}\n\n"
            f"**Rationale:** Based on exploring {result['tree_stats']['branches_explored']} "
            f"strategic options with up to {result['tree_stats']['max_depth']} levels of analysis.\n\n"
            f"**Best Path:** {' → '.join(result['best_path'])}",
            title="Executive Decision",
            border_style="green",
        )
    )


async def main():
    """Run production examples."""
    console.print(
        Panel(
            "[bold green]Production-Ready Reasoning Examples[/bold green]\n\n"
            "These examples demonstrate how to implement reasoning patterns\n"
            "in production systems using the handler approach.\n\n"
            "✓ No tool decorator issues\n"
            "✓ Clean abstraction\n"
            "✓ Easy to test and maintain\n"
            "✓ Extensible design",
            title="AgentiCraft v0.2.0 - Production Patterns",
            border_style="green",
        )
    )

    examples = [
        ("Customer Support System", customer_support_example),
        ("Code Review Assistant", code_review_example),
        ("Data Analysis Pipeline", data_analysis_example),
        ("Strategic Decision Support", decision_support_example),
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

    console.print("\n[bold green]✨ Production examples completed![/bold green]")
    console.print("\n[bold cyan]Key Takeaways:[/bold cyan]")
    console.print("• Use handler pattern for reliable tool integration")
    console.print("• Implement pattern selection based on problem characteristics")
    console.print("• Track metrics for continuous improvement")
    console.print("• Design for extensibility and maintainability")
    console.print("• Consider hybrid approaches for complex problems")


if __name__ == "__main__":
    asyncio.run(main())
