"""Research Team workflow for AgentiCraft.

This is the first hero workflow - a multi-agent research team that can be
deployed in 5 minutes to conduct professional research on any topic.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from agenticraft.agents.patterns import SimpleCoordinator
from agenticraft.agents.specialized import DataAnalyst, TechnicalWriter, WebResearcher
from agenticraft.core import Workflow, WorkflowConfig


class ResearchTeam(Workflow):
    """Multi-agent research team that conducts comprehensive research.
    
    This hero workflow demonstrates the power of multi-agent coordination
    by automatically:
    - Deploying multiple specialized agents
    - Coordinating research tasks
    - Analyzing findings
    - Producing professional reports
    
    Example:
        ```python
        from agenticraft.workflows import ResearchTeam
        
        team = ResearchTeam()
        report = await team.research("AI frameworks market analysis")
        print(report["executive_summary"])
        ```
    
    Args:
        size: Team size (3-10 agents). Default is 5.
        provider: LLM provider for all agents
        model: Model to use for all agents
        name: Name for this research team
        **kwargs: Additional configuration
    """
    
    def __init__(
        self,
        size: int = 5,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        name: str = "ResearchTeam",
        **kwargs
    ):
        # Initialize workflow
        config = WorkflowConfig(
            name=name,
            description="Multi-agent research team for comprehensive analysis",
            **kwargs
        )
        super().__init__(config)
        
        # Configuration
        self.team_size = max(3, min(size, 10))  # Clamp between 3-10
        self.provider = provider
        self.model = model
        
        # Set up the team
        self._setup_team()
        
        # Research state
        self.current_research = None
        self.research_history = []
    
    def _setup_team(self):
        """Set up the research team with appropriate agent distribution."""
        # Use default model from settings if not specified
        from agenticraft.core.config import settings
        model = self.model or settings.default_model
        
        agents = []
        
        # Calculate agent distribution based on team size
        if self.team_size == 3:
            # Minimal team: 1 researcher, 1 analyst, 1 writer
            num_researchers = 1
            num_analysts = 1
            num_writers = 1
        elif self.team_size <= 5:
            # Small team: 2 researchers, 2 analysts, 1 writer
            num_researchers = 2
            num_analysts = 2
            num_writers = 1
        elif self.team_size <= 7:
            # Medium team: 3 researchers, 2 analysts, 2 writers
            num_researchers = 3
            num_analysts = 2
            num_writers = 2
        else:
            # Large team: distribute proportionally
            num_researchers = self.team_size // 2
            num_analysts = (self.team_size - num_researchers) // 2
            num_writers = self.team_size - num_researchers - num_analysts
        
        # Create researchers
        for i in range(num_researchers):
            agents.append(
                WebResearcher(
                    name=f"Researcher_{i+1}",
                    provider=self.provider,
                    model=model
                )
            )
        
        # Create analysts
        for i in range(num_analysts):
            agents.append(
                DataAnalyst(
                    name=f"Analyst_{i+1}",
                    provider=self.provider,
                    model=model
                )
            )
        
        # Create writers
        for i in range(num_writers):
            agents.append(
                TechnicalWriter(
                    name=f"Writer_{i+1}",
                    provider=self.provider,
                    model=model
                )
            )
        
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
    
    async def research(
        self,
        topic: str,
        depth: str = "comprehensive",
        audience: str = "general",
        focus_areas: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Conduct research on a topic using the multi-agent team.
        
        Args:
            topic: The topic to research
            depth: Research depth ("quick", "standard", "comprehensive")
            audience: Target audience for the report ("general", "technical", "executive")
            focus_areas: Optional specific areas to focus on
            context: Additional context for the research
            
        Returns:
            Dictionary containing:
            - executive_summary: Brief summary for executives
            - full_report: Complete research report
            - key_findings: List of main findings
            - recommendations: List of recommendations
            - sections: Report broken down by sections
            - metadata: Research metadata (team, duration, etc.)
        """
        start_time = datetime.utcnow()
        
        # Set research parameters
        self.current_research = {
            "topic": topic,
            "depth": depth,
            "audience": audience,
            "focus_areas": focus_areas,
            "start_time": start_time
        }
        
        # Phase 1: Research Planning
        research_plan = await self._plan_research(topic, depth, focus_areas, context)
        
        # Phase 2: Parallel Research Execution
        research_results = await self._execute_research(research_plan, context)
        
        # Phase 3: Analysis and Synthesis
        analysis_results = await self._analyze_findings(research_results, topic, context)
        
        # Phase 4: Report Generation
        report = await self._generate_report(
            topic=topic,
            research_results=research_results,
            analysis_results=analysis_results,
            audience=audience,
            context=context
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
                "agents_involved": len(self.coordinator.agents),
                "total_subtasks": len(research_plan["subtasks"]) + len(analysis_results.get("synthesis_tasks", []))
            },
            "reasoning_trace": self._get_reasoning_trace()
        }
        
        # Save to history
        self.research_history.append(result)
        self.current_research = None
        
        return result
    
    async def _plan_research(
        self,
        topic: str,
        depth: str,
        focus_areas: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Plan the research approach."""
        # Use coordinator to plan
        planning_prompt = f"""Plan a {depth} research project on: {topic}

Consider:
1. What aspects need to be researched?
2. What data should be gathered?
3. What analysis would be valuable?"""
        
        if focus_areas:
            planning_prompt += f"\n\nFocus areas: {', '.join(focus_areas)}"
        
        # Get plan from coordinator
        plan_response = await self.coordinator.arun(planning_prompt, context=context)
        
        # Define research subtasks based on depth
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
        
        # Add focus area subtasks
        if focus_areas:
            for area in focus_areas[:3]:  # Limit to 3 focus areas
                subtasks.append(f"Specific analysis of {area} in relation to {topic}")
        
        return {
            "approach": plan_response.content,
            "subtasks": subtasks,
            "reasoning": plan_response.reasoning
        }
    
    async def _execute_research(
        self,
        research_plan: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute research tasks in parallel."""
        subtasks = research_plan["subtasks"]
        
        # Use coordinator to delegate and execute all subtasks
        research_results = await self.coordinator.coordinate(
            task=f"Research: {self.current_research['topic']}",
            subtasks=subtasks,
            context=context
        )
        
        # Extract individual results
        results = []
        for task_id, result in research_results["results"].items():
            results.append({
                "subtask": result["subtask"],
                "agent": result["agent"],
                "findings": result.get("result", result.get("error", "No result")),
                "task_id": task_id
            })
        
        return results
    
    async def _analyze_findings(
        self,
        research_results: List[Dict[str, Any]],
        topic: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze research findings to extract insights."""
        # Prepare findings for analysis
        all_findings = [
            {
                "source": r["agent"],
                "content": r["findings"]
            }
            for r in research_results
        ]
        
        # Create analysis tasks
        analysis_tasks = [
            "Identify key themes and patterns across all research findings",
            "Extract the most important insights and takeaways",
            "Identify any contradictions or gaps in the research",
            "Synthesize findings into a coherent narrative"
        ]
        
        # Execute analysis
        analysis_results = await self.coordinator.coordinate(
            task=f"Analyze findings for: {topic}",
            subtasks=analysis_tasks,
            context={"findings": all_findings, **(context or {})}
        )
        
        # Extract key findings from analysis
        key_findings = []
        for result in analysis_results["results"].values():
            if "result" in result and result["agent"].startswith("Analyst"):
                # This is from an analyst - extract insights
                content = result["result"]
                if isinstance(content, str) and len(content) > 50:
                    # Simple extraction of key points
                    lines = content.split('\n')
                    for line in lines:
                        if any(marker in line.lower() for marker in ['key', 'important', 'finding', 'insight']):
                            finding = line.strip().lstrip('•-*').strip()
                            if finding and len(finding) > 20:
                                key_findings.append(finding)
        
        # Limit to top 5 findings
        key_findings = key_findings[:5]
        
        # Aggregate synthesis
        synthesis = analysis_results.get("aggregation", "")
        
        return {
            "key_findings": key_findings,
            "synthesis": synthesis,
            "analysis_tasks": analysis_results.get("assignments", []),
            "synthesis_tasks": analysis_tasks
        }
    
    async def _generate_report(
        self,
        topic: str,
        research_results: List[Dict[str, Any]],
        analysis_results: Dict[str, Any],
        audience: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate the final research report."""
        # Prepare content for report generation
        all_findings = []
        for r in research_results:
            all_findings.append({
                "source": r["agent"],
                "findings": r["findings"]
            })
        
        # Add analysis results
        all_findings.append({
            "source": "Analysis Team",
            "findings": analysis_results["synthesis"]
        })
        
        # Select a writer (coordinator will handle this)
        report_task = f"""Create a professional research report on: {topic}

Target Audience: {audience}
Key Findings: {', '.join(analysis_results['key_findings'][:3])}

Include all research findings and analysis results in a cohesive report."""
        
        # Delegate to a writer
        assignment = await self.coordinator.delegate_task(report_task, context)
        
        # Execute with the assigned writer
        writer_result = await self.coordinator.execute_task(assignment, {
            "findings": all_findings,
            "audience": audience,
            **(context or {})
        })
        
        # Get the writer agent for specialized formatting
        writer_agent = self.coordinator.agents.get(assignment.assigned_to)
        
        if writer_agent and hasattr(writer_agent, 'create_report'):
            # Use specialized report creation
            report = await writer_agent.create_report(
                title=f"Research Report: {topic}",
                findings=all_findings,
                report_type="research",
                audience=audience,
                context=context
            )
            
            # Create executive summary
            exec_summary = await writer_agent.create_executive_summary(
                report_content=report["full_report"],
                key_findings=analysis_results["key_findings"],
                recommendations=report.get("recommendations", []),
                context=context
            )
            
            report["executive_summary"] = exec_summary
        else:
            # Fallback to basic formatting
            report = {
                "full_report": writer_result.content if hasattr(writer_result, 'content') else str(writer_result),
                "executive_summary": analysis_results["key_findings"][0] if analysis_results["key_findings"] else "Research completed.",
                "sections": {},
                "recommendations": []
            }
        
        return report
    
    def _get_reasoning_trace(self) -> List[Dict[str, Any]]:
        """Get reasoning trace from all agents."""
        trace = []
        
        # Get coordinator's reasoning
        if hasattr(self.coordinator, 'get_reasoning_summary'):
            trace.append({
                "agent": "Coordinator",
                "reasoning": self.coordinator.get_reasoning_summary()
            })
        
        # Get delegation history
        if hasattr(self.coordinator, 'delegation_history'):
            for delegation in self.coordinator.delegation_history[-5:]:  # Last 5 delegations
                trace.append({
                    "agent": "Coordinator",
                    "task": delegation.task,
                    "delegated_to": delegation.selected_agent,
                    "reasoning": delegation.reasoning
                })
        
        return trace
    
    async def get_team_status(self) -> Dict[str, Any]:
        """Get current status of the research team."""
        status = {
            "team_name": self.config.name,
            "team_size": self.team_size,
            "composition": self.team_composition,
            "agents": {},
            "current_research": self.current_research,
            "research_count": len(self.research_history)
        }
        
        # Get each agent's status
        for name, agent in self.coordinator.agents.items():
            status["agents"][name] = {
                "type": agent.__class__.__name__,
                "ready": True,  # In real implementation, check actual status
                "workload": self.coordinator.workload.get(name, 0)
            }
        
        return status
    
    async def adjust_team(
        self,
        add_researchers: int = 0,
        add_analysts: int = 0,
        add_writers: int = 0
    ) -> Dict[str, Any]:
        """Dynamically adjust team composition.
        
        Args:
            add_researchers: Number of researchers to add (negative to remove)
            add_analysts: Number of analysts to add (negative to remove)
            add_writers: Number of writers to add (negative to remove)
            
        Returns:
            New team composition
        """
        # Calculate new team size
        new_size = self.team_size + add_researchers + add_analysts + add_writers
        new_size = max(3, min(new_size, 10))  # Keep within bounds
        
        # Rebuild team if size changed
        if new_size != self.team_size:
            self.team_size = new_size
            self._setup_team()
        
        return self.team_composition
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ResearchTeam(name='{self.config.name}', "
            f"size={self.team_size}, "
            f"composition={self.team_composition})"
        )
