# Reasoning

Reasoning systems in AgentiCraft provide transparency and explainability in how agents arrive at their conclusions.

## Understanding Agent Reasoning

Traditional LLMs operate as black boxes. AgentiCraft's reasoning systems make the thought process visible and auditable.

## ReasoningAgent

The `ReasoningAgent` provides step-by-step reasoning traces:

```python
from agenticraft import ReasoningAgent

agent = ReasoningAgent(
    name="LogicalBot",
    model="gpt-4"
)

response = agent.run("Should I invest in solar panels for my home?")

print("Reasoning steps:")
for i, step in enumerate(response.reasoning):
    print(f"{i+1}. {step}")
    
print(f"\nConclusion: {response.content}")
print(f"Confidence: {response.confidence}")
```

Output:
```
Reasoning steps:
1. Consider the initial investment cost of solar panels
2. Evaluate average sunlight hours in the user's location
3. Calculate potential energy savings over time
4. Factor in available tax incentives and rebates
5. Assess environmental impact and benefits
6. Compare ROI with alternative investments

Conclusion: Based on these factors...
Confidence: 0.85
```

## Advanced Reasoning Patterns (v0.2.0)

AgentiCraft now includes three sophisticated reasoning patterns. For detailed documentation, see:
- [Feature Overview](../features/reasoning_patterns.md)
- [API Reference](../api/reasoning/index.md)
- [Integration Guide](../guides/reasoning-integration.md)

## Reasoning Features

### Chain of Thought
Break down complex problems into logical steps:

```python
agent = ReasoningAgent(
    name="ProblemSolver",
    reasoning_pattern="chain_of_thought"  # Updated in v0.2.0
)
```

### Tree of Thought
Explore multiple reasoning paths:

```python
agent = ReasoningAgent(
    name="Explorer",
    reasoning_pattern="tree_of_thoughts",  # Updated in v0.2.0
    pattern_config={
        "beam_width": 3,  # Number of branches to explore
        "max_depth": 4
    }
)
```

### Self-Reflection
Agent critiques its own reasoning:

```python
agent = ReasoningAgent(
    name="ReflectiveBot",
    enable_self_critique=True
)

response = agent.run("Analyze this business proposal")
# Includes self-critique in reasoning steps
```

## Reasoning Transparency

### Assumption Tracking
Identify and list assumptions made:

```python
response = agent.run("Predict next quarter's revenue")

print("Assumptions made:")
for assumption in response.assumptions:
    print(f"- {assumption}")
```

### Uncertainty Quantification
Express confidence levels:

```python
response = agent.run("Diagnose this technical issue")

if response.confidence < 0.7:
    print("Low confidence - seeking additional information")
    # Gather more data
```

### Evidence Citation
Link conclusions to evidence:

```python
agent = ReasoningAgent(
    name="ResearchBot",
    cite_sources=True
)

response = agent.run("What causes climate change?")
# Each reasoning step includes evidence
```

## Reasoning Patterns

### Deductive Reasoning
From general to specific:

```python
agent.run("If all birds can fly, and a penguin is a bird, can penguins fly?")
# Shows logical deduction process
```

### Inductive Reasoning
From specific to general:

```python
agent.run("Based on these customer reviews, what can we conclude?")
# Identifies patterns and generalizations
```

### Abductive Reasoning
Best explanation for observations:

```python
agent.run("The server is down and users report slow responses. What's the likely cause?")
# Generates plausible explanations
```

## Debugging with Reasoning

Use reasoning traces to debug agent behavior:

```python
# Enable verbose reasoning
agent = ReasoningAgent(
    name="DebugBot",
    verbose_reasoning=True,
    include_alternatives=True
)

response = agent.run("Complex task...")

# Analyze decision points
for decision in response.decision_points:
    print(f"Decision: {decision.question}")
    print(f"Chosen: {decision.chosen}")
    print(f"Alternatives: {decision.alternatives}")
```

## Best Practices

1. **Use for Critical Decisions**: Enable reasoning for high-stakes choices
2. **Balance Detail**: More reasoning steps increase transparency but cost
3. **Validate Reasoning**: Check logical consistency
4. **Document Assumptions**: Make implicit assumptions explicit
5. **Monitor Confidence**: Set thresholds for automated decisions

## Combining with Other Features

### Reasoning + Provider Switching
```python
# Use expensive model for complex reasoning
agent.set_provider("anthropic", model="claude-3-opus-20240229")
complex_response = agent.run("Analyze this legal document")

# Switch to cheaper model for summary
agent.set_provider("ollama", model="llama2")
summary = agent.run("Summarize the analysis")
```

### Reasoning + Workflows
```python
reasoning_workflow = [
    Step("analyze", "Analyze the problem"),
    Step("reason", "Generate reasoning trace"),
    Step("critique", "Self-critique reasoning"),
    Step("conclude", "Form conclusion")
]
```

## Next Steps

- [Explore ReasoningAgent](../features/advanced_agents.md#reasoningagent)
- [Learn about memory systems](memory.md)
- [See reasoning examples](../examples/provider-switching.md)
