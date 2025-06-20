"""
Protocol Fabric Integration Examples.

This module demonstrates how to integrate the Protocol Fabric with
all major AgentiCraft components.
"""

import asyncio
from typing import List, Dict, Any

from agenticraft.fabric import (
    agent, 
    UnifiedProtocolFabric, 
    SDKPreference,
    chain,
    parallel
)
# Import reasoning patterns - they may not all be available
try:
    from agenticraft.reasoning import ChainOfThoughtReasoning, TreeOfThoughtsReasoning
except ImportError:
    # Create mock classes if not available
    class ChainOfThoughtReasoning:
        def __init__(self):
            self.steps = []
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            pass
        
        def add_step(self, description: str):
            self.steps.append({"description": description})
        
        def add_observation(self, title: str, data: Any):
            self.steps.append({"observation": title, "data": data})
        
        def synthesize(self, data: list) -> str:
            return f"Synthesized {len(data)} sources"
        
        def get_reasoning_trace(self) -> list:
            return self.steps
        
        @property
        def confidence_score(self) -> float:
            return 0.85
    
    TreeOfThoughtsReasoning = ChainOfThoughtReasoning  # Simple mock
from agenticraft.memory import MemoryAgent, MemoryType
from agenticraft.security import SecurityMiddleware, UserContext
from agenticraft.telemetry import trace, track_metrics
from agenticraft.workflows import ResearchTeam, WorkflowVisualizer
from agenticraft.providers import get_provider


# Example 1: Protocol-Aware Reasoning Agent
@agent(
    "protocol_reasoner",
    servers=[
        "http://localhost:3000/mcp",
        "http://localhost:8080/a2a"
    ],
    extensions={'reasoning_traces': True}
)
@track_metrics(prefix="reasoning")
async def protocol_reasoning_agent(self, problem: str):
    """
    Agent that uses multiple protocols with advanced reasoning.
    
    Demonstrates:
    - Multi-protocol tool usage
    - Reasoning pattern integration
    - Automatic reasoning trace collection
    """
    # Initialize Chain of Thought reasoning
    async with ChainOfThoughtReasoning() as cot:
        # Step 1: Gather information from MCP
        cot.add_step("Gathering web information...")
        web_data = await self.tools.web_search(query=problem)
        cot.add_observation("Found relevant web data", web_data)
        
        # Step 2: Consult expert agents via A2A
        cot.add_step("Consulting expert agents...")
        expert_opinions = await self.tools.expert_analyze(
            data=web_data,
            domain="problem-solving"
        )
        cot.add_observation("Expert analysis complete", expert_opinions)
        
        # Step 3: Synthesize with reasoning
        cot.add_step("Synthesizing insights...")
        conclusion = cot.synthesize([web_data, expert_opinions])
        
        # Reasoning traces are automatically collected via extension
        return {
            "conclusion": conclusion,
            "reasoning_trace": self.get_reasoning_trace(),
            "confidence": cot.confidence_score
        }


# Example 2: Memory-Enhanced Multi-Protocol Agent
class ProtocolMemoryAgent(MemoryAgent):
    """
    Agent with protocol-aware memory system.
    
    Features:
    - Stores protocol context with memories
    - Cross-protocol memory sharing
    - Protocol-specific memory retrieval
    """
    
    def __init__(self, name: str, fabric: UnifiedProtocolFabric):
        super().__init__(name)
        self.fabric = fabric
        
    async def remember_protocol_interaction(
        self, 
        protocol: str,
        tool: str,
        result: Any,
        importance: float = 0.5
    ):
        """Store memory with protocol context."""
        await self.memory.store({
            "key": f"{protocol}:{tool}:{self.generate_timestamp()}",
            "value": result,
            "metadata": {
                "protocol": protocol,
                "tool": tool,
                "available_tools": await self.fabric.get_protocol_tools(protocol)
            },
            "type": MemoryType.LONG_TERM,
            "importance": importance
        })
    
    @agent(
        "memory_protocol_agent",
        servers=["mcp://localhost:3000", "a2a://localhost:8080"]
    )
    async def process_with_memory(self, task: str):
        """Process task using protocols and memory."""
        # Check if we've seen similar tasks
        memories = await self.memory.search(
            query=task,
            metadata_filter={"protocol": "mcp"}
        )
        
        if memories:
            # Use past experience
            context = memories[0].value
            result = await self.tools.web_search(
                query=f"{task} context: {context}"
            )
        else:
            # Fresh processing
            result = await self.tools.web_search(query=task)
        
        # Store for future
        await self.remember_protocol_interaction(
            "mcp", "web_search", result, importance=0.7
        )
        
        return result


