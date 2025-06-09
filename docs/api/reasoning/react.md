# ReAct Pattern API Reference

## Overview

ReAct (Reason + Act) combines reasoning with actions, creating a dynamic loop of thinking, acting, observing results, and reflecting on progress. It's designed for tasks requiring external tool usage and iterative problem-solving.

## Class Reference

### ReactReasoning

```python
class ReactReasoning(BaseReasoningPattern):
    """
    Implements ReAct (Reason + Act) pattern.
    
    Combines reasoning with tool actions in a loop:
    Thought → Action → Observation → Reflection
    """
```

#### Initialization

```python
from agenticraft.reasoning.patterns.react import ReactReasoning

react = ReactReasoning(
    tools: List[BaseTool],
    max_steps: int = 15,
    max_retries: int = 2,
    reflection_frequency: int = 3
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | List[BaseTool] | [] | Available tools for actions |
| `max_steps` | int | 15 | Maximum reasoning/action steps |
| `max_retries` | int | 2 | Retries for failed tool calls |
| `reflection_frequency` | int | 3 | Reflect every N steps |

#### Methods

##### reason()

```python
async def reason(
    self,
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> ReasoningTrace
```

Execute ReAct reasoning loop on the query.

**Parameters:**
- `query` (str): The problem requiring reasoning and actions
- `context` (Optional[Dict]): Additional context

**Returns:**
- `ReasoningTrace`: Complete trace of thoughts, actions, and observations

**Example:**

```python
# Define tools
search_tool = SearchTool()
calc_tool = CalculatorTool()

# Create ReAct reasoning
react = ReactReasoning(tools=[search_tool, calc_tool])

# Execute reasoning
trace = await react.reason(
    "What is the population density of Tokyo?"
)

# Access steps
for step in trace.steps:
    print(f"{step.step_type}: {step.description}")
```

##### _generate_thought()

```python
async def _generate_thought(
    self,
    query: str,
    observations: List[ReactStep]
) -> ReactStep
```

Generate a reasoning thought about what to do next.

**Returns:** ReactStep with type THOUGHT

##### _select_action()

```python
def _select_action(
    self,
    thought: str,
    available_tools: List[BaseTool]
) -> Tuple[Optional[BaseTool], Optional[str]]
```

Select appropriate tool and parameters based on thought.

**Returns:** (selected_tool, action_input) or (None, None)

##### _execute_action()

```python
async def _execute_action(
    self,
    tool: BaseTool,
    action_input: str,
    retry_count: int = 0
) -> ReactStep
```

Execute tool action with retry logic.

**Returns:** ReactStep with type ACTION containing result

##### _create_observation()

```python
def _create_observation(
    self,
    action_result: str,
    tool_name: str
) -> ReactStep
```

Create observation from action result.

**Returns:** ReactStep with type OBSERVATION

##### _should_reflect()

```python
def _should_reflect(self, step_count: int) -> bool
```

Determine if reflection is needed.

**Reflection triggers:**
- Every `reflection_frequency` steps
- After errors or low confidence
- When progress stalls

##### _reflect_on_progress()

```python
async def _reflect_on_progress(
    self,
    steps: List[ReactStep],
    original_query: str
) -> ReactStep
```

Analyze progress and adjust strategy.

**Returns:** ReactStep with type REFLECTION

##### _is_complete()

```python
def _is_complete(
    self,
    steps: List[ReactStep],
    query: str
) -> bool
```

Check if the task is complete.

**Completion criteria:**
- Answer fully addresses query
- No more actions needed
- Max steps reached

##### visualize_reasoning()

```python
def visualize_reasoning(self, format: str = "text") -> str
```

Visualize the ReAct process.

**Formats:**
- `"text"`: Sequential step display
- `"mermaid"`: Flow diagram
- `"timeline"`: Time-based visualization

### ReactStep

```python
@dataclass
class ReactStep:
    """Represents a single step in ReAct reasoning."""
    
    step_number: int
    step_type: StepType
    description: str
    content: str
    tool_used: Optional[str]
    tool_input: Optional[str]
    tool_result: Optional[str]
    confidence: float
    timestamp: datetime
    requires_revision: bool
    metadata: Dict[str, Any]
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `step_number` | int | Sequential step number |
| `step_type` | StepType | Type of reasoning step |
| `description` | str | Human-readable description |
| `content` | str | Full content of the step |
| `tool_used` | Optional[str] | Name of tool used (if any) |
| `tool_input` | Optional[str] | Input sent to tool |
| `tool_result` | Optional[str] | Result from tool |
| `confidence` | float | Confidence in step (0.0-1.0) |
| `timestamp` | datetime | When step occurred |
| `requires_revision` | bool | If step needs retry |
| `metadata` | Dict | Additional step data |

### Enums

#### StepType

```python
class StepType(Enum):
    THOUGHT = "thought"        # Reasoning about next action
    ACTION = "action"          # Tool execution
    OBSERVATION = "observation" # Interpreting results
    REFLECTION = "reflection"  # Progress assessment
    CONCLUSION = "conclusion"  # Final answer
```

## Tool Integration

### Creating Tools for ReAct

```python
from agenticraft.core.tool import BaseTool

class DatabaseTool(BaseTool):
    name = "database"
    description = "Query company database"
    
    async def execute(self, query: str) -> str:
        # Execute database query
        results = await self.db.query(query)
        return json.dumps(results)

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform mathematical calculations"
    
    async def execute(self, expression: str) -> str:
        # Safe evaluation
        result = safe_eval(expression)
        return f"Result: {result}"
```

### Tool Selection Strategy

```python
# ReAct automatically selects tools based on:
# 1. Tool descriptions
# 2. Current thought content
# 3. Previous tool success/failure

# Provide clear tool descriptions
search_tool = SearchTool(
    description="Search the web for current information. "
                "Use for: news, facts, real-time data"
)

calc_tool = CalculatorTool(
    description="Perform calculations and mathematical operations. "
                "Use for: arithmetic, statistics, conversions"
)
```

## Usage Examples

### Basic Usage

```python
from agenticraft.agents.reasoning import ReasoningAgent

# Create agent with tools
agent = ReasoningAgent(
    name="Researcher",
    reasoning_pattern="react",
    tools=[SearchTool(), CalculatorTool(), DatabaseTool()]
)

# Execute research task
response = await agent.think_and_act(
    "What is the GDP per capita of Japan compared to our Q4 revenue?"
)

# Access the process
for step in response.reasoning_steps:
    if step.tool_used:
        print(f"Used {step.tool_used}: {step.tool_input}")
        print(f"Got: {step.tool_result}")
```

### Advanced Configuration

```python
# Research-focused configuration
research_react = ReasoningAgent(
    reasoning_pattern="react",
    tools=[SearchTool(), WikiTool(), CalculatorTool()],
    pattern_config={
        "max_steps": 25,          # More steps for research
        "max_retries": 3,         # Robust retries
        "reflection_frequency": 5  # Less frequent reflection
    }
)

# Quick fact-checking
fact_check_react = ReasoningAgent(
    reasoning_pattern="react",
    tools=[SearchTool()],
    pattern_config={
        "max_steps": 8,           # Quick checks
        "max_retries": 1,         # Fast fail
        "reflection_frequency": 4  # Reflect once
    }
)
```

### Error Handling and Retries

```python
# ReAct handles tool failures gracefully
response = await agent.think_and_act(
    "Get the current weather in Tokyo"
)

# Check for retry attempts
failed_steps = [
    s for s in response.reasoning_steps
    if s.requires_revision
]

if failed_steps:
    print(f"Recovered from {len(failed_steps)} failures")
    for step in failed_steps:
        print(f"- {step.tool_used} failed: {step.metadata.get('error')}")
```

### Custom Reflection Logic

```python
class CustomReActReasoning(ReactReasoning):
    async def _reflect_on_progress(self, steps, original_query):
        reflection = await super()._reflect_on_progress(steps, original_query)
        
        # Add custom reflection logic
        tool_usage = {}
        for step in steps:
            if step.tool_used:
                tool_usage[step.tool_used] = tool_usage.get(step.tool_used, 0) + 1
        
        # Warn about tool overuse
        for tool, count in tool_usage.items():
            if count > 3:
                reflection.content += f"\nWarning: {tool} used {count} times. Consider different approach."
        
        return reflection
```

## Advanced Features

### Tool Chaining

```python
# Define tools that work together
class DataExtractorTool(BaseTool):
    name = "extractor"
    description = "Extract structured data from text"
    
class AnalyzerTool(BaseTool):
    name = "analyzer"
    description = "Analyze structured data"
    requires = ["extractor"]  # Indicates dependency

# ReAct will chain tools appropriately
response = await agent.think_and_act(
    "Extract and analyze the data from this report: ..."
)
```

### Parallel Tool Execution

```python
class ParallelReAct(ReactReasoning):
    async def _execute_parallel_actions(
        self,
        actions: List[Tuple[BaseTool, str]]
    ) -> List[ReactStep]:
        """Execute multiple independent actions in parallel."""
        tasks = [
            self._execute_action(tool, input_str)
            for tool, input_str in actions
        ]
        return await asyncio.gather(*tasks)
```

### Tool Result Caching

```python
class CachedReAct(ReactReasoning):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache = {}
    
    async def _execute_action(self, tool, action_input, retry_count=0):
        # Check cache
        cache_key = f"{tool.name}:{action_input}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Execute and cache
        result = await super()._execute_action(tool, action_input, retry_count)
        self.cache[cache_key] = result
        return result
```

## Performance Optimization

### Minimize Tool Calls

```python
# Configure for efficiency
efficient_config = {
    "max_steps": 10,
    "tool_result_cache": True,
    "batch_similar_queries": True
}

# Tools can batch operations
class BatchSearchTool(BaseTool):
    async def execute(self, queries: Union[str, List[str]]) -> str:
        if isinstance(queries, str):
            queries = [queries]
        
        # Batch API call
        results = await self.batch_search(queries)
        return json.dumps(results)
```

### Early Termination

```python
class EfficientReAct(ReactReasoning):
    def _is_complete(self, steps, query):
        # Check if we have enough information
        if self._has_sufficient_answer(steps, query):
            return True
        
        # Check if we're not making progress
        if self._is_stalled(steps):
            return True
        
        return super()._is_complete(steps, query)
```

## Monitoring and Debugging

### Step Analysis

```python
# Analyze ReAct execution
react = agent.advanced_reasoning

# Get summary statistics
summary = react._generate_summary()
print(f"Total steps: {summary['total_steps']}")
print(f"Tool calls: {summary['tool_calls']}")
print(f"Failed actions: {summary['failed_actions']}")
print(f"Reflections: {summary['reflections']}")

# Tool usage breakdown
print("\nTool Usage:")
for tool, count in summary['tools_used'].items():
    print(f"  {tool}: {count} calls")
```

### Execution Timeline

```python
# Visualize execution timeline
timeline = react.visualize_reasoning(format="timeline")
print(timeline)
"""
0:00 | THOUGHT: Need to find current weather
0:01 | ACTION: search_tool("Tokyo weather")
0:03 | OBSERVATION: 23°C, partly cloudy
0:04 | THOUGHT: Convert to Fahrenheit
0:05 | ACTION: calculator("23 * 9/5 + 32")
0:06 | OBSERVATION: 73.4°F
0:07 | REFLECTION: Task complete, both values found
0:08 | CONCLUSION: Tokyo weather is 23°C (73.4°F)
"""
```

## Common Issues and Solutions

### Issue: Tool Selection Loops

**Symptom:** Keeps selecting wrong tool
**Solution:**
```python
# Improve tool descriptions
tools = [
    SearchTool(
        description="Web search for current events, news, facts. "
                   "NOT for calculations or internal data."
    ),
    CalculatorTool(
        description="Mathematical calculations only. "
                   "Examples: arithmetic, percentages, conversions."
    )
]
```

### Issue: Insufficient Progress

**Symptom:** Many steps but little progress
**Solution:**
```python
# Add progress tracking
pattern_config = {
    "reflection_frequency": 2,  # More frequent reflection
    "progress_threshold": 0.2,  # Minimum progress per reflection
    "strategy_adaptation": True # Change approach if stuck
}
```

### Issue: Tool Errors

**Symptom:** Tools frequently fail
**Solution:**
```python
# Add robust error handling
class RobustTool(BaseTool):
    async def execute(self, input_str: str) -> str:
        try:
            # Validate input
            validated = self.validate_input(input_str)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_impl(validated),
                timeout=10.0
            )
            
            # Validate output
            return self.format_output(result)
            
        except Exception as e:
            return f"Error: {str(e)}. Try rephrasing the query."
```

## Integration Examples

### With Other Patterns

```python
# Use CoT for planning, ReAct for execution
planner = ReasoningAgent(reasoning_pattern="chain_of_thought")
executor = ReasoningAgent(reasoning_pattern="react", tools=tools)

# Plan the approach
plan = await planner.think_and_act("How should I analyze this dataset?")

# Execute with tools
result = await executor.think_and_act(f"Execute plan: {plan.content}")
```

### Multi-Stage Research

```python
async def deep_research(topic: str):
    # Stage 1: Broad search
    broad = ReasoningAgent(
        reasoning_pattern="react",
        tools=[SearchTool()],
        pattern_config={"max_steps": 10}
    )
    overview = await broad.think_and_act(f"Overview of {topic}")
    
    # Stage 2: Detailed investigation
    detailed = ReasoningAgent(
        reasoning_pattern="react",
        tools=[SearchTool(), WikiTool(), CalculatorTool()],
        pattern_config={"max_steps": 20}
    )
    
    # Use overview to guide detailed research
    details = await detailed.think_and_act(
        f"Given this overview: {overview.content}\n"
        f"Investigate specific aspects of {topic}"
    )
    
    return details
```

## See Also

- [Chain of Thought](chain_of_thought.md) - For pure reasoning tasks
- [Tree of Thoughts](tree_of_thoughts.md) - For exploration without tools
- [Base Pattern](base.md) - Understanding the interface
- [Tool Development](../../reference/tool.md) - Creating custom tools
- [Examples](../../../examples/reasoning/react_example.py) - Complete examples
