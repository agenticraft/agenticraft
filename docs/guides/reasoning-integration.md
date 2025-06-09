# Reasoning Patterns Integration Guide

This guide shows how to integrate AgentiCraft's reasoning patterns into your existing applications.

## Quick Integration

### 1. Drop-in Replacement

If you're using basic agents, upgrade to reasoning agents:

```python
# Before
from agenticraft import Agent

agent = Agent(name="Assistant")
response = await agent.run("Solve this problem")

# After
from agenticraft.agents.reasoning import ReasoningAgent

agent = ReasoningAgent(
    name="Assistant",
    reasoning_pattern="chain_of_thought"  # or auto-select
)
response = await agent.think_and_act("Solve this problem")
```

### 2. FastAPI Integration

```python
from fastapi import FastAPI
from agenticraft.agents.reasoning import ReasoningAgent
from agenticraft.reasoning.patterns.selector import PatternSelector

app = FastAPI()

# Initialize agents
agents = {}

@app.on_event("startup")
async def setup_agents():
    """Initialize reasoning agents on startup."""
    agents["default"] = ReasoningAgent(name="Assistant")
    agents["analyst"] = ReasoningAgent(
        name="Analyst",
        reasoning_pattern="chain_of_thought"
    )
    agents["designer"] = ReasoningAgent(
        name="Designer",
        reasoning_pattern="tree_of_thoughts"
    )

@app.post("/api/reason")
async def reason(query: str, pattern: str = None):
    """Process query with reasoning."""
    # Auto-select pattern if not specified
    if not pattern:
        pattern = PatternSelector.select_pattern(query)
    
    # Use default agent with selected pattern
    agent = agents["default"]
    agent.reasoning_pattern = pattern
    
    response = await agent.think_and_act(query)
    
    return {
        "answer": response.content,
        "pattern_used": pattern,
        "reasoning_steps": len(response.reasoning_steps),
        "confidence": sum(s.confidence for s in response.reasoning_steps) / len(response.reasoning_steps)
    }
```

### 3. Gradio Interface

```python
import gradio as gr
from agenticraft.agents.reasoning import ReasoningAgent

async def process_with_reasoning(query, pattern, show_steps):
    """Process query and return formatted results."""
    agent = ReasoningAgent(reasoning_pattern=pattern)
    response = await agent.think_and_act(query)
    
    output = f"**Answer:** {response.content}\n\n"
    
    if show_steps:
        output += "**Reasoning Process:**\n"
        for step in response.reasoning_steps:
            output += f"{step.number}. {step.description}\n"
            output += f"   Confidence: {step.confidence:.0%}\n\n"
    
    return output

# Create interface
interface = gr.Interface(
    fn=process_with_reasoning,
    inputs=[
        gr.Textbox(label="Your Question"),
        gr.Dropdown(
            choices=["chain_of_thought", "tree_of_thoughts", "react"],
            label="Reasoning Pattern"
        ),
        gr.Checkbox(label="Show Reasoning Steps", value=True)
    ],
    outputs=gr.Markdown(),
    title="AgentiCraft Reasoning Demo"
)

interface.launch()
```

## Production Patterns

### 1. Service Layer Pattern

