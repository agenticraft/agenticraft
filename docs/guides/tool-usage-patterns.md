# Tool Usage Patterns in AgentiCraft

## ⚠️ Quick Summary

### The Problem

The direct tool calling feature in AgentiCraft has a bug where tool response messages aren't properly formatted for the OpenAI API, causing this error:
```
Invalid parameter: messages with role 'tool' must be a response to a preceding message with 'tool_calls'.
```

### The Solutions

#### 1. **WorkflowAgent with Handlers** (Most Reliable)
See: `examples/agents/workflow_with_handlers.py`

```python
agent = WorkflowAgent(name="MyAgent")

def my_handler(agent, step, context):
    # Your tool logic here
    result = do_something(context.get("input"))
    context["output"] = result
    return f"Done: {result}"

agent.register_handler("my_tool", my_handler)
```

#### 2. **Tool Wrapper Pattern** (Clean & Reusable)
See: `examples/agents/workflow_with_wrappers.py`

```python
class ToolWrapper:
    def __init__(self, name, func):
        self.name = name
        self.func = func
    
    def create_handler(self):
        def handler(agent, step, context):
            params = context.get(f"{self.name}_params", {})
            result = self.func(**params)
            context[f"{self.name}_result"] = result
            return str(result)
        return handler

# Use it
tool = ToolWrapper("calculate", lambda x, y: x + y)
agent.register_handler("calc", tool.create_handler())
```

#### 3. **Direct LLM Calculation** (Simple Cases)
For basic calculations, just ask the LLM:

```python
agent = Agent(provider="openai", model="gpt-4")
response = await agent.arun("Calculate 15% of 850 (show your work)")
print(response.content)  # LLM does the math
```

### What NOT to Do

❌ Don't use `@tool` decorator with regular agents  
❌ Don't use `agent.add_tool()`  
❌ Don't rely on built-in tools like `simple_calculate` with regular agents  

### Recommendation

For production use, always use **WorkflowAgent with handlers**. This pattern:
- Works reliably
- Gives you full control
- Avoids framework bugs
- Is well-tested

---

## Complete Guide

Based on the examples and actual framework implementation, here's how tools work in AgentiCraft:

## ⚠️ Important Note: Tool Calling Limitations

The current implementation of tool calling in AgentiCraft has known issues, particularly with the message flow required by OpenAI's API. The framework may encounter errors like:
```
Invalid parameter: messages with role 'tool' must be a response to a preceding message with 'tool_calls'.
```

**Recommendation**: Use one of the reliable patterns below instead of direct tool calling.

## Reliable Patterns for Tool Usage

### 1. WorkflowAgent with Handlers (Recommended)

The most reliable approach is using WorkflowAgent with handlers:

```python
from agenticraft.agents import WorkflowAgent

# Create agent
agent = WorkflowAgent(
    name="DataProcessor",
    instructions="Process data through multiple steps"
)

# Define handler function
def calculate_handler(agent, step, context):
    expression = context.get("expression", "")
    result = eval(expression, {"__builtins__": {}}, {})
    context["result"] = result
    return f"Calculated: {expression} = {result}"

# Register handler
agent.register_handler("calculate", calculate_handler)

# Create workflow
workflow = agent.create_workflow("math_workflow")
workflow.add_step(name="calc", handler="calculate")

# Execute
context = {"expression": "2 + 2"}
result = await agent.execute_workflow(workflow, context=context)
```

### 2. Tool Wrapper Pattern (Clean & Reusable)

For a more structured approach, use the ToolWrapper pattern:

```python
class SimpleToolWrapper:
    """Wrapper to make tools work reliably with agents."""
    
    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func
    
    def create_handler(self):
        """Create a handler for the tool."""
        def handler(agent, step, context):
            params = context.get(f"{self.name}_params", {})
            try:
                result = self.func(**params)
                context[f"{self.name}_result"] = result
                return f"Result: {result}"
            except Exception as e:
                return f"Error: {e}"
        return handler

# Define your tool function
def calculate(expression: str) -> float:
    return eval(expression, {"__builtins__": {}}, {})

# Create wrapper and use it
calc_tool = SimpleToolWrapper("calculate", calculate)
agent.register_handler("calc", calc_tool.create_handler())
```

