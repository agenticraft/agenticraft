"""Memory interfaces for AgentiCraft agents.

This module provides the base classes and implementations for agent memory.
AgentiCraft uses a simple two-tier memory system: ConversationMemory for
recent interactions and KnowledgeMemory for persistent facts.

Example:
    Using memory with an agent::

        from agenticraft import Agent, ConversationMemory, KnowledgeMemory

        agent = Agent(
            name="Assistant",
            memory=[
                ConversationMemory(max_entries=10),
                KnowledgeMemory(persist=True)
            ]
        )
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .config import settings
from .types import Message, MessageRole


def compute_embedding(text: str) -> list[float]:
    """Compute embedding for text (placeholder implementation).

    In production, this would use a real embedding model.
    For now, returns a mock embedding based on text length.
    """
    # Mock embedding - in real implementation would use sentence-transformers or similar
    # Create deterministic embedding based on text
    hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    # Generate normalized vector
    embedding = [
        float((hash_val >> (i * 4)) & 0xF) / 15.0
        for i in range(128)  # Standard embedding size
    ]
    # Normalize
    magnitude = sum(x**2 for x in embedding) ** 0.5
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]
    return embedding


class MemoryType(str, Enum):
    """Types of memory."""

    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    EPISODIC = "episodic"


class MemoryEntry(BaseModel):
    """A single entry in memory."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    entry_type: MemoryType = MemoryType.CONVERSATION
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "type": self.entry_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "embedding": self.embedding,
        }


