"""Customer Service Desk Hero Workflow Example.

This example demonstrates the CustomerServiceDesk hero workflow - a multi-tier
customer service system with intelligent routing, load balancing, and human
escalation capabilities.

The example shows:
1. Basic customer inquiry handling
2. Automatic escalation through tiers
3. Human-in-the-loop approval
4. API key authentication
5. Multiple customer scenarios
"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv

from agenticraft.workflows import CustomerServiceDesk
from agenticraft.agents.patterns import EscalationPriority

# Load environment variables
load_dotenv()


async def main():
    """Run Customer Service Desk examples."""
    
    print("🎧 AgentiCraft Customer Service Desk - Hero Workflow")
    print("=" * 60)
    print("Deploy a complete multi-tier support system!")
    print()
    
    # Example 1: Basic setup
    print("📞 Example 1: Simple Customer Inquiry")
    print("-" * 50)
    
    # Create a service desk with default settings
    desk = CustomerServiceDesk()
    
    # Show desk composition
    status = await desk.get_desk_status()
    print(f"Service Desk: {desk.config.name}")
    print(f"Tiers: {desk.tiers}")
    print(f"Total agents: {status['mesh_status']['total_nodes']}")
    print(f"Authentication: {'Enabled' if desk.auth_enabled else 'Disabled'}")
    print()
    
    # Handle a simple inquiry
    print("Customer: 'How do I reset my password?'")
    print("Processing...\n")
    
    try:
        response = await desk.handle(
            customer_id="cust_001",
            inquiry="How do I reset my password?",
            api_key="test-key-123"  # Using default test key
        )
        
        print("✅ Response delivered!")
        print(f"Agent: {response['agent']}")
        print(f"Response: {response['response'][:200]}...")
        print(f"Resolution time: {response['resolution_time']:.1f} seconds")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Complex issue requiring escalation
    print("\n📞 Example 2: Complex Billing Issue (Escalation)")
    print("-" * 50)
    
    print("Customer: 'I was charged twice for my subscription and need a refund'")
    print("This will likely escalate through tiers...\n")
    
    try:
        response = await desk.handle(
            customer_id="cust_002",
            inquiry="I was charged twice for my subscription last month and need a refund. This is the third time this has happened!",
            context={
                "subscription_id": "sub_123",
                "amount": "$99.99",
                "charge_date": "2024-01-15"
            },
            priority=8,  # High priority
            api_key="test-key-123"
        )
        
        print("✅ Issue handled!")
        print(f"Final agent: {response['agent']}")
        print(f"Escalated: {'Yes' if response['escalated'] else 'No'}")
        print(f"Resolution path: {len(response['resolution_path'])} agents involved")
        
        # Show the path
        print("\nResolution path:")
        for step in response['resolution_path']:
            print(f"  → {step['agent']} ({step['role']})")
        
        print(f"\nResolution time: {response['resolution_time']:.1f} seconds")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 3: Custom configuration
    print("\n📞 Example 3: Custom Service Desk Configuration")
    print("-" * 50)
    
    # Create a specialized desk with custom tiers
    custom_desk = CustomerServiceDesk(
        tiers=["Support", "Technical", "Engineering", "Management"],
        agents_per_tier=[4, 3, 2, 1],
        name="TechSupportDesk"
    )
    
    # Add human reviewers
    custom_desk.add_human_reviewer(
        reviewer_id="john_doe",
        name="John Doe",
        max_concurrent=2,
        specialties={"refunds", "complaints"}
    )
    
    # Add custom API key
    custom_desk.add_api_key(
        api_key="premium-client-key",
        client_id="premium_client",
        client_name="Premium Corp",
        permissions={"customer_service", "escalation", "priority"}
    )
    
    print(f"Created custom desk: {custom_desk.config.name}")
    print(f"Tiers: {custom_desk.tiers}")
    print(f"Total agents: {sum(custom_desk.agents_per_tier)}")
    print()
    
    # Handle technical issue
    print("Customer: 'The API is returning 500 errors intermittently'")
    
    try:
        response = await custom_desk.handle(
            customer_id="premium_001",
            inquiry="Our production API integration is returning 500 errors intermittently. This is affecting our customers.",
            context={
                "api_endpoint": "/api/v2/process",
                "error_rate": "15%",
                "started": "2 hours ago"
            },
            priority=9,  # Very high priority
            api_key="premium-client-key"
        )
        
        print("✅ Technical issue addressed!")
        print(f"Handled by: {response['agent']}")
        print(f"Topic identified: {response['topic']}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 4: Load testing and metrics
    print("\n📞 Example 4: Handling Multiple Customers")
    print("-" * 50)
    
    print("Simulating multiple customer inquiries...")
    
    # Test inquiries
    test_inquiries = [
        ("cust_101", "What are your business hours?", 3),
        ("cust_102", "I can't access my account", 5),
        ("cust_103", "How do I upgrade my plan?", 4),
        ("cust_104", "Bug report: app crashes on startup", 7),
        ("cust_105", "Request for enterprise pricing", 6),
    ]
    
    # Handle all inquiries concurrently
    tasks = []
    for customer_id, inquiry, priority in test_inquiries:
        task = desk.handle(
            customer_id=customer_id,
            inquiry=inquiry,
            priority=priority,
            api_key="test-key-123"
        )
        tasks.append(task)
    
    # Wait for all to complete
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Show results
    successful = sum(1 for r in responses if not isinstance(r, Exception))
    print(f"\n✅ Handled {successful}/{len(test_inquiries)} inquiries")
    
    # Get final status
    final_status = await desk.get_desk_status()
    print(f"\n📊 Final Service Desk Metrics:")
    print(f"   Total handled: {final_status['total_handled']}")
    print(f"   Escalation rate: {final_status['escalation_rate']*100:.1f}%")
    print(f"   Average resolution time: {final_status['avg_resolution_time']:.1f}s")
    print(f"   Current utilization: {final_status['mesh_status']['utilization']}")
    
    # Show agent breakdown
    print(f"\n👥 Agent Status by Tier:")
    for tier, agents in final_status['mesh_status']['nodes_by_role'].items():
        print(f"   {tier.upper()}:")
        for agent in agents:
            print(f"     • {agent['agent']}: {agent['load']} ({agent['load_percentage']})")
    
    # Example 5: Human escalation
    print("\n📞 Example 5: Human-in-the-Loop Escalation")
    print("-" * 50)
    
    print("Creating a complex complaint requiring human review...")
    
    try:
        response = await desk.handle(
            customer_id="cust_vip",
            inquiry="I demand a full refund and compensation for the terrible service. I've been a customer for 10 years and this is unacceptable! I want to speak to a manager immediately!",
            context={
                "customer_tier": "VIP",
                "account_value": "$50,000/year",
                "complaint_severity": "high"
            },
            priority=10,  # Maximum priority
            api_key="test-key-123"
        )
        
        print("✅ Complaint handled with care")
        if "supervisor" in response['response'].lower() or "escalated" in response['response'].lower():
            print("   → Escalated to human supervisor")
        
        # Check pending escalations
        pending = desk.escalation_manager.get_pending_escalations()
        if pending:
            print(f"\n🔔 Pending human escalations: {len(pending)}")
            for esc in pending[:3]:
                print(f"   • {esc.title}")
                print(f"     Priority: {esc.priority.value}")
                print(f"     Assigned to: {esc.assigned_to or 'Unassigned'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Show escalation statistics
    esc_stats = desk.escalation_manager.get_statistics()
    print(f"\n📈 Escalation Statistics:")
    print(f"   Total escalations: {esc_stats['total_escalations']}")
    print(f"   Active escalations: {esc_stats['active_escalations']}")
    print(f"   Approval rate: {esc_stats['approval_rate']*100:.1f}%")
    
    print("\n💡 Pro Tips:")
    print("-" * 50)
    print("1. Customize tiers to match your support structure")
    print("2. Add human reviewers for sensitive escalations")
    print("3. Use API keys to authenticate different clients")
    print("4. Monitor escalation rates to optimize agent training")
    print("5. Adjust agent capacity based on load patterns")
    print()
    
    print("🎯 Your multi-tier customer service desk is ready!")


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
