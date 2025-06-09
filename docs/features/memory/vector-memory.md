# Vector Memory Guide

Comprehensive guide to using ChromaDB-based vector memory in AgentiCraft for semantic storage and retrieval.

## Overview

Vector memory uses embedding models to convert text into high-dimensional vectors, enabling semantic similarity search. This allows agents to find relevant information based on meaning rather than exact keyword matches.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Text Input    │────▶│ Embedding Model  │────▶│  Vector Store   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Retrieved Docs  │◀────│ Similarity Search│◀────│  Query Vector   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Detailed Setup

### Installation

```bash
# Install with vector memory support
pip install agenticraft[vector-memory]

# Or install ChromaDB separately
pip install chromadb sentence-transformers
```

### Basic Configuration

```python
from agenticraft.memory.vector import ChromaDBMemory

# In-memory (temporary)
memory = ChromaDBMemory()

# Persistent storage
memory = ChromaDBMemory(
    collection_name="my_agent_memory",
    persist_directory="./data/chroma"
)

# Custom embedding model
memory = ChromaDBMemory(
    embedding_function=embedding_functions.OpenAIEmbeddingFunction(
        api_key="your-api-key",
        model_name="text-embedding-ada-002"
    )
)
```

## Core Operations

### Storing Memories

```python
# Store simple text
await memory.store(
    key="fact_001",
    value="Paris is the capital of France"
)

# Store with metadata
await memory.store(
    key="conversation_042",
    value="User prefers dark mode and larger fonts",
    metadata={
        "agent_id": "ui_assistant",
        "user_id": "user_123",
        "timestamp": "2025-06-15T10:30:00Z",
        "category": "preferences",
        "confidence": 0.95
    }
)

# Store structured data
conversation = {
    "role": "assistant",
    "content": "I've updated your preferences",
    "context": {"action": "settings_update"}
}
await memory.store(
    key="msg_1234",
    value=conversation,  # Will be JSON serialized
    metadata={"type": "conversation"}
)
```

### Retrieving Memories

```python
# Get by exact key
memory_item = await memory.retrieve("fact_001")
if memory_item:
    print(f"Content: {memory_item['content']}")
    print(f"Metadata: {memory_item['metadata']}")

# Semantic search
results = await memory.search(
    query="What is the capital of France?",
    limit=5
)

for result in results:
    print(f"ID: {result['id']}")
    print(f"Content: {result['content']}")
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Metadata: {result['metadata']}")
    print("-" * 40)
```

### Advanced Search

```python
# Search with metadata filters
results = await memory.search(
    query="user interface preferences",
    limit=10,
    filter={
        "agent_id": "ui_assistant",
        "confidence": {"$gte": 0.8}
    }
)

# Search specific agent's memories
agent_memories = await memory.search(
    query="configuration settings",
    agent_id="config_agent",
    limit=20
)

# Complex filters
results = await memory.search(
    query="error messages",
    filter={
        "$and": [
            {"category": "errors"},
            {"timestamp": {"$gte": "2025-06-01"}},
            {"severity": {"$in": ["high", "critical"]}}
        ]
    }
)
```

## Memory Management

### Consolidation

Reduce redundancy by merging similar memories:

```python
# Automatic consolidation
consolidated_count = await memory.consolidate_memories(
    max_memories=1000,          # Keep at most 1000 memories
    similarity_threshold=0.95   # Merge if >95% similar
)
print(f"Consolidated {consolidated_count} duplicate memories")

# Custom consolidation logic
async def smart_consolidate(memory):
    all_memories = await memory.get_all()
    
    # Group by category
    categories = {}
    for mem in all_memories:
        cat = mem['metadata'].get('category', 'uncategorized')
        categories.setdefault(cat, []).append(mem)
    
    # Consolidate within categories
    for category, mems in categories.items():
        if len(mems) > 100:  # Too many in category
            # Keep only most recent and highest confidence
            sorted_mems = sorted(
                mems,
                key=lambda x: (
                    x['metadata'].get('timestamp', ''),
                    x['metadata'].get('confidence', 0)
                ),
                reverse=True
            )
            
            # Delete older, low-confidence memories
            for mem in sorted_mems[50:]:
                await memory.delete(mem['id'])
```

### Memory Sharing

Share knowledge between agents:

```python
# Share specific memories
shared = await memory.share_memories(
    source_agent_id="researcher",
    target_agent_id="writer",
    query="important findings about AI safety",
    limit=10
)

# Bulk sharing
async def share_category(memory, source_id, target_id, category):
    """Share all memories from a category."""
    source_memories = await memory.search(
        query="",  # Empty query gets all
        filter={
            "agent_id": source_id,
            "category": category
        },
        limit=1000
    )
    
    shared = 0
    for mem in source_memories:
        new_metadata = mem['metadata'].copy()
        new_metadata['agent_id'] = target_id
        new_metadata['shared_from'] = source_id
        new_metadata['shared_at'] = datetime.now().isoformat()
        
        await memory.store(
            key=f"shared_{mem['id']}_{target_id}",
            value=mem['content'],
            metadata=new_metadata
        )
        shared += 1
    
    return shared
```

