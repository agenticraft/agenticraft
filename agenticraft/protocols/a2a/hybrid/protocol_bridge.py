"""Protocol bridge for connecting different coordination protocols."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Protocol as ProtocolType
from abc import abstractmethod

from ..base import Protocol, ProtocolMessage, MessageType

logger = logging.getLogger(__name__)


class ProtocolAdapter(ProtocolType):
    """Protocol adapter interface."""
    
    @abstractmethod
    async def send(self, message: ProtocolMessage) -> Any:
        """Send message through the protocol."""
        ...
    
    @abstractmethod
    async def receive(self) -> Optional[ProtocolMessage]:
        """Receive message from the protocol."""
        ...
    
    @abstractmethod
    def get_protocol_name(self) -> str:
        """Get the protocol name."""
        ...


class ProtocolBridge:
    """Bridges different coordination protocols.
    
    Allows seamless communication between agents using different
    coordination protocols (centralized, decentralized, hybrid).
    """
    
    def __init__(self):
        """Initialize protocol bridge."""
        self.protocols: Dict[str, ProtocolAdapter] = {}
        self.routing_rules: Dict[MessageType, List[str]] = {}
        self.transform_rules: Dict[tuple, callable] = {}
        self._running = False
        self._routing_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            "messages_routed": 0,
            "messages_transformed": 0,
            "routing_errors": 0
        }
    
    def register_protocol(self, name: str, adapter: ProtocolAdapter):
        """Register a protocol adapter.
        
        Args:
            name: Protocol name
            adapter: Protocol adapter instance
        """
        if name in self.protocols:
            raise ValueError(f"Protocol '{name}' already registered")
        
        self.protocols[name] = adapter
        logger.info(f"Registered protocol: {name}")
    
    def unregister_protocol(self, name: str):
        """Unregister a protocol."""
        if name in self.protocols:
            del self.protocols[name]
            # Remove associated routing rules
            for msg_type in list(self.routing_rules.keys()):
                self.routing_rules[msg_type] = [
                    p for p in self.routing_rules.get(msg_type, [])
                    if p != name
                ]
    
    def add_routing_rule(
        self,
        message_type: MessageType,
        target_protocols: List[str]
    ):
        """Add routing rule for message type.
        
        Args:
            message_type: Type of message to route
            target_protocols: List of protocols to route to
        """
        # Validate protocols exist
        for protocol in target_protocols:
            if protocol not in self.protocols:
                raise ValueError(f"Unknown protocol: {protocol}")
        
        self.routing_rules[message_type] = target_protocols
    
    def add_transform_rule(
        self,
        from_protocol: str,
        to_protocol: str,
        transformer: callable
    ):
        """Add message transformation rule.
        
        Args:
            from_protocol: Source protocol
            to_protocol: Target protocol
            transformer: Function to transform messages
        """
        self.transform_rules[(from_protocol, to_protocol)] = transformer
    
    async def start(self):
        """Start the protocol bridge."""
        if self._running:
            return
        
        self._running = True
        self._routing_task = asyncio.create_task(self._routing_loop())
        
        logger.info("Protocol bridge started")
    
    async def stop(self):
        """Stop the protocol bridge."""
        self._running = False
        
        if self._routing_task:
            self._routing_task.cancel()
            try:
                await self._routing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Protocol bridge stopped")
    
    async def route_message(
        self,
        message: ProtocolMessage,
        source_protocol: str
    ) -> List[Any]:
        """Route message to appropriate protocols.
        
        Args:
            message: Message to route
            source_protocol: Protocol that sent the message
            
        Returns:
            List of results from target protocols
        """
        self.metrics["messages_routed"] += 1
        
        # Determine target protocols
        target_protocols = self._determine_targets(message, source_protocol)
        
        # Route to each target
        results = []
        for target_protocol in target_protocols:
            if target_protocol == source_protocol:
                continue  # Don't route back to source
            
            try:
                # Transform message if needed
                transformed_message = await self._transform_message(
                    message, source_protocol, target_protocol
                )
                
                # Send through target protocol
                adapter = self.protocols[target_protocol]
                result = await adapter.send(transformed_message)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error routing to {target_protocol}: {e}")
                self.metrics["routing_errors"] += 1
        
        return results
    
    def _determine_targets(
        self,
        message: ProtocolMessage,
        source_protocol: str
    ) -> List[str]:
        """Determine target protocols for a message."""
        # Check explicit routing rules
        if message.type in self.routing_rules:
            return self.routing_rules[message.type]
        
        # Check message metadata for hints
        if "target_protocols" in message.metadata:
            targets = message.metadata["target_protocols"]
            # Validate they exist
            return [t for t in targets if t in self.protocols]
        
        # Default behavior based on message type
        if message.type == MessageType.BROADCAST:
            # Broadcast to all protocols
            return list(self.protocols.keys())
        elif message.target:
            # Try to find protocol that has the target node
            for name, adapter in self.protocols.items():
                if hasattr(adapter, "has_node") and adapter.has_node(message.target):
                    return [name]
        
        # Default: route to all other protocols
        return [p for p in self.protocols.keys() if p != source_protocol]
    
    async def _transform_message(
        self,
        message: ProtocolMessage,
        from_protocol: str,
        to_protocol: str
    ) -> ProtocolMessage:
        """Transform message between protocols."""
        transformer = self.transform_rules.get((from_protocol, to_protocol))
        
        if transformer:
            self.metrics["messages_transformed"] += 1
            return await transformer(message)
        
        # No transformation needed
        return message
    
    async def _routing_loop(self):
        """Main routing loop."""
        while self._running:
            try:
                # Check each protocol for messages
                for name, adapter in self.protocols.items():
                    try:
                        # Non-blocking receive
                        message = await asyncio.wait_for(
                            adapter.receive(),
                            timeout=0.1
                        )
                        
                        if message:
                            # Route the message
                            await self.route_message(message, name)
                            
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"Error receiving from {name}: {e}")
                
                await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Routing loop error: {e}")
                await asyncio.sleep(1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status."""
        return {
            "protocols": list(self.protocols.keys()),
            "routing_rules": {
                msg_type.value: protocols
                for msg_type, protocols in self.routing_rules.items()
            },
            "transform_rules": [
                f"{from_p} -> {to_p}"
                for (from_p, to_p) in self.transform_rules.keys()
            ],
            "metrics": self.metrics
        }


