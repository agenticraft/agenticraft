"""
Agent health monitoring for production deployments.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import logging
from dataclasses import dataclass, field
import psutil
import os

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status levels."""
    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    UNRESPONSIVE = "unresponsive"
    ERROR = "error"


@dataclass
class AgentHealthMetrics:
    """Metrics for individual agent health."""
    agent_name: str
    agent_type: str
    status: AgentStatus = AgentStatus.AVAILABLE
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time_ms: float = 0.0
    current_load: float = 0.0  # 0-1 scale
    memory_usage_mb: float = 0.0
    last_activity: Optional[datetime] = None
    error_messages: List[str] = field(default_factory=list)
    capabilities: Set[str] = field(default_factory=set)


class AgentHealth:
    """Monitor health of individual agents."""
    
    def __init__(self):
        """Initialize agent health monitor."""
        self.agents: Dict[str, AgentHealthMetrics] = {}
        self._response_times: Dict[str, List[float]] = {}
        self._task_queues: Dict[str, int] = {}
        self.start_time = datetime.now()
        
    def register_agent(self, agent_name: str, agent_type: str, capabilities: Set[str] = None):
        """Register an agent for health monitoring."""
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentHealthMetrics(
                agent_name=agent_name,
                agent_type=agent_type,
                capabilities=capabilities or set()
            )
            self._response_times[agent_name] = []
            self._task_queues[agent_name] = 0
            logger.info(f"Registered agent '{agent_name}' of type '{agent_type}' for health monitoring")
            
    async def check_agent_health(self, agent_instance: Any, agent_name: str) -> AgentHealthMetrics:
        """
        Perform health check on a specific agent.
        
        Args:
            agent_instance: The agent instance to check
            agent_name: Name of the agent
            
        Returns:
            AgentHealthMetrics with current status
        """
        if agent_name not in self.agents:
            self.register_agent(agent_name, type(agent_instance).__name__)
            
        metrics = self.agents[agent_name]
        
        try:
            # Check 1: Agent responsiveness
            start_time = time.time()
            
            # Try to ping the agent (assuming it has a ping or similar method)
            if hasattr(agent_instance, "ping"):
                response = await agent_instance.ping()
                response_time = (time.time() - start_time) * 1000
                self._record_response_time(agent_name, response_time)
                
                if response_time < 100:  # Less than 100ms
                    responsiveness_score = 1.0
                elif response_time < 500:
                    responsiveness_score = 0.7
                elif response_time < 1000:
                    responsiveness_score = 0.4
                else:
                    responsiveness_score = 0.1
            else:
                # If no ping method, check if instance is alive
                responsiveness_score = 1.0 if agent_instance is not None else 0.0
                
            # Check 2: Task queue length (if available)
            queue_score = 1.0
            if hasattr(agent_instance, "task_queue"):
                queue_length = len(agent_instance.task_queue)
                self._task_queues[agent_name] = queue_length
                
                if queue_length < 10:
                    queue_score = 1.0
                elif queue_length < 50:
                    queue_score = 0.7
                elif queue_length < 100:
                    queue_score = 0.4
                else:
                    queue_score = 0.1
                    
            # Check 3: Memory usage
            memory_score = 1.0
            try:
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                metrics.memory_usage_mb = memory_mb
                
                # Assume agents should use less than 500MB
                if memory_mb < 200:
                    memory_score = 1.0
                elif memory_mb < 500:
                    memory_score = 0.7
                elif memory_mb < 1000:
                    memory_score = 0.4
                else:
                    memory_score = 0.1
            except:
                pass
                
            # Check 4: Error rate
            error_score = 1.0
            if metrics.tasks_completed > 0:
                error_rate = metrics.tasks_failed / (metrics.tasks_completed + metrics.tasks_failed)
                if error_rate < 0.01:  # Less than 1% error
                    error_score = 1.0
                elif error_rate < 0.05:
                    error_score = 0.7
                elif error_rate < 0.1:
                    error_score = 0.4
                else:
                    error_score = 0.1
                    
            # Calculate overall health score
            overall_score = (responsiveness_score + queue_score + memory_score + error_score) / 4
            metrics.current_load = 1 - overall_score  # Invert for load metric
            
            # Determine status based on score
            if overall_score >= 0.8:
                metrics.status = AgentStatus.AVAILABLE
            elif overall_score >= 0.6:
                metrics.status = AgentStatus.BUSY
            elif overall_score >= 0.4:
                metrics.status = AgentStatus.OVERLOADED
            else:
                metrics.status = AgentStatus.UNRESPONSIVE
                
            metrics.last_activity = datetime.now()
            
        except Exception as e:
            metrics.status = AgentStatus.ERROR
            metrics.error_messages.append(f"{datetime.now().isoformat()}: {str(e)}")
            # Keep only last 10 error messages
            metrics.error_messages = metrics.error_messages[-10:]
            logger.error(f"Health check failed for agent '{agent_name}': {e}")
            
        return metrics
        
    def _record_response_time(self, agent_name: str, response_time_ms: float):
        """Record agent response time."""
        if agent_name not in self._response_times:
            self._response_times[agent_name] = []
            
        times = self._response_times[agent_name]
        times.append(response_time_ms)
        
        # Keep only last 100 response times
        if len(times) > 100:
            self._response_times[agent_name] = times[-100:]
            
        # Update average
        self.agents[agent_name].average_response_time_ms = sum(times) / len(times)
        
    def record_task_completion(self, agent_name: str, success: bool = True, duration_ms: float = None):
        """Record task completion for an agent."""
        if agent_name not in self.agents:
            logger.warning(f"Agent '{agent_name}' not registered for health monitoring")
            return
            
        metrics = self.agents[agent_name]
        
        if success:
            metrics.tasks_completed += 1
        else:
            metrics.tasks_failed += 1
            
        if duration_ms is not None:
            self._record_response_time(agent_name, duration_ms)
            
        metrics.last_activity = datetime.now()
        
    def get_agent_status(self, agent_name: str) -> Optional[AgentHealthMetrics]:
        """Get current status for a specific agent."""
        return self.agents.get(agent_name)
        
    def get_all_agents_status(self) -> Dict[str, AgentHealthMetrics]:
        """Get status for all monitored agents."""
        return self.agents.copy()
        
    def get_available_agents(self, required_capability: str = None) -> List[str]:
        """
        Get list of available agents.
        
        Args:
            required_capability: Optional capability filter
            
        Returns:
            List of available agent names
        """
        available = []
        
        for agent_name, metrics in self.agents.items():
            if metrics.status in [AgentStatus.AVAILABLE, AgentStatus.BUSY]:
                if required_capability is None or required_capability in metrics.capabilities:
                    available.append(agent_name)
                    
        return available
        
    def get_healthiest_agent(self, agent_type: str = None, required_capability: str = None) -> Optional[str]:
        """
        Get the healthiest available agent.
        
        Args:
            agent_type: Optional agent type filter
            required_capability: Optional capability filter
            
        Returns:
            Name of healthiest agent or None
        """
        candidates = []
        
        for agent_name, metrics in self.agents.items():
            # Skip unhealthy agents
            if metrics.status not in [AgentStatus.AVAILABLE, AgentStatus.BUSY]:
                continue
                
            # Apply filters
            if agent_type and metrics.agent_type != agent_type:
                continue
            if required_capability and required_capability not in metrics.capabilities:
                continue
                
            candidates.append((agent_name, metrics))
            
        if not candidates:
            return None
            
        # Sort by load (lower is better)
        candidates.sort(key=lambda x: x[1].current_load)
        return candidates[0][0]
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all agents' health."""
        total_agents = len(self.agents)
        
        status_counts = {
            AgentStatus.AVAILABLE: 0,
            AgentStatus.BUSY: 0,
            AgentStatus.OVERLOADED: 0,
            AgentStatus.UNRESPONSIVE: 0,
            AgentStatus.ERROR: 0,
        }
        
        total_tasks = 0
        total_failures = 0
        avg_response_times = []
        
        for metrics in self.agents.values():
            status_counts[metrics.status] += 1
            total_tasks += metrics.tasks_completed + metrics.tasks_failed
            total_failures += metrics.tasks_failed
            
            if metrics.average_response_time_ms > 0:
                avg_response_times.append(metrics.average_response_time_ms)
                
        return {
            "total_agents": total_agents,
            "status_breakdown": {
                status.value: count for status, count in status_counts.items()
            },
            "healthy_agents": status_counts[AgentStatus.AVAILABLE] + status_counts[AgentStatus.BUSY],
            "unhealthy_agents": (
                status_counts[AgentStatus.OVERLOADED] + 
                status_counts[AgentStatus.UNRESPONSIVE] + 
                status_counts[AgentStatus.ERROR]
            ),
            "total_tasks_processed": total_tasks,
            "overall_success_rate": (
                (total_tasks - total_failures) / total_tasks if total_tasks > 0 else 0
            ),
            "average_response_time_ms": (
                sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0
            ),
            "uptime": str(datetime.now() - self.start_time),
        }
        
    async def continuous_monitoring(self, agents: Dict[str, Any], interval_seconds: int = 30):
        """
        Continuously monitor multiple agents.
        
        Args:
            agents: Dictionary of agent_name -> agent_instance
            interval_seconds: Check interval in seconds
        """
        logger.info(f"Starting continuous monitoring for {len(agents)} agents")
        
        while True:
            try:
                tasks = []
                for agent_name, agent_instance in agents.items():
                    tasks.append(self.check_agent_health(agent_instance, agent_name))
                    
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Agent monitoring error: {result}")
                        
                # Log summary
                summary = self.get_summary()
                logger.info(
                    f"Agent health summary: {summary['healthy_agents']}/{summary['total_agents']} healthy, "
                    f"avg response time: {summary['average_response_time_ms']:.2f}ms"
                )
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
            await asyncio.sleep(interval_seconds)


