"""Memory-enhanced agent base class for AgentiCraft.

Provides memory capabilities to any agent that inherits from it.
"""

from typing import Any, Dict, List, Optional
import logging

from ..core import Agent
from . import MemoryType, MemorySearchResult
from .consolidation import ConsolidatedMemory

logger = logging.getLogger(__name__)


class MemoryAgent(Agent):
    """Agent with integrated memory capabilities."""
    
    def __init__(
        self,
        name: str,
        model: str = "gpt-4",
        memory_enabled: bool = True,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, model)
        
        self.memory_enabled = memory_enabled
        self._memory: Optional[ConsolidatedMemory] = None
        
        if memory_enabled:
            config = memory_config or {}
            self._memory = ConsolidatedMemory(
                short_term_capacity=config.get("short_term_capacity", 100),
                consolidation_threshold=config.get("consolidation_threshold", 0.7)
            )
    
    async def initialize(self):
        """Initialize agent with memory system."""
        await super().initialize()
        if self._memory:
            await self._memory.start()
            logger.info(f"Memory system initialized for agent {self.name}")
    
    async def shutdown(self):
        """Shutdown agent and memory system."""
        if self._memory:
            await self._memory.stop()
        await super().shutdown()
    
    async def remember(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store something in memory."""
        if not self._memory:
            return None
        
        return await self._memory.store(
            key=key,
            value=value,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )
    
    async def recall(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """Recall memories matching the query."""
        if not self._memory:
            return []
        
        return await self._memory.retrieve(
            query=query,
            memory_types=memory_types,
            limit=limit,
            min_importance=min_importance,
            metadata_filter=metadata_filter
        )
    
    async def remember_task_context(
        self,
        task_id: str,
        key: str,
        value: Any,
        importance: float = 0.5
    ) -> Optional[str]:
        """Remember something specific to a task."""
        return await self.remember(
            key=key,
            value=value,
            memory_type=MemoryType.TASK,
            importance=importance,
            metadata={"task_id": task_id}
        )
    
    async def recall_task_context(
        self,
        task_id: str,
        query: str = "",
        limit: int = 10
    ) -> List[MemorySearchResult]:
        """Recall task-specific memories."""
        return await self.recall(
            query=query,
            memory_types=[MemoryType.TASK],
            limit=limit,
            metadata_filter={"task_id": task_id}
        )
    
    async def consolidate_memories(self) -> Dict[str, int]:
        """Manually trigger memory consolidation."""
        if not self._memory:
            return {"promoted": 0, "deleted": 0}
        
        return await self._memory.consolidate()
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        if not self._memory:
            return {"enabled": False}
        
        stats = await self._memory.get_stats()
        stats["enabled"] = True
        return stats
    
    async def think_with_memory(self, prompt: str) -> str:
        """Think about a prompt with memory context."""
        if not self._memory:
            # No memory, just regular thinking
            return await self.think(prompt)
        
        # Recall relevant memories
        memories = await self.recall(prompt, limit=5)
        
        # Build context from memories
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant memories:\n"
            for i, result in enumerate(memories, 1):
                entry = result.entry
                memory_context += f"{i}. [{entry.key}]: {entry.value}\n"
        
        # Think with memory context
        enhanced_prompt = f"{prompt}{memory_context}"
        response = await self.think(enhanced_prompt)
        
        # Store this interaction in short-term memory
        await self.remember(
            key=f"thought_{self.name}",
            value={
                "prompt": prompt,
                "response": response,
                "memory_count": len(memories)
            },
            importance=0.6
        )
        
        return response
    
    async def learn_from_feedback(
        self,
        task_id: str,
        feedback: str,
        success: bool,
        importance: float = 0.8
    ):
        """Learn from task feedback and store in memory."""
        # Store feedback in task memory
        await self.remember_task_context(
            task_id=task_id,
            key=f"feedback_{task_id}",
            value={
                "feedback": feedback,
                "success": success,
                "agent": self.name
            },
            importance=importance
        )
        
        # If successful, promote to long-term memory
        if success:
            await self.remember(
                key=f"learned_pattern_{self.name}",
                value={
                    "task_type": task_id.split("_")[0],  # Extract task type
                    "successful_approach": feedback,
                    "agent": self.name
                },
                memory_type=MemoryType.LONG_TERM,
                importance=0.9
            )
