"""Tests for knowledge graph memory implementation."""

import pytest

from agenticraft.core.types import Message, MessageRole
from agenticraft.memory.graph import KnowledgeGraphMemory


@pytest.fixture
async def kg_memory():
    """Create a knowledge graph memory instance."""
    memory = KnowledgeGraphMemory(
        max_entities=100,
        max_relationships=500,
        entity_types=["PERSON", "ORGANIZATION", "LOCATION", "PROJECT"],
        relationship_types=[
            "works_at",
            "works_with",
            "manages",
            "located_in",
            "created",
        ],
    )
    yield memory
    # Cleanup
    await memory.clear()


@pytest.mark.asyncio
async def test_entity_creation(kg_memory):
    """Test creating and retrieving entities."""
    # Add an entity
    entity = await kg_memory.add_entity(
        name="Alice Johnson",
        type="PERSON",
        properties={"title": "Engineer", "department": "AI"},
    )

    assert entity.name == "Alice Johnson"
    assert entity.type == "PERSON"
    assert entity.properties["title"] == "Engineer"

    # Retrieve by name
    retrieved = await kg_memory.get_entity("Alice Johnson")
    assert retrieved is not None
    assert retrieved.id == entity.id

    # Retrieve by ID
    by_id = await kg_memory.retrieve(entity.id)
    assert by_id is not None
    assert by_id["entity"]["name"] == "Alice Johnson"


@pytest.mark.asyncio
async def test_relationship_creation(kg_memory):
    """Test creating relationships between entities."""
    # Create entities
    alice = await kg_memory.add_entity("Alice", "PERSON")
    openai = await kg_memory.add_entity("OpenAI", "ORGANIZATION")

    # Create relationship
    rel = await kg_memory.add_relationship(
        source_id=alice.id,
        target_id=openai.id,
        type="works_at",
        properties={"since": "2020"},
        confidence=0.9,
    )

    assert rel.source_id == alice.id
    assert rel.target_id == openai.id
    assert rel.type == "works_at"
    assert rel.confidence == 0.9

    # Test invalid relationship (non-existent entities)
    with pytest.raises(ValueError):
        await kg_memory.add_relationship(
            source_id="invalid_id", target_id=openai.id, type="works_at"
        )


@pytest.mark.asyncio
async def test_text_processing(kg_memory):
    """Test entity and relationship extraction from text."""
    text = "Alice Johnson works at OpenAI. She collaborates with Bob Smith on GPT-4."

    entities, relationships = await kg_memory.process_text(text)

    # Should extract entities
    assert len(entities) > 0
    entity_names = [e.name for e in entities]
    assert "Alice Johnson" in entity_names
    assert "Bob Smith" in entity_names
    assert "OpenAI" in entity_names

    # Should extract relationships
    assert len(relationships) > 0
    rel_types = [r.type for r in relationships]
    assert any(r in rel_types for r in ["works_at", "works_with", "related_to"])


@pytest.mark.asyncio
@pytest.mark.skip(reason="Entity extraction not yet implemented")
async def test_entity_extraction_patterns(kg_memory):
    """Test various entity extraction patterns."""
    # Test email extraction
    text = "Contact john.doe@example.com for more information."
    entities, _ = await kg_memory.process_text(text)

    emails = [e for e in entities if e.type == "EMAIL"]
    assert len(emails) > 0
    assert emails[0].name == "john.doe@example.com"

    # Test organization extraction
    text = "Microsoft and Google are leading tech companies."
    entities, _ = await kg_memory.process_text(text)

    orgs = [e for e in entities if e.type == "ORGANIZATION"]
    assert len(orgs) >= 2
    org_names = [o.name for o in orgs]
    assert "Microsoft" in org_names
    assert "Google" in org_names


@pytest.mark.asyncio
@pytest.mark.skip(reason="Relationship inference not yet implemented")
async def test_relationship_inference(kg_memory):
    """Test relationship type inference from text."""
    test_cases = [
        ("Alice works at Google", "works_at"),
        ("Bob manages the team", "manages"),
        ("The office is located in San Francisco", "located_in"),
        ("Tesla created the Model S", "created"),
        ("Carol knows David", "knows"),
    ]

    for text, expected_rel in test_cases:
        # Extract entities first
        entities, _ = await kg_memory.process_text(text)

        if len(entities) >= 2:
            # Test relationship inference
            rel_type = kg_memory._infer_relationship(
                text, entities[0].name, entities[1].name
            )
            # Should infer the expected relationship or default to related_to
            assert rel_type in [expected_rel, "related_to"]


