"""Tests for workflow functionality."""

import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

import pytest

from agenticraft import Agent, Workflow, Step, tool
from agenticraft.core.workflow import StepResult, WorkflowResult
from agenticraft.core.exceptions import WorkflowError, StepExecutionError


class TestStep:
    """Test Step model."""
    
    def test_step_creation_with_agent(self, mock_openai_key):
        """Test creating a step with an agent."""
        agent = Agent(name="TestAgent")
        step = Step(
            name="analyze",
            agent=agent,
            inputs={"data": "test"},
            depends_on=["load"]
        )
        
        assert step.name == "analyze"
        assert step.agent == agent
        assert step.tool is None
        assert step.inputs == {"data": "test"}
        assert step.depends_on == ["load"]
    
    def test_step_creation_with_tool(self):
        """Test creating a step with a tool."""
        @tool
        def process_data(data: str) -> str:
            return data.upper()
        
        step = Step(
            name="process",
            tool=process_data,
            retry_count=2,
            timeout=30
        )
        
        assert step.name == "process"
        assert step.tool == process_data
        assert step.agent is None
        assert step.retry_count == 2
        assert step.timeout == 30
    
    def test_step_validation(self, mock_openai_key):
        """Test step validation."""
        # Must have either agent or tool
        with pytest.raises(ValueError, match="must have either an agent or a tool"):
            Step(name="invalid")
        
        # Cannot have both
        agent = Agent(name="TestAgent")  # Use actual Agent instance
        
        @tool
        def test_tool():
            """Test tool."""
            return "test"
        
        with pytest.raises(ValueError, match="cannot have both agent and tool"):
            Step(name="invalid", agent=agent, tool=test_tool)


