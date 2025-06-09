# Chain of Thought API Reference

## Overview

Chain of Thought (CoT) implements linear, step-by-step reasoning with confidence tracking, alternative thought generation, and comprehensive problem analysis.

## Class Reference

### ChainOfThoughtReasoning

```python
class ChainOfThoughtReasoning(BaseReasoningPattern):
    """
    Implements Chain of Thought reasoning pattern.
    
    Breaks down complex problems into sequential reasoning steps,
    tracking confidence and generating alternatives when needed.
    """
```

#### Initialization

```python
from agenticraft.reasoning.patterns.chain_of_thought import ChainOfThoughtReasoning

cot = ChainOfThoughtReasoning(
    min_confidence: float = 0.7,
    max_steps: int = 10
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_confidence` | float | 0.7 | Minimum confidence threshold for steps |
| `max_steps` | int | 10 | Maximum number of reasoning steps |

#### Methods

##### reason()

```python
async def reason(
    self,
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> ReasoningTrace
```

Execute chain of thought reasoning on the query.

**Parameters:**
- `query` (str): The problem or question to reason about
- `context` (Optional[Dict]): Additional context for reasoning

**Returns:**
- `ReasoningTrace`: Complete reasoning trace with steps and confidence

**Example:**

```python
trace = await cot.reason(
    "A train travels 120 miles in 2 hours. What is its average speed?"
)

for step in trace.steps:
    print(f"{step.step_number}: {step.thought}")
    print(f"Confidence: {step.confidence:.2%}")
```

##### _decompose_problem()

```python
def _decompose_problem(self, query: str) -> List[str]
```

Break down a complex problem into sub-problems.

**Internal method** - automatically called during reasoning.

##### _generate_thought()

```python
def _generate_thought(
    self,
    sub_problem: str,
    previous_thoughts: List[ThoughtStep]
) -> ThoughtStep
```

Generate a reasoning step for a sub-problem.

**Internal method** - includes confidence calculation.

##### _assess_confidence()

```python
def _assess_confidence(self, thought: str, context: Dict) -> float
```

Calculate confidence score for a thought (0.0 to 1.0).

**Factors considered:**
- Logical consistency
- Evidence support
- Clarity of reasoning
- Alignment with previous steps

##### _generate_alternatives()

```python
def _generate_alternatives(
    self,
    original_thought: ThoughtStep,
    context: Dict
) -> List[ThoughtStep]
```

Generate alternative thoughts when confidence is low.

**Triggered when:** step confidence < min_confidence

##### _synthesize_conclusion()

```python
def _synthesize_conclusion(
    self,
    thoughts: List[ThoughtStep]
) -> str
```

Combine all reasoning steps into a final conclusion.

##### get_reasoning_summary()

```python
def get_reasoning_summary(self) -> Dict[str, Any]
```

Get summary statistics about the reasoning process.

**Returns:**
```python
{
    "total_steps": int,
    "average_confidence": float,
    "low_confidence_steps": int,
    "alternatives_generated": int,
    "problem_complexity": str  # "simple", "moderate", "complex"
}
```

### ThoughtStep

```python
@dataclass
class ThoughtStep:
    """Represents a single step in chain of thought reasoning."""
    
    step_number: int
    thought: str
    confidence: float
    sub_problem: str
    evidence: List[str]
    alternatives: List['ThoughtStep']
    step_type: str  # "analysis", "synthesis", "validation"
    metadata: Dict[str, Any]
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `step_number` | int | Sequential step number |
| `thought` | str | The reasoning content |
| `confidence` | float | Confidence score (0.0-1.0) |
| `sub_problem` | str | Sub-problem being addressed |
| `evidence` | List[str] | Supporting evidence/facts |
| `alternatives` | List[ThoughtStep] | Alternative thoughts if confidence is low |
| `step_type` | str | Type of reasoning step |
| `metadata` | Dict | Additional step information |

## Usage Examples

### Basic Usage

```python
from agenticraft.agents.reasoning import ReasoningAgent

# Create agent with Chain of Thought
agent = ReasoningAgent(
    name="Analyst",
    reasoning_pattern="chain_of_thought"
)

# Solve a problem
response = await agent.think_and_act(
    "What are the pros and cons of remote work?"
)

# Access reasoning
print(response.reasoning)  # Human-readable summary
```

### Advanced Configuration

```python
# High-confidence reasoning
agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    pattern_config={
        "min_confidence": 0.9,  # Require very high confidence
        "max_steps": 20        # Allow more detailed analysis
    }
)

