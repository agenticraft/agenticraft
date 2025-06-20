"""Research Team workflow with memory support for AgentiCraft.

Enhanced version of the ResearchTeam that remembers previous research,
avoids duplicating work, and builds on past insights.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from agenticraft.agents.patterns import SimpleCoordinator
from agenticraft.agents.specialized import DataAnalyst, TechnicalWriter, WebResearcher
from agenticraft.core import Workflow, WorkflowConfig
from agenticraft.memory import MemoryType, ConsolidatedMemory
from agenticraft.memory.agent import MemoryAgent

import logging
logger = logging.getLogger(__name__)


class MemoryResearchTeam(Workflow):
    """Memory-enhanced multi-agent research team.
    
    This enhanced version adds:
    - Memory of previous research to avoid duplication
    - Learning from past research patterns
    - Context awareness across research sessions
    - Ability to continue/refine previous research
    
    Example:
        ```python
        from agenticraft.workflows import MemoryResearchTeam
        
        # Create team with memory
        team = MemoryResearchTeam(memory_enabled=True)
        
        # First research
        report1 = await team.research("AI frameworks market analysis")
        
        # Continue with context from previous research
        report2 = await team.research("Continue our AI analysis focusing on open source")
        ```
    """
    
    def __init__(
        self,
        size: int = 5,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        name: str = "MemoryResearchTeam",
        memory_enabled: bool = True,
        memory_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Initialize workflow
        config = WorkflowConfig(
            name=name,
            description="Memory-enhanced multi-agent research team",
            **kwargs
        )
        super().__init__(config)
        
        # Configuration
        self.team_size = max(3, min(size, 10))
        self.provider = provider
        self.model = model
        self.memory_enabled = memory_enabled
        
        # Initialize memory system
        self._memory: Optional[ConsolidatedMemory] = None
        if memory_enabled:
            mem_config = memory_config or {}
            self._memory = ConsolidatedMemory(
                short_term_capacity=mem_config.get("short_term_capacity", 200),
                consolidation_threshold=mem_config.get("consolidation_threshold", 0.7)
            )
        
        # Set up the team
        self._setup_team()
        
        # Research state
        self.current_research = None
        self.research_history = []
        self.research_count = 0
    
    async def initialize(self):
        """Initialize the workflow and memory system."""
        await super().initialize()
        if self._memory:
            await self._memory.start()
            logger.info(f"Memory system initialized for {self.config.name}")
    
    async def shutdown(self):
        """Shutdown the workflow and memory system."""
        if self._memory:
            await self._memory.stop()
        await super().shutdown()
    
    def _setup_team(self):
        """Set up the research team with memory-enabled agents."""
        # Use default model from settings if not specified
        from agenticraft.core.config import settings
        model = self.model or settings.default_model
        
        agents = []
        
        # Calculate agent distribution
        if self.team_size == 3:
            num_researchers = 1
            num_analysts = 1
            num_writers = 1
        elif self.team_size <= 5:
            num_researchers = 2
            num_analysts = 2
            num_writers = 1
        elif self.team_size <= 7:
            num_researchers = 3
            num_analysts = 2
            num_writers = 2
        else:
            num_researchers = self.team_size // 2
            num_analysts = (self.team_size - num_researchers) // 2
            num_writers = self.team_size - num_researchers - num_analysts
        
        # Create memory-enabled researchers
        for i in range(num_researchers):
            # Wrap researcher with memory capabilities
            agent = WebResearcher(
                name=f"Researcher_{i+1}",
                provider=self.provider,
                model=model
            )
            if self.memory_enabled:
                agent = self._wrap_with_memory(agent, "researcher")
            agents.append(agent)
        
        # Create memory-enabled analysts
        for i in range(num_analysts):
            agent = DataAnalyst(
                name=f"Analyst_{i+1}",
                provider=self.provider,
                model=model
            )
            if self.memory_enabled:
                agent = self._wrap_with_memory(agent, "analyst")
            agents.append(agent)
        
        # Create memory-enabled writers
        for i in range(num_writers):
            agent = TechnicalWriter(
                name=f"Writer_{i+1}",
                provider=self.provider,
                model=model
            )
            if self.memory_enabled:
                agent = self._wrap_with_memory(agent, "writer")
            agents.append(agent)
        
        # Create coordinator
        self.coordinator = SimpleCoordinator(
            agents=agents,
            name=f"{self.config.name}_Coordinator",
            strategy="load_balanced",
            provider=self.provider,
            model=model
        )
        
        # Track team composition
        self.team_composition = {
            "researchers": num_researchers,
            "analysts": num_analysts,
            "writers": num_writers,
            "total": self.team_size
        }
    
    def _wrap_with_memory(self, agent, agent_type: str):
        """Wrap an agent with memory capabilities."""
        # Create a memory-aware wrapper that delegates to the original agent
        # but adds memory functionality
        class MemoryWrapper:
            def __init__(self, base_agent, memory_system, agent_type):
                self.base_agent = base_agent
                self.memory = memory_system
                self.agent_type = agent_type
                # Expose base agent properties
                self.name = base_agent.name
                self.model = getattr(base_agent, 'model', None)
                self.provider = getattr(base_agent, 'provider', None)
            
            async def __call__(self, *args, **kwargs):
                """Make the wrapper callable like the base agent."""
                return await self.run(*args, **kwargs)
            
            async def run(self, task: str, context: Optional[Dict[str, Any]] = None):
                """Run with memory context."""
                if not self.memory:
                    # No memory, delegate to base agent
                    return await self.base_agent.run(task, context)
                
                # Recall relevant memories
                memories = await self.memory.retrieve(
                    query=task,
                    limit=5,
                    metadata_filter={"agent_type": self.agent_type}
                )
                
                # Build enhanced context
                memory_context = []
                if memories:
                    for result in memories:
                        memory_context.append({
                            "key": result.entry.key,
                            "insight": result.entry.value,
                            "relevance": result.relevance_score
                        })
                
                # Add memory context
                enhanced_context = context or {}
                if memory_context:
                    enhanced_context["previous_insights"] = memory_context
                
                # Run base agent
                result = await self.base_agent.run(task, enhanced_context)
                
                # Store result in memory
                await self.memory.store(
                    key=f"{self.agent_type}_{self.name}_{task[:50]}",
                    value={
                        "task": task,
                        "result": result.content if hasattr(result, 'content') else str(result),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    memory_type=MemoryType.SHORT_TERM,
                    metadata={
                        "agent_type": self.agent_type,
                        "agent_name": self.name,
                        "task_type": "research"
                    },
                    importance=0.6
                )
                
                return result
            
            # Delegate other attributes to base agent
            def __getattr__(self, name):
                return getattr(self.base_agent, name)
        
        return MemoryWrapper(agent, self._memory, agent_type)
    
    async def research(
        self,
        topic: str,
        depth: str = "comprehensive",
        audience: str = "general",
        focus_areas: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        continue_previous: bool = False
    ) -> Dict[str, Any]:
        """Conduct research with memory enhancement.
        
        Args:
            topic: The topic to research
            depth: Research depth ("quick", "standard", "comprehensive")
            audience: Target audience ("general", "technical", "executive")
            focus_areas: Optional specific areas to focus on
            context: Additional context
            continue_previous: Whether to continue from previous research
            
        Returns:
            Research report with memory-enhanced insights
        """
        start_time = datetime.utcnow()
        self.research_count += 1
        
        # Set research parameters
        self.current_research = {
            "topic": topic,
            "depth": depth,
            "audience": audience,
            "focus_areas": focus_areas,
            "start_time": start_time,
            "session_id": f"research_{self.research_count}"
        }
        
        # Check for previous research on similar topics
        previous_research = None
        if self._memory and (continue_previous or "continue" in topic.lower()):
            previous_results = await self._memory.retrieve(
                query=topic,
                memory_types=[MemoryType.LONG_TERM],
                limit=3,
                min_importance=0.7
            )
            
            if previous_results:
                previous_research = {
                    "found": True,
                    "insights": [r.entry.value for r in previous_results],
                    "continuation": True
                }
                logger.info(f"Found {len(previous_results)} relevant previous research items")
        
        # Phase 1: Research Planning (with memory context)
        research_plan = await self._plan_research_with_memory(
            topic, depth, focus_areas, context, previous_research
        )
        
        # Store research plan
        if self._memory:
            await self._memory.store(
                key=f"research_plan_{topic[:50]}",
                value={
                    "topic": topic,
                    "plan": research_plan["approach"],
                    "subtasks": research_plan["subtasks"]
                },
                memory_type=MemoryType.TASK,
                metadata={"task_id": self.current_research["session_id"]},
                importance=0.8
            )
        
        # Phase 2: Execute Research
        research_results = await self._execute_research(research_plan, context)
        
        # Phase 3: Analysis
        analysis_results = await self._analyze_findings(research_results, topic, context)
        
        # Phase 4: Report Generation
        report = await self._generate_report(
            topic=topic,
            research_results=research_results,
            analysis_results=analysis_results,
            audience=audience,
            context=context,
            previous_research=previous_research
        )
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Compile final result
        result = {
            "topic": topic,
            "executive_summary": report["executive_summary"],
            "full_report": report["full_report"],
            "key_findings": analysis_results["key_findings"],
            "recommendations": report["recommendations"],
            "sections": report["sections"],
            "metadata": {
                "team_composition": self.team_composition,
                "duration_seconds": duration,
                "depth": depth,
                "audience": audience,
                "timestamp": end_time.isoformat(),
                "memory_enabled": self.memory_enabled,
                "continued_from_previous": bool(previous_research),
                "session_id": self.current_research["session_id"]
            },
            "reasoning_trace": self._get_reasoning_trace()
        }
        
        # Store completed research in long-term memory
        if self._memory:
            await self._memory.store(
                key=f"completed_research_{topic[:50]}",
                value={
                    "topic": topic,
                    "summary": report["executive_summary"],
                    "key_findings": analysis_results["key_findings"],
                    "recommendations": report["recommendations"][:3]  # Top 3
                },
                memory_type=MemoryType.LONG_TERM,
                importance=0.9
            )
            
            # Trigger consolidation
            await self._memory.consolidate()
        
        # Save to history
        self.research_history.append(result)
        self.current_research = None
        
        return result
    
    async def _plan_research_with_memory(
        self,
        topic: str,
        depth: str,
        focus_areas: Optional[List[str]],
        context: Optional[Dict[str, Any]],
        previous_research: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Plan research with memory context."""
        planning_prompt = f"""Plan a {depth} research project on: {topic}

Consider:
1. What aspects need to be researched?
2. What data should be gathered?
3. What analysis would be valuable?"""
        
        if previous_research and previous_research.get("found"):
            planning_prompt += "\n\nPrevious research found:"
            for insight in previous_research["insights"][:2]:
                planning_prompt += f"\n- {insight.get('summary', insight)[:200]}..."
            planning_prompt += "\n\nBuild upon these insights and avoid duplicating work."
        
        if focus_areas:
            planning_prompt += f"\n\nFocus areas: {', '.join(focus_areas)}"
        
        # Get plan from coordinator
        plan_response = await self.coordinator.arun(planning_prompt, context=context)
        
        # Define research subtasks
        subtasks = self._generate_subtasks(topic, depth, focus_areas, previous_research)
        
        return {
            "approach": plan_response.content,
            "subtasks": subtasks,
            "reasoning": plan_response.reasoning,
            "builds_on_previous": bool(previous_research)
        }
    
    def _generate_subtasks(
        self,
        topic: str,
        depth: str,
        focus_areas: Optional[List[str]],
        previous_research: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate subtasks based on depth and previous research."""
        if depth == "quick":
            subtasks = [
                f"Quick overview of {topic}",
                f"Key facts and figures about {topic}",
                f"Recent developments in {topic}"
            ]
        elif depth == "standard":
            subtasks = [
                f"Comprehensive overview of {topic}",
                f"Current state and trends in {topic}",
                f"Key players and stakeholders in {topic}",
                f"Challenges and opportunities in {topic}",
                f"Recent developments and news about {topic}"
            ]
        else:  # comprehensive
            subtasks = [
                f"Deep dive into the fundamentals of {topic}",
                f"Historical development and evolution of {topic}",
                f"Current state and market analysis of {topic}",
                f"Key players, competitors, and stakeholders in {topic}",
                f"Technology trends and innovations in {topic}",
                f"Challenges, risks, and limitations of {topic}",
                f"Future outlook and predictions for {topic}",
                f"Best practices and recommendations for {topic}"
            ]
        
        # Modify subtasks if continuing previous research
        if previous_research and previous_research.get("found"):
            # Remove redundant subtasks and add continuation tasks
            subtasks = subtasks[len(subtasks)//2:]  # Keep latter half
            subtasks.insert(0, f"Build upon previous findings about {topic}")
            subtasks.append(f"Identify new developments since last research on {topic}")
        
        # Add focus area subtasks
        if focus_areas:
            for area in focus_areas[:3]:
                subtasks.append(f"Specific analysis of {area} in relation to {topic}")
        
        return subtasks
    
    async def get_research_history(
        self,
        topic_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get research history from memory.
        
        Args:
            topic_filter: Optional topic to filter by
            limit: Maximum number of results
            
        Returns:
            List of previous research summaries
        """
        if not self._memory:
            return self.research_history[-limit:]
        
        # Search long-term memory for research
        results = await self._memory.retrieve(
            query=topic_filter or "",
            memory_types=[MemoryType.LONG_TERM],
            limit=limit,
            metadata_filter={"task_type": "research"} if not topic_filter else None
        )
        
        history = []
        for result in results:
            if isinstance(result.entry.value, dict):
                history.append({
                    "topic": result.entry.value.get("topic", "Unknown"),
                    "summary": result.entry.value.get("summary", ""),
                    "timestamp": result.entry.timestamp.isoformat(),
                    "importance": result.entry.importance
                })
        
        return history
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        if not self._memory:
            return {"memory_enabled": False}
        
        return await self._memory.get_stats()
    
    async def clear_memory(self, memory_type: Optional[MemoryType] = None):
        """Clear memory of specific type or all."""
        if self._memory:
            if memory_type:
                await self._memory.short_term.clear(memory_type)
            else:
                await self._memory.clear_all()
            logger.info(f"Cleared memory for {self.config.name}")
