"""Tests for ChromaDB vector memory implementation."""

import tempfile

import pytest

from agenticraft.core.memory import MemoryEntry
from agenticraft.memory.vector import CHROMADB_AVAILABLE, ChromaDBMemory

pytestmark = pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")


@pytest.fixture
async def vector_memory():
    """Create a temporary vector memory instance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        memory = ChromaDBMemory(
            collection_name="test_collection", persist_directory=temp_dir
        )
        yield memory
        # Cleanup
        await memory.clear()


@pytest.mark.asyncio
async def test_store_and_search(vector_memory):
    """Test basic store and search operations."""
    # Store simple content
    doc_id1 = await vector_memory.store("Hello, world!")
    assert doc_id1 is not None

    # Store with metadata
    doc_id2 = await vector_memory.store(
        "Python is a programming language",
        metadata={"type": "programming", "user": "Alice"},
    )
    assert doc_id2 is not None

    # Search for content
    results = await vector_memory.search("world", n_results=1)
    assert len(results) > 0
    assert "Hello" in results[0].content

    # Search with metadata filter
    prog_results = await vector_memory.search(
        "programming", n_results=5, metadata_filter={"type": "programming"}
    )
    assert len(prog_results) > 0


@pytest.mark.asyncio
async def test_search_similarity(vector_memory):
    """Test similarity search functionality."""
    # Store related memories
    memories = [
        "Python is a programming language",
        "JavaScript is also a programming language",
        "Cats are cute animals",
        "Dogs are loyal animals",
        "Machine learning uses Python extensively",
    ]

    for content in memories:
        await vector_memory.store(content)

    # Search for programming-related memories
    results = await vector_memory.search("programming languages", n_results=3)

    assert len(results) > 0
    assert len(results) <= 3

    # Top results should be about programming
    top_contents = [r.content for r in results[:2]]
    assert any("programming language" in c for c in top_contents)


@pytest.mark.asyncio
async def test_metadata_filtering(vector_memory):
    """Test metadata storage and filtering."""
    # Store with metadata
    await vector_memory.store(
        "Discussion about quantum computing",
        metadata={
            "agent_id": "ResearchAgent",
            "topic": "quantum",
            "timestamp": "2024-01-01",
        },
    )

    await vector_memory.store(
        "Analysis of machine learning algorithms",
        metadata={
            "agent_id": "AnalysisAgent",
            "topic": "ml",
            "timestamp": "2024-01-02",
        },
    )

    await vector_memory.store(
        "Quantum mechanics principles",
        metadata={
            "agent_id": "ResearchAgent",
            "topic": "quantum",
            "timestamp": "2024-01-03",
        },
    )

    # Search with metadata filter
    research_results = await vector_memory.search(
        "quantum", n_results=5, metadata_filter={"agent_id": "ResearchAgent"}
    )

    assert len(research_results) >= 1
    for result in research_results:
        assert result.metadata.get("agent_id") == "ResearchAgent"


@pytest.mark.asyncio
async def test_get_recent(vector_memory):
    """Test getting recent memories."""
    # Add multiple memories
    for i in range(5):
        await vector_memory.store(f"Memory {i}")

    # Get recent memories
    recent = await vector_memory.get_recent(limit=3)
    assert len(recent) <= 3
    assert all(isinstance(m, MemoryEntry) for m in recent)


@pytest.mark.asyncio
async def test_clear_all(vector_memory):
    """Test clearing all memories."""
    # Add multiple memories
    for i in range(5):
        await vector_memory.store(f"Content {i}")

    # Get count before clear
    stats_before = await vector_memory.get_stats()
    assert stats_before["total_memories"] > 0

    # Clear all
    await vector_memory.clear()

    # Verify empty
    stats_after = await vector_memory.get_stats()
    assert stats_after["total_memories"] == 0


@pytest.mark.asyncio
async def test_memory_stats(vector_memory):
    """Test memory statistics."""
    # Add memories with different metadata
    await vector_memory.store("Memory 1", metadata={"agent_id": "Agent1"})
    await vector_memory.store("Memory 2", metadata={"agent_id": "Agent1"})
    await vector_memory.store("Memory 3", metadata={"agent_id": "Agent2"})

    # Get stats (need to await since it's async)
    stats = await vector_memory.get_stats()

    assert stats["total_memories"] == 3
    assert stats["collection_name"] == "test_collection"
    assert stats["distance_metric"] == "cosine"


@pytest.mark.asyncio
async def test_persistence(vector_memory):
    """Test that memories persist across instances."""
    persist_dir = vector_memory.persist_directory

    # Store a memory
    doc_id = await vector_memory.store("This should persist")

    # Create new instance with same directory
    memory2 = ChromaDBMemory(
        collection_name="test_collection", persist_directory=persist_dir
    )

    # Should be able to search for the memory
    results = await memory2.search("persist", n_results=1)
    assert len(results) > 0
    assert "This should persist" in results[0].content

    # Cleanup
    await memory2.clear()


@pytest.mark.asyncio
async def test_multiple_stores_with_metadata(vector_memory):
    """Test storing multiple items with metadata."""
    # Store multiple items with metadata
    items = [
        ("First item", {"category": "test", "priority": "high"}),
        ("Second item", {"category": "test", "priority": "low"}),
        ("Third item", {"category": "other", "priority": "high"}),
    ]

    doc_ids = []
    for content, metadata in items:
        doc_id = await vector_memory.store(content, metadata=metadata)
        doc_ids.append(doc_id)

    assert len(doc_ids) == 3
    assert all(doc_id is not None for doc_id in doc_ids)

    # Search with different filters
    test_results = await vector_memory.search(
        "item", n_results=10, metadata_filter={"category": "test"}
    )
    assert len(test_results) == 2

    high_priority_results = await vector_memory.search(
        "item", n_results=10, metadata_filter={"priority": "high"}
    )
    assert len(high_priority_results) == 2


@pytest.mark.asyncio
async def test_empty_search(vector_memory):
    """Test searching empty memory."""
    # Search before adding any content
    results = await vector_memory.search("anything", n_results=5)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_store_with_custom_id(vector_memory):
    """Test storing with custom document ID."""
    custom_id = "custom_doc_123"

    # Store with custom ID
    returned_id = await vector_memory.store(
        "Content with custom ID", metadata={"test": True}, document_id=custom_id
    )

    assert returned_id == custom_id

    # Search for it
    results = await vector_memory.search("custom ID", n_results=1)
    assert len(results) > 0
    assert "Content with custom ID" in results[0].content


# Skipping tests for methods that don't exist in ChromaDBMemory
@pytest.mark.skip(reason="retrieve() method not implemented")
async def test_retrieve_method(vector_memory):
    """Test retrieve method - not implemented in ChromaDBMemory."""
    pass


@pytest.mark.skip(reason="consolidate_memories() method not implemented")
async def test_memory_consolidation(vector_memory):
    """Test memory consolidation - not implemented in ChromaDBMemory."""
    pass


@pytest.mark.skip(reason="share_memories() method not implemented")
async def test_memory_sharing(vector_memory):
    """Test memory sharing - not implemented in ChromaDBMemory."""
    pass


@pytest.mark.skip(reason="delete() method not implemented")
async def test_delete_operations(vector_memory):
    """Test delete operations - not implemented in ChromaDBMemory."""
    pass


@pytest.mark.skip(reason="MemoryDocument not used in tests")
async def test_memory_document():
    """Test MemoryDocument model - not needed for basic tests."""
    pass


@pytest.mark.skip(reason="similarity scores not exposed in current implementation")
async def test_similarity_scoring(vector_memory):
    """Test similarity scoring - not exposed in current API."""
    pass
