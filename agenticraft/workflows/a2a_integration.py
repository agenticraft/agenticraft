"""Integration of A2A protocols with AgentiCraft workflows."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from agenticraft.workflows.base import Workflow
from agenticraft.core.agent import Agent
from ..protocols.a2a import ProtocolRegistry
from ..protocols.a2a.hybrid import MeshNetwork, AdaptiveModeSelector

logger = logging.getLogger(__name__)


class A2AWorkflow(Workflow):
    """Enhanced workflow with A2A protocol support.
    
    This class extends the base Workflow to add sophisticated
    agent coordination using A2A protocols.
    """
    
    def __init__(
        self,
        name: str,
        coordination_mode: str = "hybrid",
        protocol_name: Optional[str] = None,
        **kwargs
    ):
        """Initialize A2A-enabled workflow.
        
        Args:
            name: Workflow name
            coordination_mode: Coordination mode (centralized/decentralized/hybrid)
            protocol_name: Specific protocol to use (optional)
            **kwargs: Additional workflow arguments
        """
        super().__init__(name, **kwargs)
        
        self.coordination_mode = coordination_mode
        self.protocol_name = protocol_name
        self._protocol = None
        self._mode_selector = AdaptiveModeSelector()
        
        # Get protocol registry
        self._registry = ProtocolRegistry()
    
    async def initialize(self):
        """Initialize the workflow with A2A protocol."""
        await super().initialize()
        
        # Select protocol if not specified
        if not self.protocol_name:
            self.protocol_name = self._registry.select_protocol(
                coordination_type=self.coordination_mode
            )
        
        # Create protocol instance
        self._protocol = self._registry.create_instance(
            self.protocol_name,
            node_id=f"{self.name}-coordinator"
        )
        
        # Start protocol
        await self._protocol.start()
        
        # Register agents with protocol
        for agent in self.agents.values():
            if hasattr(self._protocol, 'register_agent'):
                await self._protocol.register_agent(agent)
            else:
                # Register capabilities manually
                capabilities = []
                if hasattr(agent, 'capabilities'):
                    capabilities = agent.capabilities
                elif hasattr(agent, 'tools'):
                    capabilities = list(agent.tools.keys())
                
                for cap in capabilities:
                    self._protocol.register_capability(cap)
        
        logger.info(f"Initialized {self.name} with {self.protocol_name} protocol")
    
    async def execute_with_coordination(
        self,
        task: str,
        required_capabilities: List[str],
        strategy: str = "auto",
        **kwargs
    ) -> Any:
        """Execute task with A2A coordination.
        
        Args:
            task: Task to execute
            required_capabilities: List of required capabilities
            strategy: Coordination strategy (auto/round_robin/consensus/etc)
            **kwargs: Additional execution parameters
            
        Returns:
            Task result
        """
        if not self._protocol:
            await self.initialize()
        
        # Auto-select strategy if needed
        if strategy == "auto":
            strategy = await self._select_strategy(task, required_capabilities)
        
        # Execute based on protocol type
        if self.protocol_name == "mesh_network":
            return await self._execute_mesh(task, required_capabilities, strategy, **kwargs)
        elif self.protocol_name == "task_router":
            return await self._execute_centralized(task, required_capabilities, strategy, **kwargs)
        elif self.protocol_name == "consensus":
            return await self._execute_consensus(task, required_capabilities, **kwargs)
        else:
            # Fallback to base execution
            return await self.execute(task, **kwargs)
    
    async def _select_strategy(self, task: str, capabilities: List[str]) -> str:
        """Select coordination strategy based on context."""
        # Estimate task complexity
        task_complexity = len(task.split()) / 100.0  # Simple heuristic
        agent_count = len(self.agents)
        
        # Use mode selector
        mode = await self._mode_selector.select_mode(
            task_complexity=min(task_complexity, 1.0),
            agent_count=agent_count,
            latency_requirement=1000.0,  # 1 second
            reliability_requirement=0.95
        )
        
        # Map mode to strategy
        if mode == "centralized":
            return "task_router"
        elif mode == "decentralized":
            return "consensus"
        else:
            return "round_robin"
    
    async def _execute_mesh(
        self,
        task: str,
        capabilities: List[str],
        strategy: str,
        **kwargs
    ) -> Any:
        """Execute using mesh network."""
        results = []
        
        for capability in capabilities:
            try:
                result = await self._protocol.execute_distributed(
                    task=task,
                    capability_required=capability,
                    strategy=strategy,
                    timeout=kwargs.get("timeout", 30.0)
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Mesh execution failed for {capability}: {e}")
                results.append({"error": str(e)})
        
        return self._aggregate_results(results)
    
    async def _execute_centralized(
        self,
        task: str,
        capabilities: List[str],
        strategy: str,
        **kwargs
    ) -> Any:
        """Execute using centralized router."""
        # Task router handles single capability at a time
        # For multiple capabilities, create sub-tasks
        results = []
        
        for i, capability in enumerate(capabilities):
            sub_task = f"{task} (part {i+1}: {capability})"
            
            try:
                result = await self._protocol.route_task(
                    task_name=sub_task,
                    capability=capability,
                    priority=kwargs.get("priority", 0),
                    timeout=kwargs.get("timeout", 30.0)
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Centralized execution failed for {capability}: {e}")
                results.append({"error": str(e)})
        
        return self._aggregate_results(results)
    
    async def _execute_consensus(
        self,
        task: str,
        capabilities: List[str],
        **kwargs
    ) -> Any:
        """Execute using consensus protocol."""
        # Propose task execution
        proposal_content = {
            "task": task,
            "capabilities": capabilities,
            "proposer": self.name,
            **kwargs
        }
        
        try:
            # Get consensus on task execution
            accepted = await self._protocol.propose(
                content=proposal_content,
                timeout=kwargs.get("timeout", 30.0)
            )
            
            if accepted:
                # Execute task after consensus
                return await self.execute(task, **kwargs)
            else:
                return {"error": "Consensus rejected task execution"}
                
        except Exception as e:
            logger.error(f"Consensus execution failed: {e}")
            return {"error": str(e)}
    
    def _aggregate_results(self, results: List[Any]) -> Any:
        """Aggregate results from multiple executions."""
        # Simple aggregation - can be customized
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Combine results
        combined = {
            "results": results,
            "success_count": sum(1 for r in results if not isinstance(r, dict) or "error" not in r),
            "total_count": len(results)
        }
        
        return combined
    
    async def get_coordination_status(self) -> Dict[str, Any]:
        """Get status of A2A coordination."""
        if not self._protocol:
            return {"status": "not_initialized"}
        
        status = {
            "protocol": self.protocol_name,
            "coordination_mode": self.coordination_mode,
            "network_status": self._protocol.get_network_status()
        }
        
        # Add protocol-specific status
        if hasattr(self._protocol, 'get_metrics'):
            status["metrics"] = self._protocol.get_metrics()
        elif hasattr(self._protocol, 'get_stats'):
            status["stats"] = self._protocol.get_stats()
        
        # Add mode selector stats
        status["mode_stats"] = self._mode_selector.get_mode_stats()
        
        return status
    
    async def cleanup(self):
        """Clean up workflow and protocol."""
        if self._protocol:
            await self._protocol.stop()
        
        await super().cleanup()


class A2AResearchTeam(A2AWorkflow):
    """Research team workflow with A2A coordination.
    
    Example of how to enhance existing workflows with A2A protocols.
    """
    
    def __init__(self, size: int = 5, **kwargs):
        """Initialize A2A research team."""
        super().__init__(
            name="a2a-research-team",
            coordination_mode=kwargs.get("coordination_mode", "hybrid"),
            **kwargs
        )
        
        # Create specialized agents
        self.agents = {
            "researcher": Agent(
                name="Researcher",
                instructions="You are a research specialist.",
                **kwargs
            ),
            "analyst": Agent(
                name="Analyst", 
                instructions="You analyze data and findings.",
                **kwargs
            ),
            "writer": Agent(
                name="Writer",
                instructions="You write comprehensive reports.",
                **kwargs
            ),
            "reviewer": Agent(
                name="Reviewer",
                instructions="You review and validate findings.",
                **kwargs
            ),
            "coordinator": Agent(
                name="Coordinator",
                instructions="You coordinate team efforts.",
                **kwargs
            )
        }
        
        # Set capabilities
        self.agents["researcher"].capabilities = ["research", "web_search"]
        self.agents["analyst"].capabilities = ["analysis", "data_processing"]
        self.agents["writer"].capabilities = ["writing", "documentation"]
        self.agents["reviewer"].capabilities = ["review", "validation"]
        self.agents["coordinator"].capabilities = ["coordination", "planning"]
    
    async def research(self, topic: str, **kwargs) -> Dict[str, Any]:
        """Conduct research with A2A coordination."""
        # Phase 1: Planning (consensus)
        planning_result = await self.execute_with_coordination(
            task=f"Create research plan for: {topic}",
            required_capabilities=["coordination", "planning"],
            strategy="consensus",
            **kwargs
        )
        
        # Phase 2: Research (distributed)
        research_result = await self.execute_with_coordination(
            task=f"Research topic: {topic}",
            required_capabilities=["research", "web_search"],
            strategy="round_robin",
            **kwargs
        )
        
        # Phase 3: Analysis (centralized)
        analysis_result = await self.execute_with_coordination(
            task=f"Analyze findings: {research_result}",
            required_capabilities=["analysis", "data_processing"],
            strategy="task_router",
            **kwargs
        )
        
        # Phase 4: Writing (collaborative)
        report = await self.execute_with_coordination(
            task=f"Write report on: {topic} with analysis: {analysis_result}",
            required_capabilities=["writing", "documentation"],
            strategy="round_robin",
            **kwargs
        )
        
        # Phase 5: Review (consensus)
        review_result = await self.execute_with_coordination(
            task=f"Review and validate report: {report}",
            required_capabilities=["review", "validation"],
            strategy="consensus",
            **kwargs
        )
        
        return {
            "topic": topic,
            "plan": planning_result,
            "research": research_result,
            "analysis": analysis_result,
            "report": report,
            "review": review_result,
            "coordination_status": await self.get_coordination_status()
        }