@pytest.mark.asyncio
async def test_get_related_entities(kg_memory):
    """Test finding related entities."""
    # Create a small network
    alice = await kg_memory.add_entity("Alice", "PERSON")
    bob = await kg_memory.add_entity("Bob", "PERSON")
    openai = await kg_memory.add_entity("OpenAI", "ORGANIZATION")
    sf = await kg_memory.add_entity("San Francisco", "LOCATION")

    # Create relationships
    await kg_memory.add_relationship(alice.id, openai.id, "works_at")
    await kg_memory.add_relationship(bob.id, openai.id, "works_at")
    await kg_memory.add_relationship(alice.id, bob.id, "works_with")
    await kg_memory.add_relationship(openai.id, sf.id, "located_in")

    # Test outgoing relationships
    alice_related = await kg_memory.get_related_entities(alice.id, direction="outgoing")
    assert len(alice_related) == 2
    related_names = [e.name for e in alice_related]
    assert "OpenAI" in related_names
    assert "Bob" in related_names

    # Test incoming relationships
    openai_related = await kg_memory.get_related_entities(
        openai.id, direction="incoming"
    )
    assert len(openai_related) == 2
    related_names = [e.name for e in openai_related]
    assert "Alice" in related_names
    assert "Bob" in related_names

    # Test specific relationship type
    works_at_openai = await kg_memory.get_related_entities(
        openai.id, relationship_type="works_at", direction="incoming"
    )
    assert len(works_at_openai) == 2


@pytest.mark.asyncio
@pytest.mark.skip(reason="Path finding not yet implemented")
async def test_path_finding(kg_memory):
    """Test finding paths between entities."""
    # Create a network
    alice = await kg_memory.add_entity("Alice", "PERSON")
    bob = await kg_memory.add_entity("Bob", "PERSON")
    carol = await kg_memory.add_entity("Carol", "PERSON")
    openai = await kg_memory.add_entity("OpenAI", "ORGANIZATION")
    anthropic = await kg_memory.add_entity("Anthropic", "ORGANIZATION")

    # Create relationships forming a path
    await kg_memory.add_relationship(alice.id, openai.id, "works_at")
    await kg_memory.add_relationship(bob.id, openai.id, "works_at")
    await kg_memory.add_relationship(carol.id, anthropic.id, "works_at")
    await kg_memory.add_relationship(bob.id, carol.id, "knows")

    # Find path from Alice to Anthropic
    path = await kg_memory.find_path(alice.id, anthropic.id, max_depth=4)

    assert path is not None
    assert len(path) == 4  # Alice -> OpenAI -> Bob -> Carol -> Anthropic
    assert path[0].name == "Alice"
    assert path[-1].name == "Anthropic"

    # Test no path exists (with limited depth)
    no_path = await kg_memory.find_path(alice.id, anthropic.id, max_depth=2)
    assert no_path is None


@pytest.mark.asyncio
async def test_query_graph(kg_memory):
    """Test querying the graph."""
    # Add various entities
    await kg_memory.add_entity("Alice", "PERSON", {"role": "Engineer"})
    await kg_memory.add_entity("Bob", "PERSON", {"role": "Manager"})
    await kg_memory.add_entity("OpenAI", "ORGANIZATION", {"type": "AI Company"})
    await kg_memory.add_entity("San Francisco", "LOCATION", {"country": "USA"})

    # Query by entity type
    people = await kg_memory.query_graph(entity_type="PERSON")
    assert len(people) == 2

    # Query by properties
    engineers = await kg_memory.query_graph(properties_filter={"role": "Engineer"})
    assert len(engineers) == 1
    assert engineers[0].name == "Alice"

    # Query with limit
    limited = await kg_memory.query_graph(limit=1)
    assert len(limited) == 1


@pytest.mark.asyncio
async def test_remove_operations(kg_memory):
    """Test removing entities and relationships."""
    # Create entities and relationships
    alice = await kg_memory.add_entity("Alice", "PERSON")
    bob = await kg_memory.add_entity("Bob", "PERSON")
    rel = await kg_memory.add_relationship(alice.id, bob.id, "knows")

    # Remove relationship
    await kg_memory.remove_relationship(rel.id)

    # Verify relationship is gone
    alice_related = await kg_memory.get_related_entities(alice.id)
    assert len(alice_related) == 0

    # Remove entity (should also remove its relationships)
    await kg_memory.add_relationship(alice.id, bob.id, "knows")
    await kg_memory.remove_entity(alice.id)

    # Verify entity is gone
    retrieved = await kg_memory.get_entity("Alice")
    assert retrieved is None

    # Verify relationships are also gone
    bob_related = await kg_memory.get_related_entities(bob.id, direction="incoming")
    assert len(bob_related) == 0


