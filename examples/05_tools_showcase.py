#!/usr/bin/env python3
"""Example: Tool-Enhanced Agent (Demonstration)

This example demonstrates how to create agents with various tools.
Note: This is a demonstration that shows the structure - actual execution
requires API keys configured.
"""

import asyncio
from agenticraft import Agent
from agenticraft.tools import (
    simple_calculate,
    scientific_calculate,
    read_file,
    write_file,
    read_json,
    write_json,
    list_files,
    web_search
)


def demo_calculator_agent():
    """Demonstrate creating a math tutor agent with calculator tools."""
    
    print("=== Calculator Agent Demo ===")
    print("\nCreating a math tutor agent with calculator tools...")
    
    math_tutor = Agent(
        name="MathTutor",
        instructions="""You are a helpful math tutor. You can perform calculations 
        and explain mathematical concepts. Always verify your calculations using tools.""",
        tools=[simple_calculate, scientific_calculate]
    )
    
    print(f"✅ Created: {math_tutor}")
    print(f"   Tools: {[tool.name for tool in math_tutor._tool_registry._tools.values()]}")
    
    print("\nExample prompts you could use:")
    print("- 'What is 15% of 850?'")
    print("- 'Calculate the area of a circle with radius 7.5m'")
    print("- 'Find sin(45°) in radians'")


def demo_file_manager():
    """Demonstrate creating a file management assistant."""
    
    print("\n\n=== File Manager Demo ===")
    print("\nCreating a file management assistant...")
    
    file_assistant = Agent(
        name="FileManager",
        instructions="""You help users manage files and data. You can read, write, 
        and organize files. Always confirm before overwriting files.""",
        tools=[read_file, write_file, read_json, write_json, list_files]
    )
    
    print(f"✅ Created: {file_assistant}")
    print(f"   Tools: {[tool.name for tool in file_assistant._tool_registry._tools.values()]}")
    
    print("\nExample tasks:")
    print("- Create project configuration files")
    print("- Read and summarize file contents")
    print("- Organize directory structures")


def demo_research_assistant():
    """Demonstrate creating a research assistant."""
    
    print("\n\n=== Research Assistant Demo ===")
    print("\nCreating a research assistant...")
    
    researcher = Agent(
        name="ResearchAssistant",
        instructions="""You are a research assistant. You search for information,
        analyze it, and provide summaries. Focus on accuracy and cite your sources.""",
        tools=[web_search, simple_calculate],
        temperature=0.3  # Lower temperature for more focused responses
    )
    
    print(f"✅ Created: {researcher}")
    print(f"   Tools: {[tool.name for tool in researcher._tool_registry._tools.values()]}")
    print(f"   Temperature: {researcher.config.temperature}")
    
    print("\nExample research tasks:")
    print("- Search for renewable energy statistics")
    print("- Find and analyze market trends")
    print("- Research technical topics with calculations")


def demo_multi_tool_agent():
    """Demonstrate an agent using multiple tools together."""
    
    print("\n\n=== Multi-Tool Agent Demo ===")
    print("\nCreating a data analyst with multiple tools...")
    
    analyst = Agent(
        name="DataAnalyst",
        instructions="""You are a data analyst. You can search for information,
        perform calculations, and save results to files for later reference.""",
        tools=[web_search, simple_calculate, write_json, read_json]
    )
    
    print(f"✅ Created: {analyst}")
    print(f"   Tools: {[tool.name for tool in analyst._tool_registry._tools.values()]}")
    
    print("\nComplex tasks this agent could handle:")
    print("- Search for data and perform analysis")
    print("- Calculate statistics and save results")
    print("- Create reports with multiple data sources")


def demo_custom_tools():
    """Show how to create custom tools."""
    
    print("\n\n=== Custom Tool Creation Demo ===")
    
    from agenticraft.core.tool import tool
    
    # Simple custom tool
    @tool(description="Convert temperature between Celsius and Fahrenheit")
    def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature between units."""
        if from_unit.lower() == "c" and to_unit.lower() == "f":
            return (value * 9/5) + 32
        elif from_unit.lower() == "f" and to_unit.lower() == "c":
            return (value - 32) * 5/9
        else:
            raise ValueError(f"Unsupported conversion: {from_unit} to {to_unit}")
    
    # Async custom tool
    @tool(
        name="fetch_data",
        description="Fetch data from an API endpoint"
    )
    async def fetch_api_data(endpoint: str, params: dict = None) -> dict:
        """Fetch data from API (mock implementation)."""
        await asyncio.sleep(0.1)  # Simulate network delay
        return {
            "endpoint": endpoint,
            "params": params or {},
            "data": {"example": "response"},
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    print("Created custom tools:")
    print(f"✅ {convert_temperature.name}: {convert_temperature.description}")
    print(f"✅ {fetch_api_data.name}: {fetch_api_data.description}")
    
    # Test the temperature converter
    print("\nTesting temperature converter:")
    result = convert_temperature(100, "C", "F")
    print(f"   100°C = {result}°F")
    result = convert_temperature(32, "F", "C")
    print(f"   32°F = {result}°C")


def show_tool_details():
    """Show details about available tools."""
    
    print("\n\n=== Available Built-in Tools ===")
    
    from agenticraft.tools import (
        CALCULATOR_TOOLS,
        FILE_TOOLS,
        WEB_TOOLS
    )
    
    print("\n📊 Calculator Tools:")
    for tool in CALCULATOR_TOOLS:
        print(f"   • {tool.name}: {tool.description}")
    
    print("\n📁 File Tools:")
    for tool in FILE_TOOLS:
        print(f"   • {tool.name}: {tool.description}")
    
    print("\n🌐 Web Tools:")
    for tool in WEB_TOOLS:
        print(f"   • {tool.name}: {tool.description}")


def main():
    """Run all demonstrations."""
    
    print("=== AgentiCraft Tool Examples (Demo Mode) ===")
    print("\nThis demonstrates the structure of tool-enhanced agents.")
    print("To run with actual LLM backends, configure your API keys.\n")
    
    # Run demos
    demo_calculator_agent()
    demo_file_manager()
    demo_research_assistant()
    demo_multi_tool_agent()
    demo_custom_tools()
    show_tool_details()
    
    print("\n\n=== Demo Complete ===")
    print("\nTo use these agents:")
    print("1. Set up your API keys (OPENAI_API_KEY, etc.)")
    print("2. Call agent.run() or await agent.arun() with your prompts")
    print("3. The agent will automatically use tools as needed")
    
    print("\nExample usage:")
    print("   response = await agent.arun('Calculate 15% of 850')")
    print("   print(response.content)")
    print("   print(f'Tools used: {response.tool_calls}')")


if __name__ == "__main__":
    main()
