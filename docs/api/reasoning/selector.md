# Pattern Selector API Reference

## Overview

The Pattern Selector automatically chooses the most appropriate reasoning pattern based on problem characteristics, available tools, and performance requirements.

## Class Reference

### PatternSelector

```python
class PatternSelector:
    """
    Automatically selects the best reasoning pattern for a given problem.
    
    Analyzes query characteristics, context, and available resources
    to recommend the optimal reasoning approach.
    """
```

#### Methods

##### select_pattern()

```python
@classmethod
def select_pattern(
    cls,
    query: str,
    available_tools: Optional[List[BaseTool]] = None,
    context: Optional[Dict[str, Any]] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> str
```

Select the best pattern for the given query.

**Parameters:**
- `query` (str): The problem or question to solve
- `available_tools` (Optional[List[BaseTool]]): Tools available for ReAct
- `context` (Optional[Dict]): Additional context about the problem
- `constraints` (Optional[Dict]): Performance or other constraints

**Returns:**
- `str`: Pattern name ("chain_of_thought", "tree_of_thoughts", or "react")

**Example:**

```python
# Automatic selection
pattern = PatternSelector.select_pattern(
    "Design a logo for a tech startup"
)
# Returns: "tree_of_thoughts"

# With tools available
pattern = PatternSelector.select_pattern(
    "What's the current weather in Tokyo?",
    available_tools=[SearchTool()]
)
# Returns: "react"
```

##### analyze_query()

```python
@classmethod
def analyze_query(cls, query: str) -> Dict[str, Any]
```

Analyze query characteristics for pattern selection.

**Returns:**
```python
{
    "type": str,  # "analytical", "creative", "research", etc.
    "complexity": str,  # "simple", "moderate", "complex"
    "requires_tools": bool,
    "requires_exploration": bool,
    "is_sequential": bool,
    "keywords": List[str],
    "indicators": Dict[str, float]
}
```

##### get_pattern_recommendation()

```python
@classmethod
def get_pattern_recommendation(
    cls,
    query: str,
    detailed: bool = False
) -> Union[str, Dict[str, Any]]
```

Get pattern recommendation with optional detailed analysis.

**Parameters:**
- `query` (str): The problem to analyze
- `detailed` (bool): Return detailed analysis if True

**Returns:**
- If `detailed=False`: Pattern name (str)
- If `detailed=True`: Dictionary with full analysis

**Example:**

```python
# Simple recommendation
pattern = PatternSelector.get_pattern_recommendation(
    "Explain how photosynthesis works"
)
# Returns: "chain_of_thought"

# Detailed recommendation
analysis = PatternSelector.get_pattern_recommendation(
    "Explain how photosynthesis works",
    detailed=True
)
# Returns:
{
    "pattern": "chain_of_thought",
    "confidence": 0.85,
    "reasoning": "Sequential explanation task",
    "alternatives": ["react"],
    "analysis": {...}
}
```

##### score_patterns()

```python
@classmethod
def score_patterns(
    cls,
    query_analysis: Dict[str, Any],
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, float]
```

Score each pattern for the given query analysis.

**Returns:**
```python
{
    "chain_of_thought": 0.85,
    "tree_of_thoughts": 0.45,
    "react": 0.20
}
```

## Selection Criteria

### Query Type Classification

| Query Type | Characteristics | Preferred Pattern |
|------------|----------------|-------------------|
| **Analytical** | Step-by-step breakdown, calculations | Chain of Thought |
| **Creative** | Multiple valid solutions, design tasks | Tree of Thoughts |
| **Research** | Information gathering, current data | ReAct |
| **Explanatory** | Teaching, describing processes | Chain of Thought |
| **Comparative** | Evaluating options, trade-offs | Tree of Thoughts |
| **Investigative** | Finding facts, troubleshooting | ReAct |

### Pattern Scoring Factors

#### Chain of Thought Scoring

```python
# High score indicators:
- Sequential keywords: "explain", "calculate", "analyze"
- Logical progression: "how", "why", "prove"
- Single correct answer expected
- No external data needed

# Low score indicators:
- Multiple valid approaches
- Requires current information
- Creative or design tasks
```

#### Tree of Thoughts Scoring

```python
# High score indicators:
- Creative keywords: "design", "create", "brainstorm"
- Multiple options: "alternatives", "approaches", "ideas"
- Comparison tasks: "compare", "evaluate", "choose"
- Open-ended problems

# Low score indicators:
- Single correct answer
- Time-sensitive tasks
- Requires external data
```

