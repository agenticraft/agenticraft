"""
Examples of using Official SDKs with AgentiCraft Protocol Fabric.

This module demonstrates:
1. Using official SDKs
2. Hybrid mode with fallback
3. Gradual migration
4. Preserving AgentiCraft features
"""

import asyncio
from agenticraft.fabric import UnifiedProtocolFabric
from agenticraft.fabric.adapters import SDKPreference
from agenticraft.fabric.decorators import agent, chain, parallel


# Example 1: Using Official SDKs
async def example_official_sdks():
    """Example using official SDKs where available."""
    print("\n=== Example 1: Official SDKs ===")
    
    # Create fabric with official SDK preferences
    fabric = UnifiedProtocolFabric(
        sdk_preferences={
            'mcp': SDKPreference.OFFICIAL,    # Use official MCP SDK
            'a2a': SDKPreference.OFFICIAL,    # Use official A2A SDK
            'acp': SDKPreference.OFFICIAL,    # Use Bee framework
            'anp': SDKPreference.CUSTOM       # No official SDK yet
        }
    )
    
    # Register servers - adapters use official SDKs automatically
    await fabric.register_server('mcp', {
        'url': 'http://localhost:3000',
        'transport': 'sse'  # Official SDK options
    })
    
    await fabric.register_server('a2a', {
        'url': 'http://localhost:8080',
        'name': 'my-agent',
        'discovery_url': 'http://localhost:8080/discovery',
        'trusted_agents': ['agent1', 'agent2']  # A2A trust features
    })
    
    # Use tools - same interface regardless of SDK
    tools = await fabric.discover_tools()
    print(f"Discovered {len(tools)} tools using official SDKs")
    
    # Get SDK info
    info = fabric.get_sdk_info()
    print("\nSDK Status:")
    for protocol, pref in info['preferences'].items():
        print(f"  {protocol}: {pref}")


# Example 2: Hybrid Mode with Fallback
async def example_hybrid_mode():
    """Example using hybrid mode for best compatibility."""
    print("\n=== Example 2: Hybrid Mode ===")
    
    fabric = UnifiedProtocolFabric(
        sdk_preferences={
            'mcp': SDKPreference.HYBRID,  # Official with custom fallback
            'a2a': SDKPreference.HYBRID,
            'acp': SDKPreference.HYBRID,
            'anp': SDKPreference.CUSTOM
        }
    )
    
    # Define agent with hybrid SDK support
    @agent(
        "hybrid_agent",
        servers=[
            "http://localhost:3000/mcp",
            "http://localhost:8080/a2a"
        ]
    )
    async def hybrid_agent(self, task: str):
        """Agent that works with official or custom SDKs."""
        # This tool might only exist in custom implementation
        try:
            result = await self.tools.experimental_feature(task)
        except Exception:
            # Fallback handled automatically in hybrid mode
            result = await self.tools.standard_feature(task)
        
        return result
    
    # Test the agent
    agent_instance = hybrid_agent()
    print("Hybrid agent ready with automatic fallback support")


# Example 3: Gradual Migration Strategy
async def example_gradual_migration():
    """Example showing gradual migration to official SDKs."""
    print("\n=== Example 3: Gradual Migration ===")
    
    # Phase 1: Start with all custom implementations
    fabric = UnifiedProtocolFabric(
        sdk_preferences={
            'mcp': SDKPreference.CUSTOM,
            'a2a': SDKPreference.CUSTOM,
            'acp': SDKPreference.CUSTOM,
            'anp': SDKPreference.CUSTOM
        }
    )
    print("Phase 1: Using all custom implementations")
    
    # Phase 2: Test official MCP SDK
    print("\nPhase 2: Testing MCP official SDK...")
    results = await fabric.migrate_to_official_sdks(
        protocols=['mcp'],
        test_mode=True
    )
    
    if results['mcp']:
        print("✓ MCP SDK test passed, updating preference")
        fabric.update_sdk_preference('mcp', SDKPreference.OFFICIAL)
    else:
        print("✗ MCP SDK not available, staying with custom")
    
    # Phase 3: Enable hybrid mode for safety
    print("\nPhase 3: Enabling hybrid mode for A2A...")
    fabric.update_sdk_preference('a2a', SDKPreference.HYBRID)
    
    # Phase 4: Full migration where possible
    print("\nPhase 4: Attempting full migration...")
    all_results = await fabric.migrate_to_official_sdks(test_mode=False)
    
    print("\nMigration Results:")
    for protocol, success in all_results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {protocol}")


