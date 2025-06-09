# Memory API Reference

Complete API documentation for AgentiCraft's memory systems.

## Base Classes

### BaseMemory

Abstract base class for all memory implementations.

```python
class BaseMemory(ABC):
    """Abstract base class for memory implementations.
    
    All memory systems in AgentiCraft inherit from this class,
    providing a consistent interface for storage and retrieval.
    """
    
    @abstractmethod
    async def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store a value in memory.
        
        Args:
            key: Unique identifier for the memory
            value: The value to store
            metadata: Optional metadata dictionary
        """
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The stored value or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from memory.
        
        Args:
            key: The key to delete
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from memory."""
        pass
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        value = await self.retrieve(key)
        return value is not None
```

## Vector Memory

### ChromaDBMemory

```python
class ChromaDBMemory(BaseMemory):
    """Vector memory implementation using ChromaDB.
    
    Provides semantic search capabilities using vector embeddings.
    
    Args:
        collection_name (str): Name of the ChromaDB collection.
            Default: "agenticraft_memory"
        persist_directory (str, optional): Directory for persistence.
            If None, uses in-memory storage.
        embedding_function (callable, optional): Custom embedding function.
            If None, uses default sentence transformer.
        distance_metric (str): Distance metric for similarity.
            Options: "cosine", "l2", "ip". Default: "cosine"
    
    Example:
        memory = ChromaDBMemory(
            collection_name="agent_memory",
            persist_directory="./data/chroma"
        )
        
        await memory.store("key", "value", {"agent": "assistant"})
        results = await memory.search("query text", limit=5)
    """
    
    def __init__(
        self,
        collection_name: str = "agenticraft_memory",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Any] = None,
        distance_metric: str = "cosine"
    ): ...
```

#### Methods

<a id="search-methods"></a>

##### store
```python
async def store(
    self,
    key: str,
    value: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Store a value with its embedding.
    
    Args:
        key: Unique identifier
        value: Value to store (will be converted to string)
        metadata: Optional metadata
        
    Raises:
        ChromaDBError: If storage fails
    """
```

##### retrieve
```python
async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific memory by key.
    
    Args:
        key: The key to retrieve
        
    Returns:
        Dictionary with 'content' and 'metadata' or None
    """
```

##### search
```python
async def search(
    self,
    query: str,
    limit: int = 10,
    filter: Optional[Dict[str, Any]] = None,
    agent_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search for similar memories.
    
    Args:
        query: Search query text
        limit: Maximum results to return
        filter: Metadata filter dictionary
        agent_id: Filter by specific agent
        
    Returns:
        List of results with similarity scores
        
    Example:
        results = await memory.search(
            "machine learning",
            limit=5,
            filter={"category": "research"}
        )
    """
```

##### consolidate_memories
```python
async def consolidate_memories(
    self,
    max_memories: int = 100,
    similarity_threshold: float = 0.9
) -> int:
    """Consolidate similar memories.
    
    Args:
        max_memories: Maximum memories to keep
        similarity_threshold: Threshold for merging
        
    Returns:
        Number of memories consolidated
    """
```

##### share_memories
```python
async def share_memories(
    self,
    source_agent_id: str,
    target_agent_id: str,
    query: Optional[str] = None,
    limit: int = 10
) -> int:
    """Share memories between agents.
    
    Args:
        source_agent_id: Source agent identifier
        target_agent_id: Target agent identifier
        query: Optional filter query
        limit: Maximum memories to share
        
    Returns:
        Number of memories shared
    """
```

##### get_stats
```python
def get_stats(self) -> Dict[str, Any]:
    """Get memory statistics.
    
    Returns:
        Dictionary with stats:
        - total_memories: Total count
        - collection_name: Collection name
        - unique_agents: Number of unique agents
        - distance_metric: Distance metric used
        - persist_directory: Persistence directory
    """
```

### MemoryDocument

```python
class MemoryDocument(BaseModel):
    """Document structure for vector memory.
    
    Attributes:
        id (str): Unique identifier
        content (str): Document content
        metadata (Dict[str, Any]): Metadata
        embedding (List[float], optional): Vector embedding
        timestamp (datetime): Creation timestamp
        agent_id (str, optional): Associated agent
        conversation_id (str, optional): Conversation identifier
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    def to_chroma_format(self) -> Dict[str, Any]:
        """Convert to ChromaDB storage format."""
```

