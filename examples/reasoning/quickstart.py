#!/usr/bin/env python3
"""Quick start script for reasoning examples.

This script helps you get started with AgentiCraft reasoning patterns quickly.
"""

import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()

# Try to load environment variables
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


def check_environment():
    """Check if environment is properly set up."""
    issues = []

    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(
            "Python 3.8+ required (you have {}.{})".format(*sys.version_info[:2])
        )

    # Check if AgentiCraft is installed
    try:
        import agenticraft

        console.print("✅ AgentiCraft is installed")
    except ImportError:
        issues.append("AgentiCraft not installed")

    # Check for API keys
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

    if has_openai:
        console.print("✅ OpenAI API key found")
    if has_anthropic:
        console.print("✅ Anthropic API key found")

    if not has_openai and not has_anthropic:
        console.print("ℹ️  No API keys found (examples will run in mock mode)")

    return issues


def show_menu():
    """Show interactive menu."""
    console.print("\n[bold cyan]Available Examples:[/bold cyan]\n")

    examples = [
        {
            "name": "Simple Demo (No API Required)",
            "file": "reasoning_demo.py",
            "description": "See all patterns in action without needing API keys",
        },
        {
            "name": "Chain of Thought",
            "file": "chain_of_thought.py",
            "description": "Step-by-step reasoning for math, analysis, and decisions",
        },
        {
            "name": "Tree of Thoughts",
            "file": "tree_of_thoughts.py",
            "description": "Explore multiple paths for creative and strategic problems",
        },
        {
            "name": "ReAct Pattern",
            "file": "react.py",
            "description": "Combine reasoning with tool use for research and analysis",
        },
        {
            "name": "Pattern Comparison",
            "file": "pattern_comparison.py",
            "description": "Compare all patterns on the same problems",
        },
        {
            "name": "Production Examples",
            "file": "production_handlers.py",
            "description": "Real-world applications using handler pattern",
        },
        {
            "name": "Reasoning Transparency",
            "file": "reasoning_transparency.py",
            "description": "See and understand how AI thinks and makes decisions",
        },
    ]

    for i, example in enumerate(examples, 1):
        console.print(f"[bold]{i}.[/bold] {example['name']}")
        console.print(f"   [dim]{example['description']}[/dim]")
        console.print()

    return examples


def run_example(example_file: str):
    """Run a specific example."""
    example_path = Path(__file__).parent / example_file

    if not example_path.exists():
        console.print(f"[red]Error: {example_file} not found![/red]")
        return

    console.print(f"\n[green]Running {example_file}...[/green]\n")
    console.print("-" * 70)

    try:
        subprocess.run([sys.executable, str(example_path)], check=True)
    except subprocess.CalledProcessError:
        console.print("\n[red]Example failed to run properly.[/red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Example interrupted by user.[/yellow]")


def setup_api_key():
    """Help user set up API keys."""
    console.print("\n[bold]API Key Setup[/bold]\n")
    console.print("You can use AgentiCraft with:")
    console.print("1. OpenAI (GPT-3.5/GPT-4)")
    console.print("2. Anthropic (Claude)")
    console.print("3. Ollama (Local models)")
    console.print("4. Mock mode (no API needed)\n")

    choice = Prompt.ask(
        "Which would you like to set up?",
        choices=["1", "2", "3", "4", "skip"],
        default="skip",
    )

    if choice == "1":
        console.print("\n[bold]OpenAI Setup:[/bold]")
        console.print("1. Get your API key from: https://platform.openai.com/api-keys")
        console.print("2. Set environment variable:")
        console.print("   export OPENAI_API_KEY='your-key-here'")
        console.print("   # Or add to your .env file")
    elif choice == "2":
        console.print("\n[bold]Anthropic Setup:[/bold]")
        console.print("1. Get your API key from: https://console.anthropic.com/")
        console.print("2. Set environment variable:")
        console.print("   export ANTHROPIC_API_KEY='your-key-here'")
        console.print("   # Or add to your .env file")
    elif choice == "3":
        console.print("\n[bold]Ollama Setup:[/bold]")
        console.print("1. Install Ollama: https://ollama.ai")
        console.print("2. Pull a model: ollama pull llama2")
        console.print("3. Start Ollama: ollama serve")
        console.print("   (No API key needed!)")
    elif choice == "4":
        console.print("\n[bold]Mock Mode:[/bold]")
        console.print("All examples work without API keys!")
        console.print("They'll use simulated responses that demonstrate the patterns.")


