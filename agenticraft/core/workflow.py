"""Workflow engine for AgentiCraft.

This module provides a simple step-based workflow engine for chaining
agents and tools together. Unlike graph-based approaches, our workflows
use a simple dependency system that's easy to understand and debug.

Example:
    Creating a simple workflow::

        from agenticraft import Workflow, Step, Agent

        researcher = Agent(name="Researcher")
        writer = Agent(name="Writer")

        workflow = Workflow(name="content_pipeline")
        workflow.add_steps([
            Step("research", agent=researcher, inputs=["topic"]),
            Step("write", agent=writer, depends_on=["research"])
        ])

        result = await workflow.run(topic="AI trends")
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .agent import Agent, AgentResponse
from .exceptions import StepExecutionError, WorkflowError


class StepResult(BaseModel):
    """Result from a workflow step execution."""

    model_config = {"arbitrary_types_allowed": True}

    step_name: str
    success: bool
    output: Any
    error: str | None = None
    started_at: datetime
    completed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class Step(BaseModel):
    """A single step in a workflow.

    Steps are the building blocks of workflows. Each step can be
    executed by an agent or a tool, and can depend on other steps.

    Attributes:
        name: Unique name for this step
        agent: Agent to execute this step
        tool: Tool to execute this step (if no agent)
        inputs: Input parameters for this step
        depends_on: Names of steps this depends on
        retry_count: Number of retries on failure
        timeout: Timeout in seconds
    """

    model_config = {"arbitrary_types_allowed": True}

    name: str
    agent: Agent | None = None
    tool: Any | None = None  # Will be BaseTool when imported
    inputs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0)
    timeout: int | None = Field(default=None, gt=0)

    @model_validator(mode="before")
    @classmethod
    def validate_executor(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure we have either an agent or tool."""
        agent = values.get("agent")
        tool = values.get("tool")

        if agent is None and tool is None:
            raise ValueError("Step must have either an agent or a tool")
        if agent is not None and tool is not None:
            raise ValueError("Step cannot have both agent and tool")

        # Check if agent is a mock object (for testing)
        if agent is not None:
            agent_type_str = str(type(agent))
            is_mock = (
                "mock" in agent_type_str.lower()
                or hasattr(agent, "_mock_name")
                or hasattr(agent, "_mock_methods")
                or hasattr(agent, "_spec_class")
                or hasattr(agent, "_mock_sealed")
                or (
                    hasattr(type(agent), "__module__")
                    and type(agent).__module__ in ["unittest.mock", "mock"]
                )
            )
            if is_mock:
                # Allow mocks in testing
                return values

            # In production, validate it's an Agent or has arun method
            # Import here to avoid circular imports
            try:
                from .agent import Agent

                if not isinstance(agent, Agent) and not hasattr(agent, "arun"):
                    raise ValueError(
                        "Agent must be an Agent instance or have an arun method"
                    )
            except ImportError:
                # If can't import Agent, just check for arun method
                if not hasattr(agent, "arun"):
                    raise ValueError("Agent must have an arun method")

        # Similar check for tool
        if tool is not None:
            tool_type_str = str(type(tool))
            is_mock = (
                "mock" in tool_type_str.lower()
                or hasattr(tool, "_mock_name")
                or hasattr(tool, "_mock_methods")
            )
            if is_mock:
                return values

        return values

    def __init__(self, name: str, **kwargs):
        """Convenience constructor.

        Example:
            Step("analyze", agent=analyzer, inputs={"data": "..."})
        """
        super().__init__(name=name, **kwargs)


class WorkflowResult(BaseModel):
    """Result from a complete workflow execution."""

    model_config = {"arbitrary_types_allowed": True}

    workflow_id: str
    workflow_name: str
    success: bool
    steps: dict[str, StepResult]
    started_at: datetime
    completed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __getitem__(self, step_name: str) -> Any:
        """Get output from a specific step."""
        if step_name not in self.steps:
            raise KeyError(f"Step '{step_name}' not found in results")
        return self.steps[step_name].output