## Knowledge Graph Memory

### KnowledgeGraphMemory

```python
class KnowledgeGraphMemory(BaseMemory):
    """Graph-based memory for entities and relationships.
    
    Automatically extracts entities and relationships from text,
    building a queryable knowledge graph.
    
    Args:
        capacity (int): Maximum number of entities. Default: 10000
        entity_types (List[str], optional): Entity types to extract.
            Default: ["PERSON", "ORGANIZATION", "LOCATION", "DATE",
                     "PRODUCT", "EVENT", "CONCEPT"]
    
    Example:
        graph = KnowledgeGraphMemory(capacity=50000)
        await graph.store("doc1", "John works at OpenAI")
        
        entities = await graph.get_entities()
        relationships = await graph.get_relationships("John")
    """
    
    def __init__(
        self,
        capacity: int = 10000,
        entity_types: Optional[List[str]] = None
    ): ...
```

#### Methods

<a id="graph-operations"></a>

##### store
```python
async def store(
    self,
    key: str,
    value: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Store text and extract entities/relationships.
    
    Args:
        key: Document identifier
        value: Text to process
        metadata: Optional metadata
        
    Note:
        Automatically extracts entities and relationships
        from the provided text.
    """
```

##### extract_entities
```python
def extract_entities(self, text: str) -> List[Dict[str, Any]]:
    """Extract entities from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of entities with structure:
        {
            "name": str,
            "type": str,
            "start": int,  # Start position in text
            "end": int,    # End position in text
            "confidence": float
        }
    """
```

##### add_entity
```python
def add_entity(
    self,
    name: str,
    entity_type: str,
    attributes: Optional[Dict[str, Any]] = None
) -> None:
    """Manually add an entity.
    
    Args:
        name: Entity name
        entity_type: Type (PERSON, ORGANIZATION, etc.)
        attributes: Optional attributes
    """
```

##### get_entities
```python
async def get_entities(
    self,
    entity_type: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get entities from the graph.
    
    Args:
        entity_type: Filter by type
        limit: Maximum results
        
    Returns:
        List of entity dictionaries
    """
```

##### add_relationship
```python
def add_relationship(
    self,
    from_entity: str,
    relation: str,
    to_entity: str,
    attributes: Optional[Dict[str, Any]] = None
) -> None:
    """Add a relationship between entities.
    
    Args:
        from_entity: Source entity name
        relation: Relationship type
        to_entity: Target entity name
        attributes: Optional attributes
        
    Example:
        graph.add_relationship(
            "OpenAI",
            "develops",
            "GPT-4",
            {"year": 2023}
        )
    """
```

##### get_relationships
```python
async def get_relationships(
    self,
    entity_name: str,
    relation_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get relationships for an entity.
    
    Args:
        entity_name: Entity to query
        relation_type: Filter by relation type
        
    Returns:
        List of relationships
    """
```

##### find_paths
```python
def find_paths(
    self,
    start_entity: str,
    end_entity: str,
    max_depth: int = 3
) -> List[List[str]]:
    """Find paths between entities.
    
    Args:
        start_entity: Starting entity
        end_entity: Target entity
        max_depth: Maximum path length
        
    Returns:
        List of paths (each path is a list of alternating
        entities and relationships)
    """
```

##### get_subgraph
```python
def get_subgraph(
    self,
    center_entity: str,
    depth: int = 2,
    include_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Extract subgraph around an entity.
    
    Args:
        center_entity: Central entity
        depth: How many hops to include
        include_types: Entity types to include
        
    Returns:
        Dictionary with 'nodes' and 'edges'
    """
```

##### visualize
```python
def visualize(
    self,
    format: str = "dict"
) -> Union[Dict[str, Any], str]:
    """Generate graph visualization.
    
    Args:
        format: Output format
            - "dict": Python dictionary
            - "cytoscape": Cytoscape.js format
            - "graphviz": DOT format
            
    Returns:
        Visualization in requested format
    """
```

### Entity Classes

