"""
Protocol Fabric Integration Examples - Simplified Version.

This version handles cases where certain modules might not be available.
"""

import asyncio
from typing import List, Dict, Any, Optional

# Core imports that should always work
from agenticraft.fabric import (
    agent, 
    UnifiedProtocolFabric, 
    SDKPreference,
)

# Try to import optional components
try:
    from agenticraft.memory import MemoryAgent, MemoryType
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("Note: Memory module not available")

try:
    from agenticraft.telemetry import trace, track_metrics
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    # Create no-op decorators
    def trace(name): return lambda f: f
    def track_metrics(**kwargs): return lambda f: f

# Import reasoning with fallback
try:
    from agenticraft.reasoning.patterns import ChainOfThoughtReasoning
    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False
    print("Note: Reasoning patterns not available, using mock")
    
    # Simple mock for demonstration
    class ChainOfThoughtReasoning:
        def __init__(self):
            self.steps = []
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            pass
        
        def add_step(self, description: str):
            self.steps.append({"step": description})
        
        def add_observation(self, title: str, data: Any):
            self.steps.append({"observation": title, "data": str(data)[:100]})
        
        def synthesize(self, data: list) -> str:
            return f"Synthesized conclusion from {len(data)} sources"
        
        @property
        def confidence_score(self) -> float:
            return 0.85


# Example 1: Basic Multi-Protocol Agent
@agent(
    "basic_protocol_agent",
    servers=[
        "http://localhost:3000/mcp",
        "http://localhost:8080/a2a"
    ]
)
async def basic_protocol_agent(self, task: str):
    """
    Basic agent using multiple protocols.
    
    This works even without optional modules.
    """
    # Use MCP for web search
    mcp_result = await self.tools.web_search(query=task)
    
    # Use A2A for analysis
    a2a_result = await self.tools.expert_analyze(data=mcp_result)
    
    return {
        "task": task,
        "mcp_data": mcp_result,
        "a2a_analysis": a2a_result
    }


# Example 2: Protocol Agent with Optional Features
@agent(
    "enhanced_protocol_agent",
    servers=[
        "http://localhost:3000/mcp",
        "http://localhost:8080/a2a"
    ],
    extensions={'reasoning_traces': True}
)
@track_metrics(prefix="enhanced")
async def enhanced_protocol_agent(self, problem: str):
    """
    Enhanced agent that gracefully handles optional features.
    """
    result = {"problem": problem, "features_used": []}
    
    # Use reasoning if available
    if REASONING_AVAILABLE or True:  # Always true because we have mock
        async with ChainOfThoughtReasoning() as cot:
            cot.add_step("Gathering information...")
            web_data = await self.tools.web_search(query=problem)
            cot.add_observation("Web data collected", web_data)
            
            cot.add_step("Analyzing with experts...")
            analysis = await self.tools.expert_analyze(data=web_data)
            cot.add_observation("Expert analysis complete", analysis)
            
            conclusion = cot.synthesize([web_data, analysis])
            result["conclusion"] = conclusion
            result["confidence"] = cot.confidence_score
            result["features_used"].append("reasoning")
    else:
        # Fallback without reasoning
        web_data = await self.tools.web_search(query=problem)
        analysis = await self.tools.expert_analyze(data=web_data)
        result["conclusion"] = f"Analysis of {problem}"
        result["confidence"] = 0.7
    
    return result


# Example 3: SDK-Aware Agent
@agent(
    "sdk_aware_agent",
    servers=["http://localhost:3000/mcp"],
    sdk_preference=SDKPreference.AUTO
)
async def sdk_aware_agent(self, query: str):
    """
    Agent that works with any SDK preference.
    """
    # This works the same whether using official SDK or custom
    results = await self.tools.web_search(query=query)
    
    # Check which implementation is being used
    fabric_info = self.fabric.get_sdk_info() if hasattr(self.fabric, 'get_sdk_info') else {}
    
    return {
        "query": query,
        "results": results,
        "sdk_info": fabric_info.get('preferences', {})
    }


