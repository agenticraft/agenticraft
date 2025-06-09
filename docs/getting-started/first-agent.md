# Your First Agent

Let's create your first AI agent with AgentiCraft in just a few lines of code.

## Basic Agent

```python
from agenticraft import Agent

# Create an agent
agent = Agent(name="Assistant", model="gpt-4")

# Have a conversation
response = agent.run("Hello! What can you help me with today?")
print(response)
```

## Agent with Capabilities

```python
from agenticraft.agents import WorkflowAgent

# Define handler functions for capabilities
def calculate_handler(agent, step, context):
    """Handler for mathematical calculations."""
    expression = context.get("expression", "")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        context["result"] = result
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {e}"

# Create agent with handlers
agent = WorkflowAgent(
    name="MathBot",
    model="gpt-4",
    instructions="You are a helpful math assistant."
)

# Register the handler
agent.register_handler("calculate", calculate_handler)

# Create a workflow
workflow = agent.create_workflow("math_help")
workflow.add_step(
    name="calculation",
    handler="calculate",
    action="Performing calculation..."
)

# Execute with context
context = {"expression": "42 * 17"}
result = await agent.execute_workflow(workflow, context=context)
print(result)
```

## Agent with Memory

```python
from agenticraft import Agent

# Agent with conversation memory
agent = Agent(
    name="MemoryBot",
    model="gpt-4",
    memory_enabled=True
)

# First interaction
agent.run("My name is Alice")

# Agent remembers context
response = agent.run("What's my name?")
print(response)  # Will remember "Alice"
```

## Provider Switching

```python
from agenticraft import Agent

# Start with GPT-4
agent = Agent(name="FlexBot", model="gpt-4")
response = agent.run("Write a haiku")

# Switch to Claude
agent.set_provider("anthropic", model="claude-3-opus-20240229")
response = agent.run("Write another haiku")

# Switch to local Ollama
agent.set_provider("ollama", model="llama2")
response = agent.run("One more haiku")
```

## Simple Workflow Example

```python
from agenticraft.agents import WorkflowAgent

# Create an agent
agent = WorkflowAgent(
    name="ProcessorBot",
    instructions="You help process data step by step."
)

# Define handlers for each step
def load_data_handler(agent, step, context):
    # Simulate loading data
    data = ["item1", "item2", "item3"]
    context["data"] = data
    return f"Loaded {len(data)} items"

def process_data_handler(agent, step, context):
    data = context.get("data", [])
    processed = [item.upper() for item in data]
    context["processed"] = processed
    return f"Processed {len(processed)} items"

def save_data_handler(agent, step, context):
    processed = context.get("processed", [])
    # Simulate saving
    context["saved"] = True
    return f"Saved {len(processed)} items"

# Register handlers
agent.register_handler("load", load_data_handler)
agent.register_handler("process", process_data_handler)
agent.register_handler("save", save_data_handler)

# Create workflow
workflow = agent.create_workflow("data_pipeline")
workflow.add_step(name="load", handler="load")
workflow.add_step(name="process", handler="process", depends_on=["load"])
workflow.add_step(name="save", handler="save", depends_on=["process"])

# Execute
result = await agent.execute_workflow(workflow)
print("Pipeline complete!", result)
```

## Next Steps

- [Explore advanced agents](../features/advanced_agents.md)
- [Learn about handlers](../concepts/handlers.md)
- [Build workflows](../concepts/workflows.md)