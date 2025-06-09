"""Vector memory implementation using ChromaDB.

This module provides vector-based memory storage with:
- Semantic similarity search
- Memory consolidation
- Cross-agent memory sharing
- Efficient retrieval
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import numpy as np

from agenticraft.core.memory import BaseMemory, MemoryEntry, MemoryType

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

from pydantic import BaseModel, Field

from ...core.memory import BaseMemory, MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


class MemoryDocument(BaseModel):
    """A document stored in vector memory."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str | None = None
    conversation_id: str | None = None

    def to_chroma_format(self) -> dict[str, Any]:
        """Convert to ChromaDB format."""
        return {
            "ids": [self.id],
            "documents": [self.content],
            "metadatas": [
                {
                    **self.metadata,
                    "timestamp": self.timestamp.isoformat(),
                    "agent_id": self.agent_id or "",
                    "conversation_id": self.conversation_id or "",
                }
            ],
        }


class ChromaDBMemory(BaseMemory):
    """Vector memory implementation using ChromaDB.

    This memory implementation provides semantic search capabilities
    using vector embeddings, allowing for intelligent memory retrieval
    based on similarity rather than exact matches.

    Args:
        collection_name: Name of the ChromaDB collection
        persist_directory: Directory to persist the database
        embedding_function: Custom embedding function (optional)
        distance_metric: Distance metric for similarity ("cosine", "l2", "ip")

    Example:
        Basic usage::

            memory = ChromaDBMemory(
                collection_name="agent_memory",
                persist_directory="./chroma_db"
            )

            # Store a memory
            await memory.store(
                key="conversation_1",
                value={"role": "user", "content": "Tell me about AI"}
            )

            # Search by similarity
            results = await memory.search(
                query="artificial intelligence",
                limit=5
            )
    """

    def __init__(
        self,
        collection_name: str = "agenticraft_memory",
        persist_directory: str | None = None,
        embedding_function: Any | None = None,
        distance_metric: str = "cosine",
    ):
        """Initialize ChromaDB memory."""
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. " "Install it with: pip install chromadb"
            )

        super().__init__()

        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.distance_metric = distance_metric

        # Initialize ChromaDB client
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
        else:
            self.client = chromadb.Client(
                Settings(anonymized_telemetry=False, is_persistent=False)
            )

        # Setup embedding function
        if embedding_function is None:
            # Use default sentence transformer
            self.embedding_function = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            )
        else:
            self.embedding_function = embedding_function

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": distance_metric},
        )

        logger.info(f"Initialized ChromaDB memory: {collection_name}")

    async def store(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        document_id: str | None = None,
    ) -> str:
        """Store content in vector memory."""
        if not document_id:
            document_id = str(uuid4())

        # Add timestamp
        if metadata is None:
            metadata = {}
        metadata["timestamp"] = datetime.now().isoformat()

        # Generate embedding
        embedding = self._generate_embedding(content)

        # Ensure embedding is a list of floats
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        elif not isinstance(embedding, list):
            embedding = list(embedding)

        # Store in ChromaDB
        self.collection.upsert(
            ids=[document_id],
            documents=[content],
            metadatas=[metadata],
            embeddings=[embedding] if embedding else None,
        )

        return document_id

    async def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """Get n most recent memories."""

        # Get all memories and return the most recent n
        results = self.collection.get(limit=limit, include=["documents", "metadatas"])

        memories = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                memories.append(
                    MemoryEntry(
                        id=results["ids"][i],
                        content=results["documents"][i] if results["documents"] else "",
                        entry_type=MemoryType.KNOWLEDGE,
                        metadata=(
                            results["metadatas"][i] if results["metadatas"] else {}
                        ),
                    )
                )

        return memories

    async def search(
        self,
        query: str,
        n_results: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[MemoryEntry]:
        """Search vector memory by semantic similarity."""

        # Perform semantic search
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=metadata_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to MemoryEntry objects
        memories = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                memories.append(
                    MemoryEntry(
                        id=results["ids"][0][i],
                        content=(
                            results["documents"][0][i] if results["documents"] else ""
                        ),
                        entry_type=MemoryType.KNOWLEDGE,
                        metadata=(
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                    )
                )

        return memories

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        # Use the collection's embedding function
        # This is handled by ChromaDB internally when we pass documents
        return []  # ChromaDB will generate this

    async def clear(self) -> None:
        """Clear all memories."""
        # Get all IDs and delete them
        all_data = self.collection.get()
        if all_data["ids"]:
            self.collection.delete(ids=all_data["ids"])

    async def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        count = self.collection.count()
        return {
            "total_memories": count,
            "collection_name": self.collection_name,
            "distance_metric": self.distance_metric,
        }


def create_vector_memory(
    collection_name: str = "agenticraft_memory",
    persist_directory: str | None = None,
    **kwargs,
) -> ChromaDBMemory:
    """Create a vector memory instance.

    Args:
        collection_name: Name for the collection
        persist_directory: Directory to persist data
        **kwargs: Additional arguments for ChromaDBMemory

    Returns:
        ChromaDBMemory instance
    """
    return ChromaDBMemory(
        collection_name=collection_name, persist_directory=persist_directory, **kwargs
    )
