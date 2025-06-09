# Memory Examples

This directory contains demonstrations of memory systems in AgentiCraft.

```
📁 memory/
├── vector_memory_demo.py      # Vector memory demonstration
├── knowledge_graph_demo.py    # Knowledge graph demonstration
└── README.md
```

## About These Examples

These examples demonstrate memory concepts using simplified in-memory implementations. They show:

- **Vector Memory**: Semantic similarity search, memory storage and retrieval
- **Knowledge Graph**: Entity relationships, graph queries, structured knowledge

## Running the Examples

```bash
# Vector memory demonstration
python vector_memory_demo.py

# Knowledge graph demonstration  
python knowledge_graph_demo.py
```

## Why Demo Versions?

The AgentiCraft framework's memory classes (`ChromaDBMemory`, `KnowledgeGraphMemory`) currently have unimplemented abstract methods that cause instantiation errors. These demo versions:

1. **Show the concepts** - Demonstrate how memory systems work
2. **Provide working code** - Run without any errors
3. **Offer patterns** - Show how to implement memory functionality

## Real Memory Systems

To use real vector databases or graph databases:

### ChromaDB (Vector Memory)
```python
# When framework is fixed, you'll be able to:
from agenticraft.memory import ChromaDBMemory

memory = ChromaDBMemory(
    collection_name="agent_memory",
    persist_directory="./chroma_db"
)
```

### Neo4j (Knowledge Graph)
```python
# When framework is fixed, you'll be able to:
from agenticraft.memory import Neo4jMemory

memory = Neo4jMemory(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)
```

## Current Workaround

Until the framework classes are fixed, you can:

1. **Use the demo implementations** as a starting point
2. **Integrate directly** with ChromaDB or Neo4j
3. **Create custom memory classes** that don't inherit from the broken base classes

## Memory Patterns

### Vector Memory Pattern
```python
class SimpleVectorMemory:
    def __init__(self):
        self.memories = {}
    
    async def store(self, content: str, metadata: dict = None):
        # Store with embedding (simplified)
        memory_id = str(uuid.uuid4())
        self.memories[memory_id] = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now()
        }
        return memory_id
    
    async def search(self, query: str, limit: int = 5):
        # Simplified keyword search
        # Real implementation would use embeddings
        results = []
        for id, memory in self.memories.items():
            if query.lower() in memory["content"].lower():
                results.append(memory)
        return results[:limit]
```

### Knowledge Graph Pattern
```python
class SimpleKnowledgeGraph:
    def __init__(self):
        self.entities = {}
        self.relationships = []
    
    def add_entity(self, name: str, entity_type: str, **attributes):
        entity_id = f"{entity_type}_{name}"
        self.entities[entity_id] = {
            "name": name,
            "type": entity_type,
            "attributes": attributes
        }
        return entity_id
    
    def add_relationship(self, from_id: str, to_id: str, rel_type: str):
        self.relationships.append({
            "from": from_id,
            "to": to_id,
            "type": rel_type
        })
```

## Next Steps

1. Use these demos to understand memory concepts
2. Implement your own memory solutions as needed
3. Wait for framework fixes to use the official memory classes

The demos provide a solid foundation for understanding how memory systems work in agent applications!