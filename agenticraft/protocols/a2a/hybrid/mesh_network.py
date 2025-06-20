"""Mesh network implementation for agent coordination."""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from ..base import Protocol, ProtocolMessage, ProtocolNode, MessageType, NodeStatus

logger = logging.getLogger(__name__)


@dataclass
class MeshRoute:
    """Route information in mesh network."""
    target: str
    next_hop: str
    distance: int
    last_updated: float = field(default_factory=time.time)


class MeshNetwork(Protocol):
    """Decentralized mesh network for agent coordination.
    
    Features:
    - Self-organizing network topology
    - Automatic route discovery
    - Fault tolerance with route redundancy
    - Load balancing across nodes
    - Distributed task execution
    """
    
    def __init__(self, node_id: str, max_connections: int = 5, discovery_interval: float = 30.0):
        """Initialize mesh network node.
        
        Args:
            node_id: Unique identifier for this node
            max_connections: Maximum direct connections to maintain
            discovery_interval: Interval for network discovery (seconds)
        """
        super().__init__(node_id)
        self.max_connections = max_connections
        self.discovery_interval = discovery_interval
        
        # Mesh-specific data structures
        self.connections: Set[str] = set()  # Direct connections
        self.routing_table: Dict[str, MeshRoute] = {}  # Routing information
        self.pending_messages: Dict[str, ProtocolMessage] = {}  # Messages awaiting response
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._discovery_task: Optional[asyncio.Task] = None
        self._routing_task: Optional[asyncio.Task] = None
        
        # Message handlers
        self.register_handler(MessageType.TASK, self._handle_task)
        self.register_handler(MessageType.RESULT, self._handle_result)
        
        # Metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "tasks_executed": 0,
            "routing_updates": 0
        }
    
    async def start(self):
        """Start the mesh network node."""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        self._routing_task = asyncio.create_task(self._routing_loop())
        
        logger.info(f"Mesh node {self.node_id} started")
    
    async def stop(self):
        """Stop the mesh network node."""
        self._running = False
        
        # Cancel background tasks
        for task in [self._heartbeat_task, self._discovery_task, self._routing_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Notify peers we're going offline
        offline_msg = ProtocolMessage(
            type=MessageType.STATUS,
            sender=self.node_id,
            content={"status": NodeStatus.OFFLINE.value}
        )
        await self.broadcast(offline_msg)
        
        logger.info(f"Mesh node {self.node_id} stopped")
    
    async def send_message(self, message: ProtocolMessage) -> Any:
        """Send a message through the mesh network."""
        message.sender = self.node_id
        self.metrics["messages_sent"] += 1
        
        if message.target:
            # Targeted message - use routing
            return await self._route_message(message)
        else:
            # No target - broadcast
            await self.broadcast(message)
    
    async def broadcast(self, message: ProtocolMessage):
        """Broadcast a message to all connected nodes."""
        message.sender = self.node_id
        message.metadata["ttl"] = message.metadata.get("ttl", 3)  # Time to live
        message.metadata["seen"] = message.metadata.get("seen", [])
        message.metadata["seen"].append(self.node_id)
        
        # Send to all direct connections
        tasks = []
        for node_id in self.connections:
            if node_id not in message.metadata["seen"]:
                tasks.append(self._send_to_node(node_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def register_agent(self, agent):
        """Register an agent with the mesh network."""
        # Extract agent capabilities
        capabilities = []
        if hasattr(agent, 'capabilities'):
            capabilities = agent.capabilities
        elif hasattr(agent, 'tools'):
            capabilities = list(agent.tools.keys())
        
        # Update node capabilities
        for cap in capabilities:
            self.register_capability(cap)
        
        # Register message handler for agent
        async def agent_handler(message: ProtocolMessage):
            if message.content.get("task"):
                result = await agent.execute(message.content["task"])
                return result
        
        self.register_handler(MessageType.TASK, agent_handler)
        
        logger.info(f"Registered agent {agent.name} with capabilities: {capabilities}")
    
    async def execute_distributed(
        self,
        task: str,
        capability_required: str,
        strategy: str = "round_robin",
        timeout: float = 30.0
    ) -> Any:
        """Execute task on a node with required capability."""
        # Find capable nodes
        capable_nodes = self.get_nodes_with_capability(capability_required)
        
        if not capable_nodes:
            raise RuntimeError(f"No nodes found with capability: {capability_required}")
        
        # Select node based on strategy
        target_node = self._select_node(capable_nodes, strategy)
        
        # Create task message
        task_id = str(uuid4())
        message = ProtocolMessage(
            type=MessageType.TASK,
            sender=self.node_id,
            target=target_node,
            content={
                "task": task,
                "capability": capability_required,
                "task_id": task_id
            }
        )
        
        # Store pending message
        self.pending_messages[task_id] = message
        
        # Send and wait for response
        await self.send_message(message)
        
        # Wait for result with timeout
        try:
            result = await asyncio.wait_for(
                self._wait_for_result(task_id),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            del self.pending_messages[task_id]
            raise TimeoutError(f"Task execution timed out after {timeout}s")
    
    def _select_node(self, nodes: List[str], strategy: str) -> str:
        """Select a node based on strategy."""
        if strategy == "round_robin":
            # Simple round-robin selection
            return nodes[hash(time.time()) % len(nodes)]
        elif strategy == "random":
            return random.choice(nodes)
        elif strategy == "least_busy":
            # Select least busy node based on status
            busy_counts = {}
            for node_id in nodes:
                if node_id in self.nodes:
                    status = self.nodes[node_id].status
                    busy_counts[node_id] = 0 if status == NodeStatus.IDLE else 1
            
            return min(busy_counts, key=busy_counts.get)
        else:
            # Default to first available
            return nodes[0]
    
    async def _route_message(self, message: ProtocolMessage) -> Any:
        """Route a message to its target."""
        target = message.target
        
        # Check if target is directly connected
        if target in self.connections:
            return await self._send_to_node(target, message)
        
        # Check routing table
        if target in self.routing_table:
            route = self.routing_table[target]
            message.metadata["route"] = message.metadata.get("route", [])
            message.metadata["route"].append(self.node_id)
            return await self._send_to_node(route.next_hop, message)
        
        # No route found - try discovery
        logger.warning(f"No route to {target}, attempting discovery")
        await self._discover_route(target)
        
        # Retry after discovery
        if target in self.routing_table:
            return await self._route_message(message)
        else:
            raise RuntimeError(f"No route found to node: {target}")
    
    async def _send_to_node(self, node_id: str, message: ProtocolMessage):
        """Send message to a specific node."""
        # In a real implementation, this would use actual network communication
        # For now, we'll simulate with direct method calls or events
        
        logger.debug(f"Sending {message.type.value} from {self.node_id} to {node_id}")
        
        # Simulate network delay
        await asyncio.sleep(0.01)
        
        # In real implementation, this would be network call
        # For now, we'll use the message queue
        await self._message_queue.put((node_id, message))
    
    async def _handle_task(self, message: ProtocolMessage):
        """Handle task execution request."""
        task = message.content.get("task")
        capability = message.content.get("capability")
        task_id = message.content.get("task_id")
        
        if not task or not capability:
            logger.error("Invalid task message: missing task or capability")
            return
        
        # Check if we have the capability
        if capability not in self.nodes[self.node_id].capabilities:
            logger.warning(f"Capability {capability} not available on this node")
            # Forward to another node if possible
            capable_nodes = self.get_nodes_with_capability(capability)
            if capable_nodes:
                message.sender = self.node_id
                message.target = capable_nodes[0]
                await self._route_message(message)
            return
        
        # Execute task
        try:
            self.update_status(NodeStatus.BUSY)
            self.metrics["tasks_executed"] += 1
            
            # Execute through registered handler
            # In real implementation, this would call the agent
            result = f"Task '{task}' executed by {self.node_id}"
            
            # Send result back
            result_msg = ProtocolMessage(
                type=MessageType.RESULT,
                sender=self.node_id,
                target=message.sender,
                content={
                    "task_id": task_id,
                    "result": result,
                    "success": True
                }
            )
            await self.send_message(result_msg)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            # Send error result
            error_msg = ProtocolMessage(
                type=MessageType.ERROR,
                sender=self.node_id,
                target=message.sender,
                content={
                    "task_id": task_id,
                    "error": str(e),
                    "success": False
                }
            )
            await self.send_message(error_msg)
        finally:
            self.update_status(NodeStatus.IDLE)
    
    async def _handle_result(self, message: ProtocolMessage):
        """Handle task result."""
        task_id = message.content.get("task_id")
        
        if task_id and task_id in self.pending_messages:
            # Store result for waiting task
            self.pending_messages[task_id] = message
    
    async def _wait_for_result(self, task_id: str) -> Any:
        """Wait for a task result."""
        while task_id in self.pending_messages:
            msg = self.pending_messages[task_id]
            if isinstance(msg, ProtocolMessage) and msg.type == MessageType.RESULT:
                del self.pending_messages[task_id]
                if msg.content.get("success"):
                    return msg.content.get("result")
                else:
                    raise RuntimeError(msg.content.get("error", "Task failed"))
            await asyncio.sleep(0.1)
        
        raise RuntimeError("Task result not found")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self._running:
            try:
                # Send heartbeat
                heartbeat = ProtocolMessage(
                    type=MessageType.HEARTBEAT,
                    sender=self.node_id,
                    content={
                        "status": self.nodes[self.node_id].status.value,
                        "capabilities": self.nodes[self.node_id].capabilities,
                        "connections": len(self.connections),
                        "metrics": self.metrics
                    }
                )
                await self.broadcast(heartbeat)
                
                # Check for stale nodes
                current_time = time.time()
                stale_threshold = 60.0  # 60 seconds
                
                for node_id, node in list(self.nodes.items()):
                    if node_id != self.node_id:
                        time_since_heartbeat = current_time - node.last_heartbeat.timestamp()
                        if time_since_heartbeat > stale_threshold:
                            logger.warning(f"Node {node_id} is stale, marking as offline")
                            node.status = NodeStatus.OFFLINE
                            # Remove from connections
                            self.connections.discard(node_id)
                
                await asyncio.sleep(10)  # Heartbeat every 10 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(10)
    
    async def _discovery_loop(self):
        """Discover new nodes periodically."""
        while self._running:
            try:
                # Send discovery request
                discovery = ProtocolMessage(
                    type=MessageType.DISCOVERY,
                    sender=self.node_id,
                    content={
                        "capabilities": self.nodes[self.node_id].capabilities,
                        "looking_for": "peers"
                    }
                )
                await self.broadcast(discovery)
                
                # Try to establish new connections if below max
                if len(self.connections) < self.max_connections:
                    active_nodes = self.get_active_nodes()
                    for node_id in active_nodes:
                        if node_id not in self.connections:
                            # Try to connect
                            self.connections.add(node_id)
                            logger.info(f"Connected to node: {node_id}")
                            
                            if len(self.connections) >= self.max_connections:
                                break
                
                await asyncio.sleep(self.discovery_interval)
                
            except Exception as e:
                logger.error(f"Discovery error: {e}")
                await asyncio.sleep(self.discovery_interval)
    
    async def _routing_loop(self):
        """Update routing table periodically."""
        while self._running:
            try:
                # Update routing table based on network topology
                self._update_routing_table()
                self.metrics["routing_updates"] += 1
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Routing error: {e}")
                await asyncio.sleep(30)
    
    def _update_routing_table(self):
        """Update routing table based on current network state."""
        # Simple distance vector routing
        
        # Direct connections have distance 1
        for node_id in self.connections:
            if node_id not in self.routing_table or self.routing_table[node_id].distance > 1:
                self.routing_table[node_id] = MeshRoute(
                    target=node_id,
                    next_hop=node_id,
                    distance=1
                )
        
        # Remove routes to offline nodes
        for node_id in list(self.routing_table.keys()):
            if node_id in self.nodes and self.nodes[node_id].status == NodeStatus.OFFLINE:
                del self.routing_table[node_id]
    
    async def _discover_route(self, target: str):
        """Discover route to a target node."""
        # Send route discovery message
        discovery = ProtocolMessage(
            type=MessageType.DISCOVERY,
            sender=self.node_id,
            content={
                "looking_for": target,
                "route_discovery": True
            }
        )
        await self.broadcast(discovery)
        
        # Wait a bit for responses
        await asyncio.sleep(1.0)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get network metrics."""
        return {
            "node_id": self.node_id,
            "connections": len(self.connections),
            "total_nodes": len(self.nodes),
            "routing_entries": len(self.routing_table),
            **self.metrics,
            "status": self.get_network_status()
        }
