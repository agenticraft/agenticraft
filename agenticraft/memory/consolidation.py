"""Consolidated memory system for AgentiCraft.

Simplified implementation focusing on practical memory management
for multi-agent workflows.
"""

import asyncio
import json
import os
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import logging

from . import MemoryEntry, MemoryQuery, MemorySearchResult, MemoryStore, MemoryType

logger = logging.getLogger(__name__)


class ShortTermMemory(MemoryStore):
    """Short-term memory with sliding window (last N interactions)."""
    
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.memories: deque = deque(maxlen=capacity)
        self._index: Dict[str, MemoryEntry] = {}
    
    async def store(self, entry: MemoryEntry) -> str:
        """Store in short-term memory."""
        entry_id = entry.generate_id()
        
        # If at capacity, oldest will be automatically removed by deque
        if len(self.memories) == self.capacity and self.memories:
            oldest = self.memories[0]
            old_id = oldest.generate_id()
            self._index.pop(old_id, None)
        
        self.memories.append(entry)
        self._index[entry_id] = entry
        
        logger.debug(f"Stored in short-term memory: {entry.key}")
        return entry_id
    
    async def retrieve(self, query: MemoryQuery) -> List[MemorySearchResult]:
        """Retrieve from short-term memory."""
        results = []
        
        for entry in self.memories:
            if query.matches(entry):
                # Recent memories get higher relevance
                recency_score = 1.0 - (len(self.memories) - self.memories.index(entry)) / len(self.memories)
                results.append(MemorySearchResult(entry, recency_score))
        
        # Sort by relevance and limit
        results.sort(reverse=True)
        return results[:query.limit]
    
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        if entry_id in self._index:
            entry = self._index[entry_id]
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            return True
        return False
    
    async def delete(self, entry_id: str) -> bool:
        """Delete from short-term memory."""
        if entry_id in self._index:
            entry = self._index.pop(entry_id)
            self.memories.remove(entry)
            return True
        return False
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear short-term memories."""
        if memory_type and memory_type != MemoryType.SHORT_TERM:
            return 0
        
        count = len(self.memories)
        self.memories.clear()
        self._index.clear()
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get short-term memory statistics."""
        return {
            "type": "short_term",
            "count": len(self.memories),
            "capacity": self.capacity,
            "utilization": len(self.memories) / self.capacity if self.capacity > 0 else 0
        }


