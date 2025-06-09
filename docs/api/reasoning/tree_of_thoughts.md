# Tree of Thoughts API Reference

## Overview

Tree of Thoughts (ToT) implements multi-path reasoning exploration with scoring, pruning, and optimal path selection. It explores multiple solution paths simultaneously, evaluating and pruning to find the best approach.

## Class Reference

### TreeOfThoughtsReasoning

```python
class TreeOfThoughtsReasoning(BaseReasoningPattern):
    """
    Implements Tree of Thoughts reasoning pattern.
    
    Explores multiple reasoning paths simultaneously, scoring each path
    and pruning unpromising branches to find optimal solutions.
    """
```

#### Initialization

```python
from agenticraft.reasoning.patterns.tree_of_thoughts import TreeOfThoughtsReasoning

tot = TreeOfThoughtsReasoning(
    max_depth: int = 4,
    beam_width: int = 3,
    exploration_factor: float = 0.3,
    pruning_threshold: float = 0.4
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_depth` | int | 4 | Maximum tree depth to explore |
| `beam_width` | int | 3 | Number of paths to explore at each level |
| `exploration_factor` | float | 0.3 | Balance between exploration and exploitation (0-1) |
| `pruning_threshold` | float | 0.4 | Score below which to prune branches |

#### Methods

##### reason()

```python
async def reason(
    self,
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> ReasoningTrace
```

Execute tree of thoughts reasoning on the query.

**Parameters:**
- `query` (str): The problem to explore solutions for
- `context` (Optional[Dict]): Additional context for reasoning

**Returns:**
- `ReasoningTrace`: Complete reasoning trace with exploration tree

**Example:**

```python
trace = await tot.reason(
    "Design a mobile app for elderly users to stay connected with family"
)

# Access the best solution
best = tot.get_best_solution()
print(f"Best path score: {best['score']}")
for thought in best['thoughts']:
    print(f"- {thought}")
```

##### _initialize_tree()

```python
def _initialize_tree(self, query: str) -> str
```

Create the root node of the reasoning tree.

**Returns:** Root node ID

##### _generate_children()

```python
async def _generate_children(
    self,
    node_id: str,
    num_children: int
) -> List[str]
```

Generate child thoughts for a node.

**Internal method** - creates diverse branches using exploration factor.

##### _evaluate_node()

```python
def _evaluate_node(self, node_id: str) -> float
```

Calculate score for a tree node.

**Scoring factors:**
- Coherence with parent thoughts
- Problem-solving progress
- Creativity/novelty (when exploration_factor > 0)
- Feasibility assessment

##### _should_prune()

```python
def _should_prune(self, node_id: str) -> bool
```

Determine if a branch should be pruned.

**Pruning criteria:**
- Score below pruning_threshold
- Circular reasoning detected
- No progress from parent

##### _select_best_nodes()

```python
def _select_best_nodes(
    self,
    nodes: List[str],
    k: int
) -> List[str]
```

Select top k nodes for further exploration.

**Uses:** Score-based selection with exploration bonus

##### get_best_solution()

```python
def get_best_solution(self) -> Optional[Dict[str, Any]]
```

Get the highest-scoring complete solution path.

**Returns:**
```python
{
    "path": List[str],  # Node IDs from root to solution
    "thoughts": List[str],  # Thoughts along the path
    "score": float,  # Path score
    "depth": int  # Solution depth
}
```

##### get_all_solutions()

```python
def get_all_solutions(self) -> List[Dict[str, Any]]
```

Get all complete solution paths, sorted by score.

##### visualize_tree()

```python
def visualize_tree(self, format: str = "text") -> str
```

Generate tree visualization.

**Formats:**
- `"text"`: ASCII tree representation
- `"mermaid"`: Mermaid diagram format
- `"json"`: Structured JSON representation

### TreeNode

