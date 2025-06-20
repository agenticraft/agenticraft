"""Memory system abstractions for AgentiCraft.

Simplified from Agentic Framework to focus on practical memory capabilities
for the hero workflows.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import json
import hashlib


class MemoryType(Enum):
    """Types of memory storage."""
    SHORT_TERM = "short_term"  # Recent interactions
    LONG_TERM = "long_term"    # Consolidated knowledge
    TASK = "task"              # Task-specific context


@dataclass
class MemoryEntry:
    """A single memory entry."""
    key: str
    value: Any
    memory_type: MemoryType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    importance: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key": self.key,
            "value": self.value,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "access_count": self.access_count,
            "importance": self.importance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            access_count=data.get("access_count", 0),
            importance=data.get("importance", 0.5)
        )
    
    def generate_id(self) -> str:
        """Generate a unique ID for this entry."""
        content = f"{self.key}_{self.timestamp.isoformat()}_{self.memory_type.value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class MemoryQuery:
    """Query for retrieving memories."""
    query: str
    memory_types: Optional[List[MemoryType]] = None
    limit: int = 10
    min_importance: float = 0.0
    metadata_filter: Optional[Dict[str, Any]] = None
    
    def matches(self, entry: MemoryEntry) -> bool:
        """Check if an entry matches this query."""
        # Type filter
        if self.memory_types and entry.memory_type not in self.memory_types:
            return False
        
        # Importance filter
        if entry.importance < self.min_importance:
            return False
        
        # Metadata filter
        if self.metadata_filter:
            for key, value in self.metadata_filter.items():
                if entry.metadata.get(key) != value:
                    return False
        
        # Text matching (simple contains for now)
        if self.query:
            entry_text = str(entry.value).lower()
            query_text = self.query.lower()
            if query_text not in entry_text:
                return False
        
        return True


@dataclass
class MemorySearchResult:
    """Result from a memory search."""
    entry: MemoryEntry
    relevance_score: float
    
    def __lt__(self, other):
        """For sorting by relevance."""
        return self.relevance_score < other.relevance_score


class MemoryStore(ABC):
    """Abstract base class for memory storage."""
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns entry ID."""
        pass
    
    @abstractmethod
    async def retrieve(self, query: MemoryQuery) -> List[MemorySearchResult]:
        """Retrieve memories matching the query."""
        pass
    
    @abstractmethod
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        pass
    
    @abstractmethod
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear memories. Returns count of deleted entries."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        pass


# Import key components for easier access
from .consolidation import ConsolidatedMemory, ShortTermMemory, LongTermMemory, TaskMemory
from .agent import MemoryAgent

__all__ = [
    # Core abstractions
    "MemoryType",
    "MemoryEntry",
    "MemoryQuery",
    "MemorySearchResult",
    "MemoryStore",
    # Implementations
    "ConsolidatedMemory",
    "ShortTermMemory",
    "LongTermMemory",
    "TaskMemory",
    # Agent support
    "MemoryAgent",
]
