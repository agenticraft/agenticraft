"""
Templates command - Manage AgentiCraft templates.
"""

from pathlib import Path

import click

from .new import AVAILABLE_TEMPLATES


@click.group()
def templates():
    """Manage AgentiCraft templates."""
    pass


@templates.command()
def list():
    """List available templates."""
    click.echo("Available AgentiCraft templates:\n")

    for name, description in AVAILABLE_TEMPLATES.items():
        # Check if template exists
        template_path = _get_template_path(name)
        status = "✓" if template_path.exists() else "✗"

        click.echo(f"  {status} {name:12} - {description}")

    click.echo(
        "\nUse 'agenticraft new <project> --template <name>' to create a project"
    )


@templates.command()
@click.argument("name")
def info(name: str):
    """Show information about a template."""
    if name not in AVAILABLE_TEMPLATES:
        click.echo(f"Error: Unknown template '{name}'", err=True)
        click.echo(f"Available templates: {', '.join(AVAILABLE_TEMPLATES.keys())}")
        raise click.Abort()

    template_path = _get_template_path(name)

    if not template_path.exists():
        click.echo(f"Error: Template '{name}' not installed", err=True)
        raise click.Abort()

    click.echo(f"Template: {name}")
    click.echo(f"Description: {AVAILABLE_TEMPLATES[name]}")
    click.echo(f"Location: {template_path}")

    # Show README preview if available
    readme_path = template_path / "README.md"
    if readme_path.exists():
        click.echo("\nREADME Preview:")
        click.echo("-" * 50)

        # Show first 20 lines
        with open(readme_path) as f:
            lines = f.readlines()[:20]
            for line in lines:
                click.echo(line.rstrip())

        if len(lines) == 20:
            click.echo("...")
            click.echo(f"\nFull README at: {readme_path}")


@templates.command()
@click.argument("url")
@click.option("--name", help="Template name (default: derived from URL)")
def install(url: str, name: str):
    """Install a template from a URL or GitHub repo."""
    click.echo("Template installation coming soon!")
    click.echo(f"Would install: {url}")
    if name:
        click.echo(f"As: {name}")


def _get_template_path(name: str) -> Path:
    """Get the path to a template directory."""
    # First, check if we're in development mode
    dev_templates = Path(__file__).parent.parent.parent.parent / "templates"
    if dev_templates.exists():
        return dev_templates / name

    # Otherwise, check installed templates
    import agenticraft

    package_path = Path(agenticraft.__file__).parent
    return package_path / "templates" / name
