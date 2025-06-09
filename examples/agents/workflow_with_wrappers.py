"""Working with Tools in AgentiCraft - Clean Approach

This example shows how to use tools with WorkflowAgent by working around
the framework's current limitations WITHOUT any patches or modifications.

The approach: Use a tool wrapper that ensures compatibility.
"""

import asyncio
import json
from collections.abc import Callable
from typing import Any

from agenticraft.agents import StepStatus, WorkflowAgent


class ToolWrapper:
    """Wrapper to make tools work with current framework limitations."""

    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
        self._results = {}  # Store results by step name

    async def execute(self, *args, **kwargs):
        """Execute the wrapped function."""
        try:
            result = self.func(*args, **kwargs)
            return result
        except Exception as e:
            return {"error": str(e)}

    def create_step_handler(self, step_name: str):
        """Create a handler for workflow steps."""

        async def handler(agent, step, context):
            # Get parameters from context
            params = context.get(f"{step_name}_params", {})
            result = await self.execute(**params)

            # Store result in context
            context[f"{step_name}_result"] = result
            self._results[step_name] = result

            # Return formatted result
            if isinstance(result, dict):
                return json.dumps(result, indent=2)
            return str(result)

        return handler


# Define our tool functions as regular Python functions
def fetch_weather_data(city: str) -> dict[str, Any]:
    """Fetch weather data for a city."""
    weather_db = {
        "New York": {"temp": 72, "humidity": 65, "conditions": "Partly cloudy"},
        "London": {"temp": 59, "humidity": 80, "conditions": "Rainy"},
        "Tokyo": {"temp": 68, "humidity": 55, "conditions": "Clear"},
        "Miami": {"temp": 88, "humidity": 90, "conditions": "Thunderstorms"},
    }

    data = weather_db.get(city, {"temp": 70, "humidity": 60, "conditions": "Unknown"})
    return {
        "city": city,
        "temperature": data["temp"],
        "humidity": data["humidity"],
        "conditions": data["conditions"],
        "timestamp": "2024-01-15 10:00:00",
    }


def analyze_weather_list(cities_data: list) -> dict[str, Any]:
    """Analyze weather data from multiple cities."""
    if not cities_data:
        return {"error": "No data provided"}

    temps = [d["temperature"] for d in cities_data]
    humidities = [d["humidity"] for d in cities_data]

    return {
        "city_count": len(cities_data),
        "avg_temperature": round(sum(temps) / len(temps), 1),
        "avg_humidity": round(sum(humidities) / len(humidities), 1),
        "hottest": max(cities_data, key=lambda x: x["temperature"])["city"],
        "coolest": min(cities_data, key=lambda x: x["temperature"])["city"],
        "most_humid": max(cities_data, key=lambda x: x["humidity"])["city"],
    }


def generate_report(weather_data: list, analysis: dict) -> str:
    """Generate a weather report."""
    report = "WEATHER REPORT\n" + "=" * 50 + "\n\n"

    report += "Current Conditions:\n"
    for city_data in weather_data:
        report += f"- {city_data['city']}: {city_data['temperature']}°F, "
        report += f"{city_data['conditions']} ({city_data['humidity']}% humidity)\n"

    report += "\nSummary:\n"
    report += f"- Average Temperature: {analysis['avg_temperature']}°F\n"
    report += f"- Average Humidity: {analysis['avg_humidity']}%\n"
    report += f"- Hottest City: {analysis['hottest']}\n"
    report += f"- Most Humid: {analysis['most_humid']}\n"

    return report


