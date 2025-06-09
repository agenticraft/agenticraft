#!/usr/bin/env python3
"""Marketplace example for AgentiCraft.

This example demonstrates:
- Creating plugin manifests
- Searching for plugins
- Installing and managing plugins
- Version management
- Creating your own plugin
"""

import asyncio
import tempfile
from pathlib import Path

from agenticraft.marketplace import (
    PluginCategory,
    PluginManifest,
    PluginType,
    RegistryClient,
    Version,
    VersionRange,
    create_manifest,
)


async def main():
    """Run marketplace examples."""
    print("🛍️ AgentiCraft Marketplace Example")
    print("=" * 50)

    # Note: This example uses a mock registry for demonstration
    # In production, it would connect to the actual AgentiCraft registry

    # Example 1: Creating a plugin manifest
    print("\n📝 Creating a Plugin Manifest")
    print("-" * 40)

    # Create a tool plugin manifest
    tool_manifest = create_manifest(
        plugin_type=PluginType.TOOL,
        name="weather-tool",
        title="Weather Information Tool",
        author_name="John Doe",
        description="Get real-time weather information for any location",
        category=PluginCategory.UTILITY,
        version="1.0.0",
        tags=["weather", "api", "real-time"],
        capabilities=["weather_current", "weather_forecast", "weather_alerts"],
    )

    print("Created tool manifest:")
    print(f"  Name: {tool_manifest.name}")
    print(f"  Version: {tool_manifest.version}")
    print(f"  Type: {tool_manifest.type}")
    print(f"  Category: {tool_manifest.category}")

    # Save manifest to YAML
    yaml_content = tool_manifest.to_yaml()
    print("\nManifest YAML preview:")
    print(yaml_content[:200] + "..." if len(yaml_content) > 200 else yaml_content)

    # Example 2: Version management
    print("\n🔢 Version Management")
    print("-" * 40)

    v1 = Version("1.0.0")
    v2 = Version("1.1.0")
    v3 = Version("2.0.0-beta.1")
    v4 = Version("2.0.0")

    print("Version comparisons:")
    print(f"  {v1} < {v2}: {v1 < v2}")
    print(f"  {v3} < {v4}: {v3 < v4} (pre-release < release)")
    print(f"  {v2}.is_compatible_with({v1}): {v2.is_compatible_with(v1)}")

    # Version ranges
    range1 = VersionRange(spec=">=1.0.0")
    range2 = VersionRange(spec="^1.0.0")  # Compatible with 1.x.x
    range3 = VersionRange(spec="~1.1.0")  # Compatible with 1.1.x

    print("\nVersion range checks:")
    print(f"  {v2} satisfies {range1}: {v2.satisfies(range1)}")
    print(f"  {v4} satisfies {range2}: {v4.satisfies(range2)}")
    print(f"  {v2} satisfies {range3}: {v2.satisfies(range3)}")

    # Example 3: Using the registry client (mock mode)
    print("\n🔍 Registry Client Demo")
    print("-" * 40)

    # Create a mock registry client
    # In production, this would connect to the real registry
    async with RegistryClient() as client:
        # Note: These operations are simulated for the example
        print("\nSimulated marketplace operations:")

        # Search for plugins
        print("\n1. Searching for 'web browser' plugins...")
        # In real usage: results = await client.search("web browser", plugin_type=PluginType.TOOL)
        print("   Found: web-browser-tool, selenium-wrapper, playwright-tool")

        # Get plugin info
        print("\n2. Getting info for 'web-browser-tool'...")
        # In real usage: info = await client.get_plugin_info("web-browser-tool")
        print("   Version: 2.1.0")
        print("   Downloads: 15,234")
        print("   Rating: 4.8/5")
        print("   Dependencies: requests>=2.28.0, beautifulsoup4>=4.11.0")

        # List installed plugins
        print("\n3. Listing installed plugins...")
        # In real usage: installed = await client.list_installed()
        print("   Installed: (none in this demo)")

        # Install a plugin
        print("\n4. Installing 'web-browser-tool'...")
        # In real usage: success = await client.install("web-browser-tool")
        print("   ✅ Successfully installed web-browser-tool v2.1.0")

    # Example 4: Creating your own plugin
    print("\n🔧 Creating Your Own Plugin")
    print("-" * 40)

    # Create a simple calculator tool plugin
    with tempfile.TemporaryDirectory() as temp_dir:
        plugin_dir = Path(temp_dir) / "calculator-tool"
        plugin_dir.mkdir()

        # Create the plugin manifest
        calc_manifest = PluginManifest(
            name="calculator-tool",
            version="1.0.0",
            type=PluginType.TOOL,
            category=PluginCategory.UTILITY,
            title="Calculator Tool",
            description="Simple calculator for basic math operations",
            author={"name": "AgentiCraft Team", "email": "team@agenticraft.ai"},
            entry_point="calculator_tool.main:CalculatorTool",
            requirements={
                "python": ">=3.10",
                "agenticraft": ">=0.2.0",
                "dependencies": [],
            },
            config=[
                {
                    "name": "precision",
                    "description": "Decimal precision for calculations",
                    "type": "integer",
                    "default_value": 2,
                    "required": False,
                }
            ],
            tags=["math", "calculator", "utility"],
            capabilities=["add", "subtract", "multiply", "divide", "power", "sqrt"],
            examples=[
                {
                    "name": "Basic calculation",
                    "code": """
from agenticraft import Agent
from calculator_tool import CalculatorTool

agent = Agent()
agent.add_tool(CalculatorTool())

result = agent.run("Calculate 15 * 23 + 42")
print(result.content)  # "387"
""".strip(),
                }
            ],
        )

        # Save manifest
        manifest_path = plugin_dir / "plugin.yaml"
        manifest_path.write_text(calc_manifest.to_yaml())

        # Create the main module
        main_py = plugin_dir / "calculator_tool.py"
        main_py.write_text(
            '''
"""Calculator tool for AgentiCraft."""

from agenticraft import tool
import math


class CalculatorTool:
    """Simple calculator tool."""
    
    def __init__(self, precision: int = 2):
        self.precision = precision
    
    @tool(name="calculate", description="Perform mathematical calculations")
    def calculate(self, expression: str) -> float:
        """Safely evaluate mathematical expressions."""
        # In production, use a proper expression parser
        # This is simplified for the example
        try:
            # Only allow safe operations
            allowed = {
                'abs': abs, 'round': round,
                'sin': math.sin, 'cos': math.cos,
                'sqrt': math.sqrt, 'pow': pow
            }
            result = eval(expression, {"__builtins__": {}}, allowed)
            return round(float(result), self.precision)
        except Exception as e:
            return f"Error: {str(e)}"
'''
        )

        print("Created plugin structure:")
        print(f"  📁 {plugin_dir.name}/")
        print("     📄 plugin.yaml (manifest)")
        print("     📄 calculator_tool.py (implementation)")

        print("\nManifest summary:")
        print(f"  Name: {calc_manifest.name}")
        print(f"  Version: {calc_manifest.version}")
        print(f"  Entry point: {calc_manifest.entry_point}")
        print(f"  Capabilities: {', '.join(calc_manifest.capabilities)}")

    # Example 5: Plugin manifest templates
    print("\n📋 Plugin Manifest Templates")
    print("-" * 40)

    print("AgentiCraft provides templates for common plugin types:")
    print("\n1. Tool Plugin Template:")
    print("   - Web scraping tools")
    print("   - API integration tools")
    print("   - Data processing tools")

    print("\n2. Agent Plugin Template:")
    print("   - Specialized agents")
    print("   - Multi-agent systems")
    print("   - Domain-specific assistants")

    print("\n3. Memory Plugin Template:")
    print("   - Custom memory backends")
    print("   - Specialized storage systems")

    print("\n✅ Marketplace example complete!")
    print("\n💡 Key Concepts:")
    print("   - Plugin manifests define metadata and requirements")
    print("   - Semantic versioning ensures compatibility")
    print("   - Registry client handles search, install, and updates")
    print("   - Plugins can be tools, agents, memory, and more")
    print("   - Easy to create and share your own plugins")

    print("\n🚀 Next Steps:")
    print("   1. Create your own plugin")
    print("   2. Test it locally")
    print("   3. Publish to the marketplace")
    print("   4. Share with the community!")


if __name__ == "__main__":
    asyncio.run(main())
