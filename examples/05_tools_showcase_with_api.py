#!/usr/bin/env python3
"""Example: Tool-Enhanced Agent

This example demonstrates how to create agents with various tools
and use them for practical tasks.
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


async def calculator_agent_example():
    """Create a math tutor agent with calculator tools."""
    
    math_tutor = Agent(
        name="MathTutor",
        instructions="""You are a helpful math tutor. You can perform calculations 
        and explain mathematical concepts. Always verify your calculations using tools.""",
        tools=[simple_calculate, scientific_calculate],
        model="openai:gpt-4",
        # Use mock mode to avoid API calls in example
        api_key="mock-key-for-example"
    )
    
    # Example 1: Basic calculation
    response = await math_tutor.arun(
        "What is 15% of 850? Also calculate the compound interest on $1000 "
        "at 5% annual rate for 3 years."
    )
    print("Math Tutor Response:")
    print(response.content)
    print(f"\nTools used: {[tc['name'] for tc in response.tool_calls]}")
    
    # Example 2: Scientific calculation with explanation
    response2 = await math_tutor.arun(
        "Calculate the area of a circle with radius 7.5m and explain the formula. "
        "Also find sin(45°) in radians."
    )
    print("\n" + "="*50)
    print("Scientific Calculation:")
    print(response2.content)


async def file_manager_example():
    """Create a file management assistant."""
    
    file_assistant = Agent(
        name="FileManager",
        instructions="""You help users manage files and data. You can read, write, 
        and organize files. Always confirm before overwriting files.""",
        tools=[read_file, write_file, read_json, write_json, list_files],
        model="anthropic:claude-3-haiku"
    )
    
    # Example: Create a project structure
    response = await file_assistant.arun("""
        Create a project configuration file with the following:
        - Project name: AgentiCraft Demo
        - Version: 0.1.0
        - Description: Demo of file operations
        - Created: today's date
        
        Save it as 'project_config.json'
    """)
    
    print("\nFile Assistant Response:")
    print(response.content)
    
    # Read back the file
    response2 = await file_assistant.arun(
        "Read the project_config.json file and summarize its contents"
    )
    print("\nFile Contents Summary:")
    print(response2.content)


async def research_assistant_example():
    """Create a simple research assistant."""
    
    researcher = Agent(
        name="ResearchAssistant",
        instructions="""You are a research assistant. You search for information,
        analyze it, and provide summaries. Focus on accuracy and cite your sources.""",
        tools=[web_search, simple_calculate],
        temperature=0.3  # Lower temperature for more focused responses
    )
    
    # Research task
    response = await researcher.arun("""
        Search for information about renewable energy growth in 2024.
        If you find any statistics, calculate the year-over-year growth rates.
    """)
    
    print("\nResearch Assistant Findings:")
    print(response.content)
    print(f"\nTools used: {[tc['name'] for tc in response.tool_calls]}")


async def multi_tool_example():
    """Demonstrate an agent using multiple tools together."""
    
    analyst = Agent(
        name="DataAnalyst",
        instructions="""You are a data analyst. You can search for information,
        perform calculations, and save results to files for later reference.""",
        tools=[web_search, simple_calculate, write_json, read_json]
    )
    
    # Complex task using multiple tools
    response = await analyst.arun("""
        1. Search for the top 3 programming languages by popularity in 2024
        2. Create a simple scoring system (assign scores 3, 2, 1 for ranks)
        3. Calculate the percentage each language represents of the total score
        4. Save the analysis as 'language_analysis.json'
    """)
    
    print("\nData Analyst Report:")
    print(response.content)
    
    # Show tool usage pattern
    print("\nTool Usage Pattern:")
    for i, tool_call in enumerate(response.tool_calls, 1):
        print(f"{i}. {tool_call['name']}: {list(tool_call.get('arguments', {}).keys())}")


async def main():
    """Run all examples."""
    
    print("=== AgentiCraft Tool Examples ===\n")
    
    # Run examples sequentially
    print("1. CALCULATOR AGENT")
    print("-" * 50)
    await calculator_agent_example()
    
    print("\n\n2. FILE MANAGER")
    print("-" * 50)
    await file_manager_example()
    
    print("\n\n3. RESEARCH ASSISTANT")
    print("-" * 50)
    await research_assistant_example()
    
    print("\n\n4. MULTI-TOOL ANALYST")
    print("-" * 50)
    await multi_tool_example()
    
    print("\n\n=== Examples Complete ===")


# Tool creation example
def custom_tool_example():
    """Show how to create custom tools."""
    
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
        # In real implementation, use aiohttp
        await asyncio.sleep(0.1)  # Simulate network delay
        return {
            "endpoint": endpoint,
            "params": params or {},
            "data": {"example": "response"},
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    print("\nCustom tools created:")
    print(f"- {convert_temperature.name}: {convert_temperature.description}")
    print(f"- {fetch_api_data.name}: {fetch_api_data.description}")
    
    return convert_temperature, fetch_api_data


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())
    
    # Show custom tool creation
    print("\n\n=== CUSTOM TOOL CREATION ===")
    print("-" * 50)
    custom_tool_example()
