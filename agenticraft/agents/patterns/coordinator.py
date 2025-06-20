"""Simple multi-agent coordinator for AgentiCraft.

This module implements a minimal coordinator for multi-agent teams,
extracted and simplified from Agentic Framework's hierarchical coordination.
Focuses on transparency and simplicity over complex features.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from agenticraft.core import Agent

logger = logging.getLogger(__name__)


@dataclass
class TaskAssignment:
    """Simple task assignment for coordination."""
    task_id: str = field(default_factory=lambda: str(uuid4()))
    task_description: str = ""
    assigned_to: str = ""
    assigned_by: str = "coordinator"
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class DelegationReasoning:
    """Reasoning trace for delegation decisions."""
    task: str
    selected_agent: str
    reasoning: str
    workload_before: Dict[str, float]
    workload_after: Dict[str, float]


class SimpleCoordinator(Agent):
    """Minimal multi-agent coordinator for Research Team and other heroes.
    
    This coordinator manages a team of agents with:
    - Simple round-robin or load-balanced delegation
    - Transparent reasoning about decisions
    - Basic result aggregation
    - No complex hierarchies or roles
    
    Args:
        agents: List of Agent instances to coordinate
        name: Name for the coordinator
        strategy: "round_robin" or "load_balanced"
        **kwargs: Additional arguments passed to Agent base class
    """
    
    def __init__(
        self,
        agents: List[Agent],
        name: str = "Coordinator",
        strategy: str = "load_balanced",
        **kwargs
    ):
        # Remove provider from kwargs if present (handled by Agent base class)
        kwargs.pop('provider', None)
        
        # Initialize as an Agent with coordination capabilities
        instructions = kwargs.pop(
            "instructions",
            "You are a team coordinator. Your job is to delegate tasks to the right team members and aggregate their results."
        )
        super().__init__(name=name, instructions=instructions, **kwargs)
        
        # Team management
        self.agents = {agent.name: agent for agent in agents}
        self.strategy = strategy
        self.workload: Dict[str, float] = {name: 0.0 for name in self.agents}
        
        # Task tracking
        self.assignments: Dict[str, TaskAssignment] = {}
        self.last_delegated_to = None  # For round-robin
        
        # Reasoning transparency
        self.last_delegation_reasoning: Optional[DelegationReasoning] = None
        self.delegation_history: List[DelegationReasoning] = []
        
        logger.info(f"Initialized SimpleCoordinator '{name}' with {len(agents)} agents")
    
    async def delegate_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskAssignment:
        """Delegate a task to the most appropriate agent.
        
        Args:
            task: Task description
            context: Optional context for the task
            
        Returns:
            TaskAssignment with delegation details
        """
        # Think about who should handle this task
        thought = await self.arun(
            f"I need to delegate this task: {task}\n"
            f"Available agents: {list(self.agents.keys())}\n"
            f"Current workloads: {self.workload}\n"
            f"Strategy: {self.strategy}\n\n"
            f"Which agent should handle this task?"
        )
        
        # Select agent based on strategy
        if self.strategy == "round_robin":
            selected_agent = self._select_round_robin()
        else:  # load_balanced
            selected_agent = self._select_load_balanced()
        
        # Create assignment
        assignment = TaskAssignment(
            task_description=task,
            assigned_to=selected_agent
        )
        self.assignments[assignment.task_id] = assignment
        
        # Update workload
        workload_before = self.workload.copy()
        self.workload[selected_agent] += 1.0
        
        # Record reasoning
        self.last_delegation_reasoning = DelegationReasoning(
            task=task,
            selected_agent=selected_agent,
            reasoning=thought.reasoning if hasattr(thought, 'reasoning') and thought.reasoning else "Direct delegation",
            workload_before=workload_before,
            workload_after=self.workload.copy()
        )
        self.delegation_history.append(self.last_delegation_reasoning)
        
        logger.info(f"Delegated task '{task[:50]}...' to {selected_agent}")
        return assignment
    
    async def execute_task(
        self,
        assignment: TaskAssignment,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a delegated task with the assigned agent.
        
        Args:
            assignment: Task assignment to execute
            context: Optional context for execution
            
        Returns:
            Result from the assigned agent
        """
        if assignment.assigned_to not in self.agents:
            raise ValueError(f"Agent '{assignment.assigned_to}' not found")
        
        agent = self.agents[assignment.assigned_to]
        assignment.status = "running"
        
        try:
            # Execute with agent
            response = await agent.arun(
                assignment.task_description,
                context=context
            )
            
            # Update assignment
            assignment.status = "completed"
            assignment.result = response
            assignment.completed_at = datetime.utcnow()
            
            # Update workload
            self.workload[assignment.assigned_to] = max(
                0, self.workload[assignment.assigned_to] - 1.0
            )
            
            return response
            
        except Exception as e:
            assignment.status = "failed"
            assignment.result = {"error": str(e)}
            assignment.completed_at = datetime.utcnow()
            
            # Update workload even on failure
            self.workload[assignment.assigned_to] = max(
                0, self.workload[assignment.assigned_to] - 1.0
            )
            
            raise
    
    async def coordinate(
        self,
        task: str,
        subtasks: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Coordinate a complex task by breaking it down and delegating.
        
        Args:
            task: Main task description
            subtasks: Optional pre-defined subtasks (otherwise will decompose)
            context: Optional context for all subtasks
            
        Returns:
            Aggregated results from all subtasks
        """
        # If no subtasks provided, decompose the main task
        if not subtasks:
            decomposition_thought = await self.arun(
                f"I need to break down this task into subtasks for my team:\n"
                f"Task: {task}\n"
                f"Team members: {list(self.agents.keys())}\n\n"
                f"Please list the subtasks needed to complete this task."
            )
            
            # Simple decomposition - in real implementation, this would be smarter
            subtasks = self._extract_subtasks_from_thought(decomposition_thought)
        
        # Delegate and execute each subtask
        results = {}
        assignments = []
        
        for subtask in subtasks:
            # Delegate
            assignment = await self.delegate_task(subtask, context)
            assignments.append(assignment)
            
            # Execute
            try:
                result = await self.execute_task(assignment, context)
                results[assignment.task_id] = {
                    "subtask": subtask,
                    "agent": assignment.assigned_to,
                    "result": result.content if hasattr(result, 'content') else result
                }
            except Exception as e:
                results[assignment.task_id] = {
                    "subtask": subtask,
                    "agent": assignment.assigned_to,
                    "error": str(e)
                }
        
        # Aggregate results
        aggregation = await self._aggregate_results(task, results)
        
        return {
            "task": task,
            "subtasks": subtasks,
            "assignments": [
                {
                    "id": a.task_id,
                    "task": a.task_description,
                    "agent": a.assigned_to,
                    "status": a.status
                }
                for a in assignments
            ],
            "results": results,
            "aggregation": aggregation,
            "reasoning": self.get_reasoning_summary()
        }
    
    def _select_round_robin(self) -> str:
        """Select next agent using round-robin strategy."""
        agent_names = list(self.agents.keys())
        
        if self.last_delegated_to is None:
            selected = agent_names[0]
        else:
            try:
                current_idx = agent_names.index(self.last_delegated_to)
                selected = agent_names[(current_idx + 1) % len(agent_names)]
            except ValueError:
                selected = agent_names[0]
        
        self.last_delegated_to = selected
        return selected
    
    def _select_load_balanced(self) -> str:
        """Select agent with lowest workload."""
        return min(self.workload.keys(), key=lambda k: self.workload[k])
    
    def _extract_subtasks_from_thought(self, thought) -> List[str]:
        """Extract subtasks from reasoning - simplified version."""
        # In a real implementation, this would parse the thought more intelligently
        # For now, return a simple default breakdown
        # TODO: Parse the actual response content to extract subtasks
        return [
            "Gather initial information",
            "Analyze and process data",
            "Synthesize findings",
            "Format final output"
        ]
    
    async def _aggregate_results(
        self,
        task: str,
        results: Dict[str, Any]
    ) -> str:
        """Aggregate results from multiple agents."""
        # Use the coordinator's own reasoning to aggregate
        results_summary = "\n".join([
            f"- {r['agent']} ({r['subtask']}): {r.get('result', r.get('error', 'No result'))[:100]}..."
            for r in results.values()
        ])
        
        aggregation_response = await self.arun(
            f"Aggregate these results into a cohesive response for the task: {task}\n\n"
            f"Results from team:\n{results_summary}"
        )
        
        return aggregation_response.content
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get a summary of delegation reasoning."""
        return {
            "strategy": self.strategy,
            "current_workload": self.workload.copy(),
            "last_delegation": (
                {
                    "task": self.last_delegation_reasoning.task,
                    "selected": self.last_delegation_reasoning.selected_agent,
                    "reasoning": self.last_delegation_reasoning.reasoning
                }
                if self.last_delegation_reasoning else None
            ),
            "total_delegations": len(self.delegation_history)
        }
    
    def reset_workload(self):
        """Reset workload tracking."""
        self.workload = {name: 0.0 for name in self.agents}
        logger.info("Reset workload for all agents")
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SimpleCoordinator(name='{self.name}', "
            f"agents={len(self.agents)}, "
            f"strategy='{self.strategy}')"
        )
