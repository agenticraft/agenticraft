# Memory System Guide

AgentiCraft's memory system enables agents and workflows to remember past interactions, learn from experience, and build upon previous work. This guide covers how to use memory in your applications.

## Overview

The memory system provides three types of memory storage:

1. **Short-term Memory**: Recent interactions (sliding window)
2. **Long-term Memory**: Consolidated important insights
3. **Task Memory**: Context specific to tasks/workflows

## Key Features

- 🧠 **Automatic Consolidation**: Important memories promoted to long-term storage
- 🔍 **Semantic Search**: Find relevant memories by content
- 💾 **Persistent Storage**: Long-term memories saved to disk
- 🎯 **Task Context**: Maintain context within specific tasks
- 📊 **Memory Statistics**: Track memory usage and patterns

## Basic Usage

### Memory-Enhanced Research Team

```python
from agenticraft.workflows.memory_research_team import MemoryResearchTeam

# Create team with memory
team = MemoryResearchTeam(
    size=5,
    memory_enabled=True,
    memory_config={
        "short_term_capacity": 200,
        "consolidation_threshold": 0.7
    }
)

# Initialize
await team.initialize()

# First research
report1 = await team.research(
    topic="AI frameworks analysis",
    depth="comprehensive"
)

# Continue previous research
report2 = await team.research(
    topic="Continue our AI analysis with open source focus",
    continue_previous=True
)

# Shutdown
await team.shutdown()
```

### Direct Memory Usage

```python
from agenticraft.memory import ConsolidatedMemory, MemoryType

# Create memory system
memory = ConsolidatedMemory(
    short_term_capacity=100,
    consolidation_threshold=0.7
)

await memory.start()

# Store memories
await memory.store(
    key="user_preference",
    value="Prefers technical explanations",
    memory_type=MemoryType.LONG_TERM,
    importance=0.9
)

# Retrieve memories
results = await memory.retrieve(
    query="user preferences",
    memory_types=[MemoryType.LONG_TERM],
    limit=5
)

for result in results:
    print(f"Found: {result.entry.value} (relevance: {result.relevance_score})")

# Get statistics
stats = await memory.get_stats()
print(f"Total memories: {stats}")

await memory.stop()
```

### Memory-Enhanced Agents

```python
from agenticraft.memory.agent import MemoryAgent

# Create agent with memory
agent = MemoryAgent(
    name="ResearchAssistant",
    model="gpt-4",
    memory_enabled=True,
    memory_config={
        "short_term_capacity": 50,
        "consolidation_threshold": 0.6
    }
)

await agent.initialize()

# Agent remembers interactions
response = await agent.think_with_memory(
    "What did we discuss about Python frameworks?"
)

# Store important insights
await agent.remember(
    key="framework_comparison",
    value="FastAPI is faster than Flask for async operations",
    memory_type=MemoryType.LONG_TERM,
    importance=0.8
)

# Learn from feedback
await agent.learn_from_feedback(
    task_id="research_001",
    feedback="Excellent analysis of performance metrics",
    success=True,
    importance=0.9
)
```

## Memory Types

### Short-term Memory
- **Purpose**: Recent interactions and temporary context
- **Capacity**: Configurable (default: 100 entries)
- **Persistence**: In-memory only
- **Use cases**: Current conversation, recent tasks

### Long-term Memory
- **Purpose**: Important insights and learned patterns
- **Capacity**: Unlimited
- **Persistence**: Saved to disk
- **Use cases**: User preferences, successful strategies, key findings

### Task Memory
- **Purpose**: Context specific to tasks or workflows
- **Capacity**: Limited per task
- **Persistence**: In-memory
- **Use cases**: Multi-step workflows, project context

## Memory Configuration

### Basic Configuration

```python
memory_config = {
    "short_term_capacity": 100,        # Max short-term memories
    "consolidation_threshold": 0.7,    # Min importance for long-term
    "storage_path": Path.home() / ".agenticraft" / "memory"
}
```

### Advanced Configuration

```python
# Custom memory with all options
memory = ConsolidatedMemory(
    short_term_capacity=200,
    consolidation_threshold=0.6,
    storage_path=Path("/custom/path")
)

# Task memory configuration
task_memory_config = {
    "max_tasks": 10,          # Maximum concurrent tasks
    "max_per_task": 50        # Max memories per task
}
```

## Memory Consolidation

The system automatically consolidates memories based on importance:

```python
# Manual consolidation
stats = await memory.consolidate(force=True)
print(f"Promoted: {stats['promoted']}, Deleted: {stats['deleted']}")

# Automatic consolidation runs every 5 minutes
# Memories with importance >= threshold are promoted
# Low-importance old memories are deleted
```

### Importance Scoring

Memory importance is calculated based on:
- Access frequency
- Recency
- User-specified importance
- Task relevance
- Semantic density

## Search and Retrieval

### Basic Search

```python
# Search all memory types
results = await memory.retrieve(
    query="machine learning frameworks",
    limit=10
)
```

### Filtered Search

```python
# Search specific memory types
results = await memory.retrieve(
    query="deployment strategies",
    memory_types=[MemoryType.LONG_TERM],
    min_importance=0.7,
    metadata_filter={"task_type": "research"}
)
```

### Task-specific Search

