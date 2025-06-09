# Memory Performance Guide

Optimization techniques and best practices for high-performance memory operations in AgentiCraft.

## Overview

This guide covers:
- Performance benchmarks and expectations
- Optimization strategies for vector and graph memory
- Scaling considerations
- Monitoring and debugging performance issues

## Performance Benchmarks

### Expected Performance Metrics

| Operation | Vector Memory | Knowledge Graph | Target Latency |
|-----------|--------------|-----------------|----------------|
| Store (single) | 5-10ms | 2-5ms | <10ms |
| Retrieve (by key) | 2-5ms | 1-2ms | <5ms |
| Search (semantic) | 20-50ms | N/A | <50ms |
| Graph traversal | N/A | 5-20ms | <20ms |
| Batch store (100) | 50-100ms | 20-50ms | <100ms |
| Memory scan (10k) | 100-200ms | 50-100ms | <200ms |

### Hardware Requirements

```python
# Recommended specifications for different scales

SMALL_SCALE = {
    "memory_items": "< 10,000",
    "ram": "4GB",
    "cpu": "2 cores",
    "storage": "10GB SSD",
    "concurrent_users": "< 10"
}

MEDIUM_SCALE = {
    "memory_items": "10,000 - 100,000",
    "ram": "16GB",
    "cpu": "4-8 cores",
    "storage": "100GB SSD",
    "concurrent_users": "10-100"
}

LARGE_SCALE = {
    "memory_items": "> 100,000",
    "ram": "32GB+",
    "cpu": "8-16 cores",
    "storage": "500GB+ NVMe SSD",
    "concurrent_users": "> 100"
}
```

## Vector Memory Optimization

### ChromaDB Configuration

```python
from agenticraft.memory.vector import ChromaDBMemory
import chromadb

# Optimized configuration for performance
def create_optimized_memory(collection_name: str, scale: str = "medium"):
    """Create optimized vector memory for different scales."""
    
    # HNSW parameters based on scale
    hnsw_configs = {
        "small": {
            "hnsw:space": "cosine",
            "hnsw:construction_ef": 100,  # Lower for faster indexing
            "hnsw:M": 16,  # Fewer connections
            "hnsw:search_ef": 50,  # Faster search
            "hnsw:num_threads": 2
        },
        "medium": {
            "hnsw:space": "cosine",
            "hnsw:construction_ef": 200,  # Balanced
            "hnsw:M": 32,  # Default connections
            "hnsw:search_ef": 100,  # Good accuracy
            "hnsw:num_threads": 4
        },
        "large": {
            "hnsw:space": "cosine",
            "hnsw:construction_ef": 400,  # Better quality
            "hnsw:M": 48,  # More connections
            "hnsw:search_ef": 200,  # Higher accuracy
            "hnsw:num_threads": 8
        }
    }
    
    # Create client with performance settings
    client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            persist_directory="./chroma_db",
            chroma_cache_dir="./chroma_cache"
        )
    )
    
    # Create collection with optimized settings
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata=hnsw_configs.get(scale, hnsw_configs["medium"])
    )
    
    return ChromaDBMemory(
        collection_name=collection_name,
        persist_directory="./chroma_db"
    )
```

### Embedding Optimization

