"""Centralized task router for hierarchical coordination."""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from ..base import Protocol, ProtocolMessage, ProtocolNode, MessageType, NodeStatus

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task in the system."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    capability_required: str = ""
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    status: str = "pending"  # pending, assigned, executing, completed, failed
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerStats:
    """Statistics for a worker node."""
    node_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    current_load: int = 0
    max_concurrent_tasks: int = 3
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total > 0 else 1.0
    
    @property
    def avg_execution_time(self) -> float:
        """Calculate average execution time."""
        return self.total_execution_time / self.tasks_completed if self.tasks_completed > 0 else 0.0
    
    def can_accept_task(self) -> bool:
        """Check if worker can accept more tasks."""
        return self.current_load < self.max_concurrent_tasks


class TaskRouter(Protocol):
    """Centralized task routing with intelligent distribution.
    
    Features:
    - Priority-based task queuing
    - Load balancing across workers
    - Capability-based routing
    - Performance tracking
    - Automatic failover
    """
    
    def __init__(self, node_id: str = "task-router"):
        """Initialize task router."""
        super().__init__(node_id)
        
        # Task management
        self.tasks: Dict[UUID, Task] = {}
        self.task_queues: Dict[str, deque] = defaultdict(deque)  # Per capability
        self.pending_results: Dict[UUID, asyncio.Future] = {}
        
        # Worker management
        self.worker_stats: Dict[str, WorkerStats] = {}
        self.capability_map: Dict[str, Set[str]] = defaultdict(set)  # capability -> workers
        
        # Background tasks
        self._scheduler_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.config = {
            "max_retries": 3,
            "task_timeout": 300.0,  # 5 minutes
            "scheduler_interval": 0.5,
            "monitor_interval": 10.0
        }
        
        # Register handlers
        self.register_handler(MessageType.TASK, self._handle_task_request)
        self.register_handler(MessageType.RESULT, self._handle_task_result)
        self.register_handler(MessageType.STATUS, self._handle_worker_status)
    
    async def start(self):
        """Start the task router."""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"Task router {self.node_id} started")
    
    async def stop(self):
        """Stop the task router."""
        self._running = False
        
        # Cancel background tasks
        for task_handle in [self._scheduler_task, self._monitor_task]:
            if task_handle:
                task_handle.cancel()
                try:
                    await task_handle
                except asyncio.CancelledError:
                    pass
        
        # Cancel pending results
        for future in self.pending_results.values():
            if not future.done():
                future.cancel()
        
        logger.info(f"Task router {self.node_id} stopped")
    
    async def route_task(
        self,
        task_name: str,
        capability: str,
        priority: int = 0,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """Route a task to appropriate worker.
        
        Args:
            task_name: Name/description of the task
            capability: Required capability
            priority: Task priority (higher = more important)
            timeout: Task timeout in seconds
            **kwargs: Additional task parameters
            
        Returns:
            Task result
            
        Raises:
            RuntimeError: If task fails or times out
        """
        # Create task
        task = Task(
            name=task_name,
            capability_required=capability,
            priority=priority,
            metadata=kwargs
        )
        
        # Store task
        self.tasks[task.id] = task
        
        # Create future for result
        future = asyncio.Future()
        self.pending_results[task.id] = future
        
        # Queue task
        self.task_queues[capability].append(task.id)
        
        logger.info(f"Queued task {task.id} requiring {capability}")
        
        # Wait for result
        try:
            result = await asyncio.wait_for(
                future,
                timeout=timeout or self.config["task_timeout"]
            )
            return result
        except asyncio.TimeoutError:
            task.status = "failed"
            task.error = "Task timed out"
            raise TimeoutError(f"Task {task.id} timed out")
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            raise
    
    def register_worker(self, node_id: str, capabilities: List[str]):
        """Register a worker node.
        
        Args:
            node_id: Worker node ID
            capabilities: List of capabilities
        """
        # Create worker stats
        if node_id not in self.worker_stats:
            self.worker_stats[node_id] = WorkerStats(node_id=node_id)
        
        # Update capability map
        for capability in capabilities:
            self.capability_map[capability].add(node_id)
        
        # Update node info
        if node_id not in self.nodes:
            self.nodes[node_id] = ProtocolNode(
                node_id=node_id,
                capabilities=capabilities,
                status=NodeStatus.IDLE
            )
        else:
            self.nodes[node_id].capabilities = capabilities
        
        logger.info(f"Registered worker {node_id} with capabilities: {capabilities}")
    
    def unregister_worker(self, node_id: str):
        """Unregister a worker node."""
        # Remove from capability map
        for capability, workers in self.capability_map.items():
            workers.discard(node_id)
        
        # Mark node as offline
        if node_id in self.nodes:
            self.nodes[node_id].status = NodeStatus.OFFLINE
        
        # Reassign tasks
        for task in self.tasks.values():
            if task.assigned_to == node_id and task.status == "executing":
                task.status = "pending"
                task.assigned_to = None
                self.task_queues[task.capability_required].append(task.id)
    
    async def _scheduler_loop(self):
        """Main scheduling loop."""
        while self._running:
            try:
                # Process each capability queue
                for capability, queue in self.task_queues.items():
                    if not queue:
                        continue
                    
                    # Find available workers
                    available_workers = self._get_available_workers(capability)
                    
                    if not available_workers:
                        continue
                    
                    # Assign tasks to workers
                    while queue and available_workers:
                        task_id = queue.popleft()
                        task = self.tasks.get(task_id)
                        
                        if not task or task.status != "pending":
                            continue
                        
                        # Select best worker
                        worker_id = self._select_worker(available_workers, task)
                        
                        # Assign task
                        await self._assign_task(task, worker_id)
                        
                        # Update available workers
                        available_workers = self._get_available_workers(capability)
                
                await asyncio.sleep(self.config["scheduler_interval"])
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_loop(self):
        """Monitor task execution and handle timeouts."""
        while self._running:
            try:
                current_time = datetime.now()
                
                # Check for timed out tasks
                for task in list(self.tasks.values()):
                    if task.status == "executing":
                        elapsed = (current_time - task.created_at).total_seconds()
                        
                        if elapsed > self.config["task_timeout"]:
                            logger.warning(f"Task {task.id} timed out")
                            
                            # Mark as failed
                            task.status = "failed"
                            task.error = "Execution timeout"
                            
                            # Notify waiting future
                            if task.id in self.pending_results:
                                future = self.pending_results[task.id]
                                if not future.done():
                                    future.set_exception(TimeoutError("Task execution timeout"))
                            
                            # Update worker stats
                            if task.assigned_to and task.assigned_to in self.worker_stats:
                                stats = self.worker_stats[task.assigned_to]
                                stats.tasks_failed += 1
                                stats.current_load -= 1
                
                # Clean up old completed tasks
                cutoff_time = current_time.timestamp() - 3600  # 1 hour
                old_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if task.status in ["completed", "failed"] and
                    task.created_at.timestamp() < cutoff_time
                ]
                
                for task_id in old_tasks:
                    del self.tasks[task_id]
                    self.pending_results.pop(task_id, None)
                
                await asyncio.sleep(self.config["monitor_interval"])
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(self.config["monitor_interval"])
    
    def _get_available_workers(self, capability: str) -> List[str]:
        """Get available workers for a capability."""
        available = []
        
        for worker_id in self.capability_map.get(capability, []):
            # Check if worker is online
            if worker_id not in self.nodes:
                continue
            
            node = self.nodes[worker_id]
            if node.status == NodeStatus.OFFLINE:
                continue
            
            # Check if worker can accept tasks
            stats = self.worker_stats.get(worker_id)
            if stats and stats.can_accept_task():
                available.append(worker_id)
        
        return available
    
    def _select_worker(self, workers: List[str], task: Task) -> str:
        """Select best worker for a task."""
        # Score each worker
        scores = {}
        
        for worker_id in workers:
            stats = self.worker_stats.get(worker_id)
            if not stats:
                scores[worker_id] = 0
                continue
            
            # Calculate score based on:
            # - Success rate (40%)
            # - Current load (30%)  
            # - Average execution time (30%)
            
            success_score = stats.success_rate * 40
            load_score = (1 - stats.current_load / stats.max_concurrent_tasks) * 30
            
            # Normalize execution time (lower is better)
            if stats.avg_execution_time > 0:
                time_score = min(30, 30 / (stats.avg_execution_time / 60))  # Normalize to minutes
            else:
                time_score = 30
            
            scores[worker_id] = success_score + load_score + time_score
        
        # Select worker with highest score
        return max(scores, key=scores.get)
    
    async def _assign_task(self, task: Task, worker_id: str):
        """Assign task to a worker."""
        task.assigned_to = worker_id
        task.status = "assigned"
        
        # Update worker stats
        stats = self.worker_stats[worker_id]
        stats.current_load += 1
        
        # Send task to worker
        message = ProtocolMessage(
            type=MessageType.TASK,
            sender=self.node_id,
            target=worker_id,
            content={
                "task_id": str(task.id),
                "task_name": task.name,
                "capability": task.capability_required,
                **task.metadata
            }
        )
        
        await self.send_message(message)
        
        # Update task status
        task.status = "executing"
        
        logger.info(f"Assigned task {task.id} to worker {worker_id}")
    
    async def _handle_task_request(self, message: ProtocolMessage):
        """Handle incoming task request."""
        # This would be used if router receives tasks via protocol
        content = message.content
        
        result = await self.route_task(
            task_name=content.get("task_name", ""),
            capability=content.get("capability", ""),
            priority=content.get("priority", 0),
            **content.get("metadata", {})
        )
        
        # Send result back
        response = ProtocolMessage(
            type=MessageType.RESULT,
            sender=self.node_id,
            target=message.sender,
            content={
                "task_id": content.get("task_id"),
                "result": result
            }
        )
        
        await self.send_message(response)
    
    async def _handle_task_result(self, message: ProtocolMessage):
        """Handle task result from worker."""
        content = message.content
        task_id = UUID(content.get("task_id"))
        
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Received result for unknown task: {task_id}")
            return
        
        # Update task
        task.status = "completed" if content.get("success", True) else "failed"
        task.result = content.get("result")
        task.error = content.get("error")
        
        # Update worker stats
        if task.assigned_to in self.worker_stats:
            stats = self.worker_stats[task.assigned_to]
            stats.current_load -= 1
            
            if task.status == "completed":
                stats.tasks_completed += 1
            else:
                stats.tasks_failed += 1
            
            # Update execution time
            exec_time = (datetime.now() - task.created_at).total_seconds()
            stats.total_execution_time += exec_time
        
        # Notify waiting future
        if task_id in self.pending_results:
            future = self.pending_results[task_id]
            if not future.done():
                if task.status == "completed":
                    future.set_result(task.result)
                else:
                    future.set_exception(RuntimeError(task.error or "Task failed"))
    
    async def _handle_worker_status(self, message: ProtocolMessage):
        """Handle worker status update."""
        worker_id = message.sender
        status = NodeStatus(message.content.get("status", "idle"))
        
        # Update node status
        if worker_id in self.nodes:
            self.nodes[worker_id].status = status
        
        # Handle offline workers
        if status == NodeStatus.OFFLINE:
            self.unregister_worker(worker_id)
    
    async def send_message(self, message: ProtocolMessage) -> Any:
        """Send a message (simplified for now)."""
        # In real implementation, this would use network communication
        logger.debug(f"Sending {message.type.value} to {message.target}")
        return message
    
    async def broadcast(self, message: ProtocolMessage):
        """Broadcast not used in centralized router."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        total_tasks = len(self.tasks)
        pending_tasks = sum(1 for t in self.tasks.values() if t.status == "pending")
        executing_tasks = sum(1 for t in self.tasks.values() if t.status == "executing")
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed_tasks = sum(1 for t in self.tasks.values() if t.status == "failed")
        
        return {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "executing_tasks": executing_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "queues": {
                cap: len(queue) for cap, queue in self.task_queues.items()
            },
            "workers": {
                worker_id: {
                    "tasks_completed": stats.tasks_completed,
                    "tasks_failed": stats.tasks_failed,
                    "success_rate": stats.success_rate,
                    "current_load": stats.current_load,
                    "avg_execution_time": stats.avg_execution_time
                }
                for worker_id, stats in self.worker_stats.items()
            }
        }
