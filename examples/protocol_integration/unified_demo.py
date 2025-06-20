"""
Example: Unified Protocol Integration Demo

This example demonstrates:
1. Exposing AgentiCraft agents through A2A and MCP
2. Connecting to external services
3. Unified task execution across protocols
"""

import asyncio
import logging
from typing import Dict, Any

# Add AgentiCraft to path
import sys
sys.path.insert(0, '/Users/zahere/Desktop/TLV/agenticraft')

from agenticraft.core.agent import Agent
from agenticraft.tools.web import web_search, extract_text
from agenticraft.tools.calculator import calculator
from agenticraft.protocols import (
    ProtocolGateway,
    ExternalProtocol,
    A2AServer,
    MCPServerBuilder,
    create_unified_gateway
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_agent_exposure():
    """Demonstrate exposing agents through multiple protocols."""
    print("\n🚀 Demo 1: Multi-Protocol Agent Exposure")
    print("-" * 60)
    
    # Create sample agents with tools
    research_agent = Agent(
        name="ResearchAgent",
        model="gpt-4",
        tools=[web_search, extract_text],
        system_prompt="You are a research specialist with web search capabilities."
    )
    
    analysis_agent = Agent(
        name="AnalysisAgent", 
        model="gpt-4",
        tools=[calculator],
        system_prompt="You are a data analysis expert with calculation capabilities."
    )
    
    # Create protocol gateway
    gateway = ProtocolGateway()
    await gateway.start()
    
    # Expose agents through both A2A and MCP
    print("\n📡 Exposing agents through multiple protocols...")
    
    # Note: In a real scenario, these would start actual servers
    # For demo purposes, we'll show the registration process
    print("\n  Would expose ResearchAgent on:")
    print("    - A2A: http://localhost:8080")
    print("    - MCP: http://localhost:8081")
    
    print("\n  Would expose AnalysisAgent on:")
    print("    - A2A: http://localhost:8082")
    print("    - MCP: http://localhost:8083")
    
    # Show what capabilities would be exposed
    print("\n📋 Exposed Capabilities:")
    print(f"\n  ResearchAgent:")
    print(f"    - web_search: Search the web for information")
    print(f"    - extract_text: Extract text from URLs")
    
    print(f"\n  AnalysisAgent:")
    print(f"    - calculator: Perform calculations")
    
    # List all services (simulated)
    print("\n📊 Service Registry (simulated):")
    print("  - ResearchAgent (A2A): internal")
    print("  - ResearchAgent (MCP): internal")
    print("  - AnalysisAgent (A2A): internal")
    print("  - AnalysisAgent (MCP): internal")
    
    await gateway.stop()
    return gateway


async def demo_external_connections():
    """Demonstrate connecting to external A2A and MCP services."""
    print("\n🌐 Demo 2: External Service Connections")
    print("-" * 60)
    
    gateway = ProtocolGateway()
    await gateway.start()
    
    # Simulate connecting to external services
    print("\n🔗 Connecting to external services...")
    
    # Connect to external A2A agent (simulated)
    print("\n  Would connect to external A2A agent at:")
    print("    URL: https://example.com/a2a-agent")
    print("    ✅ Connection established (simulated)")
    print("    Capabilities discovered: ['data_processing', 'nlp_analysis']")
    
    # Connect to external MCP server (simulated)
    print("\n  Would connect to external MCP server:")
    print("    Type: filesystem-server")
    print("    Transport: stdio")
    print("    ✅ Connection established (simulated)")
    print("    Tools discovered: ['read_file', 'write_file', 'list_directory']")
    
    # Show metrics
    print("\n📈 Gateway Metrics:")
    metrics = gateway.get_metrics()
    print(f"  Total requests: {metrics['total_requests']}")
    print(f"  Active connections: {metrics['active_connections']}")
    print(f"  Total services: 2 (simulated)")
    
    await gateway.stop()
    return gateway


async def demo_unified_execution():
    """Demonstrate unified task execution across protocols."""
    print("\n⚡ Demo 3: Unified Task Execution")
    print("-" * 60)
    
    # Create agents
    agents = [
        Agent(
            name="Researcher",
            model="gpt-4",
            tools=[web_search],
            system_prompt="You are a research specialist."
        ),
        Agent(
            name="Calculator",
            model="gpt-4",
            tools=[calculator],
            system_prompt="You are a calculation expert."
        )
    ]
    
    # Create gateway
    gateway = ProtocolGateway()
    await gateway.start()
    
    print("\n✅ Unified gateway created with multiple agents")
    
    # Simulate task execution
    print("\n🎯 Executing tasks through unified interface...")
    
    tasks = [
        ("Search for information about Python", "tool:web_search"),
        ("Calculate 2 + 2", "tool:calculator"),
        ("Analyze data trends", None),  # Any capable agent
    ]
    
    for task_desc, capability in tasks:
        print(f"\n  Task: '{task_desc}'")
        print(f"  Required capability: {capability or 'Any'}")
        print(f"  ✅ Result: Task would be routed to appropriate agent")
    
    # Health check
    print("\n🏥 System Health Check:")
    health = await gateway.health_check()
    print(f"  Overall status: {health['status']}")
    print(f"  Services checked: {len(health['services'])}")
    
    await gateway.stop()
    return gateway


async def demo_mcp_server_building():
    """Demonstrate building MCP servers with the new builder."""
    print("\n🔧 Demo 4: MCP Server Builder")
    print("-" * 60)
    
    # Check if MCP SDK is available
    try:
        from mcp.server.fastmcp import FastMCP
        mcp_available = True
    except ImportError:
        mcp_available = False
    
    if not mcp_available:
        print("\n⚠️  MCP SDK not installed. Showing what would be created:")
        print("\nMCP Server: 'Custom AgentiCraft Server'")
        print("  Tools:")
        print("    - calculate: Perform calculations")
        print("    - get_system_info: Get system information")
        print("  Resources:")
        print("    - config://agenticraft: Get configuration")
        print("  Prompts:")
        print("    - code_review: Generate code review prompt")
        
        print("\n📝 Claude Desktop Configuration would be:")
        print("""
{
  "mcpServers": {
    "Custom AgentiCraft Server": {
      "command": "python",
      "args": ["-m", "custom_agenticraft_server"],
      "description": "Demonstrates MCP server building"
    }
  }
}
""")
        return None
    
    # If MCP is available, create actual server
    print("✅ MCP SDK available - creating server...")
    # Server creation code would go here
    
    return None


async def demo_a2a_mcp_interop():
    """Demonstrate interoperability between A2A and MCP."""
    print("\n🌉 Demo 5: A2A-MCP Interoperability")
    print("-" * 60)
    
    # Create an agent that can work with both protocols
    hybrid_agent = Agent(
        name="HybridAgent",
        model="gpt-4",
        tools=[web_search, calculator],
        system_prompt="You are a multi-protocol capable assistant."
    )
    
    gateway = ProtocolGateway()
    await gateway.start()
    
    print("\n🔄 Agent capabilities:")
    print(f"  Name: {hybrid_agent.name}")
    print(f"  Tools: web_search, calculator")
    print(f"  Can be exposed through: A2A and MCP")
    
    # Demonstrate cross-protocol execution
    print("\n🔀 Cross-protocol task execution (simulated):")
    
    task = "Search for information about protocol interoperability"
    
    print(f"\n  Task: '{task}'")
    print("\n  Would execute through A2A:")
    print("    - Route to A2A endpoint")
    print("    - Execute web_search tool")
    print("    - Return results via A2A protocol")
    
    print("\n  Same task through MCP:")
    print("    - Route to MCP server")
    print("    - Execute web_search tool")
    print("    - Return results via MCP protocol")
    
    print("\n  ✅ Both protocols can execute the same task!")
    
    # Show protocol statistics
    print("\n📊 Protocol Usage Statistics:")
    print("  A2A: 1 service")
    print("  MCP: 1 service")
    print("  Total: 2 services")
    
    await gateway.stop()
    return gateway


async def main():
    """Run all protocol integration demos."""
    print("🚀 AgentiCraft Protocol Integration Demonstrations")
    print("=" * 60)
    print("\nThese demos showcase the new A2A and MCP integration features:")
    print("- Multi-protocol agent exposure")
    print("- External service connections")
    print("- Unified task execution")
    print("- MCP server building")
    print("- A2A-MCP interoperability")
    print("=" * 60)
    
    # Run demos
    demos = [
        demo_agent_exposure,
        demo_external_connections,
        demo_unified_execution,
        demo_mcp_server_building,
        demo_a2a_mcp_interop
    ]
    
    gateways = []
    for demo in demos:
        try:
            result = await demo()
            if result and hasattr(result, 'stop'):
                gateways.append(result)
        except Exception as e:
            print(f"\n⚠️  Demo error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        await asyncio.sleep(1)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    for gateway in gateways:
        if hasattr(gateway, 'stop'):
            try:
                await gateway.stop()
            except:
                pass
    
    print("\n✅ All demonstrations completed!")
    print("\n📚 Key Takeaways:")
    print("- AgentiCraft agents can be exposed through both A2A and MCP protocols")
    print("- The Protocol Gateway provides unified management of all connections")
    print("- Tasks can be executed across protocols transparently")
    print("- MCP servers can be built easily with the MCPServerBuilder")
    print("- Full interoperability between internal and external protocols")
    
    print("\n💡 Note: This demo simulates protocol operations.")
    print("   To see actual protocol servers running:")
    print("   1. Install MCP SDK: pip install 'mcp[cli]'")
    print("   2. Set up actual agent servers")
    print("   3. Configure external connections")


if __name__ == "__main__":
    asyncio.run(main())