# Example 4: Preserving AgentiCraft Features with Official SDKs
async def example_preserve_features():
    """Example showing AgentiCraft features work with official SDKs."""
    print("\n=== Example 4: AgentiCraft Features + Official SDKs ===")
    
    # Use official SDKs
    fabric = UnifiedProtocolFabric(
        sdk_preferences={
            'mcp': SDKPreference.OFFICIAL,
            'a2a': SDKPreference.OFFICIAL
        }
    )
    
    # Register servers
    await fabric.register_server('mcp', 'http://localhost:3000')
    await fabric.register_server('a2a', 'http://localhost:8080')
    
    # Enable AgentiCraft's unique extensions
    print("\nEnabling AgentiCraft extensions...")
    
    # 1. Mesh networking (unique to AgentiCraft)
    mesh = await fabric.create_mesh_network(
        agents=['agent1', 'agent2', 'agent3'],
        topology='dynamic'
    )
    print(f"✓ Mesh network created: {mesh['mesh_id']}")
    
    # 2. Byzantine consensus (unique to AgentiCraft)
    consensus = await fabric.enable_consensus(
        consensus_type='byzantine',
        min_agents=3
    )
    print(f"✓ Consensus enabled: {consensus['consensus_id']}")
    
    # 3. Reasoning traces (unique to AgentiCraft)
    traces = await fabric.enable_reasoning_traces(level='detailed')
    print(f"✓ Reasoning traces enabled: {traces['trace_id']}")
    
    # Define agent using official SDKs + AgentiCraft features
    @agent(
        "advanced_agent",
        servers=[
            "http://localhost:3000/mcp",
            "http://localhost:8080/a2a"
        ],
        extensions={
            'mesh': True,
            'consensus': 'byzantine',
            'reasoning': 'detailed'
        }
    )
    async def advanced_agent(self, query: str):
        """Agent combining official SDKs with AgentiCraft features."""
        # Use official SDK tools
        mcp_result = await self.tools.search(query)  # MCP tool
        a2a_result = await self.tools.analyze(mcp_result)  # A2A tool
        
        # Use AgentiCraft consensus
        decision = await self.consensus.decide(
            options=a2a_result['options'],
            min_votes=3
        )
        
        return decision
    
    print("\n✓ Advanced agent ready with official SDKs + AgentiCraft features")


# Example 5: Configuration-Based SDK Selection
async def example_config_based():
    """Example using configuration file for SDK preferences."""
    print("\n=== Example 5: Configuration-Based SDK Selection ===")
    
    # Configuration (usually from YAML file)
    config = {
        'fabric': {
            'sdk_preferences': {
                'mcp': 'official',
                'a2a': 'hybrid',
                'acp': 'official',
                'anp': 'custom'
            },
            'fallback_enabled': True,
            'required_features': ['tools', 'discovery', 'streaming']
        },
        'servers': {
            'mcp': {
                'url': 'http://localhost:3000',
                'transport': 'sse'
            },
            'a2a': {
                'url': 'http://localhost:8080',
                'trust_verification': True
            }
        }
    }
    
    # Initialize fabric from config
    from agenticraft.fabric import initialize_fabric
    fabric = await initialize_fabric(config)
    
    # Register servers from config
    for protocol, server_config in config['servers'].items():
        await fabric.register_server(protocol, server_config)
    
    print("✓ Fabric initialized from configuration")
    print("\nActive SDK preferences:")
    info = fabric.get_sdk_info()
    for protocol, pref in info['preferences'].items():
        recommended = info['recommendations'].get(protocol, 'unknown')
        print(f"  {protocol}: {pref} (recommended: {recommended})")