class MeshProtocolAdapter(ProtocolAdapter):
    """Adapter for mesh network protocol."""
    
    def __init__(self, mesh_network):
        """Initialize mesh adapter.
        
        Args:
            mesh_network: MeshNetwork instance
        """
        self.mesh = mesh_network
        self._receive_queue = asyncio.Queue()
        
        # Register handler to capture messages
        async def capture_handler(message: ProtocolMessage):
            await self._receive_queue.put(message)
        
        # Register for all message types we want to bridge
        for msg_type in [MessageType.TASK, MessageType.RESULT, MessageType.COORDINATION]:
            self.mesh.register_handler(msg_type, capture_handler)
    
    async def send(self, message: ProtocolMessage) -> Any:
        """Send message through mesh network."""
        if message.target:
            return await self.mesh.send_message(message)
        else:
            await self.mesh.broadcast(message)
    
    async def receive(self) -> Optional[ProtocolMessage]:
        """Receive message from mesh network."""
        try:
            return await asyncio.wait_for(
                self._receive_queue.get(),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            return None
    
    def get_protocol_name(self) -> str:
        """Get protocol name."""
        return "mesh"
    
    def has_node(self, node_id: str) -> bool:
        """Check if protocol has a specific node."""
        return node_id in self.mesh.nodes


class AdaptiveModeSelector:
    """Selects optimal coordination mode based on context."""
    
    def __init__(self):
        """Initialize mode selector."""
        self.mode_history = []
        self.performance_metrics = {}
    
    async def select_mode(
        self,
        task_complexity: float,
        agent_count: int,
        latency_requirement: float,
        reliability_requirement: float = 0.9
    ) -> str:
        """Select coordination mode.
        
        Args:
            task_complexity: Complexity score (0-1)
            agent_count: Number of agents involved
            latency_requirement: Maximum acceptable latency (ms)
            reliability_requirement: Required success rate (0-1)
            
        Returns:
            Selected mode: "centralized", "decentralized", or "hybrid"
        """
        # Simple heuristics for mode selection
        
        if agent_count < 5 and task_complexity < 0.5:
            # Small scale, simple tasks - centralized is efficient
            mode = "centralized"
        elif agent_count > 20 or reliability_requirement > 0.95:
            # Large scale or high reliability - mesh/decentralized
            mode = "decentralized"
        elif latency_requirement < 100 and task_complexity > 0.7:
            # Low latency + complex tasks - hybrid approach
            mode = "hybrid"
        else:
            # Default to hybrid for flexibility
            mode = "hybrid"
        
        # Record decision
        self.mode_history.append({
            "mode": mode,
            "context": {
                "task_complexity": task_complexity,
                "agent_count": agent_count,
                "latency_requirement": latency_requirement,
                "reliability_requirement": reliability_requirement
            }
        })
        
        return mode
    
    def update_performance(
        self,
        mode: str,
        success: bool,
        latency: float,
        resource_usage: Dict[str, float]
    ):
        """Update performance metrics for a mode.
        
        Args:
            mode: Coordination mode used
            success: Whether task succeeded
            latency: Actual latency (ms)
            resource_usage: Resource usage metrics
        """
        if mode not in self.performance_metrics:
            self.performance_metrics[mode] = {
                "success_count": 0,
                "failure_count": 0,
                "total_latency": 0,
                "count": 0
            }
        
        metrics = self.performance_metrics[mode]
        if success:
            metrics["success_count"] += 1
        else:
            metrics["failure_count"] += 1
        
        metrics["total_latency"] += latency
        metrics["count"] += 1
    
    def get_mode_stats(self) -> Dict[str, Any]:
        """Get statistics for each mode."""
        stats = {}
        
        for mode, metrics in self.performance_metrics.items():
            count = metrics["count"]
            if count > 0:
                stats[mode] = {
                    "success_rate": metrics["success_count"] / count,
                    "avg_latency": metrics["total_latency"] / count,
                    "total_tasks": count
                }
        
        return stats
