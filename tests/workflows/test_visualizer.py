"""Tests for workflow visualization module."""

import json
from datetime import datetime, timedelta

import pytest

from agenticraft.agents.workflow import (
    Workflow as AgentWorkflow,
)
from agenticraft.core.workflow import Step, StepResult, Workflow, WorkflowResult
from agenticraft.workflows.visual import (
    VisualizationFormat,
    WorkflowVisualizer,
    save_workflow_visualization,
    visualize_workflow,
)


class MockTool:
    """Mock tool for testing."""

    def __init__(self, name: str = "mock_tool"):
        self.name = name

    async def arun(self, **kwargs):
        """Mock async run method."""
        return f"Executed {self.name}"


class TestWorkflowVisualizer:
    """Test workflow visualization functionality."""

    @pytest.fixture
    def simple_workflow(self):
        """Create a simple test workflow."""
        workflow = Workflow("test_workflow", "Test workflow")
        workflow.add_step(Step("load", tool=MockTool("load")))
        workflow.add_step(
            Step("process", tool=MockTool("process"), depends_on=["load"])
        )
        workflow.add_step(Step("save", tool=MockTool("save"), depends_on=["process"]))
        return workflow

    @pytest.fixture
    def parallel_workflow(self):
        """Create a workflow with parallel steps."""
        workflow = Workflow("parallel_test", "Parallel workflow")
        workflow.add_step(Step("start", tool=MockTool("start")))
        workflow.add_step(Step("task1", tool=MockTool("task1"), depends_on=["start"]))
        workflow.add_step(Step("task2", tool=MockTool("task2"), depends_on=["start"]))
        workflow.add_step(Step("task3", tool=MockTool("task3"), depends_on=["start"]))
        workflow.add_step(
            Step(
                "merge", tool=MockTool("merge"), depends_on=["task1", "task2", "task3"]
            )
        )
        return workflow

    @pytest.fixture
    def agent_workflow(self):
        """Create an agent workflow."""
        workflow = AgentWorkflow(name="test_workflow")
        workflow.add_step(name="init", action="Initialize")
        workflow.add_step(name="process", action="Process data", depends_on=["init"])
        workflow.add_step(name="finalize", action="Finalize", depends_on=["process"])
        return workflow

    @pytest.fixture
    def workflow_result(self, simple_workflow):
        """Create a mock workflow result."""
        return WorkflowResult(
            workflow_id=simple_workflow.id,
            workflow_name=simple_workflow.name,
            success=True,
            steps={
                "load": StepResult(
                    step_name="load",
                    success=True,
                    output="Data loaded",
                    started_at=datetime.now() - timedelta(seconds=10),
                    completed_at=datetime.now() - timedelta(seconds=8),
                ),
                "process": StepResult(
                    step_name="process",
                    success=True,
                    output="Data processed",
                    started_at=datetime.now() - timedelta(seconds=8),
                    completed_at=datetime.now() - timedelta(seconds=5),
                ),
                "save": StepResult(
                    step_name="save",
                    success=False,
                    output=None,
                    error="Failed to save",
                    started_at=datetime.now() - timedelta(seconds=5),
                    completed_at=datetime.now() - timedelta(seconds=3),
                ),
            },
            started_at=datetime.now() - timedelta(seconds=10),
            completed_at=datetime.now() - timedelta(seconds=3),
        )

    def test_mermaid_visualization(self, simple_workflow):
        """Test Mermaid diagram generation."""
        visualizer = WorkflowVisualizer()
        result = visualizer.to_mermaid(simple_workflow)

        assert "graph TD" in result
        assert "load[load]" in result
        assert "process[process]" in result
        assert "save[save]" in result
        assert "load --> process" in result
        assert "process --> save" in result
        assert "classDef completed" in result

    def test_mermaid_with_progress(self, simple_workflow, workflow_result):
        """Test Mermaid with execution progress."""
        visualizer = WorkflowVisualizer()
        result = visualizer.to_mermaid(
            simple_workflow, include_progress=True, result=workflow_result
        )

        # Check for status icons
        assert "✅" in result  # Completed steps
        assert "❌" in result  # Failed step

        # Check for timing information
        assert "timer" in result
        assert "s" in result

    def test_ascii_visualization(self, simple_workflow):
        """Test ASCII art visualization."""
        visualizer = WorkflowVisualizer()
        result = visualizer.to_ascii(simple_workflow)

        assert "Workflow: test_workflow" in result
        assert "[load]" in result
        assert "[process]" in result
        assert "[save]" in result
        assert "|" in result
        assert "v" in result

    def test_ascii_parallel_steps(self, parallel_workflow):
        """Test ASCII visualization of parallel steps."""
        visualizer = WorkflowVisualizer()
        result = visualizer.to_ascii(parallel_workflow)

        assert "[start]" in result
        assert "[task1]" in result
        assert "[task2]" in result
        assert "[task3]" in result
        assert "(parallel)" in result
        assert "[merge]" in result

    def test_json_export(self, simple_workflow):
        """Test JSON export."""
        visualizer = WorkflowVisualizer()
        result = visualizer.to_json(simple_workflow)

        data = json.loads(result)
        assert data["name"] == "test_workflow"
        assert len(data["steps"]) == 3

        # Check step structure
        load_step = next(s for s in data["steps"] if s["name"] == "load")
        assert load_step["depends_on"] == []

        process_step = next(s for s in data["steps"] if s["name"] == "process")
        assert process_step["depends_on"] == ["load"]

    def test_json_with_progress(self, simple_workflow, workflow_result):
        """Test JSON export with execution data."""
        visualizer = WorkflowVisualizer()
        result = visualizer.to_json(
            simple_workflow, include_progress=True, result=workflow_result
        )

        data = json.loads(result)
        assert "execution" in data
        assert data["execution"]["status"] == "unknown"  # From mock

        # Check step execution data
        load_step = next(s for s in data["steps"] if s["name"] == "load")
        assert load_step["success"] is True
        assert "duration" in load_step

    def test_html_visualization(self, simple_workflow):
        """Test HTML generation."""
        visualizer = WorkflowVisualizer()
        result = visualizer.to_html(simple_workflow)

        assert "<!DOCTYPE html>" in result
        assert "mermaid.min.js" in result
        assert simple_workflow.name in result
        assert "graph TD" in result

    def test_agent_workflow_visualization(self, agent_workflow):
        """Test visualization of agent workflows."""
        visualizer = WorkflowVisualizer()

        # Test all formats
        mermaid = visualizer.to_mermaid(agent_workflow)
        assert "init[init]" in mermaid

        ascii_viz = visualizer.to_ascii(agent_workflow)
        assert "[init]" in ascii_viz

        json_export = visualizer.to_json(agent_workflow)
        data = json.loads(json_export)
        assert len(data["steps"]) == 3

    def test_visualization_format_enum(self):
        """Test visualization format enum."""
        assert VisualizationFormat.MERMAID == "mermaid"
        assert VisualizationFormat.ASCII == "ascii"
        assert VisualizationFormat.JSON == "json"
        assert VisualizationFormat.HTML == "html"

    def test_visualize_workflow_function(self, simple_workflow):
        """Test convenience function."""
        result = visualize_workflow(simple_workflow, format="mermaid")
        assert "graph TD" in result

        result = visualize_workflow(simple_workflow, format="ascii")
        assert "Workflow:" in result

    def test_save_visualization(self, simple_workflow, tmp_path):
        """Test saving visualization to file."""
        filepath = tmp_path / "test_workflow.html"
        save_workflow_visualization(simple_workflow, str(filepath), format="html")

        assert filepath.exists()
        content = filepath.read_text()
        assert "<!DOCTYPE html>" in content
        assert simple_workflow.name in content

    def test_invalid_format(self, simple_workflow):
        """Test invalid visualization format."""
        visualizer = WorkflowVisualizer()

        with pytest.raises(ValueError, match="Unsupported format"):
            visualizer.visualize(simple_workflow, "invalid_format")

    def test_complex_dependencies(self):
        """Test visualization of complex dependencies."""
        workflow = Workflow("complex", "Complex workflow")

        # Diamond pattern
        workflow.add_step(Step("start", tool=MockTool("start")))
        workflow.add_step(Step("left", tool=MockTool("left"), depends_on=["start"]))
        workflow.add_step(Step("right", tool=MockTool("right"), depends_on=["start"]))
        workflow.add_step(
            Step("merge", tool=MockTool("merge"), depends_on=["left", "right"])
        )
        workflow.add_step(Step("end", tool=MockTool("end"), depends_on=["merge"]))

        visualizer = WorkflowVisualizer()
        mermaid = visualizer.to_mermaid(workflow)

        # Check all connections
        assert "start --> left" in mermaid
        assert "start --> right" in mermaid
        assert "left --> merge" in mermaid
        assert "right --> merge" in mermaid
        assert "merge --> end" in mermaid

    def test_empty_workflow(self):
        """Test visualization of empty workflow."""
        workflow = Workflow("empty", "Empty workflow")

        visualizer = WorkflowVisualizer()

        mermaid = visualizer.to_mermaid(workflow)
        assert "graph TD" in mermaid

        ascii_viz = visualizer.to_ascii(workflow)
        assert "Workflow: empty" in ascii_viz

        json_export = visualizer.to_json(workflow)
        data = json.loads(json_export)
        assert data["steps"] == []

    def test_special_characters_escaping(self):
        """Test escaping of special characters in Mermaid."""
        workflow = Workflow("test", "Test")
        workflow.add_step(Step("step'with'quotes", tool=MockTool("step'with'quotes")))
        workflow.add_step(Step('step"with"double', tool=MockTool('step"with"double')))
        workflow.add_step(
            Step("step\nwith\nnewlines", tool=MockTool("step\nwith\nnewlines"))
        )

        visualizer = WorkflowVisualizer()
        mermaid = visualizer.to_mermaid(workflow)

        # Check escaping
        assert "\\'with\\'" in mermaid
        assert '\\"with\\"' in mermaid
        assert "<br/>" in mermaid  # Newlines converted
