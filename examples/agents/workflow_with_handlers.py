"""Alternative approach: Using AgentiCraft with inline tool logic.

This approach embeds tool functionality directly in workflow steps,
avoiding the @tool decorator issues entirely while maintaining
tool-like functionality.
"""

import asyncio
import json
from datetime import datetime

from agenticraft.agents import StepStatus, WorkflowAgent


# Tool logic as regular functions (not decorated)
def weather_database():
    """Simulated weather database."""
    return {
        "New York": {
            "temperature": 72,
            "humidity": 65,
            "conditions": "Partly cloudy",
            "wind_speed": 12,
            "pressure": 30.15,
        },
        "London": {
            "temperature": 59,
            "humidity": 80,
            "conditions": "Rainy",
            "wind_speed": 18,
            "pressure": 29.92,
        },
        "Tokyo": {
            "temperature": 68,
            "humidity": 55,
            "conditions": "Clear",
            "wind_speed": 8,
            "pressure": 30.20,
        },
        "Miami": {
            "temperature": 88,
            "humidity": 90,
            "conditions": "Thunderstorms",
            "wind_speed": 25,
            "pressure": 29.75,
        },
        "Sydney": {
            "temperature": 75,
            "humidity": 70,
            "conditions": "Sunny",
            "wind_speed": 15,
            "pressure": 30.10,
        },
    }


async def integrated_weather_workflow():
    """Weather workflow with integrated tool logic."""
    print("=== Integrated Weather Analysis Workflow ===\n")

    agent = WorkflowAgent(
        name="WeatherAnalyzer",
        instructions="""You are a weather analysis system. 
        Execute each step and work with the data provided in the context.
        Format outputs clearly and provide insights.""",
    )

    workflow = agent.create_workflow(
        name="integrated_weather_analysis",
        description="Analyze weather using integrated tool logic",
    )

    # Step 1: Fetch weather data (tool logic inline)
    def fetch_all_weather(agent, step, context):
        """Fetch weather for multiple cities."""
        cities = context.get("target_cities", ["New York", "London", "Tokyo"])
        weather_db = weather_database()

        fetched_data = []
        for city in cities:
            if city in weather_db:
                data = weather_db[city].copy()
                data["city"] = city
                data["fetch_time"] = datetime.now().isoformat()
                fetched_data.append(data)

        context["weather_data"] = fetched_data
        return f"Successfully fetched weather data for {len(fetched_data)} cities: {', '.join(cities)}"

    agent.register_handler("fetch_weather", fetch_all_weather)

    # Step 2: Analyze the data (tool logic inline)
    def analyze_weather_data(agent, step, context):
        """Analyze weather patterns."""
        weather_data = context.get("weather_data", [])

        if not weather_data:
            return "No weather data available for analysis"

        # Perform analysis
        temps = [d["temperature"] for d in weather_data]
        humidities = [d["humidity"] for d in weather_data]
        wind_speeds = [d["wind_speed"] for d in weather_data]

        analysis = {
            "summary": {
                "cities_analyzed": len(weather_data),
                "avg_temperature": round(sum(temps) / len(temps), 1),
                "avg_humidity": round(sum(humidities) / len(humidities), 1),
                "avg_wind_speed": round(sum(wind_speeds) / len(wind_speeds), 1),
            },
            "extremes": {
                "hottest": max(weather_data, key=lambda x: x["temperature"]),
                "coldest": min(weather_data, key=lambda x: x["temperature"]),
                "most_humid": max(weather_data, key=lambda x: x["humidity"]),
                "windiest": max(weather_data, key=lambda x: x["wind_speed"]),
            },
            "alerts": [],
        }

        # Check for severe conditions
        for city_data in weather_data:
            if city_data["temperature"] > 85:
                analysis["alerts"].append(
                    f"High temperature alert for {city_data['city']}"
                )
            if "storm" in city_data["conditions"].lower():
                analysis["alerts"].append(f"Storm warning for {city_data['city']}")
            if city_data["wind_speed"] > 20:
                analysis["alerts"].append(f"High wind warning for {city_data['city']}")

        context["analysis"] = analysis
        return json.dumps(analysis, indent=2)

    agent.register_handler("analyze", analyze_weather_data)

    # Step 3: Generate report (tool logic inline)
    def generate_weather_report(agent, step, context):
        """Generate comprehensive weather report."""
        weather_data = context.get("weather_data", [])
        analysis = context.get("analysis", {})

        report = "COMPREHENSIVE WEATHER REPORT\n"
        report += "=" * 50 + "\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Current conditions
        report += "CURRENT CONDITIONS:\n"
        report += "-" * 30 + "\n"
        for city_data in weather_data:
            report += f"{city_data['city']:15} "
            report += f"{city_data['temperature']}°F, "
            report += f"{city_data['conditions']}, "
            report += f"Wind: {city_data['wind_speed']} mph\n"

        # Summary statistics
        summary = analysis.get("summary", {})
        report += "\nSUMMARY STATISTICS:\n"
        report += "-" * 30 + "\n"
        report += f"Cities Analyzed:    {summary.get('cities_analyzed', 0)}\n"
        report += f"Average Temp:       {summary.get('avg_temperature', 'N/A')}°F\n"
        report += f"Average Humidity:   {summary.get('avg_humidity', 'N/A')}%\n"
        report += f"Average Wind:       {summary.get('avg_wind_speed', 'N/A')} mph\n"

        # Extremes
        extremes = analysis.get("extremes", {})
        report += "\nEXTREME CONDITIONS:\n"
        report += "-" * 30 + "\n"
        if extremes.get("hottest"):
            report += f"Hottest:   {extremes['hottest']['city']} ({extremes['hottest']['temperature']}°F)\n"
        if extremes.get("windiest"):
            report += f"Windiest:  {extremes['windiest']['city']} ({extremes['windiest']['wind_speed']} mph)\n"

        # Alerts
        alerts = analysis.get("alerts", [])
        if alerts:
            report += "\n⚠️  WEATHER ALERTS:\n"
            report += "-" * 30 + "\n"
            for alert in alerts:
                report += f"• {alert}\n"

        context["final_report"] = report
        return report

    agent.register_handler("generate_report", generate_weather_report)

    # Define workflow steps
    workflow.add_step(
        name="fetch_data",
        handler="fetch_weather",
        action="Fetching weather data for target cities...",
    )

    workflow.add_step(
        name="analyze",
        handler="analyze",
        action="Analyzing weather patterns and identifying extremes...",
        depends_on=["fetch_data"],
    )

    workflow.add_step(
        name="report",
        handler="generate_report",
        action="Generating comprehensive weather report...",
        depends_on=["analyze"],
    )

    # Execute with context
    context = {"target_cities": ["New York", "London", "Tokyo", "Miami", "Sydney"]}

    print("Executing integrated workflow...")
    print("-" * 40)

    try:
        result = await agent.execute_workflow(workflow, context=context)

        print("\n✅ Workflow completed successfully!")

        # Show final report
        report_step = result.step_results.get("report")
        if report_step and report_step.status == StepStatus.COMPLETED:
            print("\n" + report_step.result)

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")


