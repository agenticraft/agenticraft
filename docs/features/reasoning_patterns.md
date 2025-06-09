# Advanced Reasoning Patterns

**Released in v0.2.0** - AgentiCraft now includes three sophisticated reasoning patterns that make agent thinking transparent and structured.

## Overview

Traditional LLMs operate as black boxes. AgentiCraft's advanced reasoning patterns provide:

- **Transparency**: See exactly how agents arrive at conclusions
- **Structure**: Organized thinking for different problem types  
- **Confidence**: Know how certain the agent is about each step
- **Flexibility**: Automatic pattern selection or manual control

## Available Patterns

### 🔗 Chain of Thought (CoT)

Linear, step-by-step reasoning perfect for:
- Mathematical problems
- Logical puzzles
- Explanations
- Sequential analysis

```python
from agenticraft.agents.reasoning import ReasoningAgent

agent = ReasoningAgent(
    name="MathTutor",
    reasoning_pattern="chain_of_thought"
)

response = await agent.think_and_act(
    "If a train travels 120 miles in 2 hours, what is its average speed?"
)

# See the reasoning steps
for step in response.reasoning_steps:
    print(f"{step.number}. {step.description}")
    print(f"   Confidence: {step.confidence:.0%}")
```

### 🌳 Tree of Thoughts (ToT)

Multi-path exploration for:
- Creative tasks
- Design problems
- Strategy planning
- Comparing alternatives

```python
agent = ReasoningAgent(
    name="Designer",
    reasoning_pattern="tree_of_thoughts"
)

response = await agent.think_and_act(
    "Design a mobile app for elderly users to stay connected with family"
)

# Visualize the exploration tree
tree = agent.advanced_reasoning.visualize_tree()
print(tree)
```

### 🔄 ReAct (Reason + Act)

Combines thinking with tool usage for:
- Research tasks
- Data analysis
- Information gathering
- Troubleshooting

```python
from agenticraft.tools import SearchTool, CalculatorTool

agent = ReasoningAgent(
    name="Researcher",
    reasoning_pattern="react",
    tools=[SearchTool(), CalculatorTool()]
)

response = await agent.think_and_act(
    "What's the population density of Tokyo?"
)

# See thought → action → observation cycles
for step in response.reasoning_steps:
    print(f"{step.step_type}: {step.description}")
```

## Pattern Selection

### Automatic Selection

Let AgentiCraft choose the best pattern:

```python
agent = ReasoningAgent(name="SmartAgent")

# The agent analyzes the problem and selects the best pattern
pattern = agent.select_best_pattern(
    "Find the current stock price of Apple and calculate the P/E ratio"
)
print(f"Selected: {pattern}")  # Will select 'react'
```

### Selection Guide

| Problem Type | Best Pattern | Why |
|--------------|-------------|-----|
| Math problems | Chain of Thought | Step-by-step progression |
| Explanations | Chain of Thought | Clear, linear reasoning |
| Design tasks | Tree of Thoughts | Multiple options to explore |
| Creative writing | Tree of Thoughts | Various approaches valid |
| Research | ReAct | Needs information gathering |
| Data analysis | ReAct | Requires tools and iteration |

## Configuration Options

### Chain of Thought

```python
agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    pattern_config={
        "min_confidence": 0.7,    # Minimum confidence threshold
        "max_steps": 10          # Maximum reasoning steps
    }
)
```

### Tree of Thoughts

```python
agent = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "max_depth": 4,           # Maximum tree depth
        "beam_width": 3,          # Paths to explore at each level
        "exploration_factor": 0.3, # Balance exploration vs exploitation
        "pruning_threshold": 0.4   # Score below which to prune
    }
)
```

### ReAct

```python
agent = ReasoningAgent(
    reasoning_pattern="react",
    pattern_config={
        "max_steps": 15,          # Maximum reasoning steps
        "max_retries": 2,         # Retries for failed actions
        "reflection_frequency": 3  # Reflect every N steps
    }
)
```

## Understanding the Output

### Reasoning Steps

All patterns provide structured reasoning steps:

```python
response = await agent.think_and_act(query)

# Common attributes for all patterns
for step in response.reasoning_steps:
    print(f"Step {step.number}: {step.description}")
    print(f"Confidence: {step.confidence}")
    print(f"Type: {step.step_type}")
```

### Pattern-Specific Features

#### Chain of Thought
- Confidence tracking per step
- Alternative thoughts for low-confidence steps
- Problem complexity assessment
- Synthesis of all steps

#### Tree of Thoughts
- Visual tree representation
- Multiple solution paths
- Path scoring and ranking
- Pruning statistics