```python
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

class ReasoningService:
    """Centralized reasoning service for your application."""
    
    def __init__(self):
        self.agents = {}
        self.metrics = {
            "total_requests": 0,
            "pattern_usage": {},
            "average_confidence": 0.0
        }
    
    async def initialize(self):
        """Initialize agents and tools."""
        # Basic agents for each pattern
        self.agents["cot"] = ReasoningAgent(
            name="Analyst",
            reasoning_pattern="chain_of_thought"
        )
        
        self.agents["tot"] = ReasoningAgent(
            name="Explorer", 
            reasoning_pattern="tree_of_thoughts"
        )
        
        # ReAct with tools
        from agenticraft.tools import SearchTool, CalculatorTool
        self.agents["react"] = ReasoningAgent(
            name="Researcher",
            reasoning_pattern="react",
            tools=[SearchTool(), CalculatorTool()]
        )
    
    async def process(
        self,
        query: str,
        pattern: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process query with reasoning."""
        start_time = datetime.now()
        
        # Auto-select pattern if needed
        if not pattern:
            from agenticraft.reasoning.patterns.selector import PatternSelector
            pattern = PatternSelector.select_pattern(query)
        
        # Map pattern to agent
        agent_key = {
            "chain_of_thought": "cot",
            "tree_of_thoughts": "tot",
            "react": "react"
        }.get(pattern, "cot")
        
        agent = self.agents[agent_key]
        
        try:
            # Execute reasoning
            response = await agent.think_and_act(query, context)
            
            # Calculate metrics
            duration = (datetime.now() - start_time).total_seconds()
            avg_confidence = sum(
                s.confidence for s in response.reasoning_steps
            ) / len(response.reasoning_steps)
            
            # Update service metrics
            self._update_metrics(pattern, avg_confidence)
            
            return {
                "success": True,
                "answer": response.content,
                "pattern": pattern,
                "reasoning": {
                    "steps": len(response.reasoning_steps),
                    "confidence": avg_confidence,
                    "duration": duration
                },
                "metadata": response.metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pattern": pattern
            }
    
    def _update_metrics(self, pattern: str, confidence: float):
        """Update service metrics."""
        self.metrics["total_requests"] += 1
        
        if pattern not in self.metrics["pattern_usage"]:
            self.metrics["pattern_usage"][pattern] = 0
        self.metrics["pattern_usage"][pattern] += 1
        
        # Update rolling average confidence
        n = self.metrics["total_requests"]
        self.metrics["average_confidence"] = (
            (self.metrics["average_confidence"] * (n - 1) + confidence) / n
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return self.metrics
```

### 2. Caching Layer

```python
import hashlib
from functools import lru_cache
import pickle
import redis

class CachedReasoningService(ReasoningService):
    """Reasoning service with caching."""
    
    def __init__(self, redis_url: str = None):
        super().__init__()
        self.cache = redis.from_url(redis_url) if redis_url else {}
        self.cache_ttl = 3600  # 1 hour
    
    def _cache_key(self, query: str, pattern: str, context: Dict) -> str:
        """Generate cache key."""
        data = f"{query}:{pattern}:{sorted(context.items()) if context else ''}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def process(
        self,
        query: str,
        pattern: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Process with caching."""
        if not use_cache:
            return await super().process(query, pattern, context)
        
        # Check cache
        cache_key = self._cache_key(query, pattern or "auto", context or {})
        
        if isinstance(self.cache, dict):
            # In-memory cache
            if cache_key in self.cache:
                return self.cache[cache_key]
        else:
            # Redis cache
            cached = self.cache.get(cache_key)
            if cached:
                return pickle.loads(cached)
        
        # Process and cache
        result = await super().process(query, pattern, context)
        
        if result["success"]:
            if isinstance(self.cache, dict):
                self.cache[cache_key] = result
            else:
                self.cache.setex(
                    cache_key,
                    self.cache_ttl,
                    pickle.dumps(result)
                )
        
        return result
```

### 3. Async Queue Processing

```python
from asyncio import Queue, create_task
from typing import List

class QueuedReasoningService(ReasoningService):
    """Process reasoning requests through a queue."""
    
    def __init__(self, max_workers: int = 5):
        super().__init__()
        self.queue = Queue()
        self.max_workers = max_workers
        self.workers = []
    
    async def start(self):
        """Start worker tasks."""
        await self.initialize()
        
        for i in range(self.max_workers):
            worker = create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Stop all workers."""
        for worker in self.workers:
            worker.cancel()
    
    async def _worker(self, name: str):
        """Worker to process queue items."""
        while True:
            try:
                item = await self.queue.get()
                
                # Process the request
                result = await super().process(
                    item["query"],
                    item.get("pattern"),
                    item.get("context")
                )
                
                # Call callback with result
                if item.get("callback"):
                    await item["callback"](result)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {name} error: {e}")
    
    async def enqueue(
        self,
        query: str,
        pattern: Optional[str] = None,
        context: Optional[Dict] = None,
        callback: Optional[callable] = None
    ):
        """Add request to queue."""
        await self.queue.put({
            "query": query,
            "pattern": pattern,
            "context": context,
            "callback": callback
        })
```