```python
# Search within task context
results = await memory.retrieve(
    query="",  # Empty query returns all
    memory_types=[MemoryType.TASK],
    metadata_filter={"task_id": "research_001"}
)
```

## Best Practices

### 1. Choose Appropriate Memory Types

```python
# Short-term: Current context
await memory.store(
    key="current_topic",
    value="Discussing Python async",
    memory_type=MemoryType.SHORT_TERM,
    importance=0.5
)

# Long-term: Important insights
await memory.store(
    key="learned_pattern",
    value="User prefers examples in Python",
    memory_type=MemoryType.LONG_TERM,
    importance=0.9
)

# Task: Workflow-specific
await memory.store(
    key="research_finding",
    value="FastAPI outperforms Flask in benchmarks",
    memory_type=MemoryType.TASK,
    metadata={"task_id": "framework_comparison"},
    importance=0.8
)
```

### 2. Set Meaningful Importance

```python
# Critical information
importance = 0.9  # User preferences, key insights

# Useful information  
importance = 0.7  # Relevant findings, good examples

# Contextual information
importance = 0.5  # Conversation flow, temporary data

# Low priority
importance = 0.3  # Redundant or outdated info
```

### 3. Use Metadata Effectively

```python
await memory.store(
    key="research_insight",
    value="TensorFlow has better GPU support",
    memory_type=MemoryType.LONG_TERM,
    metadata={
        "source": "benchmark_study",
        "confidence": 0.85,
        "date": "2024-01",
        "tags": ["ml", "performance", "gpu"]
    },
    importance=0.8
)
```

### 4. Implement Memory Cleanup

```python
# Clear old task memories
await memory.task.clear_task("old_task_id")

# Clear all short-term memories
await memory.short_term.clear()

# Selective cleanup based on age
old_memories = await memory.retrieve(
    query="",
    metadata_filter={"date": {"$lt": "2024-01-01"}}
)
```

## Workflow Integration

### Research Team with Memory

```python
team = MemoryResearchTeam(memory_enabled=True)

# Research builds on previous work
reports = []
for topic in ["AI basics", "AI frameworks", "AI deployment"]:
    report = await team.research(
        topic=topic,
        continue_previous=True  # Uses memory context
    )
    reports.append(report)

# Get research history
history = await team.get_research_history(
    topic_filter="AI",
    limit=10
)
```

### Customer Service with Memory

```python
from agenticraft.workflows import CustomerServiceDesk

desk = CustomerServiceDesk(
    memory_enabled=True,
    memory_config={
        "consolidation_threshold": 0.6
    }
)

# Remembers customer interactions
response = await desk.handle(
    inquiry="What was my last order?",
    customer_id="user_123"
)
```

## Performance Considerations

### Memory Limits

```python
# Monitor memory usage
stats = await memory.get_stats()

if stats["short_term"]["utilization"] > 0.9:
    # Trigger consolidation
    await memory.consolidate()

if stats["long_term"]["count"] > 10000:
    # Consider archiving old memories
    pass
```

### Search Optimization

```python
# Use specific queries
results = await memory.retrieve(
    query="specific search terms",  # Better
    limit=5  # Only what you need
)

# Filter by type and metadata
results = await memory.retrieve(
    query="python",
    memory_types=[MemoryType.LONG_TERM],  # Faster
    metadata_filter={"tags": "frameworks"}  # More specific
)
```

## Troubleshooting

### Common Issues

1. **Memory not persisting**
   ```python
   # Ensure proper shutdown
   await memory.stop()  # Saves to disk
   ```

2. **High memory usage**
   ```python
   # Reduce short-term capacity
   memory = ConsolidatedMemory(short_term_capacity=50)
   
   # More aggressive consolidation
   memory = ConsolidatedMemory(consolidation_threshold=0.5)
   ```

3. **Slow retrieval**
   ```python
   # Use more specific queries
   # Limit search scope with memory_types
   # Add metadata filters
   ```

## Examples

### Complete Memory Workflow

```python
async def intelligent_assistant():
    """Assistant that learns and remembers."""
    
    # Initialize memory
    memory = ConsolidatedMemory()
    await memory.start()
    
    # Remember user preference
    await memory.store(
        key="user_style",
        value="Prefers concise technical answers",
        memory_type=MemoryType.LONG_TERM,
        importance=0.9
    )
    
    # Task-specific memory
    task_id = "project_analysis"
    await memory.store(
        key="project_context",
        value="Working on ML pipeline optimization",
        memory_type=MemoryType.TASK,
        metadata={"task_id": task_id},
        importance=0.8
    )
    
    # Retrieve relevant context
    context = await memory.retrieve(
        query="user preferences project",
        limit=5
    )
    
    # Use context in response
    response = generate_response(context)
    
    # Learn from interaction
    await memory.store(
        key="successful_response",
        value=f"Pattern: {response.pattern}",
        memory_type=MemoryType.LONG_TERM,
        importance=0.7
    )
    
    # Cleanup
    await memory.stop()
```

## Next Steps

- Explore [Memory API Reference](../api/memory.md)
- Learn about [Advanced Memory Patterns](./advanced-memory.md)
- See [Memory Integration Examples](../examples/memory/)
- Read about [Performance Optimization](./memory-performance.md)
