# Memory Systems Documentation

AgentiCraft provides advanced memory systems that enable agents to store, retrieve, and share information intelligently using both vector embeddings and knowledge graphs.

## Overview

The memory system in AgentiCraft consists of two complementary approaches:

1. **Vector Memory** - Semantic similarity-based storage using ChromaDB
2. **Knowledge Graph** - Entity and relationship-based memory with graph traversal

Both systems extend the `BaseMemory` interface and can be used independently or together for comprehensive memory capabilities.

## Quick Start

### Vector Memory

```python
from agenticraft.memory.vector import ChromaDBMemory

# Create vector memory
memory = ChromaDBMemory(
    collection_name="agent_memory",
    persist_directory="./chroma_db"
)

# Store information
await memory.store(
    key="conv_001",
    value="The user prefers Python for data science projects",
    metadata={"agent_id": "assistant", "topic": "preferences"}
)

# Search by semantic similarity
results = await memory.search(
    query="programming language preferences",
    limit=5
)

# Results include similarity scores
for result in results:
    print(f"Content: {result['content']}")
    print(f"Similarity: {result['similarity']:.2f}")
```

### Knowledge Graph

```python
from agenticraft.memory.graph import KnowledgeGraphMemory

# Create knowledge graph
graph = KnowledgeGraphMemory(capacity=10000)

# Store information with automatic entity extraction
await graph.store(
    key="meeting_notes",
    value="John Smith from Acme Corp discussed the new AI project with Sarah Johnson"
)

# Query the graph
entities = await graph.get_entities(entity_type="PERSON")
relationships = await graph.get_relationships("John Smith")

# Visualize the graph
graph_data = graph.visualize(format="dict")
```

## Core Concepts

### Memory Persistence

Both memory types support persistence:
- **Vector Memory**: Uses ChromaDB's persistent storage
- **Knowledge Graph**: Can be serialized to JSON

### Cross-Agent Sharing

Memories can be shared between agents:

```python
# Share memories between agents
shared_count = await memory.share_memories(
    source_agent_id="researcher",
    target_agent_id="writer",
    query="AI research findings",
    limit=20
)
```

### Memory Consolidation

Vector memory supports automatic consolidation to reduce redundancy:

```python
# Consolidate similar memories
consolidated = await memory.consolidate_memories(
    max_memories=1000,
    similarity_threshold=0.9
)
print(f"Consolidated {consolidated} duplicate memories")
```

## Integration with Agents

### Basic Integration

```python
from agenticraft import Agent
from agenticraft.memory.vector import ChromaDBMemory

# Create agent with memory
agent = Agent(
    name="ResearchAssistant",
    memory=ChromaDBMemory(collection_name="research_memory")
)

# Agent automatically stores conversation history
response = await agent.arun("Tell me about quantum computing")
```

### Advanced Integration

```python
from agenticraft.agents import MemoryAgent
from agenticraft.memory.graph import KnowledgeGraphMemory

# Create specialized memory agent
memory_agent = MemoryAgent(
    name="KnowledgeKeeper",
    vector_memory=ChromaDBMemory(),
    graph_memory=KnowledgeGraphMemory(),
    auto_extract_entities=True
)

# Agent extracts and stores structured knowledge
await memory_agent.arun(
    "Process this research paper and extract key insights"
)
```

## Memory Types Comparison

| Feature | Vector Memory | Knowledge Graph |
|---------|--------------|-----------------|
| **Storage** | Embeddings in vector space | Entities and relationships |
| **Retrieval** | Semantic similarity | Graph traversal |
| **Best For** | Conversational context, documents | Structured information, facts |
| **Query Speed** | Fast (<50ms) | Very fast (<10ms) |
| **Storage Size** | Moderate | Low |
| **Persistence** | ChromaDB files | JSON serialization |

## Configuration

### Vector Memory Configuration

```python
memory = ChromaDBMemory(
    collection_name="agent_memory",     # Collection name
    persist_directory="./chroma_db",    # Persistence directory
    embedding_function=None,            # Custom embeddings (optional)
    distance_metric="cosine"            # Distance metric: cosine, l2, ip
)
```

### Knowledge Graph Configuration

```python
graph = KnowledgeGraphMemory(
    capacity=10000,                     # Maximum nodes
    enable_visualization=True,          # Enable viz support
    entity_types=[                      # Custom entity types
        "PERSON", "ORGANIZATION", 
        "LOCATION", "PRODUCT"
    ]
)
```

## Advanced Features

### Custom Embedding Functions

```python
from sentence_transformers import SentenceTransformer

# Use custom embeddings
model = SentenceTransformer('all-mpnet-base-v2')
memory = ChromaDBMemory(
    embedding_function=model.encode
)
```

