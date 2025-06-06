#!/usr/bin/env python3
"""AgentiCraft Quickstart - Build a Smart Research Assistant in 5 Minutes!

This example shows how to create an AI agent that can:
1. Use multiple tools to gather information
2. Show its reasoning process transparently
3. Produce well-structured outputs
"""

import os
from datetime import datetime
from agenticraft import Agent, tool


@tool
def search_web(query: str, max_results: int = 3) -> str:
    """Search the web for current information."""
    # In production, this would use a real search API
    return f"Found {max_results} relevant results about '{query}'"


@tool 
def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment and key themes in text."""
    # Simplified for demo
    return {
        "sentiment": "positive",
        "confidence": 0.85,
        "key_themes": ["innovation", "simplicity", "transparency"]
    }


@tool
def create_summary(points: list, style: str = "bullet") -> str:
    """Create a formatted summary from key points."""
    if style == "bullet":
        return "\n".join(f"• {point}" for point in points)
    else:
        return " ".join(points)


def main():
    """5-minute quickstart showing AgentiCraft's power."""
    print("🚀 AgentiCraft 5-Minute Quickstart")
    print("=" * 60)
    
    # Create a research assistant with multiple tools
    assistant = Agent(
        name="ResearchAssistant",
        instructions="""You are a smart research assistant that helps users 
        gather and analyze information. You're transparent about your process
        and always structure your findings clearly.""",
        tools=[search_web, analyze_sentiment, create_summary],
        model="gpt-4"  # or "gpt-3.5-turbo" for faster/cheaper
    )
    
    # Example 1: Simple question
    print("\n📝 Example 1: Simple Question")
    print("-" * 40)
    
    response = assistant.run("What are the main benefits of Python for data science?")
    print(f"Response: {response.content}")
    
    # Example 2: Complex research with reasoning
    print("\n\n📝 Example 2: Complex Research Task")
    print("-" * 40)
    
    complex_query = """
    Research AgentiCraft framework and create a brief analysis covering:
    1. Main features and benefits
    2. How it compares to alternatives
    3. Best use cases
    Show your research process.
    """
    
    response = assistant.run(complex_query)
    
    # Show reasoning (unique to AgentiCraft!)
    print("\n🧠 Assistant's Reasoning Process:")
    print(response.reasoning)
    
    # Show tools used
    print("\n🔧 Tools Used:")
    for tool_call in response.tool_calls:
        print(f"  - {tool_call['name']}")
    
    # Show final response
    print("\n📊 Research Results:")
    print(response.content)
    
    # Example 3: Workflow with memory
    print("\n\n📝 Example 3: Multi-step Workflow")
    print("-" * 40)
    
    # First step
    response1 = assistant.run("Find information about sustainable AI practices")
    print(f"Step 1 Result: {response1.content[:100]}...")
    
    # Second step (agent remembers context)
    response2 = assistant.run("Based on what you found, what are the top 3 recommendations?")
    print(f"\nStep 2 Result: {response2.content}")
    
    print("\n\n✨ What Makes AgentiCraft Special:")
    print("  ✓ See how your agent thinks (reasoning transparency)")
    print("  ✓ Use multiple tools seamlessly")
    print("  ✓ Build complex workflows easily")
    print("  ✓ Production-ready from the start")
    print("  ✓ No complex abstractions to learn")
    
    print("\n🎯 Next Steps:")
    print("  1. Install: pip install agenticraft")
    print("  2. Set your API key: export OPENAI_API_KEY='your-key'")
    print("  3. Copy this example and customize")
    print("  4. Build something amazing!")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  No API key found!")
        print("Set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nOr create a .env file with:")
        print("  OPENAI_API_KEY=your-key-here")
        print("\n" + "-"*60)
        
    main()
