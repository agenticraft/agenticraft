"""WorkflowAgent implementation for AgentiCraft.

The WorkflowAgent provides capabilities for executing multi-step workflows,
with support for sequential execution, conditional logic, parallel tasks,
error handling, visual planning, and checkpoint/resume capabilities.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from ..core.agent import Agent
from ..core.exceptions import AgentError

# TODO: Import when workflows.visual is implemented
# from ..workflows.visual import WorkflowVisualizer, VisualizationFormat


class StepStatus(str, Enum):
    """Status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep(BaseModel):
    """A single step in a workflow."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    action: str | None = None  # Prompt or action to execute
    handler: str | None = None  # Name of custom handler function
    depends_on: list[str] = Field(default_factory=list)
    condition: str | None = None  # Condition to evaluate
    parallel: bool = False
    retry_count: int = 0
    max_retries: int = 3
    timeout: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Runtime state
    status: StepStatus = StepStatus.PENDING
    result: Any | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration(self) -> float | None:
        """Get step duration in seconds."""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def can_run(self, completed_steps: list[str]) -> bool:
        """Check if this step can run based on dependencies."""
        return all(dep in completed_steps for dep in self.depends_on)


class Workflow(BaseModel):
    """A workflow definition."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    steps: list[WorkflowStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Runtime state
    status: StepStatus = StepStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    context: dict[str, Any] = Field(default_factory=dict)

    def add_step(
        self,
        name: str,
        action: str | None = None,
        handler: str | None = None,
        depends_on: list[str] | None = None,
        **kwargs,
    ) -> WorkflowStep:
        """Add a step to the workflow.

        Args:
            name: Step name
            action: Prompt or action to execute
            handler: Custom handler function name
            depends_on: List of step names this depends on
            **kwargs: Additional step configuration

        Returns:
            The created WorkflowStep
        """
        step = WorkflowStep(
            name=name,
            action=action,
            handler=handler,
            depends_on=depends_on or [],
            **kwargs,
        )
        self.steps.append(step)
        return step

    def get_step(self, name: str) -> WorkflowStep | None:
        """Get a step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_ready_steps(self) -> list[WorkflowStep]:
        """Get all steps that are ready to run."""
        completed = [s.name for s in self.steps if s.status == StepStatus.COMPLETED]
        ready = []

        for step in self.steps:
            if step.status == StepStatus.PENDING and step.can_run(completed):
                ready.append(step)

        return ready

    def validate(self) -> list[str]:
        """Validate the workflow configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        step_names = {step.name for step in self.steps}

        # Check for duplicate names
        if len(step_names) != len(self.steps):
            errors.append("Duplicate step names found")

        # Check dependencies
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_names:
                    errors.append(f"Step '{step.name}' depends on unknown step '{dep}'")

        # Check for circular dependencies
        for step in self.steps:
            if self._has_circular_dependency(step, step_names):
                errors.append(f"Circular dependency detected for step '{step.name}'")

        return errors

    def _has_circular_dependency(
        self, step: WorkflowStep, all_steps: set, visited: set | None = None
    ) -> bool:
        """Check if a step has circular dependencies."""
        if visited is None:
            visited = set()

        if step.name in visited:
            return True

        visited.add(step.name)

        for dep_name in step.depends_on:
            dep_step = self.get_step(dep_name)
            if dep_step and self._has_circular_dependency(
                dep_step, all_steps, visited.copy()
            ):
                return True

        return False


