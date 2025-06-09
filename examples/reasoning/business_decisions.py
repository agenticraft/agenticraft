#!/usr/bin/env python3
"""
Real-world example: Using reasoning patterns for decision making.
This example shows how to use AgentiCraft reasoning for a practical scenario.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent / ".env")

from agenticraft.agents.reasoning import ReasoningAgent
from agenticraft.core.tool import BaseTool, ToolDefinition

# === Custom Tools for Business Analysis ===


class MarketDataTool(BaseTool):
    """Tool to get market data."""

    name = "market_data"
    description = "Get market data and trends for a product category"

    async def arun(self, category: str) -> str:
        """Simulate market data retrieval."""
        # In production, this would call a real API
        market_data = {
            "smartphones": {
                "market_size": "$500B",
                "growth_rate": "5.2%",
                "top_players": ["Apple", "Samsung", "Xiaomi"],
                "trends": ["Foldable screens", "AI integration", "5G adoption"],
            },
            "electric_vehicles": {
                "market_size": "$250B",
                "growth_rate": "23.1%",
                "top_players": ["Tesla", "BYD", "Volkswagen"],
                "trends": [
                    "Autonomous driving",
                    "Battery tech",
                    "Charging infrastructure",
                ],
            },
            "sustainable_fashion": {
                "market_size": "$15B",
                "growth_rate": "12.5%",
                "top_players": ["Patagonia", "Eileen Fisher", "Reformation"],
                "trends": ["Circular economy", "Transparency", "Bio-materials"],
            },
        }

        data = market_data.get(
            category.lower(),
            {
                "market_size": "Unknown",
                "growth_rate": "Unknown",
                "trends": ["Limited data available"],
            },
        )

        return f"Market data for {category}: Size: {data['market_size']}, Growth: {data['growth_rate']}, Trends: {', '.join(data['trends'])}"

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Product category to analyze",
                    }
                },
                "required": ["category"],
            },
        )


class CostCalculatorTool(BaseTool):
    """Tool to calculate business costs."""

    name = "cost_calculator"
    description = "Calculate startup costs for a business venture"

    async def arun(self, venture_type: str, scale: str = "small") -> str:
        """Calculate estimated costs."""
        base_costs = {
            "app": {"small": 50000, "medium": 200000, "large": 1000000},
            "restaurant": {"small": 100000, "medium": 500000, "large": 2000000},
            "ecommerce": {"small": 20000, "medium": 100000, "large": 500000},
            "consulting": {"small": 10000, "medium": 50000, "large": 200000},
        }

        venture_key = venture_type.lower()
        if venture_key in base_costs:
            cost = base_costs[venture_key].get(
                scale.lower(), base_costs[venture_key]["small"]
            )
            return f"Estimated startup cost for {scale} {venture_type}: ${cost:,}"
        else:
            return f"Estimated startup cost for {venture_type}: $50,000-$500,000 depending on scale"

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "venture_type": {
                        "type": "string",
                        "description": "Type of business venture",
                    },
                    "scale": {
                        "type": "string",
                        "description": "Scale: small, medium, or large",
                        "default": "small",
                    },
                },
                "required": ["venture_type"],
            },
        )


# === Business Decision Scenarios ===


async def startup_decision_example():
    """Example: Deciding on a startup idea using reasoning."""
    print("\n🚀 STARTUP DECISION EXAMPLE")
    print("=" * 60)

    # Get provider configuration
    provider_name, model = get_best_provider_config()

    # Scenario 1: Use Tree of Thoughts for exploring options
    print("\n1️⃣ Exploring Startup Ideas (Tree of Thoughts)")
    print("-" * 40)

    explorer = ReasoningAgent(
        name="StartupIdeaExplorer",
        instructions="You are a startup advisor exploring innovative business ideas.",
        reasoning_pattern="tree_of_thoughts",
        pattern_config={"max_depth": 2, "beam_width": 3},
        provider=provider_name,
        model=model,
    )

    exploration_prompt = """
    I have $100,000 to invest in a startup. I have experience in software development
    and interest in sustainability. What are the best startup opportunities that combine
    technology and environmental impact?
    """

    print("Question:", exploration_prompt.strip())
    print("\nExploring options...")

    response = await explorer.think_and_act(exploration_prompt)
    print("\nTop Ideas Found:")
    print(response.content)

    # Scenario 2: Use ReAct for market research
    print("\n\n2️⃣ Market Research (ReAct Pattern)")
    print("-" * 40)

    researcher = ReasoningAgent(
        name="MarketResearcher",
        instructions="You are a market research analyst who gathers data to validate business ideas.",
        reasoning_pattern="react",
        tools=[MarketDataTool(), CostCalculatorTool()],
        provider=provider_name,
        model=model,
    )

    research_prompt = """
    Research the sustainable fashion market. What's the market size, growth rate,
    and startup costs for launching a sustainable clothing brand?
    """

    print("Research Task:", research_prompt.strip())
    print("\nConducting research...")

    response = await researcher.think_and_act(research_prompt)
    print("\nResearch Findings:")
    print(response.content)

    # Scenario 3: Use Chain of Thought for decision analysis
    print("\n\n3️⃣ Decision Analysis (Chain of Thought)")
    print("-" * 40)

    analyst = ReasoningAgent(
        name="DecisionAnalyst",
        instructions="You are a business analyst who helps make strategic decisions through careful analysis.",
        reasoning_pattern="chain_of_thought",
        pattern_config={"min_confidence": 0.7},
        provider=provider_name,
        model=model,
    )

    decision_prompt = """
    Based on the following factors, should I start a sustainable fashion e-commerce platform?
    - Budget: $100,000
    - Market growth: 12.5% annually
    - Competition: Moderate, with room for differentiation
    - Personal experience: Software development, no fashion experience
    - Time commitment: Can dedicate full-time
    
    Analyze the pros and cons and give a recommendation.
    """

    print("Decision to Analyze:", decision_prompt.strip())
    print("\nAnalyzing step by step...")

    response = await analyst.think_and_act(decision_prompt)

    # Show reasoning steps
    if response.reasoning_steps:
        print("\nReasoning Process:")
        for step in response.reasoning_steps[:5]:  # Show first 5 steps
            print(f"  Step {step.number}: {step.description}")

    print("\nRecommendation:")
    print(response.content)


async def problem_solving_example():
    """Example: Solving a complex problem using multiple patterns."""
    print("\n\n🔧 PROBLEM SOLVING EXAMPLE")
    print("=" * 60)

    provider_name, model = get_best_provider_config()

    # The problem
    problem = """
    Our e-commerce website has seen a 30% drop in conversion rate over the last month.
    Customer support tickets about checkout issues have increased by 50%.
    Mobile traffic is up 40% but mobile conversions are down 60%.
    What's wrong and how do we fix it?
    """

    print("Problem:", problem.strip())

    # Step 1: Diagnose with Chain of Thought
    print("\n📊 Diagnosing the Issue (Chain of Thought)")
    print("-" * 40)

    diagnostician = ReasoningAgent(
        name="Diagnostician",
        reasoning_pattern="chain_of_thought",
        provider=provider_name,
        model=model,
    )

    diagnosis = await diagnostician.think_and_act(
        f"Diagnose this e-commerce problem: {problem}"
    )

    print("Diagnosis:", diagnosis.content[:300] + "...")

    # Step 2: Generate solutions with Tree of Thoughts
    print("\n💡 Generating Solutions (Tree of Thoughts)")
    print("-" * 40)

    solution_designer = ReasoningAgent(
        name="SolutionDesigner",
        reasoning_pattern="tree_of_thoughts",
        pattern_config={"max_depth": 2, "beam_width": 3},
        provider=provider_name,
        model=model,
    )

    solutions = await solution_designer.think_and_act(
        f"Based on this diagnosis: {diagnosis.content[:200]}... Generate multiple solution approaches."
    )

    print("Solution Options:", solutions.content[:300] + "...")

    print("\n✅ Problem-solving process complete!")


def get_best_provider_config():
    """Get the best available provider configuration."""
    if os.getenv("OPENAI_API_KEY"):
        print("[Using OpenAI]")
        return "openai", "gpt-4"
    elif os.getenv("ANTHROPIC_API_KEY"):
        print("[Using Anthropic]")
        return "anthropic", "claude-3-opus-20240229"
    else:
        print("[Using Ollama - ensure it's running]")
        return "ollama", "llama2"


async def main():
    """Run real-world examples."""
    print("\n🌟 AgentiCraft Reasoning: Real-World Examples")
    print("=" * 60)

    print("\nThese examples show how to use reasoning patterns for:")
    print("• Business decisions")
    print("• Problem solving")
    print("• Research and analysis")

    # Check for API availability
    if not any([os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY")]):
        print("\n⚠️  No API keys found. Using Ollama.")
        print("For best results, add API keys to your .env file.")

        # Quick Ollama check
        try:
            import httpx

            response = httpx.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code != 200:
                print("❌ Ollama is not running! Please run: ollama serve")
                return
        except:
            print("❌ Cannot connect to Ollama! Please run: ollama serve")
            return

    try:
        # Run examples
        await startup_decision_example()
        await problem_solving_example()

        print("\n" + "=" * 60)
        print("✨ Examples completed successfully!")

        print("\n💡 Key Takeaways:")
        print("• Tree of Thoughts: Great for exploring multiple options")
        print("• ReAct: Perfect for research and data gathering")
        print("• Chain of Thought: Ideal for systematic analysis")
        print("• Combine patterns for complex problems!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        if os.getenv("DEBUG"):
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