```python
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import torch

class OptimizedEmbeddings:
    """Optimized embedding generation."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = None,
        batch_size: int = 32
    ):
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        self.batch_size = batch_size
        
        # Load model with optimizations
        self.model = SentenceTransformer(model_name)
        self.model.to(device)
        
        # Enable eval mode for inference
        self.model.eval()
        
        # Dimension reduction (optional)
        self.use_pca = False
        self.pca = None
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """Encode texts to embeddings with optimization."""
        if isinstance(texts, str):
            texts = [texts]
        
        # Batch processing
        embeddings = []
        
        with torch.no_grad():  # Disable gradients for inference
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                # Encode batch
                batch_embeddings = self.model.encode(
                    batch,
                    convert_to_numpy=True,
                    normalize_embeddings=normalize,
                    device=self.device
                )
                
                embeddings.append(batch_embeddings)
        
        # Concatenate results
        embeddings = np.vstack(embeddings)
        
        # Apply dimension reduction if enabled
        if self.use_pca and self.pca is not None:
            embeddings = self.pca.transform(embeddings)
        
        return embeddings
    
    def enable_dimension_reduction(self, target_dim: int = 128):
        """Enable PCA dimension reduction."""
        from sklearn.decomposition import PCA
        
        self.use_pca = True
        self.pca = PCA(n_components=target_dim)
        
        # Fit PCA on sample data (in production, use representative data)
        sample_texts = [
            "sample text for PCA fitting",
            "another sample for dimension calculation"
        ]
        sample_embeddings = self.encode(sample_texts, normalize=False)
        self.pca.fit(sample_embeddings)
```

### Search Optimization

```python
class OptimizedVectorSearch:
    """Optimized vector search strategies."""
    
    def __init__(self, memory: ChromaDBMemory):
        self.memory = memory
        self.search_cache = {}
        self.cache_size = 1000
    
    async def cached_search(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> List[Dict]:
        """Search with caching."""
        # Create cache key
        cache_key = f"{query}:{limit}:{str(kwargs)}"
        
        # Check cache
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Perform search
        results = await self.memory.search(query, limit, **kwargs)
        
        # Update cache
        self._update_cache(cache_key, results)
        
        return results
    
    async def approximate_search(
        self,
        query: str,
        limit: int = 10,
        sample_rate: float = 0.1
    ) -> List[Dict]:
        """Approximate search for large collections."""
        # Get collection size
        stats = self.memory.get_stats()
        total_items = stats["total_memories"]
        
        if total_items < 10000:
            # Use exact search for small collections
            return await self.memory.search(query, limit)
        
        # Sample subset for approximate search
        sample_size = int(total_items * sample_rate)
        
        # Perform search on sample
        # In production, implement proper sampling
        results = await self.memory.search(
            query,
            limit=min(limit * 2, sample_size)
        )
        
        return results[:limit]
    
    def _update_cache(self, key: str, value: List[Dict]):
        """Update cache with LRU eviction."""
        if len(self.search_cache) >= self.cache_size:
            # Remove oldest entry
            oldest = next(iter(self.search_cache))
            del self.search_cache[oldest]
        
        self.search_cache[key] = value
```

## Knowledge Graph Optimization

### Graph Structure Optimization