@pytest.mark.asyncio
async def test_capacity_limits(kg_memory):
    """Test entity and relationship capacity limits."""
    # Create small capacity graph
    small_kg = KnowledgeGraphMemory(max_entities=3, max_relationships=3)

    # Add entities up to limit
    e1 = await small_kg.add_entity("Entity1", "PERSON")
    e2 = await small_kg.add_entity("Entity2", "PERSON")
    e3 = await small_kg.add_entity("Entity3", "PERSON")

    # Adding another should remove the oldest
    e4 = await small_kg.add_entity("Entity4", "PERSON")

    assert len(small_kg.entities) == 3
    assert e1.id not in small_kg.entities  # Oldest was removed
    assert e4.id in small_kg.entities

    # Test relationship limits
    await small_kg.add_relationship(e2.id, e3.id, "knows", confidence=0.5)
    await small_kg.add_relationship(e3.id, e4.id, "knows", confidence=0.7)
    await small_kg.add_relationship(e4.id, e2.id, "knows", confidence=0.3)

    # Adding another should remove the one with lowest confidence
    await small_kg.add_relationship(e2.id, e4.id, "works_with", confidence=0.9)

    assert len(small_kg.relationships) == 3


@pytest.mark.asyncio
async def test_update_existing_entity(kg_memory):
    """Test updating existing entities."""
    # Add entity
    entity = await kg_memory.add_entity("Alice", "PERSON", {"role": "Junior Engineer"})

    original_id = entity.id
    original_created = entity.created_at

    # Update same entity (same name and type)
    updated = await kg_memory.add_entity(
        "Alice", "PERSON", {"role": "Senior Engineer", "department": "AI"}
    )

    # Should be the same entity with updated properties
    assert updated.id == original_id
    assert updated.created_at == original_created
    assert updated.updated_at > original_created
    assert updated.properties["role"] == "Senior Engineer"
    assert updated.properties["department"] == "AI"


@pytest.mark.asyncio
async def test_visualization_formats(kg_memory):
    """Test different visualization formats."""
    # Create a small graph
    alice = await kg_memory.add_entity("Alice", "PERSON")
    openai = await kg_memory.add_entity("OpenAI", "ORGANIZATION")
    await kg_memory.add_relationship(alice.id, openai.id, "works_at")

    # Test dict format
    dict_viz = kg_memory.visualize_graph(format="dict")
    assert "nodes" in dict_viz
    assert "edges" in dict_viz
    assert len(dict_viz["nodes"]) == 2
    assert len(dict_viz["edges"]) == 1

    # Test cytoscape format
    cyto_viz = kg_memory.visualize_graph(format="cytoscape")
    assert "elements" in cyto_viz
    assert len(cyto_viz["elements"]) == 3  # 2 nodes + 1 edge

    # Test graphviz format
    dot_viz = kg_memory.visualize_graph(format="graphviz")
    assert "digraph KnowledgeGraph" in dot_viz
    assert "Alice" in dot_viz
    assert "OpenAI" in dot_viz
    assert "works_at" in dot_viz


@pytest.mark.asyncio
@pytest.mark.skip(reason="Stats calculation needs update")
async def test_get_stats(kg_memory):
    """Test graph statistics."""
    # Add some data
    alice = await kg_memory.add_entity("Alice", "PERSON")
    bob = await kg_memory.add_entity("Bob", "PERSON")
    openai = await kg_memory.add_entity("OpenAI", "ORGANIZATION")

    await kg_memory.add_relationship(alice.id, openai.id, "works_at")
    await kg_memory.add_relationship(bob.id, openai.id, "works_at")
    await kg_memory.add_relationship(alice.id, bob.id, "knows")

    stats = kg_memory.get_stats()

    assert stats["total_entities"] == 3
    assert stats["total_relationships"] == 3
    assert stats["entity_types"]["PERSON"] == 2
    assert stats["entity_types"]["ORGANIZATION"] == 1
    assert stats["relationship_types"]["works_at"] == 2
    assert stats["relationship_types"]["knows"] == 1
    assert stats["avg_relationships_per_entity"] == 2.0  # 6 connections / 3 entities


@pytest.mark.asyncio
async def test_store_method_integration(kg_memory):
    """Test the store method that processes different value types."""
    # Store a Message
    msg = Message(
        role=MessageRole.USER, content="Alice works at OpenAI in San Francisco"
    )
    await kg_memory.store("msg1", msg)

    # Should have extracted entities
    alice = await kg_memory.get_entity("Alice")
    openai = await kg_memory.get_entity("OpenAI")
    sf = await kg_memory.get_entity("San Francisco")

    assert alice is not None
    assert openai is not None
    assert sf is not None

    # Store a dict
    await kg_memory.store(
        "dict1",
        {"text": "Bob manages the engineering team"},
        metadata={"source": "test"},
    )

    bob = await kg_memory.get_entity("Bob")
    assert bob is not None
