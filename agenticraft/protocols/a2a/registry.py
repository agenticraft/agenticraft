"""Protocol registry for managing A2A protocols."""

import logging
from typing import Dict, List, Optional, Type, Any

from .base import Protocol, MessageType
from .centralized.task_router import TaskRouter
from .decentralized.consensus import ConsensusProtocol, ConsensusType
from .hybrid.mesh_network import MeshNetwork

logger = logging.getLogger(__name__)


class ProtocolRegistry:
    """Central registry for all A2A protocols.
    
    Manages protocol registration, discovery, and lifecycle.
    """
    
    _instance: Optional["ProtocolRegistry"] = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize protocol registry."""
        if self._initialized:
            return
        
        self._protocols: Dict[str, Type[Protocol]] = {}
        self._instances: Dict[str, Protocol] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
        # Register built-in protocols
        self._register_builtin_protocols()
        
        self._initialized = True
    
    def _register_builtin_protocols(self):
        """Register built-in protocol types."""
        # Centralized protocols
        self.register_protocol(
            "task_router",
            TaskRouter,
            {
                "description": "Centralized task routing with load balancing",
                "coordination_type": "centralized",
                "features": ["load_balancing", "priority_queue", "failover"]
            }
        )
        
        # Decentralized protocols
        self.register_protocol(
            "consensus",
            ConsensusProtocol,
            {
                "description": "Decentralized consensus protocol",
                "coordination_type": "decentralized",
                "features": ["byzantine_tolerance", "leader_election", "voting"]
            }
        )
        
        # Hybrid protocols
        self.register_protocol(
            "mesh_network",
            MeshNetwork,
            {
                "description": "Self-organizing mesh network",
                "coordination_type": "hybrid",
                "features": ["auto_discovery", "fault_tolerance", "routing"]
            }
        )
        
        # Note: ProtocolBridge is not a Protocol subclass - it's a bridge between protocols
        # It should be instantiated separately when needed, not registered as a protocol
    
    def register_protocol(
        self,
        name: str,
        protocol_class: Type[Protocol],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a protocol type.
        
        Args:
            name: Protocol name
            protocol_class: Protocol class
            metadata: Additional metadata about the protocol
        """
        if name in self._protocols:
            raise ValueError(f"Protocol '{name}' already registered")
        
        if not issubclass(protocol_class, Protocol):
            raise TypeError(f"{protocol_class} must be a subclass of Protocol")
        
        self._protocols[name] = protocol_class
        self._metadata[name] = metadata or {}
        
        logger.info(f"Registered protocol: {name}")
    
    def unregister_protocol(self, name: str):
        """Unregister a protocol type."""
        if name not in self._protocols:
            raise ValueError(f"Protocol '{name}' not found")
        
        # Stop and remove any instances
        if name in self._instances:
            instance = self._instances[name]
            if hasattr(instance, 'stop'):
                asyncio.create_task(instance.stop())
            del self._instances[name]
        
        del self._protocols[name]
        del self._metadata[name]
        
        logger.info(f"Unregistered protocol: {name}")
    
    def create_instance(
        self,
        protocol_name: str,
        node_id: str,
        **kwargs
    ) -> Protocol:
        """Create a protocol instance.
        
        Args:
            protocol_name: Name of the protocol to create
            node_id: Node ID for the protocol instance
            **kwargs: Additional arguments for protocol constructor
            
        Returns:
            Protocol instance
        """
        if protocol_name not in self._protocols:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        
        protocol_class = self._protocols[protocol_name]
        
        # Create instance
        instance = protocol_class(node_id=node_id, **kwargs)
        
        # Store instance
        instance_key = f"{protocol_name}:{node_id}"
        self._instances[instance_key] = instance
        
        logger.info(f"Created {protocol_name} instance for node {node_id}")
        
        return instance
    
    def get_instance(self, protocol_name: str, node_id: str) -> Optional[Protocol]:
        """Get a protocol instance.
        
        Args:
            protocol_name: Protocol name
            node_id: Node ID
            
        Returns:
            Protocol instance or None
        """
        instance_key = f"{protocol_name}:{node_id}"
        return self._instances.get(instance_key)
    
    def list_protocols(self) -> List[str]:
        """List all registered protocol names."""
        return list(self._protocols.keys())
    
    def get_protocol_info(self, name: str) -> Dict[str, Any]:
        """Get information about a protocol.
        
        Args:
            name: Protocol name
            
        Returns:
            Protocol information
        """
        if name not in self._protocols:
            raise ValueError(f"Unknown protocol: {name}")
        
        protocol_class = self._protocols[name]
        metadata = self._metadata[name].copy()
        
        # Add class information
        metadata.update({
            "class_name": protocol_class.__name__,
            "module": protocol_class.__module__,
            "docstring": protocol_class.__doc__
        })
        
        return metadata
    
    def list_instances(self) -> Dict[str, Protocol]:
        """List all active protocol instances."""
        return self._instances.copy()
    
    def select_protocol(
        self,
        coordination_type: str = "hybrid",
        features: Optional[List[str]] = None
    ) -> str:
        """Select a protocol based on requirements.
        
        Args:
            coordination_type: Type of coordination needed
            features: Required features
            
        Returns:
            Selected protocol name
        """
        candidates = []
        
        for name, metadata in self._metadata.items():
            # Check coordination type
            if metadata.get("coordination_type") == coordination_type:
                # Check features
                if features:
                    protocol_features = set(metadata.get("features", []))
                    if all(f in protocol_features for f in features):
                        candidates.append(name)
                else:
                    candidates.append(name)
        
        if not candidates:
            # Fallback to mesh network as default
            return "mesh_network"
        
        # Return first matching candidate
        return candidates[0]
    
    async def stop_all_instances(self):
        """Stop all protocol instances."""
        import asyncio
        
        tasks = []
        for instance in self._instances.values():
            if hasattr(instance, 'stop'):
                tasks.append(instance.stop())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self._instances.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        stats = {
            "total_protocols": len(self._protocols),
            "total_instances": len(self._instances),
            "protocols": {},
            "instances_by_protocol": {}
        }
        
        # Count instances by protocol
        for instance_key in self._instances:
            protocol_name = instance_key.split(":")[0]
            if protocol_name not in stats["instances_by_protocol"]:
                stats["instances_by_protocol"][protocol_name] = 0
            stats["instances_by_protocol"][protocol_name] += 1
        
        # Get protocol details
        for name in self._protocols:
            stats["protocols"][name] = self._metadata.get(name, {})
        
        return stats


# Global registry instance
registry = ProtocolRegistry()


# Helper functions for easy access
def get_protocol(name: str) -> Type[Protocol]:
    """Get a protocol class by name."""
    if name not in registry._protocols:
        raise ValueError(f"Unknown protocol: {name}")
    return registry._protocols[name]


def create_protocol(name: str, node_id: str, **kwargs) -> Protocol:
    """Create a protocol instance."""
    return registry.create_instance(name, node_id, **kwargs)


def list_protocols() -> List[str]:
    """List all available protocols."""
    return registry.list_protocols()
