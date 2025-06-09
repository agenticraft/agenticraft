# Reasoning Patterns Quick Reference

## Pattern Selection

```python
# Automatic selection
from agenticraft.agents.reasoning import ReasoningAgent

agent = ReasoningAgent(name="SmartAgent")
response = await agent.think_and_act("Your query")  # Auto-selects pattern

# Manual selection
agent = ReasoningAgent(
    name="Agent",
    reasoning_pattern="chain_of_thought"  # or "tree_of_thoughts", "react"
)
```

## Quick Comparison

| Pattern | Best For | Speed | Memory | Key Feature |
|---------|----------|-------|--------|-------------|
| **Chain of Thought** | Math, logic, explanations | Fast (~50-150ms) | Low | Step-by-step with confidence |
| **Tree of Thoughts** | Design, creativity, options | Medium (~200-500ms) | High | Explores multiple paths |
| **ReAct** | Research, data, troubleshooting | Variable | Medium | Combines reasoning + tools |

## Chain of Thought

```python
# Basic usage
agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    pattern_config={
        "min_confidence": 0.7,  # Minimum step confidence
        "max_steps": 10        # Maximum reasoning steps
    }
)

response = await agent.think_and_act("Explain how X works")

# Access reasoning
for step in response.reasoning_steps:
    print(f"{step.number}. {step.description} ({step.confidence:.0%})")
```

**When to use**: Sequential problems, calculations, explanations
**Avoid for**: Creative tasks, multiple valid solutions

## Tree of Thoughts

```python
# Basic usage
agent = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "max_depth": 4,          # Tree depth
        "beam_width": 3,         # Branches per level
        "exploration_factor": 0.3, # Creativity (0-1)
        "pruning_threshold": 0.4  # Cut bad branches
    }
)

response = await agent.think_and_act("Design a mobile app")

# Visualize exploration
tree = agent.advanced_reasoning.visualize_tree()
print(tree)
```

**When to use**: Design, strategy, comparison, creativity
**Avoid for**: Simple questions, time-critical tasks

## ReAct Pattern

```python
# Basic usage with tools
from agenticraft.tools import SearchTool, CalculatorTool

agent = ReasoningAgent(
    reasoning_pattern="react",
    tools=[SearchTool(), CalculatorTool()],
    pattern_config={
        "max_steps": 15,         # Total steps allowed
        "max_retries": 2,        # Tool retry attempts  
        "reflection_frequency": 3 # Reflect every N steps
    }
)

response = await agent.think_and_act("Research topic X")

# See what happened
for step in response.reasoning_steps:
    if step.tool_used:
        print(f"{step.step_type}: Used {step.tool_used}")
```

**When to use**: Current info needed, calculations, research
**Avoid for**: Pure reasoning, no tools available

## Common Configurations

### High Confidence (Slower, More Thorough)
```python
high_confidence = {
    "chain_of_thought": {"min_confidence": 0.9, "max_steps": 20},
    "tree_of_thoughts": {"beam_width": 5, "pruning_threshold": 0.6},
    "react": {"max_retries": 3, "reflection_frequency": 2}
}
```

### Fast Processing (Quick Results)
```python
fast_processing = {
    "chain_of_thought": {"max_steps": 5},
    "tree_of_thoughts": {"max_depth": 2, "beam_width": 2},
    "react": {"max_steps": 8, "max_retries": 1}
}
```

### Creative/Exploratory
```python
exploratory = {
    "tree_of_thoughts": {
        "max_depth": 6,
        "beam_width": 4,
        "exploration_factor": 0.5,  # More random
        "pruning_threshold": 0.2    # Keep more options
    }
}
```

## Pattern Selection Rules

```python
# Simple heuristic
def select_pattern(query: str) -> str:
    query_lower = query.lower()
    
    # ReAct indicators
    if any(word in query_lower for word in ["find", "search", "current", "latest"]):
        return "react"
    
    # Tree of Thoughts indicators  
    if any(word in query_lower for word in ["design", "create", "compare", "alternatives"]):
        return "tree_of_thoughts"
    
    # Default to Chain of Thought
    return "chain_of_thought"
```

## Accessing Pattern Results

```python
# Common for all patterns
response = await agent.think_and_act(query)

# Basic info
print(f"Answer: {response.content}")
print(f"Pattern used: {agent.reasoning_pattern_name}")
print(f"Steps taken: {len(response.reasoning_steps)}")

# Average confidence
avg_conf = sum(s.confidence for s in response.reasoning_steps) / len(response.reasoning_steps)
print(f"Confidence: {avg_conf:.0%}")

# Pattern-specific
if agent.reasoning_pattern_name == "tree_of_thoughts":
    # Get best paths
    best = agent.advanced_reasoning.get_best_solution()
    print(f"Best path score: {best['score']}")
    
elif agent.reasoning_pattern_name == "react":
    # Get tool usage
    tools_used = set(s.tool_used for s in response.reasoning_steps if s.tool_used)
    print(f"Tools used: {tools_used}")
```

## Debugging Tips

```python
# Enable verbose output
agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    verbose=True  # Show reasoning process
)

# Check pattern performance
import time
start = time.time()
response = await agent.think_and_act(query)
print(f"Time: {time.time() - start:.2f}s")

# Analyze low confidence
low_conf = [s for s in response.reasoning_steps if s.confidence < 0.5]
if low_conf:
    print(f"Warning: {len(low_conf)} low-confidence steps")
```

## Combining Patterns

```python
# Multi-stage reasoning
async def complex_task(problem: str):
    # 1. Research phase
    researcher = ReasoningAgent(reasoning_pattern="react", tools=[SearchTool()])
    data = await researcher.think_and_act(f"Research: {problem}")
    
    # 2. Creative phase  
    designer = ReasoningAgent(reasoning_pattern="tree_of_thoughts")
    options = await designer.think_and_act(f"Given {data.content}, design solutions")
    
    # 3. Analysis phase
    analyst = ReasoningAgent(reasoning_pattern="chain_of_thought")
    plan = await analyst.think_and_act(f"Analyze and detail: {options.content}")
    
    return plan
```

## Error Handling

```python
try:
    response = await agent.think_and_act(query)
except Exception as e:
    # Pattern-specific handling
    if agent.reasoning_pattern_name == "react":
        print("Tool error - check tool availability")
    elif agent.reasoning_pattern_name == "tree_of_thoughts":
        print("Exploration failed - try simpler query")
    else:
        print("Reasoning error - check query complexity")
```

## Performance Tips

1. **Cache common queries** - Reasoning can be expensive
2. **Use appropriate patterns** - Don't use ToT for simple questions
3. **Configure for your needs** - Balance speed vs quality
4. **Monitor confidence** - Low confidence may need different pattern
5. **Batch similar queries** - Process multiple queries efficiently

## Quick Migration

```python
# From basic agent
old_agent = Agent(name="Bot", reasoning=True)

# To reasoning agent
new_agent = ReasoningAgent(
    name="Bot",
    reasoning_pattern="chain_of_thought"  # Start with CoT
)
```

Need more details? See the [full documentation](../api/reasoning/index.md).