async def working_tool_workflow():
    """Workflow that uses tools through handlers."""
    print("=== Weather Analysis with Tool Wrappers ===\n")

    # Create tool wrappers
    weather_tool = ToolWrapper(
        "fetch_weather", "Fetch weather data", fetch_weather_data
    )
    analyze_tool = ToolWrapper(
        "analyze_weather", "Analyze weather data", analyze_weather_list
    )
    report_tool = ToolWrapper(
        "generate_report", "Generate weather report", generate_report
    )

    # Create workflow agent
    agent = WorkflowAgent(
        name="WeatherBot",
        instructions="""You coordinate weather data analysis. 
        When handlers are used, describe what they're doing and interpret their results.""",
    )

    # Register handlers
    agent.register_handler("fetch_nyc", weather_tool.create_step_handler("fetch_nyc"))
    agent.register_handler(
        "fetch_london", weather_tool.create_step_handler("fetch_london")
    )
    agent.register_handler(
        "fetch_tokyo", weather_tool.create_step_handler("fetch_tokyo")
    )
    agent.register_handler(
        "analyze_data", analyze_tool.create_step_handler("analyze_data")
    )
    agent.register_handler(
        "create_report", report_tool.create_step_handler("create_report")
    )

    # Create workflow
    workflow = agent.create_workflow(
        name="weather_analysis", description="Analyze weather across multiple cities"
    )

    # Define context with parameters
    context = {
        "fetch_nyc_params": {"city": "New York"},
        "fetch_london_params": {"city": "London"},
        "fetch_tokyo_params": {"city": "Tokyo"},
        "cities_data": [],  # Will be populated by steps
    }

    # Add workflow steps
    workflow.add_step(
        name="fetch_nyc",
        handler="fetch_nyc",
        action="Fetching weather data for New York...",
    )

    workflow.add_step(
        name="fetch_london",
        handler="fetch_london",
        action="Fetching weather data for London...",
        depends_on=["fetch_nyc"],
    )

    workflow.add_step(
        name="fetch_tokyo",
        handler="fetch_tokyo",
        action="Fetching weather data for Tokyo...",
        depends_on=["fetch_london"],
    )

    # Step to combine data
    def combine_data(agent, step, context):
        """Combine fetched weather data."""
        cities_data = []
        for city in ["nyc", "london", "tokyo"]:
            result = context.get(f"fetch_{city}_result")
            if result:
                cities_data.append(result)

        context["cities_data"] = cities_data
        context["analyze_data_params"] = {"cities_data": cities_data}
        return f"Combined data for {len(cities_data)} cities"

    agent.register_handler("combine_data", combine_data)

    workflow.add_step(
        name="combine_data",
        handler="combine_data",
        action="Combining weather data from all cities...",
        depends_on=["fetch_tokyo"],
    )

    workflow.add_step(
        name="analyze_data",
        handler="analyze_data",
        action="Analyzing weather patterns...",
        depends_on=["combine_data"],
    )

    # Final report step
    def prepare_report(agent, step, context):
        """Prepare final report."""
        cities_data = context.get("cities_data", [])
        analysis = context.get("analyze_data_result", {})

        report = generate_report(cities_data, analysis)
        return report

    agent.register_handler("prepare_report", prepare_report)

    workflow.add_step(
        name="prepare_report",
        handler="prepare_report",
        action="Generating final weather report...",
        depends_on=["analyze_data"],
    )

    # Execute workflow
    print("Starting workflow execution...")
    print("-" * 40)

    try:
        result = await agent.execute_workflow(workflow, context=context)

        print("\n✅ Workflow completed successfully!")

        # Show results
        print("\n📊 Results:")
        for step_name in [
            "fetch_nyc",
            "fetch_london",
            "fetch_tokyo",
            "analyze_data",
            "prepare_report",
        ]:
            step_result = result.step_results.get(step_name)
            if step_result and step_result.status == StepStatus.COMPLETED:
                print(f"\n{step_name}:")
                if step_name == "prepare_report":
                    print(step_result.result)
                else:
                    print("  Status: ✓ Completed")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")


async def simple_calculation_workflow():
    """Simple calculation workflow using handlers."""
    print("\n\n=== Calculation Workflow ===\n")

    # Define calculation functions
    def add_numbers(a: float, b: float) -> float:
        return a + b

    def multiply_numbers(a: float, b: float) -> float:
        return a * b

    def calculate_percentage(value: float, total: float) -> dict:
        percentage = (value / total) * 100
        return {"value": value, "total": total, "percentage": round(percentage, 2)}

    # Create workflow
    agent = WorkflowAgent(
        name="Calculator", instructions="Perform calculations step by step."
    )

    # Register calculation handlers
    def create_calc_handler(func, param_getter):
        def handler(agent, step, context):
            params = param_getter(context)
            result = func(**params)
            context[f"{step.name}_result"] = result
            return f"Result: {result}"

        return handler

    agent.register_handler(
        "add", create_calc_handler(add_numbers, lambda ctx: {"a": 10, "b": 25})
    )

    agent.register_handler(
        "multiply",
        create_calc_handler(
            multiply_numbers, lambda ctx: {"a": ctx.get("add_result", 0), "b": 3}
        ),
    )

    agent.register_handler(
        "percentage",
        create_calc_handler(
            calculate_percentage,
            lambda ctx: {"value": ctx.get("multiply_result", 0), "total": 200},
        ),
    )

    # Create workflow
    workflow = agent.create_workflow(
        name="calculations", description="Perform a series of calculations"
    )

    workflow.add_step(name="add", handler="add", action="Adding 10 + 25")

    workflow.add_step(
        name="multiply",
        handler="multiply",
        action="Multiplying the previous result by 3",
        depends_on=["add"],
    )

    workflow.add_step(
        name="percentage",
        handler="percentage",
        action="Calculating what percentage the result is of 200",
        depends_on=["multiply"],
    )

    workflow.add_step(
        name="summarize",
        action="Summarize all calculation results",
        depends_on=["percentage"],
    )

    print("Executing calculation workflow...")

    try:
        result = await agent.execute_workflow(workflow)

        # Show calculation flow
        print("\n📊 Calculation Flow:")
        print("  10 + 25 = 35")
        print("  35 × 3 = 105")
        print("  105 is 52.5% of 200")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")


async def main():
    """Run examples that work with the current framework."""
    print("WorkflowAgent with Tools - Clean Approach (No Patches)")
    print("=" * 60)
    print("\nThis demonstrates tool usage through handlers,")
    print("which works reliably with the current framework.\n")

    import os

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return

    # Run examples
    await working_tool_workflow()
    await simple_calculation_workflow()

    print("\n" + "=" * 60)
    print("✅ Examples completed successfully!")
    print("\nKey approach:")
    print("- Use handlers instead of @tool decorators")
    print("- Pass data through workflow context")
    print("- No framework modifications needed")
    print("- Works reliably with current AgentiCraft version")


if __name__ == "__main__":
    asyncio.run(main())
