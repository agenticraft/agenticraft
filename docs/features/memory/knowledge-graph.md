# Knowledge Graph Memory Guide

Learn how to use AgentiCraft's knowledge graph memory for storing and querying structured information through entities and relationships.

## Overview

Knowledge graph memory extracts entities and relationships from text, creating a queryable graph structure. This enables agents to understand connections between people, places, organizations, and concepts.

## Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Text Input   │────▶│ Entity Extractor│────▶│   Entities   │
└──────────────┘     └─────────────────┘     └──────────────┘
                              │                      │
                              ▼                      ▼
                     ┌─────────────────┐     ┌──────────────┐
                     │  Relationship   │────▶│    Graph     │
                     │   Detector      │     │   Storage    │
                     └─────────────────┘     └──────────────┘
```

## Basic Usage

### Creating a Knowledge Graph

```python
from agenticraft.memory.graph import KnowledgeGraphMemory

# Create knowledge graph
graph = KnowledgeGraphMemory(
    capacity=10000  # Maximum number of nodes
)

# Store information - entities are extracted automatically
await graph.store(
    key="meeting_001",
    value="John Smith from OpenAI met with Sarah Chen from Microsoft to discuss the GPT-4 integration project."
)

# View extracted entities
entities = await graph.get_entities()
print("Entities found:")
for entity in entities:
    print(f"- {entity['name']} ({entity['type']})")
```

### Entity Types

The system recognizes these entity types by default:

| Type | Description | Examples |
|------|-------------|----------|
| PERSON | People names | John Smith, Dr. Chen |
| ORGANIZATION | Companies, institutions | OpenAI, Microsoft, MIT |
| LOCATION | Places, cities, countries | San Francisco, USA |
| DATE | Temporal references | June 2025, yesterday |
| PRODUCT | Products, technologies | GPT-4, Windows |
| EVENT | Events, occurrences | conference, meeting |
| CONCEPT | Abstract concepts | AI safety, machine learning |

## Entity Extraction

### Automatic Extraction

```python
# Automatic extraction with store
text = """
Dr. Emily Watson from Stanford University published groundbreaking research 
on quantum computing in Nature journal. She collaborated with teams from 
IBM Research in Zurich and Google's quantum AI lab in Santa Barbara.
"""

await graph.store("research_news", text)

# Check extracted entities
people = await graph.get_entities(entity_type="PERSON")
# Returns: [{"name": "Dr. Emily Watson", "type": "PERSON", "count": 1}]

orgs = await graph.get_entities(entity_type="ORGANIZATION")
# Returns: Stanford University, IBM Research, Google, Nature
```

### Manual Entity Addition

```python
# Add entities manually
graph.add_entity(
    name="AGI Summit 2025",
    entity_type="EVENT",
    attributes={
        "date": "2025-09-15",
        "location": "San Francisco",
        "attendees": 5000
    }
)

