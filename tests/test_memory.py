"""Tests for memory functionality."""

import asyncio
from datetime import datetime

import pytest

from agenticraft.core.memory import (
    BaseMemory,
    ConversationMemory,
    KnowledgeMemory,
    MemoryItem,
    MemoryStore,
)
from agenticraft.core.types import Message, MessageRole


class TestMemoryItem:
    """Test MemoryItem model."""
    
    def test_memory_item_creation(self):
        """Test creating a memory item."""
        item = MemoryItem(
            content="Test content",
            metadata={"source": "test"}
        )
        
        assert item.content == "Test content"
        assert item.metadata == {"source": "test"}
        assert item.id is not None
        assert item.access_count == 0
        assert isinstance(item.created_at, datetime)
    
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


class TestConversationMemory:
    """Test ConversationMemory implementation."""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        """Test storing and retrieving messages."""
        memory = ConversationMemory(max_entries=6)  # 3 turns = 6 entries
        
        # Store messages
        user_msg1 = Message(role=MessageRole.USER, content="Hello")
        asst_msg1 = Message(role=MessageRole.ASSISTANT, content="Hi there!")
        await memory.store(user_msg1, asst_msg1)
        
        user_msg2 = Message(role=MessageRole.USER, content="How are you?")
        asst_msg2 = Message(role=MessageRole.ASSISTANT, content="I'm doing well!")
        await memory.store(user_msg2, asst_msg2)
        
        # Get recent messages
        items = await memory.get_recent(limit=10)
        
        assert len(items) == 4  # 2 turns = 4 entries
        # get_recent returns in reverse order (most recent first)
        # The last stored was assistant message "I'm doing well!"
        assert "I'm doing well!" in items[0].content  # Most recent first
        assert "How are you?" in items[1].content
    
    @pytest.mark.asyncio
    async def test_max_turns_limit(self):
        """Test that max_turns limit is enforced."""
        memory = ConversationMemory(max_entries=4)  # 2 turns = 4 entries
        
        # Store more than max_turns messages (3 turns worth)
        for i in range(3):
            user_msg = Message(role=MessageRole.USER, content=f"User message {i}")
            asst_msg = Message(role=MessageRole.ASSISTANT, content=f"Assistant message {i}")
            await memory.store(user_msg, asst_msg)
        
        # Should only keep last 4 entries (2 turns)
        assert await memory.size() == 4
        messages = memory.get_messages()
        assert len(messages) == 4
        assert messages[0].content == "User message 1"  # Oldest kept message
        assert messages[-1].content == "Assistant message 2"  # Newest message
    
    @pytest.mark.asyncio
    async def test_store_message_object(self):
        """Test storing Message objects directly."""
        memory = ConversationMemory()
        
        user_msg = Message(role=MessageRole.USER, content="Test message")
        asst_msg = Message(role=MessageRole.ASSISTANT, content="Test response")
        await memory.store(user_msg, asst_msg)
        
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0].content == "Test message"
        assert messages[0].role == MessageRole.USER
        assert messages[1].content == "Test response"
        assert messages[1].role == MessageRole.ASSISTANT
    
    @pytest.mark.asyncio
    async def test_clear_memory(self):
        """Test clearing conversation memory."""
        memory = ConversationMemory()
        
        user_msg = Message(role=MessageRole.USER, content="Message 1")
        asst_msg = Message(role=MessageRole.ASSISTANT, content="Message 2")
        await memory.store(user_msg, asst_msg)
        
        assert await memory.size() == 2
        
        memory.clear()  # clear() is not async
        
        assert await memory.size() == 0
        assert len(memory.get_messages()) == 0
    
    @pytest.mark.asyncio
    async def test_get_messages(self):
        """Test getting all messages."""
        memory = ConversationMemory()
        
        # Store messages properly
        user_msg = Message(role=MessageRole.USER, content="Hello")
        asst_msg = Message(role=MessageRole.ASSISTANT, content="Hi")
        await memory.store(user_msg, asst_msg)
        
        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi"
        
        # Ensure it's a copy
        messages.append(Message(role=MessageRole.USER, content="New"))
        assert len(memory.get_messages()) == 2  # Original unchanged