### 3. Direct LLM Calculation (Simple Cases)

For simple calculations, just let the LLM handle it:

```python
from agenticraft import Agent

agent = Agent(
    name="Assistant",
    provider="openai",
    model="gpt-4"
)

# No tools needed - LLM can calculate
response = await agent.arun("Calculate 15% of 850 (show your work)")
print(response.content)  # LLM will show the calculation
```

### Available Built-in Tools (Currently Problematic)
- **Calculator Tools**: `simple_calculate`, `scientific_calculate`
- **File Tools**: `read_file`, `write_file`, `read_json`, `write_json`, `list_files`, `file_info`
- **Web Tools**: `web_search`, `extract_text`, `get_page_metadata`, `check_url`

*Note: These tools exist but have integration issues with the current framework.*

## Complete Example: Weather Analysis with Tools

Here's a complete example using the wrapper pattern:

```python
import asyncio
from agenticraft.agents import WorkflowAgent

class ToolWrapper:
    def __init__(self, name, func):
        self.name = name
        self.func = func
    
    def create_handler(self):
        def handler(agent, step, context):
            params = context.get(f"{self.name}_params", {})
            result = self.func(**params)
            context[f"{self.name}_result"] = result
            return str(result)
        return handler

# Define tools
def fetch_weather(city: str) -> dict:
    # Mock weather data
    return {"city": city, "temp": 72, "conditions": "Sunny"}

def analyze_temps(cities_data: list) -> dict:
    temps = [d["temp"] for d in cities_data]
    return {"avg": sum(temps) / len(temps), "max": max(temps)}

# Create agent and register tools
agent = WorkflowAgent(name="WeatherBot")

weather_tool = ToolWrapper("weather", fetch_weather)
analyze_tool = ToolWrapper("analyze", analyze_temps)

agent.register_handler("fetch", weather_tool.create_handler())
agent.register_handler("analyze", analyze_tool.create_handler())

# Create workflow
workflow = agent.create_workflow("weather_analysis")
workflow.add_step(name="fetch_ny", handler="fetch")
workflow.add_step(name="fetch_la", handler="fetch", depends_on=["fetch_ny"])
workflow.add_step(name="analyze", handler="analyze", depends_on=["fetch_la"])

# Execute
context = {
    "weather_params": {"city": "New York"},  # for first fetch
    "cities_data": []  # will be populated
}

result = await agent.execute_workflow(workflow, context=context)
```

## Key Takeaways

1. **Direct tool calling with `@tool` is broken** - Avoid using it
2. **WorkflowAgent with handlers is the most reliable** - Use this for production
3. **Tool wrapper pattern provides clean abstraction** - Good for reusable tools
4. **Let LLMs calculate directly for simple cases** - Often sufficient

## Migration Path

If you have code using direct tools:

```python
# OLD (broken)
@tool
def my_tool(param: str) -> str:
    return f"Result: {param}"

agent = Agent(tools=[my_tool])
```

Migrate to:

```python
# NEW (working)
agent = WorkflowAgent(name="MyAgent")

def my_tool_handler(agent, step, context):
    param = context.get("param")
    result = f"Result: {param}"
    context["result"] = result
    return result

agent.register_handler("my_tool", my_tool_handler)
```

## Example Files to Reference

- `examples/agents/workflow_with_handlers.py` - Basic handler pattern
- `examples/agents/workflow_with_wrappers.py` - Tool wrapper pattern
- `examples/providers/tool_wrapper_pattern.py` - Complete examples

These patterns work reliably with the current AgentiCraft framework and avoid all the tool calling issues.
