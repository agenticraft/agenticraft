"""Unit tests for WorkflowAgent."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from agenticraft.agents import (
    WorkflowAgent,
    Workflow,
    WorkflowStep,
    WorkflowResult,
    StepStatus,
    StepResult
)
from agenticraft.core.exceptions import AgentError


class TestWorkflowStep:
    """Test WorkflowStep class."""
    
    def test_step_creation(self):
        """Test creating a workflow step."""
        step = WorkflowStep(
            name="test_step",
            description="Test step",
            action="Do something",
            depends_on=["previous_step"]
        )
        
        assert step.name == "test_step"
        assert step.description == "Test step"
        assert step.action == "Do something"
        assert step.depends_on == ["previous_step"]
        assert step.status == StepStatus.PENDING
        assert step.parallel is False
        assert step.max_retries == 3
    
    def test_can_run_no_dependencies(self):
        """Test can_run with no dependencies."""
        step = WorkflowStep(name="independent")
        assert step.can_run([]) is True
        assert step.can_run(["other"]) is True
    
    def test_can_run_with_dependencies(self):
        """Test can_run with dependencies."""
        step = WorkflowStep(
            name="dependent",
            depends_on=["step1", "step2"]
        )
        
        assert step.can_run([]) is False
        assert step.can_run(["step1"]) is False
        assert step.can_run(["step1", "step2"]) is True
        assert step.can_run(["step1", "step2", "step3"]) is True
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        step = WorkflowStep(name="timed")
        assert step.duration is None
        
        step.started_at = datetime.now()
        assert step.duration is None
        
        import time
        time.sleep(0.1)
        step.completed_at = datetime.now()
        assert step.duration > 0.09
        assert step.duration < 0.2


class TestWorkflow:
    """Test Workflow class."""
    
    def test_workflow_creation(self):
        """Test creating a workflow."""
        workflow = Workflow(
            name="test_workflow",
            description="Test workflow"
        )
        
        assert workflow.name == "test_workflow"
        assert workflow.description == "Test workflow"
        assert workflow.steps == []
        assert workflow.status == StepStatus.PENDING
        assert workflow.context == {}
    
    def test_add_step(self):
        """Test adding steps to workflow."""
        workflow = Workflow(name="test")
        
        step1 = workflow.add_step(
            name="step1",
            action="First action"
        )
        
        step2 = workflow.add_step(
            name="step2",
            action="Second action",
            depends_on=["step1"]
        )
        
        assert len(workflow.steps) == 2
        assert workflow.steps[0] == step1
        assert workflow.steps[1] == step2
        assert step2.depends_on == ["step1"]
    
    def test_get_step(self):
        """Test getting step by name."""
        workflow = Workflow(name="test")
        workflow.add_step(name="step1")
        workflow.add_step(name="step2")
        
        assert workflow.get_step("step1").name == "step1"
        assert workflow.get_step("step2").name == "step2"
        assert workflow.get_step("missing") is None
    
    def test_get_ready_steps(self):
        """Test getting ready steps."""
        workflow = Workflow(name="test")
        
        # Add independent steps
        step1 = workflow.add_step(name="step1")
        step2 = workflow.add_step(name="step2")
        
        # Add dependent step
        step3 = workflow.add_step(
            name="step3",
            depends_on=["step1", "step2"]
        )
        
        # Initially, only independent steps are ready
        ready = workflow.get_ready_steps()
        assert len(ready) == 2
        assert step1 in ready
        assert step2 in ready
        
        # Complete step1
        step1.status = StepStatus.COMPLETED
        ready = workflow.get_ready_steps()
        assert len(ready) == 1
        assert step2 in ready
        
        # Complete step2
        step2.status = StepStatus.COMPLETED
        ready = workflow.get_ready_steps()
        assert len(ready) == 1
        assert step3 in ready
    
    def test_validate_valid_workflow(self):
        """Test validating a valid workflow."""
        workflow = Workflow(name="valid")
        workflow.add_step(name="step1")
        workflow.add_step(name="step2", depends_on=["step1"])
        
        errors = workflow.validate()
        assert errors == []
    
    def test_validate_duplicate_names(self):
        """Test validation catches duplicate names."""
        workflow = Workflow(name="invalid")
        workflow.add_step(name="step1")
        workflow.add_step(name="step1")  # Duplicate
        
        errors = workflow.validate()
        assert len(errors) == 1
        assert "Duplicate step names" in errors[0]
    
    def test_validate_unknown_dependency(self):
        """Test validation catches unknown dependencies."""
        workflow = Workflow(name="invalid")
        workflow.add_step(name="step1", depends_on=["missing"])
        
        errors = workflow.validate()
        assert len(errors) == 1
        assert "unknown step 'missing'" in errors[0]
    
    def test_validate_circular_dependency(self):
        """Test validation catches circular dependencies."""
        workflow = Workflow(name="invalid")
        
        # Create circular dependency
        step1 = workflow.add_step(name="step1", depends_on=["step2"])
        step2 = workflow.add_step(name="step2", depends_on=["step1"])
        
        errors = workflow.validate()
        assert len(errors) >= 1
        assert any("Circular dependency" in error for error in errors)


class TestWorkflowAgent:
    """Test WorkflowAgent class."""
    
    @pytest.fixture
    def agent(self):
        """Create a WorkflowAgent instance."""
        return WorkflowAgent(
            name="TestWorkflowAgent",
            instructions="Test workflow agent"
        )
    
    def test_initialization(self):
        """Test WorkflowAgent initialization."""
        agent = WorkflowAgent()
        
        assert agent.name == "WorkflowAgent"
        assert "workflow execution" in agent.config.instructions
        assert agent.workflows == {}
        assert agent.handlers == {}
        assert agent.running_workflows == {}
    
    def test_create_workflow(self, agent):
        """Test creating a workflow."""
        workflow = agent.create_workflow(
            name="test_workflow",
            description="Test description"
        )
        
        assert workflow.name == "test_workflow"
        assert workflow.description == "Test description"
        assert workflow.id in agent.workflows
        assert agent.workflows[workflow.id] == workflow
    
    def test_register_handler(self, agent):
        """Test registering custom handlers."""
        def custom_handler(agent, step, context):
            return f"Handled {step.name}"
        
        agent.register_handler("custom", custom_handler)
        
        assert "custom" in agent.handlers
        assert agent.handlers["custom"] == custom_handler
    
    @pytest.mark.asyncio
    async def test_execute_workflow_simple(self, agent):
        """Test executing a simple workflow."""
        # Create workflow
        workflow = agent.create_workflow("simple")
        workflow.add_step(name="step1", action="Do first thing")
        workflow.add_step(name="step2", action="Do second thing", depends_on=["step1"])
        
        # Mock agent.arun
        mock_response = MagicMock()
        mock_response.content = "Step completed"
        
        with patch.object(agent, 'arun', new_callable=AsyncMock) as mock_arun:
            mock_arun.return_value = mock_response
            
            # Execute workflow
            result = await agent.execute_workflow(workflow, parallel=False)
            
            assert isinstance(result, WorkflowResult)
            assert result.workflow_name == "simple"
            assert result.status == StepStatus.COMPLETED
            assert result.successful
            assert len(result.step_results) == 2
            assert all(r.status == StepStatus.COMPLETED for r in result.step_results.values())
    
    @pytest.mark.asyncio
    async def test_execute_workflow_by_id(self, agent):
        """Test executing workflow by ID."""
        workflow = agent.create_workflow("test")
        workflow.add_step(name="step1")
        
        mock_response = MagicMock()
        mock_response.content = "Done"
        
        with patch.object(agent, 'arun', new_callable=AsyncMock) as mock_arun:
            mock_arun.return_value = mock_response
            
            result = await agent.execute_workflow(workflow.id)
            assert result.workflow_id == workflow.id
    
    @pytest.mark.asyncio
    async def test_execute_workflow_validation_error(self, agent):
        """Test workflow validation errors."""
        workflow = agent.create_workflow("invalid")
        workflow.add_step(name="step1", depends_on=["missing"])
        
        with pytest.raises(AgentError) as exc_info:
            await agent.execute_workflow(workflow)
        
        assert "validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_context(self, agent):
        """Test executing workflow with initial context."""
        workflow = agent.create_workflow("contextual")
        workflow.add_step(name="process")
        
        mock_response = MagicMock()
        mock_response.content = "Processed"
        
        with patch.object(agent, 'arun', new_callable=AsyncMock) as mock_arun:
            mock_arun.return_value = mock_response
            
            initial_context = {"input": "test data"}
            result = await agent.execute_workflow(workflow, context=initial_context)
            
            # Check context was passed
            assert result.context["input"] == "test data"
            assert "process_result" in result.context
    
    @pytest.mark.asyncio
    async def test_execute_parallel_workflow(self, agent):
        """Test parallel workflow execution."""
        workflow = agent.create_workflow("parallel")
        
        # Add parallel steps
        workflow.add_step(name="parallel1", action="Task 1", parallel=True)
        workflow.add_step(name="parallel2", action="Task 2", parallel=True)
        workflow.add_step(
            name="final",
            action="Final task",
            depends_on=["parallel1", "parallel2"]
        )
        
        # Track execution order
        execution_order = []
        
        async def mock_arun(prompt):
            step_name = "parallel1" if "Task 1" in prompt else (
                "parallel2" if "Task 2" in prompt else "final"
            )
            execution_order.append(step_name)
            await asyncio.sleep(0.01)  # Simulate work
            response = MagicMock()
            response.content = f"Completed {step_name}"
            return response
        
        with patch.object(agent, 'arun', side_effect=mock_arun):
            result = await agent.execute_workflow(workflow, parallel=True)
            
            assert result.successful
            # Parallel steps can execute in any order
            assert set(execution_order[:2]) == {"parallel1", "parallel2"}
            # Final step must be last
            assert execution_order[2] == "final"
    
    @pytest.mark.asyncio
    async def test_step_with_custom_handler(self, agent):
        """Test step with custom handler."""
        # Register handler
        async def async_handler(agent, step, context):
            return f"Custom handled: {context.get('input', 'none')}"
        
        agent.register_handler("custom_async", async_handler)
        
        # Create workflow
        workflow = agent.create_workflow("custom")
        workflow.add_step(name="custom_step", handler="custom_async")
        
        # Execute
        result = await agent.execute_workflow(
            workflow,
            context={"input": "test"}
        )
        
        assert result.successful
        assert result.get_step_result("custom_step") == "Custom handled: test"
    
    @pytest.mark.asyncio
    async def test_step_with_condition(self, agent):
        """Test conditional step execution."""
        workflow = agent.create_workflow("conditional")
        workflow.add_step(name="always_run", action="Always execute")
        workflow.add_step(
            name="conditional",
            action="Maybe execute",
            condition="mode == 'skip'"  # Execute when mode is 'skip'
        )
        
        mock_response = MagicMock()
        mock_response.content = "Executed"
        
        with patch.object(agent, 'arun', new_callable=AsyncMock) as mock_arun:
            mock_arun.return_value = mock_response
            
            # Execute with condition false (mode != 'skip')
            result = await agent.execute_workflow(
                workflow,
                context={"mode": "run"}
            )
            
            assert result.step_results["always_run"].status == StepStatus.COMPLETED
            assert result.step_results["conditional"].status == StepStatus.SKIPPED  # Should be skipped when condition is false
            
            # Reset workflow
            for step in workflow.steps:
                step.status = StepStatus.PENDING
            
            # Execute with condition true (mode == 'skip')
            result = await agent.execute_workflow(
                workflow,
                context={"mode": "skip"}
            )
            
            assert result.step_results["always_run"].status == StepStatus.COMPLETED
            assert result.step_results["conditional"].status == StepStatus.COMPLETED  # Should be completed when condition is true
    
    @pytest.mark.asyncio
    async def test_step_timeout(self, agent):
        """Test step timeout handling."""
        workflow = agent.create_workflow("timeout")
        workflow.add_step(
            name="slow_step",
            action="Slow task",
            timeout=0.1  # 100ms timeout
        )
        
        async def slow_arun(prompt):
            await asyncio.sleep(0.2)  # Exceed timeout
            return MagicMock(content="Too late")
        
        with patch.object(agent, 'arun', side_effect=slow_arun):
            result = await agent.execute_workflow(workflow)
            
            step_result = result.step_results["slow_step"]
            assert step_result.status == StepStatus.FAILED
            assert "timed out" in step_result.error
    
    @pytest.mark.asyncio
    async def test_step_retry(self, agent):
        """Test step retry on failure."""
        workflow = agent.create_workflow("retry")
        workflow.add_step(
            name="flaky_step",
            action="Flaky task",
            max_retries=2
        )
        
        # Track attempts
        attempts = []
        
        async def flaky_arun(prompt):
            attempts.append(1)
            if len(attempts) < 2:
                raise Exception("Temporary failure")
            return MagicMock(content="Success on retry")
        
        with patch.object(agent, 'arun', side_effect=flaky_arun):
            # The retry mechanism is working correctly!
            result = await agent.execute_workflow(workflow)
            
            # Should have retried once after first failure
            assert len(attempts) == 2
            
            # The step should eventually succeed
            step_result = result.step_results["flaky_step"]
            assert step_result.status == StepStatus.COMPLETED
            assert step_result.result == "Success on retry"
    
    def test_get_workflow_status(self, agent):
        """Test getting workflow status."""
        workflow = agent.create_workflow("status_test")
        workflow.add_step(name="step1")
        
        # Not running
        assert agent.get_workflow_status(workflow.id) is None
        
        # Add to running
        workflow.status = StepStatus.RUNNING
        agent.running_workflows[workflow.id] = workflow
        
        status = agent.get_workflow_status(workflow.id)
        assert status is not None
        assert status["id"] == workflow.id
        assert status["name"] == "status_test"
        assert status["status"] == StepStatus.RUNNING


class TestWorkflowResult:
    """Test WorkflowResult class."""
    
    def test_result_creation(self):
        """Test creating workflow result."""
        step_results = {
            "step1": StepResult(
                name="step1",
                status=StepStatus.COMPLETED,
                result="Result 1"
            ),
            "step2": StepResult(
                name="step2",
                status=StepStatus.FAILED,
                error="Error occurred"
            )
        }
        
        result = WorkflowResult(
            workflow_id="test-id",
            workflow_name="test",
            status=StepStatus.FAILED,
            duration=5.5,
            step_results=step_results
        )
        
        assert result.workflow_id == "test-id"
        assert result.workflow_name == "test"
        assert not result.successful
        assert result.failed_steps == ["step2"]
        assert result.get_step_result("step1") == "Result 1"
        assert result.get_step_result("missing") is None
    
    def test_format_summary(self):
        """Test formatting workflow summary."""
        step_results = {
            "fetch": StepResult(
                name="fetch",
                status=StepStatus.COMPLETED,
                duration=1.2
            ),
            "process": StepResult(
                name="process",
                status=StepStatus.FAILED,
                error="Processing error",
                duration=0.5
            ),
            "save": StepResult(
                name="save",
                status=StepStatus.SKIPPED
            )
        }
        
        result = WorkflowResult(
            workflow_id="test",
            workflow_name="Data Pipeline",
            status=StepStatus.FAILED,
            duration=2.0,
            step_results=step_results
        )
        
        summary = result.format_summary()
        
        assert "Workflow: Data Pipeline" in summary
        assert "Status: StepStatus.FAILED" in summary
        assert "Duration: 2.00s" in summary
        assert "✅ fetch: StepStatus.COMPLETED (1.20s)" in summary
        assert "❌ process: StepStatus.FAILED (0.50s) - Error: Processing error" in summary
        assert "⏭️ save: StepStatus.SKIPPED" in summary