```python
from collections import defaultdict
from typing import Set, Dict, List
import networkx as nx

class OptimizedKnowledgeGraph:
    """Optimized knowledge graph implementation."""
    
    def __init__(self, capacity: int = 100000):
        self.capacity = capacity
        
        # Use efficient data structures
        self.entities = {}  # entity_name -> Entity
        self.entity_index = defaultdict(set)  # entity_type -> Set[entity_names]
        
        # Adjacency list for relationships
        self.forward_edges = defaultdict(list)  # from -> [(relation, to)]
        self.backward_edges = defaultdict(list)  # to -> [(relation, from)]
        
        # Relationship index
        self.relation_index = defaultdict(set)  # relation -> Set[(from, to)]
        
        # Cache for frequent queries
        self.path_cache = {}
        self.subgraph_cache = {}
    
    def add_entity_optimized(
        self,
        name: str,
        entity_type: str,
        attributes: Dict = None
    ):
        """Add entity with indexing."""
        if len(self.entities) >= self.capacity:
            self._evict_lru_entity()
        
        self.entities[name] = {
            "type": entity_type,
            "attributes": attributes or {},
            "access_count": 0,
            "last_access": datetime.now()
        }
        
        # Update index
        self.entity_index[entity_type].add(name)
    
    def add_relationship_optimized(
        self,
        from_entity: str,
        relation: str,
        to_entity: str
    ):
        """Add relationship with dual indexing."""
        # Forward edge
        self.forward_edges[from_entity].append((relation, to_entity))
        
        # Backward edge for reverse lookups
        self.backward_edges[to_entity].append((relation, from_entity))
        
        # Relation index
        self.relation_index[relation].add((from_entity, to_entity))
        
        # Invalidate caches
        self._invalidate_caches(from_entity, to_entity)
    
    def find_paths_optimized(
        self,
        start: str,
        end: str,
        max_depth: int = 3
    ) -> List[List[str]]:
        """Find paths using bidirectional search."""
        # Check cache
        cache_key = f"{start}:{end}:{max_depth}"
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        
        # Bidirectional BFS
        forward_frontier = {start: [[start]]}
        backward_frontier = {end: [[end]]}
        
        for depth in range(max_depth // 2 + 1):
            # Expand smaller frontier
            if len(forward_frontier) <= len(backward_frontier):
                new_forward = self._expand_frontier(
                    forward_frontier,
                    self.forward_edges
                )
                
                # Check for intersection
                paths = self._find_intersections(
                    new_forward,
                    backward_frontier
                )
                
                if paths:
                    self.path_cache[cache_key] = paths
                    return paths
                
                forward_frontier = new_forward
            else:
                new_backward = self._expand_frontier(
                    backward_frontier,
                    self.backward_edges
                )
                
                # Check for intersection
                paths = self._find_intersections(
                    forward_frontier,
                    new_backward,
                    reverse=True
                )
                
                if paths:
                    self.path_cache[cache_key] = paths
                    return paths
                
                backward_frontier = new_backward
        
        return []
    
    def _expand_frontier(
        self,
        frontier: Dict[str, List[List[str]]],
        edges: Dict[str, List]
    ) -> Dict[str, List[List[str]]]:
        """Expand search frontier."""
        new_frontier = {}
        
        for node, paths in frontier.items():
            for relation, neighbor in edges.get(node, []):
                if neighbor not in new_frontier:
                    new_frontier[neighbor] = []
                
                for path in paths:
                    if neighbor not in path:  # Avoid cycles
                        new_path = path + [relation, neighbor]
                        new_frontier[neighbor].append(new_path)
        
        return new_frontier
    
    def _invalidate_caches(self, *entities):
        """Invalidate caches for affected entities."""
        # Clear path cache entries containing these entities
        keys_to_remove = []
        for key in self.path_cache:
            if any(entity in key for entity in entities):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.path_cache[key]
        
        # Clear subgraph cache
        for entity in entities:
            self.subgraph_cache.pop(entity, None)
```

### Query Optimization

```python
class GraphQueryOptimizer:
    """Optimize graph queries."""
    
    def __init__(self, graph: KnowledgeGraphMemory):
        self.graph = graph
        
        # Query statistics
        self.query_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "avg_time": 0
        })
    
    async def optimized_entity_search(
        self,
        entity_type: str = None,
        pattern: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Optimized entity search."""
        start_time = time.time()
        
        if entity_type:
            # Use type index
            candidates = self.graph.entity_index.get(entity_type, set())
        else:
            candidates = set(self.graph.entities.keys())
        
        # Apply pattern filter if provided
        if pattern:
            pattern_lower = pattern.lower()
            candidates = {
                name for name in candidates
                if pattern_lower in name.lower()
            }
        
        # Sort by access count for relevance
        sorted_entities = sorted(
            candidates,
            key=lambda x: self.graph.entities[x]["access_count"],
            reverse=True
        )
        
        # Update statistics
        query_time = time.time() - start_time
        self._update_stats("entity_search", query_time)
        
        return [
            {
                "name": name,
                "type": self.graph.entities[name]["type"],
                "attributes": self.graph.entities[name]["attributes"]
            }
            for name in sorted_entities[:limit]
        ]
    
    async def batch_relationship_query(
        self,
        entity_names: List[str]
    ) -> Dict[str, List[Dict]]:
        """Batch query relationships for multiple entities."""
        results = {}
        
        # Single pass through relationships
        for entity in entity_names:
            forward = self.graph.forward_edges.get(entity, [])
            backward = self.graph.backward_edges.get(entity, [])
            
            results[entity] = {
                "outgoing": [
                    {"relation": rel, "to": to}
                    for rel, to in forward
                ],
                "incoming": [
                    {"relation": rel, "from": from_e}
                    for rel, from_e in backward
                ]
            }
        
        return results
    
    def _update_stats(self, query_type: str, duration: float):
        """Update query statistics."""
        stats = self.query_stats[query_type]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"]
```

