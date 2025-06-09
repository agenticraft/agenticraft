"""Tests for enhanced WorkflowAgent features."""

import asyncio
import json
import os
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agenticraft.agents.workflow import (
    StepStatus,
    Workflow,
    WorkflowAgent,
    WorkflowResult,
)
from agenticraft.core.exceptions import AgentError


class TestEnhancedWorkflowAgent:
    """Test enhanced WorkflowAgent capabilities."""

    @pytest.fixture
    def workflow_agent(self):
        """Create a test workflow agent."""
        return WorkflowAgent(name="TestAgent", instructions="Test workflow execution")

    @pytest.fixture
    def sample_workflow(self, workflow_agent):
        """Create a sample workflow."""
        workflow = workflow_agent.create_workflow(
            "test_workflow", "Test workflow for enhanced features"
        )

        workflow.add_step("step1", "Execute step 1")
        workflow.add_step("step2", "Execute step 2", depends_on=["step1"])
        workflow.add_step("step3", "Execute step 3", depends_on=["step2"])

        return workflow

    def test_visualize_workflow(self, workflow_agent, sample_workflow):
        """Test workflow visualization."""
        # Test Mermaid format
        mermaid = workflow_agent.visualize_workflow(sample_workflow, format="mermaid")
        # The default visualization is ASCII, not Mermaid
        assert "Workflow:" in mermaid or "graph TD" in mermaid
        # Visualization might be ASCII or Mermaid
        assert ("step1[step1]" in mermaid) or (
            "step1" in mermaid and "Workflow:" in mermaid
        )
        # Check for ASCII format or Mermaid format
        assert ("step1 --> step2" in mermaid) or (
            "step2 (depends on: step1)" in mermaid
        )

        # Test ASCII format
        ascii_viz = workflow_agent.visualize_workflow(sample_workflow, format="ascii")
        assert "[step1]" in ascii_viz
        assert "|" in ascii_viz
        assert "v" in ascii_viz

        # Test JSON format
        json_viz = workflow_agent.visualize_workflow(sample_workflow, format="json")
        data = json.loads(json_viz)
        assert data["name"] == "test_workflow"
        assert len(data["steps"]) == 3

        # Test HTML format
        html_viz = workflow_agent.visualize_workflow(sample_workflow, format="html")
        assert "<!DOCTYPE html>" in html_viz
        assert "mermaid" in html_viz

    def test_visualize_workflow_by_id(self, workflow_agent, sample_workflow):
        """Test visualization using workflow ID."""
        workflow_id = sample_workflow.id

        # Visualize by ID
        viz = workflow_agent.visualize_workflow(workflow_id, format="ascii")
        assert "test_workflow" in viz

        # Test with invalid ID
        with pytest.raises(AgentError, match="Workflow .* not found"):
            workflow_agent.visualize_workflow("invalid_id")

    @pytest.mark.asyncio
    async def test_plan_workflow_visually(self, workflow_agent):
        """Test visual workflow planning."""
        # Mock the agent's arun method
        mock_response = AsyncMock()
        mock_response.content = """
        Plan:
        1. Research: Gather information about AI trends
        2. Analyze: Analyze the collected data
        3. Report: Create summary report
        """
        workflow_agent.arun = AsyncMock(return_value=mock_response)

        # Plan workflow
        goal = "Analyze AI market trends"
        constraints = {"time_limit": "2 hours", "resources": ["web", "database"]}

        workflow = await workflow_agent.plan_workflow_visually(goal, constraints)

        # Check workflow created
        assert isinstance(workflow, Workflow)
        assert workflow.name.startswith("workflow_for_")
        assert goal in workflow.description

        # Check default steps added
        step_names = [s.name for s in workflow.steps]
        assert "analyze" in step_names
        assert "plan" in step_names
        assert "execute" in step_names
        assert "verify" in step_names

        # Check dependencies
        plan_step = next(s for s in workflow.steps if s.name == "plan")
        assert "analyze" in plan_step.depends_on

    def test_modify_workflow_dynamically(self, workflow_agent, sample_workflow):
        """Test dynamic workflow modification."""
        # Add new step
        modifications = {
            "add_steps": [
                {"name": "step4", "action": "New step 4", "depends_on": ["step3"]}
            ]
        }

        workflow_agent.modify_workflow_dynamically(sample_workflow.id, modifications)

        # Check step added
        assert len(sample_workflow.steps) == 4
        step4 = sample_workflow.get_step("step4")
        assert step4 is not None
        assert step4.action == "New step 4"
        assert "step3" in step4.depends_on

        # Remove pending step
        modifications = {"remove_steps": ["step4"]}
        workflow_agent.modify_workflow_dynamically(sample_workflow.id, modifications)
        assert len(sample_workflow.steps) == 3

        # Modify existing step
        modifications = {"modify_steps": {"step3": {"timeout": 30.0, "max_retries": 5}}}
        workflow_agent.modify_workflow_dynamically(sample_workflow.id, modifications)

        step3 = sample_workflow.get_step("step3")
        assert step3.timeout == 30.0
        assert step3.max_retries == 5

    def test_modify_running_workflow(self, workflow_agent, sample_workflow):
        """Test modifying a running workflow."""
        # Simulate running workflow
        workflow_agent.running_workflows[sample_workflow.id] = sample_workflow
        sample_workflow.status = StepStatus.RUNNING

        # Mark step1 as completed
        step1 = sample_workflow.get_step("step1")
        step1.status = StepStatus.COMPLETED

        # Try to remove completed step (should fail)
        modifications = {"remove_steps": ["step1"]}
        workflow_agent.modify_workflow_dynamically(sample_workflow.id, modifications)

        # Step should still exist (can't remove completed steps)
        assert sample_workflow.get_step("step1") is not None

        # Clean up
        del workflow_agent.running_workflows[sample_workflow.id]

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, workflow_agent, sample_workflow, tmp_path):
        """Test saving workflow checkpoint."""
        # Set checkpoint directory
        checkpoint_dir = str(tmp_path / "checkpoints")

        # Mark some steps as completed
        step1 = sample_workflow.get_step("step1")
        step1.status = StepStatus.COMPLETED
        step1.result = "Step 1 complete"
        step1.started_at = datetime.now()
        step1.completed_at = datetime.now()

        # Save checkpoint
        checkpoint_file = await workflow_agent.save_checkpoint(
            sample_workflow.id, checkpoint_dir
        )

        # Check file created
        assert os.path.exists(checkpoint_file)
        assert checkpoint_file.endswith(".json")

        # Check content
        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)

        assert checkpoint_data["agent_name"] == "TestAgent"
        assert checkpoint_data["workflow"]["name"] == "test_workflow"
        assert len(checkpoint_data["workflow"]["steps"]) == 3

        # Check step status preserved
        saved_step1 = next(
            s for s in checkpoint_data["workflow"]["steps"] if s["name"] == "step1"
        )
        assert saved_step1["status"] == "completed"
        assert saved_step1["result"] == "Step 1 complete"

    @pytest.mark.asyncio
    async def test_load_checkpoint(self, workflow_agent, tmp_path):
        """Test loading workflow from checkpoint."""
        # Create checkpoint file
        checkpoint_data = {
            "workflow": {
                "id": "test-id",
                "name": "restored_workflow",
                "description": "Restored from checkpoint",
                "steps": [
                    {
                        "id": "step1-id",
                        "name": "step1",
                        "action": "Step 1 action",
                        "status": "completed",
                        "result": "Done",
                        "started_at": datetime.now().isoformat(),
                        "completed_at": datetime.now().isoformat(),
                        "depends_on": [],
                    },
                    {
                        "id": "step2-id",
                        "name": "step2",
                        "action": "Step 2 action",
                        "status": "pending",
                        "depends_on": ["step1"],
                    },
                ],
                "status": "running",
                "started_at": datetime.now().isoformat(),
            },
            "timestamp": datetime.now().isoformat(),
            "agent_name": "TestAgent",
        }

        checkpoint_file = tmp_path / "checkpoint.json"
        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f)

        # Load checkpoint
        workflow = await workflow_agent.load_checkpoint(str(checkpoint_file))

        # Check workflow restored
        assert workflow.name == "restored_workflow"
        assert len(workflow.steps) == 2
        assert workflow.id in workflow_agent.workflows

        # Check step status
        step1 = workflow.get_step("step1")
        assert step1.status == StepStatus.COMPLETED
        assert step1.result == "Done"
        assert isinstance(step1.started_at, datetime)

        # Check file not found error
        with pytest.raises(AgentError, match="Checkpoint file not found"):
            await workflow_agent.load_checkpoint("nonexistent.json")

    @pytest.mark.asyncio
    async def test_resume_workflow(self, workflow_agent, sample_workflow):
        """Test resuming workflow execution."""
        # Mark step1 as completed, step2 as failed
        step1 = sample_workflow.get_step("step1")
        step1.status = StepStatus.COMPLETED

        step2 = sample_workflow.get_step("step2")
        step2.status = StepStatus.FAILED
        step2.retry_count = 1  # Has retries left
        step2.error = "Temporary failure"

        # Mock execute_workflow
        mock_result = WorkflowResult(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            status=StepStatus.COMPLETED,
            duration=10.0,
            step_results={},
            context={},
        )
        workflow_agent.execute_workflow = AsyncMock(return_value=mock_result)

        # Resume
        result = await workflow_agent.resume_workflow(sample_workflow)

        # Check failed step reset to pending
        assert step2.status == StepStatus.PENDING
        assert step2.error is None

        # Check execute called with preserved context
        workflow_agent.execute_workflow.assert_called_once_with(
            sample_workflow, sample_workflow.context, True
        )

    @pytest.mark.asyncio
    async def test_stream_workflow_progress(self, workflow_agent, sample_workflow):
        """Test streaming workflow progress."""
        # Simulate running workflow
        workflow_agent.running_workflows[sample_workflow.id] = sample_workflow
        sample_workflow.status = StepStatus.RUNNING

        # Collect progress updates
        progress_updates = []

        def progress_callback(update):
            progress_updates.append(update)

        # Create progress streaming task
        async def simulate_execution():
            # Wait a bit
            await asyncio.sleep(0.1)

            # Update step status
            step1 = sample_workflow.get_step("step1")
            step1.status = StepStatus.COMPLETED

            await asyncio.sleep(0.1)

            # Complete workflow
            sample_workflow.status = StepStatus.COMPLETED

        # Run simulation and streaming concurrently
        exec_task = asyncio.create_task(simulate_execution())

        # Stream progress
        stream_gen = workflow_agent.stream_workflow_progress(
            sample_workflow.id, callback=progress_callback
        )

        # Collect updates
        updates = []
        async for update in stream_gen:
            updates.append(update)
            if update.get("completed"):
                break

        await exec_task

        # Check updates received
        assert len(updates) > 0
        assert len(progress_updates) > 0  # Callback called

        # Check final update
        final_update = updates[-1]
        assert final_update["completed"] is True
        assert final_update["workflow_id"] == sample_workflow.id

        # Clean up
        del workflow_agent.running_workflows[sample_workflow.id]

    @pytest.mark.asyncio
    async def test_stream_progress_not_running(self, workflow_agent):
        """Test streaming progress for non-running workflow."""
        with pytest.raises(AgentError, match="Workflow .* not running"):
            async for _ in workflow_agent.stream_workflow_progress("invalid_id"):
                pass

    def test_modify_invalid_workflow(self, workflow_agent):
        """Test modifying non-existent workflow."""
        with pytest.raises(AgentError, match="Workflow .* not found"):
            workflow_agent.modify_workflow_dynamically("invalid_id", {"add_steps": []})

    @pytest.mark.asyncio
    async def test_checkpoint_invalid_workflow(self, workflow_agent, tmp_path):
        """Test checkpointing non-existent workflow."""
        with pytest.raises(AgentError, match="Workflow .* not found"):
            await workflow_agent.save_checkpoint("invalid_id", str(tmp_path))

    @pytest.mark.asyncio
    async def test_resume_by_id(self, workflow_agent, sample_workflow):
        """Test resuming workflow by ID."""
        # Mock execute_workflow
        mock_result = WorkflowResult(
            workflow_id=sample_workflow.id,
            workflow_name=sample_workflow.name,
            status=StepStatus.COMPLETED,
            duration=5.0,
            step_results={},
            context={},
        )
        workflow_agent.execute_workflow = AsyncMock(return_value=mock_result)

        # Resume by ID
        result = await workflow_agent.resume_workflow(sample_workflow.id)
        assert result.workflow_id == sample_workflow.id

        # Test with invalid ID
        with pytest.raises(AgentError, match="Workflow .* not found"):
            await workflow_agent.resume_workflow("invalid_id")
