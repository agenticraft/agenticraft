# Base Pattern API Reference

## Overview

The base pattern provides the foundation for all reasoning patterns in AgentiCraft, defining the interface and common functionality.

## Class Reference

### BaseReasoningPattern

```python
class BaseReasoningPattern(ABC):
    """
    Abstract base class for all reasoning patterns.
    
    Defines the interface that all reasoning patterns must implement
    and provides common functionality.
    """
```

#### Abstract Methods

##### reason()

```python
@abstractmethod
async def reason(
    self,
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> ReasoningTrace
```

Core method that all patterns must implement.

**Parameters:**
- `query` (str): The problem or question to reason about
- `context` (Optional[Dict]): Additional context for reasoning

**Returns:**
- `ReasoningTrace`: Structured reasoning output

#### Common Methods

##### format_reasoning()

```python
def format_reasoning(self, trace: ReasoningTrace) -> str
```

Convert reasoning trace to human-readable format.

**Default implementation** provides basic formatting, patterns can override.

##### get_pattern_info()

```python
def get_pattern_info(self) -> Dict[str, Any]
```

Get pattern metadata and configuration.

**Returns:**
```python
{
    "name": str,
    "version": str,
    "capabilities": List[str],
    "config": Dict[str, Any]
}
```

### ReasoningTrace

```python
@dataclass
class ReasoningTrace:
    """
    Structured output from any reasoning pattern.
    
    Provides a consistent interface for accessing reasoning results
    regardless of the pattern used.
    """
    
    query: str
    pattern: str
    steps: List[ReasoningStep]
    conclusion: str
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime
    duration: float
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `query` | str | Original query that was reasoned about |
| `pattern` | str | Name of pattern used |
| `steps` | List[ReasoningStep] | All reasoning steps taken |
| `conclusion` | str | Final conclusion/answer |
| `confidence` | float | Overall confidence (0.0-1.0) |
| `metadata` | Dict | Pattern-specific metadata |
| `timestamp` | datetime | When reasoning started |
| `duration` | float | Time taken in seconds |

#### Methods

##### format_reasoning()

```python
def format_reasoning(self) -> str
```

Get human-readable reasoning summary.

##### get_step_by_type()

```python
def get_step_by_type(self, step_type: str) -> List[ReasoningStep]
```

Filter steps by type.

##### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Convert to dictionary for serialization.

### ReasoningStep

```python
@dataclass
class ReasoningStep:
    """
    A single step in the reasoning process.
    
    Base class for pattern-specific step types.
    """
    
    number: int
    description: str
    confidence: float
    timestamp: datetime
    step_type: str
    content: str
    metadata: Dict[str, Any]
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `number` | int | Step number in sequence |
| `description` | str | Brief step description |
| `confidence` | float | Step confidence (0.0-1.0) |
| `timestamp` | datetime | When step occurred |
| `step_type` | str | Type categorization |
| `content` | str | Full step content |
| `metadata` | Dict | Additional step data |

### PatternConfig

```python
@dataclass
class PatternConfig:
    """Configuration for reasoning patterns."""
    
    # Common configuration
    max_thinking_time: float = 30.0
    enable_caching: bool = False
    verbose: bool = False
    
    # Pattern-specific config
    pattern_params: Dict[str, Any] = field(default_factory=dict)
```

## Creating Custom Patterns

### Basic Pattern Implementation

```python
from agenticraft.reasoning.patterns.base import BaseReasoningPattern

class CustomReasoningPattern(BaseReasoningPattern):
    """Custom reasoning pattern implementation."""
    
    def __init__(self, custom_param: str = "default"):
        self.custom_param = custom_param
        self.steps_taken = []
    
    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningTrace:
        start_time = datetime.now()
        
        # Implement your reasoning logic
        steps = []
        
        # Step 1: Analyze query
        step1 = ReasoningStep(
            number=1,
            description="Analyze the query",
            confidence=0.9,
            timestamp=datetime.now(),
            step_type="analysis",
            content=f"Analyzing: {query}",
            metadata={"custom": self.custom_param}
        )
        steps.append(step1)
        
        # Step 2: Custom reasoning
        # ... your logic here ...
        
        # Create conclusion
        conclusion = "Your conclusion based on reasoning"
        confidence = sum(s.confidence for s in steps) / len(steps)
        
        # Return structured trace
        return ReasoningTrace(
            query=query,
            pattern="custom",
            steps=steps,
            conclusion=conclusion,
            confidence=confidence,
            metadata={
                "custom_param": self.custom_param,
                "context_used": context is not None
            },
            timestamp=start_time,
            duration=(datetime.now() - start_time).total_seconds()
        )
```

