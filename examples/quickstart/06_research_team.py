"""Research Team Quickstart - 5 Minutes to Multi-Agent Research.

This is the simplest possible example of using the ResearchTeam hero workflow.
In just a few lines of code, you get a full multi-agent research team!
"""

import asyncio
import os

from dotenv import load_dotenv

from agenticraft.workflows import ResearchTeam

# Load environment variables
load_dotenv()


async def main():
    """The 5-minute Research Team setup."""
    
    print("🚀 ResearchTeam - 5 Minute Setup")
    print("=" * 40)
    
    # That's it! One line to create your research team
    team = ResearchTeam()
    
    # One line to conduct research
    report = await team.research("AI frameworks market analysis")
    
    # Show the results
    print("\n📋 Executive Summary:")
    print(report["executive_summary"])
    
    print("\n🔍 Key Findings:")
    for finding in report["key_findings"]:
        print(f"• {finding}")
    
    print(f"\n✅ Research completed in {report['metadata']['duration_seconds']:.1f} seconds!")
    print(f"   by {report['metadata']['agents_involved']} specialized agents")


if __name__ == "__main__":
    # Check for any supported API key
    api_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "AZURE_OPENAI_API_KEY": "Azure OpenAI",
        "GOOGLE_API_KEY": "Google",
        "GROQ_API_KEY": "Groq",
        "MISTRAL_API_KEY": "Mistral",
        "TOGETHER_API_KEY": "Together AI"
    }
    
    found_key = False
    for key, provider in api_keys.items():
        if os.getenv(key):
            print(f"✅ Using {provider} API")
            found_key = True
            break
    
    if not found_key:
        print("❌ No API key found!")
        print("\nPlease set one of these in your .env file:")
        for key, provider in api_keys.items():
            print(f"  {key}='your-key-here'  # For {provider}")
    else:
        # Run the example
        asyncio.run(main())