## Domain-Specific Applications

### 1. Customer Support System

```python
class SupportReasoningSystem:
    """Customer support with reasoning."""
    
    def __init__(self):
        self.classifier = ReasoningAgent(
            name="Classifier",
            reasoning_pattern="chain_of_thought"
        )
        
        self.resolver = ReasoningAgent(
            name="Resolver",
            reasoning_pattern="react",
            tools=[KnowledgeBaseTool(), TicketSystemTool()]
        )
    
    async def handle_ticket(self, ticket: Dict) -> Dict:
        """Process support ticket with reasoning."""
        # Classify the issue
        classification = await self.classifier.think_and_act(
            f"Classify this support ticket: {ticket['description']}\n"
            "Categories: technical, billing, general"
        )
        
        # Resolve based on classification
        if "technical" in classification.content.lower():
            solution = await self.resolver.think_and_act(
                f"Resolve technical issue: {ticket['description']}"
            )
        else:
            solution = await self.resolver.think_and_act(
                f"Handle {classification.content} issue: {ticket['description']}"
            )
        
        return {
            "ticket_id": ticket["id"],
            "classification": classification.content,
            "solution": solution.content,
            "confidence": solution.confidence,
            "reasoning_steps": len(solution.reasoning_steps)
        }
```

### 2. Educational Platform

```python
class TeachingAssistant:
    """Educational assistant with adaptive reasoning."""
    
    def __init__(self):
        self.explainer = ReasoningAgent(
            name="Explainer",
            reasoning_pattern="chain_of_thought",
            pattern_config={
                "min_confidence": 0.8,
                "max_steps": 15
            }
        )
        
        self.problem_solver = ReasoningAgent(
            name="Solver",
            reasoning_pattern="chain_of_thought"
        )
        
        self.creative = ReasoningAgent(
            name="Creative",
            reasoning_pattern="tree_of_thoughts"
        )
    
    async def help_student(
        self,
        question: str,
        student_level: str = "intermediate"
    ) -> Dict:
        """Provide adaptive help based on question type."""
        # Determine question type
        if any(word in question.lower() for word in ["explain", "what is", "how does"]):
            agent = self.explainer
            prompt = f"Explain to a {student_level} student: {question}"
        
        elif any(word in question.lower() for word in ["solve", "calculate", "find"]):
            agent = self.problem_solver
            prompt = f"Solve step-by-step: {question}"
        
        elif any(word in question.lower() for word in ["create", "design", "write"]):
            agent = self.creative
            prompt = f"Help a {student_level} student: {question}"
        
        else:
            agent = self.explainer
            prompt = question
        
        # Get response with reasoning
        response = await agent.think_and_act(prompt)
        
        # Format for student
        return {
            "answer": response.content,
            "steps": [
                {
                    "number": step.number,
                    "explanation": step.description,
                    "confidence": step.confidence
                }
                for step in response.reasoning_steps
            ],
            "pattern_used": agent.reasoning_pattern_name,
            "additional_resources": self._get_resources(question)
        }
    
    def _get_resources(self, question: str) -> List[str]:
        """Get additional learning resources."""
        # Implementation depends on your resource system
        return []
```

### 3. Data Analysis Platform