def test_all_examples():
    """Test all example files to ensure they're properly structured."""
    console.print("\n[bold]Testing all examples...[/bold]\n")

    example_files = [
        "reasoning_demo.py",
        "chain_of_thought.py",
        "tree_of_thoughts.py",
        "react.py",
        "pattern_comparison.py",
        "production_handlers.py",
        "reasoning_transparency.py",
    ]

    results = []
    for file in example_files:
        path = Path(__file__).parent / file
        if path.exists():
            # Just check if we can import it
            try:
                # Read first few lines to check for syntax
                with open(path) as f:
                    content = f.read()
                compile(content, file, "exec")
                results.append((file, "✅ Ready"))
            except SyntaxError as e:
                results.append((file, f"❌ Syntax error: {e}"))
            except Exception as e:
                results.append((file, f"⚠️  Warning: {e}"))
        else:
            results.append((file, "❌ Not found"))

    # Display results
    console.print("\n[bold]Test Results:[/bold]")
    for file, status in results:
        console.print(f"  {file:<30} {status}")

    all_ready = all("✅" in status for _, status in results)
    if all_ready:
        console.print("\n[green]✅ All examples are ready to run![/green]")
    else:
        console.print("\n[yellow]⚠️  Some examples need attention[/yellow]")


def main():
    """Main entry point."""
    console.print(
        Panel(
            "[bold green]AgentiCraft Reasoning Examples - Quick Start[/bold green]\n\n"
            "Welcome! This tool helps you explore reasoning patterns:\n"
            "• Chain of Thought - Step-by-step reasoning\n"
            "• Tree of Thoughts - Explore multiple paths\n"
            "• ReAct - Combine thinking with actions",
            title="Welcome to AgentiCraft v0.2.0",
            border_style="green",
        )
    )

    # Check environment
    console.print("\n[bold]Checking environment...[/bold]")
    issues = check_environment()

    if issues:
        console.print("\n[yellow]Setup needed:[/yellow]")
        for issue in issues:
            console.print(f"  ⚠️  {issue}")

        if "AgentiCraft not installed" in issues:
            console.print("\n[bold]To install AgentiCraft:[/bold]")
            console.print("  cd /path/to/agenticraft")
            console.print("  pip install -e .")
            return

    # Main loop
    while True:
        examples = show_menu()

        console.print("[bold]Options:[/bold]")
        console.print("  Enter 1-7 to run an example")
        console.print("  Enter 'setup' to configure API keys")
        console.print("  Enter 'test' to test all examples")
        console.print("  Enter 'quit' to exit\n")

        choice = Prompt.ask("What would you like to do?", default="1")

        if choice.lower() == "quit":
            console.print("\n[green]Thanks for using AgentiCraft![/green]")
            break
        elif choice.lower() == "setup":
            setup_api_key()
        elif choice.lower() == "test":
            test_all_examples()
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(examples):
                    example = examples[idx]
                    run_example(example["file"])
                else:
                    console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                console.print("[red]Invalid choice. Please try again.[/red]")

        if not Confirm.ask("\n[bold]Run another example?[/bold]", default=True):
            break

    console.print("\n[dim]Tip: You can also run examples directly:[/dim]")
    console.print("[dim]  python reasoning_demo.py[/dim]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if os.getenv("DEBUG"):
            import traceback

            traceback.print_exc()
