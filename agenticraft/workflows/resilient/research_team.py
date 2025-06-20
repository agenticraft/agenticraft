"""Resilient Research Team workflow with production-ready error handling.

This module enhances the base ResearchTeam with decorators for:
- Automatic retry on failures
- Timeouts for long-running operations
- Caching of research results
- Rate limiting for API calls
- Fallback mechanisms
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from agenticraft.workflows.research_team import ResearchTeam as BaseResearchTeam
from agenticraft.utils.decorators import (
    retry, timeout, cache, rate_limit, fallback, measure_time, resilient
)
from agenticraft.core.exceptions import AgentError, WorkflowError


class ResilientResearchTeam(BaseResearchTeam):
    """Production-ready research team with comprehensive error handling.
    
    Enhances the base ResearchTeam with:
    - Automatic retry on transient failures
    - Timeouts to prevent hanging
    - Caching to avoid redundant research
    - Rate limiting for API protection
    - Graceful fallbacks
    
    Example:
        ```python
        from agenticraft.workflows.resilient import ResilientResearchTeam
        
        # Create a resilient team
        team = ResilientResearchTeam(
            size=5,
            cache_results=True,
            max_retries=3
        )
        
        # Research with automatic error handling
        report = await team.research("AI safety frameworks")
        ```
    """
    
    def __init__(
        self,
        size: int = 5,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        name: str = "ResilientResearchTeam",
        cache_results: bool = True,
        max_retries: int = 3,
        timeout_seconds: float = 300.0,  # 5 minutes default
        **kwargs
    ):
        super().__init__(size, provider, model, name, **kwargs)
        
        # Resilience configuration
        self.cache_results = cache_results
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # Metrics tracking
        self.metrics = {
            "total_researches": 0,
            "successful_researches": 0,
            "failed_researches": 0,
            "cache_hits": 0,
            "retries": 0,
            "timeouts": 0
        }
    
    @measure_time(log_level="INFO")
    @rate_limit(calls=10, period=60.0)  # 10 researches per minute
    async def research(
        self,
        topic: str,
        depth: str = "comprehensive",
        audience: str = "general",
        focus_areas: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Conduct research with comprehensive error handling."""
        self.metrics["total_researches"] += 1
        
        # Apply caching if enabled
        if self.cache_results:
            return await self._cached_research(
                topic, depth, audience, focus_areas, context
            )
        else:
            return await self._resilient_research(
                topic, depth, audience, focus_areas, context
            )
    
    @cache(ttl=3600.0, maxsize=50)  # Cache for 1 hour
    async def _cached_research(
        self,
        topic: str,
        depth: str,
        audience: str,
        focus_areas: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Cached version of research."""
        # Check if this is a cache hit (for metrics)
        # In a real implementation, we'd hook into the cache decorator
        return await self._resilient_research(
            topic, depth, audience, focus_areas, context
        )
    
    @timeout(seconds=300.0)  # 5 minute timeout
    @retry(
        attempts=3,
        backoff="exponential",
        exceptions=(AgentError, WorkflowError, asyncio.TimeoutError)
    )
    async def _resilient_research(
        self,
        topic: str,
        depth: str,
        audience: str,
        focus_areas: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute research with retry logic."""
        try:
            result = await super().research(
                topic, depth, audience, focus_areas, context
            )
            self.metrics["successful_researches"] += 1
            return result
        except Exception as e:
            self.metrics["failed_researches"] += 1
            raise
    
    @timeout(seconds=60.0)  # 1 minute for planning
    @retry(attempts=2, backoff="exponential")
    @fallback(
        default={"approach": "Standard research approach", "subtasks": [], "reasoning": "Fallback plan"},
        exceptions=(AgentError, asyncio.TimeoutError)
    )
    async def _plan_research(
        self,
        topic: str,
        depth: str,
        focus_areas: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Plan research with timeout and fallback."""
        return await super()._plan_research(topic, depth, focus_areas, context)
    
    @timeout(seconds=180.0)  # 3 minutes for execution
    @retry(attempts=3, backoff="exponential", delay=2.0)
    async def _execute_research(
        self,
        research_plan: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute research with enhanced error handling."""
        try:
            return await super()._execute_research(research_plan, context)
        except asyncio.TimeoutError:
            self.metrics["timeouts"] += 1
            # Return partial results if available
            return self._get_partial_results(research_plan)
        except Exception as e:
            self.metrics["retries"] += 1
            raise
    
    @timeout(seconds=120.0)  # 2 minutes for analysis
    @fallback(
        default={
            "key_findings": ["Research completed but analysis unavailable"],
            "synthesis": "Analysis could not be completed",
            "analysis_tasks": [],
            "synthesis_tasks": []
        }
    )
    async def _analyze_findings(
        self,
        research_results: List[Dict[str, Any]],
        topic: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze findings with fallback on failure."""
        return await super()._analyze_findings(research_results, topic, context)
    
    @timeout(seconds=90.0)  # 1.5 minutes for report generation
    @retry(attempts=2, delay=1.0)
    @fallback(
        default={
            "full_report": "Report generation failed. Please see findings.",
            "executive_summary": "Research completed but report unavailable.",
            "sections": {},
            "recommendations": []
        }
    )
    async def _generate_report(
        self,
        topic: str,
        research_results: List[Dict[str, Any]],
        analysis_results: Dict[str, Any],
        audience: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate report with fallback."""
        return await super()._generate_report(
            topic, research_results, analysis_results, audience, context
        )
    
    def _get_partial_results(self, research_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get any partial results available."""
        # In a real implementation, this would check for completed subtasks
        return [{
            "subtask": "Partial research results",
            "agent": "System",
            "findings": "Research timed out. Partial results may be available.",
            "task_id": "timeout"
        }]
    
    @resilient(
        retry_attempts=3,
        timeout_seconds=30,
        fallback_value={},
        cache_ttl=300  # 5 minutes
    )
    async def get_team_status(self) -> Dict[str, Any]:
        """Get team status with full resilience."""
        status = await super().get_team_status()
        status["metrics"] = self.metrics
        status["resilience_config"] = {
            "cache_enabled": self.cache_results,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds
        }
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the research team."""
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics,
            "checks": {}
        }
        
        # Check coordinator health
        try:
            # Simple health check - can the coordinator respond?
            await asyncio.wait_for(
                self.coordinator.arun("Status check"),
                timeout=5.0
            )
            health["checks"]["coordinator"] = "healthy"
        except Exception as e:
            health["checks"]["coordinator"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"
        
        # Check agent availability
        healthy_agents = 0
        for name, agent in self.coordinator.agents.items():
            try:
                # Simple check - can the agent respond?
                await asyncio.wait_for(
                    agent.arun("Status check"),
                    timeout=2.0
                )
                healthy_agents += 1
            except:
                health["checks"][f"agent_{name}"] = "unhealthy"
        
        health["checks"]["agents_healthy"] = f"{healthy_agents}/{len(self.coordinator.agents)}"
        
        if healthy_agents < len(self.coordinator.agents) / 2:
            health["status"] = "unhealthy"
        
        # Check success rate
        if self.metrics["total_researches"] > 0:
            success_rate = self.metrics["successful_researches"] / self.metrics["total_researches"]
            health["metrics"]["success_rate"] = f"{success_rate:.2%}"
            
            if success_rate < 0.5:
                health["status"] = "degraded"
        
        return health
    
    def get_retry_strategy(self) -> Dict[str, Any]:
        """Get current retry strategy configuration."""
        return {
            "research": {
                "attempts": self.max_retries,
                "backoff": "exponential",
                "timeout": self.timeout_seconds
            },
            "planning": {
                "attempts": 2,
                "backoff": "exponential",
                "timeout": 60.0
            },
            "execution": {
                "attempts": 3,
                "backoff": "exponential",
                "timeout": 180.0,
                "delay": 2.0
            },
            "analysis": {
                "attempts": 1,  # Fallback only
                "timeout": 120.0
            },
            "report": {
                "attempts": 2,
                "delay": 1.0,
                "timeout": 90.0
            }
        }