```python
class DataAnalysisService:
    """Data analysis with reasoning patterns."""
    
    def __init__(self):
        from agenticraft.tools import (
            DatabaseTool, VisualizationTool, 
            StatisticsTool, ExportTool
        )
        
        self.analyzer = ReasoningAgent(
            name="DataAnalyst",
            reasoning_pattern="react",
            tools=[
                DatabaseTool(),
                StatisticsTool(),
                VisualizationTool(),
                ExportTool()
            ],
            pattern_config={
                "max_steps": 25,
                "reflection_frequency": 5
            }
        )
        
        self.explorer = ReasoningAgent(
            name="DataExplorer",
            reasoning_pattern="tree_of_thoughts"
        )
    
    async def analyze_dataset(
        self,
        dataset_id: str,
        analysis_type: str = "exploratory"
    ) -> Dict:
        """Analyze dataset with appropriate reasoning."""
        if analysis_type == "exploratory":
            # Use Tree of Thoughts to explore different angles
            result = await self.explorer.think_and_act(
                f"Explore dataset {dataset_id} from multiple perspectives. "
                "Consider: patterns, anomalies, insights, visualizations"
            )
            
        elif analysis_type == "hypothesis":
            # Use ReAct for hypothesis testing
            result = await self.analyzer.think_and_act(
                f"Test hypothesis on dataset {dataset_id}: "
                f"{analysis_type}"
            )
            
        else:
            # General analysis with ReAct
            result = await self.analyzer.think_and_act(
                f"Perform {analysis_type} analysis on dataset {dataset_id}"
            )
        
        return {
            "dataset_id": dataset_id,
            "analysis_type": analysis_type,
            "findings": result.content,
            "visualizations": self._extract_visualizations(result),
            "tool_usage": self._extract_tool_usage(result),
            "confidence": result.confidence
        }
    
    def _extract_visualizations(self, result):
        """Extract any visualizations created."""
        # Implementation depends on your visualization system
        return []
    
    def _extract_tool_usage(self, result):
        """Extract tool usage statistics."""
        tools_used = {}
        for step in result.reasoning_steps:
            if hasattr(step, 'tool_used') and step.tool_used:
                tools_used[step.tool_used] = tools_used.get(step.tool_used, 0) + 1
        return tools_used
```

## Performance Optimization

### 1. Pattern-Specific Optimization

```python
class OptimizedReasoningService(ReasoningService):
    """Service with pattern-specific optimizations."""
    
    async def initialize(self):
        await super().initialize()
        
        # Optimize Chain of Thought for speed
        self.agents["cot"].pattern_config = {
            "max_steps": 8,  # Limit steps
            "min_confidence": 0.65,  # Lower threshold
            "early_stopping": True
        }
        
        # Optimize Tree of Thoughts for focused search
        self.agents["tot"].pattern_config = {
            "beam_width": 2,  # Narrow beam
            "max_depth": 3,  # Shallow tree
            "pruning_threshold": 0.5,  # Aggressive pruning
            "cache_evaluations": True
        }
        
        # Optimize ReAct for minimal tool calls
        self.agents["react"].pattern_config = {
            "max_steps": 10,
            "tool_timeout": 5.0,  # 5 second timeout
            "batch_similar_actions": True,
            "cache_tool_results": True
        }
```

### 2. Load Balancing

```python
class LoadBalancedReasoningService:
    """Distribute reasoning across multiple instances."""
    
    def __init__(self, num_instances: int = 3):
        self.instances = [
            ReasoningService() for _ in range(num_instances)
        ]
        self.current = 0
        self.load_stats = {i: 0 for i in range(num_instances)}
    
    async def initialize_all(self):
        """Initialize all instances."""
        tasks = [instance.initialize() for instance in self.instances]
        await asyncio.gather(*tasks)
    
    async def process(self, query: str, **kwargs) -> Dict:
        """Process using round-robin load balancing."""
        instance = self.instances[self.current]
        self.current = (self.current + 1) % len(self.instances)
        
        # Track load
        instance_id = self.current
        self.load_stats[instance_id] += 1
        
        result = await instance.process(query, **kwargs)
        result["instance_id"] = instance_id
        
        return result
    
    def get_load_stats(self) -> Dict[int, int]:
        """Get load distribution statistics."""
        return self.load_stats
```

## Monitoring and Observability

### 1. Metrics Collection

