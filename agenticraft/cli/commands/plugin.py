"""
Plugin command - Manage AgentiCraft plugins.
"""

from pathlib import Path

import click


@click.group()
def plugin():
    """Manage AgentiCraft plugins."""
    pass


@plugin.command()
def list():
    """List installed plugins."""
    from agenticraft.plugins.registry import PluginRegistry

    registry = PluginRegistry()
    plugins = registry.list_plugins()

    if not plugins:
        click.echo("No plugins installed.")
        click.echo("\nInstall plugins with: agenticraft plugin install <name>")
        return

    click.echo("Installed AgentiCraft plugins:\n")

    for plugin_info in plugins:
        status = "✓" if plugin_info.get("enabled", True) else "✗"
        name = plugin_info["name"]
        version = plugin_info.get("version", "unknown")
        description = plugin_info.get("description", "No description")

        click.echo(f"  {status} {name} v{version}")
        click.echo(f"     {description}")

        # Show what the plugin provides
        provides = []
        if plugin_info.get("tools"):
            provides.append(f"{len(plugin_info['tools'])} tools")
        if plugin_info.get("agents"):
            provides.append(f"{len(plugin_info['agents'])} agents")
        if plugin_info.get("providers"):
            provides.append(f"{len(plugin_info['providers'])} providers")

        if provides:
            click.echo(f"     Provides: {', '.join(provides)}")

        click.echo()


@plugin.command()
@click.argument("name")
def info(name: str):
    """Show detailed information about a plugin."""
    from agenticraft.plugins.registry import PluginRegistry

    registry = PluginRegistry()
    plugin_info = registry.get_plugin_info(name)

    if not plugin_info:
        click.echo(f"Error: Plugin '{name}' not found", err=True)
        raise click.Abort()

    click.echo(f"Plugin: {plugin_info['name']}")
    click.echo(f"Version: {plugin_info.get('version', 'unknown')}")
    click.echo(f"Description: {plugin_info.get('description', 'No description')}")

    if plugin_info.get("author"):
        click.echo(f"Author: {plugin_info['author']}")

    if plugin_info.get("homepage"):
        click.echo(f"Homepage: {plugin_info['homepage']}")

    # Configuration
    if plugin_info.get("config_schema"):
        click.echo("\nConfiguration Schema:")
        import json

        click.echo(json.dumps(plugin_info["config_schema"], indent=2))

    # Tools
    if plugin_info.get("tools"):
        click.echo(f"\nTools ({len(plugin_info['tools'])}):")
        for tool in plugin_info["tools"]:
            click.echo(
                f"  - {tool['name']}: {tool.get('description', 'No description')}"
            )

    # Agents
    if plugin_info.get("agents"):
        click.echo(f"\nAgents ({len(plugin_info['agents'])}):")
        for agent in plugin_info["agents"]:
            click.echo(
                f"  - {agent['name']}: {agent.get('description', 'No description')}"
            )

    # Dependencies
    if plugin_info.get("dependencies"):
        click.echo("\nDependencies:")
        for dep in plugin_info["dependencies"]:
            click.echo(f"  - {dep}")


@plugin.command()
@click.argument("name")
@click.option("--source", help="Plugin source (GitHub URL, PyPI, or local path)")
@click.option("--version", help="Specific version to install")
def install(name: str, source: str | None, version: str | None):
    """Install a plugin."""
    click.echo(f"Installing plugin: {name}")

    if source:
        click.echo(f"From: {source}")
    else:
        click.echo("From: Plugin Hub (default)")

    if version:
        click.echo(f"Version: {version}")

    # TODO: Implement actual plugin installation
    click.echo("\n⚠️  Plugin installation coming soon!")
    click.echo("\nFor now, manually install plugins by:")
    click.echo("1. pip install <plugin-package>")
    click.echo("2. Add to your agent configuration")


@plugin.command()
@click.argument("name")
def uninstall(name: str):
    """Uninstall a plugin."""
    if click.confirm(f"Uninstall plugin '{name}'?"):
        click.echo(f"Uninstalling {name}...")
        # TODO: Implement actual uninstallation
        click.echo("⚠️  Plugin uninstallation coming soon!")


@plugin.command()
@click.argument("name")
def enable(name: str):
    """Enable a plugin."""
    from agenticraft.plugins.registry import PluginRegistry

    registry = PluginRegistry()

    if registry.enable_plugin(name):
        click.echo(f"✓ Plugin '{name}' enabled")
    else:
        click.echo(f"Error: Failed to enable plugin '{name}'", err=True)


@plugin.command()
@click.argument("name")
def disable(name: str):
    """Disable a plugin."""
    from agenticraft.plugins.registry import PluginRegistry

    registry = PluginRegistry()

    if registry.disable_plugin(name):
        click.echo(f"✓ Plugin '{name}' disabled")
    else:
        click.echo(f"Error: Failed to disable plugin '{name}'", err=True)


@plugin.command()
@click.option("--check", is_flag=True, help="Check for updates")
def update(check: bool):
    """Update installed plugins."""
    from agenticraft.plugins.registry import PluginRegistry

    registry = PluginRegistry()
    plugins = registry.list_plugins()

    if not plugins:
        click.echo("No plugins installed.")
        return

    if check:
        click.echo("Checking for plugin updates...")
        # TODO: Implement update checking
        click.echo("⚠️  Update checking coming soon!")
    else:
        click.echo("Updating all plugins...")
        # TODO: Implement plugin updates
        click.echo("⚠️  Plugin updates coming soon!")


@plugin.command()
@click.argument("directory", type=click.Path(exists=True))
def develop(directory: str):
    """Install a plugin in development mode."""
    plugin_path = Path(directory).resolve()

    # Check if it's a valid plugin directory
    if (
        not (plugin_path / "plugin.yaml").exists()
        and not (plugin_path / "pyproject.toml").exists()
    ):
        click.echo("Error: Not a valid plugin directory", err=True)
        click.echo("Plugin directory must contain plugin.yaml or pyproject.toml")
        raise click.Abort()

    click.echo(f"Installing plugin in development mode from: {plugin_path}")

    # TODO: Implement development mode installation
    click.echo("\n⚠️  Development mode coming soon!")
    click.echo("\nFor now, add the plugin directory to your PYTHONPATH")