```python
@dataclass
class TreeNode:
    """Represents a node in the reasoning tree."""
    
    id: str
    thought: str
    parent_id: Optional[str]
    children: List[str]
    score: float
    depth: int
    status: NodeStatus
    node_type: NodeType
    metadata: Dict[str, Any]
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | str | Unique node identifier |
| `thought` | str | The reasoning content |
| `parent_id` | Optional[str] | Parent node ID (None for root) |
| `children` | List[str] | Child node IDs |
| `score` | float | Node evaluation score (0.0-1.0) |
| `depth` | int | Depth in tree (root = 0) |
| `status` | NodeStatus | Current node status |
| `node_type` | NodeType | Type of reasoning node |
| `metadata` | Dict | Additional node information |

### Enums

#### NodeStatus

```python
class NodeStatus(Enum):
    ACTIVE = "active"      # Currently being explored
    EXPANDED = "expanded"  # Has been expanded
    PRUNED = "pruned"      # Pruned from exploration
    SOLUTION = "solution"  # Terminal solution node
```

#### NodeType

```python
class NodeType(Enum):
    ROOT = "root"              # Starting point
    EXPLORATION = "exploration" # Exploring options
    REFINEMENT = "refinement"  # Refining approach
    SOLUTION = "solution"      # Final solution
```

## Usage Examples

### Basic Usage

```python
from agenticraft.agents.reasoning import ReasoningAgent

# Create agent with Tree of Thoughts
agent = ReasoningAgent(
    name="Designer",
    reasoning_pattern="tree_of_thoughts"
)

# Explore design options
response = await agent.think_and_act(
    "Design a sustainable packaging solution for food delivery"
)

# Visualize the exploration
tree_viz = agent.advanced_reasoning.visualize_tree()
print(tree_viz)
```

### Advanced Configuration

```python
# Extensive exploration
exploratory_tot = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "max_depth": 6,           # Deeper exploration
        "beam_width": 5,          # More paths
        "exploration_factor": 0.5, # Higher creativity
        "pruning_threshold": 0.3  # Keep more branches
    }
)

# Focused search
focused_tot = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "max_depth": 3,           # Shallower
        "beam_width": 2,          # Fewer paths
        "exploration_factor": 0.1, # More focused
        "pruning_threshold": 0.6  # Aggressive pruning
    }
)
```

### Accessing Tree Structure

```python
# Get the reasoning tree
tot = agent.advanced_reasoning

# Explore all nodes
for node_id, node in tot.nodes.items():
    print(f"Node {node_id}: {node.thought[:50]}...")
    print(f"  Score: {node.score:.2f}")
    print(f"  Status: {node.status.value}")
    print(f"  Children: {len(node.children)}")

# Get pruned branches
pruned_nodes = [
    node for node in tot.nodes.values()
    if node.status == NodeStatus.PRUNED
]
print(f"Pruned {len(pruned_nodes)} branches")

# Find all solutions
solutions = tot.get_all_solutions()
print(f"Found {len(solutions)} complete solutions")
```

### Visualization Examples

```python
# Text visualization
text_tree = tot.visualize_tree(format="text")
print(text_tree)
"""
Root: Design sustainable packaging
├── Option 1: Biodegradable materials (0.75)
│   ├── Approach: Plant-based plastics (0.82)
│   │   └── Solution: Corn starch containers (0.88) ✓
│   └── Approach: Paper alternatives (0.70)
└── Option 2: Reusable systems (0.68)
    └── [PRUNED]
"""

# Mermaid diagram
mermaid = tot.visualize_tree(format="mermaid")
# Use in documentation or visualization tools

# JSON structure
json_tree = tot.visualize_tree(format="json")
# Parse for custom visualization
```

## Advanced Features

### Custom Evaluation Function

```python
class CustomTreeOfThoughts(TreeOfThoughtsReasoning):
    def _evaluate_node(self, node_id: str) -> float:
        node = self.nodes[node_id]
        base_score = super()._evaluate_node(node_id)
        
        # Add custom criteria
        if "innovative" in node.thought.lower():
            base_score += 0.1
        
        # Penalize complexity
        complexity = len(node.thought.split()) / 100
        base_score -= complexity * 0.05
        
        return max(0, min(1, base_score))
```

### Guided Exploration

```python
# Provide hints for exploration
context = {
    "constraints": ["eco-friendly", "cost-effective"],
    "avoid": ["single-use plastics"],
    "prefer": ["local materials"]
}

response = await agent.think_and_act(
    "Design packaging solution",
    context=context
)
```

### Parallel Exploration

```python
# Explore multiple problems simultaneously
problems = [
    "Design a logo for a tech startup",
    "Design a logo for a bakery",
    "Design a logo for a law firm"
]

