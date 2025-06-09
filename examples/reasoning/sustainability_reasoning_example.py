#!/usr/bin/env python3
"""Simple Reasoning Transparency Example - Sustainability Use Case

This beginner-friendly example demonstrates AgentiCraft's reasoning transparency
feature through a practical sustainability advisor scenario. It shows how agents
expose their thought process while solving real-world problems.

For a more comprehensive reasoning transparency guide with multiple patterns,
see reasoning_transparency.py in this directory.
"""

from agenticraft import Agent, tool
from agenticraft.core.reasoning import ChainOfThought


@tool
def search_knowledge(query: str) -> str:
    """Search for information in knowledge base."""
    # Simulated knowledge base
    knowledge = {
        "renewable energy": "Solar, wind, hydro, and geothermal are main renewable sources",
        "climate impact": "Buildings account for 40% of global energy consumption",
        "green building": "LEED certification, passive house design, smart systems",
        "sustainable materials": "Bamboo, recycled steel, reclaimed wood, hempcrete",
    }

    for key, value in knowledge.items():
        if key in query.lower():
            return value
    return "No specific information found, but I can reason about this."


@tool
def calculate_savings(current_usage: float, reduction_percent: float) -> dict:
    """Calculate energy savings from efficiency improvements."""
    savings = current_usage * (reduction_percent / 100)
    remaining = current_usage - savings
    return {
        "current_usage_kwh": current_usage,
        "reduction_percent": reduction_percent,
        "savings_kwh": savings,
        "new_usage_kwh": remaining,
        "cost_savings_usd": savings * 0.12,  # $0.12 per kWh average
    }


def main():
    """Demonstrate reasoning transparency with a practical example."""
    print("🧠 AgentiCraft Simple Reasoning Transparency Demo")
    print("Sustainability Advisor Example")
    print("=" * 60)

    # Create an agent with reasoning transparency
    agent = Agent(
        name="SustainabilityAdvisor",
        instructions="""You are an expert in sustainable building practices. 
        You help people make their buildings more energy efficient.
        Always explain your reasoning step by step.""",
        tools=[search_knowledge, calculate_savings],
        reasoning_pattern=ChainOfThought(),
    )

    # Complex query that requires reasoning
    query = """
    I have a 2000 sq ft office building using 50,000 kWh annually. 
    What are the best ways to reduce energy consumption, and how much 
    could I save with a 30% reduction?
    """

    print("\n📝 User Query:")
    print(query.strip())

    # Get response with reasoning
    response = agent.run(query)

    # Show the reasoning process
    print("\n🧠 Agent's Reasoning Process:")
    print("-" * 60)
    print(response.reasoning)

    # Show tool usage
    if response.tool_calls:
        print("\n🔧 Tools Used:")
        for tool_call in response.tool_calls:
            print(f"  - {tool_call['name']}: {tool_call['arguments']}")

    # Show final response
    print("\n💡 Final Response:")
    print("-" * 60)
    print(response.content)

    # Show how this builds trust
    print("\n✨ Why Reasoning Transparency Matters:")
    print("  - You can verify the agent's logic")
    print("  - You understand which tools were used and why")
    print("  - You can debug if something goes wrong")
    print("  - You can improve prompts based on reasoning patterns")
    print("  - You build trust through transparency")


if __name__ == "__main__":
    # Note: This is a demonstration. In production, you would need
    # to set up your OpenAI API key and the agent would make real LLM calls.
    print("\n⚠️  Note: This example shows the structure. In production,")
    print("    set your OPENAI_API_KEY to see real reasoning traces.")

    # Simulated output for demonstration
    print("\n" + "=" * 60)
    print("🧠 SIMULATED OUTPUT (with real API key, you'd see actual reasoning):")
    print("=" * 60)

    print("\n🧠 Agent's Reasoning Process:")
    print("-" * 60)
    print(
        """Step 1: Understanding the problem
- Building size: 2000 sq ft office
- Current usage: 50,000 kWh/year (25 kWh/sq ft - quite high)
- Goal: Reduce consumption and calculate 30% savings

Step 2: Searching for energy reduction strategies
- Searching knowledge base for "green building" practices
- Found: LEED certification, passive house design, smart systems

Step 3: Searching for renewable energy options
- Searching for "renewable energy" solutions
- Found: Solar, wind, hydro, and geothermal options

Step 4: Calculating potential savings
- Using calculator tool with current_usage=50000, reduction_percent=30
- Results: 15,000 kWh saved, $1,800/year cost savings

Step 5: Formulating comprehensive response
- Prioritizing most effective solutions for office buildings
- Including both immediate and long-term strategies
- Providing specific calculated savings"""
    )

    print("\n🔧 Tools Used:")
    print("  - search_knowledge: {'query': 'green building'}")
    print("  - search_knowledge: {'query': 'renewable energy'}")
    print("  - calculate_savings: {'current_usage': 50000, 'reduction_percent': 30}")

    print("\n💡 Final Response:")
    print("-" * 60)
    print(
        """Based on my analysis of your 2000 sq ft office building using 50,000 kWh annually:

**Energy Reduction Strategies:**

1. **Immediate Actions** (10-15% reduction):
   - LED lighting upgrade throughout
   - Smart thermostats and occupancy sensors
   - Weather stripping and insulation improvements

2. **Medium-term Improvements** (15-20% reduction):
   - Energy-efficient HVAC system upgrade
   - Smart building management system
   - Window films or double-glazing

3. **Long-term Investments** (20-30%+ reduction):
   - Solar panel installation
   - Green roof or cool roof technology
   - Full building envelope upgrade

**30% Reduction Calculation:**
- Current usage: 50,000 kWh/year
- 30% reduction: 15,000 kWh saved
- New usage: 35,000 kWh/year
- **Annual cost savings: $1,800** (at $0.12/kWh)

Your building currently uses 25 kWh/sq ft/year, which is above average for offices 
(typical is 15-20). This means you have excellent potential for savings. I recommend 
starting with an energy audit to identify the biggest opportunities specific to 
your building."""
    )