class WorkflowAgent(Agent):
    """An agent optimized for executing multi-step workflows.

    WorkflowAgent extends the base Agent to provide workflow execution
    capabilities including step dependencies, parallel execution,
    conditional logic, and error handling.

    Example:
        Basic workflow::

            agent = WorkflowAgent(name="DataProcessor")

            # Define workflow
            workflow = agent.create_workflow("data_pipeline")
            workflow.add_step("fetch", "Fetch data from the API")
            workflow.add_step("validate", "Validate the data format", depends_on=["fetch"])
            workflow.add_step("transform", "Transform data to new format", depends_on=["validate"])
            workflow.add_step("save", "Save to database", depends_on=["transform"])

            # Execute workflow
            result = await agent.execute_workflow(workflow)

            # Check results
            for step_name, step_result in result.step_results.items():
                print(f"{step_name}: {step_result.status}")
    """

    def __init__(
        self,
        name: str = "WorkflowAgent",
        instructions: str = "You are a workflow execution agent. Follow the steps precisely.",
        **kwargs,
    ):
        """Initialize WorkflowAgent.

        Args:
            name: Agent name
            instructions: System instructions
            **kwargs: Additional configuration
        """
        # Augment instructions for workflow execution
        workflow_instructions = (
            f"{instructions}\n\n"
            "When executing workflow steps:\n"
            "1. Follow the exact instructions for each step\n"
            "2. Use the context from previous steps when needed\n"
            "3. Provide clear, actionable output\n"
            "4. Report any issues or blockers immediately"
        )

        super().__init__(name=name, instructions=workflow_instructions, **kwargs)

        self.workflows: dict[str, Workflow] = {}
        self.handlers: dict[str, Callable] = {}
        self.running_workflows: dict[str, Workflow] = {}

    def create_workflow(self, name: str, description: str = "") -> Workflow:
        """Create a new workflow.

        Args:
            name: Workflow name
            description: Workflow description

        Returns:
            The created Workflow
        """
        workflow = Workflow(name=name, description=description)
        self.workflows[workflow.id] = workflow
        return workflow

    def register_handler(self, name: str, handler: Callable) -> None:
        """Register a custom step handler.

        Args:
            name: Handler name
            handler: Callable that takes (agent, step, context) and returns result
        """
        self.handlers[name] = handler

    async def execute_workflow(
        self,
        workflow: Workflow | str,
        context: dict[str, Any] | None = None,
        parallel: bool = True,
    ) -> WorkflowResult:
        """Execute a workflow.

        Args:
            workflow: Workflow instance or ID
            context: Initial workflow context
            parallel: Whether to run parallel steps concurrently

        Returns:
            WorkflowResult with execution details
        """
        # Get workflow instance
        if isinstance(workflow, str):
            workflow = self.workflows.get(workflow)
            if not workflow:
                raise AgentError(f"Workflow '{workflow}' not found")

        # Validate workflow
        errors = workflow.validate()
        if errors:
            raise AgentError(f"Workflow validation failed: {errors}")

        # Initialize execution
        workflow.status = StepStatus.RUNNING
        workflow.started_at = datetime.now()
        workflow.context = context or {}
        self.running_workflows[workflow.id] = workflow

        try:
            # Execute workflow
            if parallel:
                await self._execute_parallel(workflow)
            else:
                await self._execute_sequential(workflow)

            # Mark as completed
            workflow.status = StepStatus.COMPLETED
            workflow.completed_at = datetime.now()

        except Exception:
            workflow.status = StepStatus.FAILED
            workflow.completed_at = datetime.now()
            raise
        finally:
            del self.running_workflows[workflow.id]

        # Build result
        return WorkflowResult(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status=workflow.status,
            duration=self._calculate_duration(workflow),
            step_results={
                step.name: StepResult(
                    name=step.name,
                    status=step.status,
                    result=step.result,
                    error=step.error,
                    duration=step.duration,
                )
                for step in workflow.steps
            },
            context=workflow.context,
        )

    async def _execute_sequential(self, workflow: Workflow) -> None:
        """Execute workflow steps sequentially."""
        completed_steps = []

        while True:
            # Get next ready step
            ready_steps = workflow.get_ready_steps()
            if not ready_steps:
                break

            # Execute first ready step
            step = ready_steps[0]
            await self._execute_step(step, workflow)

            if step.status == StepStatus.COMPLETED:
                completed_steps.append(step.name)

    async def _execute_parallel(self, workflow: Workflow) -> None:
        """Execute workflow with parallel step support."""
        completed_steps = set()
        pending_tasks = {}

        while True:
            # Get ready steps
            ready_steps = workflow.get_ready_steps()

            # Start tasks for ready steps
            for step in ready_steps:
                if step.name not in pending_tasks:
                    task = asyncio.create_task(self._execute_step(step, workflow))
                    pending_tasks[step.name] = (step, task)

            # If no pending tasks, we're done
            if not pending_tasks:
                break

            # Wait for any task to complete
            done, pending = await asyncio.wait(
                [task for _, task in pending_tasks.values()],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Process completed tasks
            for task in done:
                # Find which step this task belongs to
                for step_name, (step, step_task) in list(pending_tasks.items()):
                    if step_task == task:
                        del pending_tasks[step_name]
                        if step.status == StepStatus.COMPLETED:
                            completed_steps.add(step_name)
                        break

    async def _execute_step(self, step: WorkflowStep, workflow: Workflow) -> None:
        """Execute a single workflow step."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()

        try:
            # Check condition if present
            if step.condition and not self._evaluate_condition(
                step.condition, workflow.context
            ):
                step.status = StepStatus.SKIPPED
                step.result = "Skipped due to condition"
                return

            # Execute with timeout if specified
            if step.timeout:
                result = await asyncio.wait_for(
                    self._run_step_action(step, workflow), timeout=step.timeout
                )
            else:
                result = await self._run_step_action(step, workflow)

            # Store result
            step.result = result
            step.status = StepStatus.COMPLETED

            # Update workflow context
            workflow.context[f"{step.name}_result"] = result

        except asyncio.TimeoutError:
            step.error = f"Step timed out after {step.timeout} seconds"
            step.status = StepStatus.FAILED

            # Retry if allowed
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.PENDING

        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED

            # Retry if allowed
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.PENDING

        finally:
            if step.status in [
                StepStatus.COMPLETED,
                StepStatus.FAILED,
                StepStatus.SKIPPED,
            ]:
                step.completed_at = datetime.now()

    async def _run_step_action(self, step: WorkflowStep, workflow: Workflow) -> Any:
        """Run the action for a step."""
        # Use custom handler if specified
        if step.handler and step.handler in self.handlers:
            handler = self.handlers[step.handler]
            if asyncio.iscoroutinefunction(handler):
                return await handler(self, step, workflow.context)
            else:
                return handler(self, step, workflow.context)

        # Use action prompt
        if step.action:
            # Build prompt with context
            prompt = f"Execute the following step: {step.action}"

            # Add relevant context
            if workflow.context:
                relevant_context = {
                    k: v
                    for k, v in workflow.context.items()
                    if any(dep in k for dep in step.depends_on)
                    or k in ["initial_input", "user_request"]
                }
                if relevant_context:
                    prompt += f"\n\nContext from previous steps:\n{relevant_context}"

            # Execute with agent
            response = await self.arun(prompt)
            return response.content

        # No action defined
        return f"Step '{step.name}' completed"

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a step condition.

        Simple evaluation - in production, use a safe expression evaluator.
        """
        try:
            # Very basic condition evaluation
            # In production, use a proper expression evaluator
            if "==" in condition:
                parts = condition.split("==")
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip().strip("'\"")
                    return str(context.get(left, "")) == right

            # Default to True if we can't evaluate
            return True

        except Exception:
            return True

    def _calculate_duration(self, workflow: Workflow) -> float:
        """Calculate total workflow duration."""
        if not workflow.started_at or not workflow.completed_at:
            return 0.0
        return (workflow.completed_at - workflow.started_at).total_seconds()

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get the current status of a running workflow."""
        workflow = self.running_workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status,
            "steps": {
                step.name: {"status": step.status, "duration": step.duration}
                for step in workflow.steps
            },
        }

    # Visual planning capabilities
    def visualize_workflow(
        self,
        workflow: Workflow | str,
        format: str = "mermaid",
        include_progress: bool = False,
    ) -> str:
        """Visualize a workflow.

        Args:
            workflow: Workflow instance or ID
            format: Visualization format (mermaid, ascii, json, html)
            include_progress: Include execution progress

        Returns:
            Visualization string
        """
        # Get workflow instance
        if isinstance(workflow, str):
            workflow = self.workflows.get(workflow)
            if not workflow:
                raise AgentError(f"Workflow '{workflow}' not found")

        # TODO: Implement when WorkflowVisualizer is available
        # visualizer = WorkflowVisualizer()
        # return visualizer.visualize(
        #     workflow,
        #     VisualizationFormat(format),
        #     include_progress
        # )

        if format == "ascii":
            # Generate ASCII art visualization
            lines = [f"Workflow: {workflow.name}"]
            lines.append("")

            # Create a map of step dependencies
            dep_map = {}
            for step in workflow.steps:
                dep_map[step.name] = step.depends_on

            # Draw each step with connections
            for i, step in enumerate(workflow.steps):
                # Draw the step box
                lines.append(f"[{step.name}]")

                # Draw connections to next steps that depend on this one
                if i < len(workflow.steps) - 1:
                    # Check if any subsequent steps depend on this one
                    has_dependent = False
                    for j in range(i + 1, len(workflow.steps)):
                        next_step = workflow.steps[j]
                        if step.name in next_step.depends_on:
                            has_dependent = True
                            break

                    if has_dependent:
                        lines.append("|")
                        lines.append("v")

            return "\n".join(lines)

        elif format == "json":
            # Return JSON representation
            import json

            data = {
                "name": workflow.name,
                "description": workflow.description,
                "steps": [
                    {
                        "name": step.name,
                        "action": step.action,
                        "depends_on": step.depends_on,
                        "status": step.status.value if include_progress else None,
                    }
                    for step in workflow.steps
                ],
            }
            return json.dumps(data, indent=2)

        elif format == "html":
            # Return HTML with Mermaid diagram
            mermaid_code = self._generate_mermaid_code(workflow)
            return f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
</head>
<body>
    <h1>{workflow.name}</h1>
    <div class="mermaid">
    {mermaid_code}
    </div>
</body>
</html>"""

        else:
            # Default format (mermaid or simple text)
            lines = [f"Workflow: {workflow.name}"]
            for step in workflow.steps:
                deps = (
                    f" (depends on: {', '.join(step.depends_on)})"
                    if step.depends_on
                    else ""
                )
                lines.append(f"  - {step.name}{deps}")
            return "\n".join(lines)

    def _generate_mermaid_code(self, workflow: Workflow) -> str:
        """Generate Mermaid diagram code for workflow."""
        lines = ["graph TD"]

        # Add nodes
        for step in workflow.steps:
            lines.append(f"    {step.name}[{step.name}]")

        # Add edges
        for step in workflow.steps:
            for dep in step.depends_on:
                lines.append(f"    {dep} --> {step.name}")

        return "\n".join(lines)

    async def plan_workflow_visually(
        self, goal: str, constraints: dict[str, Any] | None = None
    ) -> Workflow:
        """Use visual planning to create a workflow.

        Args:
            goal: The goal to achieve
            constraints: Optional constraints (time, resources, etc.)

        Returns:
            Planned workflow
        """
        # Use agent capabilities to plan workflow
        planning_prompt = f"""
        Create a workflow plan to achieve: {goal}
        
        Constraints: {constraints or 'None'}
        
        Break down the goal into clear, actionable steps.
        For each step, specify:
        1. Step name (short identifier)
        2. Description of what to do
        3. Dependencies on other steps
        4. Whether it can run in parallel with other steps
        
        Format your response as a structured plan.
        """

        response = await self.arun(planning_prompt)

        # Parse response and create workflow
        workflow = self.create_workflow(
            name=f"workflow_for_{goal[:30]}", description=f"Workflow to achieve: {goal}"
        )

        # In a real implementation, we'd parse the response
        # For now, create a simple example
        workflow.add_step("analyze", f"Analyze requirements for: {goal}")
        workflow.add_step(
            "plan", "Create detailed execution plan", depends_on=["analyze"]
        )
        workflow.add_step("execute", "Execute the plan", depends_on=["plan"])
        workflow.add_step("verify", "Verify goal achievement", depends_on=["execute"])

        return workflow

    def modify_workflow_dynamically(
        self, workflow_id: str, modifications: dict[str, Any]
    ) -> None:
        """Modify a workflow during execution.

        Args:
            workflow_id: Workflow ID
            modifications: Dict with 'add_steps', 'remove_steps', 'modify_steps'
        """
        workflow = self.running_workflows.get(workflow_id)
        if not workflow:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                raise AgentError(f"Workflow '{workflow_id}' not found")

        # Add new steps
        for step_def in modifications.get("add_steps", []):
            workflow.add_step(**step_def)

        # Remove steps (only if not started)
        for step_name in modifications.get("remove_steps", []):
            step = workflow.get_step(step_name)
            if step and step.status == StepStatus.PENDING:
                workflow.steps.remove(step)

        # Modify existing steps
        for step_name, changes in modifications.get("modify_steps", {}).items():
            step = workflow.get_step(step_name)
            if step and step.status == StepStatus.PENDING:
                for key, value in changes.items():
                    if hasattr(step, key):
                        setattr(step, key, value)

    # Checkpoint and resume capabilities
    async def save_checkpoint(
        self, workflow_id: str, checkpoint_dir: str = "./checkpoints"
    ) -> str:
        """Save workflow checkpoint.

        Args:
            workflow_id: Workflow ID
            checkpoint_dir: Directory to save checkpoints

        Returns:
            Checkpoint file path
        """
        workflow = self.running_workflows.get(workflow_id)
        if not workflow:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                raise AgentError(f"Workflow '{workflow_id}' not found")

        # Create checkpoint directory
        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

        # Prepare checkpoint data
        checkpoint = {
            "workflow": workflow.dict(),
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.name,
        }

        # Save checkpoint
        checkpoint_file = os.path.join(
            checkpoint_dir,
            f"{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint, f, indent=2, default=str)

        return checkpoint_file

    async def load_checkpoint(self, checkpoint_file: str) -> Workflow:
        """Load workflow from checkpoint.

        Args:
            checkpoint_file: Path to checkpoint file

        Returns:
            Loaded workflow
        """
        if not os.path.exists(checkpoint_file):
            raise AgentError(f"Checkpoint file not found: {checkpoint_file}")

        with open(checkpoint_file) as f:
            checkpoint = json.load(f)

        # Recreate workflow
        workflow_data = checkpoint["workflow"]
        workflow = Workflow(**workflow_data)

        # Convert datetime strings back to datetime objects
        for step in workflow.steps:
            if step.started_at:
                if isinstance(step.started_at, str):
                    step.started_at = datetime.fromisoformat(step.started_at)
            if step.completed_at:
                if isinstance(step.completed_at, str):
                    step.completed_at = datetime.fromisoformat(step.completed_at)

        if workflow.started_at:
            if isinstance(workflow.started_at, str):
                workflow.started_at = datetime.fromisoformat(workflow.started_at)
        if workflow.completed_at:
            if isinstance(workflow.completed_at, str):
                workflow.completed_at = datetime.fromisoformat(workflow.completed_at)

        # Register workflow
        self.workflows[workflow.id] = workflow

        return workflow

    async def resume_workflow(
        self, workflow: Workflow | str, parallel: bool = True
    ) -> WorkflowResult:
        """Resume workflow execution from checkpoint.

        Args:
            workflow: Workflow instance or ID
            parallel: Whether to run parallel steps concurrently

        Returns:
            WorkflowResult
        """
        # Get workflow instance
        if isinstance(workflow, str):
            workflow = self.workflows.get(workflow)
            if not workflow:
                raise AgentError(f"Workflow '{workflow}' not found")

        # Reset failed steps to pending if retry allowed
        for step in workflow.steps:
            if step.status == StepStatus.FAILED and step.retry_count < step.max_retries:
                step.status = StepStatus.PENDING
                step.error = None

        # Resume execution
        return await self.execute_workflow(workflow, workflow.context, parallel)

    # Progress streaming
    async def stream_workflow_progress(
        self,
        workflow_id: str,
        callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Stream workflow progress updates.

        Args:
            workflow_id: Workflow ID
            callback: Optional callback for progress updates
        """
        workflow = self.running_workflows.get(workflow_id)
        if not workflow:
            raise AgentError(f"Workflow '{workflow_id}' not running")

        last_status = {}

        while workflow.status == StepStatus.RUNNING:
            current_status = self.get_workflow_status(workflow_id)

            # Check for changes
            if current_status != last_status:
                # Emit progress update
                progress = {
                    "workflow_id": workflow_id,
                    "workflow_name": workflow.name,
                    "overall_status": workflow.status,
                    "steps_total": len(workflow.steps),
                    "steps_completed": sum(
                        1
                        for s in workflow.steps
                        if s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
                    ),
                    "steps_failed": sum(
                        1 for s in workflow.steps if s.status == StepStatus.FAILED
                    ),
                    "current_steps": [
                        s.name for s in workflow.steps if s.status == StepStatus.RUNNING
                    ],
                    "timestamp": datetime.now().isoformat(),
                }

                # Call callback if provided
                if callback:
                    callback(progress)

                # Also yield for async iteration
                yield progress

                last_status = current_status

            # Small delay to avoid busy waiting
            await asyncio.sleep(0.5)

        # Final status
        final_progress = {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "overall_status": workflow.status,
            "completed": True,
            "duration": self._calculate_duration(workflow),
            "timestamp": datetime.now().isoformat(),
        }

        if callback:
            callback(final_progress)

        yield final_progress


class StepResult(BaseModel):
    """Result from a workflow step execution."""

    name: str
    status: StepStatus
    result: Any | None = None
    error: str | None = None
    duration: float | None = None


class WorkflowResult(BaseModel):
    """Result from workflow execution."""

    workflow_id: str
    workflow_name: str
    status: StepStatus
    duration: float
    step_results: dict[str, StepResult]
    context: dict[str, Any] = Field(default_factory=dict)

    @property
    def successful(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == StepStatus.COMPLETED

    @property
    def failed_steps(self) -> list[str]:
        """Get list of failed step names."""
        return [
            name
            for name, result in self.step_results.items()
            if result.status == StepStatus.FAILED
        ]

    def get_step_result(self, step_name: str) -> Any | None:
        """Get the result of a specific step."""
        step = self.step_results.get(step_name)
        return step.result if step else None

    def format_summary(self) -> str:
        """Format a summary of the workflow execution."""
        lines = [
            f"Workflow: {self.workflow_name}",
            f"Status: {self.status}",
            f"Duration: {self.duration:.2f}s",
            "\nStep Results:",
        ]

        for name, result in self.step_results.items():
            status_emoji = {
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️",
                StepStatus.PENDING: "⏸️",
                StepStatus.RUNNING: "🔄",
            }.get(result.status, "❓")

            line = f"  {status_emoji} {name}: {result.status}"
            if result.duration:
                line += f" ({result.duration:.2f}s)"
            if result.error:
                line += f" - Error: {result.error}"

            lines.append(line)

        return "\n".join(lines)