# Run explorations in parallel
import asyncio
tasks = [agent.think_and_act(p) for p in problems]
results = await asyncio.gather(*tasks)

# Compare exploration patterns
for i, result in enumerate(results):
    print(f"\nProblem {i+1}: {problems[i]}")
    print(f"Solutions explored: {len(agent.advanced_reasoning.solution_nodes)}")
    print(f"Best score: {agent.advanced_reasoning.get_best_solution()['score']}")
```

## Performance Optimization

### Memory Management

```python
# For large explorations
memory_efficient_config = {
    "max_depth": 4,
    "beam_width": 3,
    "pruning_threshold": 0.5,  # Aggressive pruning
    "cache_thoughts": False     # Don't cache intermediate thoughts
}
```

### Early Stopping

```python
class EarlyStoppingToT(TreeOfThoughtsReasoning):
    def __init__(self, target_score: float = 0.9, **kwargs):
        super().__init__(**kwargs)
        self.target_score = target_score
    
    async def _explore_level(self, nodes: List[str], depth: int):
        # Check if we found good enough solution
        best = self.get_best_solution()
        if best and best['score'] >= self.target_score:
            return  # Stop exploration
        
        await super()._explore_level(nodes, depth)
```

### Batch Evaluation

```python
# Evaluate multiple nodes efficiently
async def batch_evaluate(self, node_ids: List[str]) -> Dict[str, float]:
    # Evaluate all nodes in one LLM call
    thoughts = [self.nodes[nid].thought for nid in node_ids]
    scores = await self._batch_score_thoughts(thoughts)
    return dict(zip(node_ids, scores))
```

## Common Issues and Solutions

### Issue: Exploration Explosion

**Symptom:** Too many nodes, slow performance
**Solution:**
```python
# Reduce exploration space
pattern_config = {
    "beam_width": 2,          # Fewer branches
    "pruning_threshold": 0.5, # More aggressive pruning
    "max_nodes": 50          # Hard limit on nodes
}
```

### Issue: Shallow Solutions

**Symptom:** All solutions are superficial
**Solution:**
```python
# Encourage deeper exploration
pattern_config = {
    "max_depth": 6,
    "depth_bonus": 0.1,  # Bonus for deeper nodes
    "exploration_factor": 0.4
}
```

### Issue: Similar Branches

**Symptom:** Many branches explore similar ideas
**Solution:**
```python
# Increase diversity
pattern_config = {
    "exploration_factor": 0.6,  # More randomness
    "diversity_penalty": 0.2,   # Penalize similar thoughts
    "min_branch_distance": 0.3  # Minimum semantic distance
}
```

## Integration Examples

### With Chain of Thought

```python
# Use ToT to explore, CoT to detail
explorer = ReasoningAgent(reasoning_pattern="tree_of_thoughts")
detailer = ReasoningAgent(reasoning_pattern="chain_of_thought")

# Explore options
options = await explorer.think_and_act("Design a new product")

# Detail the best option
best_option = explorer.advanced_reasoning.get_best_solution()
detailed_plan = await detailer.think_and_act(
    f"Create detailed plan for: {best_option['thoughts'][-1]}"
)
```

### With ReAct

```python
# Use ToT for strategy, ReAct for execution
strategy = await tot_agent.think_and_act("How to analyze this dataset?")
result = await react_agent.think_and_act(
    f"Execute strategy: {strategy.content}"
)
```

## Debugging and Analysis

```python
# Analyze tree exploration
analysis = tot._generate_tree_analysis()
print(f"Total nodes: {analysis['total_nodes']}")
print(f"Solution nodes: {analysis['solution_nodes']}")
print(f"Pruning rate: {analysis['pruning_rate']:.1%}")
print(f"Average branching: {analysis['avg_branching']:.1f}")
print(f"Max depth reached: {analysis['max_depth']}")

# Find bottlenecks
for depth in range(analysis['max_depth']):
    nodes_at_depth = [n for n in tot.nodes.values() if n.depth == depth]
    print(f"Depth {depth}: {len(nodes_at_depth)} nodes")
```

## See Also

- [Chain of Thought](chain_of_thought.md) - For linear reasoning
- [ReAct Pattern](react.md) - For tool-based exploration
- [Pattern Selector](selector.md) - Automatic pattern selection
- [Examples](../../../examples/reasoning/tree_of_thoughts_example.py) - Complete examples
