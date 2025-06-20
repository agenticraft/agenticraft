#!/usr/bin/env python3
"""Example: Resilient Research Team with Error Handling

This example demonstrates how to use the ResilientResearchTeam for production
deployments with automatic retry, caching, and error handling.
"""

import asyncio
import random
from agenticraft.workflows.resilient import ResilientResearchTeam


async def main():
    """Run resilient research example."""
    print("🛡️ Resilient Research Team Example")
    print("=" * 50)
    
    # Create a resilient research team
    team = ResilientResearchTeam(
        size=5,
        cache_results=True,
        max_retries=3,
        timeout_seconds=300  # 5 minutes
    )
    
    print("\n1️⃣ First Research (will be cached):")
    print("-" * 30)
    
    try:
        # First research - this will be cached
        report1 = await team.research(
            topic="Best practices for microservices architecture",
            depth="standard",  # Use standard instead of comprehensive for faster demo
            audience="technical"
        )
        
        print(f"✅ Research completed successfully!")
        print(f"📊 Executive Summary: {report1['executive_summary'][:200]}...")
        print(f"🔍 Key Findings: {len(report1['key_findings'])} insights")
        print(f"⏱️ Duration: {report1['metadata']['duration_seconds']:.1f}s")
        
    except Exception as e:
        print(f"❌ Research failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2️⃣ Same Research (should hit cache):")
    print("-" * 30)
    
    try:
        # Same research - should be instant from cache
        report2 = await team.research(
            topic="Best practices for microservices architecture",
            depth="standard",
            audience="technical"
        )
        
        print(f"✅ Research completed (from cache)!")
        print(f"⏱️ Duration: {report2['metadata']['duration_seconds']:.1f}s")
    except Exception as e:
        print(f"❌ Cached research failed: {e}")
    
    print("\n3️⃣ Health Check:")
    print("-" * 30)
    
    try:
        # Check team health
        health = await team.health_check()
        print(f"🏥 Team Status: {health['status']}")
        print(f"📈 Success Rate: {health['metrics'].get('success_rate', 'N/A')}")
        print(f"🔄 Total Retries: {health['metrics']['retries']}")
        print(f"⏱️ Timeouts: {health['metrics']['timeouts']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("\n4️⃣ Retry Strategy:")
    print("-" * 30)
    
    # Show retry configuration
    strategy = team.get_retry_strategy()
    for operation, config in strategy.items():
        print(f"\n{operation.title()}:")
        for key, value in config.items():
            print(f"  - {key}: {value}")
    
    print("\n5️⃣ Quick Research Test:")
    print("-" * 30)
    
    try:
        # Quick research to test basic functionality
        report = await team.research(
            topic="Python async programming basics",
            depth="quick",
            audience="general"
        )
        
        print(f"✅ Quick research completed!")
        print(f"📝 Topic: {report['topic']}")
        print(f"⏱️ Duration: {report['metadata']['duration_seconds']:.1f}s")
        
    except Exception as e:
        print(f"❌ Quick research failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n📊 Final Metrics:")
    print("-" * 30)
    
    try:
        final_status = await team.get_team_status()
        metrics = final_status["metrics"]
        
        print(f"Total Researches: {metrics['total_researches']}")
        print(f"Successful: {metrics['successful_researches']}")
        print(f"Failed: {metrics['failed_researches']}")
        print(f"Cache Hits: {metrics['cache_hits']}")
        print(f"Retries: {metrics['retries']}")
        
        # Calculate success rate
        if metrics['total_researches'] > 0:
            success_rate = metrics['successful_researches'] / metrics['total_researches']
            print(f"Success Rate: {success_rate:.1%}")
    except Exception as e:
        print(f"❌ Final status failed: {e}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