class LongTermMemory(MemoryStore):
    """Long-term memory with consolidated insights and knowledge."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".agenticraft" / "memory"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.memories: Dict[str, MemoryEntry] = {}
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load memories from disk."""
        memory_file = self.storage_path / "long_term.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                    for entry_data in data.get("memories", []):
                        entry = MemoryEntry.from_dict(entry_data)
                        self.memories[entry.generate_id()] = entry
                logger.info(f"Loaded {len(self.memories)} long-term memories")
            except Exception as e:
                logger.error(f"Failed to load long-term memories: {e}")
    
    def _save_to_disk(self):
        """Save memories to disk."""
        memory_file = self.storage_path / "long_term.json"
        try:
            data = {
                "memories": [entry.to_dict() for entry in self.memories.values()],
                "saved_at": datetime.utcnow().isoformat()
            }
            with open(memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save long-term memories: {e}")
    
    async def store(self, entry: MemoryEntry) -> str:
        """Store in long-term memory."""
        entry_id = entry.generate_id()
        
        # Check for similar existing memories to merge
        similar = await self._find_similar(entry)
        if similar:
            # Merge with existing memory
            existing_id, existing = similar[0]
            existing.access_count += 1
            existing.importance = max(existing.importance, entry.importance)
            existing.metadata.update(entry.metadata)
            logger.debug(f"Merged with existing long-term memory: {existing.key}")
            self._save_to_disk()
            return existing_id
        
        # Store new memory
        self.memories[entry_id] = entry
        logger.debug(f"Stored in long-term memory: {entry.key}")
        self._save_to_disk()
        return entry_id
    
    async def retrieve(self, query: MemoryQuery) -> List[MemorySearchResult]:
        """Retrieve from long-term memory."""
        results = []
        
        for entry_id, entry in self.memories.items():
            if query.matches(entry):
                # Calculate relevance based on importance and access count
                relevance = entry.importance * 0.7 + min(entry.access_count / 10, 1.0) * 0.3
                results.append(MemorySearchResult(entry, relevance))
                
                # Update access count
                entry.access_count += 1
        
        # Sort by relevance and limit
        results.sort(reverse=True)
        
        if results:
            self._save_to_disk()  # Save updated access counts
        
        return results[:query.limit]
    
    async def _find_similar(self, entry: MemoryEntry, threshold: float = 0.8) -> List[Tuple[str, MemoryEntry]]:
        """Find similar memories for deduplication."""
        similar = []
        
        for entry_id, existing in self.memories.items():
            if existing.key == entry.key and existing.memory_type == entry.memory_type:
                # Simple similarity check based on key and type
                similar.append((entry_id, existing))
        
        return similar
    
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        if entry_id in self.memories:
            entry = self.memories[entry_id]
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            self._save_to_disk()
            return True
        return False
    
    async def delete(self, entry_id: str) -> bool:
        """Delete from long-term memory."""
        if entry_id in self.memories:
            del self.memories[entry_id]
            self._save_to_disk()
            return True
        return False
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear long-term memories."""
        if memory_type and memory_type != MemoryType.LONG_TERM:
            return 0
        
        count = len(self.memories)
        self.memories.clear()
        self._save_to_disk()
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get long-term memory statistics."""
        total_access = sum(m.access_count for m in self.memories.values())
        avg_importance = sum(m.importance for m in self.memories.values()) / len(self.memories) if self.memories else 0
        
        return {
            "type": "long_term",
            "count": len(self.memories),
            "total_access_count": total_access,
            "average_importance": avg_importance,
            "storage_path": str(self.storage_path)
        }


class TaskMemory(MemoryStore):
    """Task-specific memory for workflow context."""
    
    def __init__(self, max_tasks: int = 10, max_per_task: int = 50):
        self.max_tasks = max_tasks
        self.max_per_task = max_per_task
        self.task_memories: Dict[str, Dict[str, MemoryEntry]] = {}
        self.task_order: deque = deque(maxlen=max_tasks)
    
    async def store(self, entry: MemoryEntry) -> str:
        """Store in task memory."""
        task_id = entry.metadata.get("task_id", "default")
        entry_id = entry.generate_id()
        
        # Initialize task memory if needed
        if task_id not in self.task_memories:
            # If at capacity, remove oldest task
            if len(self.task_order) == self.max_tasks:
                oldest_task = self.task_order[0]
                del self.task_memories[oldest_task]
            
            self.task_memories[task_id] = {}
            self.task_order.append(task_id)
        
        # Store in task memory with size limit
        task_mem = self.task_memories[task_id]
        if len(task_mem) >= self.max_per_task:
            # Remove oldest entry in this task
            oldest_id = next(iter(task_mem))
            del task_mem[oldest_id]
        
        task_mem[entry_id] = entry
        logger.debug(f"Stored in task memory {task_id}: {entry.key}")
        return entry_id
    
    async def retrieve(self, query: MemoryQuery) -> List[MemorySearchResult]:
        """Retrieve from task memory."""
        results = []
        task_id = query.metadata_filter.get("task_id") if query.metadata_filter else None
        
        if task_id and task_id in self.task_memories:
            # Search specific task
            for entry in self.task_memories[task_id].values():
                if query.matches(entry):
                    results.append(MemorySearchResult(entry, 0.9))  # High relevance for task context
        else:
            # Search all tasks
            for task_memories in self.task_memories.values():
                for entry in task_memories.values():
                    if query.matches(entry):
                        results.append(MemorySearchResult(entry, 0.7))
        
        # Sort by relevance and limit
        results.sort(reverse=True)
        return results[:query.limit]
    
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        for task_memories in self.task_memories.values():
            if entry_id in task_memories:
                entry = task_memories[entry_id]
                for key, value in updates.items():
                    if hasattr(entry, key):
                        setattr(entry, key, value)
                return True
        return False
    
    async def delete(self, entry_id: str) -> bool:
        """Delete from task memory."""
        for task_memories in self.task_memories.values():
            if entry_id in task_memories:
                del task_memories[entry_id]
                return True
        return False
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear task memories."""
        if memory_type and memory_type != MemoryType.TASK:
            return 0
        
        count = sum(len(tm) for tm in self.task_memories.values())
        self.task_memories.clear()
        self.task_order.clear()
        return count
    
    async def clear_task(self, task_id: str) -> int:
        """Clear memories for a specific task."""
        if task_id in self.task_memories:
            count = len(self.task_memories[task_id])
            del self.task_memories[task_id]
            if task_id in self.task_order:
                self.task_order.remove(task_id)
            return count
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get task memory statistics."""
        task_stats = {}
        for task_id, memories in self.task_memories.items():
            task_stats[task_id] = len(memories)
        
        return {
            "type": "task",
            "task_count": len(self.task_memories),
            "total_memories": sum(task_stats.values()),
            "max_tasks": self.max_tasks,
            "max_per_task": self.max_per_task,
            "tasks": task_stats
        }


class ConsolidatedMemory:
    """
    Unified memory system that manages short-term, long-term, and task memories.
    Handles consolidation from short-term to long-term based on importance.
    """
    
    def __init__(
        self,
        short_term_capacity: int = 100,
        consolidation_threshold: float = 0.7,
        storage_path: Optional[Path] = None
    ):
        self.short_term = ShortTermMemory(capacity=short_term_capacity)
        self.long_term = LongTermMemory(storage_path=storage_path)
        self.task = TaskMemory()
        self.consolidation_threshold = consolidation_threshold
        
        # Start background consolidation task
        self._consolidation_task = None
    
    async def start(self):
        """Start the memory system."""
        self._consolidation_task = asyncio.create_task(self._consolidation_loop())
        logger.info("Consolidated memory system started")
    
    async def stop(self):
        """Stop the memory system."""
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass
        logger.info("Consolidated memory system stopped")
    
    async def store(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> str:
        """Store a memory in the appropriate tier."""
        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=memory_type,
            metadata=metadata or {},
            importance=importance
        )
        
        # Route to appropriate memory store
        if memory_type == MemoryType.SHORT_TERM:
            return await self.short_term.store(entry)
        elif memory_type == MemoryType.LONG_TERM:
            return await self.long_term.store(entry)
        elif memory_type == MemoryType.TASK:
            return await self.task.store(entry)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
    
    async def retrieve(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """Retrieve memories from all appropriate tiers."""
        memory_query = MemoryQuery(
            query=query,
            memory_types=memory_types,
            limit=limit,
            min_importance=min_importance,
            metadata_filter=metadata_filter
        )
        
        # Search in all requested memory types
        if not memory_types:
            memory_types = list(MemoryType)
        
        all_results = []
        
        if MemoryType.SHORT_TERM in memory_types:
            all_results.extend(await self.short_term.retrieve(memory_query))
        
        if MemoryType.LONG_TERM in memory_types:
            all_results.extend(await self.long_term.retrieve(memory_query))
        
        if MemoryType.TASK in memory_types:
            all_results.extend(await self.task.retrieve(memory_query))
        
        # Sort all results by relevance and limit
        all_results.sort(reverse=True)
        return all_results[:limit]
    
    async def consolidate(self, force: bool = False) -> Dict[str, int]:
        """Consolidate important short-term memories to long-term."""
        stats = {"promoted": 0, "deleted": 0}
        
        # Get all short-term memories
        all_memories = await self.short_term.retrieve(MemoryQuery(query="", limit=1000))
        
        for result in all_memories:
            entry = result.entry
            
            # Promote high-importance memories to long-term
            if entry.importance >= self.consolidation_threshold or force:
                # Change type and store in long-term
                entry.memory_type = MemoryType.LONG_TERM
                await self.long_term.store(entry)
                
                # Remove from short-term
                await self.short_term.delete(entry.generate_id())
                stats["promoted"] += 1
                
                logger.debug(f"Promoted to long-term: {entry.key}")
            
            # Delete low-importance old memories
            elif entry.importance < 0.3:
                age = datetime.utcnow() - entry.timestamp
                if age > timedelta(hours=1):
                    await self.short_term.delete(entry.generate_id())
                    stats["deleted"] += 1
        
        return stats
    
    async def _consolidation_loop(self):
        """Background task for periodic consolidation."""
        while True:
            try:
                # Wait before next consolidation
                await asyncio.sleep(300)  # 5 minutes
                
                # Run consolidation
                stats = await self.consolidate()
                if stats["promoted"] > 0 or stats["deleted"] > 0:
                    logger.info(f"Memory consolidation: {stats}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in consolidation loop: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        return {
            "short_term": await self.short_term.get_stats(),
            "long_term": await self.long_term.get_stats(),
            "task": await self.task.get_stats(),
            "consolidation_threshold": self.consolidation_threshold
        }
    
    async def clear_all(self) -> Dict[str, int]:
        """Clear all memories."""
        return {
            "short_term": await self.short_term.clear(),
            "long_term": await self.long_term.clear(),
            "task": await self.task.clear()
        }
