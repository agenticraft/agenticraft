# Advanced Agents

AgentiCraft provides specialized agent types for complex use cases.

## ReasoningAgent

The ReasoningAgent makes its thought process transparent and explainable.

```python
from agenticraft import ReasoningAgent

agent = ReasoningAgent(
    name="ThoughtfulBot",
    model="gpt-4"
)

response = agent.run("What are the pros and cons of solar energy?")
print("Reasoning:", response.reasoning)
print("Answer:", response.content)
```

### Features
- Step-by-step reasoning traces
- Explainable decision making
- Confidence scoring
- Assumption tracking

### Use Cases
- Complex problem solving
- Educational applications
- Audit trails for decisions
- Debugging AI behavior

## WorkflowAgent

The WorkflowAgent excels at multi-step processes and task orchestration.

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(
    name="ProcessBot",
    model="gpt-4"
)

# Define workflow
workflow = [
    Step("analyze", "Analyze the user's request"),
    Step("plan", "Create an action plan"),
    Step("execute", "Execute the plan"),
    Step("verify", "Verify the results")
]

response = agent.run_workflow(
    "Help me plan a dinner party for 8 people",
    workflow=workflow
)

# Access individual step results
for step_name, result in response.steps.items():
    print(f"{step_name}: {result}")
```

### Features
- Multi-step execution
- Step dependencies
- Parallel processing
- Progress tracking
- Error recovery

### Use Cases
- Data processing pipelines
- Content generation workflows
- Multi-stage analysis
- Automated workflows

## Combining Advanced Features

```python
from agenticraft import ReasoningAgent

# Create a reasoning agent that can switch providers
agent = ReasoningAgent(
    name="SmartBot",
    model="gpt-4",
    tools=[web_search, calculate]
)

# Use expensive model for complex reasoning
response = agent.run("Analyze the environmental impact of electric vehicles")

# Switch to cheaper model for simple tasks
agent.set_provider("ollama", model="llama2")
response = agent.run("Summarize the previous analysis in 3 points")
```

## Performance Tips

1. **Choose the right agent type**
   - Use base Agent for simple tasks
   - Use ReasoningAgent when transparency matters
   - Use WorkflowAgent for multi-step processes

2. **Optimize provider usage**
   - Use powerful models for complex reasoning
   - Switch to efficient models for simple tasks
   - Use local models for privacy-sensitive data

3. **Design efficient workflows**
   - Break complex tasks into clear steps
   - Parallelize independent steps
   - Cache intermediate results

## Next Steps

- [See advanced examples](../examples/advanced-agents.md)
- [Learn about workflows](../concepts/workflows.md)
- [Optimize performance](../guides/performance-tuning.md)
