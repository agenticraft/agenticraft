# Agent Examples

This directory contains examples demonstrating different types of agents and workflows in AgentiCraft.

```
📁 agents/
├── workflow_simple_example.py    # Start here - basic workflow introduction
├── workflow_with_handlers.py     # Tool functionality using handlers (recommended)
├── workflow_with_wrappers.py     # Tool functionality using wrapper pattern
├── workflow_features_demo.py     # All workflow features demonstration
├── reasoning_agent_example.py    # Advanced: reasoning patterns
└── combined_agents_example.py    # Advanced: multi-agent coordination
```

## Getting Started

### Basic Examples

#### 1. `workflow_simple_example.py` 
**Start here if you're new to AgentiCraft workflows.**

Learn the basics:
- Creating a simple workflow
- Adding steps with dependencies
- Basic agent configuration

#### 2. `workflow_with_handlers.py` (RECOMMENDED)
**The standard approach for implementing tool functionality.**

Learn how to:
- Use handlers for tool-like functionality
- Pass data between workflow steps
- Build real-world workflows (weather analysis, data processing)

**Key Pattern:**
```python
def process_data_handler(agent, step, context):
    """Handler functions replace traditional tool decorators."""
    data = context.get("data", [])
    result = {"sum": sum(data), "avg": sum(data) / len(data)}
    context["result"] = result
    return f"Processed {len(data)} items"

agent.register_handler("process", process_data_handler)
```

#### 3. `workflow_with_wrappers.py`
**Alternative pattern using wrapper classes.**

Learn how to:
- Organize multiple tools with wrapper classes
- Create reusable tool patterns
- Structure larger projects

#### 4. `workflow_features_demo.py`
**Comprehensive demonstration of workflow capabilities.**

Explore advanced features:
- Sequential and parallel execution
- Conditional logic
- Custom handlers
- Complex multi-step processes

### Advanced Examples

#### `reasoning_agent_example.py`
**Advanced reasoning patterns for complex decision-making.**

Demonstrates:
- Chain of Thought (CoT) reasoning
- ReAct pattern for action planning
- Self-reflection and improvement

#### `combined_agents_example.py`
**Coordinating multiple specialized agents.**

Demonstrates:
- Multi-agent architectures
- Agent communication patterns
- Specialized agent roles

## Quick Start Guide

```python
from agenticraft.agents import WorkflowAgent

# 1. Create an agent
agent = WorkflowAgent(
    name="DataProcessor",
    instructions="You process data through multiple steps"
)

# 2. Define handlers for your tools
def fetch_data_handler(agent, step, context):
    # Your tool logic here
    data = load_data_from_source()
    context["raw_data"] = data
    return f"Loaded {len(data)} records"

def analyze_data_handler(agent, step, context):
    data = context.get("raw_data", [])
    analysis = perform_analysis(data)
    context["results"] = analysis
    return "Analysis complete"

# 3. Register handlers
agent.register_handler("fetch", fetch_data_handler)
agent.register_handler("analyze", analyze_data_handler)

# 4. Create workflow
workflow = agent.create_workflow("data_pipeline")
workflow.add_step(name="load", handler="fetch")
workflow.add_step(name="process", handler="analyze", depends_on=["load"])

# 5. Execute
result = await agent.execute_workflow(workflow)
```

## Key Concepts

### Handlers: The Core Pattern

Handlers are functions that implement your tool logic:

```python
def my_handler(agent, step, context):
    # Inputs: get from context
    input_data = context.get("input_key")
    
    # Processing: your logic here
    result = process_somehow(input_data)
    
    # Outputs: store in context
    context["output_key"] = result
    
    # Return: status message
    return f"Processed successfully: {result}"
```

### Context: Data Flow Between Steps

The context dictionary carries data through your workflow:

```python
# Initial context
context = {
    "config": {"temperature": 0.7},
    "user_input": "Analyze this data"
}

# Modified by handlers
def step1_handler(agent, step, context):
    context["step1_result"] = "processed"
    
def step2_handler(agent, step, context):
    prev = context.get("step1_result")  # Access previous results
```

### Workflow Patterns

**Sequential Execution:**
```python
workflow.add_step(name="A", handler="handler_a")
workflow.add_step(name="B", handler="handler_b", depends_on=["A"])
workflow.add_step(name="C", handler="handler_c", depends_on=["B"])
```

**Parallel Execution:**
```python
workflow.add_step(name="A", handler="handler_a")
workflow.add_step(name="B", handler="handler_b", parallel=True)
workflow.add_step(name="C", handler="handler_c", parallel=True)
workflow.add_step(name="D", handler="handler_d", depends_on=["B", "C"])
```

**Conditional Execution:**
```python
def check_condition(agent, step, context):
    context["should_proceed"] = some_condition()
    
workflow.add_step(name="check", handler="check_condition")
workflow.add_step(
    name="conditional_step",
    handler="handler",
    depends_on=["check"],
    condition="should_proceed == True"
)
```

## Running the Examples

```bash
# Set your API key
export OPENAI_API_KEY='your-api-key'

# Basic examples (start here)
python workflow_simple_example.py
python workflow_with_handlers.py

# Explore more patterns
python workflow_with_wrappers.py
python workflow_features_demo.py

# Advanced examples
python reasoning_agent_example.py
python combined_agents_example.py
```

## Best Practices

1. **Use handlers for tool functionality** - They're reliable and give you full control
2. **Pass data via context** - Don't rely on global state
3. **Make handlers focused** - Each handler should do one thing well
4. **Handle errors gracefully** - Use try/except in handlers
5. **Return descriptive messages** - Help with debugging

## Common Patterns

### Data Processing Pipeline
```python
workflow.add_step(name="fetch", handler="fetch_data")
workflow.add_step(name="validate", handler="validate_data", depends_on=["fetch"])
workflow.add_step(name="transform", handler="transform_data", depends_on=["validate"])
workflow.add_step(name="save", handler="save_results", depends_on=["transform"])
```

### Multi-Source Aggregation
```python
# Parallel fetching
workflow.add_step(name="fetch_api1", handler="api1_handler", parallel=True)
workflow.add_step(name="fetch_api2", handler="api2_handler", parallel=True)
workflow.add_step(name="fetch_db", handler="db_handler", parallel=True)

# Combine results
workflow.add_step(
    name="aggregate",
    handler="combine_handler",
    depends_on=["fetch_api1", "fetch_api2", "fetch_db"]
)
```

### Error Handling
```python
def safe_handler(agent, step, context):
    try:
        result = risky_operation()
        context["success"] = True
        context["result"] = result
        return f"Success: {result}"
    except Exception as e:
        context["success"] = False
        context["error"] = str(e)
        return f"Error: {e}"
```

## Next Steps

1. Start with `workflow_simple_example.py` to understand basics
2. Move to `workflow_with_handlers.py` for real-world patterns
3. Explore `workflow_features_demo.py` for advanced features
4. Check advanced examples when ready for complex scenarios

Happy building with AgentiCraft! 🚀