#### ReAct Scoring

```python
# High score indicators:
- Action words: "find", "search", "get", "retrieve"
- Current info: "latest", "current", "today's"
- Tool-related: "calculate", "look up", "check"
- External data required

# Low score indicators:
- Pure reasoning tasks
- No tools available
- Creative exploration
```

## Usage Examples

### Basic Pattern Selection

```python
from agenticraft.reasoning.patterns.selector import PatternSelector
from agenticraft.agents.reasoning import ReasoningAgent

# Let selector choose pattern
query = "What's the population density of Tokyo?"
pattern = PatternSelector.select_pattern(query)

# Create agent with selected pattern
agent = ReasoningAgent(
    name="SmartAgent",
    reasoning_pattern=pattern
)

response = await agent.think_and_act(query)
```

### With Constraints

```python
# Performance-constrained selection
constraints = {
    "max_time": 5.0,  # 5 seconds max
    "max_memory": "low",  # Minimize memory usage
    "require_explanation": True
}

pattern = PatternSelector.select_pattern(
    query="Design a mobile app",
    constraints=constraints
)
# May return "chain_of_thought" instead of "tree_of_thoughts"
# due to performance constraints
```

### Tool-Aware Selection

```python
# Selection based on available tools
from agenticraft.tools import SearchTool, CalculatorTool

tools = [SearchTool(), CalculatorTool()]

# Query that could use tools
pattern = PatternSelector.select_pattern(
    "What's the GDP per capita of Japan in USD?",
    available_tools=tools
)
# Returns: "react" (can use search and calculator)

# Same query without tools
pattern = PatternSelector.select_pattern(
    "What's the GDP per capita of Japan in USD?",
    available_tools=[]
)
# Returns: "chain_of_thought" (will use knowledge)
```

### Detailed Analysis

```python
# Get full analysis for decision transparency
analysis = PatternSelector.get_pattern_recommendation(
    "Create a marketing strategy for our new product",
    detailed=True
)

print(f"Recommended: {analysis['pattern']}")
print(f"Confidence: {analysis['confidence']:.0%}")
print(f"Reasoning: {analysis['reasoning']}")

# Show alternatives
for alt in analysis['alternatives']:
    print(f"Alternative: {alt}")

# Access detailed scoring
for pattern, score in analysis['scores'].items():
    print(f"{pattern}: {score:.2f}")
```

## Custom Selection Logic

### Extending the Selector

```python
class CustomPatternSelector(PatternSelector):
    """Extended selector with domain-specific logic."""
    
    @classmethod
    def select_pattern(cls, query: str, **kwargs) -> str:
        # Check for domain-specific patterns first
        if cls._is_legal_document(query):
            return "chain_of_thought"  # Always use CoT for legal
        
        if cls._is_data_analysis(query):
            return "react"  # Always use ReAct for data
        
        # Fall back to standard selection
        return super().select_pattern(query, **kwargs)
    
    @classmethod
    def _is_legal_document(cls, query: str) -> bool:
        legal_terms = ["contract", "agreement", "legal", "clause"]
        return any(term in query.lower() for term in legal_terms)
    
    @classmethod
    def _is_data_analysis(cls, query: str) -> bool:
        data_terms = ["dataset", "analyze data", "statistics", "metrics"]
        return any(term in query.lower() for term in data_terms)
```

### Adding New Patterns

```python
# Register pattern with selector
class CustomPattern(BaseReasoningPattern):
    # ... implementation ...
    pass

# Extend selector to recognize the pattern
class ExtendedSelector(PatternSelector):
    @classmethod
    def analyze_query(cls, query: str) -> Dict[str, Any]:
        analysis = super().analyze_query(query)
        
        # Add custom pattern indicators
        if "quantum" in query.lower():
            analysis["requires_quantum_reasoning"] = True
        
        return analysis
    
    @classmethod
    def score_patterns(cls, query_analysis: Dict, constraints=None) -> Dict[str, float]:
        scores = super().score_patterns(query_analysis, constraints)
        
        # Score custom pattern
        if query_analysis.get("requires_quantum_reasoning"):
            scores["quantum_pattern"] = 0.95
        
        return scores
```

## Advanced Features

### Multi-Stage Selection

