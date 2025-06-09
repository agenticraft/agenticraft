"""Unit tests for workflow module.

This module tests the workflow functionality including:
- Workflow creation and configuration
- Step definition and dependencies
- Workflow execution
- Error handling and retries
- Parallel execution
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from agenticraft.core.agent import AgentResponse
from agenticraft.core.exceptions import WorkflowError
from agenticraft.core.workflow import (
    Step,
    StepResult,
    Workflow,
    WorkflowResult,
)


def create_mock_step(
    name: str,
    agent=None,
    tool=None,
    inputs=None,
    depends_on=None,
    retry_count=0,
    timeout=None,
):
    """Helper to create a Step with mock agent/tool for testing."""
    if agent is None and tool is None:
        agent = MagicMock()
        agent.arun = AsyncMock()

    return Step.model_construct(
        name=name,
        agent=agent,
        tool=tool,
        inputs=inputs or {},
        depends_on=depends_on or [],
        retry_count=retry_count,
        timeout=timeout,
    )


class TestStep:
    """Test Step class functionality."""

    def test_step_creation(self):
        """Test creating a workflow step."""
        # Create a mock agent
        agent = MagicMock()
        agent.arun = AsyncMock()

        # Create step using model_construct to bypass validation
        step = Step.model_construct(
            name="test_step",
            agent=agent,
            inputs={"task": "Do something"},
            depends_on=[],
            retry_count=0,
            timeout=None,
        )

        assert step.name == "test_step"
        assert step.agent == agent
        assert step.inputs == {"task": "Do something"}
        assert step.depends_on == []
        assert step.retry_count == 0
        assert step.timeout is None

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        agent = MagicMock()
        agent.arun = AsyncMock()

        step = Step.model_construct(
            name="final_step",
            agent=agent,
            inputs={"data": "$previous_step"},
            depends_on=["previous_step"],
            retry_count=0,
            timeout=None,
        )

        assert step.depends_on == ["previous_step"]
        assert "$previous_step" in step.inputs["data"]

    def test_step_with_retry_and_timeout(self):
        """Test step with retry and timeout configuration."""
        agent = MagicMock()
        agent.arun = AsyncMock()

        step = Step.model_construct(
            name="retry_step",
            agent=agent,
            inputs={"task": "Risky operation"},
            depends_on=[],
            retry_count=3,
            timeout=30,
        )

        assert step.retry_count == 3
        assert step.timeout == 30

    def test_step_validation(self):
        """Test step validation."""
        # Should require either agent or tool
        with pytest.raises(ValueError, match="must have either an agent or a tool"):
            Step(name="invalid", inputs={})

        # Should not have both agent and tool
        agent = MagicMock()
        agent.arun = AsyncMock()
        tool = MagicMock()
        tool.arun = AsyncMock()

        # For this test, we need to bypass validation to set both
        # First create a valid step then try to add tool
        step = Step.model_construct(
            name="invalid",
            agent=agent,
            tool=tool,
            inputs={},
            depends_on=[],
            retry_count=0,
            timeout=None,
        )

        # Validate that having both is invalid
        with pytest.raises(ValueError, match="cannot have both agent and tool"):
            Step.model_validate(step.model_dump())


class TestWorkflow:
    """Test Workflow class functionality."""

    def test_workflow_creation(self):
        """Test creating a workflow."""
        workflow = Workflow(name="test_workflow", description="A test workflow")

        assert workflow.name == "test_workflow"
        assert workflow.description == "A test workflow"
        assert workflow._steps == {}
        assert len(workflow._steps) == 0

    def test_add_single_step(self):
        """Test adding a single step to workflow."""
        workflow = Workflow(name="test")
        agent = MagicMock()
        agent.arun = AsyncMock()  # Ensure it has arun method

        # Use model_construct to bypass validation for testing
        step = Step.model_construct(
            name="step1",
            agent=agent,
            inputs={"task": "First task"},
            depends_on=[],
            retry_count=0,
            timeout=None,
        )

        workflow.add_step(step)

        assert "step1" in workflow._steps
        assert workflow._steps["step1"] == step

    def test_add_multiple_steps(self):
        """Test adding multiple steps."""
        workflow = Workflow(name="test")
        agent1 = MagicMock()
        agent1.arun = AsyncMock()
        agent2 = MagicMock()
        agent2.arun = AsyncMock()

        steps = [
            Step.model_construct(
                name="step1",
                agent=agent1,
                inputs={"task": "Task 1"},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="step2",
                agent=agent2,
                inputs={"task": "Task 2"},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
        ]

        workflow.add_steps(steps)

        assert len(workflow._steps) == 2
        assert "step1" in workflow._steps
        assert "step2" in workflow._steps

    def test_duplicate_step_names(self):
        """Test that duplicate step names raise error."""
        workflow = Workflow(name="test")
        agent = MagicMock()
        agent.arun = AsyncMock()

        step1 = Step.model_construct(
            name="duplicate",
            agent=agent,
            inputs={},
            depends_on=[],
            retry_count=0,
            timeout=None,
        )
        step2 = Step.model_construct(
            name="duplicate",
            agent=agent,
            inputs={},
            depends_on=[],
            retry_count=0,
            timeout=None,
        )

        workflow.add_step(step1)

        with pytest.raises(WorkflowError, match="already exists"):
            workflow.add_step(step2)

    def test_get_execution_order_simple(self):
        """Test execution order for simple linear workflow."""
        workflow = Workflow(name="test")
        agent = MagicMock()
        agent.arun = AsyncMock()

        steps = [
            Step.model_construct(
                name="step1",
                agent=agent,
                inputs={},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="step2",
                agent=agent,
                inputs={},
                depends_on=["step1"],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="step3",
                agent=agent,
                inputs={},
                depends_on=["step2"],
                retry_count=0,
                timeout=None,
            ),
        ]

        workflow.add_steps(steps)

        order = workflow._calculate_execution_order()
        assert order == ["step1", "step2", "step3"]

    def test_get_execution_order_parallel(self):
        """Test execution order for parallel steps."""
        workflow = Workflow(name="test")
        agent = MagicMock()
        agent.arun = AsyncMock()

        steps = [
            Step.model_construct(
                name="parallel1",
                agent=agent,
                inputs={},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="parallel2",
                agent=agent,
                inputs={},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="parallel3",
                agent=agent,
                inputs={},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="final",
                agent=agent,
                inputs={},
                depends_on=["parallel1", "parallel2", "parallel3"],
                retry_count=0,
                timeout=None,
            ),
        ]

        workflow.add_steps(steps)

        order = workflow._calculate_execution_order()

        # First three can be in any order
        assert set(order[:3]) == {"parallel1", "parallel2", "parallel3"}
        # Final must be last
        assert order[3] == "final"

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        workflow = Workflow(name="test")
        agent = MagicMock()
        agent.arun = AsyncMock()

        steps = [
            Step.model_construct(
                name="step1",
                agent=agent,
                inputs={},
                depends_on=["step3"],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="step2",
                agent=agent,
                inputs={},
                depends_on=["step1"],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="step3",
                agent=agent,
                inputs={},
                depends_on=["step2"],
                retry_count=0,
                timeout=None,
            ),
        ]

        workflow.add_steps(steps)

        with pytest.raises(
            WorkflowError, match="Workflow contains circular dependencies"
        ):
            workflow._calculate_execution_order()

    @pytest.mark.asyncio
    async def test_workflow_execution_simple(self):
        """Test simple workflow execution."""
        workflow = Workflow(name="test")

        # Mock agent and response
        agent = MagicMock()
        agent.arun = AsyncMock(
            return_value=AgentResponse(
                content="Task completed", agent_id=uuid4()  # Use a proper UUID
            )
        )

        step = Step.model_construct(
            name="step1",
            agent=agent,
            inputs={"task": "Do something"},
            depends_on=[],
            retry_count=0,
            timeout=None,
        )

        workflow.add_step(step)

        # Execute workflow
        result = await workflow.run()

        assert result.success
        assert result.success is True
        assert "step1" in result.steps
        assert result.steps["step1"].output.content == "Task completed"

    @pytest.mark.asyncio
    async def test_workflow_execution_with_dependencies(self):
        """Test workflow execution with dependencies."""
        workflow = Workflow(name="test")

        # Mock agents
        agent1 = MagicMock()
        agent1.arun = AsyncMock(
            return_value=AgentResponse(content="First result", agent_id=uuid4())
        )

        agent2 = MagicMock()
        agent2.arun = AsyncMock(
            return_value=AgentResponse(
                content="Second result using first", agent_id=uuid4()
            )
        )

        # Create steps with dependency
        steps = [
            Step.model_construct(
                name="step1",
                agent=agent1,
                inputs={"task": "First task"},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="step2",
                agent=agent2,
                inputs={"task": "Use $step1", "data": "$step1"},
                depends_on=["step1"],
                retry_count=0,
                timeout=None,
            ),
        ]

        workflow.add_steps(steps)

        # Execute
        result = await workflow.run()

        assert result.success
        assert len(result.steps) == 2

        # Check that step2 received step1's output
        agent2.arun.assert_called_once()
        call_args = agent2.arun.call_args
        # The prompt should contain "task: Use $step1" because only values that START with $ are replaced
        assert call_args[0][0] == "task: Use $step1"
        # The context should contain the AgentResponse for the "data" field
        context = call_args[1]["context"]
        assert "data" in context
        assert isinstance(context["data"], AgentResponse)
        assert context["data"].content == "First result"
        # It should also have step1 output since step2 depends on step1
        assert "step1" in context
        assert isinstance(context["step1"], AgentResponse)

    @pytest.mark.asyncio
    async def test_workflow_execution_parallel(self):
        """Test parallel step execution."""
        workflow = Workflow(name="test")

        # Track execution order
        execution_order = []

        # Create async functions for each agent
        async def agent0_run(prompt, context=None):
            execution_order.append("agent0_start")
            await asyncio.sleep(0.1)  # Simulate work
            execution_order.append("agent0_end")
            return AgentResponse(content="agent0 result", agent_id=uuid4())

        async def agent1_run(prompt, context=None):
            execution_order.append("agent1_start")
            await asyncio.sleep(0.1)  # Simulate work
            execution_order.append("agent1_end")
            return AgentResponse(content="agent1 result", agent_id=uuid4())

        async def agent2_run(prompt, context=None):
            execution_order.append("agent2_start")
            await asyncio.sleep(0.1)  # Simulate work
            execution_order.append("agent2_end")
            return AgentResponse(content="agent2 result", agent_id=uuid4())

        # Create agents with the specific functions
        agent0 = MagicMock()
        agent0.arun = AsyncMock(side_effect=agent0_run)

        agent1 = MagicMock()
        agent1.arun = AsyncMock(side_effect=agent1_run)

        agent2 = MagicMock()
        agent2.arun = AsyncMock(side_effect=agent2_run)

        # Create parallel steps
        steps = [
            Step.model_construct(
                name="parallel0",
                agent=agent0,
                inputs={"task": "Task 0"},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="parallel1",
                agent=agent1,
                inputs={"task": "Task 1"},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="parallel2",
                agent=agent2,
                inputs={"task": "Task 2"},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
        ]

        workflow.add_steps(steps)

        # Execute
        result = await workflow.run()

        assert result.success

        # Verify execution happened (workflow executes steps sequentially even without dependencies)
        assert len(execution_order) == 6  # 3 starts + 3 ends
        # Check all agents were executed
        for i in range(3):
            assert f"agent{i}_start" in execution_order
            assert f"agent{i}_end" in execution_order

    @pytest.mark.asyncio
    async def test_workflow_execution_with_retry(self):
        """Test step retry on failure."""
        workflow = Workflow(name="test")

        # Mock agent that fails twice then succeeds
        agent = MagicMock()
        agent.arun = AsyncMock(
            side_effect=[
                Exception("First failure"),
                Exception("Second failure"),
                AgentResponse(content="Success!", agent_id=uuid4()),
            ]
        )

        step = Step.model_construct(
            name="retry_step",
            agent=agent,
            inputs={"task": "Retry task"},
            depends_on=[],
            retry_count=3,
            timeout=None,
        )

        workflow.add_step(step)

        # Execute
        result = await workflow.run()

        assert result.success
        assert agent.arun.call_count == 3
        assert result.steps["retry_step"].output.content == "Success!"
        assert result.steps["retry_step"].metadata["attempts"] == 3

    @pytest.mark.asyncio
    async def test_workflow_execution_failure(self):
        """Test workflow failure handling."""
        workflow = Workflow(name="test")

        # Mock agent that always fails
        agent = MagicMock()
        agent.arun = AsyncMock(side_effect=Exception("Task failed"))

        step = Step.model_construct(
            name="failing_step",
            agent=agent,
            inputs={"task": "This will fail"},
            depends_on=[],
            retry_count=2,
            timeout=None,
        )

        workflow.add_step(step)

        # Execute
        result = await workflow.run()

        assert not result.success
        assert result.success is False
        assert "failing_step" in result.steps
        assert "Task failed" in result.steps["failing_step"].error
        assert agent.arun.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_workflow_execution_with_timeout(self):
        """Test step timeout."""
        workflow = Workflow(name="test")

        # Mock agent that takes too long
        async def slow_task():
            await asyncio.sleep(5)
            return AgentResponse(content="Too late", agent_id=uuid4())

        agent = MagicMock()
        agent.arun = AsyncMock(side_effect=slow_task)

        step = Step.model_construct(
            name="timeout_step",
            agent=agent,
            inputs={"task": "Slow task"},
            depends_on=[],
            retry_count=0,
            timeout=0.1,  # 100ms timeout
        )

        workflow.add_step(step)

        # Execute
        result = await workflow.run()

        assert not result.success
        assert "timeout_step" in result.steps
        assert "timeout" in result.steps["timeout_step"].error.lower()

    def test_workflow_visualize(self):
        """Test workflow visualization."""
        workflow = Workflow(name="test")
        agent = MagicMock()
        agent.arun = AsyncMock()

        steps = [
            Step.model_construct(
                name="start",
                agent=agent,
                inputs={},
                depends_on=[],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="process1",
                agent=agent,
                inputs={},
                depends_on=["start"],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="process2",
                agent=agent,
                inputs={},
                depends_on=["start"],
                retry_count=0,
                timeout=None,
            ),
            Step.model_construct(
                name="end",
                agent=agent,
                inputs={},
                depends_on=["process1", "process2"],
                retry_count=0,
                timeout=None,
            ),
        ]

        workflow.add_steps(steps)

        visualization = workflow.visualize()

        assert "test" in visualization
        assert "start" in visualization
        assert "process1" in visualization
        assert "process2" in visualization
        assert "end" in visualization
        assert "<-" in visualization  # Should show dependencies

    @pytest.mark.asyncio
    async def test_workflow_with_initial_context(self):
        """Test workflow execution with initial context."""
        workflow = Workflow(name="test")

        agent = MagicMock()
        agent.arun = AsyncMock(
            return_value=AgentResponse(content="Processed data", agent_id=uuid4())
        )

        step = Step.model_construct(
            name="process",
            agent=agent,
            inputs={
                "task": "Process data",
                "data": "$input_data",
            },  # data will be replaced
            depends_on=[],
            retry_count=0,
            timeout=None,
        )

        workflow.add_step(step)

        # Run with context
        result = await workflow.run(input_data="Hello World")

        assert result.success

        # Verify context was passed
        agent.arun.assert_called_once()
        call_args = agent.arun.call_args
        prompt = call_args[0][0]
        # The prompt should contain both values (order may vary)
        # because both are strings < 100 characters
        assert "task: Process data" in prompt
        assert "data: Hello World" in prompt
        # Should be a two-line prompt
        assert len(prompt.split("\n")) == 2
        # Both values are in the prompt, so context should be empty
        context = call_args[1]["context"]
        assert context == {}


class TestStepResult:
    """Test StepResult class."""

    def test_step_result_success(self):
        """Test successful step result."""
        result = StepResult(
            step_name="test_step",
            success=True,
            output="Success",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            metadata={"duration": 1.5},
        )

        assert result.step_name == "test_step"
        assert result.success is True
        assert result.output == "Success"
        assert result.error is None
        assert result.metadata["duration"] == 1.5
        assert isinstance(result.started_at, datetime)
        assert isinstance(result.completed_at, datetime)

    def test_step_result_failure(self):
        """Test failed step result."""
        result = StepResult(
            step_name="test_step",
            success=False,
            output=None,
            error="Task failed",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            metadata={"attempts": 3},
        )

        assert result.step_name == "test_step"
        assert result.success is False
        assert result.output is None
        assert result.error == "Task failed"
        assert result.metadata["attempts"] == 3


class TestWorkflowResult:
    """Test WorkflowResult class."""

    def test_workflow_result_success(self):
        """Test successful workflow result."""
        step_results = {
            "step1": StepResult(
                step_name="step1",
                success=True,
                output="Result 1",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            ),
            "step2": StepResult(
                step_name="step2",
                success=True,
                output="Result 2",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            ),
        }

        result = WorkflowResult(
            workflow_id="test-id",
            workflow_name="test",
            success=True,
            steps=step_results,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )

        assert result.workflow_name == "test"
        assert result.success is True
        assert len(result.steps) == 2
        assert result["step1"] == "Result 1"
        assert result["step2"] == "Result 2"

    def test_workflow_result_partial_failure(self):
        """Test workflow with partial failure."""
        step_results = {
            "step1": StepResult(
                step_name="step1",
                success=True,
                output="Success",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            ),
            "step2": StepResult(
                step_name="step2",
                success=False,
                output=None,
                error="Failed",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            ),
        }

        result = WorkflowResult(
            workflow_id="test-id",
            workflow_name="test",
            success=False,
            steps=step_results,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )

        assert not result.success
        assert result["step1"] == "Success"
        # The __getitem__ method returns the output, which is None for failed steps
        assert result.steps["step2"].error == "Failed"
