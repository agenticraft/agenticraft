"""Core Agent implementation"""

from typing import List, Optional, Dict, Any
import asyncio
from dataclasses import dataclass, field
import structlog

from agenticraft.core.tool import Tool
from agenticraft.core.memory import Memory

logger = structlog.get_logger()


@dataclass
class AgentConfig:
    """Configuration for an Agent"""
    name: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None
    memory_enabled: bool = False
    

class Agent:
    """Base Agent class for AgentiCraft"""
    
    def __init__(
        self,
        name: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        **kwargs
    ):
        """Initialize an Agent
        
        Args:
            name: Name of the agent
            model: LLM model to use
            temperature: Temperature for generation
            **kwargs: Additional configuration
        """
        self.config = AgentConfig(
            name=name,
            model=model,
            temperature=temperature,
            **kwargs
        )
        self.tools: Dict[str, Tool] = {}
        self.memory: Optional[Memory] = None
        
        if self.config.memory_enabled:
            self.memory = Memory()
            
        logger.info(
            "agent_initialized",
            name=name,
            model=model,
            temperature=temperature
        )
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent
        
        Args:
            tool: Tool instance to add
        """
        self.tools[tool.name] = tool
        logger.debug("tool_added", agent=self.config.name, tool=tool.name)
    
    async def run(self, prompt: str) -> str:
        """Run the agent with a prompt
        
        Args:
            prompt: User prompt
            
        Returns:
            Agent response
        """
        logger.info("agent_run_started", agent=self.config.name, prompt=prompt)
        
        # Add memory context if enabled
        if self.memory:
            context = self.memory.get_context()
            prompt = f"{context}\n\nUser: {prompt}"
        
        # TODO: Implement actual LLM call
        response = f"I'm {self.config.name}. You said: {prompt}"
        
        # Store in memory if enabled
        if self.memory:
            self.memory.add_message("user", prompt)
            self.memory.add_message("assistant", response)
        
        logger.info("agent_run_completed", agent=self.config.name)
        return response
    
    async def think(self, prompt: str) -> Dict[str, Any]:
        """Agent's thinking process
        
        Args:
            prompt: User prompt
            
        Returns:
            Thought process
        """
        return {
            "understanding": f"I need to help with: {prompt}",
            "tools_needed": list(self.tools.keys()),
            "approach": "I'll process this step by step"
        }


class ChatAgent(Agent):
    """Specialized agent for chat interactions"""
    
    def __init__(self, name: str, memory: bool = True, **kwargs):
        """Initialize a ChatAgent with memory enabled by default"""
        super().__init__(name, memory_enabled=memory, **kwargs)
    
    async def chat(self, message: str) -> str:
        """Chat with the agent
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        return await self.run(message)
