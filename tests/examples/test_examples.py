#!/usr/bin/env python3
"""Quick test to verify all reasoning examples work correctly."""

import asyncio
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def check_example(name: str, module_path: str) -> dict:
    """Check a single example module."""
    result = {
        "name": name,
        "module": module_path,
        "status": "❌ Failed",
        "error": None,
        "has_main": False,
    }

    try:
        # Check if file exists
        if not Path(module_path).exists():
            result["error"] = "File not found"
            return result

        # Try to import and check for main
        import importlib.util

        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)

        # Check if module has main function
        spec.loader.exec_module(module)
        if hasattr(module, "main"):
            result["has_main"] = True
            # Don't actually run main during test
            result["status"] = "✅ Ready"
        else:
            result["error"] = "No main() function"

    except Exception as e:
        result["error"] = str(e)[:50]

    return result


async def run_tests():
    """Test all reasoning examples."""
    console.print(
        Panel(
            "[bold green]Testing Reasoning Examples[/bold green]\n\n"
            "This will verify that all example files are properly structured\n"
            "and ready to run. It won't execute the examples fully.",
            title="AgentiCraft Reasoning Test Suite",
            border_style="green",
        )
    )

    # Load environment variables
    try:
        from dotenv import find_dotenv, load_dotenv

        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path)
            console.print(f"[dim]Loaded .env from: {dotenv_path}[/dim]")
    except ImportError:
        pass

    # Define examples to test
    base_path = Path(__file__).parent
    examples = [
        ("Simple Demo (No API)", "reasoning_demo.py"),
        ("Chain of Thought", "chain_of_thought.py"),
        ("Tree of Thoughts", "tree_of_thoughts.py"),
        ("ReAct Pattern", "react.py"),
        ("Pattern Comparison", "pattern_comparison.py"),
        ("Production Handlers", "production_handlers.py"),
        ("Reasoning Transparency", "reasoning_transparency.py"),
    ]

    # Test each example
    results = []
    for name, filename in examples:
        filepath = base_path / filename
        result = await check_example(name, str(filepath))
        results.append(result)

    # Display results
    table = Table(title="Test Results")
    table.add_column("Example", style="cyan")
    table.add_column("File", style="yellow")
    table.add_column("Status", justify="center")
    table.add_column("Notes", style="dim")

    all_passed = True
    for result in results:
        notes = ""
        if result["error"]:
            notes = result["error"]
            all_passed = False
        elif not result["has_main"]:
            notes = "No main() function"
        else:
            notes = "Ready to run"

        table.add_row(
            result["name"], Path(result["module"]).name, result["status"], notes
        )

    console.print("\n")
    console.print(table)

    # Summary
    if all_passed:
        console.print("\n[bold green]✅ All examples are ready to run![/bold green]")
        console.print("\nTo run an example:")
        console.print("  python reasoning_demo.py        # No API needed")
        console.print("  python chain_of_thought.py      # Needs API key")
    else:
        console.print("\n[bold red]❌ Some examples have issues.[/bold red]")
        console.print("Please check the errors above.")

    # Check environment
    console.print("\n[bold]Environment Check:[/bold]")
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY") is not None,
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY") is not None,
    }

    for key, is_set in api_keys.items():
        status = "✅ Set" if is_set else "❌ Not set"
        console.print(f"  {key}: {status}")

    if not any(api_keys.values()):
        console.print(
            "\n[yellow]Note: No API keys found. Examples will run in mock mode.[/yellow]"
        )
        console.print("This is fine for testing - all examples support mock mode!")

    # Import check
    console.print("\n[bold]Import Check:[/bold]")
    try:
        import agenticraft

        console.print("  ✅ AgentiCraft is installed")
    except ImportError:
        console.print("  ❌ AgentiCraft not found")
        console.print("  Install with: pip install -e /path/to/agenticraft")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_tests())

    sys.exit(0 if success else 1)