# Load balancer helper using agent health
class HealthBasedLoadBalancer:
    """Load balancer that uses agent health metrics."""
    
    def __init__(self, agent_health: AgentHealth):
        """Initialize load balancer."""
        self.agent_health = agent_health
        
    async def select_agent(self, agent_type: str = None, required_capability: str = None) -> Optional[str]:
        """
        Select best agent based on health metrics.
        
        Args:
            agent_type: Optional agent type filter
            required_capability: Optional capability filter
            
        Returns:
            Selected agent name or None
        """
        return self.agent_health.get_healthiest_agent(agent_type, required_capability)
        
    async def distribute_tasks(self, tasks: List[Any], agent_type: str = None) -> Dict[str, List[Any]]:
        """
        Distribute tasks among healthy agents.
        
        Args:
            tasks: List of tasks to distribute
            agent_type: Optional agent type filter
            
        Returns:
            Dictionary of agent_name -> assigned tasks
        """
        distribution = {}
        available_agents = self.agent_health.get_available_agents()
        
        if not available_agents:
            logger.warning("No available agents for task distribution")
            return distribution
            
        # Get agent loads
        agent_loads = []
        for agent_name in available_agents:
            metrics = self.agent_health.get_agent_status(agent_name)
            if agent_type and metrics.agent_type != agent_type:
                continue
            agent_loads.append((agent_name, metrics.current_load))
            
        if not agent_loads:
            return distribution
            
        # Sort by load (ascending)
        agent_loads.sort(key=lambda x: x[1])
        
        # Distribute tasks inversely proportional to load
        total_capacity = sum(1 - load for _, load in agent_loads)
        
        for i, task in enumerate(tasks):
            # Select agent based on capacity
            cumulative = 0
            target = (i % 100) / 100 * total_capacity
            
            for agent_name, load in agent_loads:
                cumulative += (1 - load)
                if cumulative >= target:
                    if agent_name not in distribution:
                        distribution[agent_name] = []
                    distribution[agent_name].append(task)
                    break
                    
        return distribution
