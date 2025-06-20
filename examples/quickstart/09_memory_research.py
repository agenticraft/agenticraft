"""Example: Research Team with Memory

This example demonstrates how to use the memory-enhanced ResearchTeam
that remembers previous research and builds upon past insights.
"""

import asyncio
from agenticraft.workflows.memory_research_team import MemoryResearchTeam


async def memory_research_example():
    """Demonstrate research team with memory capabilities."""
    
    print("🧠 AgentiCraft Memory-Enhanced Research Team Demo\n")
    print("=" * 50)
    
    # Create research team with memory
    team = MemoryResearchTeam(
        size=5,
        memory_enabled=True,
        memory_config={
            "short_term_capacity": 200,
            "consolidation_threshold": 0.7
        }
    )
    
    # Initialize the team
    await team.initialize()
    
    try:
        # First research: Initial topic
        print("\n📚 First Research: AI Frameworks")
        print("-" * 30)
        
        report1 = await team.research(
            topic="Current state of AI frameworks and libraries",
            depth="standard",
            audience="technical",
            focus_areas=["Python frameworks", "Performance comparison"]
        )
        
        print(f"\n📋 Executive Summary:")
        print(report1["executive_summary"])
        
        print(f"\n🔍 Key Findings:")
        for i, finding in enumerate(report1["key_findings"], 1):
            print(f"{i}. {finding}")
        
        # Check memory stats
        memory_stats = await team.get_memory_stats()
        print(f"\n💾 Memory Stats after first research:")
        print(f"- Short-term memories: {memory_stats['short_term']['count']}")
        print(f"- Long-term memories: {memory_stats['long_term']['count']}")
        
        # Second research: Continue and refine
        print("\n\n📚 Second Research: Continuing with Open Source Focus")
        print("-" * 30)
        
        report2 = await team.research(
            topic="Continue our AI frameworks analysis focusing on open source options",
            depth="comprehensive",
            audience="technical",
            continue_previous=True
        )
        
        print(f"\n📋 Executive Summary:")
        print(report2["executive_summary"])
        
        print(f"\n🔍 New Insights (building on previous):")
        for i, finding in enumerate(report2["key_findings"], 1):
            print(f"{i}. {finding}")
        
        # Check if it continued from previous
        if report2["metadata"]["continued_from_previous"]:
            print("\n✅ Successfully continued from previous research!")
        
        # Third research: Different but related topic
        print("\n\n📚 Third Research: Related Topic")
        print("-" * 30)
        
        report3 = await team.research(
            topic="Best practices for deploying AI models in production",
            depth="standard",
            audience="executive"
        )
        
        print(f"\n📋 Executive Summary:")
        print(report3["executive_summary"])
        
        # Get research history
        print("\n\n📜 Research History:")
        print("-" * 30)
        
        history = await team.get_research_history(limit=5)
        for i, item in enumerate(history, 1):
            print(f"\n{i}. Topic: {item['topic']}")
            print(f"   Time: {item['timestamp']}")
            print(f"   Summary: {item['summary'][:100]}...")
        
        # Final memory stats
        final_stats = await team.get_memory_stats()
        print(f"\n\n💾 Final Memory Statistics:")
        print(f"- Short-term: {final_stats['short_term']['count']} memories")
        print(f"- Long-term: {final_stats['long_term']['count']} memories")
        print(f"- Task-specific: {final_stats['task']['total_memories']} memories")
        print(f"- Consolidation threshold: {final_stats['consolidation_threshold']}")
        
        # Demonstrate memory search
        print("\n\n🔍 Searching Memory for 'open source':")
        print("-" * 30)
        
        # Direct memory search (if exposed)
        if hasattr(team, '_memory'):
            search_results = await team._memory.retrieve(
                query="open source",
                limit=3
            )
            
            for i, result in enumerate(search_results, 1):
                print(f"\n{i}. Memory: {result.entry.key}")
                print(f"   Relevance: {result.relevance_score:.2f}")
                print(f"   Content: {str(result.entry.value)[:100]}...")
        
    finally:
        # Shutdown
        await team.shutdown()
        print("\n\n✅ Research team with memory shutdown complete!")


async def demonstrate_memory_consolidation():
    """Demonstrate how memory consolidation works."""
    
    print("\n\n🔄 Memory Consolidation Demo")
    print("=" * 50)
    
    team = MemoryResearchTeam(
        size=3,  # Smaller team for this demo
        memory_enabled=True,
        memory_config={
            "short_term_capacity": 10,  # Small capacity to trigger consolidation
            "consolidation_threshold": 0.6
        }
    )
    
    await team.initialize()
    
    try:
        # Do multiple quick researches
        topics = [
            "Python web frameworks",
            "JavaScript frameworks", 
            "Machine learning libraries",
            "Database technologies",
            "Cloud platforms"
        ]
        
        for topic in topics:
            print(f"\n🔍 Quick research on: {topic}")
            report = await team.research(
                topic=topic,
                depth="quick",
                audience="general"
            )
            print(f"✓ Completed: {report['executive_summary'][:100]}...")
            
            # Show memory growth
            stats = await team.get_memory_stats()
            print(f"  Short-term: {stats['short_term']['count']}, "
                  f"Long-term: {stats['long_term']['count']}")
        
        # Force consolidation
        print("\n\n🔄 Triggering memory consolidation...")
        if hasattr(team, '_memory'):
            consolidation_stats = await team._memory.consolidate(force=True)
            print(f"✓ Promoted {consolidation_stats['promoted']} memories to long-term")
            print(f"✓ Deleted {consolidation_stats['deleted']} low-importance memories")
        
        # Final stats
        final_stats = await team.get_memory_stats()
        print(f"\n📊 After consolidation:")
        print(f"  Short-term: {final_stats['short_term']['count']} memories")
        print(f"  Long-term: {final_stats['long_term']['count']} memories")
        
    finally:
        await team.shutdown()


if __name__ == "__main__":
    print("Choose demo:")
    print("1. Full memory research demo")
    print("2. Memory consolidation demo")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(demonstrate_memory_consolidation())
    else:
        asyncio.run(memory_research_example())
