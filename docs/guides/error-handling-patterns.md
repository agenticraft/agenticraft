# Error Handling Patterns for Multi-Agent Systems

This guide covers error handling patterns specifically designed for multi-agent systems in AgentiCraft.

## Table of Contents

1. [Multi-Agent Challenges](#multi-agent-challenges)
2. [Agent-Level Error Handling](#agent-level-error-handling)
3. [Workflow-Level Error Handling](#workflow-level-error-handling)
4. [Coordination Failures](#coordination-failures)
5. [Recovery Strategies](#recovery-strategies)
6. [Testing Error Scenarios](#testing-error-scenarios)

## Multi-Agent Challenges

Multi-agent systems face unique error scenarios:

1. **Partial Failures**: Some agents succeed while others fail
2. **Cascade Failures**: One agent's failure affects others
3. **Coordination Breakdown**: Communication between agents fails
4. **Resource Contention**: Agents compete for limited resources
5. **Consensus Issues**: Agents disagree on results

## Agent-Level Error Handling

### 1. Self-Healing Agents

Agents that can recover from failures independently:

```python
from agenticraft.core import Agent
from agenticraft.utils.decorators import retry, fallback, timeout

class SelfHealingAgent(Agent):
    """Agent with built-in error recovery."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failure_count = 0
        self.max_failures = 3
    
    @retry(attempts=3, backoff="exponential")
    @timeout(seconds=30)
    async def process(self, task: str, context: Dict[str, Any] = None):
        """Process with automatic recovery."""
        try:
            result = await super().process(task, context)
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            
            if self.failure_count >= self.max_failures:
                # Agent needs intervention
                await self.request_help(task, e)
            
            raise
    
    async def request_help(self, task: str, error: Exception):
        """Request help from coordinator or peer agents."""
        help_request = {
            "agent": self.name,
            "task": task,
            "error": str(error),
            "failure_count": self.failure_count
        }
        
        # Emit help request event
        await self.emit_event("agent_needs_help", help_request)
```

### 2. Defensive Agent Communication

Protect against communication failures:

```python
class DefensiveAgent(Agent):
    """Agent with defensive communication patterns."""
    
    @timeout(seconds=10)
    @fallback(default={"status": "no_response"})
    async def communicate_with_peer(self, peer_name: str, message: str):
        """Safely communicate with another agent."""
        try:
            peer = await self.find_peer(peer_name)
            response = await peer.receive_message(message)
            
            # Validate response
            if not self.is_valid_response(response):
                raise ValueError(f"Invalid response from {peer_name}")
            
            return response
        except Exception as e:
            logger.warning(f"Communication failed with {peer_name}: {e}")
            return {"status": "communication_failed", "error": str(e)}
    
    def is_valid_response(self, response: Any) -> bool:
        """Validate peer response."""
        return (
            isinstance(response, dict) and
            "status" in response and
            response.get("status") != "error"
        )
```

## Workflow-Level Error Handling

### 1. Fault-Tolerant Workflows

Workflows that continue despite agent failures:

```python
from agenticraft.core import Workflow
from typing import List, Tuple

class FaultTolerantWorkflow(Workflow):
    """Workflow that handles partial failures gracefully."""
    
    def __init__(self, *args, min_success_rate: float = 0.7, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_success_rate = min_success_rate
    
    async def execute_with_fallbacks(
        self,
        tasks: List[str],
        primary_agents: List[Agent],
        fallback_agents: List[Agent] = None
    ):
        """Execute tasks with fallback agents on failure."""
        results = []
        failed_tasks = []
        
        # Try primary agents first
        for task, agent in zip(tasks, primary_agents):
            try:
                result = await self.execute_task_with_agent(task, agent)
                results.append((task, result, agent.name))
            except Exception as e:
                logger.warning(f"Primary agent {agent.name} failed: {e}")
                failed_tasks.append((task, agent, e))
        
        # Use fallback agents for failed tasks
        if fallback_agents and failed_tasks:
            for (task, failed_agent, error), fallback in zip(
                failed_tasks, 
                fallback_agents * len(failed_tasks)  # Cycle through fallbacks
            ):
                try:
                    result = await self.execute_task_with_agent(task, fallback)
                    results.append((task, result, f"{fallback.name} (fallback)"))
                except Exception as e:
                    logger.error(f"Fallback agent {fallback.name} also failed: {e}")
                    results.append((task, {"error": str(e)}, "failed"))
        
        # Check success rate
        success_count = sum(1 for _, r, _ in results if "error" not in r)
        success_rate = success_count / len(tasks)
        
        if success_rate < self.min_success_rate:
            raise WorkflowError(
                f"Workflow failed: only {success_rate:.1%} tasks succeeded "
                f"(minimum required: {self.min_success_rate:.1%})"
            )
        
        return results
    
    @retry(attempts=2, delay=1.0)
    @timeout(seconds=60)
    async def execute_task_with_agent(self, task: str, agent: Agent):
        """Execute a single task with error handling."""
        return await agent.process(task)
```

### 2. Compensating Transactions

Rollback changes on workflow failure:

```python
class CompensatingWorkflow(Workflow):
    """Workflow with compensating transactions for rollback."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.completed_steps = []
        self.compensation_map = {}
    
    async def execute_with_compensation(self, steps: List[WorkflowStep]):
        """Execute workflow with ability to compensate on failure."""
        try:
            for step in steps:
                # Execute step
                result = await self.execute_step(step)
                self.completed_steps.append((step, result))
                
                # Register compensation if provided
                if step.compensation:
                    self.compensation_map[step.name] = step.compensation
            
            return self.completed_steps
            
        except Exception as e:
            logger.error(f"Workflow failed at step {len(self.completed_steps)}: {e}")
            
            # Execute compensations in reverse order
            await self.compensate()
            raise
    
    async def compensate(self):
        """Execute compensation actions for completed steps."""
        for step, result in reversed(self.completed_steps):
            if step.name in self.compensation_map:
                try:
                    compensation = self.compensation_map[step.name]
                    await compensation(result)
                    logger.info(f"Compensated step: {step.name}")
                except Exception as e:
                    logger.error(f"Compensation failed for {step.name}: {e}")

# Usage example
class WorkflowStep:
    def __init__(self, name: str, action, compensation=None):
        self.name = name
        self.action = action
        self.compensation = compensation

async def create_resource():
    resource_id = await api.create_resource()
    return resource_id

async def delete_resource(resource_id):
    await api.delete_resource(resource_id)

workflow = CompensatingWorkflow()
steps = [
    WorkflowStep(
        "create_resource",
        create_resource,
        compensation=delete_resource
    ),
    WorkflowStep(
        "configure_resource",
        lambda rid: api.configure_resource(rid)
    )
]

try:
    await workflow.execute_with_compensation(steps)
except Exception as e:
    print("Workflow failed and was rolled back")
```

## Coordination Failures

### 1. Coordinator Failover

Handle coordinator failures with backup coordinators:

```python
class ResilientCoordination:
    """Coordination with automatic failover."""
    
    def __init__(self, primary_coordinator: Agent, backup_coordinators: List[Agent]):
        self.primary = primary_coordinator
        self.backups = backup_coordinators
        self.current_coordinator = primary_coordinator
        self.health_check_interval = 30  # seconds
    
    async def coordinate(self, task: str, agents: List[Agent]):
        """Coordinate with automatic failover."""
        max_attempts = 1 + len(self.backups)
        
        for attempt in range(max_attempts):
            try:
                # Check coordinator health
                if not await self.is_coordinator_healthy():
                    await self.failover()
                
                # Attempt coordination
                return await self.current_coordinator.coordinate_task(task, agents)
                
            except Exception as e:
                logger.error(f"Coordination failed with {self.current_coordinator.name}: {e}")
                
                if attempt < max_attempts - 1:
                    await self.failover()
                else:
                    raise WorkflowError("All coordinators failed")
    
    async def is_coordinator_healthy(self) -> bool:
        """Check if current coordinator is healthy."""
        try:
            await asyncio.wait_for(
                self.current_coordinator.health_check(),
                timeout=5.0
            )
            return True
        except:
            return False
    
    async def failover(self):
        """Switch to backup coordinator."""
        if not self.backups:
            raise WorkflowError("No backup coordinators available")
        
        failed_coordinator = self.current_coordinator
        self.current_coordinator = self.backups.pop(0)
        
        logger.warning(
            f"Failing over from {failed_coordinator.name} "
            f"to {self.current_coordinator.name}"
        )
        
        # Optionally add failed coordinator to end of backup list
        # for retry after recovery
        self.backups.append(failed_coordinator)
```

### 2. Consensus Mechanisms

Handle disagreements between agents:

```python
from collections import Counter
from typing import List, Any

class ConsensusWorkflow(Workflow):
    """Workflow requiring consensus among agents."""
    
    async def execute_with_consensus(
        self,
        task: str,
        agents: List[Agent],
        consensus_threshold: float = 0.6
    ):
        """Execute task requiring consensus among agents."""
        results = []
        
        # Gather opinions from all agents
        tasks = []
        for agent in agents:
            tasks.append(self.get_agent_opinion(agent, task))
        
        # Execute in parallel with timeout
        opinions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_opinions = []
        for agent, opinion in zip(agents, opinions):
            if isinstance(opinion, Exception):
                logger.warning(f"Agent {agent.name} failed: {opinion}")
            else:
                valid_opinions.append((agent, opinion))
        
        # Check if we have enough responses
        response_rate = len(valid_opinions) / len(agents)
        if response_rate < consensus_threshold:
            raise WorkflowError(
                f"Insufficient responses: {response_rate:.1%} "
                f"(required: {consensus_threshold:.1%})"
            )
        
        # Find consensus
        consensus = self.find_consensus(valid_opinions)
        
        if not consensus:
            # No clear consensus - use conflict resolution
            consensus = await self.resolve_conflict(valid_opinions, task)
        
        return {
            "consensus": consensus,
            "opinions": valid_opinions,
            "response_rate": response_rate
        }
    
    @timeout(seconds=30)
    @fallback(default={"opinion": "no_response"})
    async def get_agent_opinion(self, agent: Agent, task: str):
        """Get opinion from a single agent."""
        return await agent.analyze(task)
    
    def find_consensus(self, opinions: List[Tuple[Agent, Any]]) -> Any:
        """Find consensus among agent opinions."""
        # Simple majority voting
        opinion_counts = Counter(str(opinion) for _, opinion in opinions)
        
        if opinion_counts:
            most_common = opinion_counts.most_common(1)[0]
            consensus_ratio = most_common[1] / len(opinions)
            
            if consensus_ratio >= 0.5:  # Simple majority
                # Find the original opinion object
                for _, opinion in opinions:
                    if str(opinion) == most_common[0]:
                        return opinion
        
        return None
    
    async def resolve_conflict(self, opinions: List[Tuple[Agent, Any]], task: str):
        """Resolve conflicts when no consensus exists."""
        # Use a specialized arbitrator agent
        arbitrator = self.get_arbitrator_agent()
        
        conflict_data = {
            "task": task,
            "opinions": [
                {"agent": agent.name, "opinion": opinion}
                for agent, opinion in opinions
            ]
        }
        
        return await arbitrator.arbitrate(conflict_data)
```

## Recovery Strategies

### 1. Progressive Retry

Gradually increase resources on retry:

```python
class ProgressiveRetryWorkflow(Workflow):
    """Workflow that progressively adds resources on retry."""
    
    async def execute_with_progressive_retry(self, task: str):
        """Execute with progressively more resources."""
        strategies = [
            {"agents": 1, "timeout": 30, "model": "small"},
            {"agents": 3, "timeout": 60, "model": "medium"},
            {"agents": 5, "timeout": 120, "model": "large"},
        ]
        
        last_error = None
        
        for i, strategy in enumerate(strategies):
            try:
                logger.info(f"Attempt {i+1} with strategy: {strategy}")
                
                # Create agents with current strategy
                agents = await self.create_agents(
                    count=strategy["agents"],
                    model=strategy["model"]
                )
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.execute_with_agents(task, agents),
                    timeout=strategy["timeout"]
                )
                
                logger.info(f"Success with strategy: {strategy}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {i+1} failed: {e}")
                
                # Clean up agents
                await self.cleanup_agents(agents)
        
        raise WorkflowError(f"All strategies failed. Last error: {last_error}")
```

### 2. Checkpoint and Resume

Save progress to resume after failures:

```python
import pickle
from pathlib import Path

class CheckpointedWorkflow(Workflow):
    """Workflow with checkpoint/resume capability."""
    
    def __init__(self, *args, checkpoint_dir: str = "./checkpoints", **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    async def execute_with_checkpoints(self, workflow_id: str, steps: List[Any]):
        """Execute workflow with checkpointing."""
        checkpoint_file = self.checkpoint_dir / f"{workflow_id}.pkl"
        
        # Try to resume from checkpoint
        start_step = 0
        completed_results = []
        
        if checkpoint_file.exists():
            checkpoint = self.load_checkpoint(checkpoint_file)
            start_step = checkpoint["last_completed_step"] + 1
            completed_results = checkpoint["results"]
            logger.info(f"Resuming from step {start_step}")
        
        # Execute remaining steps
        try:
            for i in range(start_step, len(steps)):
                step = steps[i]
                
                # Execute step
                result = await self.execute_step(step)
                completed_results.append(result)
                
                # Save checkpoint
                self.save_checkpoint(checkpoint_file, {
                    "workflow_id": workflow_id,
                    "last_completed_step": i,
                    "results": completed_results,
                    "timestamp": datetime.utcnow()
                })
                
                logger.info(f"Completed step {i+1}/{len(steps)}")
            
            # Clean up checkpoint on success
            checkpoint_file.unlink()
            
            return completed_results
            
        except Exception as e:
            logger.error(f"Workflow failed at step {i+1}: {e}")
            logger.info(f"Progress saved. Resume with workflow_id: {workflow_id}")
            raise
    
    def save_checkpoint(self, file: Path, data: Dict):
        """Save checkpoint data."""
        with open(file, 'wb') as f:
            pickle.dump(data, f)
    
    def load_checkpoint(self, file: Path) -> Dict:
        """Load checkpoint data."""
        with open(file, 'rb') as f:
            return pickle.load(f)
```

## Testing Error Scenarios

### 1. Chaos Testing

Introduce controlled failures:

```python
import random

class ChaosAgent(Agent):
    """Agent that randomly fails for testing."""
    
    def __init__(self, *args, failure_rate: float = 0.1, **kwargs):
        super().__init__(*args, **kwargs)
        self.failure_rate = failure_rate
    
    async def process(self, task: str, context: Dict[str, Any] = None):
        """Process with random failures."""
        if random.random() < self.failure_rate:
            error_types = [
                TimeoutError("Simulated timeout"),
                ConnectionError("Simulated connection error"),
                ValueError("Simulated processing error"),
                MemoryError("Simulated resource exhaustion")
            ]
            raise random.choice(error_types)
        
        return await super().process(task, context)

# Test workflow resilience
async def test_workflow_resilience():
    """Test workflow with chaos agents."""
    workflow = FaultTolerantWorkflow(min_success_rate=0.7)
    
    # Create mix of normal and chaos agents
    agents = [
        ChaosAgent(name=f"chaos_{i}", failure_rate=0.3)
        for i in range(5)
    ]
    
    tasks = [f"task_{i}" for i in range(10)]
    
    try:
        results = await workflow.execute_with_fallbacks(tasks, agents)
        print(f"Workflow succeeded despite failures: {len(results)} tasks completed")
    except WorkflowError as e:
        print(f"Workflow failed: {e}")
```

### 2. Load Testing

Test behavior under load:

```python
class LoadTestWorkflow(Workflow):
    """Workflow for load testing error handling."""
    
    async def stress_test(
        self,
        num_tasks: int = 1000,
        concurrent_limit: int = 50,
        failure_injection_rate: float = 0.05
    ):
        """Stress test the workflow."""
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def limited_task(task_id: int):
            async with semaphore:
                # Inject random failures
                if random.random() < failure_injection_rate:
                    raise Exception(f"Injected failure for task {task_id}")
                
                # Simulate work
                await asyncio.sleep(random.uniform(0.1, 0.5))
                return f"completed_{task_id}"
        
        # Track metrics
        start_time = time.time()
        results = await asyncio.gather(
            *[limited_task(i) for i in range(num_tasks)],
            return_exceptions=True
        )
        
        duration = time.time() - start_time
        
        # Analyze results
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))
        
        return {
            "total_tasks": num_tasks,
            "successes": successes,
            "failures": failures,
            "success_rate": successes / num_tasks,
            "duration": duration,
            "tasks_per_second": num_tasks / duration
        }
```

## Summary

Effective error handling in multi-agent systems requires:

1. **Agent-level resilience**: Self-healing and defensive communication
2. **Workflow-level strategies**: Fault tolerance and compensation
3. **Coordination robustness**: Failover and consensus mechanisms
4. **Recovery capabilities**: Progressive retry and checkpointing
5. **Comprehensive testing**: Chaos testing and load testing

Remember: In multi-agent systems, partial success is often better than complete failure. Design your error handling to maximize the value delivered even when some components fail.
