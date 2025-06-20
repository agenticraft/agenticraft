"""
Example: Research Agent using Unified Protocol Fabric

This example demonstrates how to create a research agent that:
1. Connects to multiple MCP servers
2. Uses natural tool access syntax
3. Performs multi-step research with transparency
"""

import asyncio
import logging
from typing import List, Dict, Any

from agenticraft.fabric import agent, initialize_fabric, get_global_fabric

# Configure logging
logging.basicConfig(level=logging.INFO)

# Example 1: Simple Research Agent
@agent(
    "researcher",
    servers=["http://localhost:3000/mcp"],  # Connect to MCP server
    model="gpt-4",
    temperature=0.7
)
async def simple_researcher(self, topic: str) -> str:
    """
    Simple research agent that searches and summarizes.
    
    Uses natural tool access via self.tools.
    """
    print(f"🔍 Researching: {topic}")
    
    # Natural tool access - no setup needed!
    search_results = await self.tools.web_search(query=topic)
    print(f"📊 Found {len(search_results)} results")
    
    # Summarize the results
    summary = await self.tools.summarize(
        text=search_results,
        max_length=200
    )
    
    return summary


# Example 2: Advanced Multi-Protocol Agent
@agent(
    "advanced_researcher", 
    servers=[
        "http://localhost:3000/mcp",      # MCP server
        "ws://localhost:8080/a2a"         # A2A server
    ],
    reasoning="chain_of_thought",  # Enable reasoning traces
    model="gpt-4",
    temperature=0.3,
    sandbox=True  # Run in sandbox for safety
)
async def advanced_researcher(self, research_question: str) -> Dict[str, Any]:
    """
    Advanced research agent with reasoning and multiple protocols.
    
    This agent:
    - Uses chain of thought reasoning
    - Connects to multiple protocol servers
    - Provides transparent reasoning traces
    """
    results = {}
    
    # Step 1: Break down the research question
    print(f"🧠 Analyzing question: {research_question}")
    
    # The reasoning pattern is automatically applied
    subtopics = await self.tools.extract_subtopics(
        question=research_question
    )
    results['subtopics'] = subtopics
    
    # Step 2: Research each subtopic
    research_data = []
    for subtopic in subtopics:
        print(f"  📚 Researching subtopic: {subtopic}")
        
        # Use MCP tools
        web_data = await self.tools.web_search(query=subtopic)
        
        # Use A2A tools (if connected to A2A server)
        try:
            expert_analysis = await self.tools.expert_analyze(
                topic=subtopic,
                data=web_data
            )
            research_data.append({
                'subtopic': subtopic,
                'web_data': web_data,
                'expert_analysis': expert_analysis
            })
        except AttributeError:
            # A2A tool not available
            research_data.append({
                'subtopic': subtopic,
                'web_data': web_data
            })
    
    results['research_data'] = research_data
    
    # Step 3: Synthesize findings
    print("🔄 Synthesizing research findings...")
    synthesis = await self.tools.synthesize_research(
        data=research_data,
        original_question=research_question
    )
    results['synthesis'] = synthesis
    
    # Step 4: Generate final report
    report = await self.tools.create_report(
        title=f"Research Report: {research_question}",
        synthesis=synthesis,
        data=research_data
    )
    results['report'] = report
    
    return results


# Example 3: Using Manual Fabric Control
async def manual_fabric_example():
    """
    Example of using the fabric directly without decorators.
    
    This gives you more control over the protocol configuration.
    """
    print("\n=== Manual Fabric Example ===")
    
    # Initialize fabric with custom configuration
    fabric = await initialize_fabric({
        "mcp": {
            "servers": [
                {
                    "url": "http://localhost:3000",
                    "options": {
                        "timeout": 30,
                        "retry_count": 3
                    }
                }
            ]
        },
        "a2a": {
            "connection_type": "http",
            "url": "http://localhost:8080",
            "options": {
                "auth_token": "your-token-here"
            }
        }
    })
    
    # List available tools
    print("\n📋 Available tools:")
    tools = fabric.get_tools()
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Execute a tool directly
    if tools:
        tool_name = tools[0].name
        print(f"\n🔧 Executing tool: {tool_name}")
        result = await fabric.execute_tool(
            tool_name,
            query="What is AgentiCraft?"
        )
        print(f"Result: {result}")
    
    # Get protocol capabilities
    print("\n🎯 Protocol capabilities:")
    capabilities = fabric.get_capabilities()
    for protocol, caps in capabilities.items():
        print(f"\n{protocol.value}:")
        for cap in caps:
            print(f"  - {cap.name}: {cap.description}")
    
    # Create an agent with fabric tools
    unified_agent = await fabric.create_unified_agent(
        name="fabric_agent",
        model="gpt-4"
    )
    
    response = await unified_agent.arun(
        "What are the key features of AgentiCraft?"
    )
    print(f"\nAgent response: {response}")
    
    # Cleanup
    await fabric.shutdown()


# Example 4: Chaining Agents (Coming Soon)
"""
@agent("analyzer", servers=["http://localhost:3000/mcp"])
async def analyzer(self, data: str):
    return await self.tools.analyze(data)

@agent("writer", servers=["http://localhost:3001/mcp"]) 
async def writer(self, analysis: str):
    return await self.tools.write_article(analysis)

# Chain agents together
@chain(simple_researcher, analyzer, writer)
async def research_pipeline(topic: str):
    # Automatically flows through all agents
    return topic
"""


async def main():
    """Run all examples."""
    
    print("=" * 60)
    print("AgentiCraft Unified Protocol Fabric Examples")
    print("=" * 60)
    
    # Check if MCP servers are available
    print("\n⚠️  Note: These examples expect MCP servers running at:")
    print("  - http://localhost:3000 (MCP server)")
    print("  - ws://localhost:8080 (A2A server)")
    print("  You can use 'npx @modelcontextprotocol/server-memory' for testing")
    print()
    
    try:
        # Example 1: Simple researcher
        print("\n=== Example 1: Simple Research Agent ===")
        result = await simple_researcher("What is AgentiCraft?")
        print(f"\nResult: {result}")
        
    except Exception as e:
        print(f"❌ Example 1 failed: {e}")
        print("Make sure MCP server is running at http://localhost:3000")
    
    try:
        # Example 2: Advanced researcher  
        print("\n=== Example 2: Advanced Multi-Protocol Agent ===")
        result = await advanced_researcher(
            "How can AI agents improve software development?"
        )
        print(f"\nReport generated with {len(result.get('subtopics', []))} subtopics")
        
    except Exception as e:
        print(f"❌ Example 2 failed: {e}")
    
    try:
        # Example 3: Manual fabric control
        await manual_fabric_example()
        
    except Exception as e:
        print(f"❌ Example 3 failed: {e}")
    
    print("\n✅ Examples completed!")
    
    # Show fabric statistics
    fabric = get_global_fabric()
    if fabric._initialized:
        print(f"\n📊 Fabric Statistics:")
        print(f"  - Tools available: {len(fabric.unified_tools)}")
        print(f"  - Protocols active: {len(fabric.get_available_protocols())}")


if __name__ == "__main__":
    asyncio.run(main())