# Add with relationships
graph.add_entity("Claude", "PRODUCT")
graph.add_entity("Anthropic", "ORGANIZATION")
graph.add_relationship("Anthropic", "develops", "Claude")
```

### Custom Entity Patterns

```python
# Define custom entity patterns
class CustomKnowledgeGraph(KnowledgeGraphMemory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom patterns
        self.entity_patterns.update({
            "PROJECT": r"[A-Z][A-Za-z\s]+ (?:Project|Initiative|Program)",
            "VERSION": r"v?\d+\.\d+(?:\.\d+)?",
            "SKILL": r"(?:Python|JavaScript|machine learning|NLP|computer vision)"
        })
    
    def extract_entities(self, text: str):
        entities = super().extract_entities(text)
        
        # Custom extraction logic
        if "AI" in text or "ML" in text:
            entities.append({
                "name": "Artificial Intelligence",
                "type": "CONCEPT",
                "confidence": 0.9
            })
        
        return entities
```

## Relationships

### Relationship Detection

```python
# Automatic relationship detection
text = "Tim Cook announced that Apple is investing $1 billion in AI research led by John Giannandrea."

await graph.store("news_001", text)

# Query relationships
relationships = await graph.get_relationships("Tim Cook")
# Returns:
# [
#   {"from": "Tim Cook", "relation": "announced", "to": "investment"},
#   {"from": "Tim Cook", "relation": "associated_with", "to": "Apple"}
# ]
```

### Relationship Types

Common relationship types detected:

- **Organizational**: works_for, leads, founded, acquired
- **Personal**: knows, met_with, collaborated_with
- **Location**: located_in, headquartered_in, from
- **Temporal**: happened_on, started_at, ended_at
- **Causal**: caused, resulted_in, led_to

### Custom Relationships

```python
# Add custom relationships
graph.add_relationship(
    from_entity="GPT-4",
    relation="successor_of",
    to_entity="GPT-3.5",
    attributes={
        "improvement": "10x",
        "release_date": "2023-03-14"
    }
)

# Bidirectional relationships
graph.add_relationship("Alice", "collaborates_with", "Bob")
graph.add_relationship("Bob", "collaborates_with", "Alice")

# Weighted relationships
graph.add_relationship(
    "Product A",
    "competes_with",
    "Product B",
    attributes={"intensity": 0.8}
)
```

## Graph Queries

### Basic Queries

```python
# Get all entities
all_entities = await graph.get_entities()

# Filter by type
people = await graph.get_entities(entity_type="PERSON")
companies = await graph.get_entities(entity_type="ORGANIZATION")

# Get specific entity details
entity_info = graph.get_entity("John Smith")
print(f"Occurrences: {entity_info['count']}")
print(f"First seen: {entity_info['first_seen']}")
print(f"Attributes: {entity_info['attributes']}")
```

### Relationship Queries

```python
# Get all relationships for an entity
rels = await graph.get_relationships("OpenAI")

# Get specific relationship types
work_rels = await graph.get_relationships(
    entity_name="Sarah Chen",
    relation_type="works_for"
)

# Get entities connected by relationship
graph.add_relationship("Python", "used_for", "Data Science")
graph.add_relationship("Python", "used_for", "Web Development")

uses = graph.get_entities_by_relationship(
    relation="used_for",
    from_entity="Python"
)
# Returns: ["Data Science", "Web Development"]
```

### Path Finding

```python
# Find paths between entities
paths = graph.find_paths(
    start_entity="John Smith",
    end_entity="Microsoft",
    max_depth=3
)

# Example result:
# [
#   ["John Smith", "works_for", "OpenAI", "partners_with", "Microsoft"],
#   ["John Smith", "collaborates_with", "Sarah Chen", "works_for", "Microsoft"]
# ]

# Find shortest path
shortest = graph.find_shortest_path("Entity A", "Entity B")
```

### Subgraph Extraction

```python
# Get subgraph around an entity
subgraph = graph.get_subgraph(
    center_entity="GPT-4",
    depth=2,  # Two hops from center
    include_types=["PRODUCT", "ORGANIZATION", "PERSON"]
)

# Returns nodes and edges within 2 hops of GPT-4
print(f"Nodes: {len(subgraph['nodes'])}")
print(f"Edges: {len(subgraph['edges'])}")
```

## Visualization

### Dictionary Format

```python
# Get graph as dictionary
graph_dict = graph.visualize(format="dict")

print("Nodes:")
for node in graph_dict["nodes"]:
    print(f"- {node['id']} ({node['type']})")

print("\nEdges:")
for edge in graph_dict["edges"]:
    print(f"- {edge['source']} --{edge['relation']}--> {edge['target']}")
```

### Cytoscape Format

```python
# Export for Cytoscape.js visualization
cytoscape_data = graph.visualize(format="cytoscape")

# Use in web application
html_template = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
<div id="cy" style="width: 800px; height: 600px;"></div>
<script>
var cy = cytoscape({
  container: document.getElementById('cy'),
  elements: %s,
  style: [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'background-color': 'data(color)'
      }
    },
    {
      selector: 'edge',
      style: {
        'label': 'data(relation)',
        'curve-style': 'bezier',
        'target-arrow-shape': 'triangle'
      }
    }
  ]
});
</script>
""" % json.dumps(cytoscape_data)
```

### GraphViz Export

```python
# Export as GraphViz DOT format
dot_graph = graph.visualize(format="graphviz")

# Save to file
with open("knowledge_graph.dot", "w") as f:
    f.write(dot_graph)

# Render with GraphViz
# dot -Tpng knowledge_graph.dot -o knowledge_graph.png
```

### NetworkX Integration

```python
import networkx as nx
import matplotlib.pyplot as plt

# Convert to NetworkX graph
def to_networkx(knowledge_graph):
    G = nx.DiGraph()
    
    # Add nodes
    for entity in knowledge_graph.entities.values():
        G.add_node(
            entity.name,
            type=entity.entity_type,
            count=entity.count
        )
    
    # Add edges
    for rel in knowledge_graph.relationships:
        G.add_edge(
            rel.from_entity,
            rel.to_entity,
            relation=rel.relation
        )
    
    return G

# Visualize
G = to_networkx(graph)
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', 
        node_size=1000, font_size=10, arrows=True)
plt.show()
```

## Advanced Features

### Entity Resolution

```python
# Merge similar entities
class SmartKnowledgeGraph(KnowledgeGraphMemory):
    def resolve_entities(self, threshold=0.8):
        """Merge entities that likely refer to the same thing."""
        from difflib import SequenceMatcher
        
        entities = list(self.entities.values())
        merged = set()
        
        for i, e1 in enumerate(entities):
            if e1.name in merged:
                continue
                
            for j, e2 in enumerate(entities[i+1:], i+1):
                if e2.name in merged:
                    continue
                    
                # Check similarity
                similarity = SequenceMatcher(
                    None, e1.name.lower(), e2.name.lower()
                ).ratio()
                
                if similarity >= threshold:
                    # Merge e2 into e1
                    self.merge_entities(e1.name, e2.name)
                    merged.add(e2.name)
        
        return len(merged)
```

### Temporal Queries

```python
# Add temporal information
graph.add_entity(
    "Product Launch",
    "EVENT",
    attributes={
        "date": "2025-09-01",
        "products": ["ProductX", "ProductY"]
    }
)

# Query by time
async def get_events_in_range(graph, start_date, end_date):
    """Get events within a date range."""
    events = await graph.get_entities(entity_type="EVENT")
    
    in_range = []
    for event in events:
        event_date = event.get("attributes", {}).get("date")
        if event_date and start_date <= event_date <= end_date:
            in_range.append(event)
    
    return in_range
```

### Graph Analytics

```python
# Analyze graph structure
def analyze_graph(graph):
    """Compute graph statistics."""
    stats = {
        "total_entities": len(graph.entities),
        "total_relationships": len(graph.relationships),
        "entities_by_type": {},
        "most_connected": [],
        "isolated_entities": []
    }
    
    # Count by type
    for entity in graph.entities.values():
        stats["entities_by_type"][entity.entity_type] = \
            stats["entities_by_type"].get(entity.entity_type, 0) + 1
    
    # Find most connected
    connection_counts = {}
    for rel in graph.relationships:
        connection_counts[rel.from_entity] = \
            connection_counts.get(rel.from_entity, 0) + 1
        connection_counts[rel.to_entity] = \
            connection_counts.get(rel.to_entity, 0) + 1
    
    # Sort by connections
    sorted_entities = sorted(
        connection_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    stats["most_connected"] = sorted_entities[:10]
    
    # Find isolated entities
    connected = set(connection_counts.keys())
    all_entities = set(graph.entities.keys())
    stats["isolated_entities"] = list(all_entities - connected)
    
    return stats
```

### Knowledge Inference

```python
# Infer new relationships
class InferenceGraph(KnowledgeGraphMemory):
    def infer_relationships(self):
        """Infer implicit relationships."""
        new_relationships = []
        
        # Transitive relationships
        for r1 in self.relationships:
            if r1.relation == "works_for":
                for r2 in self.relationships:
                    if (r2.from_entity == r1.to_entity and 
                        r2.relation == "subsidiary_of"):
                        # Person works for subsidiary of parent company
                        new_rel = (
                            r1.from_entity,
                            "indirectly_works_for",
                            r2.to_entity
                        )
                        new_relationships.append(new_rel)
        
        # Add inferred relationships
        for from_e, rel, to_e in new_relationships:
            self.add_relationship(from_e, rel, to_e)
        
        return len(new_relationships)
```

## Performance Optimization

### Capacity Management

```python
# Monitor and manage capacity
stats = graph.get_stats()
print(f"Entities: {stats['entity_count']}/{stats['capacity']}")
print(f"Usage: {stats['usage']:.1%}")

# Prune old entities when near capacity
if stats['usage'] > 0.9:
    # Remove least recently used
    graph.prune(keep_recent=5000)
    
    # Or remove by criteria
    old_date = datetime.now() - timedelta(days=90)
    graph.prune_before(old_date)
```

### Batch Operations

```python
# Batch entity extraction
texts = [
    "Text 1 with entities...",
    "Text 2 with more entities...",
    # ... many more texts
]

# Process in batches
batch_size = 100
for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    
    # Extract entities from batch
    for j, text in enumerate(batch):
        await graph.store(f"doc_{i+j}", text)
    
    # Consolidate after each batch
    graph.consolidate_entities()
```

### Query Optimization

```python
# Cache frequent queries
class CachedKnowledgeGraph(KnowledgeGraphMemory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._query_cache = {}
        self._cache_size = 1000
    
    async def get_relationships(self, entity_name, relation_type=None):
        # Create cache key
        cache_key = f"{entity_name}:{relation_type}"
        
        # Check cache
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]
        
        # Perform query
        result = await super().get_relationships(entity_name, relation_type)
        
        # Update cache
        self._query_cache[cache_key] = result
        
        # Limit cache size
        if len(self._query_cache) > self._cache_size:
            # Remove oldest entries (simple FIFO)
            oldest = list(self._query_cache.keys())[:-self._cache_size]
            for key in oldest:
                del self._query_cache[key]
        
        return result
```

## Integration Examples

### With Agents

```python
from agenticraft.agents import KnowledgeAgent

# Create agent with knowledge graph
agent = KnowledgeAgent(
    name="KnowledgeBot",
    knowledge_graph=KnowledgeGraphMemory(capacity=50000)
)

# Agent automatically extracts knowledge
response = await agent.arun(
    "Tell me about the meeting between the CEO of OpenAI and Google's AI team"
)

# Query agent's knowledge
knowledge = agent.get_knowledge_about("OpenAI")
```

### With Vector Memory

```python
# Hybrid memory system
class HybridMemory:
    def __init__(self):
        self.vector_memory = ChromaDBMemory()
        self.graph_memory = KnowledgeGraphMemory()
    
    async def store(self, key: str, text: str):
        # Store in both systems
        await self.vector_memory.store(key, text)
        await self.graph_memory.store(key, text)
    
    async def query(self, query: str):
        # Get semantic matches
        semantic_results = await self.vector_memory.search(query)
        
        # Extract entities from query
        query_entities = self.graph_memory.extract_entities(query)
        
        # Get graph context for entities
        graph_context = []
        for entity in query_entities:
            rels = await self.graph_memory.get_relationships(entity['name'])
            graph_context.extend(rels)
        
        return {
            "semantic_matches": semantic_results,
            "graph_context": graph_context
        }
```

## Best Practices

### 1. Entity Naming Consistency

```python
# Standardize entity names
def standardize_entity_name(name: str) -> str:
    """Standardize entity names for consistency."""
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    # Consistent casing for known entities
    known_entities = {
        "openai": "OpenAI",
        "gpt-4": "GPT-4",
        "gpt4": "GPT-4",
        "microsoft": "Microsoft",
        "ms": "Microsoft"
    }
    
    lower_name = name.lower()
    return known_entities.get(lower_name, name)
```

### 2. Relationship Validation

```python
# Validate relationships make sense
VALID_RELATIONS = {
    "PERSON": ["works_for", "knows", "founded", "leads"],
    "ORGANIZATION": ["owns", "acquired", "partners_with", "competes_with"],
    "PRODUCT": ["developed_by", "used_by", "version_of", "integrates_with"]
}

def is_valid_relationship(from_type, relation, to_type):
    """Check if a relationship makes semantic sense."""
    valid_rels = VALID_RELATIONS.get(from_type, [])
    return relation in valid_rels
```

### 3. Regular Maintenance

```python
# Maintenance routine
async def maintain_knowledge_graph(graph):
    """Regular maintenance tasks."""
    # Remove duplicate entities
    graph.deduplicate_entities()
    
    # Merge similar entities
    graph.resolve_entities(threshold=0.85)
    
    # Remove orphaned entities (no relationships)
    graph.remove_orphans()
    
    # Consolidate weak relationships
    graph.consolidate_relationships(min_weight=0.1)
    
    # Update statistics
    stats = graph.get_stats()
    logger.info(f"Graph maintenance complete: {stats}")
```

## Troubleshooting

### Common Issues

**Memory capacity reached**:
```python
# Increase capacity or prune
graph = KnowledgeGraphMemory(capacity=100000)
# Or
graph.prune(keep_recent=50000)
```

**Entity extraction missing entities**:
```python
# Add custom patterns
graph.entity_patterns["CUSTOM_TYPE"] = r"your_pattern_here"

# Or override extraction
class CustomExtractor(KnowledgeGraphMemory):
    def extract_entities(self, text):
        entities = super().extract_entities(text)
        # Add your logic
        return entities
```

**Slow queries**:
```python
# Add indexing for large graphs
graph.build_index()

# Use query limits
results = await graph.get_entities(limit=100)
```

## Next Steps

- [Memory Patterns](patterns.md) - Common usage patterns
- [API Reference](api-reference.md) - Complete API documentation
- [Performance Guide](performance.md) - Optimization techniques
- [Examples](../../examples/memory/) - Working examples