#### ReAct
- Tool usage tracking
- Action-observation cycles
- Progress reflection
- Self-correction

## Performance Characteristics

| Pattern | Simple Task | Complex Task | Memory Usage |
|---------|------------|--------------|--------------|
| CoT | ~50ms | ~150ms | Low |
| ToT | ~200ms | ~500ms | High |
| ReAct | ~100ms | ~300ms + tools | Medium |

## Real-World Examples

### Educational Tutor

```python
# Use Chain of Thought for clear explanations
tutor = ReasoningAgent(
    name="Tutor",
    reasoning_pattern="chain_of_thought",
    instructions="Break down complex concepts into simple steps"
)

lesson = await tutor.think_and_act(
    "Explain how machine learning works to a beginner"
)

# Get structured lesson with confidence levels
for step in lesson.reasoning_steps:
    if step.confidence < 0.8:
        # Generate additional examples for unclear steps
        pass
```

### Creative Designer

```python
# Use Tree of Thoughts to explore design options
designer = ReasoningAgent(
    name="Designer",
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "beam_width": 5,  # Explore more options
        "exploration_factor": 0.4  # Higher creativity
    }
)

designs = await designer.think_and_act(
    "Design a logo for an eco-friendly tech startup"
)

# Get top 3 design paths
best_designs = designer.advanced_reasoning.get_all_solutions()[:3]
```

### Research Analyst

```python
# Use ReAct for data gathering and analysis
analyst = ReasoningAgent(
    name="Analyst",
    reasoning_pattern="react",
    tools=[SearchTool(), DatabaseTool(), CalculatorTool()]
)

analysis = await analyst.think_and_act(
    "Analyze our Q4 performance compared to industry benchmarks"
)

# Track tool usage
for step in analysis.reasoning_steps:
    if step.tool_used:
        print(f"Gathered data using: {step.tool_used}")
```

## Combining Patterns

For complex tasks, combine multiple patterns:

```python
# Stage 1: Research with ReAct
researcher = ReasoningAgent(
    reasoning_pattern="react",
    tools=[SearchTool(), DataTool()]
)
data = await researcher.think_and_act("Gather market data")

# Stage 2: Explore strategies with Tree of Thoughts
strategist = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts"
)
strategies = await strategist.think_and_act(
    f"Based on this data: {data.content}\n"
    "What strategies should we consider?"
)

# Stage 3: Detail the plan with Chain of Thought
planner = ReasoningAgent(
    reasoning_pattern="chain_of_thought"
)
plan = await planner.think_and_act(
    f"Create detailed plan for: {strategies.content}"
)
```

## Best Practices

1. **Choose the Right Pattern**
   - Start with the problem type, not the pattern
   - Consider available resources (time, tools)
   - Think about desired output format

2. **Configure Appropriately**
   - Don't over-configure; start with defaults
   - Adjust based on performance needs
   - Monitor resource usage

3. **Handle Edge Cases**
   ```python
   # Check reasoning quality
   if response.reasoning_steps:
       avg_confidence = sum(s.confidence for s in response.reasoning_steps) / len(response.reasoning_steps)
       if avg_confidence < 0.6:
           # Consider using different pattern
           pass
   ```

4. **Combine with Other Features**
   ```python
   # Use with streaming
   response = await agent.stream(
       problem,
       use_advanced_reasoning=True
   )
   
   # Use with provider switching
   agent.set_provider("anthropic")  # Use powerful model for reasoning
   ```

## Migration from Basic Reasoning

If you're using the basic `reasoning` parameter:

```python
# Old approach
agent = Agent(reasoning=True)

# New approach with advanced patterns
agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought"  # or other patterns
)
```

Benefits of migrating:
- More structured reasoning output
- Pattern-specific optimizations
- Confidence tracking
- Better tool integration

## Troubleshooting

### Common Issues

1. **Pattern gets stuck**: Adjust max_steps or add timeout
2. **Low confidence throughout**: Provide more context or switch patterns
3. **Too slow**: Reduce beam_width (ToT) or max_steps
4. **Wrong pattern selected**: Override automatic selection

### Performance Tips

- Cache reasoning results for common queries
- Use simpler patterns for time-sensitive tasks
- Monitor memory usage with Tree of Thoughts
- Batch similar queries for efficiency

## What's Next

- Explore the [API Reference](../api/reasoning/index.md) for detailed documentation
- Check out [Examples](../examples/reasoning/) for more use cases
- Learn about [Pattern Integration](../guides/reasoning-integration.md)
- Join the [Discord](https://discord.gg/agenticraft) to share your patterns

---

Advanced reasoning patterns make your agents smarter, more transparent, and more capable. Start with automatic pattern selection and refine based on your specific needs.