# Example 6: Real-World Multi-Protocol Agent
async def example_real_world():
    """Real-world example: Research Assistant using multiple protocols."""
    print("\n=== Example 6: Real-World Research Assistant ===")
    
    # Smart SDK selection based on requirements
    fabric = UnifiedProtocolFabric(
        sdk_preferences={
            'mcp': SDKPreference.OFFICIAL,    # For stability
            'a2a': SDKPreference.HYBRID,      # For compatibility
            'acp': SDKPreference.OFFICIAL,    # For workflows
            'anp': SDKPreference.CUSTOM       # Not available yet
        }
    )
    
    # Register protocol servers
    servers = {
        'mcp': 'http://localhost:3000',      # Web tools, search
        'a2a': 'http://localhost:8080',      # Expert agents
        'acp': 'http://localhost:9000',      # Workflow orchestration
        'anp': 'did:anp:discovery'           # Decentralized agents
    }
    
    for protocol, url in servers.items():
        try:
            await fabric.register_server(protocol, url)
            print(f"✓ Connected to {protocol} server")
        except Exception as e:
            print(f"✗ Failed to connect to {protocol}: {e}")
    
    # Enable AgentiCraft features
    await fabric.enable_consensus(min_agents=3)
    await fabric.enable_reasoning_traces()
    
    @agent(
        "research_assistant",
        servers=list(servers.values()),
        extensions={
            'consensus': 'byzantine',
            'reasoning': 'detailed'
        }
    )
    async def research_assistant(self, topic: str):
        """Multi-protocol research assistant."""
        # Phase 1: Gather information (MCP)
        web_results = await self.tools.web_search(
            query=f"{topic} recent developments"
        )
        
        # Phase 2: Expert analysis (A2A)
        expert_analysis = await self.tools.expert_analyze(
            data=web_results,
            domain="scientific"
        )
        
        # Phase 3: Create workflow (ACP)
        workflow = {
            "name": "deep_research",
            "steps": [
                {"tool": "literature_review", "params": {"topic": topic}},
                {"tool": "data_synthesis", "params": {"sources": 10}},
                {"tool": "report_generation", "params": {"format": "academic"}}
            ]
        }
        
        workflow_result = await self.tools.execute_workflow(workflow)
        
        # Phase 4: Consensus decision (AgentiCraft)
        final_report = await self.consensus.decide(
            options=[web_results, expert_analysis, workflow_result],
            criteria="most_comprehensive"
        )
        
        return final_report
    
    print("\n✓ Research Assistant ready with:")
    print("  - Official MCP SDK for web tools")
    print("  - Hybrid A2A SDK for expert collaboration")
    print("  - Official ACP (Bee) for workflows")
    print("  - Custom ANP for decentralized discovery")
    print("  - AgentiCraft consensus and reasoning")


# Main execution
async def main():
    """Run all examples."""
    examples = [
        example_official_sdks,
        example_hybrid_mode,
        example_gradual_migration,
        example_preserve_features,
        example_config_based,
        example_real_world
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\nExample failed: {e}")
        
        # Small delay between examples
        await asyncio.sleep(1)
    
    print("\n" + "="*50)
    print("All examples completed!")
    print("\nKey Takeaways:")
    print("1. Official SDKs provide better compatibility and maintenance")
    print("2. Hybrid mode offers safety with automatic fallback")
    print("3. Migration can be gradual and non-breaking")
    print("4. AgentiCraft's unique features work with any SDK")
    print("5. The same agent code works regardless of SDK choice")


if __name__ == "__main__":
    asyncio.run(main())