class TestWorkflow:
    """Test Workflow class."""
    
    def test_workflow_creation(self):
        """Test basic workflow creation."""
        workflow = Workflow(
            name="test_workflow",
            description="Test workflow"
        )
        
        assert workflow.name == "test_workflow"
        assert workflow.description == "Test workflow"
        assert workflow.id is not None
        assert len(workflow._steps) == 0
    
    def test_add_single_step(self, mock_openai_key):
        """Test adding a single step."""
        workflow = Workflow("test")
        agent = Agent(name="TestAgent")
        
        step = Step("process", agent=agent)
        workflow.add_step(step)
        
        assert len(workflow._steps) == 1
        assert "process" in workflow._steps
        assert workflow._steps["process"] == step
    
    def test_add_multiple_steps(self, mock_openai_key):
        """Test adding multiple steps."""
        workflow = Workflow("test")
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        
        steps = [
            Step("step1", agent=agent1),
            Step("step2", agent=agent2, depends_on=["step1"])
        ]
        workflow.add_steps(steps)
        
        assert len(workflow._steps) == 2
        assert "step1" in workflow._steps
        assert "step2" in workflow._steps
    
    def test_duplicate_step_name(self, mock_openai_key):
        """Test that duplicate step names are rejected."""
        workflow = Workflow("test")
        agent = Agent(name="TestAgent")
        
        workflow.add_step(Step("process", agent=agent))
        
        with pytest.raises(WorkflowError, match="already exists"):
            workflow.add_step(Step("process", agent=agent))
    
    def test_validate_dependencies(self, mock_openai_key):
        """Test dependency validation."""
        workflow = Workflow("test")
        agent = Agent(name="TestAgent")
        
        # Add step with non-existent dependency
        workflow.add_step(
            Step("process", agent=agent, depends_on=["missing"])
        )
        
        with pytest.raises(WorkflowError, match="non-existent step"):
            workflow._validate_dependencies()
    
    def test_execution_order_calculation(self, mock_openai_key):
        """Test calculation of execution order."""
        workflow = Workflow("test")
        agent = Agent(name="TestAgent")
        
        # Create a simple pipeline: load -> process -> save
        workflow.add_steps([
            Step("load", agent=agent),
            Step("process", agent=agent, depends_on=["load"]),
            Step("save", agent=agent, depends_on=["process"])
        ])
        
        order = workflow._calculate_execution_order()
        
        assert order == ["load", "process", "save"]
    
    def test_complex_execution_order(self, mock_openai_key):
        """Test execution order with complex dependencies."""
        workflow = Workflow("test")
        agent = Agent(name="TestAgent")
        
        # Create a diamond pattern:
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
        workflow.add_steps([
            Step("A", agent=agent),
            Step("B", agent=agent, depends_on=["A"]),
            Step("C", agent=agent, depends_on=["A"]),
            Step("D", agent=agent, depends_on=["B", "C"])
        ])
        
        order = workflow._calculate_execution_order()
        
        # A must come first, D must come last
        assert order[0] == "A"
        assert order[-1] == "D"
        # B and C can be in any order but must be between A and D
        assert set(order[1:3]) == {"B", "C"}
    
    def test_circular_dependency_detection(self, mock_openai_key):
        """Test detection of circular dependencies."""
        workflow = Workflow("test")
        agent = Agent(name="TestAgent")
        
        # Create circular dependency: A -> B -> C -> A
        workflow.add_steps([
            Step("A", agent=agent, depends_on=["C"]),
            Step("B", agent=agent, depends_on=["A"]),
            Step("C", agent=agent, depends_on=["B"])
        ])
        
        with pytest.raises(WorkflowError, match="circular dependencies"):
            workflow._calculate_execution_order()
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, mock_openai_key):
        """Test executing a simple workflow."""
        workflow = Workflow("test")
        
        # Create mock agents
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        
        # Mock agent execution
        mock_response1 = Mock(content="Result 1")
        mock_response2 = Mock(content="Result 2")
        
        agent1.arun = AsyncMock(return_value=mock_response1)
        agent2.arun = AsyncMock(return_value=mock_response2)
        
        # Add steps
        workflow.add_steps([
            Step("step1", agent=agent1, inputs={"data": "input"}),
            Step("step2", agent=agent2, depends_on=["step1"])
        ])
        
        # Execute workflow
        result = await workflow.run(data="test data")
        
        assert isinstance(result, WorkflowResult)
        assert result.success is True
        assert len(result.steps) == 2
        assert result["step1"] == mock_response1
        assert result["step2"] == mock_response2
    
    @pytest.mark.asyncio
    async def test_workflow_with_tool_steps(self):
        """Test workflow with tool steps."""
        workflow = Workflow("test")
        
        # Create tools
        @tool
        async def load_data(source: str) -> str:
            await asyncio.sleep(0.01)
            return f"Data from {source}"
        
        @tool
        def process_data(data: str) -> str:
            return data.upper()
        
        # Mock tool execution
        load_data.arun = AsyncMock(return_value="loaded data")
        process_data.arun = AsyncMock(return_value="PROCESSED DATA")
        
        # Add steps
        workflow.add_steps([
            Step("load", tool=load_data, inputs={"source": "file.txt"}),
            Step("process", tool=process_data, depends_on=["load"])
        ])
        
        # Execute
        result = await workflow.run()
        
        assert result.success is True
        assert result["load"] == "loaded data"
        assert result["process"] == "PROCESSED DATA"
    
    @pytest.mark.asyncio
    async def test_workflow_context_passing(self, mock_openai_key):
        """Test that context is passed between steps."""
        workflow = Workflow("test")
        
        agent = Agent(name="TestAgent")
        call_args = []
        
        async def mock_arun(prompt, context=None, **kwargs):
            call_args.append((prompt, context))
            return Mock(content=f"Processed: {prompt}")
        
        agent.arun = mock_arun
        
        workflow.add_steps([
            Step("step1", agent=agent, inputs={"task": "analyze"}),
            Step("step2", agent=agent, depends_on=["step1"])
        ])
        
        await workflow.run(initial="data")
        
        # Check that step2 received step1's output in context
        assert len(call_args) == 2
        step2_prompt, step2_context = call_args[1]
        assert "step1" in step2_context
    
    @pytest.mark.asyncio
    async def test_workflow_input_references(self, mock_openai_key):
        """Test using $ references in step inputs."""
        workflow = Workflow("test")
        
        agent = Agent(name="TestAgent")
        agent.arun = AsyncMock(return_value=Mock(content="result"))
        
        workflow.add_steps([
            Step("step1", agent=agent, inputs={"data": "$input_data"}),
            Step("step2", agent=agent, inputs={"prev": "$step1"}, depends_on=["step1"])
        ])
        
        await workflow.run(input_data="test value")
        
        # Check that references were resolved
        call1_args = agent.arun.call_args_list[0]
        assert "data: test value" in call1_args[0][0]  # prompt should have "data:" not "input_data:"
    
    @pytest.mark.asyncio
    async def test_workflow_step_failure(self, mock_openai_key):
        """Test workflow handling of step failure."""
        workflow = Workflow("test")
        
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        
        agent1.arun = AsyncMock(side_effect=Exception("Step failed"))
        agent2.arun = AsyncMock(return_value=Mock(content="Should not run"))
        
        workflow.add_steps([
            Step("step1", agent=agent1),
            Step("step2", agent=agent2, depends_on=["step1"])
        ])
        
        result = await workflow.run()
        
        assert result.success is False
        assert "step1" in result.steps
        assert result.steps["step1"].success is False
        assert "Step failed" in result.steps["step1"].error
        # step2 should not have run
        assert "step2" not in result.steps
    
    @pytest.mark.asyncio
    async def test_workflow_retry_logic(self):
        """Test step retry logic."""
        workflow = Workflow("test")
        
        # Create a tool that fails first time, succeeds second
        call_count = 0
        
        @tool
        async def flaky_tool():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return "Success"
        
        flaky_tool.arun = AsyncMock(side_effect=flaky_tool.func)
        
        workflow.add_step(Step("flaky", tool=flaky_tool, retry_count=1))
        
        result = await workflow.run()
        
        assert result.success is True
        assert result["flaky"] == "Success"
        assert call_count == 2
    
    def test_workflow_visualization(self, mock_openai_key):
        """Test workflow visualization."""
        workflow = Workflow("pipeline")
        agent = Agent(name="TestAgent")
        
        @tool
        def load():
            return "data"
        
        workflow.add_steps([
            Step("extract", tool=load),
            Step("transform", agent=agent, depends_on=["extract"]),
            Step("load", agent=agent, depends_on=["transform"])
        ])
        
        viz = workflow.visualize()
        
        assert "Workflow: pipeline" in viz
        assert "1. extract (tool)" in viz
        assert "2. transform (agent) <- extract" in viz
        assert "3. load (agent) <- transform" in viz
    
    def test_workflow_repr(self, mock_openai_key):
        """Test workflow string representation."""
        workflow = Workflow("test_flow")
        agent = Agent(name="TestAgent")  # Use actual Agent instance
        workflow.add_step(Step("step1", agent=agent))
        workflow.add_step(Step("step2", agent=agent))
        
        repr_str = repr(workflow)
        assert "test_flow" in repr_str
        assert "steps=2" in repr_str


class TestStepResult:
    """Test StepResult model."""
    
    def test_step_result_success(self):
        """Test successful step result."""
        start = datetime.now()
        result = StepResult(
            step_name="process",
            success=True,
            output={"data": "processed"},
            started_at=start,
            completed_at=datetime.now()
        )
        
        assert result.step_name == "process"
        assert result.success is True
        assert result.output == {"data": "processed"}
        assert result.error is None
    
    def test_step_result_failure(self):
        """Test failed step result."""
        result = StepResult(
            step_name="failed",
            success=False,
            output=None,
            error="Something went wrong",
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.output is None


class TestWorkflowResult:
    """Test WorkflowResult model."""
    
    def test_workflow_result_access(self):
        """Test accessing step results."""
        step1_result = StepResult(
            step_name="step1",
            success=True,
            output="output1",
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        step2_result = StepResult(
            step_name="step2",
            success=True,
            output="output2",
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        result = WorkflowResult(
            workflow_id="test-id",
            workflow_name="test",
            success=True,
            steps={"step1": step1_result, "step2": step2_result},
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        # Test dictionary-style access
        assert result["step1"] == "output1"
        assert result["step2"] == "output2"
        
        # Test missing step
        with pytest.raises(KeyError, match="step3"):
            result["step3"]