async def data_processing_workflow():
    """Data processing workflow with inline tool logic."""
    print("\n\n=== Data Processing Workflow ===\n")

    agent = WorkflowAgent(
        name="DataProcessor",
        instructions="Process and transform data through multiple stages.",
    )

    workflow = agent.create_workflow(
        name="data_pipeline", description="Multi-stage data processing pipeline"
    )

    # Data processing functions
    def load_sample_data(agent, step, context):
        """Load sample dataset."""
        # Simulate loading data
        sample_data = [
            {"id": 1, "value": 100, "category": "A", "date": "2024-01-01"},
            {"id": 2, "value": 150, "category": "B", "date": "2024-01-02"},
            {"id": 3, "value": 200, "category": "A", "date": "2024-01-03"},
            {"id": 4, "value": 120, "category": "C", "date": "2024-01-04"},
            {"id": 5, "value": 180, "category": "B", "date": "2024-01-05"},
        ]

        context["raw_data"] = sample_data
        return f"Loaded {len(sample_data)} records"

    def transform_data(agent, step, context):
        """Transform and enrich data."""
        raw_data = context.get("raw_data", [])

        transformed = []
        for record in raw_data:
            enhanced = record.copy()
            # Add computed fields
            enhanced["value_squared"] = record["value"] ** 2
            enhanced["is_high_value"] = record["value"] > 150
            enhanced["processing_time"] = datetime.now().isoformat()
            transformed.append(enhanced)

        context["transformed_data"] = transformed
        return f"Transformed {len(transformed)} records with enhanced fields"

    def aggregate_data(agent, step, context):
        """Aggregate data by category."""
        data = context.get("transformed_data", [])

        # Group by category
        aggregates = {}
        for record in data:
            cat = record["category"]
            if cat not in aggregates:
                aggregates[cat] = {
                    "category": cat,
                    "count": 0,
                    "total_value": 0,
                    "high_value_count": 0,
                }

            aggregates[cat]["count"] += 1
            aggregates[cat]["total_value"] += record["value"]
            if record["is_high_value"]:
                aggregates[cat]["high_value_count"] += 1

        # Calculate averages
        for cat_data in aggregates.values():
            cat_data["avg_value"] = round(
                cat_data["total_value"] / cat_data["count"], 2
            )

        context["aggregates"] = aggregates
        return json.dumps(aggregates, indent=2)

    # Register handlers
    agent.register_handler("load", load_sample_data)
    agent.register_handler("transform", transform_data)
    agent.register_handler("aggregate", aggregate_data)

    # Define pipeline steps
    workflow.add_step(name="load", handler="load", action="Loading sample dataset...")

    workflow.add_step(
        name="transform",
        handler="transform",
        action="Transforming and enriching data...",
        depends_on=["load"],
    )

    workflow.add_step(
        name="aggregate",
        handler="aggregate",
        action="Aggregating data by category...",
        depends_on=["transform"],
    )

    workflow.add_step(
        name="summarize",
        action="Create a summary of the data processing results",
        depends_on=["aggregate"],
    )

    print("Executing data processing pipeline...")

    try:
        result = await agent.execute_workflow(workflow)

        print("\n✅ Pipeline completed successfully!")

        # Show aggregation results
        agg_step = result.step_results.get("aggregate")
        if agg_step and agg_step.status == StepStatus.COMPLETED:
            print("\n📊 Aggregation Results:")
            print(agg_step.result)

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")


async def main():
    """Run integrated workflow examples."""
    print("AgentiCraft Workflows with Integrated Tool Logic")
    print("=" * 60)
    print("\nThis approach embeds tool functionality directly in handlers,")
    print("avoiding @tool decorator issues while maintaining full functionality.\n")

    import os

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return

    # Run examples
    await integrated_weather_workflow()
    await data_processing_workflow()

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("\nBenefits of this approach:")
    print("- No @tool decorator issues")
    print("- Full control over data flow")
    print("- Complex logic without framework limitations")
    print("- Works reliably with current AgentiCraft")


if __name__ == "__main__":
    asyncio.run(main())
