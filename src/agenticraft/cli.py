"""Command-line interface for AgentiCraft"""

import click
import asyncio
from agenticraft import Agent, __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """AgentiCraft CLI - Build AI agents from the command line"""
    pass


@cli.command()
@click.option('--name', default='Agent', help='Name of the agent')
@click.option('--model', default='gpt-3.5-turbo', help='LLM model to use')
@click.argument('prompt')
def run(name: str, model: str, prompt: str):
    """Run an agent with a single prompt"""
    async def _run():
        agent = Agent(name=name, model=model)
        response = await agent.run(prompt)
        click.echo(response)
    
    asyncio.run(_run())


@cli.command()
@click.option('--name', default='ChatBot', help='Name of the chatbot')
def chat(name: str):
    """Start an interactive chat session"""
    from agenticraft import ChatAgent
    
    async def _chat():
        chatbot = ChatAgent(name=name, memory=True)
        click.echo(f"{name}: Hello! I'm your AI assistant. Type 'quit' to exit.")
        
        while True:
            user_input = click.prompt("You")
            
            if user_input.lower() == 'quit':
                click.echo(f"{name}: Goodbye!")
                break
            
            response = await chatbot.chat(user_input)
            click.echo(f"{name}: {response}")
    
    asyncio.run(_chat())


@cli.command()
def info():
    """Show information about AgentiCraft"""
    click.echo(f"AgentiCraft v{__version__}")
    click.echo("Open-source framework for building production-ready AI agents")
    click.echo("Documentation: https://docs.agenticraft.ai")
    click.echo("GitHub: https://github.com/agenticraft/agenticraft")


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