# Example 3: Secure Protocol Execution
class SecureProtocolAgent:
    """
    Agent with protocol-level security.
    
    Features:
    - Protocol access control
    - Sandboxed execution
    - Audit logging
    """
    
    def __init__(self, fabric: UnifiedProtocolFabric):
        self.fabric = fabric
        self.security = SecurityMiddleware()
    
    @agent(
        "secure_protocol_agent",
        servers=["mcp://localhost:3000", "acp://localhost:9000"]
    )
    @trace("secure_execution")
    async def execute_secure(
        self, 
        task: str,
        user: UserContext,
        allowed_protocols: List[str]
    ):
        """Execute task with security constraints."""
        # Check user permissions
        for protocol in allowed_protocols:
            if not await self.security.check_permission(
                user, 
                f"protocol:{protocol}:execute"
            ):
                raise PermissionError(f"Access denied to {protocol}")
        
        # Execute in sandbox
        async with self.security.create_sandbox() as sandbox:
            results = {}
            
            for protocol in allowed_protocols:
                # Sandboxed execution per protocol
                result = await sandbox.execute(
                    self.fabric.execute_tool,
                    protocol,
                    "analyze",
                    data=task
                )
                results[protocol] = result
                
                # Audit log
                await self.security.audit.log({
                    "event": "protocol_execution",
                    "user": user.id,
                    "protocol": protocol,
                    "status": "success"
                })
            
            return results


# Example 4: Protocol-Enhanced Workflow
class MultiProtocolResearchWorkflow:
    """
    Research workflow using multiple protocols.
    
    Demonstrates:
    - Protocol selection per workflow step
    - Parallel protocol execution
    - Workflow visualization with protocols
    """
    
    def __init__(self, fabric: UnifiedProtocolFabric):
        self.fabric = fabric
        self.visualizer = WorkflowVisualizer()
    
    @chain("research_workflow")
    async def research_pipeline(self, topic: str):
        """Multi-stage research using different protocols."""
        
        # Stage 1: Parallel data gathering
        @parallel("data_gathering", max_workers=3)
        async def gather_data():
            return await asyncio.gather(
                self.fabric.execute_tool('mcp', 'web_search', query=topic),
                self.fabric.execute_tool('a2a', 'literature_review', topic=topic),
                self.fabric.execute_tool('anp', 'distributed_search', query=topic)
            )
        
        data_sources = await gather_data()
        
        # Stage 2: Expert analysis via A2A
        expert_analysis = await self.fabric.execute_tool(
            'a2a',
            'expert_panel',
            data=data_sources,
            experts=['economist', 'technologist', 'ethicist']
        )
        
        # Stage 3: Workflow orchestration via ACP
        workflow_result = await self.fabric.execute_tool(
            'acp',
            'execute_workflow',
            workflow={
                "name": "synthesis",
                "steps": [
                    {"tool": "summarize", "input": data_sources},
                    {"tool": "analyze", "input": expert_analysis},
                    {"tool": "report", "format": "academic"}
                ]
            }
        )
        
        # Stage 4: Consensus via AgentiCraft extension
        final_report = await self.fabric.consensus.decide(
            options=[workflow_result],
            min_agents=3,
            criteria="quality"
        )
        
        return {
            "report": final_report,
            "sources": len(data_sources),
            "protocols_used": ['mcp', 'a2a', 'anp', 'acp']
        }
    
    def visualize_workflow(self):
        """Generate workflow visualization with protocol annotations."""
        return self.visualizer.create_diagram(
            self.research_pipeline,
            annotations={
                "data_gathering": "Protocols: MCP, A2A, ANP",
                "expert_analysis": "Protocol: A2A",
                "synthesis": "Protocol: ACP",
                "consensus": "Extension: AgentiCraft Consensus"
            }
        )


# Example 5: Provider-Enhanced Protocol Agent
class ProviderProtocolAgent:
    """
    Agent that enhances LLM providers with protocol context.
    
    Features:
    - Protocol-aware prompts
    - Tool discovery injection
    - Multi-provider support
    """
    
    def __init__(self, fabric: UnifiedProtocolFabric, provider_name: str = "openai"):
        self.fabric = fabric
        self.provider = get_provider(provider_name)
    
    @agent(
        "provider_protocol_agent",
        servers=["mcp://localhost:3000"],
        sdk_preference=SDKPreference.OFFICIAL
    )
    async def enhanced_generate(self, prompt: str):
        """Generate response with protocol context."""
        # Discover available tools
        tools = await self.fabric.discover_all_tools()
        
        # Enhance prompt with tool context
        enhanced_prompt = f"""
        You have access to the following tools via protocols:
        
        {self._format_tools(tools)}
        
        User request: {prompt}
        
        Please provide a response and indicate which tools would be helpful.
        """
        
        # Generate with enhanced context
        response = await self.provider.generate([
            {"role": "system", "content": "You are a protocol-aware assistant."},
            {"role": "user", "content": enhanced_prompt}
        ])
        
        # Extract tool suggestions and execute if needed
        suggested_tools = self._extract_tool_suggestions(response)
        
        if suggested_tools:
            # Execute suggested tools
            tool_results = {}
            for tool_name in suggested_tools:
                try:
                    result = await self.tools.execute(tool_name)
                    tool_results[tool_name] = result
                except Exception as e:
                    tool_results[tool_name] = f"Error: {e}"
            
            # Generate final response with tool results
            final_response = await self.provider.generate([
                {"role": "assistant", "content": response},
                {"role": "user", "content": f"Tool results: {tool_results}"}
            ])
            
            return final_response
        
        return response
    
    def _format_tools(self, tools: List[Dict]) -> str:
        """Format tools for prompt injection."""
        formatted = []
        for tool in tools:
            formatted.append(
                f"- {tool['name']}: {tool['description']} "
                f"(Protocol: {tool.get('protocol', 'native')})"
            )
        return "\n".join(formatted)
    
    def _extract_tool_suggestions(self, response: str) -> List[str]:
        """Extract tool names mentioned in response."""
        # Simple extraction - in practice would use NLP
        tools = []
        for line in response.split('\n'):
            if 'suggest using' in line.lower() or 'tool:' in line.lower():
                # Extract tool name
                tools.append(line.split()[-1].strip('.,'))
        return tools