# Example 4: Multi-Protocol Workflow
async def multi_protocol_workflow():
    """
    Example workflow using multiple protocols.
    """
    print("\n=== Multi-Protocol Workflow Example ===")
    
    # Initialize fabric with mixed SDK preferences
    fabric = UnifiedProtocolFabric(
        sdk_preferences={
            'mcp': SDKPreference.OFFICIAL,
            'a2a': SDKPreference.HYBRID,
            'acp': SDKPreference.CUSTOM,
            'anp': SDKPreference.CUSTOM
        }
    )
    
    # Register servers
    servers = [
        ('mcp', 'http://localhost:3000'),
        ('a2a', 'http://localhost:8080'),
    ]
    
    for protocol, url in servers:
        try:
            await fabric.register_server(protocol, url)
            print(f"✓ Registered {protocol} server")
        except Exception as e:
            print(f"✗ Failed to register {protocol}: {e}")
    
    # Discover tools across all protocols
    try:
        all_tools = await fabric.discover_all_tools()
        print(f"\n✓ Discovered {len(all_tools)} tools across protocols")
        
        # Group by protocol
        by_protocol = {}
        for tool in all_tools:
            protocol = tool.get('protocol', 'unknown')
            if protocol not in by_protocol:
                by_protocol[protocol] = []
            by_protocol[protocol].append(tool['name'])
        
        for protocol, tools in by_protocol.items():
            print(f"  {protocol}: {', '.join(tools[:3])}{'...' if len(tools) > 3 else ''}")
    except Exception as e:
        print(f"✗ Failed to discover tools: {e}")
    
    print("\n✓ Multi-protocol workflow ready!")


# Example 5: Graceful Feature Detection
class ProtocolAgentBuilder:
    """
    Builder that detects available features.
    """
    
    def __init__(self):
        self.features = {
            'memory': MEMORY_AVAILABLE,
            'telemetry': TELEMETRY_AVAILABLE,
            'reasoning': REASONING_AVAILABLE,
        }
        self.fabric = None
    
    def with_fabric(self, preferences: Dict[str, str] = None):
        """Configure protocol fabric."""
        self.fabric = UnifiedProtocolFabric(
            sdk_preferences=preferences or {'mcp': SDKPreference.AUTO}
        )
        return self
    
    def build_agent(self, name: str, servers: List[str]):
        """Build agent with available features."""
        extensions = {}
        
        # Add available features
        if self.features['reasoning']:
            extensions['reasoning_traces'] = True
        
        # Create agent with detected features
        @agent(name, servers=servers, extensions=extensions)
        async def adaptive_agent(self, task: str):
            result = {
                "task": task,
                "available_features": [k for k, v in self.features.items() if v]
            }
            
            # Use available features
            if self.features['reasoning']:
                # Use reasoning
                result['reasoning'] = "Advanced reasoning applied"
            
            # Always use protocol tools
            result['protocol_result'] = await self.tools.search(task)
            
            return result
        
        return adaptive_agent()
    
    def get_status(self):
        """Get feature availability status."""
        return {
            "features": self.features,
            "all_features": all(self.features.values()),
            "some_features": any(self.features.values())
        }


# Example 6: Simple Integration Demo
async def simple_integration_demo():
    """
    Simple demo that works with minimal dependencies.
    """
    print("\n=== Simple Protocol Integration Demo ===")
    
    # Create fabric
    fabric = UnifiedProtocolFabric()
    print("✓ Created UnifiedProtocolFabric")
    
    # Create a basic agent
    agent_instance = basic_protocol_agent()
    print("✓ Created basic protocol agent")
    
    # Create enhanced agent
    enhanced = enhanced_protocol_agent()
    print("✓ Created enhanced protocol agent")
    
    # Create SDK-aware agent
    sdk_agent = sdk_aware_agent()
    print("✓ Created SDK-aware agent")
    
    # Check feature availability
    builder = ProtocolAgentBuilder()
    status = builder.get_status()
    print(f"\n✓ Feature Status:")
    for feature, available in status['features'].items():
        print(f"  {feature}: {'✓' if available else '✗'}")
    
    print("\n✓ All agents created successfully!")
    print("  Note: Actual execution requires protocol servers to be running")


# Main execution
async def main():
    """Run examples."""
    print("AgentiCraft Protocol Fabric Integration Examples")
    print("=" * 50)
    
    # Run simple demo
    await simple_integration_demo()
    
    # Run workflow example
    await multi_protocol_workflow()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: Some features may show as unavailable - this is normal")
    print("The protocol fabric works with whatever features are installed")


if __name__ == "__main__":
    asyncio.run(main())