## Scaling Strategies

### Horizontal Scaling

```python
class DistributedMemory:
    """Distributed memory across multiple nodes."""
    
    def __init__(self, nodes: List[str]):
        self.nodes = nodes
        self.node_count = len(nodes)
        
        # Consistent hashing for distribution
        self.hash_ring = self._create_hash_ring()
        
        # Connection pool for each node
        self.connections = {
            node: self._create_connection(node)
            for node in nodes
        }
    
    def _get_node_for_key(self, key: str) -> str:
        """Get node responsible for key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        
        # Find node in hash ring
        for node_hash, node in sorted(self.hash_ring.items()):
            if key_hash <= node_hash:
                return node
        
        # Wrap around to first node
        return self.hash_ring[min(self.hash_ring.keys())]
    
    async def store(self, key: str, value: Any, **kwargs):
        """Store in appropriate node."""
        node = self._get_node_for_key(key)
        connection = self.connections[node]
        
        return await connection.store(key, value, **kwargs)
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve from appropriate node."""
        node = self._get_node_for_key(key)
        connection = self.connections[node]
        
        return await connection.retrieve(key)
    
    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Fan-out search across all nodes."""
        # Parallel search on all nodes
        tasks = [
            connection.search(query, limit=limit)
            for connection in self.connections.values()
        ]
        
        all_results = await asyncio.gather(*tasks)
        
        # Merge and sort results
        merged = []
        for results in all_results:
            merged.extend(results)
        
        # Sort by similarity and return top results
        merged.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        return merged[:limit]
    
    def _create_hash_ring(self) -> Dict[str, str]:
        """Create consistent hash ring."""
        ring = {}
        
        for node in self.nodes:
            # Multiple virtual nodes for better distribution
            for i in range(150):
                virtual_node = f"{node}:{i}"
                node_hash = hashlib.md5(virtual_node.encode()).hexdigest()
                ring[node_hash] = node
        
        return ring
```

### Memory Partitioning

