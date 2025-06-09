"""Example: Using explicit provider parameter in AgentConfig.

This example demonstrates how to use the new provider parameter
introduced in v0.1.1 for explicit provider specification.
"""

import asyncio

from agenticraft import Agent


async def explicit_provider_example():
    """Demonstrate explicit provider specification."""

    print("=== Explicit Provider Parameter Example ===\n")

    # 1. Explicit provider specification (NEW in v0.1.1)
    print("1. Creating agent with explicit provider")
    print("-" * 40)

    # Specify provider explicitly
    agent = Agent(
        name="ExplicitAgent",
        provider="anthropic",  # NEW: Explicit provider
        model="claude-3-opus-20240229",
        instructions="You are Claude, created by Anthropic.",
    )

    # Provider info shows explicit provider
    info = agent.get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Model: {info['model']}")
    print(f"Config provider field: {agent.config.provider}\n")

    # 2. Auto-detection still works (backward compatible)
    print("2. Auto-detection (backward compatible)")
    print("-" * 40)

    # No provider specified - auto-detected from model
    agent_auto = Agent(name="AutoDetectAgent", model="gpt-4")  # Auto-detects as OpenAI

    info = agent_auto.get_provider_info()
    print(f"Provider: {info['provider']} (auto-detected)")
    print(f"Model: {info['model']}")
    print(f"Config provider field: {agent_auto.config.provider} (None = auto-detect)\n")

    # 3. Explicit provider helps with ambiguous models
    print("3. Handling ambiguous model names")
    print("-" * 40)

    # Some model names might be ambiguous
    # Explicit provider removes ambiguity
    agent_custom = Agent(
        name="CustomModelAgent",
        provider="ollama",  # Explicitly use Ollama
        model="my-custom-model",  # Custom model name
        base_url="http://localhost:11434",
    )

    print(
        f"Using custom model '{agent_custom.config.model}' with {agent_custom.config.provider}\n"
    )

    # 4. Provider switching updates config.provider
    print("4. Provider switching updates config")
    print("-" * 40)

    # Start with one provider
    agent_switch = Agent(
        name="SwitchingAgent", provider="openai", model="gpt-3.5-turbo"
    )

    print(
        f"Initial: provider={agent_switch.config.provider}, model={agent_switch.config.model}"
    )

    # Switch provider
    agent_switch.set_provider("anthropic", model="claude-3-sonnet-20240229")
    print(
        f"After switch: provider={agent_switch.config.provider}, model={agent_switch.config.model}\n"
    )

    # 5. Provider validation
    print("5. Provider validation")
    print("-" * 40)

    try:
        # Invalid provider name
        bad_agent = Agent(
            name="BadAgent",
            provider="invalid_provider",  # This will raise an error
            model="some-model",
        )
    except ValueError as e:
        print(f"✓ Validation error caught: {e}\n")

    # 6. Benefits of explicit provider
    print("6. Benefits of explicit provider specification")
    print("-" * 40)
    print("• Clarity: No ambiguity about which provider is being used")
    print("• Control: Override auto-detection when needed")
    print("• Future-proofing: Support for models with similar naming patterns")
    print("• Testing: Easier to mock specific providers in tests")
    print("• Configuration: Can be set via config files or environment\n")


async def provider_config_patterns():
    """Show different configuration patterns with provider parameter."""

    print("\n=== Provider Configuration Patterns ===\n")

    # Pattern 1: From configuration dict
    config = {
        "name": "ConfiguredAgent",
        "provider": "anthropic",
        "model": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    agent = Agent(**config)
    print(f"1. From config dict: {agent.config.provider} / {agent.config.model}")

    # Pattern 2: Environment-based configuration
    import os

    # Could read from environment
    provider = os.getenv("AGENT_PROVIDER", "openai")
    model = os.getenv("AGENT_MODEL", "gpt-4")

    agent = Agent(name="EnvAgent", provider=provider, model=model)
    print(f"2. From environment: {agent.config.provider} / {agent.config.model}")

    # Pattern 3: Factory pattern with provider
    def create_agent(task_type: str) -> Agent:
        """Create agent based on task type."""
        if task_type == "creative":
            return Agent(
                name="CreativeAgent",
                provider="anthropic",
                model="claude-3-opus-20240229",
                temperature=0.9,
            )
        elif task_type == "analytical":
            return Agent(
                name="AnalyticalAgent",
                provider="openai",
                model="gpt-4",
                temperature=0.1,
            )
        else:
            return Agent(name="LocalAgent", provider="ollama", model="llama2")

    creative = create_agent("creative")
    print(f"3. Factory pattern: {creative.name} uses {creative.config.provider}")

    # Pattern 4: Multi-provider pool
    providers_pool = [
        {"provider": "openai", "model": "gpt-4", "priority": 1},
        {"provider": "anthropic", "model": "claude-3-opus-20240229", "priority": 2},
        {"provider": "ollama", "model": "llama2", "priority": 3},
    ]

    # Try providers in priority order
    for config in sorted(providers_pool, key=lambda x: x["priority"]):
        try:
            agent = Agent(
                name="PooledAgent", provider=config["provider"], model=config["model"]
            )
            print(
                f"4. Provider pool: Selected {config['provider']} (priority {config['priority']})"
            )
            break
        except Exception:
            continue


async def main():
    """Run all examples."""
    await explicit_provider_example()
    await provider_config_patterns()

    print("\n✅ Provider parameter examples completed!")
    print("\nKey Takeaway: The provider parameter gives you explicit control")
    print("over which LLM provider to use, while maintaining backward")
    print("compatibility with auto-detection from model names.")


if __name__ == "__main__":
    asyncio.run(main())
