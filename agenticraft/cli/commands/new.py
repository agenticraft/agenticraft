"""
New command - Create new AgentiCraft projects from templates.
"""

import shutil
from pathlib import Path

import click

AVAILABLE_TEMPLATES = {
    "fastapi": "Production-ready REST API with agents",
    "cli": "Command-line application with agents",
    "bot": "Multi-platform bot template",
    "mcp-server": "Standalone MCP server",
    "basic": "Minimal agent application",
}


@click.command()
@click.argument("name")
@click.option(
    "--template",
    "-t",
    type=click.Choice(list(AVAILABLE_TEMPLATES.keys())),
    default="basic",
    help="Template to use for the new project",
)
@click.option(
    "--directory",
    "-d",
    type=click.Path(),
    help="Directory to create the project in (default: current directory)",
)
@click.option(
    "--no-git",
    is_flag=True,
    help="Don't initialize a git repository",
)
def new(name: str, template: str, directory: str | None, no_git: bool):
    """
    Create a new AgentiCraft project.

    Example:
        agenticraft new my-api --template fastapi
    """
    # Determine project path
    if directory:
        project_path = Path(directory) / name
    else:
        project_path = Path.cwd() / name

    # Check if directory already exists
    if project_path.exists():
        click.echo(f"Error: Directory '{project_path}' already exists", err=True)
        raise click.Abort()

    # Get template path
    template_path = _get_template_path(template)

    if not template_path.exists():
        click.echo(f"Error: Template '{template}' not found", err=True)
        click.echo(f"Available templates: {', '.join(AVAILABLE_TEMPLATES.keys())}")
        raise click.Abort()

    # Create project directory
    click.echo(f"Creating new {template} project: {name}")
    project_path.mkdir(parents=True, exist_ok=True)

    try:
        # Copy template files
        _copy_template(template_path, project_path, name)

        # Initialize git repository
        if not no_git:
            _init_git(project_path)

        # Update project files with name
        _update_project_files(project_path, name, template)

        # Success message
        click.echo(f"\n✨ Project '{name}' created successfully!")
        click.echo("\nNext steps:")

        # Try to get relative path, but fall back to absolute if not possible
        try:
            display_path = project_path.relative_to(Path.cwd())
        except ValueError:
            # Paths are not relative to each other, use absolute path
            display_path = project_path

        click.echo(f"  cd {display_path}")

        if template == "fastapi":
            click.echo("  cp .env.example .env")
            click.echo("  # Edit .env with your API keys")
            click.echo("  docker-compose up")
        elif template == "cli":
            click.echo("  python -m venv venv")
            click.echo("  source venv/bin/activate")
            click.echo("  pip install -e .")
            click.echo(f"  {name} --help")
        else:
            click.echo("  pip install -r requirements.txt")
            click.echo("  python main.py")

    except Exception as e:
        # Clean up on error
        click.echo(f"Error creating project: {str(e)}", err=True)
        if project_path.exists():
            shutil.rmtree(project_path)
        raise click.Abort()


def _get_template_path(template: str) -> Path:
    """Get the path to a template directory."""
    # First, check if we're in development mode (templates in the repo)
    dev_templates = Path(__file__).parent.parent.parent.parent / "templates"
    if dev_templates.exists():
        return dev_templates / template

    # Otherwise, check installed templates
    import agenticraft

    package_path = Path(agenticraft.__file__).parent
    return package_path / "templates" / template


def _copy_template(src: Path, dst: Path, project_name: str):
    """Copy template files to destination."""
    for item in src.iterdir():
        if item.name in [".git", "__pycache__", ".pytest_cache"]:
            continue

        dest_item = dst / item.name

        if item.is_dir():
            dest_item.mkdir(exist_ok=True)
            _copy_template(item, dest_item, project_name)
        else:
            shutil.copy2(item, dest_item)


def _init_git(project_path: Path):
    """Initialize a git repository."""
    import subprocess

    try:
        # Initialize git
        subprocess.run(
            ["git", "init"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )

        # Create .gitignore if it doesn't exist
        gitignore_path = project_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
build/
dist/
*.egg-info/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
"""
            gitignore_path.write_text(gitignore_content)

        # Initial commit
        subprocess.run(
            ["git", "add", "."],
            cwd=project_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit from AgentiCraft template"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )

        click.echo("✓ Initialized git repository")

    except subprocess.CalledProcessError:
        click.echo("⚠️  Failed to initialize git repository (git not found?)")
    except Exception as e:
        click.echo(f"⚠️  Failed to initialize git repository: {str(e)}")


def _update_project_files(project_path: Path, name: str, template: str):
    """Update project files with the project name."""
    # Update pyproject.toml if it exists
    pyproject_path = project_path / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        content = content.replace('name = "agenticraft-template"', f'name = "{name}"')
        content = content.replace("agenticraft-template", name)
        pyproject_path.write_text(content)

    # Update README.md
    readme_path = project_path / "README.md"
    if readme_path.exists():
        content = readme_path.read_text()
        content = content.replace(
            "AgentiCraft Template", name.replace("-", " ").title().replace(" ", "-")
        )
        content = content.replace("agenticraft-template", name)
        readme_path.write_text(content)

    # Template-specific updates
    if template == "fastapi":
        # Update docker-compose.yml
        compose_path = project_path / "docker" / "docker-compose.yml"
        if compose_path.exists():
            content = compose_path.read_text()
            content = content.replace("agenticraft-api", name)
            compose_path.write_text(content)
