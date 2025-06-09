"""Knowledge graph memory implementation.

This module provides graph-based memory storage with:
- Entity extraction and recognition
- Relationship mapping
- Graph queries and traversal
- Knowledge inference
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from agenticraft.core.memory import BaseMemory, MemoryEntry, MemoryType

from ...core.memory import BaseMemory
from ...core.types import Message

logger = logging.getLogger(__name__)


class Entity(BaseModel):
    """An entity in the knowledge graph."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.id == other.id
        return False


class Relationship(BaseModel):
    """A relationship between entities."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    confidence: float = 1.0

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Relationship):
            return self.id == other.id
        return False


class KnowledgeGraphMemory(BaseMemory):
    """Knowledge graph memory implementation.

    This memory implementation stores information as a graph of entities
    and relationships, allowing for complex knowledge representation
    and inference.

    Args:
        max_entities: Maximum number of entities to store
        max_relationships: Maximum number of relationships
        entity_types: Allowed entity types (None for any)
        relationship_types: Allowed relationship types (None for any)

    Example:
        Basic usage::

            memory = KnowledgeGraphMemory()

            # Extract and store entities from text
            await memory.process_text(
                "Alice works at OpenAI. She collaborates with Bob on GPT-4."
            )

            # Query the graph
            alice = await memory.get_entity("Alice")
            colleagues = await memory.get_related_entities(
                alice.id,
                relationship_type="collaborates_with"
            )
    """

    def __init__(
        self,
        max_entities: int = 10000,
        max_relationships: int = 50000,
        entity_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
    ):
        """Initialize knowledge graph memory."""
        super().__init__()

        self.max_entities = max_entities
        self.max_relationships = max_relationships
        self.entity_types = set(entity_types) if entity_types else None
        self.relationship_types = (
            set(relationship_types) if relationship_types else None
        )

        # Storage
        self.entities: dict[str, Entity] = {}
        self.relationships: dict[str, Relationship] = {}

        # Indexes for efficient lookup
        self.entity_name_index: dict[str, set[str]] = defaultdict(set)
        self.entity_type_index: dict[str, set[str]] = defaultdict(set)
        self.relationship_index: dict[str, set[str]] = defaultdict(set)
        self.reverse_relationship_index: dict[str, set[str]] = defaultdict(set)

        # Entity recognition patterns
        self.entity_patterns = {
            "PERSON": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
            "ORGANIZATION": r"\b[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*\b",
            "LOCATION": r"\b(?:in|at|from|to) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
            "DATE": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        }

        logger.info("Initialized knowledge graph memory")

    def extract_entities_and_relationships(
        self, text: str
    ) -> tuple[list[dict], list[dict]]:
        """Extract entities and relationships from text.

        Simple pattern-based extraction for demonstration.
        """
        entities = []
        relationships = []

        # Simple entity patterns
        import re

        # Pattern: "X is a Y" -> Entity X of type Y
        is_a_pattern = r"(\w+)\s+is\s+(?:a|an)\s+(\w+)"
        for match in re.finditer(is_a_pattern, text, re.IGNORECASE):
            entities.append({"name": match.group(1), "type": match.group(2)})

        # Pattern: "X knows Y" -> Relationship
        knows_pattern = r"(\w+)\s+knows\s+(\w+)"
        for match in re.finditer(knows_pattern, text, re.IGNORECASE):
            relationships.append(
                {"from": match.group(1), "to": match.group(2), "type": "knows"}
            )

        # Pattern: "X works at Y" -> Entity + Relationship
        works_pattern = r"(\w+)\s+works?\s+(?:at|for)\s+(\w+)"
        for match in re.finditer(works_pattern, text, re.IGNORECASE):
            entities.extend(
                [
                    {"name": match.group(1), "type": "person"},
                    {"name": match.group(2), "type": "organization"},
                ]
            )
            relationships.append(
                {"from": match.group(1), "to": match.group(2), "type": "works_at"}
            )

        return entities, relationships

    def infer_relationships(self) -> list[dict]:
        """Infer new relationships from existing data."""
        inferred = []

        # If A knows B and B knows C, infer A might know C
        knows_rels = [r for r in self.relationships if r["type"] == "knows"]

        for rel1 in knows_rels:
            for rel2 in knows_rels:
                if rel1["to"] == rel2["from"] and rel1["from"] != rel2["to"]:
                    # Check if relationship already exists
                    exists = any(
                        r["from"] == rel1["from"]
                        and r["to"] == rel2["to"]
                        and r["type"] == "related_to"
                        for r in self.relationships
                    )
                    if not exists:
                        inferred.append(
                            {
                                "from": rel1["from"],
                                "to": rel2["to"],
                                "type": "related_to",
                            }
                        )

        return inferred

    def find_path(self, start: str, end: str, max_depth: int = 5) -> list[str] | None:
        """Find path between two entities."""
        if start == end:
            return [start]

        visited = set()
        queue = [(start, [start])]

        while queue and len(queue[0][1]) <= max_depth:
            current, path = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            # Find all connections
            for rel in self.relationships:
                next_node = None
                if rel["from"] == current:
                    next_node = rel["to"]
                elif rel["to"] == current and rel["type"] != "directed":
                    next_node = rel["from"]

                if next_node and next_node not in visited:
                    new_path = path + [next_node]
                    if next_node == end:
                        return new_path
                    queue.append((next_node, new_path))

        return None

    def get_stats(self) -> dict:
        """Get statistics about the knowledge graph."""
        entity_types = {}
        for entity in self.entities.values():
            entity_type = entity.get("type", "unknown")
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        relationship_types = {}
        for rel in self.relationships:
            rel_type = rel.get("type", "unknown")
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

        # Calculate density
        max_relationships = len(self.entities) * (len(self.entities) - 1)
        density = (
            len(self.relationships) / max_relationships if max_relationships > 0 else 0
        )

        return {
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
            "entity_types": entity_types,
            "relationship_types": relationship_types,
            "density": density,
        }

    async def store(
        self, key: str, value: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Store information in the knowledge graph.

        Args:
            key: Unique key (used as entity ID if value is entity-like)
            value: Value to store
            metadata: Optional metadata
        """
        # Convert value to text
        if isinstance(value, dict):
            text = json.dumps(value)
        elif isinstance(value, Message):
            text = value.content
        else:
            text = str(value)

        # Process text to extract entities and relationships
        await self.process_text(text, source_id=key, metadata=metadata)

    async def retrieve(self, key: str) -> Any | None:
        """Retrieve an entity by ID.

        Args:
            key: Entity ID

        Returns:
            Entity or None if not found
        """
        entity = self.entities.get(key)
        if entity:
            # Get relationships
            relationships = []
            for rel_id in self.relationship_index.get(key, []):
                if rel_id in self.relationships:
                    relationships.append(self.relationships[rel_id])

            return {
                "entity": entity.dict(),
                "relationships": [r.dict() for r in relationships],
            }

        return None

    async def process_text(
        self,
        text: str,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[list[Entity], list[Relationship]]:
        """Process text to extract entities and relationships.

        Args:
            text: Text to process
            source_id: Optional source ID
            metadata: Optional metadata

        Returns:
            Tuple of (entities, relationships) extracted
        """
        extracted_entities = []
        extracted_relationships = []

        # Extract entities
        entities_found = self._extract_entities(text)

        # Create or update entities
        for entity_name, entity_type in entities_found:
            entity = await self.add_entity(
                name=entity_name,
                type=entity_type,
                properties={"source": source_id} if source_id else {},
            )
            extracted_entities.append(entity)

        # Extract relationships
        if len(extracted_entities) >= 2:
            # Simple co-occurrence based relationships
            for i, entity1 in enumerate(extracted_entities):
                for entity2 in extracted_entities[i + 1 :]:
                    # Check if entities appear in same sentence
                    sentences = text.split(".")
                    for sentence in sentences:
                        if entity1.name in sentence and entity2.name in sentence:
                            # Infer relationship type from sentence
                            rel_type = self._infer_relationship(
                                sentence, entity1.name, entity2.name
                            )
                            if rel_type:
                                relationship = await self.add_relationship(
                                    source_id=entity1.id,
                                    target_id=entity2.id,
                                    type=rel_type,
                                    properties={"sentence": sentence.strip()},
                                )
                                extracted_relationships.append(relationship)

        return extracted_entities, extracted_relationships

    def _extract_entities(self, text: str) -> list[tuple[str, str]]:
        """Extract entities from text using patterns.

        Args:
            text: Text to analyze

        Returns:
            List of (entity_name, entity_type) tuples
        """
        entities = []

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean up match
                if isinstance(match, tuple):
                    match = match[0]
                match = match.strip()

                # Skip if entity type is restricted
                if self.entity_types and entity_type not in self.entity_types:
                    continue

                entities.append((match, entity_type))

        # Deduplicate
        return list(set(entities))

    def _infer_relationship(
        self, sentence: str, entity1: str, entity2: str
    ) -> str | None:
        """Infer relationship type from sentence.

        Args:
            sentence: Sentence containing both entities
            entity1: First entity name
            entity2: Second entity name

        Returns:
            Relationship type or None
        """
        sentence_lower = sentence.lower()

        # Common relationship patterns
        patterns = {
            "works_at": ["works at", "employed by", "employee of"],
            "works_with": ["works with", "collaborates with", "partners with"],
            "manages": ["manages", "supervises", "leads"],
            "located_in": ["located in", "based in", "from"],
            "created": ["created", "built", "developed", "made"],
            "owns": ["owns", "has", "possesses"],
            "knows": ["knows", "met", "friends with"],
        }

        for rel_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    # Check if relationship type is allowed
                    if (
                        self.relationship_types
                        and rel_type not in self.relationship_types
                    ):
                        continue
                    return rel_type

        # Default relationship if entities co-occur
        default_rel = "related_to"
        if self.relationship_types and default_rel not in self.relationship_types:
            return None

        return default_rel

    async def add_entity(
        self, name: str, type: str, properties: dict[str, Any] | None = None
    ) -> Entity:
        """Add or update an entity.

        Args:
            name: Entity name
            type: Entity type
            properties: Optional properties

        Returns:
            Created or updated entity
        """
        # Check if entity already exists
        existing_ids = self.entity_name_index.get(name.lower(), set())
        for entity_id in existing_ids:
            entity = self.entities.get(entity_id)
            if entity and entity.type == type:
                # Update existing entity
                entity.properties.update(properties or {})
                entity.updated_at = datetime.now()
                return entity

        # Check capacity
        if len(self.entities) >= self.max_entities:
            # Remove oldest entity
            oldest = min(self.entities.values(), key=lambda e: e.updated_at)
            await self.remove_entity(oldest.id)

        # Create new entity
        entity = Entity(name=name, type=type, properties=properties or {})

        # Store entity
        self.entities[entity.id] = entity

        # Update indexes
        self.entity_name_index[name.lower()].add(entity.id)
        self.entity_type_index[type].add(entity.id)

        logger.debug(f"Added entity: {name} ({type})")
        return entity

    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        type: str,
        properties: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> Relationship:
        """Add a relationship between entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            type: Relationship type
            properties: Optional properties
            confidence: Confidence score (0-1)

        Returns:
            Created relationship
        """
        # Verify entities exist
        if source_id not in self.entities or target_id not in self.entities:
            raise ValueError("Source or target entity not found")

        # Check if relationship already exists
        for rel_id in self.relationship_index.get(source_id, []):
            rel = self.relationships.get(rel_id)
            if rel and rel.target_id == target_id and rel.type == type:
                # Update confidence if higher
                if confidence > rel.confidence:
                    rel.confidence = confidence
                return rel

        # Check capacity
        if len(self.relationships) >= self.max_relationships:
            # Remove relationship with lowest confidence
            if self.relationships:
                weakest = min(self.relationships.values(), key=lambda r: r.confidence)
                await self.remove_relationship(weakest.id)

        # Create relationship
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            type=type,
            properties=properties or {},
            confidence=confidence,
        )

        # Store relationship
        self.relationships[relationship.id] = relationship

        # Update indexes
        self.relationship_index[source_id].add(relationship.id)
        self.reverse_relationship_index[target_id].add(relationship.id)

        logger.debug(f"Added relationship: {type} between {source_id} and {target_id}")
        return relationship

    async def get_entity(self, name: str) -> Entity | None:
        """Get entity by name.

        Args:
            name: Entity name

        Returns:
            Entity or None if not found
        """
        entity_ids = self.entity_name_index.get(name.lower(), set())
        if entity_ids:
            # Return most recently updated
            entities = [
                self.entities[eid] for eid in entity_ids if eid in self.entities
            ]
            if entities:
                return max(entities, key=lambda e: e.updated_at)

        return None

    async def get_related_entities(
        self,
        entity_id: str,
        relationship_type: str | None = None,
        direction: str = "outgoing",
    ) -> list[Entity]:
        """Get entities related to a given entity.

        Args:
            entity_id: Entity ID
            relationship_type: Optional filter by relationship type
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of related entities
        """
        related_entities = []

        # Get outgoing relationships
        if direction in ["outgoing", "both"]:
            for rel_id in self.relationship_index.get(entity_id, []):
                rel = self.relationships.get(rel_id)
                if rel and (not relationship_type or rel.type == relationship_type):
                    target = self.entities.get(rel.target_id)
                    if target:
                        related_entities.append(target)

        # Get incoming relationships
        if direction in ["incoming", "both"]:
            for rel_id in self.reverse_relationship_index.get(entity_id, []):
                rel = self.relationships.get(rel_id)
                if rel and (not relationship_type or rel.type == relationship_type):
                    source = self.entities.get(rel.source_id)
                    if source:
                        related_entities.append(source)

        return related_entities

    async def find_path(
        self, start_entity_id: str, end_entity_id: str, max_depth: int = 5
    ) -> list[Entity] | None:
        """Find a path between two entities.

        Args:
            start_entity_id: Starting entity ID
            end_entity_id: Target entity ID
            max_depth: Maximum path length

        Returns:
            List of entities forming the path, or None if no path exists
        """
        if start_entity_id not in self.entities or end_entity_id not in self.entities:
            return None

        # BFS to find shortest path
        queue = [(start_entity_id, [start_entity_id])]
        visited = {start_entity_id}

        while queue and len(visited) < max_depth * 10:  # Limit search
            current_id, path = queue.pop(0)

            if current_id == end_entity_id:
                # Found path - convert IDs to entities
                return [self.entities[eid] for eid in path if eid in self.entities]

            # Explore neighbors
            for rel_id in self.relationship_index.get(current_id, []):
                rel = self.relationships.get(rel_id)
                if rel and rel.target_id not in visited and len(path) < max_depth:
                    visited.add(rel.target_id)
                    queue.append((rel.target_id, path + [rel.target_id]))

        return None

    async def query_graph(
        self,
        entity_type: str | None = None,
        properties_filter: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[Entity]:
        """Query the graph for entities.

        Args:
            entity_type: Filter by entity type
            properties_filter: Filter by properties
            limit: Maximum results

        Returns:
            List of matching entities
        """
        results = []

        # Get candidate entities
        if entity_type:
            candidates = [
                self.entities[eid]
                for eid in self.entity_type_index.get(entity_type, [])
                if eid in self.entities
            ]
        else:
            candidates = list(self.entities.values())

        # Apply property filters
        for entity in candidates:
            if properties_filter:
                match = all(
                    entity.properties.get(k) == v for k, v in properties_filter.items()
                )
                if not match:
                    continue

            results.append(entity)

            if len(results) >= limit:
                break

        return results

    async def remove_entity(self, entity_id: str) -> None:
        """Remove an entity and its relationships.

        Args:
            entity_id: Entity ID to remove
        """
        entity = self.entities.get(entity_id)
        if not entity:
            return

        # Remove relationships
        rel_ids = list(self.relationship_index.get(entity_id, []))
        rel_ids.extend(self.reverse_relationship_index.get(entity_id, []))

        for rel_id in set(rel_ids):
            await self.remove_relationship(rel_id)

        # Remove from indexes
        self.entity_name_index[entity.name.lower()].discard(entity_id)
        self.entity_type_index[entity.type].discard(entity_id)

        # Remove entity
        del self.entities[entity_id]

        logger.debug(f"Removed entity: {entity_id}")

    async def remove_relationship(self, relationship_id: str) -> None:
        """Remove a relationship.

        Args:
            relationship_id: Relationship ID to remove
        """
        rel = self.relationships.get(relationship_id)
        if not rel:
            return

        # Remove from indexes
        self.relationship_index[rel.source_id].discard(relationship_id)
        self.reverse_relationship_index[rel.target_id].discard(relationship_id)

        # Remove relationship
        del self.relationships[relationship_id]

    async def clear(self) -> None:
        """Clear all entities and relationships."""
        self.entities.clear()
        self.relationships.clear()
        self.entity_name_index.clear()
        self.entity_type_index.clear()
        self.relationship_index.clear()
        self.reverse_relationship_index.clear()

        logger.info("Cleared knowledge graph")

    def get_stats(self) -> dict[str, Any]:
        """Get graph statistics.

        Returns:
            Dictionary with graph stats
        """
        # Calculate average relationships per entity
        total_relationships = sum(
            len(rels) for rels in self.relationship_index.values()
        )
        avg_relationships = (
            total_relationships / len(self.entities) if self.entities else 0
        )

        # Count entity types
        entity_type_counts = {
            etype: len(eids) for etype, eids in self.entity_type_index.items()
        }

        # Count relationship types
        relationship_type_counts = defaultdict(int)
        for rel in self.relationships.values():
            relationship_type_counts[rel.type] += 1

        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": entity_type_counts,
            "relationship_types": dict(relationship_type_counts),
            "avg_relationships_per_entity": avg_relationships,
            "max_entities": self.max_entities,
            "max_relationships": self.max_relationships,
        }

    def visualize_graph(self, format: str = "dict") -> Any:
        """Visualize the graph structure.

        Args:
            format: Output format ("dict", "cytoscape", "graphviz")

        Returns:
            Graph visualization in requested format
        """
        if format == "dict":
            # Simple dictionary representation
            nodes = []
            edges = []

            for entity in self.entities.values():
                nodes.append(
                    {
                        "id": entity.id,
                        "label": entity.name,
                        "type": entity.type,
                        "properties": entity.properties,
                    }
                )

            for rel in self.relationships.values():
                edges.append(
                    {
                        "id": rel.id,
                        "source": rel.source_id,
                        "target": rel.target_id,
                        "type": rel.type,
                        "properties": rel.properties,
                        "confidence": rel.confidence,
                    }
                )

            return {"nodes": nodes, "edges": edges}

        elif format == "cytoscape":
            # Cytoscape.js format
            elements = []

            for entity in self.entities.values():
                elements.append(
                    {
                        "data": {
                            "id": entity.id,
                            "label": entity.name,
                            "type": entity.type,
                        }
                    }
                )

            for rel in self.relationships.values():
                elements.append(
                    {
                        "data": {
                            "id": rel.id,
                            "source": rel.source_id,
                            "target": rel.target_id,
                            "label": rel.type,
                        }
                    }
                )

            return {"elements": elements}

        elif format == "graphviz":
            # DOT format for Graphviz
            lines = ["digraph KnowledgeGraph {"]
            lines.append("  rankdir=LR;")
            lines.append("  node [shape=box];")

            # Add nodes
            for entity in self.entities.values():
                label = f"{entity.name}\\n({entity.type})"
                lines.append(f'  "{entity.id}" [label="{label}"];')

            # Add edges
            for rel in self.relationships.values():
                lines.append(
                    f'  "{rel.source_id}" -> "{rel.target_id}" '
                    f'[label="{rel.type}"];'
                )

            lines.append("}")
            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown format: {format}")

    async def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """Get recent items from memory."""
        entries = []

        # Convert entities to MemoryEntry objects
        sorted_entities = sorted(
            self.entities.items(),
            key=lambda x: x[1].get("created_at", ""),
            reverse=True,
        )

        for entity_id, entity_data in sorted_entities[:limit]:
            entry = MemoryEntry(
                id=entity_id,
                content=f"Entity: {entity_data['name']} ({entity_data['type']})",
                entry_type=MemoryType.KNOWLEDGE,
                metadata={
                    "entity_type": entity_data["type"],
                    "attributes": entity_data.get("attributes", {}),
                    "relationships": [
                        rel
                        for rel in self.relationships
                        if rel["from"] == entity_id or rel["to"] == entity_id
                    ],
                },
            )
            entries.append(entry)

        return entries

    async def search(self, query: str, max_results: int = 5) -> list[MemoryEntry]:
        """Search for items in memory."""
        entries = []
        query_lower = query.lower()

        # Search entities
        for entity_id, entity_data in self.entities.items():
            # Check name and type
            if (
                query_lower in entity_data["name"].lower()
                or query_lower in entity_data["type"].lower()
            ):

                # Also check attributes
                attr_match = any(
                    query_lower in str(v).lower()
                    for v in entity_data.get("attributes", {}).values()
                )

                if attr_match or query_lower in entity_data["name"].lower():
                    entry = MemoryEntry(
                        id=entity_id,
                        content=f"Entity: {entity_data['name']} ({entity_data['type']})",
                        entry_type=MemoryType.KNOWLEDGE,
                        metadata={
                            "entity_type": entity_data["type"],
                            "attributes": entity_data.get("attributes", {}),
                            "match_score": 1.0,
                        },
                    )
                    entries.append(entry)

        # Sort by relevance (simple for now)
        entries.sort(key=lambda x: x.metadata.get("match_score", 0), reverse=True)

        return entries[:max_results]


# Convenience function
def create_knowledge_graph(
    max_entities: int = 10000, max_relationships: int = 50000, **kwargs
) -> KnowledgeGraphMemory:
    """Create a knowledge graph memory instance.

    Args:
        max_entities: Maximum entities to store
        max_relationships: Maximum relationships
        **kwargs: Additional arguments

    Returns:
        KnowledgeGraphMemory instance
    """
    return KnowledgeGraphMemory(
        max_entities=max_entities, max_relationships=max_relationships, **kwargs
    )