## Embedding Strategies

### Default Embeddings

ChromaDB uses `all-MiniLM-L6-v2` by default:
- 384 dimensions
- Good balance of speed and quality
- ~80MB model size

### Alternative Embeddings

```python
# OpenAI embeddings (better quality, requires API key)
from chromadb.utils import embedding_functions

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-openai-api-key",
    model_name="text-embedding-ada-002"  # 1536 dimensions
)

memory = ChromaDBMemory(
    embedding_function=openai_ef
)

# Larger sentence transformer
sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"  # 768 dimensions, better quality
)

# Custom embedding function
class CustomEmbeddings:
    def __init__(self, model):
        self.model = model
    
    def __call__(self, texts):
        # Your embedding logic
        return self.model.encode(texts)

custom_ef = CustomEmbeddings(your_model)
memory = ChromaDBMemory(embedding_function=custom_ef)
```

### Embedding Optimization

```python
# Pre-compute embeddings for batch insert
documents = ["doc1", "doc2", "doc3", ...]
embeddings = memory.embedding_function(documents)

# Batch insert with pre-computed embeddings
memory.collection.add(
    ids=[f"doc_{i}" for i in range(len(documents))],
    documents=documents,
    embeddings=embeddings,
    metadatas=[{"batch": "preprocessed"} for _ in documents]
)
```

## Distance Metrics

### Cosine Distance (Default)

Best for normalized embeddings:

```python
memory = ChromaDBMemory(distance_metric="cosine")
```

- Range: [0, 2] (0 = identical, 2 = opposite)
- Converted to similarity: 1 - distance

### L2 (Euclidean) Distance

Better for embeddings with meaningful magnitudes:

```python
memory = ChromaDBMemory(distance_metric="l2")
```

- Range: [0, ∞)
- Converted to similarity: 1 / (1 + distance)

### Inner Product

For maximizing dot product:

```python
memory = ChromaDBMemory(distance_metric="ip")
```

- Can be negative
- Useful for learned embeddings

## Performance Tuning

### Collection Configuration

```python
# Optimize for large collections
memory = ChromaDBMemory(
    collection_name="optimized_memory",
    collection_metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,  # Higher = better quality, slower build
        "hnsw:M": 48,  # Higher = better quality, more memory
        "hnsw:search_ef": 100,  # Higher = better search quality, slower
        "hnsw:num_threads": 4  # Parallelization
    }
)
```

### Batch Operations

```python
# Batch storage
async def batch_store_memories(memory, documents, batch_size=100):
    """Store documents in batches for efficiency."""
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        ids = [f"doc_{j}" for j in range(i, i + len(batch))]
        values = [doc['content'] for doc in batch]
        metadatas = [doc.get('metadata', {}) for doc in batch]
        
        # ChromaDB handles batching internally
        memory.collection.add(
            ids=ids,
            documents=values,
            metadatas=metadatas
        )
        
        print(f"Stored batch {i//batch_size + 1}")
```

### Query Optimization

```python
# Efficient similarity search
class OptimizedMemory(ChromaDBMemory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}
    
    async def search_with_cache(self, query: str, **kwargs):
        """Cache frequently used queries."""
        cache_key = f"{query}:{str(kwargs)}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        results = await self.search(query, **kwargs)
        self._cache[cache_key] = results
        
        # Limit cache size
        if len(self._cache) > 1000:
            # Remove oldest entries
            oldest = list(self._cache.keys())[:100]
            for key in oldest:
                del self._cache[key]
        
        return results
```

## Use Cases

### Conversation Memory

```python
class ConversationMemory:
    def __init__(self, agent_id: str):
        self.memory = ChromaDBMemory(
            collection_name=f"conversations_{agent_id}"
        )
        self.agent_id = agent_id
    
    async def add_message(self, role: str, content: str, user_id: str):
        """Add a conversation message."""
        message_id = f"msg_{datetime.now().timestamp()}"
        
        await self.memory.store(
            key=message_id,
            value=f"{role}: {content}",
            metadata={
                "role": role,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
        )
    
    async def get_context(self, query: str, user_id: str, limit: int = 5):
        """Get relevant conversation context."""
        return await self.memory.search(
            query=query,
            filter={"user_id": user_id},
            limit=limit
        )
```

### Document Store