### Advanced Pattern with State

```python
class StatefulReasoningPattern(BaseReasoningPattern):
    """Pattern that maintains state across steps."""
    
    def __init__(self):
        self.state = {
            "assumptions": [],
            "evidence": [],
            "hypotheses": []
        }
    
    async def reason(self, query: str, context: Optional[Dict] = None) -> ReasoningTrace:
        # Reset state for new query
        self._reset_state()
        
        steps = []
        
        # Generate hypotheses
        hypotheses = await self._generate_hypotheses(query)
        self.state["hypotheses"] = hypotheses
        
        # Test each hypothesis
        for i, hypothesis in enumerate(hypotheses):
            evidence = await self._gather_evidence(hypothesis)
            self.state["evidence"].extend(evidence)
            
            step = ReasoningStep(
                number=i + 1,
                description=f"Testing hypothesis: {hypothesis}",
                confidence=self._evaluate_hypothesis(hypothesis, evidence),
                timestamp=datetime.now(),
                step_type="hypothesis_testing",
                content=f"Hypothesis: {hypothesis}\nEvidence: {evidence}",
                metadata={"hypothesis_id": i}
            )
            steps.append(step)
        
        # Select best hypothesis
        best = self._select_best_hypothesis()
        
        return ReasoningTrace(
            query=query,
            pattern="stateful",
            steps=steps,
            conclusion=best["conclusion"],
            confidence=best["confidence"],
            metadata={"state": self.state},
            timestamp=steps[0].timestamp,
            duration=(datetime.now() - steps[0].timestamp).total_seconds()
        )
```

### Pattern with External Dependencies

```python
class DependentReasoningPattern(BaseReasoningPattern):
    """Pattern that uses external services."""
    
    def __init__(self, knowledge_base, llm_client):
        self.kb = knowledge_base
        self.llm = llm_client
    
    async def reason(self, query: str, context: Optional[Dict] = None) -> ReasoningTrace:
        steps = []
        
        # Step 1: Search knowledge base
        kb_results = await self.kb.search(query)
        steps.append(ReasoningStep(
            number=1,
            description="Search knowledge base",
            confidence=0.95,
            timestamp=datetime.now(),
            step_type="knowledge_retrieval",
            content=f"Found {len(kb_results)} relevant items",
            metadata={"sources": kb_results}
        ))
        
        # Step 2: Generate reasoning with LLM
        prompt = self._build_prompt(query, kb_results, context)
        reasoning = await self.llm.generate(prompt)
        
        # Parse and structure the reasoning
        structured_steps = self._parse_reasoning(reasoning)
        steps.extend(structured_steps)
        
        # Create trace
        return self._create_trace(query, steps)
```

## Integration with ReasoningAgent

### Registering Custom Patterns

```python
from agenticraft.agents.reasoning import ReasoningAgent

# Register pattern globally
ReasoningAgent.register_pattern("custom", CustomReasoningPattern)

# Use the pattern
agent = ReasoningAgent(
    name="CustomAgent",
    reasoning_pattern="custom"
)
```

### Pattern Factory

```python
class PatternFactory:
    """Factory for creating reasoning patterns."""
    
    _patterns = {
        "chain_of_thought": ChainOfThoughtReasoning,
        "tree_of_thoughts": TreeOfThoughtsReasoning,
        "react": ReactReasoning
    }
    
    @classmethod
    def create(
        cls,
        pattern_name: str,
        config: Optional[PatternConfig] = None
    ) -> BaseReasoningPattern:
        """Create a pattern instance."""
        if pattern_name not in cls._patterns:
            raise ValueError(f"Unknown pattern: {pattern_name}")
        
        pattern_class = cls._patterns[pattern_name]
        
        if config:
            return pattern_class(**config.pattern_params)
        return pattern_class()
    
    @classmethod
    def register(cls, name: str, pattern_class: Type[BaseReasoningPattern]):
        """Register a new pattern."""
        cls._patterns[name] = pattern_class
```

