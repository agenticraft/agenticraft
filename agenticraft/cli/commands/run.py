"""
Run command - Run agents from configuration or scripts.
"""

import sys
from pathlib import Path

import click


@click.command()
@click.argument("agent_file", type=click.Path(exists=True))
@click.option(
    "--prompt",
    "-p",
    help="Initial prompt for the agent",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Run in interactive mode",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "ollama"]),
    help="LLM provider to use",
)
def run(
    agent_file: str,
    prompt: str | None,
    interactive: bool,
    config: str | None,
    provider: str | None,
):
    """
    Run an agent from a Python file or configuration.

    Examples:
        agenticraft run agent.py --prompt "Hello"
        agenticraft run config.yaml --interactive
    """
    file_path = Path(agent_file)

    if file_path.suffix == ".py":
        _run_python_agent(file_path, prompt, interactive, config, provider)
    elif file_path.suffix in [".yaml", ".yml"]:
        _run_yaml_agent(file_path, prompt, interactive, provider)
    else:
        click.echo(f"Error: Unsupported file type: {file_path.suffix}", err=True)
        click.echo("Supported types: .py, .yaml, .yml")
        raise click.Abort()


def _run_python_agent(
    file_path: Path,
    prompt: str | None,
    interactive: bool,
    config: str | None,
    provider: str | None,
):
    """Run an agent from a Python file."""
    import asyncio
    import importlib.util

    # Load the Python module
    spec = importlib.util.spec_from_file_location("agent_module", file_path)
    if spec is None or spec.loader is None:
        click.echo(f"Error: Failed to load {file_path}", err=True)
        raise click.Abort()

    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_module"] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        click.echo(f"Error loading agent: {str(e)}", err=True)
        raise click.Abort()

    # Find the agent
    agent = None
    if hasattr(module, "agent"):
        agent = module.agent
    elif hasattr(module, "main_agent"):
        agent = module.main_agent
    elif hasattr(module, "create_agent"):
        # Call factory function
        agent = module.create_agent()
    else:
        # Look for first Agent instance
        from agenticraft.core.agent import Agent

        for name, obj in vars(module).items():
            if isinstance(obj, Agent):
                agent = obj
                break

    if agent is None:
        click.echo("Error: No agent found in file", err=True)
        click.echo(
            "Make sure your file exports an 'agent' variable or 'create_agent' function"
        )
        raise click.Abort()

    # Override provider if specified
    if provider:
        from agenticraft.providers import get_provider

        agent.provider = get_provider(provider)

    # Run the agent
    if interactive:
        _run_interactive(agent)
    else:
        if not prompt:
            click.echo("Error: --prompt required for non-interactive mode", err=True)
            raise click.Abort()

        # Run single prompt
        async def run_once():
            result = await agent.run(prompt)
            click.echo(f"\nAgent: {result.content}")

            if hasattr(result, "reasoning") and result.reasoning:
                click.echo(f"\nReasoning: {result.reasoning.synthesis}")

        asyncio.run(run_once())


def _run_yaml_agent(
    file_path: Path, prompt: str | None, interactive: bool, provider: str | None
):
    """Run an agent from a YAML configuration file."""
    import yaml

    from agenticraft import Agent, ReasoningAgent
    from agenticraft.providers import get_provider

    # Load configuration
    with open(file_path) as f:
        config = yaml.safe_load(f)

    # Create agent from config
    agent_config = config.get("agent", {})
    agent_type = agent_config.get("type", "simple")

    # Get provider
    provider_name = provider or agent_config.get("provider", "openai")
    llm_provider = get_provider(provider_name)

    # Create agent
    if agent_type == "reasoning":
        agent = ReasoningAgent(
            name=agent_config.get("name", "Assistant"),
            provider=llm_provider,
        )
    else:
        agent = Agent(
            name=agent_config.get("name", "Assistant"),
            provider=llm_provider,
        )

    # Add tools if specified
    tools = agent_config.get("tools", [])
    if tools:
        from agenticraft.tools import (
            extract_text,
            read_file,
            simple_calculate,
            web_search,
            write_file,
        )

        tool_map = {
            "search": web_search,
            "calculator": simple_calculate,
            "files": read_file,
            "http": extract_text,
            "text": write_file,
        }

        for tool_name in tools:
            if tool_name in tool_map:
                agent.add_tool(tool_map[tool_name])

    # Run the agent
    if interactive:
        _run_interactive(agent)
    else:
        if not prompt:
            prompt = agent_config.get("default_prompt", "Hello!")

        # Run single prompt
        import asyncio

        async def run_once():
            result = await agent.run(prompt)
            click.echo(f"\nAgent: {result.content}")

            if hasattr(result, "reasoning") and result.reasoning:
                click.echo(f"\nReasoning: {result.reasoning.synthesis}")

        asyncio.run(run_once())


def _run_interactive(agent):
    """Run agent in interactive mode."""
    import asyncio

    click.echo(f"\n🤖 {agent.name} (Interactive Mode)")
    click.echo("Type 'quit' or 'exit' to stop\n")

    async def interactive_loop():
        while True:
            try:
                # Get user input
                user_input = click.prompt("You", type=str)

                if user_input.lower() in ["quit", "exit"]:
                    click.echo("\nGoodbye! 👋")
                    break

                # Run agent
                result = await agent.run(user_input)

                # Display response
                click.echo(f"\n{agent.name}: {result.content}\n")

                # Show reasoning if available
                if hasattr(result, "reasoning") and result.reasoning:
                    if click.confirm("Show reasoning?", default=False):
                        click.echo(f"Reasoning: {result.reasoning.synthesis}\n")

            except KeyboardInterrupt:
                click.echo("\n\nGoodbye! 👋")
                break
            except Exception as e:
                click.echo(f"\nError: {str(e)}\n", err=True)

    asyncio.run(interactive_loop())
