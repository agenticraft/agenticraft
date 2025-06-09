# AgentiCraft Tool Usage Status Report

> 💡 **Looking for workarounds?** See the [Tool Usage Patterns Guide](/docs/guides/tool-usage-patterns.md) for reliable patterns that work with the current framework.

## Current Issues with @tool Decorator

The AgentiCraft framework has critical issues with tool message formatting when using OpenAI's API. These issues are at the framework level and cannot be fixed in user code.

### Specific Errors Encountered:

1. **Tool Message Ordering Error**
   ```
   "Invalid parameter: messages with role 'tool' must be a response to a preceeding message with 'tool_calls'"
   ```
   - The framework incorrectly places tool response messages in the conversation history

2. **Missing Tool Call Type**
   ```
   "Missing required parameter: 'messages[2].tool_calls[0].type'"
   ```
   - The framework doesn't include the required 'type' field in tool_calls

3. **Array Schema Generation**
   ```
   "Invalid schema for function 'analyze_weather_data': array schema missing items"
   ```
   - The framework doesn't properly generate schemas for List[T] parameters

## Attempted Workarounds (All Failed):

1. ❌ Using string parameters instead of List[Dict]
2. ❌ JSON serialization for complex data types
3. ❌ Sequential step execution to minimize tool calls
4. ❌ Custom message ordering patches

## What Works:

✅ **Workflows WITHOUT tools** - See `workflow_agent_no_tools.py`
- Sequential execution with dependencies
- Parallel step execution
- Conditional logic
- Custom handlers
- Data flow between steps

## What Doesn't Work:

❌ **Any example using @tool decorator with OpenAI**
- `workflow_agent_example.py`
- `workflow_agent_working.py`
- Any workflow that includes tool usage

## Recommendations:

### For Users:
- Use `workflow_agent_no_tools.py` for workflow demonstrations
- Avoid @tool decorator until framework is fixed
- Use agent reasoning to simulate tool functionality

### For Framework Team:
Fix these core issues in the tool handling code:
1. Ensure tool messages immediately follow their corresponding tool_calls
2. Add 'type': 'function' to all tool_call objects
3. Properly generate OpenAI schemas for array parameters with 'items' field
4. Test all examples with actual OpenAI API before release

## Example of Working Code (No Tools):

```python
# Works reliably
workflow.add_step(
    name="analyze_data",
    action="Analyze the provided data and return insights as JSON"
)

# Doesn't work - causes errors
@tool
def analyze_data(data: List[Dict]) -> Dict:
    return {"result": "analysis"}
```

Until these framework issues are resolved, users should avoid tool usage in AgentiCraft when using OpenAI as the provider.