```python
class PartitionedMemory:
    """Partition memory by criteria."""
    
    def __init__(self):
        # Partition by time
        self.time_partitions = {
            "hot": ChromaDBMemory("hot_data"),  # Last 24 hours
            "warm": ChromaDBMemory("warm_data"),  # Last week
            "cold": ChromaDBMemory("cold_data")  # Older
        }
        
        # Partition by type
        self.type_partitions = {
            "conversations": ChromaDBMemory("conversations"),
            "facts": ChromaDBMemory("facts"),
            "documents": ChromaDBMemory("documents")
        }
    
    async def store(self, key: str, value: Any, metadata: Dict):
        """Store in appropriate partition."""
        # Time-based partition
        timestamp = metadata.get("timestamp", datetime.now().isoformat())
        partition = self._get_time_partition(timestamp)
        
        await partition.store(key, value, metadata)
        
        # Type-based partition (if applicable)
        data_type = metadata.get("type")
        if data_type in self.type_partitions:
            await self.type_partitions[data_type].store(
                key, value, metadata
            )
    
    async def search(self, query: str, **kwargs) -> List[Dict]:
        """Search across partitions."""
        # Determine which partitions to search
        search_hot = kwargs.get("include_recent", True)
        search_warm = kwargs.get("include_week", True)
        search_cold = kwargs.get("include_old", False)
        
        tasks = []
        if search_hot:
            tasks.append(self.time_partitions["hot"].search(query))
        if search_warm:
            tasks.append(self.time_partitions["warm"].search(query))
        if search_cold:
            tasks.append(self.time_partitions["cold"].search(query))
        
        # Parallel search
        results = await asyncio.gather(*tasks)
        
        # Merge results
        merged = []
        for partition_results in results:
            merged.extend(partition_results)
        
        # Sort by relevance
        merged.sort(key=lambda x: x["similarity"], reverse=True)
        
        return merged[:kwargs.get("limit", 10)]
    
    def _get_time_partition(self, timestamp: str):
        """Determine time partition."""
        ts = datetime.fromisoformat(timestamp)
        age = datetime.now() - ts
        
        if age.days < 1:
            return self.time_partitions["hot"]
        elif age.days < 7:
            return self.time_partitions["warm"]
        else:
            return self.time_partitions["cold"]
    
    async def migrate_partitions(self):
        """Migrate data between partitions."""
        # Move from hot to warm
        hot_data = await self.time_partitions["hot"].search(
            "",  # All data
            limit=10000
        )
        
        for item in hot_data:
            ts = item["metadata"].get("timestamp")
            if ts:
                age = datetime.now() - datetime.fromisoformat(ts)
                if age.days >= 1:
                    # Move to warm
                    await self.time_partitions["warm"].store(
                        item["id"],
                        item["content"],
                        item["metadata"]
                    )
                    await self.time_partitions["hot"].delete(item["id"])
```

## Monitoring and Debugging

### Performance Monitoring

```python
import psutil
from prometheus_client import Counter, Histogram, Gauge

class MemoryPerformanceMonitor:
    """Monitor memory system performance."""
    
    def __init__(self):
        # Metrics
        self.operation_counter = Counter(
            'memory_operations_total',
            'Total memory operations',
            ['operation', 'memory_type']
        )
        
        self.operation_duration = Histogram(
            'memory_operation_duration_seconds',
            'Memory operation duration',
            ['operation', 'memory_type']
        )
        
        self.memory_size = Gauge(
            'memory_items_total',
            'Total items in memory',
            ['memory_type']
        )
        
        self.error_counter = Counter(
            'memory_errors_total',
            'Total memory errors',
            ['operation', 'error_type']
        )
        
        # System metrics
        self.cpu_percent = Gauge('memory_cpu_percent', 'CPU usage')
        self.memory_percent = Gauge('memory_ram_percent', 'RAM usage')
    
    async def monitor_operation(
        self,
        operation: str,
        memory_type: str,
        func,
        *args,
        **kwargs
    ):
        """Monitor a memory operation."""
        start_time = time.time()
        
        try:
            # Execute operation
            result = await func(*args, **kwargs)
            
            # Record success
            self.operation_counter.labels(
                operation=operation,
                memory_type=memory_type
            ).inc()
            
            duration = time.time() - start_time
            self.operation_duration.labels(
                operation=operation,
                memory_type=memory_type
            ).observe(duration)
            
            return result
            
        except Exception as e:
            # Record error
            self.error_counter.labels(
                operation=operation,
                error_type=type(e).__name__
            ).inc()
            raise
        finally:
            # Update system metrics
            self.cpu_percent.set(psutil.cpu_percent())
            self.memory_percent.set(psutil.virtual_memory().percent)
    
    def get_operation_stats(self) -> Dict:
        """Get operation statistics."""
        # This would integrate with Prometheus
        return {
            "operations": {
                "total": self.operation_counter._value.sum(),
                "by_type": self.operation_counter._value
            },
            "performance": {
                "avg_duration": self.operation_duration._sum.value() / 
                               self.operation_duration._count.value()
                if self.operation_duration._count.value() > 0 else 0
            },
            "errors": {
                "total": self.error_counter._value.sum()
            },
            "system": {
                "cpu_percent": self.cpu_percent._value.get(),
                "memory_percent": self.memory_percent._value.get()
            }
        }
```

