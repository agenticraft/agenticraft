#!/usr/bin/env python3
"""Vector memory example using ChromaDB (Clean Version).

This example demonstrates:
- Setting up vector memory
- Storing and retrieving memories
- Semantic similarity search
- Memory context for agents

Note: This is a clean version that works without patches.
"""

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryItem:
    """Simple memory item."""

    id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] = None


class SimpleVectorMemory:
    """Simple in-memory vector store for demonstration."""

    def __init__(self, name: str = "demo_memory"):
        self.name = name
        self.memories: dict[str, MemoryItem] = {}
        print(f"✅ Initialized in-memory vector store: {name}")

    async def store(self, content: str, metadata: dict[str, Any] = None) -> str:
        """Store a memory item."""
        memory_id = str(uuid.uuid4())
        self.memories[memory_id] = MemoryItem(
            id=memory_id, content=content, metadata=metadata or {}
        )
        return memory_id

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Simple keyword-based search (real vector memory would use embeddings)."""
        results = []
        query_lower = query.lower()

        for memory in self.memories.values():
            # Simple keyword matching (real implementation would use vector similarity)
            if any(word in memory.content.lower() for word in query_lower.split()):
                similarity = sum(
                    1 for word in query_lower.split() if word in memory.content.lower()
                ) / len(query_lower.split())
                results.append(
                    {
                        "id": memory.id,
                        "content": memory.content,
                        "metadata": memory.metadata,
                        "similarity": similarity,
                    }
                )

        # Sort by similarity and return top results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        return {"total_memories": len(self.memories), "memory_store": self.name}


async def main():
    """Run vector memory examples."""
    print("🧠 AgentiCraft Vector Memory Example (Clean)")
    print("=" * 50)

    # Create vector memory
    memory = SimpleVectorMemory("agent_conversations")

    print("\n📝 Storing memories...")

    # Store some conversations
    conversations = [
        {
            "content": "The user asked about quantum computing. I explained that quantum computers use qubits instead of classical bits, allowing superposition and entanglement.",
            "topic": "quantum computing",
        },
        {
            "content": "We discussed machine learning algorithms. I covered supervised learning, unsupervised learning, and reinforcement learning approaches.",
            "topic": "machine learning",
        },
        {
            "content": "The user inquired about climate change. I provided information about greenhouse gases, global temperature rise, and renewable energy solutions.",
            "topic": "climate change",
        },
        {
            "content": "We explored quantum mechanics principles including wave-particle duality, uncertainty principle, and quantum tunneling effects.",
            "topic": "quantum mechanics",
        },
    ]

    # Store memories
    for i, conv in enumerate(conversations):
        await memory.store(
            content=conv["content"],
            metadata={"topic": conv["topic"], "conversation_id": f"conv_{i}"},
        )
        print(f"   Stored: {conv['topic']}")

    # Test similarity search
    print("\n🔍 Testing similarity search...")

    queries = [
        "Tell me about quantum physics",
        "How does AI learning work?",
        "Environmental issues and solutions",
    ]

    for query in queries:
        print(f"\n   Query: '{query}'")
        results = await memory.search(query, limit=2)

        for result in results:
            print(
                f"   - Match (similarity: {result['similarity']:.2f}): {result['metadata']['topic']}"
            )
            print(f"     Preview: {result['content'][:100]}...")

    # Show final statistics
    print("\n📊 Memory Statistics:")
    final_stats = memory.get_stats()
    for key, value in final_stats.items():
        print(f"   {key}: {value}")

    print("\n✅ Vector memory example complete!")
    print("\n💡 To use real vector memory with ChromaDB:")
    print("   1. Install chromadb: pip install chromadb")
    print("   2. Import from agenticraft.memory import ChromaDBMemory")
    print("   3. The framework will handle vector embeddings automatically")


if __name__ == "__main__":
    asyncio.run(main())