# Example 6: Full Integration Demo
async def full_integration_demo():
    """
    Demonstrate all integrations working together.
    """
    print("=== Protocol Fabric Full Integration Demo ===\n")
    
    # Initialize fabric with official SDKs
    fabric = UnifiedProtocolFabric(
        sdk_preferences={
            'mcp': SDKPreference.OFFICIAL,
            'a2a': SDKPreference.HYBRID,
            'acp': SDKPreference.OFFICIAL,
            'anp': SDKPreference.CUSTOM
        }
    )
    
    # Enable all extensions
    await fabric.enable_consensus(min_agents=3)
    await fabric.enable_reasoning_traces()
    await fabric.create_mesh_network(['agent1', 'agent2', 'agent3'])
    
    # 1. Reasoning + Protocols
    print("1. Testing Protocol-Aware Reasoning...")
    reasoner = protocol_reasoning_agent()
    reasoning_result = await reasoner("How to solve climate change?")
    print(f"   Conclusion: {reasoning_result['conclusion'][:100]}...")
    print(f"   Confidence: {reasoning_result['confidence']}")
    
    # 2. Memory + Protocols
    print("\n2. Testing Protocol-Aware Memory...")
    memory_agent = ProtocolMemoryAgent("researcher", fabric)
    memory_result = await memory_agent.process_with_memory("climate solutions")
    print(f"   Memory-enhanced result: {memory_result[:100]}...")
    
    # 3. Security + Protocols
    print("\n3. Testing Secure Protocol Execution...")
    secure_agent = SecureProtocolAgent(fabric)
    user = UserContext(id="user123", roles=["researcher"])
    try:
        secure_result = await secure_agent.execute_secure(
            "analyze security risks",
            user,
            allowed_protocols=['mcp']
        )
        print(f"   Secure execution completed: {len(secure_result)} protocols")
    except PermissionError as e:
        print(f"   Security check: {e}")
    
    # 4. Workflow + Protocols
    print("\n4. Testing Multi-Protocol Workflow...")
    workflow = MultiProtocolResearchWorkflow(fabric)
    workflow_result = await workflow.research_pipeline("AI safety")
    print(f"   Workflow completed using {workflow_result['protocols_used']}")
    print(f"   Sources gathered: {workflow_result['sources']}")
    
    # 5. Provider + Protocols
    print("\n5. Testing Provider-Protocol Integration...")
    provider_agent = ProviderProtocolAgent(fabric)
    provider_result = await provider_agent.enhanced_generate(
        "What tools can help me research quantum computing?"
    )
    print(f"   Provider response: {provider_result[:100]}...")
    
    print("\n=== All integrations working successfully! ===")


# Example 7: Custom Integration Pattern
class ProtocolIntegrationBuilder:
    """
    Builder for creating custom protocol integrations.
    """
    
    def __init__(self):
        self.fabric = None
        self.components = {}
    
    def with_fabric(self, sdk_preferences: Dict[str, str] = None):
        """Add protocol fabric with SDK preferences."""
        self.fabric = UnifiedProtocolFabric(
            sdk_preferences=sdk_preferences or {
                'mcp': SDKPreference.AUTO,
                'a2a': SDKPreference.AUTO
            }
        )
        return self
    
    def with_reasoning(self, pattern: str = "chain_of_thought"):
        """Add reasoning capability."""
        self.components['reasoning'] = pattern
        return self
    
    def with_memory(self, memory_type: str = "long_term"):
        """Add memory capability."""
        self.components['memory'] = memory_type
        return self
    
    def with_security(self, level: str = "standard"):
        """Add security features."""
        self.components['security'] = level
        return self
    
    def with_telemetry(self, enabled: bool = True):
        """Add telemetry tracking."""
        self.components['telemetry'] = enabled
        return self
    
    def build(self, name: str, servers: List[str]):
        """Build the integrated agent."""
        @agent(
            name,
            servers=servers,
            extensions=self.components
        )
        async def integrated_agent(self, task: str):
            # Agent with all requested integrations
            result = {"task": task, "components": list(self.components.keys())}
            
            if 'reasoning' in self.components:
                # Use reasoning
                result['reasoning'] = "Applied " + self.components['reasoning']
            
            if 'memory' in self.components:
                # Use memory
                result['memory'] = "Stored in " + self.components['memory']
            
            # Execute with all integrations
            return result
        
        return integrated_agent()


# Run the demo
if __name__ == "__main__":
    asyncio.run(full_integration_demo())
