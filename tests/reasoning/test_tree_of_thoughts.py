"""Tests for Tree of Thoughts reasoning pattern."""

from unittest.mock import MagicMock

import pytest

# Handle imports for not-yet-implemented modules
try:
    from agenticraft.reasoning.patterns.tree_of_thoughts import (
        EvaluationCriteria,
        SearchStrategy,
        ThoughtNode,
        ThoughtTree,
        TreeOfThoughtsReasoning,
    )

    TOT_AVAILABLE = True
except ImportError:
    TOT_AVAILABLE = False
    # Create dummy classes to prevent syntax errors
    TreeOfThoughtsReasoning = None
    ThoughtNode = None
    ThoughtTree = None
    EvaluationCriteria = None
    SearchStrategy = None

# Skip all tests if module not implemented
pytestmark = pytest.mark.skipif(
    not TOT_AVAILABLE, reason="Tree of Thoughts reasoning not yet implemented"
)


@pytest.mark.asyncio
class TestTreeOfThoughtsReasoning:
    """Test Tree of Thoughts reasoning pattern."""

    async def test_thought_node_creation(self):
        """Test creating thought nodes."""
        root = ThoughtNode(id="root", thought="Initial problem", value=1.0, depth=0)

        child = ThoughtNode(
            id="child1", thought="First approach", value=0.8, depth=1, parent_id="root"
        )

        assert root.id == "root"
        assert child.parent_id == "root"
        assert child.depth == 1
        assert child.value == 0.8

    async def test_tree_construction(self, mock_provider):
        """Test building a thought tree."""
        tot = TreeOfThoughtsReasoning(
            provider=mock_provider, branch_factor=3, max_depth=2
        )

        # Mock responses for tree expansion
        mock_provider.complete.side_effect = [
            # Root expansion
            MagicMock(content="Approach 1|Approach 2|Approach 3"),
            # Evaluations
            MagicMock(content="0.8"),
            MagicMock(content="0.6"),
            MagicMock(content="0.9"),
            # Best branch expansion
            MagicMock(content="Refined 1|Refined 2|Refined 3"),
            # More evaluations
            MagicMock(content="0.85"),
            MagicMock(content="0.95"),
            MagicMock(content="0.7"),
        ]

        tree = await tot.build_tree("Solve problem", max_depth=2)

        assert tree.root is not None
        assert len(tree.get_children(tree.root.id)) == 3
        assert tree.depth <= 2

    async def test_breadth_first_search(self, mock_provider):
        """Test BFS search strategy."""
        tot = TreeOfThoughtsReasoning(
            provider=mock_provider, search_strategy=SearchStrategy.BREADTH_FIRST
        )

        # Create test tree
        tree = ThoughtTree()
        root = ThoughtNode("root", "Start", 1.0)
        tree.add_node(root)

        # Add children
        for i in range(3):
            child = ThoughtNode(f"child_{i}", f"Option {i}", 0.5 + i * 0.2)
            tree.add_node(child, parent_id="root")

        # Search for best path
        best_path = await tot.search_best_path(tree)

        assert len(best_path) > 0
        assert best_path[0] == root

    async def test_beam_search(self, mock_provider):
        """Test beam search strategy."""
        tot = TreeOfThoughtsReasoning(
            provider=mock_provider,
            search_strategy=SearchStrategy.BEAM_SEARCH,
            beam_width=2,
        )

        # Mock evaluations
        mock_provider.complete.side_effect = [
            MagicMock(content="0.7"),
            MagicMock(content="0.9"),
            MagicMock(content="0.6"),
            MagicMock(content="0.8"),
        ]

        tree = await tot.build_tree("Test query", max_depth=2)
        paths = tot.get_top_k_paths(tree, k=2)

        assert len(paths) <= 2
        # Paths should be sorted by value
        if len(paths) == 2:
            assert paths[0].total_value >= paths[1].total_value

    async def test_evaluation_criteria(self, mock_provider):
        """Test different evaluation criteria."""
        # Test coherence evaluation
        tot_coherence = TreeOfThoughtsReasoning(
            provider=mock_provider, evaluation_criteria=EvaluationCriteria.COHERENCE
        )

        mock_provider.complete.return_value = MagicMock(
            content="This thought is highly coherent: 0.9"
        )

        score = await tot_coherence.evaluate_thought(
            "Logical step following from previous"
        )
        assert score > 0.8

        # Test feasibility evaluation
        tot_feasibility = TreeOfThoughtsReasoning(
            provider=mock_provider, evaluation_criteria=EvaluationCriteria.FEASIBILITY
        )

        mock_provider.complete.return_value = MagicMock(
            content="This approach is feasible: 0.7"
        )

        score = await tot_feasibility.evaluate_thought("Practical implementation plan")
        assert score > 0.6

    async def test_pruning_low_value_branches(self, mock_provider):
        """Test pruning branches with low values."""
        tot = TreeOfThoughtsReasoning(provider=mock_provider, prune_threshold=0.5)

        tree = ThoughtTree()
        root = ThoughtNode("root", "Start", 1.0)
        tree.add_node(root)

        # Add mix of good and bad branches
        good_node = ThoughtNode("good", "Good idea", 0.8)
        bad_node = ThoughtNode("bad", "Bad idea", 0.3)
        tree.add_node(good_node, "root")
        tree.add_node(bad_node, "root")

        # Prune
        tot.prune_tree(tree)

        # Bad node should be pruned
        assert tree.get_node("good") is not None
        assert tree.get_node("bad") is None

    async def test_multi_criteria_evaluation(self, mock_provider):
        """Test evaluation with multiple criteria."""
        tot = TreeOfThoughtsReasoning(
            provider=mock_provider,
            evaluation_criteria=[
                EvaluationCriteria.COHERENCE,
                EvaluationCriteria.RELEVANCE,
                EvaluationCriteria.NOVELTY,
            ],
            criteria_weights=[0.4, 0.4, 0.2],
        )

        # Mock evaluations for each criterion
        mock_provider.complete.side_effect = [
            MagicMock(content="Coherence: 0.9"),
            MagicMock(content="Relevance: 0.8"),
            MagicMock(content="Novelty: 0.6"),
        ]

        score = await tot.evaluate_thought("Test thought")

        # Weighted average: 0.9*0.4 + 0.8*0.4 + 0.6*0.2 = 0.8
        assert abs(score - 0.8) < 0.1

    async def test_backtracking_on_dead_ends(self, mock_provider):
        """Test backtracking when reaching dead ends."""
        tot = TreeOfThoughtsReasoning(provider=mock_provider, allow_backtrack=True)

        # Mock a dead-end scenario
        mock_provider.complete.side_effect = [
            MagicMock(content="Path 1|Path 2"),
            MagicMock(content="0.7"),
            MagicMock(content="0.8"),
            MagicMock(content="DEAD_END"),  # Path 2 leads to dead end
            MagicMock(content="Alternative path"),
            MagicMock(content="0.75"),
        ]

        tree = await tot.build_tree("Test", max_depth=3)

        # Should have backtracked and tried alternative
        assert any(node.is_backtrack for node in tree.nodes.values())

    async def test_parallel_branch_exploration(self, mock_provider):
        """Test exploring branches in parallel."""
        tot = TreeOfThoughtsReasoning(
            provider=mock_provider, parallel_branches=True, max_parallel=3
        )

        # Mock parallel evaluations
        async def mock_batch_evaluate(thoughts):
            return [0.7, 0.8, 0.9]

        tot.batch_evaluate = mock_batch_evaluate

        tree = await tot.build_tree("Test parallel", max_depth=1)

        # All branches should be evaluated in parallel
        assert tree.evaluation_time < tree.sequential_time_estimate

    async def test_save_and_visualize_tree(self, mock_provider, temp_dir):
        """Test saving and visualizing thought trees."""
        tot = TreeOfThoughtsReasoning(provider=mock_provider)

        # Create a simple tree
        tree = ThoughtTree()
        root = ThoughtNode("root", "Problem", 1.0)
        child1 = ThoughtNode("c1", "Solution 1", 0.8)
        child2 = ThoughtNode("c2", "Solution 2", 0.6)

        tree.add_node(root)
        tree.add_node(child1, "root")
        tree.add_node(child2, "root")

        # Save tree
        save_path = temp_dir / "thought_tree.json"
        await tot.save_tree(tree, save_path)
        assert save_path.exists()

        # Generate visualization
        viz_path = temp_dir / "thought_tree.png"
        await tot.visualize_tree(tree, viz_path)
        # Visualization might not work in test env, just check method exists

    async def test_reasoning_with_constraints(self, mock_provider):
        """Test reasoning with specific constraints."""
        tot = TreeOfThoughtsReasoning(
            provider=mock_provider,
            constraints={
                "max_tokens_per_thought": 50,
                "required_keywords": ["solution", "approach"],
                "forbidden_patterns": ["give up", "impossible"],
            },
        )

        # Mock constrained generation
        mock_provider.complete.return_value = MagicMock(
            content="Solution approach: implement step by step"
        )

        result = await tot.reason("Find solution")

        # Should respect constraints
        assert "solution" in result.best_path[-1].thought.lower()
        assert "approach" in result.best_path[-1].thought.lower()
        assert "give up" not in result.best_path[-1].thought.lower()


@pytest.fixture
def sample_thought_tree():
    """Create a sample thought tree for testing."""
    tree = ThoughtTree()

    # Root
    root = ThoughtNode("root", "How to learn programming?", 1.0, depth=0)
    tree.add_node(root)

    # Level 1
    online = ThoughtNode("online", "Take online courses", 0.8, depth=1)
    books = ThoughtNode("books", "Read programming books", 0.7, depth=1)
    practice = ThoughtNode("practice", "Build projects", 0.9, depth=1)

    tree.add_node(online, "root")
    tree.add_node(books, "root")
    tree.add_node(practice, "root")

    # Level 2 (under practice)
    web = ThoughtNode("web", "Build web apps", 0.85, depth=2)
    mobile = ThoughtNode("mobile", "Build mobile apps", 0.8, depth=2)

    tree.add_node(web, "practice")
    tree.add_node(mobile, "practice")

    return tree