# Problem solving with context
context = {
    "domain": "mathematics",
    "difficulty": "intermediate"
}

response = await agent.think_and_act(
    "Solve: 2x² + 5x - 3 = 0",
    context=context
)
```

### Accessing Internal State

```python
# Get detailed reasoning information
cot_reasoning = agent.advanced_reasoning

# Access all steps
for step in cot_reasoning.thoughts:
    print(f"Step {step.step_number}: {step.thought}")
    if step.alternatives:
        print(f"  Alternatives considered: {len(step.alternatives)}")

# Get confidence report
report = cot_reasoning._generate_confidence_report()
print(f"Steps below threshold: {report['below_threshold']}")
print(f"Average confidence: {report['average']:.2%}")

# Check problem assessment
print(f"Problem complexity: {cot_reasoning.problem_complexity}")
```

### Error Handling

```python
try:
    response = await agent.think_and_act(query)
except MaxStepsExceeded:
    # Handle case where reasoning is too long
    print("Problem too complex for current settings")
except LowConfidenceError:
    # Handle case where confidence remains low
    print("Unable to reach confident conclusion")
```

## Best Practices

### 1. Configuration Guidelines

```python
# For mathematical/logical problems
math_config = {
    "min_confidence": 0.8,  # High confidence needed
    "max_steps": 15        # Allow detailed steps
}

# For creative/subjective problems  
creative_config = {
    "min_confidence": 0.6,  # Lower threshold acceptable
    "max_steps": 8         # Fewer steps needed
}

# For analysis tasks
analysis_config = {
    "min_confidence": 0.75,
    "max_steps": 12
}
```

### 2. Monitoring Reasoning Quality

```python
# Check reasoning quality
response = await agent.think_and_act(query)

# Validate confidence levels
avg_confidence = sum(s.confidence for s in response.reasoning_steps) / len(response.reasoning_steps)

if avg_confidence < 0.7:
    # Consider re-running with different config
    # or switching to different pattern
    pass

# Check for excessive alternatives
high_alternative_steps = [
    s for s in response.reasoning_steps 
    if len(s.alternatives) > 2
]

if len(high_alternative_steps) > 3:
    # Problem may be too ambiguous
    pass
```

### 3. Performance Optimization

```python
# For faster reasoning
fast_cot = {
    "max_steps": 5,
    "min_confidence": 0.65  # Accept slightly lower confidence
}

# For thorough analysis
thorough_cot = {
    "max_steps": 20,
    "min_confidence": 0.85
}
```

## Integration with Other Patterns

### Fallback to Tree of Thoughts

```python
# Try CoT first, fall back to ToT if needed
response = await agent.think_and_act(query)

if response.metadata.get("low_confidence_conclusion"):
    # Switch to Tree of Thoughts for exploration
    agent.reasoning_pattern = "tree_of_thoughts"
    response = await agent.think_and_act(query)
```

### Combine with ReAct

```python
# Use CoT for planning, ReAct for execution
planner = ReasoningAgent(reasoning_pattern="chain_of_thought")
executor = ReasoningAgent(reasoning_pattern="react", tools=[...])

# Plan the approach
plan = await planner.think_and_act("How should I analyze this dataset?")

# Execute with tools
result = await executor.think_and_act(
    f"Execute this plan: {plan.content}"
)
```

## Common Issues and Solutions

### Issue: Circular Reasoning

**Symptom:** Steps repeat similar thoughts
**Solution:** 
```python
# Add loop detection
pattern_config = {
    "detect_loops": True,
    "max_similar_thoughts": 2
}
```

### Issue: Low Confidence Throughout

**Symptom:** All steps have confidence < threshold
**Solution:**
```python
# Either lower threshold or provide more context
pattern_config = {
    "min_confidence": 0.6,  # Lower threshold
    "require_evidence": True  # Enforce evidence gathering
}
```

### Issue: Too Many Steps

**Symptom:** Reaching max_steps limit
**Solution:**
```python
# Increase limit or decompose problem differently
pattern_config = {
    "max_steps": 20,
    "aggressive_synthesis": True  # Synthesize earlier
}
```

## See Also

- [Tree of Thoughts](tree_of_thoughts.md) - For problems needing exploration
- [ReAct Pattern](react.md) - For tool-based reasoning
- [Base Pattern](base.md) - Understanding the base interface
- [Examples](../../../examples/reasoning/chain_of_thought_example.py) - Complete examples
