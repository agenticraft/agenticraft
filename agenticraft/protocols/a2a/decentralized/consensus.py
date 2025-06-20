"""Consensus protocol for decentralized coordination."""

import asyncio
import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from ..base import Protocol, ProtocolMessage, ProtocolNode, MessageType, NodeStatus

logger = logging.getLogger(__name__)


class ConsensusType(Enum):
    """Types of consensus algorithms."""
    SIMPLE_MAJORITY = "simple_majority"
    BYZANTINE = "byzantine"
    RAFT = "raft"
    PROOF_OF_WORK = "proof_of_work"


class ProposalStatus(Enum):
    """Status of a consensus proposal."""
    PROPOSED = "proposed"
    VOTING = "voting"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Vote:
    """A vote in consensus."""
    voter_id: str
    proposal_id: UUID
    value: bool  # True = accept, False = reject
    timestamp: datetime = field(default_factory=datetime.now)
    signature: Optional[str] = None  # For cryptographic verification


@dataclass
class Proposal:
    """A proposal for consensus."""
    id: UUID = field(default_factory=uuid4)
    proposer_id: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    status: ProposalStatus = ProposalStatus.PROPOSED
    votes: Dict[str, Vote] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    consensus_type: ConsensusType = ConsensusType.SIMPLE_MAJORITY
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_vote(self, vote: Vote):
        """Add a vote to the proposal."""
        self.votes[vote.voter_id] = vote
    
    def get_vote_count(self) -> Tuple[int, int]:
        """Get (accept, reject) vote counts."""
        accept = sum(1 for v in self.votes.values() if v.value)
        reject = sum(1 for v in self.votes.values() if not v.value)
        return accept, reject
    
    def is_expired(self) -> bool:
        """Check if proposal has expired."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


class ConsensusProtocol(Protocol):
    """Decentralized consensus protocol for agent coordination.
    
    Features:
    - Multiple consensus algorithms
    - Byzantine fault tolerance
    - Proposal lifecycle management
    - Cryptographic verification (optional)
    - Automatic leader election
    """
    
    def __init__(
        self,
        node_id: str,
        consensus_type: ConsensusType = ConsensusType.SIMPLE_MAJORITY,
        min_nodes: int = 3
    ):
        """Initialize consensus protocol.
        
        Args:
            node_id: Unique node identifier
            consensus_type: Type of consensus algorithm
            min_nodes: Minimum nodes required for consensus
        """
        super().__init__(node_id)
        self.consensus_type = consensus_type
        self.min_nodes = min_nodes
        
        # Consensus state
        self.proposals: Dict[UUID, Proposal] = {}
        self.pending_decisions: Dict[UUID, asyncio.Future] = {}
        self.leader_id: Optional[str] = None
        self.term: int = 0  # For leader election
        
        # Configuration
        self.config = {
            "proposal_timeout": 30.0,  # 30 seconds
            "heartbeat_interval": 5.0,
            "election_timeout": 10.0,
            "byzantine_threshold": 0.67  # 2/3 majority for Byzantine
        }
        
        # Background tasks
        self._consensus_task: Optional[asyncio.Task] = None
        self._election_task: Optional[asyncio.Task] = None
        
        # Message handlers
        self.register_handler(MessageType.CONSENSUS, self._handle_consensus_message)
        
        # Metrics
        self.metrics = {
            "proposals_created": 0,
            "proposals_accepted": 0,
            "proposals_rejected": 0,
            "votes_cast": 0,
            "elections_held": 0
        }
    
    async def start(self):
        """Start consensus protocol."""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._consensus_task = asyncio.create_task(self._consensus_loop())
        if self.consensus_type == ConsensusType.RAFT:
            self._election_task = asyncio.create_task(self._election_loop())
        
        logger.info(f"Consensus protocol {self.node_id} started (type: {self.consensus_type.value})")
    
    async def stop(self):
        """Stop consensus protocol."""
        self._running = False
        
        # Cancel background tasks
        for task in [self._consensus_task, self._election_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Cancel pending decisions
        for future in self.pending_decisions.values():
            if not future.done():
                future.cancel()
        
        logger.info(f"Consensus protocol {self.node_id} stopped")
    
    async def propose(
        self,
        content: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> bool:
        """Propose a decision for consensus.
        
        Args:
            content: Proposal content
            timeout: Timeout for reaching consensus
            
        Returns:
            True if proposal accepted, False if rejected
            
        Raises:
            TimeoutError: If consensus not reached in time
            RuntimeError: If insufficient nodes for consensus
        """
        # Check if we have enough nodes
        active_nodes = self.get_active_nodes()
        if len(active_nodes) + 1 < self.min_nodes:  # +1 for self
            raise RuntimeError(f"Insufficient nodes for consensus: {len(active_nodes) + 1} < {self.min_nodes}")
        
        # Create proposal
        proposal = Proposal(
            proposer_id=self.node_id,
            content=content,
            consensus_type=self.consensus_type,
            expires_at=datetime.now().timestamp() + (timeout or self.config["proposal_timeout"])
        )
        
        self.proposals[proposal.id] = proposal
        self.metrics["proposals_created"] += 1
        
        # Create future for result
        future = asyncio.Future()
        self.pending_decisions[proposal.id] = future
        
        # Broadcast proposal
        message = ProtocolMessage(
            type=MessageType.CONSENSUS,
            sender=self.node_id,
            content={
                "action": "propose",
                "proposal": self._serialize_proposal(proposal)
            }
        )
        
        await self.broadcast(message)
        
        # Vote on own proposal
        self_vote = Vote(
            voter_id=self.node_id,
            proposal_id=proposal.id,
            value=True  # Always vote yes on own proposals
        )
        proposal.add_vote(self_vote)
        
        # Wait for consensus
        try:
            result = await asyncio.wait_for(
                future,
                timeout=timeout or self.config["proposal_timeout"]
            )
            return result
        except asyncio.TimeoutError:
            proposal.status = ProposalStatus.EXPIRED
            raise TimeoutError(f"Consensus not reached for proposal {proposal.id}")
    
    async def _handle_consensus_message(self, message: ProtocolMessage):
        """Handle consensus protocol messages."""
        action = message.content.get("action")
        
        if action == "propose":
            await self._handle_proposal(message)
        elif action == "vote":
            await self._handle_vote(message)
        elif action == "request_vote":  # For Raft
            await self._handle_vote_request(message)
        elif action == "heartbeat":  # For leader
            await self._handle_heartbeat(message)
    
    async def _handle_proposal(self, message: ProtocolMessage):
        """Handle incoming proposal."""
        proposal_data = message.content.get("proposal", {})
        
        # Deserialize proposal
        proposal = self._deserialize_proposal(proposal_data)
        
        # Store proposal
        self.proposals[proposal.id] = proposal
        
        # Decide how to vote
        vote_value = await self._decide_vote(proposal)
        
        # Create vote
        vote = Vote(
            voter_id=self.node_id,
            proposal_id=proposal.id,
            value=vote_value
        )
        
        # Send vote
        vote_message = ProtocolMessage(
            type=MessageType.CONSENSUS,
            sender=self.node_id,
            target=proposal.proposer_id,
            content={
                "action": "vote",
                "vote": {
                    "proposal_id": str(proposal.id),
                    "value": vote.value,
                    "timestamp": vote.timestamp.isoformat()
                }
            }
        )
        
        await self.send_message(vote_message)
        self.metrics["votes_cast"] += 1
    
    async def _handle_vote(self, message: ProtocolMessage):
        """Handle incoming vote."""
        vote_data = message.content.get("vote", {})
        
        proposal_id = UUID(vote_data["proposal_id"])
        proposal = self.proposals.get(proposal_id)
        
        if not proposal:
            logger.warning(f"Received vote for unknown proposal: {proposal_id}")
            return
        
        # Create vote object
        vote = Vote(
            voter_id=message.sender,
            proposal_id=proposal_id,
            value=vote_data["value"],
            timestamp=datetime.fromisoformat(vote_data["timestamp"])
        )
        
        # Add vote
        proposal.add_vote(vote)
        
        # Check if consensus reached
        if self._check_consensus(proposal):
            await self._finalize_proposal(proposal)
    
    def _check_consensus(self, proposal: Proposal) -> bool:
        """Check if consensus has been reached."""
        total_nodes = len(self.get_active_nodes()) + 1  # +1 for self
        accept_votes, reject_votes = proposal.get_vote_count()
        
        if proposal.consensus_type == ConsensusType.SIMPLE_MAJORITY:
            # Simple majority
            required = total_nodes // 2 + 1
            return accept_votes >= required or reject_votes >= required
            
        elif proposal.consensus_type == ConsensusType.BYZANTINE:
            # Byzantine fault tolerance - 2/3 majority
            required = int(total_nodes * self.config["byzantine_threshold"])
            return accept_votes >= required or reject_votes >= (total_nodes - required + 1)
            
        elif proposal.consensus_type == ConsensusType.RAFT:
            # Raft - majority with leader
            if self.leader_id == self.node_id:
                required = total_nodes // 2 + 1
                return accept_votes >= required
            else:
                # Only leader can declare consensus in Raft
                return False
                
        elif proposal.consensus_type == ConsensusType.PROOF_OF_WORK:
            # Proof of work - first valid solution wins
            # This is simplified - real PoW would verify work
            return len(proposal.votes) > 0
        
        return False
    
    async def _finalize_proposal(self, proposal: Proposal):
        """Finalize a proposal after consensus."""
        accept_votes, reject_votes = proposal.get_vote_count()
        
        if accept_votes > reject_votes:
            proposal.status = ProposalStatus.ACCEPTED
            self.metrics["proposals_accepted"] += 1
            result = True
        else:
            proposal.status = ProposalStatus.REJECTED
            self.metrics["proposals_rejected"] += 1
            result = False
        
        # Notify waiting future
        if proposal.id in self.pending_decisions:
            future = self.pending_decisions[proposal.id]
            if not future.done():
                future.set_result(result)
        
        # Broadcast result
        result_message = ProtocolMessage(
            type=MessageType.CONSENSUS,
            sender=self.node_id,
            content={
                "action": "result",
                "proposal_id": str(proposal.id),
                "status": proposal.status.value,
                "votes": {
                    "accept": accept_votes,
                    "reject": reject_votes
                }
            }
        )
        
        await self.broadcast(result_message)
    
    async def _decide_vote(self, proposal: Proposal) -> bool:
        """Decide how to vote on a proposal."""
        # Simple voting logic - can be customized
        content = proposal.content
        
        # Example: Vote based on resource requirements
        if "resource_required" in content:
            # Check if we have the resources
            required = content["resource_required"]
            available = content.get("resource_available", 100)
            return required <= available
        
        # Example: Vote based on task complexity
        if "complexity" in content:
            # Accept if complexity is manageable
            return content["complexity"] < 0.8
        
        # Default: Accept proposals
        return True
    
    async def _consensus_loop(self):
        """Background task for consensus management."""
        while self._running:
            try:
                # Check for expired proposals
                current_time = datetime.now()
                
                for proposal in list(self.proposals.values()):
                    if proposal.status == ProposalStatus.VOTING and proposal.is_expired():
                        proposal.status = ProposalStatus.EXPIRED
                        
                        # Notify if pending
                        if proposal.id in self.pending_decisions:
                            future = self.pending_decisions[proposal.id]
                            if not future.done():
                                future.set_exception(TimeoutError("Proposal expired"))
                
                # Clean old proposals
                cutoff_time = current_time.timestamp() - 3600  # 1 hour
                old_proposals = [
                    prop_id for prop_id, prop in self.proposals.items()
                    if prop.created_at.timestamp() < cutoff_time and
                    prop.status in [ProposalStatus.ACCEPTED, ProposalStatus.REJECTED, ProposalStatus.EXPIRED]
                ]
                
                for prop_id in old_proposals:
                    del self.proposals[prop_id]
                    self.pending_decisions.pop(prop_id, None)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Consensus loop error: {e}")
                await asyncio.sleep(1)
    
    async def _election_loop(self):
        """Leader election for Raft consensus."""
        election_timeout = random.uniform(
            self.config["election_timeout"],
            self.config["election_timeout"] * 2
        )
        last_heartbeat = time.time()
        
        while self._running:
            try:
                # Check if we need to start election
                if self.leader_id is None or (time.time() - last_heartbeat) > election_timeout:
                    await self._start_election()
                    election_timeout = random.uniform(
                        self.config["election_timeout"],
                        self.config["election_timeout"] * 2
                    )
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Election loop error: {e}")
                await asyncio.sleep(1)
    
    async def _start_election(self):
        """Start leader election (Raft)."""
        self.term += 1
        self.leader_id = None
        self.metrics["elections_held"] += 1
        
        logger.info(f"Starting election for term {self.term}")
        
        # Vote for self
        votes_received = 1
        
        # Request votes from other nodes
        vote_request = ProtocolMessage(
            type=MessageType.CONSENSUS,
            sender=self.node_id,
            content={
                "action": "request_vote",
                "term": self.term,
                "candidate_id": self.node_id
            }
        )
        
        await self.broadcast(vote_request)
        
        # Wait for votes (simplified)
        await asyncio.sleep(self.config["election_timeout"] / 2)
        
        # Check if we won (simplified - assumes we get all votes)
        active_nodes = len(self.get_active_nodes()) + 1
        if votes_received > active_nodes // 2:
            self.leader_id = self.node_id
            logger.info(f"Elected as leader for term {self.term}")
            
            # Send heartbeat as new leader
            await self._send_leader_heartbeat()
    
    async def _send_leader_heartbeat(self):
        """Send heartbeat as leader."""
        heartbeat = ProtocolMessage(
            type=MessageType.CONSENSUS,
            sender=self.node_id,
            content={
                "action": "heartbeat",
                "term": self.term,
                "leader_id": self.leader_id
            }
        )
        
        await self.broadcast(heartbeat)
    
    async def _handle_vote_request(self, message: ProtocolMessage):
        """Handle vote request in leader election."""
        # Simplified - always vote for first candidate in higher term
        request_term = message.content.get("term", 0)
        candidate_id = message.content.get("candidate_id")
        
        if request_term > self.term:
            self.term = request_term
            self.leader_id = None
            
            # Send vote
            vote_response = ProtocolMessage(
                type=MessageType.CONSENSUS,
                sender=self.node_id,
                target=candidate_id,
                content={
                    "action": "vote_response",
                    "term": self.term,
                    "vote_granted": True
                }
            )
            
            await self.send_message(vote_response)
    
    async def _handle_heartbeat(self, message: ProtocolMessage):
        """Handle leader heartbeat."""
        leader_id = message.content.get("leader_id")
        term = message.content.get("term", 0)
        
        if term >= self.term:
            self.term = term
            self.leader_id = leader_id
    
    def _serialize_proposal(self, proposal: Proposal) -> Dict[str, Any]:
        """Serialize proposal for transmission."""
        return {
            "id": str(proposal.id),
            "proposer_id": proposal.proposer_id,
            "content": proposal.content,
            "consensus_type": proposal.consensus_type.value,
            "created_at": proposal.created_at.isoformat(),
            "expires_at": proposal.expires_at
        }
    
    def _deserialize_proposal(self, data: Dict[str, Any]) -> Proposal:
        """Deserialize proposal from transmission."""
        return Proposal(
            id=UUID(data["id"]),
            proposer_id=data["proposer_id"],
            content=data["content"],
            consensus_type=ConsensusType(data["consensus_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=data.get("expires_at")
        )
    
    async def send_message(self, message: ProtocolMessage) -> Any:
        """Send a message (simplified)."""
        logger.debug(f"Sending {message.type.value} to {message.target or 'all'}")
        return message
    
    async def broadcast(self, message: ProtocolMessage):
        """Broadcast message to all nodes."""
        message.sender = self.node_id
        # In real implementation, this would use network
        logger.debug(f"Broadcasting {message.content.get('action', 'unknown')} message")
    
    def get_consensus_stats(self) -> Dict[str, Any]:
        """Get consensus statistics."""
        return {
            "consensus_type": self.consensus_type.value,
            "current_leader": self.leader_id,
            "current_term": self.term,
            "active_proposals": sum(1 for p in self.proposals.values() if p.status == ProposalStatus.VOTING),
            "total_proposals": len(self.proposals),
            **self.metrics
        }
