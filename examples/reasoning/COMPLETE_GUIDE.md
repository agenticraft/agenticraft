# AgentiCraft Reasoning Patterns - Complete Guide

This guide covers everything you need to know about AgentiCraft's advanced reasoning patterns: Chain of Thought (CoT), Tree of Thoughts (ToT), and ReAct.

## Table of Contents
1. [Overview](#overview)
2. [Pattern Deep Dive](#pattern-deep-dive)
3. [Configuration Reference](#configuration-reference)
4. [Integration Guide](#integration-guide)
5. [Performance Optimization](#performance-optimization)
6. [Production Patterns](#production-patterns)
7. [Troubleshooting](#troubleshooting)

## Overview

AgentiCraft provides three sophisticated reasoning patterns that enable agents to tackle complex problems with transparency and structure:

| Pattern | Best For | Key Feature | Performance |
|---------|----------|-------------|-------------|
| **Chain of Thought** | Step-by-step problems | Linear reasoning with confidence tracking | Fast, O(n) |
| **Tree of Thoughts** | Creative/design tasks | Explores multiple solution paths | Slower, O(b^d) |
| **ReAct** | Research & investigation | Combines reasoning with tool usage | Medium, O(n) + tools |

### Quick Decision Guide

```python
def select_pattern(problem: str) -> str:
    """Simple heuristic for pattern selection."""
    problem_lower = problem.lower()
    
    # Mathematical or logical problems → Chain of Thought
    if any(word in problem_lower for word in ["calculate", "solve", "explain", "analyze"]):
        return "chain_of_thought"
    
    # Creative or design problems → Tree of Thoughts
    elif any(word in problem_lower for word in ["design", "create", "options", "compare"]):
        return "tree_of_thoughts"
    
    # Research or tool-based problems → ReAct
    elif any(word in problem_lower for word in ["find", "search", "current", "data"]):
        return "react"
    
    # Default to Chain of Thought
    return "chain_of_thought"
```

## Pattern Deep Dive

### Chain of Thought (CoT)

Chain of Thought breaks down complex problems into sequential reasoning steps, tracking confidence and building solutions incrementally.

#### When to Use
- ✅ Mathematical calculations
- ✅ Logical deductions
- ✅ Step-by-step explanations
- ✅ Process analysis
- ❌ Creative tasks with multiple valid approaches
- ❌ Problems requiring external data

#### Basic Example
```python
from agenticraft.agents.reasoning import ReasoningAgent

# Create CoT agent
agent = ReasoningAgent(
    name="MathTutor",
    reasoning_pattern="chain_of_thought",
    instructions="Break down problems step by step with clear explanations.",
    pattern_config={
        "min_confidence": 0.8,  # Minimum confidence threshold
        "max_steps": 10        # Maximum reasoning steps
    }
)

# Solve problem
response = await agent.think_and_act(
    "If a car travels 120 miles in 2 hours, then stops for 30 minutes, "
    "then travels another 90 miles in 1.5 hours, what is the average speed "
    "for the entire trip including the stop?"
)

# Access reasoning
for step in response.reasoning_steps:
    print(f"Step {step.number}: {step.description}")
    print(f"  Confidence: {step.confidence:.0%}")
    print(f"  Details: {step.thought}")
```

#### Advanced Configuration
```python
# High-confidence CoT for critical decisions
critical_agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    pattern_config={
        "min_confidence": 0.9,      # Very high threshold
        "max_steps": 20,           # Allow more steps
        "require_confidence": True, # Fail if confidence too low
        "alternative_thoughts": 3   # Generate alternatives for low-confidence steps
    }
)

# Educational CoT with detailed explanations
tutor_agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    instructions="Explain each step in detail suitable for students.",
    pattern_config={
        "min_confidence": 0.7,
        "max_steps": 15,
        "verbose": True,           # Detailed step descriptions
        "include_examples": True   # Add examples to steps
    }
)
```

### Tree of Thoughts (ToT)

Tree of Thoughts explores multiple reasoning paths simultaneously, evaluating and pruning to find optimal solutions.

#### When to Use
- ✅ Design problems
- ✅ Strategic planning
- ✅ Creative tasks
- ✅ Optimization problems
- ❌ Simple linear problems
- ❌ Time-critical applications

#### Basic Example
```python
# Create ToT agent
agent = ReasoningAgent(
    name="Designer",
    reasoning_pattern="tree_of_thoughts",
    instructions="Explore multiple creative solutions.",
    pattern_config={
        "max_depth": 4,           # Tree depth
        "beam_width": 3,          # Paths per level
        "exploration_factor": 0.3, # Creativity vs focus
        "pruning_threshold": 0.4   # Min score to continue
    }
)

# Design task
response = await agent.think_and_act(
    "Design a mobile app for elderly users to stay connected with family. "
    "Consider ease of use, accessibility, and emotional connection."
)

# Visualize exploration
if hasattr(response, 'tree_visualization'):
    print(response.tree_visualization)

# Get top solutions
for i, solution in enumerate(response.top_solutions[:3]):
    print(f"\nSolution {i+1} (Score: {solution.score:.2f}):")
    print(solution.description)
```

#### Advanced Configuration
```python
# Highly exploratory ToT
creative_agent = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "max_depth": 6,
        "beam_width": 5,
        "exploration_factor": 0.7,  # High exploration
        "pruning_threshold": 0.2,   # Keep more paths
        "diversity_bonus": 0.2,     # Reward different approaches
        "convergence_penalty": 0.1  # Penalize similar paths
    }
)

# Focused optimization ToT
optimizer_agent = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "max_depth": 8,
        "beam_width": 2,           # Narrow search
        "exploration_factor": 0.1,  # Focus on best paths
        "pruning_threshold": 0.6,   # Aggressive pruning
        "use_mcts": True           # Monte Carlo tree search
    }
)
```

### ReAct Pattern

ReAct combines reasoning with actions, creating cycles of thinking, acting, and observing.

#### When to Use
- ✅ Research tasks
- ✅ Data gathering
- ✅ Troubleshooting
- ✅ Multi-step investigations
- ❌ Pure reasoning tasks
- ❌ No tools available

#### Basic Example
```python
from agenticraft.core.tool import tool

# Define tools
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implementation
    return f"Results for: {query}"

@tool
def calculate(expression: str) -> float:
    """Perform calculations."""
    return eval(expression)  # Use safe eval in production

# Create ReAct agent
agent = ReasoningAgent(
    name="Researcher",
    reasoning_pattern="react",
    tools=[search_web, calculate],
    pattern_config={
        "max_steps": 15,
        "max_retries": 2,
        "reflection_frequency": 3
    }
)

# Research task
response = await agent.think_and_act(
    "What is the population density of Tokyo and how does it "
    "compare to New York City? Calculate the ratio."
)

# View thought-action cycles
for cycle in response.reasoning_cycles:
    print(f"\nCycle {cycle.number}:")
    print(f"  Thought: {cycle.thought}")
    print(f"  Action: {cycle.action} - {cycle.tool_used}")
    print(f"  Observation: {cycle.observation}")
```

#### Advanced Configuration
```python
# Research-focused ReAct
research_agent = ReasoningAgent(
    reasoning_pattern="react",
    tools=[search_web, arxiv_search, calculate, summarize],
    pattern_config={
        "max_steps": 30,
        "parallel_tools": True,     # Run compatible tools in parallel
        "cache_results": True,      # Cache tool results
        "reflection_frequency": 5,
        "min_tool_confidence": 0.8, # Confidence before using tool
        "fallback_on_error": True   # Continue if tool fails
    }
)

# Diagnostic ReAct
diagnostic_agent = ReasoningAgent(
    reasoning_pattern="react",
    tools=[check_system, run_test, analyze_logs],
    pattern_config={
        "max_steps": 20,
        "systematic_exploration": True,  # Methodical tool use
        "hypothesis_tracking": True,     # Track and test hypotheses
        "confidence_threshold": 0.9      # High confidence for diagnostics
    }
)
```

## Configuration Reference

### Common Configuration Options

```python
# All patterns support these base options
base_config = {
    "temperature": 0.7,          # LLM temperature
    "max_tokens": 2000,         # Max response tokens
    "timeout": 30,              # Timeout in seconds
    "retry_on_error": True,     # Retry on failures
    "track_performance": True,  # Performance metrics
    "verbose": False            # Detailed logging
}
```

### Pattern-Specific Options

#### Chain of Thought
```python
cot_config = {
    "min_confidence": 0.7,       # Minimum acceptable confidence
    "max_steps": 15,            # Maximum reasoning steps
    "alternative_thoughts": 2,   # Alternatives for low confidence
    "confidence_decay": 0.95,   # Confidence decay per step
    "require_confidence": False, # Fail if below threshold
    "step_validation": True,    # Validate each step
    "synthesis_strategy": "weighted"  # How to combine steps
}
```

#### Tree of Thoughts
```python
tot_config = {
    "max_depth": 5,             # Maximum tree depth
    "beam_width": 3,            # Branches per level
    "exploration_factor": 0.3,  # 0=greedy, 1=random
    "pruning_threshold": 0.4,   # Min score to continue
    "diversity_bonus": 0.1,     # Reward diverse paths
    "convergence_penalty": 0.1, # Penalize similar paths
    "use_mcts": False,         # Monte Carlo tree search
    "evaluation_strategy": "llm", # How to score nodes
    "backpropagation": True    # Update parent scores
}
```

#### ReAct
```python
react_config = {
    "max_steps": 20,            # Maximum cycles
    "max_retries": 2,           # Tool retry attempts
    "reflection_frequency": 5,  # Reflect every N steps
    "parallel_tools": False,    # Parallel tool execution
    "cache_results": True,      # Cache tool results
    "tool_timeout": 10,         # Tool execution timeout
    "min_tool_confidence": 0.7, # Confidence before tool use
    "hypothesis_tracking": False, # Track hypotheses
    "systematic_exploration": False  # Methodical approach
}
```

## Integration Guide

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncio

app = FastAPI()

# Request models
class ReasoningRequest(BaseModel):
    query: str
    pattern: Optional[str] = None
    show_reasoning: bool = True
    config: Optional[dict] = None

class ReasoningResponse(BaseModel):
    answer: str
    pattern_used: str
    reasoning_steps: Optional[List[dict]] = None
    confidence: float
    execution_time: float

# Reasoning service
class ReasoningService:
    def __init__(self):
        self.agents = {}
        self._init_agents()
    
    def _init_agents(self):
        """Initialize agents for each pattern."""
        patterns = ["chain_of_thought", "tree_of_thoughts", "react"]
        
        for pattern in patterns:
            self.agents[pattern] = ReasoningAgent(
                name=f"{pattern}_agent",
                reasoning_pattern=pattern,
                pattern_config=self._get_default_config(pattern)
            )
    
    def _get_default_config(self, pattern: str) -> dict:
        """Get optimized default config for pattern."""
        configs = {
            "chain_of_thought": {"min_confidence": 0.8, "max_steps": 15},
            "tree_of_thoughts": {"max_depth": 4, "beam_width": 3},
            "react": {"max_steps": 20, "reflection_frequency": 5}
        }
        return configs.get(pattern, {})
    
    async def process(self, request: ReasoningRequest) -> ReasoningResponse:
        """Process reasoning request."""
        # Auto-select pattern if not specified
        pattern = request.pattern or self._select_pattern(request.query)
        
        # Get or create agent
        agent = self.agents.get(pattern)
        if not agent:
            raise HTTPException(400, f"Unknown pattern: {pattern}")
        
        # Apply custom config if provided
        if request.config:
            agent.pattern_config.update(request.config)
        
        # Execute with timeout
        try:
            start_time = asyncio.get_event_loop().time()
            
            response = await asyncio.wait_for(
                agent.think_and_act(request.query),
                timeout=30.0
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Prepare response
            result = ReasoningResponse(
                answer=response.content,
                pattern_used=pattern,
                confidence=self._calculate_confidence(response),
                execution_time=execution_time
            )
            
            # Add reasoning steps if requested
            if request.show_reasoning:
                result.reasoning_steps = [
                    {
                        "step": step.number,
                        "description": step.description,
                        "confidence": step.confidence,
                        "type": step.step_type
                    }
                    for step in response.reasoning_steps
                ]
            
            return result
            
        except asyncio.TimeoutError:
            raise HTTPException(504, "Request timed out")
        except Exception as e:
            raise HTTPException(500, f"Reasoning error: {str(e)}")
    
    def _select_pattern(self, query: str) -> str:
        """Auto-select best pattern for query."""
        # Use the selection heuristic from earlier
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["calculate", "solve", "explain"]):
            return "chain_of_thought"
        elif any(word in query_lower for word in ["design", "create", "options"]):
            return "tree_of_thoughts"
        elif any(word in query_lower for word in ["find", "search", "current"]):
            return "react"
        
        return "chain_of_thought"
    
    def _calculate_confidence(self, response) -> float:
        """Calculate average confidence from response."""
        if not response.reasoning_steps:
            return 0.0
        
        confidences = [s.confidence for s in response.reasoning_steps]
        return sum(confidences) / len(confidences)

# Initialize service
reasoning_service = ReasoningService()

# API endpoints
@app.post("/api/reason", response_model=ReasoningResponse)
async def reason(request: ReasoningRequest):
    """Process a reasoning request."""
    return await reasoning_service.process(request)

@app.get("/api/patterns")
async def get_patterns():
    """Get available reasoning patterns."""
    return {
        "patterns": [
            {
                "name": "chain_of_thought",
                "description": "Step-by-step linear reasoning",
                "best_for": ["calculations", "explanations", "analysis"]
            },
            {
                "name": "tree_of_thoughts",
                "description": "Explore multiple solution paths",
                "best_for": ["design", "creativity", "optimization"]
            },
            {
                "name": "react",
                "description": "Reasoning with tool usage",
                "best_for": ["research", "data gathering", "troubleshooting"]
            }
        ]
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "reasoning"}
```

### Gradio UI Integration

```python
import gradio as gr
import asyncio
from agenticraft.agents.reasoning import ReasoningAgent

class ReasoningUI:
    def __init__(self):
        self.agents = {
            "Chain of Thought": ReasoningAgent(reasoning_pattern="chain_of_thought"),
            "Tree of Thoughts": ReasoningAgent(reasoning_pattern="tree_of_thoughts"),
            "ReAct": ReasoningAgent(reasoning_pattern="react", tools=[...])
        }
    
    async def process(self, query, pattern, show_steps, show_tree, max_steps):
        """Process query with selected pattern."""
        agent = self.agents[pattern]
        
        # Update config
        if pattern == "Chain of Thought":
            agent.pattern_config["max_steps"] = max_steps
        elif pattern == "Tree of Thoughts":
            agent.pattern_config["max_depth"] = max_steps
        else:  # ReAct
            agent.pattern_config["max_steps"] = max_steps
        
        # Execute
        response = await agent.think_and_act(query)
        
        # Format output
        output = f"## Answer\n{response.content}\n\n"
        
        if show_steps:
            output += "## Reasoning Steps\n"
            for step in response.reasoning_steps:
                output += f"**Step {step.number}**: {step.description}\n"
                output += f"- Confidence: {step.confidence:.0%}\n"
                if hasattr(step, 'thought'):
                    output += f"- Details: {step.thought}\n"
                output += "\n"
        
        if show_tree and pattern == "Tree of Thoughts":
            output += "## Exploration Tree\n"
            output += "```\n"
            output += response.tree_visualization
            output += "\n```\n"
        
        return output
    
    def create_interface(self):
        """Create Gradio interface."""
        with gr.Blocks(title="AgentiCraft Reasoning Demo") as interface:
            gr.Markdown("# AgentiCraft Advanced Reasoning Patterns")
            gr.Markdown("Explore different reasoning patterns for problem solving.")
            
            with gr.Row():
                with gr.Column(scale=2):
                    query = gr.Textbox(
                        label="Your Question",
                        lines=3,
                        placeholder="Enter a problem or question..."
                    )
                    
                    pattern = gr.Radio(
                        choices=list(self.agents.keys()),
                        label="Reasoning Pattern",
                        value="Chain of Thought"
                    )
                    
                    with gr.Row():
                        show_steps = gr.Checkbox(
                            label="Show Reasoning Steps",
                            value=True
                        )
                        show_tree = gr.Checkbox(
                            label="Show Exploration Tree (ToT only)",
                            value=False
                        )
                    
                    max_steps = gr.Slider(
                        minimum=3,
                        maximum=20,
                        value=10,
                        step=1,
                        label="Max Steps/Depth"
                    )
                    
                    submit = gr.Button("Reason", variant="primary")
                
                with gr.Column(scale=3):
                    output = gr.Markdown(label="Response")
            
            # Examples
            gr.Examples(
                examples=[
                    ["Calculate the compound interest on $10,000 at 5% for 10 years", "Chain of Thought"],
                    ["Design a logo for an eco-friendly tech startup", "Tree of Thoughts"],
                    ["What's the current population of Tokyo and its growth rate?", "ReAct"]
                ],
                inputs=[query, pattern]
            )
            
            # Connect
            submit.click(
                fn=lambda *args: asyncio.run(self.process(*args)),
                inputs=[query, pattern, show_steps, show_tree, max_steps],
                outputs=output
            )
        
        return interface

# Launch UI
ui = ReasoningUI()
interface = ui.create_interface()
interface.launch(share=True)
```

## Performance Optimization

### Pattern-Specific Optimizations

#### Chain of Thought
```python
# Optimization strategies
class OptimizedCoTAgent:
    def __init__(self):
        self.agent = ReasoningAgent(
            reasoning_pattern="chain_of_thought",
            pattern_config={
                "max_steps": 10,  # Limit steps
                "early_stopping": True,  # Stop when confident
                "confidence_threshold": 0.9,  # Early stop threshold
                "step_caching": True,  # Cache intermediate results
                "parallel_alternatives": True  # Generate alternatives in parallel
            }
        )
        self.cache = {}
    
    async def think_cached(self, query: str) -> Any:
        """Think with caching."""
        cache_key = hashlib.md5(query.encode()).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        response = await self.agent.think_and_act(query)
        self.cache[cache_key] = response
        
        return response
```

#### Tree of Thoughts
```python
# Memory-efficient ToT
class EfficientToTAgent:
    def __init__(self):
        self.agent = ReasoningAgent(
            reasoning_pattern="tree_of_thoughts",
            pattern_config={
                "beam_width": 2,  # Narrow beam
                "pruning_threshold": 0.5,  # Aggressive pruning
                "max_depth": 4,  # Limit depth
                "lazy_evaluation": True,  # Evaluate only when needed
                "memory_limit_mb": 100,  # Memory cap
                "progressive_widening": True  # Start narrow, widen if needed
            }
        )
    
    async def think_progressive(self, query: str) -> Any:
        """Progressive exploration - start narrow, widen if needed."""
        for beam_width in [2, 3, 5]:
            self.agent.pattern_config["beam_width"] = beam_width
            response = await self.agent.think_and_act(query)
            
            if response.best_solution_score > 0.8:
                return response
        
        return response
```

#### ReAct
```python
# Optimized ReAct with tool result caching
class CachedReActAgent:
    def __init__(self, tools):
        self.agent = ReasoningAgent(
            reasoning_pattern="react",
            tools=tools,
            pattern_config={
                "cache_tool_results": True,
                "parallel_tools": True,
                "tool_timeout": 5,
                "max_retries": 1,
                "batch_similar_tools": True
            }
        )
        self.tool_cache = TTLCache(maxsize=1000, ttl=3600)
    
    async def execute_with_cache(self, query: str) -> Any:
        """Execute with tool result caching."""
        # Inject cache into agent
        self.agent.tool_cache = self.tool_cache
        
        return await self.agent.think_and_act(query)
```

### Batch Processing

```python
import asyncio
from typing import List, Dict

class BatchReasoningProcessor:
    def __init__(self, pattern: str, max_concurrent: int = 5):
        self.pattern = pattern
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.results = []
    
    async def process_batch(self, queries: List[str]) -> List[Dict]:
        """Process multiple queries concurrently."""
        tasks = [self._process_single(q) for q in queries]
        return await asyncio.gather(*tasks)
    
    async def _process_single(self, query: str) -> Dict:
        """Process single query with concurrency control."""
        async with self.semaphore:
            agent = ReasoningAgent(reasoning_pattern=self.pattern)
            
            try:
                start = asyncio.get_event_loop().time()
                response = await agent.think_and_act(query)
                duration = asyncio.get_event_loop().time() - start
                
                return {
                    "query": query,
                    "success": True,
                    "answer": response.content,
                    "pattern": self.pattern,
                    "steps": len(response.reasoning_steps),
                    "confidence": self._avg_confidence(response),
                    "duration": duration
                }
            except Exception as e:
                return {
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "pattern": self.pattern
                }
    
    def _avg_confidence(self, response) -> float:
        """Calculate average confidence."""
        if not response.reasoning_steps:
            return 0.0
        return sum(s.confidence for s in response.reasoning_steps) / len(response.reasoning_steps)

# Usage
processor = BatchReasoningProcessor("chain_of_thought", max_concurrent=10)
results = await processor.process_batch(queries)
```

## Production Patterns

### Service Layer Pattern

```python
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import logging

class ReasoningServiceLayer:
    """Production-ready reasoning service."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = {}
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "avg_duration": 0,
            "pattern_usage": {}
        }
        self.logger = logging.getLogger(__name__)
        self._init_agents()
    
    def _init_agents(self):
        """Initialize agents with production configs."""
        patterns = ["chain_of_thought", "tree_of_thoughts", "react"]
        
        for pattern in patterns:
            self.agents[pattern] = ReasoningAgent(
                name=f"{pattern}_agent",
                reasoning_pattern=pattern,
                pattern_config=self._get_production_config(pattern)
            )
    
    def _get_production_config(self, pattern: str) -> Dict:
        """Get production-optimized configs."""
        base_config = {
            "timeout": 30,
            "retry_on_error": True,
            "track_performance": True,
            "temperature": 0.7
        }
        
        pattern_configs = {
            "chain_of_thought": {
                "max_steps": 15,
                "min_confidence": 0.8,
                "early_stopping": True
            },
            "tree_of_thoughts": {
                "max_depth": 4,
                "beam_width": 3,
                "pruning_threshold": 0.5,
                "memory_limit_mb": 200
            },
            "react": {
                "max_steps": 20,
                "cache_tool_results": True,
                "tool_timeout": 10,
                "parallel_tools": True
            }
        }
        
        return {**base_config, **pattern_configs.get(pattern, {})}
    
    async def reason(
        self,
        query: str,
        pattern: Optional[str] = None,
        context: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main reasoning endpoint with full production features."""
        request_id = self._generate_request_id()
        start_time = datetime.utcnow()
        
        # Log request
        self.logger.info(f"Request {request_id}: {query[:100]}... | Pattern: {pattern}")
        
        try:
            # Select pattern
            pattern = pattern or self._select_pattern(query)
            
            # Get agent
            agent = self.agents.get(pattern)
            if not agent:
                raise ValueError(f"Unknown pattern: {pattern}")
            
            # Add context if provided
            if context:
                agent.add_context(context)
            
            # Execute with timeout
            response = await asyncio.wait_for(
                agent.think_and_act(query),
                timeout=self.config.get("global_timeout", 60)
            )
            
            # Calculate metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            confidence = self._calculate_confidence(response)
            
            # Update metrics
            self._update_metrics(pattern, duration, success=True)
            
            # Log success
            self.logger.info(
                f"Request {request_id} completed in {duration:.2f}s | "
                f"Steps: {len(response.reasoning_steps)} | "
                f"Confidence: {confidence:.2%}"
            )
            
            # Build response
            result = {
                "request_id": request_id,
                "success": True,
                "answer": response.content,
                "pattern_used": pattern,
                "confidence": confidence,
                "reasoning_steps": len(response.reasoning_steps),
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add reasoning details if not in production mode
            if self.config.get("include_reasoning", False):
                result["reasoning"] = [
                    {
                        "step": step.number,
                        "description": step.description,
                        "confidence": step.confidence
                    }
                    for step in response.reasoning_steps
                ]
            
            # Store for analysis if enabled
            if self.config.get("store_results", False):
                await self._store_result(request_id, result, user_id)
            
            return result
            
        except asyncio.TimeoutError:
            self._update_metrics(pattern, 0, success=False)
            self.logger.error(f"Request {request_id} timed out")
            
            return {
                "request_id": request_id,
                "success": False,
                "error": "Request timed out",
                "pattern_attempted": pattern,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self._update_metrics(pattern, 0, success=False)
            self.logger.error(f"Request {request_id} failed: {str(e)}")
            
            return {
                "request_id": request_id,
                "success": False,
                "error": str(e),
                "pattern_attempted": pattern,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return f"req_{uuid.uuid4().hex[:8]}"
    
    def _select_pattern(self, query: str) -> str:
        """Intelligent pattern selection."""
        # Could use ML model here
        query_lower = query.lower()
        
        # Check for pattern hints in query
        if "step by step" in query_lower:
            return "chain_of_thought"
        elif "explore" in query_lower or "options" in query_lower:
            return "tree_of_thoughts"
        elif "find" in query_lower or "search" in query_lower:
            return "react"
        
        # Use keyword matching
        keywords = {
            "chain_of_thought": ["calculate", "explain", "solve", "analyze"],
            "tree_of_thoughts": ["design", "create", "compare", "optimize"],
            "react": ["current", "latest", "research", "data"]
        }
        
        scores = {pattern: 0 for pattern in keywords}
        
        for pattern, words in keywords.items():
            for word in words:
                if word in query_lower:
                    scores[pattern] += 1
        
        # Return pattern with highest score
        best_pattern = max(scores, key=scores.get)
        return best_pattern if scores[best_pattern] > 0 else "chain_of_thought"
    
    def _calculate_confidence(self, response) -> float:
        """Calculate average confidence."""
        if not response.reasoning_steps:
            return 0.0
        
        confidences = [s.confidence for s in response.reasoning_steps]
        return sum(confidences) / len(confidences)
    
    def _update_metrics(self, pattern: str, duration: float, success: bool):
        """Update service metrics."""
        self.metrics["requests"] += 1
        
        if success:
            self.metrics["successes"] += 1
            
            # Update average duration
            total_duration = self.metrics["avg_duration"] * (self.metrics["successes"] - 1)
            self.metrics["avg_duration"] = (total_duration + duration) / self.metrics["successes"]
        else:
            self.metrics["failures"] += 1
        
        # Update pattern usage
        if pattern not in self.metrics["pattern_usage"]:
            self.metrics["pattern_usage"][pattern] = 0
        self.metrics["pattern_usage"][pattern] += 1
    
    async def _store_result(self, request_id: str, result: Dict, user_id: Optional[str]):
        """Store result for analysis (implement based on your storage)."""
        # Example: store in database or S3
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            **self.metrics,
            "success_rate": self.metrics["successes"] / max(self.metrics["requests"], 1),
            "failure_rate": self.metrics["failures"] / max(self.metrics["requests"], 1)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Service health check."""
        checks = {
            "service": "healthy",
            "agents_loaded": len(self.agents),
            "total_requests": self.metrics["requests"],
            "success_rate": self.get_metrics()["success_rate"]
        }
        
        # Check each agent
        for pattern, agent in self.agents.items():
            try:
                # Quick test
                test_response = asyncio.run(agent.think_and_act("test"))
                checks[f"agent_{pattern}"] = "healthy"
            except:
                checks[f"agent_{pattern}"] = "unhealthy"
        
        checks["overall_status"] = "healthy" if all(
            v == "healthy" for k, v in checks.items() 
            if k.startswith("agent_")
        ) else "degraded"
        
        return checks

# Usage
config = {
    "global_timeout": 60,
    "include_reasoning": False,  # Set True for development
    "store_results": True,
    "cache_enabled": True
}

service = ReasoningServiceLayer(config)

# Use in API
async def handle_request(query: str, user_id: str):
    result = await service.reason(query, user_id=user_id)
    return result

# Get metrics
metrics = service.get_metrics()
health = service.health_check()
```

### Monitoring Integration

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Prometheus metrics
reasoning_requests = Counter(
    'reasoning_requests_total',
    'Total reasoning requests',
    ['pattern', 'status']
)

reasoning_duration = Histogram(
    'reasoning_duration_seconds',
    'Reasoning request duration',
    ['pattern']
)

reasoning_confidence = Gauge(
    'reasoning_confidence',
    'Average reasoning confidence',
    ['pattern']
)

active_reasoning = Gauge(
    'active_reasoning_requests',
    'Currently active reasoning requests'
)

class MonitoredReasoningService(ReasoningServiceLayer):
    """Reasoning service with Prometheus monitoring."""
    
    async def reason(self, query: str, **kwargs):
        """Reasoning with monitoring."""
        pattern = kwargs.get('pattern') or self._select_pattern(query)
        
        # Track active requests
        active_reasoning.inc()
        
        # Time the request
        start_time = time.time()
        
        try:
            result = await super().reason(query, **kwargs)
            
            # Update metrics
            reasoning_requests.labels(pattern=pattern, status='success').inc()
            duration = time.time() - start_time
            reasoning_duration.labels(pattern=pattern).observe(duration)
            
            if result.get('confidence'):
                reasoning_confidence.labels(pattern=pattern).set(result['confidence'])
            
            return result
            
        except Exception as e:
            reasoning_requests.labels(pattern=pattern, status='error').inc()
            raise
            
        finally:
            active_reasoning.dec()
```

## Troubleshooting

### Common Issues and Solutions

#### Chain of Thought Issues

**Problem**: Reasoning gets stuck in loops
```python
# Solution: Add loop detection
class LoopDetectionCoT:
    def __init__(self):
        self.agent = ReasoningAgent(
            reasoning_pattern="chain_of_thought",
            pattern_config={
                "max_steps": 10,
                "loop_detection": True,
                "loop_threshold": 0.8  # Similarity threshold
            }
        )
```

**Problem**: Low confidence throughout
```python
# Solution: Use alternative thoughts
agent = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    pattern_config={
        "alternative_thoughts": 3,
        "min_confidence": 0.6,
        "confidence_aggregation": "max"  # Use best alternative
    }
)
```

#### Tree of Thoughts Issues

**Problem**: Memory usage too high
```python
# Solution: Implement memory limits
agent = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "memory_limit_mb": 100,
        "progressive_pruning": True,
        "keep_only_solutions": True  # Don't store intermediate nodes
    }
)
```

**Problem**: Takes too long to explore
```python
# Solution: Use adaptive exploration
agent = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={
        "adaptive_depth": True,     # Reduce depth if taking too long
        "time_limit_seconds": 10,   # Hard time limit
        "early_termination": True   # Stop if good solution found
    }
)
```

#### ReAct Issues

**Problem**: Tools fail frequently
```python
# Solution: Implement robust tool handling
class RobustReActAgent:
    def __init__(self, tools):
        self.agent = ReasoningAgent(
            reasoning_pattern="react",
            tools=self._wrap_tools(tools),
            pattern_config={
                "max_retries": 3,
                "fallback_on_error": True,
                "alternative_tools": True  # Try similar tools
            }
        )
    
    def _wrap_tools(self, tools):
        """Wrap tools with error handling."""
        wrapped = []
        for tool in tools:
            wrapped.append(self._create_robust_tool(tool))
        return wrapped
    
    def _create_robust_tool(self, tool):
        """Create robust version of tool."""
        async def robust_execute(*args, **kwargs):
            try:
                return await tool.execute(*args, **kwargs)
            except Exception as e:
                # Log error
                print(f"Tool {tool.name} failed: {e}")
                # Return informative error
                return f"Tool error: {str(e)[:100]}"
        
        # Create new tool with robust execute
        from types import SimpleNamespace
        return SimpleNamespace(
            name=tool.name,
            description=tool.description,
            execute=robust_execute
        )
```

**Problem**: Wrong pattern selected
```python
# Solution: Override or improve selection
class ImprovedPatternSelector:
    def __init__(self):
        # Could use a trained classifier here
        self.pattern_rules = {
            "must_use_cot": ["explain", "prove", "derive"],
            "must_use_tot": ["design", "creative", "brainstorm"],
            "must_use_react": ["search", "find", "current", "real-time"]
        }
    
    def select(self, query: str, hint: Optional[str] = None) -> str:
        """Improved pattern selection."""
        # Check hint first
        if hint and hint in ["chain_of_thought", "tree_of_thoughts", "react"]:
            return hint
        
        query_lower = query.lower()
        
        # Check strict rules
        for pattern, keywords in self.pattern_rules.items():
            if any(keyword in query_lower for keyword in keywords):
                return pattern.replace("must_use_", "")
        
        # Use scoring system
        scores = self._calculate_scores(query_lower)
        return max(scores, key=scores.get)
```

### Performance Debugging

```python
import cProfile
import pstats
from io import StringIO

class ProfilingReasoningAgent:
    """Agent with built-in profiling."""
    
    def __init__(self, pattern: str):
        self.agent = ReasoningAgent(reasoning_pattern=pattern)
        self.profiler = cProfile.Profile()
    
    async def think_and_profile(self, query: str):
        """Think and generate performance profile."""
        self.profiler.enable()
        
        try:
            response = await self.agent.think_and_act(query)
            return response
        finally:
            self.profiler.disable()
            
            # Generate report
            s = StringIO()
            ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            print("\nPerformance Profile:")
            print(s.getvalue())
```

### Memory Profiling

```python
import tracemalloc
import gc

class MemoryProfilingAgent:
    """Agent with memory profiling."""
    
    async def think_with_memory_tracking(self, query: str, pattern: str):
        """Track memory usage during reasoning."""
        gc.collect()
        tracemalloc.start()
        
        agent = ReasoningAgent(reasoning_pattern=pattern)
        
        # Snapshot before
        snapshot1 = tracemalloc.take_snapshot()
        
        # Execute
        response = await agent.think_and_act(query)
        
        # Snapshot after
        snapshot2 = tracemalloc.take_snapshot()
        
        # Calculate difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print("\nMemory Usage:")
        for stat in top_stats[:10]:
            print(stat)
        
        # Get peak
        current, peak = tracemalloc.get_traced_memory()
        print(f"\nPeak memory usage: {peak / 1024 / 1024:.1f} MB")
        
        tracemalloc.stop()
        return response
```

## Summary

This guide covered:

1. **Pattern Selection**: When and how to use each reasoning pattern
2. **Configuration**: Detailed options for optimizing each pattern  
3. **Integration**: FastAPI, Gradio, and service layer examples
4. **Performance**: Optimization strategies and monitoring
5. **Production**: Robust patterns for real-world deployment
6. **Troubleshooting**: Common issues and solutions

Key takeaways:
- Choose patterns based on problem type, not preference
- Start with defaults, optimize based on metrics
- Implement proper error handling and monitoring
- Cache aggressively for production performance
- Use batch processing for multiple queries

For hands-on examples, see the example files in this directory:
- `reasoning_demo.py` - Introduction to all patterns
- `chain_of_thought.py` - CoT deep dive
- `tree_of_thoughts.py` - ToT exploration  
- `react.py` - ReAct with tools
- `pattern_comparison.py` - Side-by-side comparison
- `production_handlers.py` - Production patterns
- `reasoning_transparency.py` - Understanding AI thinking

Happy reasoning! 🧠✨
