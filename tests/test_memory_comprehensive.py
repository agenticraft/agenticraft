"""Comprehensive tests for memory module to achieve >95% coverage."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from agenticraft.core.memory import (
    BaseMemory, ConversationMemory, KnowledgeMemory,
    MemoryItem, MemoryStore
)
from agenticraft.core.types import Message, MessageRole


class TestMemoryItem:
    """Test MemoryItem model."""
    
    def test_memory_item_creation(self):
        """Test creating a memory item."""
        item = MemoryItem(
            content="Test content",
            metadata={"key": "value"}
        )
        
        assert item.content == "Test content"
        assert item.metadata == {"key": "value"}
        assert item.access_count == 0
        assert isinstance(item.id, str)
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.accessed_at, datetime)
    
    def test_memory_item_access(self):
        """Test accessing a memory item."""
        item = MemoryItem(content="Test")
        original_time = item.accessed_at
        original_count = item.access_count
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.01)
        
        item.access()
        
        assert item.access_count == original_count + 1
        assert item.accessed_at > original_time
    
    def test_memory_item_multiple_access(self):
        """Test multiple accesses."""
        item = MemoryItem(content="Test")
        
        for i in range(5):
            item.access()
        
        assert item.access_count == 5


class TestConversationMemory:
    """Test ConversationMemory implementation."""
    
    @pytest.fixture
    def conv_memory(self):
        """Create a conversation memory instance."""
        return ConversationMemory(max_turns=3)
    
    @pytest.mark.asyncio
    async def test_store_message_from_metadata(self, conv_memory):
        """Test storing a message from metadata."""
        msg = Message(role=MessageRole.USER, content="Hello")
        
        result = await conv_memory.store(
            "Hello",
            metadata={"message": msg}
        )
        
        assert isinstance(result, str)  # ISO timestamp
        assert await conv_memory.size() == 1
        
        messages = conv_memory.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Hello"
        assert messages[0].role == MessageRole.USER
    
    @pytest.mark.asyncio
    async def test_store_with_role_metadata(self, conv_memory):
        """Test storing with role in metadata."""
        result = await conv_memory.store(
            "Assistant response",
            metadata={"role": MessageRole.ASSISTANT}
        )
        
        messages = conv_memory.get_messages()
        assert len(messages) == 1
        assert messages[0].role == MessageRole.ASSISTANT
        assert messages[0].content == "Assistant response"
    
    @pytest.mark.asyncio
    async def test_store_default_user_message(self, conv_memory):
        """Test storing defaults to user message."""
        await conv_memory.store("Default message")
        
        messages = conv_memory.get_messages()
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Default message"
    
    @pytest.mark.asyncio
    async def test_max_turns_trimming(self, conv_memory):
        """Test that messages are trimmed to max_turns."""
        # max_turns=3 means 6 messages (3 user + 3 assistant)
        for i in range(10):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            await conv_memory.store(
                f"Message {i}",
                metadata={"role": role}
            )
        
        messages = conv_memory.get_messages()
        assert len(messages) == 6  # 3 turns * 2 messages per turn
        
        # Should have kept the last 6 messages
        assert messages[0].content == "Message 4"
        assert messages[-1].content == "Message 9"
    
    @pytest.mark.asyncio
    async def test_retrieve_messages(self, conv_memory):
        """Test retrieving messages as memory items."""
        # Store some messages
        await conv_memory.store("Hello", metadata={"role": MessageRole.USER})
        await conv_memory.store("Hi there", metadata={"role": MessageRole.ASSISTANT})
        await conv_memory.store("How are you?", metadata={"role": MessageRole.USER})
        
        # Retrieve with limit
        items = await conv_memory.retrieve("test query", limit=2)
        
        assert len(items) == 2
        # Should get the most recent messages
        assert items[0].content == "Hi there"
        assert items[1].content == "How are you?"
        
        # Check metadata
        assert items[0].metadata["role"] == "assistant"
        assert items[1].metadata["role"] == "user"
        assert items[0].metadata["query"] == "test query"
    
    @pytest.mark.asyncio
    async def test_clear_memory(self, conv_memory):
        """Test clearing conversation memory."""
        # Add messages
        await conv_memory.store("Message 1")
        await conv_memory.store("Message 2")
        
        assert await conv_memory.size() == 2
        
        await conv_memory.clear()
        
        assert await conv_memory.size() == 0
        assert conv_memory.get_messages() == []
    
    @pytest.mark.asyncio
    async def test_size(self, conv_memory):
        """Test getting memory size."""
        assert await conv_memory.size() == 0
        
        await conv_memory.store("Message 1")
        assert await conv_memory.size() == 1
        
        await conv_memory.store("Message 2")
        assert await conv_memory.size() == 2
    
    def test_get_messages_returns_copy(self, conv_memory):
        """Test that get_messages returns a copy."""
        asyncio.run(conv_memory.store("Test"))
        
        messages1 = conv_memory.get_messages()
        messages2 = conv_memory.get_messages()
        
        # Should be different lists
        assert messages1 is not messages2
        # But same content
        assert messages1 == messages2
    
    def test_default_max_turns_from_settings(self):
        """Test default max_turns from settings."""
        with patch("agenticraft.core.memory.settings.conversation_memory_size", 5):
            memory = ConversationMemory()
            assert memory.max_turns == 5


class TestKnowledgeMemory:
    """Test KnowledgeMemory implementation."""
    
    @pytest.fixture
    def knowledge_memory(self):
        """Create a knowledge memory instance."""
        return KnowledgeMemory(persist=False)
    
    @pytest.fixture
    def persistent_memory(self, tmp_path):
        """Create a persistent knowledge memory."""
        storage_path = str(tmp_path / "knowledge.json")
        return KnowledgeMemory(persist=True, storage_path=storage_path)
    
    @pytest.mark.asyncio
    async def test_store_knowledge(self, knowledge_memory):
        """Test storing knowledge."""
        item_id = await knowledge_memory.store(
            "The capital of France is Paris",
            metadata={"category": "geography"}
        )
        
        assert isinstance(item_id, str)
        assert await knowledge_memory.size() == 1
        
        # Check item was stored
        assert item_id in knowledge_memory._items
        item = knowledge_memory._items[item_id]
        assert item.content == "The capital of France is Paris"
        assert item.metadata == {"category": "geography"}
    
    @pytest.mark.asyncio
    async def test_retrieve_by_query(self, knowledge_memory):
        """Test retrieving knowledge by query."""
        # Store some facts
        await knowledge_memory.store("The capital of France is Paris")
        await knowledge_memory.store("The capital of Germany is Berlin")
        await knowledge_memory.store("France is in Europe")
        await knowledge_memory.store("Tokyo is the capital of Japan")
        
        # Search for France
        results = await knowledge_memory.retrieve("France", limit=2)
        
        assert len(results) == 2
        # Both items mentioning France should be returned
        france_contents = [r.content for r in results]
        assert "The capital of France is Paris" in france_contents
        assert "France is in Europe" in france_contents
    
    @pytest.mark.asyncio
    async def test_retrieve_case_insensitive(self, knowledge_memory):
        """Test retrieval is case insensitive."""
        await knowledge_memory.store("Python is a programming language")
        
        # Different case queries
        results1 = await knowledge_memory.retrieve("python")
        results2 = await knowledge_memory.retrieve("PYTHON")
        results3 = await knowledge_memory.retrieve("Python")
        
        assert len(results1) == len(results2) == len(results3) == 1
        assert results1[0].content == results2[0].content == results3[0].content
    
    @pytest.mark.asyncio
    async def test_retrieve_updates_access(self, knowledge_memory):
        """Test retrieval updates access count."""
        await knowledge_memory.store("Test fact")
        
        # First retrieval
        results = await knowledge_memory.retrieve("test")
        assert results[0].access_count == 1
        
        # Second retrieval
        results = await knowledge_memory.retrieve("test")
        assert results[0].access_count == 2
    
    @pytest.mark.asyncio
    async def test_retrieve_sorted_by_access(self, knowledge_memory):
        """Test results are sorted by access count."""
        # Store items
        id1 = await knowledge_memory.store("Test fact one")
        id2 = await knowledge_memory.store("Test fact two")
        id3 = await knowledge_memory.store("Test fact three")
        
        # Access them different numbers of times
        knowledge_memory._items[id3].access_count = 5
        knowledge_memory._items[id2].access_count = 3
        knowledge_memory._items[id1].access_count = 1
        
        results = await knowledge_memory.retrieve("test")
        
        # Should be sorted by access count (descending)
        assert results[0].content == "Test fact three"
        assert results[1].content == "Test fact two"
        assert results[2].content == "Test fact one"
    
    @pytest.mark.asyncio
    async def test_retrieve_respects_limit(self, knowledge_memory):
        """Test retrieve respects limit parameter."""
        # Store many items
        for i in range(10):
            await knowledge_memory.store(f"Test fact {i}")
        
        results = await knowledge_memory.retrieve("test", limit=3)
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_clear(self, knowledge_memory):
        """Test clearing knowledge memory."""
        # Store items
        await knowledge_memory.store("Fact 1")
        await knowledge_memory.store("Fact 2")
        
        assert await knowledge_memory.size() == 2
        
        await knowledge_memory.clear()
        
        assert await knowledge_memory.size() == 0
        assert knowledge_memory._items == {}
    
    @pytest.mark.asyncio
    async def test_size(self, knowledge_memory):
        """Test getting memory size."""
        assert await knowledge_memory.size() == 0
        
        await knowledge_memory.store("Fact 1")
        assert await knowledge_memory.size() == 1
        
        await knowledge_memory.store("Fact 2")
        assert await knowledge_memory.size() == 2
    
    def test_persistence_initialization(self, tmp_path):
        """Test persistent memory initialization."""
        storage_path = str(tmp_path / "knowledge.json")
        
        # Mock _load method
        with patch.object(KnowledgeMemory, '_load') as mock_load:
            memory = KnowledgeMemory(persist=True, storage_path=storage_path)
            mock_load.assert_called_once()
            assert memory.persist is True
            assert memory.storage_path == storage_path
    
    @pytest.mark.asyncio
    async def test_persistence_on_store(self, tmp_path):
        """Test persistence is triggered on store."""
        storage_path = str(tmp_path / "knowledge.json")
        memory = KnowledgeMemory(persist=True, storage_path=storage_path)
        
        # Mock _save method
        with patch.object(memory, '_save') as mock_save:
            await memory.store("Test fact")
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_persistence_on_clear(self, tmp_path):
        """Test persistence is triggered on clear."""
        storage_path = str(tmp_path / "knowledge.json")
        memory = KnowledgeMemory(persist=True, storage_path=storage_path)
        
        # Add an item first
        await memory.store("Test fact")
        
        # Mock _save method
        with patch.object(memory, '_save') as mock_save:
            await memory.clear()
            mock_save.assert_called_once()
    
    def test_load_not_implemented(self, knowledge_memory):
        """Test _load is not implemented yet."""
        # Should not raise error, just pass
        knowledge_memory._load()
    
    def test_save_not_implemented(self, knowledge_memory):
        """Test _save is not implemented yet."""
        # Should not raise error, just pass
        knowledge_memory._save()


class TestMemoryStore:
    """Test MemoryStore that manages multiple memories."""
    
    @pytest.fixture
    def memory_store(self):
        """Create a memory store."""
        return MemoryStore()
    
    def test_add_memory(self, memory_store):
        """Test adding memory implementations."""
        conv_mem = ConversationMemory()
        know_mem = KnowledgeMemory()
        
        memory_store.add_memory(conv_mem)
        memory_store.add_memory(know_mem)
        
        assert len(memory_store._memories) == 2
        assert conv_mem in memory_store._memories
        assert know_mem in memory_store._memories
    
    @pytest.mark.asyncio
    async def test_store_messages_in_conversation_memory(self, memory_store):
        """Test storing messages in conversation memory."""
        conv_mem = ConversationMemory()
        memory_store.add_memory(conv_mem)
        
        user_msg = Message(role=MessageRole.USER, content="Hello")
        assistant_msg = Message(role=MessageRole.ASSISTANT, content="Hi there")
        
        await memory_store.store(user_msg, assistant_msg)
        
        # Check both messages were stored
        messages = conv_mem.get_messages()
        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there"
    
    @pytest.mark.asyncio
    async def test_store_skips_knowledge_memory(self, memory_store):
        """Test store skips knowledge memory (not implemented)."""
        know_mem = KnowledgeMemory()
        memory_store.add_memory(know_mem)
        
        user_msg = Message(role=MessageRole.USER, content="Hello")
        assistant_msg = Message(role=MessageRole.ASSISTANT, content="Hi there")
        
        await memory_store.store(user_msg, assistant_msg)
        
        # Knowledge memory should remain empty
        assert await know_mem.size() == 0
    
    @pytest.mark.asyncio
    async def test_get_context_from_all_memories(self, memory_store):
        """Test getting context from all memories."""
        # Set up memories
        conv_mem = ConversationMemory()
        know_mem = KnowledgeMemory()
        memory_store.add_memory(conv_mem)
        memory_store.add_memory(know_mem)
        
        # Add to conversation memory
        await conv_mem.store("User message", metadata={"role": MessageRole.USER})
        await conv_mem.store("Assistant message", metadata={"role": MessageRole.ASSISTANT})
        
        # Add to knowledge memory
        await know_mem.store("Fact about query topic")
        
        # Get context
        context = await memory_store.get_context("query", max_items=10)
        
        assert len(context) == 3
        # Should be sorted by creation time
        assert all(isinstance(msg, Message) for msg in context)
    
    @pytest.mark.asyncio
    async def test_get_context_respects_max_items(self, memory_store):
        """Test get_context respects max_items limit."""
        conv_mem = ConversationMemory()
        memory_store.add_memory(conv_mem)
        
        # Add many messages
        for i in range(10):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            await conv_mem.store(f"Message {i}", metadata={"role": role})
        
        # Get limited context
        context = await memory_store.get_context("test", max_items=3)
        
        assert len(context) == 3
    
    @pytest.mark.asyncio
    async def test_get_context_converts_memory_items(self, memory_store):
        """Test get_context converts MemoryItems to Messages."""
        know_mem = KnowledgeMemory()
        memory_store.add_memory(know_mem)
        
        # Store knowledge with metadata
        await know_mem.store(
            "Test fact",
            metadata={"role": "assistant", "source": "test"}
        )
        
        context = await memory_store.get_context("test")
        
        assert len(context) == 1
        assert isinstance(context[0], Message)
        assert context[0].role == MessageRole.ASSISTANT
        assert context[0].content == "Test fact"
        assert context[0].metadata["source"] == "test"
    
    def test_clear_all_memories(self, memory_store):
        """Test clearing all memories."""
        conv_mem = ConversationMemory()
        know_mem = KnowledgeMemory()
        memory_store.add_memory(conv_mem)
        memory_store.add_memory(know_mem)
        
        # Add some data
        asyncio.run(conv_mem.store("Message"))
        asyncio.run(know_mem.store("Fact"))
        
        # Clear all
        memory_store.clear()
        
        # Check all are empty
        assert asyncio.run(conv_mem.size()) == 0
        assert asyncio.run(know_mem.size()) == 0


class TestBaseMemoryAbstract:
    """Test that BaseMemory is properly abstract."""
    
    def test_cannot_instantiate_base_memory(self):
        """Test BaseMemory cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseMemory()
    
    def test_subclass_must_implement_methods(self):
        """Test subclass must implement all abstract methods."""
        class IncompleteMemory(BaseMemory):
            pass
        
        with pytest.raises(TypeError):
            IncompleteMemory()
    
    @pytest.mark.asyncio
    async def test_complete_implementation(self):
        """Test a complete implementation works."""
        class CompleteMemory(BaseMemory):
            async def store(self, content: str, metadata=None) -> str:
                return "id"
            
            async def retrieve(self, query: str, limit: int = 5):
                return []
            
            async def clear(self) -> None:
                pass
            
            async def size(self) -> int:
                return 0
        
        # Should work
        memory = CompleteMemory()
        assert await memory.store("test") == "id"
        assert await memory.retrieve("test") == []
        assert await memory.size() == 0
        await memory.clear()  # Should not raise