```python
class Entity(BaseModel):
    """Entity in the knowledge graph.
    
    Attributes:
        name (str): Entity name
        entity_type (str): Type of entity
        count (int): Occurrence count
        first_seen (datetime): First occurrence
        last_seen (datetime): Last occurrence
        attributes (Dict[str, Any]): Additional attributes
    """
    
    name: str
    entity_type: str
    count: int = 1
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    attributes: Dict[str, Any] = Field(default_factory=dict)
```

```python
class Relationship(BaseModel):
    """Relationship between entities.
    
    Attributes:
        from_entity (str): Source entity
        relation (str): Relationship type
        to_entity (str): Target entity
        confidence (float): Confidence score
        count (int): Occurrence count
        attributes (Dict[str, Any]): Additional attributes
    """
    
    from_entity: str
    relation: str
    to_entity: str
    confidence: float = 1.0
    count: int = 1
    attributes: Dict[str, Any] = Field(default_factory=dict)
```

## Utility Functions

### create_vector_memory

```python
def create_vector_memory(
    collection_name: str = "agenticraft_memory",
    persist_directory: Optional[str] = None,
    **kwargs
) -> ChromaDBMemory:
    """Create a vector memory instance.
    
    Args:
        collection_name: Collection name
        persist_directory: Persistence directory
        **kwargs: Additional ChromaDBMemory arguments
        
    Returns:
        Configured ChromaDBMemory instance
    """
```

### create_knowledge_graph

```python
def create_knowledge_graph(
    capacity: int = 10000,
    **kwargs
) -> KnowledgeGraphMemory:
    """Create a knowledge graph instance.
    
    Args:
        capacity: Maximum entities
        **kwargs: Additional arguments
        
    Returns:
        Configured KnowledgeGraphMemory instance
    """
```

## Constants and Enums

### EntityType

<a id="entity-types"></a>

```python
class EntityType(str, Enum):
    """Standard entity types."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"
    CONCEPT = "CONCEPT"
    CUSTOM = "CUSTOM"
```

### DistanceMetric

```python
class DistanceMetric(str, Enum):
    """Distance metrics for vector similarity."""
    COSINE = "cosine"
    L2 = "l2"
    INNER_PRODUCT = "ip"
```

## Error Handling

### MemoryError

```python
class MemoryError(Exception):
    """Base exception for memory operations."""
    pass
```

### MemoryCapacityError

```python
class MemoryCapacityError(MemoryError):
    """Raised when memory capacity is exceeded."""
    pass
```

### MemoryNotFoundError

```python
class MemoryNotFoundError(MemoryError):
    """Raised when requested memory is not found."""
    pass
```

## Type Definitions

```python
# Type aliases for clarity
MemoryKey = str
MemoryValue = Any
MemoryMetadata = Dict[str, Any]
SimilarityScore = float
EntityName = str
RelationType = str

# Result types
SearchResult = TypedDict('SearchResult', {
    'id': str,
    'content': str,
    'metadata': MemoryMetadata,
    'similarity': SimilarityScore,
    'distance': float
})

EntityResult = TypedDict('EntityResult', {
    'name': str,
    'type': str,
    'count': int,
    'attributes': Dict[str, Any]
})

RelationshipResult = TypedDict('RelationshipResult', {
    'from': EntityName,
    'relation': RelationType,
    'to': EntityName,
    'confidence': float,
    'attributes': Dict[str, Any]
})
```

## Integration Interfaces

### MemoryAgent Protocol

```python
class MemoryAgentProtocol(Protocol):
    """Protocol for agents with memory capabilities."""
    
    @property
    def memory(self) -> BaseMemory:
        """Get the agent's memory system."""
        ...
    
    async def remember(self, key: str, value: Any) -> None:
        """Store in memory."""
        ...
    
    async def recall(self, query: str) -> List[Any]:
        """Recall from memory."""
        ...
```

### MemoryProvider Protocol

```python
class MemoryProvider(Protocol):
    """Protocol for memory providers."""
    
    def create_memory(
        self,
        memory_type: str,
        **kwargs
    ) -> BaseMemory:
        """Create a memory instance."""
        ...
    
    def get_supported_types(self) -> List[str]:
        """Get supported memory types."""
        ...
```

## Next Steps

- [Memory Guide](README.md) - Overview and concepts
- [Vector Memory Guide](vector-memory.md) - Detailed vector memory
- [Knowledge Graph Guide](knowledge-graph.md) - Graph operations
- [Examples](../../examples/memory/) - Working code examples