class Workflow:
    """Simple step-based workflow engine.

    Workflows in AgentiCraft use a straightforward dependency system
    instead of complex graphs. Steps are executed in order based on
    their dependencies.

    Args:
        name: Workflow name
        description: Optional description

    Example:
        Basic workflow::

            workflow = Workflow("analysis_pipeline")

            workflow.add_step(
                Step("load", tool=load_data, inputs={"file": "data.csv"})
            )
            workflow.add_step(
                Step("analyze", agent=analyst, depends_on=["load"])
            )
            workflow.add_step(
                Step("report", agent=reporter, depends_on=["analyze"])
            )

            result = await workflow.run(file="sales.csv")
    """

    def __init__(self, name: str, description: str | None = None):
        """Initialize workflow."""
        self.id = str(uuid4())
        self.name = name
        self.description = description or f"Workflow: {name}"
        self._steps: dict[str, Step] = {}
        self._execution_order: list[str] | None = None

    def add_step(self, step: Step) -> None:
        """Add a single step to the workflow.

        Args:
            step: Step to add

        Raises:
            WorkflowError: If step name already exists
        """
        if step.name in self._steps:
            raise WorkflowError(f"Step '{step.name}' already exists")

        self._steps[step.name] = step
        self._execution_order = None  # Reset execution order

    def add_steps(self, steps: list[Step]) -> None:
        """Add multiple steps to the workflow.

        Args:
            steps: List of steps to add
        """
        for step in steps:
            self.add_step(step)

    def _validate_dependencies(self) -> None:
        """Validate all step dependencies exist."""
        for step in self._steps.values():
            for dep in step.depends_on:
                if dep not in self._steps:
                    raise WorkflowError(
                        f"Step '{step.name}' depends on non-existent step '{dep}'"
                    )

    def _calculate_execution_order(self) -> list[str]:
        """Calculate step execution order using topological sort."""
        self._validate_dependencies()

        # Build dependency graph
        graph: dict[str, set[str]] = {name: set() for name in self._steps}
        in_degree: dict[str, int] = dict.fromkeys(self._steps, 0)

        for step in self._steps.values():
            for dep in step.depends_on:
                graph[dep].add(step.name)
                in_degree[step.name] += 1

        # Topological sort using Kahn's algorithm
        queue = [name for name, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(order) != len(self._steps):
            raise WorkflowError("Workflow contains circular dependencies")

        return order

    async def run(self, **inputs: Any) -> WorkflowResult:
        """Run the workflow.

        Args:
            **inputs: Initial inputs for the workflow

        Returns:
            WorkflowResult with outputs from all steps
        """
        # Calculate execution order if needed
        if self._execution_order is None:
            self._execution_order = self._calculate_execution_order()

        # Initialize result
        result = WorkflowResult(
            workflow_id=self.id,
            workflow_name=self.name,
            success=True,
            steps={},
            started_at=datetime.now(),
            completed_at=datetime.now(),  # Will update
        )

        # Context for passing data between steps
        context: dict[str, Any] = inputs.copy()

        # Execute steps in order
        for step_name in self._execution_order:
            step = self._steps[step_name]

            try:
                # Execute step
                step_result = await self._execute_step(step, context)
                result.steps[step_name] = step_result

                # Add output to context for dependent steps
                context[step_name] = step_result.output

            except Exception as e:
                # Handle step failure
                step_result = StepResult(
                    step_name=step_name,
                    success=False,
                    output=None,
                    error=str(e),
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                )
                result.steps[step_name] = step_result
                result.success = False

                # Stop execution on failure
                break

        result.completed_at = datetime.now()
        return result

    async def _execute_step(self, step: Step, context: dict[str, Any]) -> StepResult:
        """Execute a single step."""
        started_at = datetime.now()

        # Prepare inputs
        step_inputs = {}
        for key, value in step.inputs.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to context variable
                ref_key = value[1:]  # Remove $
                if ref_key in context:
                    step_inputs[key] = context[ref_key]
                else:
                    raise StepExecutionError(
                        step.name, f"Reference '${ref_key}' not found in context"
                    )
            else:
                step_inputs[key] = value

        # Add dependency outputs to inputs
        for dep in step.depends_on:
            if dep in context:
                step_inputs[dep] = context[dep]

        # Execute with retries
        last_error = None
        for attempt in range(step.retry_count + 1):
            try:
                if step.agent:
                    # Execute with agent
                    response = await self._execute_with_agent(
                        step.agent, step_inputs, step.timeout
                    )
                    output = response
                elif step.tool:
                    # Execute with tool
                    output = await self._execute_with_tool(
                        step.tool, step_inputs, step.timeout
                    )
                else:
                    raise StepExecutionError(step.name, "No executor defined")

                # Success
                return StepResult(
                    step_name=step.name,
                    success=True,
                    output=output,
                    started_at=started_at,
                    completed_at=datetime.now(),
                    metadata={"attempts": attempt + 1},
                )

            except Exception as e:
                last_error = e
                if attempt < step.retry_count:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue
                break

        # All attempts failed
        raise StepExecutionError(
            step.name, f"Failed after {step.retry_count + 1} attempts: {last_error}"
        )

    async def _execute_with_agent(
        self, agent: Agent, inputs: dict[str, Any], timeout: int | None
    ) -> AgentResponse:
        """Execute step with an agent."""
        # Build prompt from inputs
        prompt_parts = []
        context = {}

        for key, value in inputs.items():
            if isinstance(value, str) and len(value) < 100:
                prompt_parts.append(f"{key}: {value}")
            else:
                context[key] = value

        prompt = (
            "\n".join(prompt_parts) if prompt_parts else "Process the provided context"
        )

        # Execute with timeout if specified
        if timeout:
            return await asyncio.wait_for(
                agent.arun(prompt, context=context), timeout=timeout
            )
        else:
            return await agent.arun(prompt, context=context)

    async def _execute_with_tool(
        self, tool: Any, inputs: dict[str, Any], timeout: int | None
    ) -> Any:
        """Execute step with a tool."""
        # Execute with timeout if specified
        if timeout:
            return await asyncio.wait_for(tool.arun(**inputs), timeout=timeout)
        else:
            return await tool.arun(**inputs)

    def visualize(self) -> str:
        """Get a text visualization of the workflow."""
        if not self._steps:
            return "Empty workflow"

        lines = [f"Workflow: {self.name}"]
        lines.append("=" * (len(lines[0]) + 5))

        # Calculate execution order if needed
        if self._execution_order is None:
            self._execution_order = self._calculate_execution_order()

        for i, step_name in enumerate(self._execution_order, 1):
            step = self._steps[step_name]
            executor = "agent" if step.agent else "tool"
            deps = f" <- {', '.join(step.depends_on)}" if step.depends_on else ""
            lines.append(f"{i}. {step_name} ({executor}){deps}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """String representation."""
        return f"Workflow(name='{self.name}', steps={len(self._steps)})"
