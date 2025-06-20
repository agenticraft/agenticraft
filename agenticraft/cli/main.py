"""
AgentiCraft CLI - Command line interface for AgentiCraft.

This module provides the main entry point for the AgentiCraft command-line tool.
"""

import sys

import click

from agenticraft import __version__
from agenticraft.cli.commands import new, plugin, run, templates


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="agenticraft")
@click.pass_context
def cli(ctx):
    """
    AgentiCraft - The AI Agent Framework.

    Build production-ready AI agents with ease.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    # If no command was provided, show a welcome message
    if ctx.invoked_subcommand is None:
        click.echo("AgentiCraft - The AI Agent Framework")
        click.echo("Build production-ready AI agents with ease.")
        click.echo("\nUse 'agenticraft --help' for more information.")


@cli.command()
def version():
    """Show the AgentiCraft version."""
    click.echo(f"AgentiCraft {__version__}")


@cli.command()
def info():
    """Show information about AgentiCraft installation."""
    import os
    import platform

    click.echo(f"AgentiCraft {__version__}")
    click.echo(f"Python {platform.python_version()}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Installation: {os.path.dirname(os.path.dirname(__file__))}")

    # Check available providers
    click.echo("\nAvailable Providers:")
    try:
        from agenticraft.providers import list_providers

        for provider in list_providers():
            click.echo(f"  - {provider}")
    except:
        click.echo("  - Unable to load providers")

    # Check available tools
    click.echo("\nCore Tools:")
    tools = ["search", "calculator", "files", "http", "text"]
    for tool in tools:
        click.echo(f"  - {tool}")


# Add command groups
cli.add_command(new.new)
cli.add_command(run.run)
cli.add_command(templates.templates)
cli.add_command(plugin.plugin)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
