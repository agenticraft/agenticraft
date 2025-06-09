#!/usr/bin/env python3
"""Example: Using tools with Regular Agents - Wrapper Pattern

This example shows how to use tools with regular agents by leveraging
the WorkflowAgent pattern, which is more reliable than direct tool calling.
"""

import asyncio
import os
from collections.abc import Callable

from dotenv import load_dotenv

from agenticraft.agents import WorkflowAgent

# Load environment variables
load_dotenv()


class SimpleToolWrapper:
    """Wrapper to make tools work reliably with agents."""

    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func

    def create_handler(self):
        """Create a handler for the tool."""

        def handler(agent, step, context):
            # Get parameters from context
            params = context.get(f"{self.name}_params", {})
            try:
                result = self.func(**params)
                context[f"{self.name}_result"] = result
                return f"Result: {result}"
            except Exception as e:
                return f"Error: {e}"

        return handler


# Define tool functions
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    # In production, use a proper expression parser
    try:
        # Only allow basic math operations
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        }
        # Evaluate with restricted globals
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def temperature_converter(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between Celsius and Fahrenheit."""
    from_unit = from_unit.upper()
    to_unit = to_unit.upper()

    if from_unit == "C" and to_unit == "F":
        return (value * 9 / 5) + 32
    elif from_unit == "F" and to_unit == "C":
        return (value - 32) * 5 / 9
    else:
        raise ValueError(f"Unsupported conversion: {from_unit} to {to_unit}")


async def example_with_calculation():
    """Example using calculation tool through workflow."""
    print("=== Calculation Example (Using Workflow Pattern) ===\n")

    # Create workflow agent
    agent = WorkflowAgent(
        name="CalculatorAgent",
        instructions="You perform calculations using the provided tools.",
        model="gpt-3.5-turbo",  # Use cheaper model for demo
    )

    # Create tool wrapper
    calc_tool = SimpleToolWrapper("calculate", calculate)

    # Register handler
    agent.register_handler("calc", calc_tool.create_handler())

    # Test calculations
    calculations = [
        {"expression": "2 + 2", "description": "Basic addition"},
        {"expression": "15 * 0.85", "description": "15% discount from 100"},
        {"expression": "pow(12, 2)", "description": "12 squared"},
        {"expression": "round(355/113, 4)", "description": "Approximation of pi"},
    ]

    for calc in calculations:
        # Create workflow for each calculation
        workflow = agent.create_workflow(f"calc_{calc['expression']}")
        workflow.add_step(
            name="calculate",
            handler="calc",
            action=f"Calculating: {calc['description']}",
        )

        # Execute with context
        context = {"calculate_params": {"expression": calc["expression"]}}
        result = await agent.execute_workflow(workflow, context=context)

        print(
            f"{calc['description']}: {calc['expression']} = {context.get('calculate_result')}"
        )


async def example_with_temperature():
    """Example using temperature conversion tool."""
    print("\n\n=== Temperature Conversion Example ===\n")

    # Create agent
    agent = WorkflowAgent(
        name="TemperatureConverter",
        instructions="You help with temperature conversions.",
        model="gpt-3.5-turbo",
    )

    # Create tool wrapper
    temp_tool = SimpleToolWrapper("convert_temp", temperature_converter)
    agent.register_handler("convert", temp_tool.create_handler())

    # Test conversions
    conversions = [
        {"value": 0, "from": "C", "to": "F", "desc": "Freezing point"},
        {"value": 100, "from": "C", "to": "F", "desc": "Boiling point"},
        {"value": 98.6, "from": "F", "to": "C", "desc": "Body temperature"},
        {"value": -40, "from": "C", "to": "F", "desc": "Same in both scales"},
    ]

    for conv in conversions:
        workflow = agent.create_workflow(f"convert_{conv['value']}")
        workflow.add_step(
            name="convert",
            handler="convert",
            action=f"Converting {conv['value']}°{conv['from']} to °{conv['to']}",
        )

        context = {
            "convert_temp_params": {
                "value": conv["value"],
                "from_unit": conv["from"],
                "to_unit": conv["to"],
            }
        }

        result = await agent.execute_workflow(workflow, context=context)
        converted = context.get("convert_temp_result")

        print(
            f"{conv['desc']}: {conv['value']}°{conv['from']} = {converted}°{conv['to']}"
        )


async def example_combined_workflow():
    """Example combining multiple tools in a workflow."""
    print("\n\n=== Combined Tools Example ===\n")

    agent = WorkflowAgent(
        name="MultiToolAgent",
        instructions="You coordinate multiple calculations and conversions.",
        model="gpt-3.5-turbo",
    )

    # Register both tools
    calc_tool = SimpleToolWrapper("calculate", calculate)
    temp_tool = SimpleToolWrapper("temp_convert", temperature_converter)

    agent.register_handler("calc", calc_tool.create_handler())
    agent.register_handler("convert", temp_tool.create_handler())

    # Create a workflow that uses both tools
    workflow = agent.create_workflow("weather_calculation")

    # Step 1: Convert temperature
    workflow.add_step(
        name="convert_temp", handler="convert", action="Converting 22°C to Fahrenheit"
    )

    # Step 2: Calculate feels-like temperature
    workflow.add_step(
        name="calculate_feels_like",
        handler="calc",
        action="Calculating feels-like temperature with wind chill",
        depends_on=["convert_temp"],
    )

    # Step 3: Summarize
    workflow.add_step(
        name="summarize",
        action="Summarize the weather calculations",
        depends_on=["calculate_feels_like"],
    )

    # Execute workflow
    context = {"temp_convert_params": {"value": 22, "from_unit": "C", "to_unit": "F"}}

    # Add a handler to prepare the feels-like calculation
    def prep_feels_like(agent, step, context):
        temp_f = context.get("temp_convert_result", 72)
        # Simple wind chill approximation
        wind_speed = 15  # mph
        feels_like_expr = f"{temp_f} - ({wind_speed} * 0.7)"
        context["calculate_params"] = {"expression": feels_like_expr}
        return "Prepared feels-like calculation"

    agent.register_handler("prep_calc", prep_feels_like)

    # Insert prep step
    workflow.steps[1].handler = "prep_calc"
    workflow.add_step(
        name="do_calc",
        handler="calc",
        action="Calculating feels-like temperature",
        depends_on=["calculate_feels_like"],
    )

    result = await agent.execute_workflow(workflow, context=context)

    print("\nResults:")
    print(f"- Actual: 22°C = {context.get('temp_convert_result')}°F")
    print(f"- Feels like: {context.get('calculate_result', 'N/A')}°F with 15mph wind")


async def main():
    """Run all examples."""
    print("🛠️  Tool Usage with Regular Agents - Wrapper Pattern")
    print("=" * 60)
    print("\nThis shows how to use tools reliably by leveraging WorkflowAgent")
    print("instead of the problematic direct tool calling.\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return

    try:
        await example_with_calculation()
        await example_with_temperature()
        await example_combined_workflow()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("\nKey Takeaways:")
        print("- Use WorkflowAgent with handlers for reliable tool usage")
        print("- The SimpleToolWrapper pattern makes it easy to convert functions")
        print("- Pass parameters through context")
        print("- This approach works reliably with current AgentiCraft")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
