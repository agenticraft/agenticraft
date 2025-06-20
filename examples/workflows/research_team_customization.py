"""Research Team Customization Example.

This example shows how to customize the ResearchTeam workflow for
different use cases and requirements.
"""

import asyncio
import os

from dotenv import load_dotenv

from agenticraft.workflows import ResearchTeam

# Load environment variables
load_dotenv()


async def main():
    """Demonstrate ResearchTeam customization options."""
    
    print("🔧 ResearchTeam Customization Examples")
    print("=" * 50)
    
    # Example 1: Small focused team for quick research
    print("\n1️⃣ Small Team for Quick Research")
    print("-" * 40)
    
    quick_team = ResearchTeam(
        size=3,  # Minimal team: 1 researcher, 1 analyst, 1 writer
        name="QuickResearch"
    )
    
    result = await quick_team.research(
        topic="Python async programming best practices",
        depth="quick",  # Quick overview
        audience="technical"  # Technical audience
    )
    
    print(f"✓ Completed in {result['metadata']['duration_seconds']:.1f}s with {result['metadata']['agents_involved']} agents")
    print(f"✓ Key findings: {len(result['key_findings'])}")
    
    # Example 2: Large team for comprehensive analysis
    print("\n2️⃣ Large Team for Deep Research")
    print("-" * 40)
    
    deep_team = ResearchTeam(
        size=8,  # Larger team for comprehensive coverage
        name="DeepDive",
        model="gpt-4"  # Specify a specific model
    )
    
    # Show team composition
    status = await deep_team.get_team_status()
    print(f"Team composition: {status['composition']}")
    
    result = await deep_team.research(
        topic="Quantum computing applications in cryptography",
        depth="comprehensive",
        audience="technical",
        focus_areas=[
            "Post-quantum cryptography",
            "Current vulnerabilities",
            "Migration strategies"
        ]
    )
    
    print(f"✓ Generated {len(result['sections'])} report sections")
    print(f"✓ Recommendations: {len(result['recommendations'])}")
    
    # Example 3: Executive-focused team
    print("\n3️⃣ Executive Briefing Team")
    print("-" * 40)
    
    exec_team = ResearchTeam(
        size=5,
        name="ExecBriefing",
        provider="anthropic",  # Use Anthropic's Claude
        model="claude-3-sonnet-20240229"
    )
    
    result = await exec_team.research(
        topic="Competitive analysis: AWS vs Azure vs GCP in 2024",
        depth="standard",
        audience="executive",
        context={
            "company_focus": "Enterprise migrations",
            "budget_range": "$1M-$10M annually",
            "key_concerns": ["cost", "security", "support"]
        }
    )
    
    print("✓ Executive summary generated")
    print(f"✓ Business-focused recommendations: {len(result['recommendations'])}")
    
    # Example 4: Dynamic team adjustment
    print("\n4️⃣ Dynamic Team Scaling")
    print("-" * 40)
    
    adaptive_team = ResearchTeam(size=4, name="AdaptiveTeam")
    
    # Start with initial research
    print("Initial team:", (await adaptive_team.get_team_status())['composition'])
    
    # Scale up for more complex research
    print("\nScaling up team for complex topic...")
    await adaptive_team.adjust_team(
        add_researchers=2,  # Add more researchers
        add_analysts=1      # Add another analyst
    )
    
    print("Scaled team:", (await adaptive_team.get_team_status())['composition'])
    
    # Example 5: Custom context and focus
    print("\n5️⃣ Industry-Specific Research")
    print("-" * 40)
    
    industry_team = ResearchTeam(
        size=6,
        name="HealthcareResearch"
    )
    
    result = await industry_team.research(
        topic="AI applications in personalized medicine",
        depth="comprehensive",
        audience="technical",
        focus_areas=[
            "FDA regulations",
            "HIPAA compliance",
            "Clinical trial integration"
        ],
        context={
            "industry": "Healthcare",
            "regulatory_framework": "US",
            "target_market": "Hospital systems",
            "implementation_timeline": "2-3 years"
        }
    )
    
    print("✓ Industry-specific research completed")
    print("✓ Regulatory considerations included")
    
    # Show reasoning transparency
    print("\n🧠 Reasoning Transparency")
    print("-" * 40)
    print("Sample delegation reasoning:")
    if result['reasoning_trace']:
        for trace in result['reasoning_trace'][:2]:
            if 'task' in trace:
                print(f"• Task: {trace['task'][:50]}...")
                print(f"  Delegated to: {trace.get('delegated_to', 'N/A')}")


if __name__ == "__main__":
    # Check for API key
    if not any(os.getenv(key) for key in [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
        "AZURE_OPENAI_API_KEY", "GROQ_API_KEY"
    ]):
        print("❌ No API key found!")
        print("Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.")
    else:
        asyncio.run(main())
