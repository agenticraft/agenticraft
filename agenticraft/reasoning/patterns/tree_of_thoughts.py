"""Tree of Thoughts (ToT) reasoning pattern implementation.

This module implements a tree-based reasoning approach where multiple
thought paths are explored and evaluated to find the best solution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from agenticraft.core.reasoning import BaseReasoning, ReasoningTrace


class NodeStatus(Enum):
    """Status of a thought node in the tree."""

    UNEXPLORED = "unexplored"
    EXPLORING = "exploring"
    EVALUATED = "evaluated"
    PRUNED = "pruned"
    SOLUTION = "solution"


@dataclass
class ThoughtNode:
    """A node in the tree of thoughts.

    Attributes:
        id: Unique identifier for the node
        thought: The thought/reasoning at this node
        parent_id: ID of the parent node (None for root)
        children: List of child node IDs
        depth: Depth in the tree (0 for root)
        score: Evaluation score for this thought path
        status: Current status of the node
        metadata: Additional information about the node
    """

    id: str
    thought: str
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    depth: int = 0
    score: float = 0.0
    status: NodeStatus = NodeStatus.UNEXPLORED
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "thought": self.thought,
            "parent_id": self.parent_id,
            "children": self.children,
            "depth": self.depth,
            "score": self.score,
            "status": self.status.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class TreeOfThoughtsReasoning(BaseReasoning):
    """Implements Tree of Thoughts reasoning pattern.

    This pattern explores multiple reasoning paths simultaneously,
    evaluating each path and selecting the most promising ones.
    It supports backtracking and pruning of unpromising paths.

    Example:
        >>> tot = TreeOfThoughtsReasoning(max_depth=5, beam_width=3)
        >>> trace = await tot.think(
        ...     "Design a sustainable city transportation system",
        ...     context={"constraints": ["low emissions", "high capacity"]}
        ... )
        >>> best_path = tot.get_best_path()
    """

    def __init__(
        self,
        max_depth: int = 5,
        beam_width: int = 3,
        exploration_factor: float = 0.3,
        pruning_threshold: float = 0.4,
    ):
        """Initialize Tree of Thoughts reasoning.

        Args:
            max_depth: Maximum depth of the reasoning tree
            beam_width: Number of paths to explore at each level
            exploration_factor: Balance between exploration and exploitation
            pruning_threshold: Score threshold below which to prune branches
        """
        super().__init__(
            name="tree_of_thoughts",
            description="Tree-based exploration of multiple reasoning paths",
        )
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.exploration_factor = exploration_factor
        self.pruning_threshold = pruning_threshold

        self.nodes: dict[str, ThoughtNode] = {}
        self.root_id: str | None = None
        self.solution_nodes: list[str] = []
        self.node_counter = 0

    async def think(
        self, problem: str, context: dict[str, Any] | None = None
    ) -> ReasoningTrace:
        """Generate tree of thoughts reasoning for a problem.

        Args:
            problem: The problem to reason about
            context: Additional context for reasoning

        Returns:
            ReasoningTrace containing the complete reasoning process
        """
        trace = ReasoningTrace()
        self._reset_tree()

        # Step 1: Create root node
        self.root_id = self._create_node(
            thought=f"Problem: {problem}", parent_id=None, depth=0
        )
        trace.add_step(
            "root_creation",
            {"problem": problem, "root_id": self.root_id, "context": context or {}},
        )

        # Step 2: Iterative tree exploration
        for depth in range(self.max_depth):
            # Get nodes to explore at current depth
            nodes_to_explore = self._select_nodes_for_exploration(depth)

            if not nodes_to_explore:
                trace.add_step(
                    f"depth_{depth}_complete",
                    {"message": "No more nodes to explore", "depth": depth},
                )
                break

            trace.add_step(
                f"depth_{depth}_exploration",
                {
                    "depth": depth,
                    "exploring_nodes": len(nodes_to_explore),
                    "total_nodes": len(self.nodes),
                },
            )

            # Explore each selected node
            for node_id in nodes_to_explore:
                # Generate children for this node
                children = await self._generate_children(node_id, context)

                # Evaluate and potentially prune children
                for child_id in children:
                    score = await self._evaluate_node(child_id)
                    self.nodes[child_id].score = score

                    if score < self.pruning_threshold:
                        self.nodes[child_id].status = NodeStatus.PRUNED
                        trace.add_step(
                            "node_pruned",
                            {
                                "node_id": child_id,
                                "score": score,
                                "thought": self.nodes[child_id].thought[:50] + "...",
                            },
                        )
                    else:
                        self.nodes[child_id].status = NodeStatus.EVALUATED

                        # Check if this is a solution
                        if self._is_solution(child_id):
                            self.nodes[child_id].status = NodeStatus.SOLUTION
                            self.solution_nodes.append(child_id)
                            trace.add_step(
                                "solution_found",
                                {
                                    "node_id": child_id,
                                    "score": score,
                                    "depth": self.nodes[child_id].depth,
                                },
                            )

            # Prune the tree periodically
            if depth % 2 == 0:
                pruned_count = self._prune_tree()
                if pruned_count > 0:
                    trace.add_step(
                        f"tree_pruning_depth_{depth}",
                        {
                            "pruned_nodes": pruned_count,
                            "remaining_nodes": len(
                                [
                                    n
                                    for n in self.nodes.values()
                                    if n.status != NodeStatus.PRUNED
                                ]
                            ),
                        },
                    )

        # Step 3: Select best paths
        best_paths = self._get_best_paths(n=3)
        trace.add_step(
            "best_paths_selection",
            {
                "paths_found": len(best_paths),
                "best_scores": [path["score"] for path in best_paths],
            },
        )

        # Step 4: Generate final analysis
        analysis = self._generate_tree_analysis()
        trace.add_step("tree_analysis", analysis)

        return trace

    def _reset_tree(self):
        """Reset the tree for a new problem."""
        self.nodes.clear()
        self.root_id = None
        self.solution_nodes.clear()
        self.node_counter = 0

    def _create_node(self, thought: str, parent_id: str | None, depth: int) -> str:
        """Create a new node in the tree.

        Args:
            thought: The thought content
            parent_id: ID of the parent node
            depth: Depth in the tree

        Returns:
            ID of the created node
        """
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1

        node = ThoughtNode(
            id=node_id, thought=thought, parent_id=parent_id, depth=depth
        )

        self.nodes[node_id] = node

        # Update parent's children list
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node_id)

        return node_id

    def _select_nodes_for_exploration(self, target_depth: int) -> list[str]:
        """Select nodes to explore at a given depth.

        Args:
            target_depth: The depth level to explore

        Returns:
            List of node IDs to explore
        """
        # Get all nodes at the target depth that haven't been explored
        candidates = [
            node_id
            for node_id, node in self.nodes.items()
            if node.depth == target_depth
            and node.status in [NodeStatus.UNEXPLORED, NodeStatus.EVALUATED]
            and node.status != NodeStatus.PRUNED
        ]

        if not candidates:
            return []

        # Sort by score and select top beam_width nodes
        candidates.sort(key=lambda x: self.nodes[x].score, reverse=True)

        # Apply exploration factor to occasionally explore lower-scored nodes
        import random

        if (
            random.random() < self.exploration_factor
            and len(candidates) > self.beam_width
        ):
            # Randomly shuffle some lower-scored nodes into consideration
            exploration_count = max(1, int(self.beam_width * 0.3))
            random_indices = random.sample(
                range(self.beam_width, len(candidates)),
                min(exploration_count, len(candidates) - self.beam_width),
            )
            for idx in random_indices:
                swap_idx = random.randint(0, self.beam_width - 1)
                candidates[swap_idx], candidates[idx] = (
                    candidates[idx],
                    candidates[swap_idx],
                )

        return candidates[: self.beam_width]

    async def _generate_children(
        self, parent_id: str, context: dict[str, Any] | None = None
    ) -> list[str]:
        """Generate child nodes for a parent node.

        Args:
            parent_id: ID of the parent node
            context: Additional context

        Returns:
            List of created child node IDs
        """
        parent = self.nodes[parent_id]
        parent.status = NodeStatus.EXPLORING

        # In a real implementation, this would use an LLM to generate thoughts
        # For now, we'll create structured branches
        branches = self._get_thought_branches(parent.thought, parent.depth)

        child_ids = []
        for branch in branches:
            child_id = self._create_node(
                thought=branch, parent_id=parent_id, depth=parent.depth + 1
            )
            child_ids.append(child_id)

        parent.status = NodeStatus.EVALUATED
        return child_ids

    def _get_thought_branches(self, parent_thought: str, depth: int) -> list[str]:
        """Generate possible thought branches from a parent thought.

        Args:
            parent_thought: The parent's thought
            depth: Current depth in tree

        Returns:
            List of branch thoughts
        """
        # Simplified branching logic based on depth
        if depth == 0:
            # Initial problem decomposition
            return [
                "Approach 1: Focus on environmental sustainability",
                "Approach 2: Prioritize economic efficiency",
                "Approach 3: Emphasize social equity and accessibility",
            ]
        elif depth == 1:
            # Refine approaches
            if "sustainability" in parent_thought.lower():
                return [
                    "Electric public transit with renewable energy",
                    "Bicycle infrastructure and walkable neighborhoods",
                    "Green corridors with mixed transportation modes",
                ]
            elif "efficiency" in parent_thought.lower():
                return [
                    "High-speed rail and metro systems",
                    "Smart traffic management with AI",
                    "Integrated multimodal transport hubs",
                ]
            else:
                return [
                    "Free public transit for low-income residents",
                    "Accessible design for all abilities",
                    "Community-owned transport cooperatives",
                ]
        else:
            # Further refinements
            return [
                f"Refinement A: {parent_thought[:30]}... with advanced features",
                f"Refinement B: {parent_thought[:30]}... with cost optimization",
                f"Refinement C: {parent_thought[:30]}... with phased implementation",
            ]

    async def _evaluate_node(self, node_id: str) -> float:
        """Evaluate the quality/promise of a node.

        Args:
            node_id: ID of the node to evaluate

        Returns:
            Evaluation score (0-1)
        """
        node = self.nodes[node_id]

        # Simple heuristic evaluation
        # In real implementation, this would use an LLM or evaluator

        # Base score decreases with depth (favoring simpler solutions)
        base_score = 0.9 - (node.depth * 0.1)

        # Adjust based on thought content
        thought_lower = node.thought.lower()

        # Positive keywords
        positive_keywords = [
            "efficient",
            "sustainable",
            "integrated",
            "innovative",
            "cost-effective",
        ]
        positive_score = sum(
            0.05 for keyword in positive_keywords if keyword in thought_lower
        )

        # Negative keywords
        negative_keywords = ["expensive", "complex", "difficult", "problematic"]
        negative_score = sum(
            0.05 for keyword in negative_keywords if keyword in thought_lower
        )

        # Parent score influence
        parent_influence = 0
        if node.parent_id and node.parent_id in self.nodes:
            parent_influence = self.nodes[node.parent_id].score * 0.3

        # Calculate final score
        score = base_score + positive_score - negative_score + parent_influence

        # Add some randomness
        import random

        score += random.uniform(-0.1, 0.1)

        return max(0.0, min(1.0, score))

    def _is_solution(self, node_id: str) -> bool:
        """Check if a node represents a complete solution.

        Args:
            node_id: ID of the node to check

        Returns:
            True if the node is a solution
        """
        node = self.nodes[node_id]

        # Simple heuristic: deep enough and high score
        return (
            node.depth >= 3
            and node.score >= 0.7
            and "implementation" in node.thought.lower()
        )

    def _prune_tree(self) -> int:
        """Prune low-scoring branches from the tree.

        Returns:
            Number of nodes pruned
        """
        pruned_count = 0

        # Find nodes to prune (low score and no promising children)
        for node_id, node in self.nodes.items():
            if node.status == NodeStatus.PRUNED:
                continue

            # Check if this node and all its descendants are low-scoring
            if node.score < self.pruning_threshold:
                if not any(
                    self.nodes[child_id].score >= self.pruning_threshold
                    for child_id in node.children
                    if child_id in self.nodes
                ):
                    # Prune this entire subtree
                    pruned_count += self._prune_subtree(node_id)

        return pruned_count

    def _prune_subtree(self, root_id: str) -> int:
        """Prune an entire subtree starting from a root.

        Args:
            root_id: ID of the subtree root

        Returns:
            Number of nodes pruned
        """
        pruned = 0
        nodes_to_prune = [root_id]

        while nodes_to_prune:
            node_id = nodes_to_prune.pop()
            if node_id in self.nodes:
                node = self.nodes[node_id]
                if node.status != NodeStatus.PRUNED:
                    node.status = NodeStatus.PRUNED
                    pruned += 1
                    nodes_to_prune.extend(node.children)

        return pruned

    def _get_best_paths(self, n: int = 1) -> list[dict[str, Any]]:
        """Get the n best paths from root to leaf.

        Args:
            n: Number of paths to return

        Returns:
            List of path dictionaries with nodes and scores
        """
        # Find all leaf nodes (solutions or dead ends)
        leaf_nodes = [
            node_id
            for node_id, node in self.nodes.items()
            if not node.children or node.status == NodeStatus.SOLUTION
        ]

        paths = []
        for leaf_id in leaf_nodes:
            path = self._trace_path_to_root(leaf_id)
            path_score = self._calculate_path_score(path)

            paths.append(
                {
                    "leaf_id": leaf_id,
                    "path": path,
                    "score": path_score,
                    "thoughts": [self.nodes[nid].thought for nid in path],
                }
            )

        # Sort by score and return top n
        paths.sort(key=lambda x: x["score"], reverse=True)
        return paths[:n]

    def _trace_path_to_root(self, node_id: str) -> list[str]:
        """Trace path from a node back to root.

        Args:
            node_id: Starting node ID

        Returns:
            List of node IDs from root to node
        """
        path = []
        current = node_id

        while current is not None:
            path.append(current)
            current = self.nodes[current].parent_id if current in self.nodes else None

        return list(reversed(path))

    def _calculate_path_score(self, path: list[str]) -> float:
        """Calculate the overall score for a path.

        Args:
            path: List of node IDs in the path

        Returns:
            Path score
        """
        if not path:
            return 0.0

        # Average score of all nodes in path, with slight preference for shorter paths
        scores = [self.nodes[nid].score for nid in path if nid in self.nodes]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Length penalty (prefer shorter paths)
        length_penalty = 0.01 * len(path)

        return avg_score - length_penalty

    def _generate_tree_analysis(self) -> dict[str, Any]:
        """Generate analysis of the tree exploration.

        Returns:
            Tree statistics and insights
        """
        total_nodes = len(self.nodes)
        evaluated_nodes = sum(
            1 for n in self.nodes.values() if n.status == NodeStatus.EVALUATED
        )
        pruned_nodes = sum(
            1 for n in self.nodes.values() if n.status == NodeStatus.PRUNED
        )
        solution_nodes = len(self.solution_nodes)

        depth_distribution = {}
        for node in self.nodes.values():
            depth_distribution[node.depth] = depth_distribution.get(node.depth, 0) + 1

        return {
            "total_nodes": total_nodes,
            "evaluated_nodes": evaluated_nodes,
            "pruned_nodes": pruned_nodes,
            "solution_nodes": solution_nodes,
            "max_depth_reached": (
                max(node.depth for node in self.nodes.values()) if self.nodes else 0
            ),
            "depth_distribution": depth_distribution,
            "exploration_efficiency": (
                evaluated_nodes / total_nodes if total_nodes > 0 else 0
            ),
            "pruning_rate": pruned_nodes / total_nodes if total_nodes > 0 else 0,
        }

    def get_best_solution(self) -> dict[str, Any] | None:
        """Get the best solution found.

        Returns:
            Best solution with path and score, or None
        """
        best_paths = self._get_best_paths(n=1)
        return best_paths[0] if best_paths else None

    def visualize_tree(self) -> str:
        """Generate a text visualization of the tree.

        Returns:
            ASCII art representation of the tree
        """
        if not self.root_id:
            return "Empty tree"

        lines = ["Tree of Thoughts:"]
        lines.append("=" * 50)

        def add_node(node_id: str, prefix: str = "", is_last: bool = True):
            node = self.nodes[node_id]

            # Node representation
            connector = "└── " if is_last else "├── "
            status_symbol = {
                NodeStatus.SOLUTION: "✓",
                NodeStatus.PRUNED: "✗",
                NodeStatus.EVALUATED: "•",
                NodeStatus.EXPLORING: "○",
                NodeStatus.UNEXPLORED: "·",
            }.get(node.status, "?")

            lines.append(
                f"{prefix}{connector}[{status_symbol}] "
                f"{node.thought[:40]}... (score: {node.score:.2f})"
            )

            # Add children
            children = node.children
            for i, child_id in enumerate(children):
                extension = "    " if is_last else "│   "
                add_node(child_id, prefix + extension, i == len(children) - 1)

        add_node(self.root_id)
        return "\n".join(lines)

    def start_trace(self, prompt: str) -> ReasoningTrace:
        """Start a new reasoning trace.

        Args:
            prompt: The prompt to trace

        Returns:
            A new ReasoningTrace instance
        """
        trace = ReasoningTrace(prompt=prompt)
        trace.add_step(
            "tree_initialization",
            {
                "prompt": prompt,
                "approach": "tree_of_thoughts",
                "max_depth": self.max_depth,
                "beam_width": self.beam_width,
            },
        )
        return trace

    def format_trace(self, trace: ReasoningTrace) -> str:
        """Format a trace for human consumption.

        Args:
            trace: The trace to format

        Returns:
            Formatted string representation
        """
        if not trace.steps:
            return "No reasoning steps recorded."

        lines = [f"[{self.name}] Tree of Thoughts Reasoning:"]
        lines.append(f"\nProblem: {trace.prompt}")
        lines.append("\nExploration Process:")

        for i, step in enumerate(trace.steps, 1):
            lines.append(f"{i}. {step.step_type}: {step.description}")

            # Add relevant data based on step type
            if step.step_type == "tree_initialization":
                lines.append(f"   - Max depth: {step.data.get('max_depth')}")
                lines.append(f"   - Beam width: {step.data.get('beam_width')}")
            elif step.step_type.startswith("depth_"):
                lines.append(
                    f"   - Nodes explored: {step.data.get('exploring_nodes', 0)}"
                )
                lines.append(f"   - Total nodes: {step.data.get('total_nodes', 0)}")
            elif step.step_type == "solution_found":
                lines.append(f"   - Node ID: {step.data.get('node_id')}")
                lines.append(f"   - Score: {step.data.get('score', 0):.2f}")
            elif step.step_type == "best_paths_selection":
                lines.append(f"   - Paths found: {step.data.get('paths_found', 0)}")
                scores = step.data.get("best_scores", [])
                if scores:
                    lines.append(
                        f"   - Best scores: {', '.join(f'{s:.2f}' for s in scores)}"
                    )

        # Add tree visualization if available
        if hasattr(self, "visualize_tree"):
            lines.append("\nTree Structure:")
            lines.append(self.visualize_tree())

        if trace.result:
            lines.append(f"\nResult: {trace.result}")

        return "\n".join(lines)
