"""
Consensus communication pattern.

This module provides a protocol-agnostic consensus pattern
that can be used by any protocol implementation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, List, Callable, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConsensusType(Enum):
    """Types of consensus algorithms."""
    RAFT = "raft"
    PBFT = "pbft"
    PAXOS = "paxos"
    SIMPLE_MAJORITY = "simple_majority"


@dataclass
class Proposal:
    """Consensus proposal."""
    id: str
    proposer: str
    value: Any
    timestamp: float


@dataclass
class Vote:
    """Vote on a proposal."""
    voter: str
    proposal_id: str
    accept: bool
    reason: Optional[str] = None


class ConsensusNode(ABC):
    """Abstract node in consensus protocol."""
    
    def __init__(self, node_id: str, consensus_type: ConsensusType):
        """Initialize consensus node."""
        self.node_id = node_id
        self.consensus_type = consensus_type
        self._peers: List[str] = []
        self._proposals: Dict[str, Proposal] = {}
        self._votes: Dict[str, List[Vote]] = {}
        
    @abstractmethod
    async def propose(self, value: Any) -> str:
        """Propose a value for consensus."""
        pass
        
    @abstractmethod
    async def vote(self, proposal_id: str, accept: bool, reason: Optional[str] = None) -> None:
        """Vote on a proposal."""
        pass
        
    @abstractmethod
    async def get_consensus(self, proposal_id: str) -> Optional[Any]:
        """Get consensus result if reached."""
        pass
        
    def add_peer(self, peer_id: str) -> None:
        """Add a peer node."""
        if peer_id not in self._peers:
            self._peers.append(peer_id)
            
    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer node."""
        if peer_id in self._peers:
            self._peers.remove(peer_id)
            
    def get_quorum_size(self) -> int:
        """Get required quorum size."""
        total_nodes = len(self._peers) + 1  # Include self
        
        if self.consensus_type == ConsensusType.SIMPLE_MAJORITY:
            return (total_nodes // 2) + 1
        elif self.consensus_type == ConsensusType.PBFT:
            # Byzantine fault tolerance: (3f + 1) nodes tolerate f faults
            # Quorum = 2f + 1
            f = (total_nodes - 1) // 3
            return 2 * f + 1
        else:
            # Default to simple majority
            return (total_nodes // 2) + 1


class ConsensusPattern:
    """Consensus communication pattern."""
    
    def __init__(self, consensus_type: ConsensusType = ConsensusType.SIMPLE_MAJORITY):
        """Initialize pattern."""
        self.consensus_type = consensus_type
        self._nodes: Dict[str, ConsensusNode] = {}
        
    def create_node(self, node_id: str, node_class: type[ConsensusNode] = None) -> ConsensusNode:
        """Create a consensus node."""
        if node_class is None:
            node_class = self._get_default_node_class()
            
        node = node_class(node_id, self.consensus_type)
        self._nodes[node_id] = node
        
        # Add existing nodes as peers
        for other_id, other_node in self._nodes.items():
            if other_id != node_id:
                node.add_peer(other_id)
                other_node.add_peer(node_id)
                
        return node
        
    def remove_node(self, node_id: str) -> None:
        """Remove a node from consensus group."""
        if node_id in self._nodes:
            # Remove from other nodes' peer lists
            for other_node in self._nodes.values():
                other_node.remove_peer(node_id)
                
            del self._nodes[node_id]
            
    def _get_default_node_class(self) -> type[ConsensusNode]:
        """Get default consensus node implementation."""
        
        class SimpleMajorityNode(ConsensusNode):
            """Simple majority consensus implementation."""
            
            async def propose(self, value: Any) -> str:
                """Propose a value."""
                import time
                proposal = Proposal(
                    id=f"{self.node_id}-{int(time.time())}",
                    proposer=self.node_id,
                    value=value,
                    timestamp=time.time()
                )
                
                self._proposals[proposal.id] = proposal
                self._votes[proposal.id] = []
                
                # Auto-vote yes as proposer
                await self.vote(proposal.id, True, "Proposer")
                
                return proposal.id
                
            async def vote(self, proposal_id: str, accept: bool, reason: Optional[str] = None) -> None:
                """Vote on proposal."""
                if proposal_id not in self._proposals:
                    raise ValueError(f"Unknown proposal: {proposal_id}")
                    
                vote = Vote(
                    voter=self.node_id,
                    proposal_id=proposal_id,
                    accept=accept,
                    reason=reason
                )
                
                self._votes[proposal_id].append(vote)
                
            async def get_consensus(self, proposal_id: str) -> Optional[Any]:
                """Check if consensus reached."""
                if proposal_id not in self._proposals:
                    return None
                    
                votes = self._votes.get(proposal_id, [])
                accepts = sum(1 for v in votes if v.accept)
                
                if accepts >= self.get_quorum_size():
                    return self._proposals[proposal_id].value
                    
                return None
                
        return SimpleMajorityNode
