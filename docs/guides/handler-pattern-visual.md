# AgentiCraft Handler Pattern - Visual Guide

## WorkflowAgent with Handlers

```
┌─────────────────┐
│ Workflow Start  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ WorkflowAgent   │────▶│   Step: fetch   │
│                 │     │  Handler: fetch │
│ Handlers:       │     └────────┬────────┘
│ - fetch         │              │
│ - process       │              ▼
│ - report        │     ┌─────────────────┐
└─────────────────┘     │ fetch_handler() │
                        │ Updates context │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Step: process   │
                        │ Uses context    │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │process_handler()│
                        │ Reads context   │
                        │ Updates context │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Step: report   │
                        │  Final output   │
                        └─────────────────┘

Code Example:
```python
def fetch_handler(agent, step, context):
    data = fetch_data()
    context["data"] = data
    return f"Fetched {len(data)} items"

def process_handler(agent, step, context):
    data = context.get("data", [])
    result = process(data)
    context["result"] = result
    return f"Processed: {result}"

workflow_agent.register_handler("fetch", fetch_handler)
workflow_agent.register_handler("process", process_handler)

workflow.add_step(name="fetch_step", handler="fetch")
workflow.add_step(name="process_step", handler="process", depends_on=["fetch_step"])
```

**Telemetry Spans**: 
- `workflow.step.fetch_step`
- `workflow.step.process_step`

---

## Basic Agent Pattern

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Basic Agent   │────▶│ LLM Processing  │
│                 │     │                 │
│ Instructions:   │     │ "Analyze this   │
│ - Analyze data  │     │  based on       │
│ - Calculate     │     │  instructions"  │
│ - Explain       │     └────────┬────────┘
└─────────────────┘              │
                                 ▼
                        ┌─────────────────┐
                        │ Natural Language│
                        │    Response     │
                        └─────────────────┘

Code Example:
```python
agent = Agent(
    name="Analyzer",
    instructions="""You are a data analyzer.
    When given numbers, calculate statistics and explain patterns.""",
    model="gpt-4o-mini"
)

response = await agent.arun(
    "Analyze these numbers: 10, 20, 30, 40, 50"
)
```

**Telemetry Span**: `agent.Analyzer.arun`

---

## Context Flow in Handlers

```
┌──────────────┐
│   Context    │ ←─── Shared across all steps
│ (Dictionary) │
└──────┬───────┘
       │
    ┌──┴──┐
    │ {} │ ← Initial (empty or with input data)
    └──┬──┘
       ▼
┌─────────────┐
│   Step 1    │
│   Handler   │ ──→ context["data"] = [1,2,3]
└──────┬──────┘
       ▼
    ┌──┴──────────┐
    │ {           │
    │  "data":    │
    │   [1,2,3]   │
    │ }           │
    └──┬──────────┘
       ▼
┌─────────────┐
│   Step 2    │
│   Handler   │ ──→ data = context["data"]
└──────┬──────┘     context["sum"] = 6
       ▼
    ┌──┴──────────┐
    │ {           │
    │  "data":    │
    │   [1,2,3],  │
    │  "sum": 6   │
    │ }           │
    └─────────────┘
```

---

## Handler Pattern Benefits

| Aspect | Handler Pattern |
|--------|-----------------|
| **Use Case** | Multi-step workflows |
| **Execution** | Orchestrated by workflow |
| **State** | Managed via context |
| **Data Flow** | Explicit through context |
| **Error Handling** | Try/except in handlers |
| **Testing** | Easy to unit test |
| **Debugging** | Clear execution flow |

## Telemetry Integration

Both patterns are **fully instrumented**:

### WorkflowAgent Telemetry
- Automatic workflow execution spans
- Handler execution tracking
- Context size monitoring
- Step dependency visualization

### Basic Agent Telemetry
- Automatic agent.arun() spans
- Token usage tracking
- Latency measurements
- Error tracking

No manual instrumentation needed - just enable telemetry!

## Best Practices

### 1. Handler Naming
```python
# Good: Descriptive action names
def fetch_user_data_handler(agent, step, context):
def calculate_statistics_handler(agent, step, context):
def generate_report_handler(agent, step, context):

# Avoid: Generic names
def handler1(agent, step, context):
def process(agent, step, context):
```

### 2. Context Keys
```python
# Good: Namespaced and descriptive
context["user_data.raw"] = raw_data
context["user_data.processed"] = processed_data
context["stats.mean"] = mean_value

# Avoid: Generic keys that might collide
context["data"] = data
context["result"] = result
```

### 3. Error Messages
```python
def safe_handler(agent, step, context):
    try:
        # Handler logic
        return "Success: Processed X items"
    except ValueError as e:
        return f"Validation Error: {e}"
    except Exception as e:
        return f"Unexpected Error: {e}"
```

The handler pattern provides a clean, testable, and observable way to extend AgentiCraft agents with custom functionality!