### Metadata Filtering

```python
# Store with rich metadata
await memory.store(
    key="doc_001",
    value=document_content,
    metadata={
        "source": "research_paper",
        "date": "2025-06-15",
        "author": "Dr. Smith",
        "confidence": 0.95
    }
)

# Filter by metadata
results = await memory.search(
    query="AI safety",
    filter={"source": "research_paper", "confidence": {"$gte": 0.9}}
)
```

### Graph Queries

```python
# Find paths between entities
paths = graph.find_paths(
    start_entity="John Smith",
    end_entity="AI Project",
    max_depth=3
)

# Get entity statistics
stats = graph.get_entity_stats()
print(f"People: {stats['PERSON']}")
print(f"Organizations: {stats['ORGANIZATION']}")
```

## Performance Optimization

### Vector Memory

1. **Batch Operations**:
   ```python
   # Store multiple memories at once
   memories = [
       {"key": f"mem_{i}", "value": content[i]}
       for i in range(100)
   ]
   await memory.batch_store(memories)
   ```

2. **Index Optimization**:
   ```python
   # Configure HNSW parameters for large datasets
   memory = ChromaDBMemory(
       collection_metadata={
           "hnsw:space": "cosine",
           "hnsw:construction_ef": 200,
           "hnsw:M": 48
       }
   )
   ```

### Knowledge Graph

1. **Capacity Management**:
   ```python
   # Set appropriate capacity
   graph = KnowledgeGraphMemory(capacity=50000)
   
   # Monitor usage
   stats = graph.get_stats()
   if stats["usage"] > 0.8:
       graph.prune(keep_recent=10000)
   ```

2. **Entity Caching**:
   ```python
   # Enable caching for frequent queries
   graph.enable_cache(size=1000)
   ```

## Best Practices

### 1. Choose the Right Memory Type

- Use **Vector Memory** for:
  - Conversation history
  - Document storage
  - Semantic search
  - Similar content retrieval

- Use **Knowledge Graph** for:
  - Fact extraction
  - Relationship mapping
  - Entity tracking
  - Structured queries

### 2. Memory Lifecycle Management

```python
# Regular maintenance
async def maintain_memory(memory):
    # Consolidate similar memories
    await memory.consolidate_memories()
    
    # Get statistics
    stats = memory.get_stats()
    
    # Clean old memories if needed
    if stats["total_memories"] > 10000:
        await memory.prune_old_memories(keep_recent=5000)
```

### 3. Security Considerations

```python
# Use agent-specific collections
agent_memory = ChromaDBMemory(
    collection_name=f"agent_{agent_id}_memory",
    metadata_filters={"access_level": "private"}
)

# Implement access controls
async def get_memory_with_auth(memory, user_id, query):
    # Check permissions
    if not has_permission(user_id, memory.collection_name):
        raise PermissionError("Access denied")
    
    # Filter by access level
    return await memory.search(
        query=query,
        filter={"access_level": {"$lte": get_user_level(user_id)}}
    )
```

## Troubleshooting

### Common Issues

**ChromaDB not installed**:
```bash
pip install chromadb
```

**Embedding model download**:
```python
# First run downloads the model
# Use local model path for offline usage
memory = ChromaDBMemory(
    embedding_model_path="./models/all-MiniLM-L6-v2"
)
```

**Memory persistence**:
```python
# Ensure directory exists and has write permissions
import os
os.makedirs("./chroma_db", exist_ok=True)
```

**Graph visualization**:
```python
# Install optional dependencies
pip install networkx matplotlib
```

## Examples

Complete examples are available in `/examples/memory/`:

- **vector_memory_example.py** - Comprehensive vector memory usage
- **knowledge_graph_example.py** - Knowledge graph operations
- **memory_agent_example.py** - Agent with integrated memory
- **cross_agent_memory.py** - Memory sharing between agents

## API Reference

### Vector Memory API

- [ChromaDBMemory](api-reference.md#chromadbmemory) - Vector memory implementation
- [MemoryDocument](api-reference.md#memorydocument) - Document structure
- [Search Methods](api-reference.md#search-methods) - Query capabilities

### Knowledge Graph API

- [KnowledgeGraphMemory](api-reference.md#knowledgegraphmemory) - Graph memory implementation
- [Entity Types](api-reference.md#entity-types) - Supported entities
- [Graph Operations](api-reference.md#graph-operations) - Query and traversal

## Next Steps

- [Vector Memory Guide](vector-memory.md) - Deep dive into vector memory
- [Knowledge Graph Guide](knowledge-graph.md) - Advanced graph operations
- [Memory Patterns](patterns.md) - Common memory usage patterns
- [Performance Guide](performance.md) - Optimization techniques