```python
class MultiStageSelector:
    """Select different patterns for different stages."""
    
    @classmethod
    def select_stages(cls, task: str) -> List[Dict[str, str]]:
        stages = []
        
        # Analyze task complexity
        if "research" in task and "design" in task:
            # Stage 1: Research
            stages.append({
                "stage": "research",
                "pattern": "react",
                "description": "Gather information"
            })
            
            # Stage 2: Design
            stages.append({
                "stage": "design",
                "pattern": "tree_of_thoughts",
                "description": "Explore design options"
            })
            
            # Stage 3: Planning
            stages.append({
                "stage": "planning",
                "pattern": "chain_of_thought",
                "description": "Create detailed plan"
            })
        
        return stages
```

### Context-Aware Selection

```python
# Selection based on context
context = {
    "user_expertise": "beginner",
    "time_available": "limited",
    "previous_patterns": ["chain_of_thought"],
    "domain": "education"
}

pattern = PatternSelector.select_pattern(
    query="Explain machine learning",
    context=context
)
# Considers user level and time constraints
```

### Performance Profiling

```python
class ProfilingSelector(PatternSelector):
    """Track pattern performance for better selection."""
    
    performance_data = {}
    
    @classmethod
    def select_pattern(cls, query: str, **kwargs) -> str:
        pattern = super().select_pattern(query, **kwargs)
        
        # Adjust based on historical performance
        query_type = cls.analyze_query(query)["type"]
        
        if query_type in cls.performance_data:
            # Use best performing pattern for this query type
            performances = cls.performance_data[query_type]
            best_pattern = max(performances, key=performances.get)
            
            if performances[best_pattern] > performances.get(pattern, 0):
                pattern = best_pattern
        
        return pattern
    
    @classmethod
    def record_performance(
        cls,
        query_type: str,
        pattern: str,
        performance_score: float
    ):
        """Record pattern performance for learning."""
        if query_type not in cls.performance_data:
            cls.performance_data[query_type] = {}
        
        cls.performance_data[query_type][pattern] = performance_score
```

## Best Practices

### 1. Trust but Verify

```python
# Get recommendation but allow override
recommended = PatternSelector.select_pattern(query)

# Check if recommendation makes sense
if "calculate" in query and recommended != "react":
    # Maybe override if calculator tool available
    if calculator_tool in available_tools:
        pattern = "react"
else:
    pattern = recommended
```

### 2. Provide Context

```python
# More context = better selection
context = {
    "domain": "scientific",
    "audience": "researchers",
    "output_format": "detailed_analysis",
    "time_sensitivity": "low"
}

pattern = PatternSelector.select_pattern(
    query=query,
    context=context
)
```

### 3. Monitor Selection Quality

```python
# Track selection effectiveness
async def evaluate_selection(query: str):
    # Try recommended pattern
    recommended = PatternSelector.select_pattern(query)
    agent1 = ReasoningAgent(reasoning_pattern=recommended)
    result1 = await agent1.think_and_act(query)
    
    # Try alternatives
    alternatives = ["chain_of_thought", "tree_of_thoughts", "react"]
    alternatives.remove(recommended)
    
    results = {}
    for pattern in alternatives:
        agent = ReasoningAgent(reasoning_pattern=pattern)
        result = await agent.think_and_act(query)
        results[pattern] = result
    
    # Compare effectiveness
    # ... analysis logic ...
```

## Common Patterns

### Query Pattern Mapping

```python
# Common query patterns and their ideal reasoning patterns
QUERY_PATTERNS = {
    # Chain of Thought patterns
    r"explain|describe|how does": "chain_of_thought",
    r"calculate|compute|solve": "chain_of_thought",
    r"analyze|break down|examine": "chain_of_thought",
    
    # Tree of Thoughts patterns
    r"design|create|brainstorm": "tree_of_thoughts",
    r"compare|evaluate|choose": "tree_of_thoughts",
    r"alternatives|options|approaches": "tree_of_thoughts",
    
    # ReAct patterns
    r"find|search|look up": "react",
    r"current|latest|today": "react",
    r"fetch|retrieve|get": "react"
}
```

## See Also

- [Chain of Thought](chain_of_thought.md) - Linear reasoning pattern
- [Tree of Thoughts](tree_of_thoughts.md) - Multi-path exploration pattern
- [ReAct Pattern](react.md) - Action-based reasoning pattern
- [Base Pattern](base.md) - Pattern interface and base classes