```python
class DocumentMemory:
    def __init__(self):
        self.memory = ChromaDBMemory(
            collection_name="documents",
            distance_metric="cosine"
        )
    
    async def index_document(self, doc_path: str, chunk_size: int = 1000):
        """Index a document by chunks."""
        with open(doc_path, 'r') as f:
            content = f.read()
        
        # Simple chunking (use better strategies in production)
        chunks = [
            content[i:i+chunk_size] 
            for i in range(0, len(content), chunk_size - 100)  # Overlap
        ]
        
        for i, chunk in enumerate(chunks):
            await self.memory.store(
                key=f"{doc_path}_chunk_{i}",
                value=chunk,
                metadata={
                    "source": doc_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
    
    async def query_documents(self, query: str, sources: List[str] = None):
        """Query indexed documents."""
        filter_dict = {}
        if sources:
            filter_dict["source"] = {"$in": sources}
        
        return await self.memory.search(
            query=query,
            filter=filter_dict if filter_dict else None,
            limit=10
        )
```

### Knowledge Base

```python
class KnowledgeBase:
    def __init__(self):
        self.memory = ChromaDBMemory(
            collection_name="knowledge_base"
        )
    
    async def add_fact(self, fact: str, source: str, confidence: float = 1.0):
        """Add a fact to the knowledge base."""
        fact_id = hashlib.md5(fact.encode()).hexdigest()
        
        await self.memory.store(
            key=fact_id,
            value=fact,
            metadata={
                "source": source,
                "confidence": confidence,
                "added_at": datetime.now().isoformat(),
                "verified": confidence > 0.9
            }
        )
    
    async def verify_claim(self, claim: str, threshold: float = 0.8):
        """Verify a claim against the knowledge base."""
        results = await self.memory.search(
            query=claim,
            filter={"verified": True},
            limit=5
        )
        
        if not results:
            return {"verified": False, "confidence": 0.0}
        
        # Check if any result strongly supports the claim
        max_similarity = max(r['similarity'] for r in results)
        
        return {
            "verified": max_similarity >= threshold,
            "confidence": max_similarity,
            "supporting_facts": [
                r for r in results if r['similarity'] >= threshold
            ]
        }
```

## Debugging and Monitoring

### Memory Statistics

```python
# Get memory stats
stats = memory.get_stats()
print(f"Total memories: {stats['total_memories']}")
print(f"Collection: {stats['collection_name']}")
print(f"Unique agents: {stats['unique_agents']}")

# Monitor memory growth
async def monitor_memory_growth(memory, interval=60):
    """Monitor memory growth over time."""
    previous_count = 0
    
    while True:
        stats = memory.get_stats()
        current_count = stats['total_memories']
        growth = current_count - previous_count
        
        print(f"Memories: {current_count} (+{growth})")
        print(f"Growth rate: {growth/interval:.2f} memories/second")
        
        previous_count = current_count
        await asyncio.sleep(interval)
```

### Query Analysis

```python
# Analyze query performance
async def analyze_query_performance(memory, test_queries):
    """Analyze search performance."""
    results = []
    
    for query in test_queries:
        start_time = time.time()
        search_results = await memory.search(query, limit=10)
        duration = time.time() - start_time
        
        results.append({
            "query": query,
            "duration_ms": duration * 1000,
            "results_count": len(search_results),
            "avg_similarity": sum(r['similarity'] for r in search_results) / len(search_results) if search_results else 0
        })
    
    # Summary statistics
    avg_duration = sum(r['duration_ms'] for r in results) / len(results)
    print(f"Average query time: {avg_duration:.2f}ms")
    
    return results
```

## Best Practices

### 1. Metadata Design

```python
# Good metadata schema
metadata = {
    # Identifiers
    "id": "unique_id",
    "agent_id": "agent_name",
    "user_id": "user_123",
    
    # Categorization
    "type": "conversation|fact|document",
    "category": "specific_category",
    "tags": ["tag1", "tag2"],
    
    # Temporal
    "created_at": "2025-06-15T10:30:00Z",
    "updated_at": "2025-06-15T10:35:00Z",
    "expires_at": "2025-12-31T23:59:59Z",
    
    # Quality
    "confidence": 0.95,
    "source": "user_input|inference|external",
    "verified": True,
    
    # Access control
    "access_level": "public|private|restricted",
    "owner": "user_123"
}
```

### 2. Memory Hygiene

```python
# Regular cleanup
async def cleanup_old_memories(memory, days=30):
    """Remove memories older than specified days."""
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    all_memories = await memory.get_all()
    deleted = 0
    
    for mem in all_memories:
        created = mem['metadata'].get('created_at', '')
        if created and created < cutoff_date:
            await memory.delete(mem['id'])
            deleted += 1
    
    return deleted
```

### 3. Error Handling

```python
# Robust memory operations
async def safe_store(memory, key, value, metadata=None, max_retries=3):
    """Store with retry logic."""
    for attempt in range(max_retries):
        try:
            await memory.store(key, value, metadata)
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to store memory: {e}")
                return False
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Next Steps

- [Knowledge Graph Guide](knowledge-graph.md) - Graph-based memory
- [Memory Patterns](patterns.md) - Common usage patterns
- [API Reference](api-reference.md) - Complete API documentation
- [Performance Guide](performance.md) - Optimization techniques
