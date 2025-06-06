"""WorkflowAgent implementation for AgentiCraft.

The WorkflowAgent provides capabilities for executing multi-step workflows,
with support for sequential execution, conditional logic, parallel tasks,
and error handling.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from ..core.agent import Agent, AgentResponse
from ..core.exceptions import AgentError


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
    action: Optional[str] = None  # Prompt or action to execute
    handler: Optional[str] = None  # Name of custom handler function
    depends_on: List[str] = Field(default_factory=list)
    condition: Optional[str] = None  # Condition to evaluate
    parallel: bool = False
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Runtime state
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get step duration in seconds."""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
    
    def can_run(self, completed_steps: List[str]) -> bool:
        """Check if this step can run based on dependencies."""
        return all(dep in completed_steps for dep in self.depends_on)


class Workflow(BaseModel):
    """A workflow definition."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    steps: List[WorkflowStep] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Runtime state
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    
    def add_step(
        self,
        name: str,
        action: Optional[str] = None,
        handler: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        **kwargs
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
            **kwargs
        )
        self.steps.append(step)
        return step
    
    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get all steps that are ready to run."""
        completed = [s.name for s in self.steps if s.status == StepStatus.COMPLETED]
        ready = []
        
        for step in self.steps:
            if step.status == StepStatus.PENDING and step.can_run(completed):
                ready.append(step)
        
        return ready
    
    def validate(self) -> List[str]:
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
        self, 
        step: WorkflowStep, 
        all_steps: set,
        visited: Optional[set] = None
    ) -> bool:
        """Check if a step has circular dependencies."""
        if visited is None:
            visited = set()
            
        if step.name in visited:
            return True
            
        visited.add(step.name)
        
        for dep_name in step.depends_on:
            dep_step = self.get_step(dep_name)
            if dep_step and self._has_circular_dependency(dep_step, all_steps, visited.copy()):
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
        **kwargs
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
        
        super().__init__(
            name=name,
            instructions=workflow_instructions,
            **kwargs
        )
        
        self.workflows: Dict[str, Workflow] = {}
        self.handlers: Dict[str, Callable] = {}
        self.running_workflows: Dict[str, Workflow] = {}
    
    def create_workflow(
        self,
        name: str,
        description: str = ""
    ) -> Workflow:
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
    
    def register_handler(
        self,
        name: str,
        handler: Callable
    ) -> None:
        """Register a custom step handler.
        
        Args:
            name: Handler name
            handler: Callable that takes (agent, step, context) and returns result
        """
        self.handlers[name] = handler
    
    async def execute_workflow(
        self,
        workflow: Union[Workflow, str],
        context: Optional[Dict[str, Any]] = None,
        parallel: bool = True
    ) -> 'WorkflowResult':
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
            
        except Exception as e:
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
                    duration=step.duration
                )
                for step in workflow.steps
            },
            context=workflow.context
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
                return_when=asyncio.FIRST_COMPLETED
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
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: Workflow
    ) -> None:
        """Execute a single workflow step."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        try:
            # Check condition if present
            if step.condition and not self._evaluate_condition(step.condition, workflow.context):
                step.status = StepStatus.SKIPPED
                step.result = "Skipped due to condition"
                return
            
            # Execute with timeout if specified
            if step.timeout:
                result = await asyncio.wait_for(
                    self._run_step_action(step, workflow),
                    timeout=step.timeout
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
            if step.status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
                step.completed_at = datetime.now()
    
    async def _run_step_action(
        self,
        step: WorkflowStep,
        workflow: Workflow
    ) -> Any:
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
                    k: v for k, v in workflow.context.items()
                    if any(dep in k for dep in step.depends_on) or k in ['initial_input', 'user_request']
                }
                if relevant_context:
                    prompt += f"\n\nContext from previous steps:\n{relevant_context}"
            
            # Execute with agent
            response = await self.arun(prompt)
            return response.content
        
        # No action defined
        return f"Step '{step.name}' completed"
    
    def _evaluate_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
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
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a running workflow."""
        workflow = self.running_workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status,
            "steps": {
                step.name: {
                    "status": step.status,
                    "duration": step.duration
                }
                for step in workflow.steps
            }
        }


class StepResult(BaseModel):
    """Result from a workflow step execution."""
    
    name: str
    status: StepStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: Optional[float] = None


class WorkflowResult(BaseModel):
    """Result from workflow execution."""
    
    workflow_id: str
    workflow_name: str
    status: StepStatus
    duration: float
    step_results: Dict[str, StepResult]
    context: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def successful(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == StepStatus.COMPLETED
    
    @property
    def failed_steps(self) -> List[str]:
        """Get list of failed step names."""
        return [
            name for name, result in self.step_results.items()
            if result.status == StepStatus.FAILED
        ]
    
    def get_step_result(self, step_name: str) -> Optional[Any]:
        """Get the result of a specific step."""
        step = self.step_results.get(step_name)
        return step.result if step else None
    
    def format_summary(self) -> str:
        """Format a summary of the workflow execution."""
        lines = [
            f"Workflow: {self.workflow_name}",
            f"Status: {self.status}",
            f"Duration: {self.duration:.2f}s",
            "\nStep Results:"
        ]
        
        for name, result in self.step_results.items():
            status_emoji = {
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️",
                StepStatus.PENDING: "⏸️",
                StepStatus.RUNNING: "🔄"
            }.get(result.status, "❓")
            
            line = f"  {status_emoji} {name}: {result.status}"
            if result.duration:
                line += f" ({result.duration:.2f}s)"
            if result.error:
                line += f" - Error: {result.error}"
                
            lines.append(line)
        
        return "\n".join(lines)
