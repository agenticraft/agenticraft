# Examples

Learn by example with practical AgentiCraft demonstrations.

## Quick Start Examples

### [Hello World](hello-world.md)
The simplest possible agent - perfect for getting started.

### [Basic Chat](hello-world.md#basic-chat)
Build a conversational AI in minutes.

## Feature Showcases

### [Provider Switching](provider-switching.md)
- Runtime provider changes
- Cost optimization strategies
- Automatic failover

### [Advanced Agents](advanced-agents.md)
- ReasoningAgent with transparent thinking
- WorkflowAgent for complex processes
- Combining agent types

### [Reasoning Patterns](../features/reasoning_patterns.md)
- Chain of Thought for step-by-step analysis
- Tree of Thoughts for exploring alternatives
- ReAct for tool-based reasoning

## Real-World Applications

### [Customer Support Bot](real-world.md#customer-support)
Multi-provider support agent with knowledge base integration.

### [Data Analysis Pipeline](real-world.md#data-analysis)
Workflow agent that processes data through multiple stages.

### [Content Generator](real-world.md#content-generator)
ReasoningAgent that creates high-quality content with citations.

## Code Snippets

### Dynamic Model Selection
```python
# Use expensive model for complex tasks
if task.complexity > 0.7:
    agent.set_provider("anthropic", model="claude-3-opus-20240229")
else:
    agent.set_provider("ollama", model="llama2")
```

### Error Recovery
```python
try:
    response = agent.run(prompt)
except ProviderError:
    # Automatic failover
    agent.set_provider("ollama", model="llama2")
    response = agent.run(prompt)
```

### Tool Integration
```python
@tool
def search(query: str) -> str:
    """Search the web."""
    # Implementation
    
agent = Agent("SearchBot", tools=[search])
```

## Running the Examples

1. Clone the repository:
   ```bash
   git clone https://github.com/agenticraft/agenticraft
   cd agenticraft/examples
   ```

2. Install dependencies:
   ```bash
   pip install agenticraft
   ```

3. Set up API keys:
   ```bash
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   ```

4. Run examples:
   ```bash
   python hello_world.py
   python provider_switching/basic.py
   ```

## Reasoning Pattern Examples

### Chain of Thought
```python
from agenticraft.agents.reasoning import ReasoningAgent

agent = ReasoningAgent(
    name="Analyst",
    reasoning_pattern="chain_of_thought"
)

response = await agent.think_and_act(
    "Calculate the ROI of solar panels over 10 years"
)

# See step-by-step reasoning
for step in response.reasoning_steps:
    print(f"{step.number}. {step.description} ({step.confidence:.0%})")
```

### Tree of Thoughts
```python
agent = ReasoningAgent(
    name="Designer",
    reasoning_pattern="tree_of_thoughts",
    pattern_config={"beam_width": 4}
)

response = await agent.think_and_act(
    "Design a user-friendly mobile app for seniors"
)

# Visualize exploration tree
print(agent.advanced_reasoning.visualize_tree())
```

### ReAct Pattern
```python
from agenticraft.tools import SearchTool, CalculatorTool

agent = ReasoningAgent(
    name="Researcher",
    reasoning_pattern="react",
    tools=[SearchTool(), CalculatorTool()]
)

response = await agent.think_and_act(
    "What's the current GDP per capita of Japan in USD?"
)

# See thought-action-observation cycles
for step in response.reasoning_steps:
    if step.tool_used:
        print(f"Used {step.tool_used}: {step.tool_input}")
```

### Pattern Comparison
```python
# Compare patterns on the same problem
patterns = ["chain_of_thought", "tree_of_thoughts", "react"]
results = {}

for pattern in patterns:
    agent = ReasoningAgent(reasoning_pattern=pattern)
    response = await agent.think_and_act("Solve: 2x + 5 = 15")
    results[pattern] = {
        "answer": response.content,
        "steps": len(response.reasoning_steps),
        "confidence": response.confidence
    }

# Analyze which pattern worked best
for pattern, result in results.items():
    print(f"{pattern}: {result['steps']} steps, {result['confidence']:.0%} confidence")
```

## Contributing Examples

Have a cool use case? We'd love to see it! Share your examples on [GitHub](https://github.com/agenticraft/agenticraft).
