#!/usr/bin/env python3
"""Knowledge Graph memory example (Clean Version).

This example demonstrates:
- Creating knowledge graphs
- Adding entities and relationships
- Querying the graph
- Using graph memory with agents

Note: This is a clean version that works without patches.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""

    id: str
    name: str
    entity_type: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Represents a relationship between entities."""

    source_id: str
    target_id: str
    relationship_type: str
    attributes: dict[str, Any] = field(default_factory=dict)


class SimpleKnowledgeGraph:
    """Simple in-memory knowledge graph for demonstration."""

    def __init__(self, name: str = "demo_graph"):
        self.name = name
        self.entities: dict[str, Entity] = {}
        self.relationships: list[Relationship] = []
        self.entity_counter = 0
        print(f"✅ Initialized knowledge graph: {name}")

    def add_entity(self, name: str, entity_type: str, **attributes) -> str:
        """Add an entity to the graph."""
        entity_id = f"entity_{self.entity_counter}"
        self.entity_counter += 1

        self.entities[entity_id] = Entity(
            id=entity_id, name=name, entity_type=entity_type, attributes=attributes
        )
        return entity_id

    def add_relationship(
        self, source_id: str, target_id: str, relationship_type: str, **attributes
    ) -> None:
        """Add a relationship between entities."""
        if source_id in self.entities and target_id in self.entities:
            self.relationships.append(
                Relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=relationship_type,
                    attributes=attributes,
                )
            )

    def get_entity(self, entity_id: str) -> Entity:
        """Get an entity by ID."""
        return self.entities.get(entity_id)

    def find_entities(
        self, entity_type: str = None, name_contains: str = None
    ) -> list[Entity]:
        """Find entities by type or name."""
        results = []
        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            if name_contains and name_contains.lower() not in entity.name.lower():
                continue
            results.append(entity)
        return results

    def get_relationships(
        self, entity_id: str, relationship_type: str = None
    ) -> list[tuple[Relationship, Entity]]:
        """Get relationships for an entity."""
        results = []
        for rel in self.relationships:
            if rel.source_id == entity_id:
                if relationship_type and rel.relationship_type != relationship_type:
                    continue
                target = self.entities.get(rel.target_id)
                if target:
                    results.append((rel, target))
        return results

    def get_graph_stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        entity_types = defaultdict(int)
        for entity in self.entities.values():
            entity_types[entity.entity_type] += 1

        relationship_types = defaultdict(int)
        for rel in self.relationships:
            relationship_types[rel.relationship_type] += 1

        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": dict(entity_types),
            "relationship_types": dict(relationship_types),
        }


async def main():
    """Run knowledge graph examples."""
    print("🕸️ AgentiCraft Knowledge Graph Example (Clean)")
    print("=" * 50)

    # Create knowledge graph
    graph = SimpleKnowledgeGraph("agent_knowledge")

    print("\n📝 Building knowledge graph...")

    # Add entities
    entities = {
        "alice": graph.add_entity(
            "Alice Johnson", "Person", role="Software Engineer", company="TechCorp"
        ),
        "bob": graph.add_entity(
            "Bob Smith", "Person", role="Data Scientist", company="AI Labs"
        ),
        "carol": graph.add_entity(
            "Carol Davis", "Person", role="Product Manager", company="TechCorp"
        ),
        "techcorp": graph.add_entity(
            "TechCorp", "Company", industry="Technology", size="Large"
        ),
        "ailabs": graph.add_entity(
            "AI Labs", "Company", industry="AI Research", size="Startup"
        ),
        "project_ai": graph.add_entity(
            "AI Assistant Project", "Project", status="Active", priority="High"
        ),
        "python": graph.add_entity("Python", "Technology", type="Programming Language"),
        "ml": graph.add_entity("Machine Learning", "Technology", type="AI Technology"),
    }

    print(f"   Added {len(entities)} entities")

    # Add relationships
    relationships = [
        (entities["alice"], entities["techcorp"], "WORKS_AT"),
        (entities["bob"], entities["ailabs"], "WORKS_AT"),
        (entities["carol"], entities["techcorp"], "WORKS_AT"),
        (entities["alice"], entities["bob"], "COLLABORATES_WITH"),
        (entities["alice"], entities["carol"], "REPORTS_TO"),
        (entities["project_ai"], entities["alice"], "ASSIGNED_TO"),
        (entities["project_ai"], entities["bob"], "ASSIGNED_TO"),
        (entities["alice"], entities["python"], "KNOWS"),
        (entities["alice"], entities["ml"], "KNOWS"),
        (entities["bob"], entities["python"], "EXPERT_IN"),
        (entities["bob"], entities["ml"], "EXPERT_IN"),
        (entities["project_ai"], entities["python"], "USES"),
        (entities["project_ai"], entities["ml"], "USES"),
    ]

    for source, target, rel_type in relationships:
        graph.add_relationship(source, target, rel_type)

    print(f"   Added {len(relationships)} relationships")

    # Query the graph
    print("\n🔍 Querying the knowledge graph...")

    # Find all people
    print("\n   People in the graph:")
    people = graph.find_entities(entity_type="Person")
    for person in people:
        print(f"   - {person.name} ({person.attributes.get('role', 'Unknown')})")

    # Find Alice's relationships
    alice_entity = graph.get_entity(entities["alice"])
    print(f"\n   {alice_entity.name}'s connections:")

    for rel, target in graph.get_relationships(entities["alice"]):
        print(f"   - {rel.relationship_type} → {target.name}")

    # Find who works on the AI project
    print("\n   AI Assistant Project team:")
    for rel in graph.relationships:
        if (
            rel.target_id == entities["project_ai"]
            and rel.relationship_type == "ASSIGNED_TO"
        ):
            person = graph.get_entity(rel.source_id)
            print(f"   - {person.name}")

    # Find technology experts
    print("\n   Technology expertise:")
    tech_entities = graph.find_entities(entity_type="Technology")
    for tech in tech_entities:
        experts = []
        for rel in graph.relationships:
            if rel.target_id == tech.id and rel.relationship_type in [
                "KNOWS",
                "EXPERT_IN",
            ]:
                expert = graph.get_entity(rel.source_id)
                level = "Expert" if rel.relationship_type == "EXPERT_IN" else "Knows"
                experts.append(f"{expert.name} ({level})")

        if experts:
            print(f"   {tech.name}: {', '.join(experts)}")

    # Graph statistics
    print("\n📊 Graph Statistics:")
    stats = graph.get_graph_stats()
    print(f"   Total entities: {stats['total_entities']}")
    print(f"   Total relationships: {stats['total_relationships']}")
    print("\n   Entity types:")
    for entity_type, count in stats["entity_types"].items():
        print(f"   - {entity_type}: {count}")
    print("\n   Relationship types:")
    for rel_type, count in stats["relationship_types"].items():
        print(f"   - {rel_type}: {count}")

    print("\n✅ Knowledge graph example complete!")
    print("\n💡 To use real knowledge graph with Neo4j:")
    print("   1. Install neo4j driver: pip install neo4j")
    print("   2. Import from agenticraft.memory import Neo4jMemory")
    print("   3. The framework will handle graph operations automatically")


if __name__ == "__main__":
    asyncio.run(main())
