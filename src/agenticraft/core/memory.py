"""Memory system for AgentiCraft"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

import structlog

logger = structlog.get_logger()


@dataclass
class MemoryEntry:
    """Single memory entry"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Memory:
    """Memory system for agents"""
    
    def __init__(self, max_entries: int = 100):
        """Initialize memory
        
        Args:
            max_entries: Maximum number of entries to keep
        """
        self.max_entries = max_entries
        self.entries: List[MemoryEntry] = []
        self._summary: Optional[str] = None
        
        logger.info("memory_initialized", max_entries=max_entries)
    
    def add_message(self, role: str, content: str, **metadata) -> None:
        """Add a message to memory
        
        Args:
            role: Role (user/assistant/system)
            content: Message content
            **metadata: Additional metadata
        """
        entry = MemoryEntry(role=role, content=content, metadata=metadata)
        self.entries.append(entry)
        
        # Trim if exceeds max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
            
        logger.debug("memory_entry_added", role=role, entry_count=len(self.entries))
    
    def get_context(self, num_messages: Optional[int] = None) -> str:
        """Get memory context as string
        
        Args:
            num_messages: Number of recent messages to include
            
        Returns:
            Formatted context string
        """
        messages = self.entries[-num_messages:] if num_messages else self.entries
        
        if not messages:
            return ""
        
        context_parts = []
        for entry in messages:
            context_parts.append(f"{entry.role}: {entry.content}")
        
        return "\n".join(context_parts)
    
    def search(self, query: str) -> List[MemoryEntry]:
        """Search memory for relevant entries
        
        Args:
            query: Search query
            
        Returns:
            List of matching entries
        """
        # Simple keyword search - in production use embeddings
        query_lower = query.lower()
        matches = [
            entry for entry in self.entries
            if query_lower in entry.content.lower()
        ]
        
        logger.debug("memory_search", query=query, matches=len(matches))
        return matches
    
    def clear(self) -> None:
        """Clear all memory entries"""
        self.entries.clear()
        self._summary = None
        logger.info("memory_cleared")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "entries": [
                {
                    "role": entry.role,
                    "content": entry.content,
                    "timestamp": entry.timestamp.isoformat(),
                    "metadata": entry.metadata
                }
                for entry in self.entries
            ],
            "summary": self._summary,
            "total_entries": len(self.entries)
        }
    
    def save(self, path: str) -> None:
        """Save memory to file
        
        Args:
            path: File path
        """
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info("memory_saved", path=path)
    
    def load(self, path: str) -> None:
        """Load memory from file
        
        Args:
            path: File path
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        self.entries = [
            MemoryEntry(
                role=entry["role"],
                content=entry["content"],
                timestamp=datetime.fromisoformat(entry["timestamp"]),
                metadata=entry.get("metadata", {})
            )
            for entry in data["entries"]
        ]
        self._summary = data.get("summary")
        
        logger.info("memory_loaded", path=path, entries=len(self.entries))