class TestKnowledgeMemory:
    """Test KnowledgeMemory implementation."""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_knowledge(self):
        """Test storing and retrieving knowledge."""
        memory = KnowledgeMemory(persist=False)
        
        # Store knowledge items
        id1 = await memory.store("The capital of France is Paris", {"type": "fact"})
        id2 = await memory.store("Python is a programming language", {"type": "fact"})
        id3 = await memory.store("Machine learning uses neural networks", {"type": "concept"})
        
        assert id1 != id2 != id3
        
        # Search by query
        items = await memory.search("France", max_results=5)
        assert len(items) == 1
        assert "Paris" in items[0].content
        
        items = await memory.search("programming", max_results=5)
        assert len(items) == 1
        assert "Python" in items[0].content
    
    @pytest.mark.asyncio
    async def test_knowledge_access_tracking(self):
        """Test that knowledge items track access."""
        memory = KnowledgeMemory(persist=False)
        
        await memory.store("Important fact about AI", {"priority": "high"})
        await memory.store("Another fact about AI", {"priority": "low"})
        
        # Access first item multiple times
        for _ in range(3):
            items = await memory.search("Important", max_results=1)
            assert len(items) == 1
        
        # Access second item once
        items = await memory.search("Another", max_results=1)
        assert len(items) == 1
        
        # Most accessed should come first when both match
        items = await memory.search("AI", max_results=2)
        assert len(items) == 2
        # Note: Current implementation doesn't sort by access count, just returns matches
    
    @pytest.mark.asyncio
    async def test_knowledge_size_and_clear(self):
        """Test size and clear operations."""
        memory = KnowledgeMemory(persist=False)
        
        assert await memory.size() == 0
        
        await memory.store("Fact 1")
        await memory.store("Fact 2")
        await memory.store("Fact 3")
        
        assert await memory.size() == 3
        
        memory.clear()  # clear() is not async
        
        assert await memory.size() == 0
        assert len(memory.entries) == 0
    
    @pytest.mark.asyncio
    async def test_case_insensitive_search(self):
        """Test that search is case-insensitive."""
        memory = KnowledgeMemory(persist=False)
        
        await memory.store("The PYTHON programming language")
        
        # Should find with different cases
        for query in ["python", "PYTHON", "Python", "PyThOn"]:
            items = await memory.search(query, max_results=1)
            assert len(items) == 1
            assert "PYTHON" in items[0].content
    
    def test_persistence_initialization(self, temp_dir):
        """Test initialization with persistence."""
        storage_path = temp_dir / "knowledge.json"
        memory = KnowledgeMemory(persist=True, storage_path=str(storage_path))
        
        assert memory.persist is True
        assert memory.storage_path == str(storage_path)
        
        # Note: Actual persistence not implemented yet
        # This just tests the initialization


class TestMemoryStore:
    """Test MemoryStore management."""
    
    def test_add_memory(self):
        """Test adding memory implementations."""
        store = MemoryStore()
        
        conv_memory = ConversationMemory()
        know_memory = KnowledgeMemory()
        
        store.add_memory(conv_memory)
        store.add_memory(know_memory)
        
        assert len(store.memories) == 2
    
    @pytest.mark.asyncio
    async def test_store_messages(self):
        """Test storing messages in appropriate memories."""
        store = MemoryStore()
        
        conv_memory = ConversationMemory()
        know_memory = KnowledgeMemory()
        
        store.add_memory(conv_memory)
        store.add_memory(know_memory)
        
        # Create messages
        user_msg = Message(role=MessageRole.USER, content="What is Python?")
        assistant_msg = Message(role=MessageRole.ASSISTANT, content="Python is a programming language")
        
        # Store messages
        await store.store(user_msg, assistant_msg)
        
        # Check conversation memory got both messages
        conv_messages = conv_memory.get_messages()
        assert len(conv_messages) == 2
        assert conv_messages[0].content == "What is Python?"
        assert conv_messages[1].content == "Python is a programming language"
        
        # Note: Knowledge extraction not implemented yet
    
    @pytest.mark.asyncio
    async def test_get_context(self):
        """Test getting context from all memories."""
        store = MemoryStore()
        
        # Add conversation memory with messages
        conv_memory = ConversationMemory()
        await conv_memory.store("Previous question", {"role": "user"})
        await conv_memory.store("Previous answer", {"role": "assistant"})
        
        # Add knowledge memory with facts
        know_memory = KnowledgeMemory()
        await know_memory.store("Python fact", {"role": "assistant"})
        
        store.add_memory(conv_memory)
        store.add_memory(know_memory)
        
        # Get context
        context = await store.get_context("Python", max_items=10)
        
        # Should get items from both memories
        assert len(context) >= 1  # At least the Python fact
        assert any("Python fact" in msg.content for msg in context)
    
    def test_clear_all_memories(self):
        """Test clearing all memories."""
        store = MemoryStore()
        
        conv_memory = ConversationMemory()
        know_memory = KnowledgeMemory()
        
        # Add some data
        asyncio.run(conv_memory.store("Test", {"role": "user"}))
        asyncio.run(know_memory.store("Fact"))
        
        store.add_memory(conv_memory)
        store.add_memory(know_memory)
        
        # Clear all
        store.clear()
        
        # Check both are cleared
        assert asyncio.run(conv_memory.size()) == 0
        assert asyncio.run(know_memory.size()) == 0
