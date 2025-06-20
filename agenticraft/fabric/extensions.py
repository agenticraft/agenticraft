"""
Protocol extensions for AgentiCraft Fabric.

Stub implementations for backwards compatibility.
"""

from typing import Any, Dict, List


class IProtocolExtension:
    """Interface for protocol extensions."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def apply(self, fabric: Any, **kwargs) -> Any:
        """Apply the extension to the fabric."""
        return {"status": "ready"}


class MeshNetworkingExtension(IProtocolExtension):
    """Mesh networking extension for agent communication."""
    
    def __init__(self):
        super().__init__("mesh_networking")
    
    async def apply(self, fabric: Any, agents: List[str], topology: str = "dynamic", **kwargs) -> Any:
        """Create mesh network for agents."""
        return {
            "status": "active",
            "agents": agents,
            "topology": topology,
            "connections": len(agents) * (len(agents) - 1) // 2
        }


class ConsensusExtension(IProtocolExtension):
    """Consensus mechanism for multi-agent agreement."""
    
    def __init__(self):
        super().__init__("consensus")
    
    async def apply(self, fabric: Any, type: str = "byzantine", min_agents: int = 3, **kwargs) -> Any:
        """Enable consensus mechanism."""
        return {
            "status": "ready",
            "type": type,
            "min_agents": min_agents
        }


class ReasoningTraceExtension(IProtocolExtension):
    """Reasoning trace collection for debugging."""
    
    def __init__(self):
        super().__init__("reasoning_traces")
    
    async def apply(self, fabric: Any, level: str = "detailed", **kwargs) -> Any:
        """Enable reasoning trace collection."""
        return {
            "collectors": ["chain_of_thought", "tree_of_thoughts", "react"],
            "level": level,
            "status": "enabled"
        }
