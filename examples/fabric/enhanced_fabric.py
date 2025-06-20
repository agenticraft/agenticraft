"""
Example: Enhanced Unified Protocol Fabric with All Protocols

This example demonstrates:
1. All 4 protocols (MCP, A2A, ACP, ANP) working together
2. AgentiCraft's unique extensions (mesh, consensus, reasoning)
3. Migration path to official SDKs
"""

import asyncio
import logging
from typing import Dict, Any, List

from agenticraft.fabric import (
    agent,
    EnhancedUnifiedProtocolFabric,
    ProtocolType,
    initialize_fabric
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Universal Agent with All Protocols
@agent(
    "universal_agent",
    servers=[
        "http://localhost:3000/mcp",      # MCP server
        "http://localhost:8080/a2a",      # A2A network
        "http://localhost:9000/acp",      # IBM ACP
        "did:anp:discovery"               # ANP discovery
    ],
    model="gpt-4",
    reasoning="chain_of_thought"
)
async def universal_agent(self, task: str) -> Dict[str, Any]:
    """
    Universal agent that can use all protocols.
    
    This agent demonstrates:
    - Tool usage from any protocol
    - Transparent protocol selection
    - Natural tool access syntax
    """
    results = {}
    
    print(f"🌐 Universal Agent processing: {task}")
    
    # Use MCP tools
    try:
        print("  📡 Using MCP protocol...")
        web_data = await self.tools.web_search(query=task)
        results['mcp_data'] = web_data
    except Exception as e:
        print(f"  ❌ MCP failed: {e}")
    
    # Use A2A agents
    try:
        print("  🤝 Using A2A protocol...")
        analysis = await self.tools.expert_analyze(data=task)
        results['a2a_analysis'] = analysis
    except Exception as e:
        print(f"  ❌ A2A failed: {e}")
    
    # Use ACP capabilities
    try:
        print("  🏢 Using IBM ACP protocol...")
        acp_result = await self.tools.process_task(task=task)
        results['acp_result'] = acp_result
    except Exception as e:
        print(f"  ❌ ACP failed: {e}")
    
    # Use ANP for discovery
    try:
        print("  🔍 Using ANP protocol...")
        discovered = await self.tools.discover_specialists(domain="AI")
        results['anp_discovered'] = discovered
    except Exception as e:
        print(f"  ❌ ANP failed: {e}")
    
    return results


# Example 2: Enhanced Fabric with Extensions
async def enhanced_fabric_example():
    """
    Demonstrate enhanced fabric with AgentiCraft extensions.
    """
    print("\n=== Enhanced Fabric with Extensions ===")
    
    # Initialize enhanced fabric
    fabric = EnhancedUnifiedProtocolFabric()
    
    config = {
        "mcp": {
            "servers": [{
                "url": "http://localhost:3000",
                "options": {"timeout": 30}
            }]
        },
        "a2a": {
            "connection_type": "http",
            "url": "http://localhost:8080"
        },
        "acp": {
            "url": "http://localhost:9000",
            "auth": {"token": "demo-token"}
        },
        "anp": {
            "ipfs_gateway": "https://ipfs.io",
            "did_method": "web",
            "create_did": True,
            "agent_name": "agenticraft-demo"
        }
    }
    
    await fabric.initialize(config)
    
    # Enable AgentiCraft extensions
    print("\n🔧 Enabling AgentiCraft Extensions:")
    
    # 1. Mesh Networking
    mesh = await fabric.create_mesh_network(
        agents=["agent1", "agent2", "agent3"],
        topology="dynamic"
    )
    print(f"  ✅ Mesh Network: {mesh['mesh_id']}")
    
    # 2. Consensus Mechanism
    consensus = await fabric.enable_consensus(
        consensus_type="byzantine",
        min_agents=3
    )
    print(f"  ✅ Consensus: {consensus['consensus_id']}")
    
    # 3. Reasoning Traces
    traces = await fabric.enable_reasoning_traces(
        level="detailed"
    )
    print(f"  ✅ Reasoning Traces: {traces['trace_id']}")
    
    # List all capabilities
    print("\n📋 Protocol Capabilities:")
    all_caps = fabric.get_capabilities()
    for protocol, caps in all_caps.items():
        print(f"\n{protocol.value}:")
        for cap in caps:
            print(f"  - {cap.name}: {cap.description}")
    
    # Show available tools
    print(f"\n🔧 Total Available Tools: {len(fabric.get_tools())}")
    for protocol in ProtocolType:
        if protocol == ProtocolType.NATIVE:
            continue
        tools = fabric.get_tools(protocol=protocol)
        if tools:
            print(f"  {protocol.value}: {len(tools)} tools")
    
    await fabric.shutdown()


# Example 3: Multi-Protocol Coordination
class MultiProtocolCoordinator:
    """
    Coordinate tasks across multiple protocols with consensus.
    """
    
    def __init__(self):
        self.fabric = None
        self.consensus_enabled = False
    
    async def initialize(self):
        """Initialize with all protocols and extensions."""
        self.fabric = await initialize_fabric({
            "mcp": {"servers": [{"url": "http://localhost:3000"}]},
            "a2a": {"connection_type": "http", "url": "http://localhost:8080"},
            "acp": {"url": "http://localhost:9000"},
            "anp": {"did_method": "web"}
        })
        
        # Enable consensus for critical decisions
        await self.fabric.enable_consensus(min_agents=3)
        self.consensus_enabled = True
    
    async def coordinate_research(self, topic: str) -> Dict[str, Any]:
        """
        Coordinate research across protocols with consensus.
        """
        print(f"\n🎯 Coordinating research on: {topic}")
        
        # Create agents for each protocol
        agents = []
        
        # MCP Agent
        mcp_agent = await self.fabric.create_unified_agent(
            name="mcp_researcher",
            model="gpt-4"
        )
        agents.append(("MCP", mcp_agent))
        
        # A2A Agent (would connect to real A2A network)
        a2a_agent = await self.fabric.create_unified_agent(
            name="a2a_analyst",
            model="gpt-4"
        )
        agents.append(("A2A", a2a_agent))
        
        # ACP Agent
        acp_agent = await self.fabric.create_unified_agent(
            name="acp_processor",
            model="gpt-4"
        )
        agents.append(("ACP", acp_agent))
        
        # Gather research from all agents
        research_tasks = []
        for protocol, agent in agents:
            task = self._research_with_agent(protocol, agent, topic)
            research_tasks.append(task)
        
        # Execute in parallel
        results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Consensus decision on best approach
        if self.consensus_enabled:
            print("\n🤝 Achieving consensus on findings...")
            # Simulated consensus
            consensus_result = {
                "agreed": True,
                "confidence": 0.92,
                "selected_approach": "hybrid"
            }
        else:
            consensus_result = {"agreed": False}
        
        return {
            "research_results": dict(zip([p for p, _ in agents], results)),
            "consensus": consensus_result,
            "recommendation": self._synthesize_findings(results)
        }
    
    async def _research_with_agent(self, protocol: str, agent: Any, topic: str) -> Dict:
        """Perform research using specific agent."""
        print(f"  🔍 {protocol} agent researching...")
        
        # Simulated research
        return {
            "protocol": protocol,
            "findings": f"{protocol} research on {topic}",
            "confidence": 0.85
        }
    
    def _synthesize_findings(self, results: List[Dict]) -> str:
        """Synthesize findings from all protocols."""
        valid_results = [r for r in results if not isinstance(r, Exception)]
        return f"Synthesized {len(valid_results)} protocol findings"


# Example 4: Migration Path Demo
async def migration_demo():
    """
    Demonstrate migration path from custom to official SDKs.
    """
    print("\n=== SDK Migration Path Demo ===")
    
    # Current state: Using custom protocol implementations
    print("\n📦 Current: Custom Protocol Implementations")
    fabric_custom = EnhancedUnifiedProtocolFabric()
    
    # Future state: Using official SDKs (when available)
    print("\n📦 Future: Official SDK Integration")
    print("  When official SDKs are available:")
    print("  - pip install mcp-sdk")
    print("  - pip install a2a-python") 
    print("  - pip install acp-client")
    print("  - pip install agentconnect")
    
    # The adapter pattern makes migration seamless
    print("\n✅ Migration Benefits:")
    print("  - No changes to agent code")
    print("  - Gradual protocol-by-protocol migration")
    print("  - Extensions remain unchanged")
    print("  - Full backward compatibility")
    
    # Example of future SDK adapter
    print("\n🔄 Future SDK Adapter Pattern:")
    print("""
    class MCPSDKAdapter(IProtocolAdapter):
        def __init__(self):
            # Use official SDK
            from mcp import Client as MCPClient
            self.client = MCPClient()
        
        # Same interface, different implementation
        async def connect(self, config):
            await self.client.connect(**config)
    """)


async def main():
    """Run all enhanced fabric examples."""
    
    print("=" * 60)
    print("Enhanced Unified Protocol Fabric Examples")
    print("=" * 60)
    
    print("\n⚠️  This example demonstrates all 4 protocols:")
    print("  - MCP: http://localhost:3000")
    print("  - A2A: http://localhost:8080")
    print("  - ACP: http://localhost:9000") 
    print("  - ANP: Decentralized (using DIDs)")
    
    # Example 1: Universal agent
    try:
        print("\n=== Example 1: Universal Agent ===")
        result = await universal_agent("Research quantum computing applications")
        print(f"\nProtocols used: {len(result)}")
        for protocol, data in result.items():
            print(f"  - {protocol}: {'✅ Success' if data else '❌ Failed'}")
    except Exception as e:
        print(f"❌ Universal agent failed: {e}")
    
    # Example 2: Enhanced fabric
    try:
        await enhanced_fabric_example()
    except Exception as e:
        print(f"❌ Enhanced fabric failed: {e}")
    
    # Example 3: Multi-protocol coordination
    try:
        print("\n=== Example 3: Multi-Protocol Coordination ===")
        coordinator = MultiProtocolCoordinator()
        await coordinator.initialize()
        
        result = await coordinator.coordinate_research("AI safety measures")
        print(f"\nCoordination complete:")
        print(f"  - Protocols engaged: {len(result['research_results'])}")
        print(f"  - Consensus achieved: {result['consensus']['agreed']}")
        print(f"  - Recommendation: {result['recommendation']}")
    except Exception as e:
        print(f"❌ Coordination failed: {e}")
    
    # Example 4: Migration demo
    await migration_demo()
    
    print("\n✅ Enhanced Fabric Examples Complete!")
    print("\n🚀 Next Steps:")
    print("  1. Implement remaining workflow decorators")
    print("  2. Add official SDK adapters when available")
    print("  3. Enhance extension system")
    print("  4. Add more real-world examples")


if __name__ == "__main__":
    asyncio.run(main())