class MemoryItem(BaseModel):
    """A single item in memory."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    accessed_at: datetime = Field(default_factory=datetime.now)
    access_count: int = 0

    def access(self) -> None:
        """Mark this item as accessed."""
        self.accessed_at = datetime.now()
        self.access_count += 1


class BaseMemory(ABC):
    """Base class for memory implementations."""

    def __init__(self, memory_type: str = "base"):
        """Initialize base memory."""
        self.memory_type = memory_type
        self.entries: list[MemoryEntry] = []

    @abstractmethod
    async def store(self, *args, **kwargs) -> str:
        """Store an item in memory."""
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[MemoryEntry]:
        """Search for items in memory."""
        pass

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """Get recent items from memory."""
        pass

    def clear(self) -> None:
        """Clear all items from memory."""
        self.entries.clear()

    async def size(self) -> int:
        """Get the number of items in memory."""
        return len(self.entries)


class ConversationMemory(BaseMemory):
    """Memory for recent conversation history.

    This memory type stores recent messages in a conversation,
    automatically managing the history size.

    Args:
        max_entries: Maximum number of entries to keep
    """

    def __init__(self, max_entries: int | None = None):
        """Initialize conversation memory."""
        super().__init__(memory_type="conversation")
        self.max_entries = max_entries or settings.conversation_memory_size * 2
        self.entries: list[MemoryEntry] = []

    async def store(self, user_message: Message, assistant_message: Message) -> str:
        """Store a conversation turn in memory."""
        # Store user message
        user_entry = MemoryEntry(
            content=f"User: {user_message.content}",
            entry_type=MemoryType.CONVERSATION,
            metadata={"role": "user", "original_message": user_message.model_dump()},
        )
        self.entries.append(user_entry)

        # Store assistant message
        assistant_entry = MemoryEntry(
            content=f"Assistant: {assistant_message.content}",
            entry_type=MemoryType.CONVERSATION,
            metadata={
                "role": "assistant",
                "original_message": assistant_message.model_dump(),
            },
        )
        self.entries.append(assistant_entry)

        # Trim to max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

        return assistant_entry.id

    async def search(self, query: str, max_results: int = 5) -> list[MemoryEntry]:
        """Search conversation history."""
        results = []
        query_lower = query.lower()

        for entry in self.entries:
            if query_lower in entry.content.lower():
                results.append(entry)

        return results[:max_results]

    async def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """Get recent conversation entries."""
        # Return in reverse chronological order (newest first)
        return list(reversed(self.entries[-limit:]))

    def get_messages(self) -> list[Message]:
        """Get all messages in conversation memory."""
        messages = []
        for entry in self.entries:
            if "original_message" in entry.metadata:
                msg_data = entry.metadata["original_message"]
                messages.append(Message(**msg_data))
        return messages


class KnowledgeMemory(BaseMemory):
    """Memory for persistent knowledge and facts.

    This memory type stores long-term knowledge that persists
    across conversations.

    Args:
        use_embeddings: Whether to compute embeddings for entries
        persist: Whether to persist memory to disk
        storage_path: Path to store persistent memory
    """

    def __init__(
        self,
        use_embeddings: bool = False,
        persist: bool = False,
        storage_path: str | None = None,
    ):
        """Initialize knowledge memory."""
        super().__init__(memory_type="knowledge")
        self.use_embeddings = use_embeddings
        self.persist = persist
        self.storage_path = storage_path or "./memory/knowledge.json"
        self.entries: list[MemoryEntry] = []
        self.embeddings = None

        # Load from storage if persisting
        if self.persist:
            self._load()

    async def store(self, *args, **kwargs) -> str:
        """Store knowledge (for compatibility)."""
        if len(args) > 0:
            content = args[0]
        else:
            content = kwargs.get("content", "")
        metadata = kwargs.get("metadata", {})
        return await self.store_knowledge(content, metadata)

    async def store_knowledge(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Store knowledge in memory."""
        entry = MemoryEntry(
            content=content, entry_type=MemoryType.KNOWLEDGE, metadata=metadata or {}
        )

        # Compute embedding if enabled
        if self.use_embeddings:
            entry.embedding = compute_embedding(content)

        self.entries.append(entry)

        # Persist if enabled
        if self.persist:
            self._save()

        return entry.id

    async def search(self, query: str, max_results: int = 5) -> list[MemoryEntry]:
        """Search knowledge entries."""
        # Simple text matching for now
        # TODO: Implement vector similarity search

        matches = []
        query_lower = query.lower()

        for entry in self.entries:
            if query_lower in entry.content.lower():
                matches.append(entry)

        return matches[:max_results]

    async def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """Get recent knowledge entries."""
        return list(reversed(self.entries[-limit:]))

    async def update_knowledge(
        self, entry_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Update an existing knowledge entry."""
        for entry in self.entries:
            if entry.id == entry_id:
                entry.content = content
                if metadata:
                    entry.metadata = metadata
                if self.persist:
                    self._save()
                break

    async def delete_knowledge(self, entry_id: str) -> None:
        """Delete a knowledge entry."""
        self.entries = [e for e in self.entries if e.id != entry_id]
        if self.persist:
            self._save()

    def _load(self) -> None:
        """Load memory from storage."""
        # TODO: Implement persistence
        pass

    def _save(self) -> None:
        """Save memory to storage."""
        # TODO: Implement persistence
        pass


class MemoryStore:
    """Manages multiple memory types for an agent."""

    def __init__(self):
        """Initialize memory store."""
        self.memories: dict[str, BaseMemory] = {}

    def add_memory(self, memory: BaseMemory) -> None:
        """Add a memory implementation."""
        self.memories[memory.memory_type] = memory

    def get_memory(self, memory_type: str) -> BaseMemory | None:
        """Get memory by type."""
        return self.memories.get(memory_type)

    async def store(self, user_message: Message, assistant_message: Message) -> None:
        """Store messages in all appropriate memories."""
        for memory in self.memories.values():
            if isinstance(memory, ConversationMemory):
                await memory.store(user_message, assistant_message)
            elif isinstance(memory, KnowledgeMemory):
                # Extract facts from assistant response
                # TODO: Implement fact extraction
                pass

    async def get_context(self, query: str, max_items: int = 10) -> list[Message]:
        """Get relevant context from all memories."""
        all_items = []

        # First, get recent conversation history
        for memory in self.memories.values():
            if isinstance(memory, ConversationMemory):
                # Get recent entries from conversation memory
                recent_items = await memory.get_recent(limit=max_items // 2)
                # Reverse them back to chronological order for context
                all_items.extend(reversed(recent_items))

        # Then search for relevant items
        for memory in self.memories.values():
            items = await memory.search(query, max_results=max_items // 2)
            all_items.extend(items)

        # Remove duplicates while preserving order
        seen_ids = set()
        unique_items = []
        for item in all_items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_items.append(item)

        # Convert memory entries to messages
        messages = []
        for item in unique_items:
            # Try to reconstruct original message if available
            if "original_message" in item.metadata:
                msg_data = item.metadata["original_message"]
                messages.append(Message(**msg_data))
            else:
                # Create message from entry
                role = MessageRole(item.metadata.get("role", "user"))
                messages.append(
                    Message(role=role, content=item.content, metadata=item.metadata)
                )

        return messages[:max_items]

    def clear(self) -> None:
        """Clear all memories."""
        for memory in self.memories.values():
            memory.clear()
        # Clear the memories dictionary itself
        self.memories.clear()
