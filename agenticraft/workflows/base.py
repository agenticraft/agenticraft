"""Base workflow class for AgentiCraft.

This module provides the base Workflow class that other workflow
implementations can extend.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Workflow:
    """Base class for workflows in AgentiCraft.
    
    A workflow coordinates multiple agents to accomplish complex tasks.
    """
    
    def __init__(self, name: str, **kwargs):
        """Initialize workflow.
        
        Args:
            name: Workflow name
            **kwargs: Additional workflow configuration
        """
        self.name = name
        self.agents: Dict[str, Any] = {}
        self.config = kwargs
        self._running = False
        
    async def initialize(self) -> None:
        """Initialize the workflow and its agents."""
        logger.info(f"Initializing workflow: {self.name}")
        
    async def execute(self, **kwargs) -> Any:
        """Execute the workflow.
        
        Args:
            **kwargs: Workflow execution parameters
            
        Returns:
            Workflow execution result
        """
        raise NotImplementedError("Subclasses must implement execute()")
        
    async def cleanup(self) -> None:
        """Cleanup workflow resources."""
        logger.info(f"Cleaning up workflow: {self.name}")
        
    def add_agent(self, agent_id: str, agent: Any) -> None:
        """Add an agent to the workflow.
        
        Args:
            agent_id: Unique identifier for the agent
            agent: Agent instance
        """
        self.agents[agent_id] = agent
        
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get an agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_id)
        
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}', agents={len(self.agents)})"