## Testing Patterns

### Unit Testing

```python
import pytest
from agenticraft.reasoning.patterns.base import ReasoningTrace

@pytest.mark.asyncio
async def test_custom_pattern():
    pattern = CustomReasoningPattern(custom_param="test")
    
    # Test basic reasoning
    trace = await pattern.reason("Test query")
    
    assert isinstance(trace, ReasoningTrace)
    assert trace.pattern == "custom"
    assert len(trace.steps) > 0
    assert 0 <= trace.confidence <= 1
    
    # Test with context
    trace_with_context = await pattern.reason(
        "Test query",
        context={"key": "value"}
    )
    assert trace_with_context.metadata["context_used"]
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_pattern_with_agent():
    # Register and use pattern
    ReasoningAgent.register_pattern("test_custom", CustomReasoningPattern)
    
    agent = ReasoningAgent(
        name="TestAgent",
        reasoning_pattern="test_custom"
    )
    
    response = await agent.think_and_act("Test problem")
    
    assert response.reasoning_steps
    assert response.metadata["pattern"] == "test_custom"
```

### Performance Testing

```python
import time

async def benchmark_pattern(pattern: BaseReasoningPattern, queries: List[str]):
    """Benchmark pattern performance."""
    times = []
    
    for query in queries:
        start = time.time()
        trace = await pattern.reason(query)
        duration = time.time() - start
        
        times.append({
            "query": query,
            "duration": duration,
            "steps": len(trace.steps),
            "confidence": trace.confidence
        })
    
    # Calculate statistics
    avg_time = sum(t["duration"] for t in times) / len(times)
    avg_steps = sum(t["steps"] for t in times) / len(times)
    
    return {
        "average_time": avg_time,
        "average_steps": avg_steps,
        "times": times
    }
```

## Best Practices

### 1. Consistent Step Structure

Always create properly structured steps:

```python
step = ReasoningStep(
    number=step_num,
    description="Clear, concise description",
    confidence=calculated_confidence,
    timestamp=datetime.now(),
    step_type="meaningful_type",
    content="Full content with details",
    metadata={
        # Pattern-specific data
    }
)
```

### 2. Meaningful Confidence Scores

Calculate confidence based on relevant factors:

```python
def calculate_confidence(self, factors: Dict[str, float]) -> float:
    """Calculate weighted confidence score."""
    weights = {
        "logical_consistency": 0.3,
        "evidence_support": 0.4,
        "clarity": 0.2,
        "completeness": 0.1
    }
    
    confidence = sum(
        factors.get(factor, 0.5) * weight
        for factor, weight in weights.items()
    )
    
    return max(0.0, min(1.0, confidence))
```

### 3. Proper Error Handling

```python
async def reason(self, query: str, context: Optional[Dict] = None) -> ReasoningTrace:
    try:
        # Your reasoning logic
        pass
    except Exception as e:
        # Create error trace
        return ReasoningTrace(
            query=query,
            pattern=self.__class__.__name__,
            steps=[
                ReasoningStep(
                    number=1,
                    description="Error during reasoning",
                    confidence=0.0,
                    timestamp=datetime.now(),
                    step_type="error",
                    content=str(e),
                    metadata={"error_type": type(e).__name__}
                )
            ],
            conclusion="Unable to complete reasoning due to error",
            confidence=0.0,
            metadata={"error": True},
            timestamp=datetime.now(),
            duration=0.0
        )
```

## See Also

- [Chain of Thought](chain_of_thought.md) - Linear reasoning implementation
- [Tree of Thoughts](tree_of_thoughts.md) - Multi-path reasoning implementation
- [ReAct Pattern](react.md) - Action-based reasoning implementation
- [Pattern Selector](selector.md) - Automatic pattern selection