### Debug Utilities

```python
class MemoryDebugger:
    """Debug utilities for memory systems."""
    
    @staticmethod
    async def analyze_memory_usage(memory: BaseMemory) -> Dict:
        """Analyze memory usage patterns."""
        stats = memory.get_stats()
        
        # Sample queries for analysis
        test_queries = [
            "test query short",
            "this is a longer test query with more words",
            "specific technical query about machine learning"
        ]
        
        query_performance = []
        
        for query in test_queries:
            start = time.time()
            results = await memory.search(query)
            duration = time.time() - start
            
            query_performance.append({
                "query": query,
                "duration_ms": duration * 1000,
                "results": len(results),
                "avg_similarity": sum(r.get("similarity", 0) for r in results) / len(results) if results else 0
            })
        
        return {
            "stats": stats,
            "query_performance": query_performance,
            "recommendations": MemoryDebugger._get_recommendations(stats, query_performance)
        }
    
    @staticmethod
    def _get_recommendations(stats: Dict, performance: List[Dict]) -> List[str]:
        """Get optimization recommendations."""
        recommendations = []
        
        # Check memory size
        if stats.get("total_memories", 0) > 50000:
            recommendations.append(
                "Consider partitioning or archiving old memories"
            )
        
        # Check query performance
        avg_duration = sum(p["duration_ms"] for p in performance) / len(performance)
        if avg_duration > 100:
            recommendations.append(
                "Query performance is slow. Consider indexing optimization"
            )
        
        # Check similarity scores
        avg_similarity = sum(p["avg_similarity"] for p in performance) / len(performance)
        if avg_similarity < 0.5:
            recommendations.append(
                "Low similarity scores. Consider improving embeddings"
            )
        
        return recommendations
    
    @staticmethod
    async def profile_memory_operation(
        memory: BaseMemory,
        operation: str,
        *args,
        **kwargs
    ):
        """Profile a specific operation."""
        import cProfile
        import pstats
        from io import StringIO
        
        profiler = cProfile.Profile()
        
        # Profile operation
        profiler.enable()
        
        try:
            if operation == "store":
                result = await memory.store(*args, **kwargs)
            elif operation == "search":
                result = await memory.search(*args, **kwargs)
            elif operation == "retrieve":
                result = await memory.retrieve(*args, **kwargs)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        finally:
            profiler.disable()
        
        # Get profile results
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions
        
        return {
            "result": result,
            "profile": stream.getvalue()
        }
```

## Best Practices Summary

### 1. Choose the Right Configuration

```python
# Match configuration to your use case
if data_volume < 10000:
    config = "small"
elif data_volume < 100000:
    config = "medium"
else:
    config = "large"
```

### 2. Monitor Performance

```python
# Always monitor in production
monitor = MemoryPerformanceMonitor()
memory = ChromaDBMemory()

# Wrap operations
result = await monitor.monitor_operation(
    "search",
    "vector",
    memory.search,
    query
)
```

### 3. Use Appropriate Caching

```python
# Cache frequently accessed data
cache = OptimizedVectorSearch(memory)
results = await cache.cached_search(query)
```

### 4. Plan for Scale

```python
# Design for growth
if expected_growth > 10x:
    use_distributed = True
    use_partitioning = True
```

## Next Steps

- [Memory Overview](README.md) - Memory system concepts
- [Memory Patterns](patterns.md) - Usage patterns
- [API Reference](api-reference.md) - Complete API docs
- [Examples](../../examples/memory/) - Working examples
