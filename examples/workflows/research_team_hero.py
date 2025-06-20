"""Research Team Hero Workflow Example.

This example demonstrates the ResearchTeam hero workflow - a multi-agent
research team that can be deployed in 5 minutes to conduct professional
research on any topic.

The example shows:
1. Quick setup with default configuration
2. Customized team sizes and composition
3. Different research depths
4. Multiple audience types
5. Accessing research metadata and reasoning
"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv

from agenticraft.workflows import ResearchTeam

# Load environment variables
load_dotenv()


async def main():
    """Run Research Team examples."""
    
    print("🚀 AgentiCraft Research Team - Hero Workflow")
    print("=" * 60)
    print("Deploy a multi-agent research team in 5 minutes!")
    print()
    
    # Example 1: Quick 5-minute setup
    print("📚 Example 1: Quick Research (5-minute setup)")
    print("-" * 50)
    
    # Create a research team with default settings
    team = ResearchTeam()
    
    # Show team composition
    status = await team.get_team_status()
    print(f"Team: {status['team_name']}")
    print(f"Size: {status['team_size']} agents")
    print(f"Composition: {status['composition']}")
    print()
    
    # Conduct quick research
    print("Researching: 'Latest trends in AI agent frameworks'")
    print("Please wait while the team conducts research...\n")
    
    try:
        report = await team.research(
            topic="Latest trends in AI agent frameworks",
            depth="quick",
            audience="general"
        )
        
        # Show results
        print("✅ Research Complete!")
        print(f"Duration: {report['metadata']['duration_seconds']:.1f} seconds")
        print(f"Agents involved: {report['metadata']['agents_involved']}")
        print()
        
        print("📋 Executive Summary:")
        print("-" * 40)
        print(report["executive_summary"])
        print()
        
        print("🔍 Key Findings:")
        for i, finding in enumerate(report["key_findings"], 1):
            print(f"{i}. {finding}")
        print()
        
    except Exception as e:
        print(f"❌ Error in quick research: {e}")
    
    # Example 2: Customized team for technical audience
    print("\n📚 Example 2: Technical Deep Dive")
    print("-" * 50)
    
    # Create a larger team for comprehensive research
    tech_team = ResearchTeam(
        size=7,  # Larger team for deeper research
        name="TechResearchTeam"
    )
    
    # Show new team composition
    status = await tech_team.get_team_status()
    print(f"Enhanced team composition: {status['composition']}")
    print()
    
    print("Researching: 'Multi-agent coordination patterns'")
    print("Depth: Comprehensive | Audience: Technical")
    print("This may take a few minutes...\n")
    
    try:
        tech_report = await tech_team.research(
            topic="Multi-agent coordination patterns in distributed systems",
            depth="comprehensive",
            audience="technical",
            focus_areas=[
                "Consensus mechanisms",
                "Load balancing strategies",
                "Fault tolerance"
            ]
        )
        
        print("✅ Technical Research Complete!")
        print(f"Duration: {tech_report['metadata']['duration_seconds']:.1f} seconds")
        print(f"Total subtasks: {tech_report['metadata']['total_subtasks']}")
        print()
        
        # Show report sections
        print("📑 Report Sections:")
        for section_name in tech_report["sections"].keys():
            print(f"  • {section_name.replace('_', ' ').title()}")
        print()
        
        print("💡 Recommendations:")
        for i, rec in enumerate(tech_report["recommendations"][:3], 1):
            print(f"{i}. {rec}")
        print()
        
    except Exception as e:
        print(f"❌ Error in technical research: {e}")
    
    # Example 3: Executive briefing
    print("\n📚 Example 3: Executive Briefing")
    print("-" * 50)
    
    # Use standard team size for executive research
    exec_team = ResearchTeam(size=5, name="ExecTeam")
    
    print("Researching: 'AI investment opportunities 2024'")
    print("Audience: Executive | Focus: Business Impact")
    print()
    
    try:
        exec_report = await exec_team.research(
            topic="AI investment opportunities in enterprise software 2024",
            depth="standard",
            audience="executive",
            context={
                "focus": "ROI and market potential",
                "timeframe": "next 12-24 months"
            }
        )
        
        print("✅ Executive Briefing Ready!")
        print()
        
        print("📊 Executive Summary:")
        print("-" * 40)
        print(exec_report["executive_summary"])
        print()
        
        # Show reasoning transparency
        print("🧠 Team Reasoning (Sample):")
        reasoning = exec_report["reasoning_trace"]
        if reasoning and len(reasoning) > 0:
            sample = reasoning[0]
            if "reasoning" in sample:
                print(f"Coordinator: {sample['reasoning']}")
        print()
        
    except Exception as e:
        print(f"❌ Error in executive research: {e}")
    
    # Example 4: Dynamic team adjustment
    print("\n📚 Example 4: Dynamic Team Adjustment")
    print("-" * 50)
    
    print("Starting with minimal team...")
    minimal_team = ResearchTeam(size=3, name="AdaptiveTeam")
    
    status = await minimal_team.get_team_status()
    print(f"Initial: {status['composition']}")
    
    print("\nScaling up for complex research...")
    new_comp = await minimal_team.adjust_team(
        add_researchers=2,
        add_analysts=1
    )
    print(f"Adjusted: {new_comp}")
    print()
    
    # Show final tips
    print("💡 Pro Tips:")
    print("-" * 50)
    print("1. Use 'quick' depth for rapid overviews (1-2 minutes)")
    print("2. Use 'comprehensive' depth for detailed analysis (3-5 minutes)")
    print("3. Adjust team size based on topic complexity (3-10 agents)")
    print("4. Specify focus_areas to guide research direction")
    print("5. Check reasoning_trace to understand team decisions")
    print()
    
    print("🎯 Ready to deploy your own research team!")
    print("Just import and use: ResearchTeam().research('your topic')")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: No API key found")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
        print("Example: OPENAI_API_KEY='your-key-here'")
    else:
        # Show which provider is configured
        if os.getenv("OPENAI_API_KEY"):
            print(f"✅ OpenAI API key found")
        if os.getenv("ANTHROPIC_API_KEY"):
            print(f"✅ Anthropic API key found")
        print()
        
        # Run examples
        asyncio.run(main())
