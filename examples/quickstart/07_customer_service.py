"""Customer Service Desk Quickstart - Multi-tier support in minutes.

This is the simplest possible example of using the CustomerServiceDesk hero workflow.
Deploy a complete customer service system with just a few lines!
"""

import asyncio
import os

from dotenv import load_dotenv

from agenticraft.workflows import CustomerServiceDesk

# Load environment variables
load_dotenv()


async def main():
    """The 5-minute Customer Service setup."""
    
    print("🎧 CustomerServiceDesk - Quick Setup")
    print("=" * 40)
    
    # That's it! One line to create your service desk
    desk = CustomerServiceDesk()
    
    # Handle a customer inquiry
    response = await desk.handle(
        customer_id="customer_123",
        inquiry="I'm having trouble logging into my account"
    )
    
    # Show the results
    print(f"\n👤 Customer: {response['response']}")
    print(f"\n🤖 Handled by: {response['agent']}")
    print(f"⏱️  Resolution time: {response['resolution_time']:.1f} seconds")
    
    if response['escalated']:
        print("⬆️  This issue was escalated to a specialist")
    
    # Show desk status
    status = await desk.get_desk_status()
    print(f"\n📊 Service Desk Status:")
    print(f"   Total agents: {status['mesh_status']['total_nodes']}")
    print(f"   Capacity: {status['mesh_status']['total_capacity']} concurrent requests")
    print(f"   Tiers: L1, L2, Expert")


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