```python
import time
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
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

class MonitoredReasoningService(ReasoningService):
    """Service with Prometheus metrics."""
    
    async def process(self, query: str, **kwargs) -> Dict:
        pattern = kwargs.get('pattern', 'auto')
        
        start_time = time.time()
        
        try:
            result = await super().process(query, **kwargs)
            
            # Record metrics
            reasoning_requests.labels(
                pattern=pattern,
                status='success'
            ).inc()
            
            duration = time.time() - start_time
            reasoning_duration.labels(pattern=pattern).observe(duration)
            
            if result.get('reasoning', {}).get('confidence'):
                reasoning_confidence.labels(pattern=pattern).set(
                    result['reasoning']['confidence']
                )
            
            return result
            
        except Exception as e:
            reasoning_requests.labels(
                pattern=pattern,
                status='error'
            ).inc()
            raise
```

### 2. Logging Integration

```python
import logging
import json

class LoggedReasoningService(ReasoningService):
    """Service with structured logging."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    async def process(self, query: str, **kwargs) -> Dict:
        request_id = kwargs.get('request_id', 'unknown')
        
        self.logger.info(
            "Reasoning request started",
            extra={
                "request_id": request_id,
                "query_length": len(query),
                "pattern": kwargs.get('pattern', 'auto')
            }
        )
        
        try:
            result = await super().process(query, **kwargs)
            
            self.logger.info(
                "Reasoning request completed",
                extra={
                    "request_id": request_id,
                    "pattern": result['pattern'],
                    "steps": result['reasoning']['steps'],
                    "confidence": result['reasoning']['confidence'],
                    "duration": result['reasoning']['duration']
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Reasoning request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "pattern": kwargs.get('pattern', 'auto')
                },
                exc_info=True
            )
            raise
```

## Testing Strategies

### 1. Unit Testing

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_reasoning_service():
    """Test basic reasoning service functionality."""
    service = ReasoningService()
    await service.initialize()
    
    # Test auto-selection
    result = await service.process("Explain photosynthesis")
    assert result["success"]
    assert result["pattern"] == "chain_of_thought"
    
    # Test specific pattern
    result = await service.process(
        "Design a logo",
        pattern="tree_of_thoughts"
    )
    assert result["success"]
    assert result["pattern"] == "tree_of_thoughts"
    
    # Test with context
    result = await service.process(
        "Analyze data",
        context={"domain": "finance"}
    )
    assert result["success"]
    assert "reasoning" in result
```

### 2. Integration Testing

```python
@pytest.mark.asyncio
async def test_full_integration():
    """Test complete integration flow."""
    # Initialize service
    service = CachedReasoningService()
    await service.initialize()
    
    # First request (cache miss)
    start = time.time()
    result1 = await service.process("What is machine learning?")
    duration1 = time.time() - start
    
    assert result1["success"]
    
    # Second request (cache hit)
    start = time.time()
    result2 = await service.process("What is machine learning?")
    duration2 = time.time() - start
    
    assert result2 == result1
    assert duration2 < duration1 * 0.1  # Should be much faster
```

## Deployment Considerations

### 1. Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Environment variables
ENV AGENTICRAFT_LOG_LEVEL=INFO
ENV AGENTICRAFT_CACHE_ENABLED=true

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reasoning-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: reasoning-service
  template:
    metadata:
      labels:
        app: reasoning-service
    spec:
      containers:
      - name: reasoning
        image: agenticraft/reasoning-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: redis://redis-service:6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: reasoning-service
spec:
  selector:
    app: reasoning-service
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Best Practices Summary

1. **Start Simple**: Use automatic pattern selection initially
2. **Monitor Performance**: Track metrics to optimize patterns
3. **Cache Wisely**: Cache reasoning results for common queries
4. **Handle Errors**: Gracefully handle pattern failures
5. **Scale Appropriately**: Use load balancing for high traffic
6. **Test Thoroughly**: Test each pattern with your use cases
7. **Document Patterns**: Document which patterns work best for your domain

## Next Steps

- Explore [Pattern API Reference](../api/reasoning/index.md)
- Check out [Examples](../examples/reasoning/)
- Read about [Performance Tuning](performance-tuning.md)
- Join our [Discord](https://discord.gg/agenticraft) for support

---

With these integration patterns, you can seamlessly add advanced reasoning to any application, from simple scripts to complex production systems.
