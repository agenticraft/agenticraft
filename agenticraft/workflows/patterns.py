"""Workflow patterns for common execution scenarios.

This module provides pre-built workflow patterns for:
- Parallel execution
- Conditional branching
- Loop/retry patterns
- Map-reduce operations
"""

import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..core.workflow import Step, Workflow


class AsyncFunction:
    """Wrapper to make functions work with workflow steps."""

    def __init__(self, func):
        self.func = func
        self.__name__ = getattr(func, "__name__", "async_function")

    async def arun(self, **kwargs):
        """Async run method required by workflow steps."""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)


class WorkflowPatterns:
    """Collection of common workflow patterns."""

    @staticmethod
    def parallel_tasks(
        name: str, tasks: list[dict[str, Any]], max_concurrent: int | None = None
    ) -> Workflow:
        """Create a workflow for parallel task execution.

        Args:
            name: Workflow name
            tasks: List of task definitions with 'name', 'agent'/'tool', and optional 'inputs'
            max_concurrent: Maximum concurrent executions (None for unlimited)

        Returns:
            Configured workflow

        Example:
            workflow = WorkflowPatterns.parallel_tasks(
                "data_processing",
                tasks=[
                    {"name": "process_csv", "tool": csv_processor, "inputs": {"file": "data.csv"}},
                    {"name": "process_json", "tool": json_processor, "inputs": {"file": "data.json"}},
                    {"name": "process_xml", "tool": xml_processor, "inputs": {"file": "data.xml"}}
                ]
            )
        """
        workflow = Workflow(
            name=name, description=f"Parallel execution of {len(tasks)} tasks"
        )

        # Add a coordinator step if we need to limit concurrency
        if max_concurrent and max_concurrent < len(tasks):
            # Create batches
            batches = [
                tasks[i : i + max_concurrent]
                for i in range(0, len(tasks), max_concurrent)
            ]

            for batch_idx, batch in enumerate(batches):
                batch_deps = []

                for task in batch:
                    step_name = f"{task['name']}_batch{batch_idx}"

                    # Add dependencies on previous batch
                    deps = []
                    if batch_idx > 0:
                        # Depend on all tasks from previous batch
                        prev_batch = batches[batch_idx - 1]
                        deps = [f"{t['name']}_batch{batch_idx-1}" for t in prev_batch]

                    workflow.add_step(
                        Step(
                            name=step_name,
                            agent=task.get("agent"),
                            tool=task.get("tool"),
                            inputs=task.get("inputs", {}),
                            depends_on=deps,
                        )
                    )
                    batch_deps.append(step_name)

            # Add aggregator step
            all_steps = [
                f"{task['name']}_batch{i}"
                for i, batch in enumerate(batches)
                for task in batch
            ]
            workflow.add_step(
                Step(
                    name="aggregate_results",
                    tool=AsyncFunction(_aggregate_results),
                    depends_on=all_steps,
                )
            )
        else:
            # Unlimited parallelism
            for task in tasks:
                workflow.add_step(
                    Step(
                        name=task["name"],
                        agent=task.get("agent"),
                        tool=task.get("tool"),
                        inputs=task.get("inputs", {}),
                        depends_on=[],  # No dependencies = parallel execution
                    )
                )

            # Add aggregator
            workflow.add_step(
                Step(
                    name="aggregate_results",
                    tool=AsyncFunction(_aggregate_results),
                    depends_on=[task["name"] for task in tasks],
                )
            )

        return workflow

    @staticmethod
    def conditional_branch(
        name: str,
        condition_step: dict[str, Any],
        if_true_steps: list[dict[str, Any]],
        if_false_steps: list[dict[str, Any]],
        merge_step: dict[str, Any] | None = None,
    ) -> Workflow:
        """Create a conditional branching workflow.

        Args:
            name: Workflow name
            condition_step: Step that evaluates the condition
            if_true_steps: Steps to execute if condition is true
            if_false_steps: Steps to execute if condition is false
            merge_step: Optional step to merge branches

        Returns:
            Configured workflow

        Example:
            workflow = WorkflowPatterns.conditional_branch(
                "quality_check",
                condition_step={"name": "check_quality", "action": "Check if quality > 90%"},
                if_true_steps=[
                    {"name": "approve", "action": "Approve the item"},
                    {"name": "ship", "action": "Ship to customer"}
                ],
                if_false_steps=[
                    {"name": "reject", "action": "Mark as rejected"},
                    {"name": "notify_qa", "action": "Notify QA team"}
                ],
                merge_step={"name": "log_result", "action": "Log the decision"}
            )
        """
        workflow = Workflow(name=name, description=f"Conditional workflow: {name}")

        # Add condition step
        workflow.add_step(
            Step(
                name=condition_step["name"],
                tool=condition_step.get("tool")
                or AsyncFunction(lambda **kwargs: {"result": True})
                or AsyncFunction(lambda **kwargs: {"result": True}),
                inputs=condition_step.get("inputs", {}),
            )
        )

        # Add true branch steps
        true_branch_names = []
        for idx, step in enumerate(if_true_steps):
            step_name = step["name"]
            true_branch_names.append(step_name)

            # First step depends on condition, others depend on previous
            deps = (
                [condition_step["name"]]
                if idx == 0
                else [if_true_steps[idx - 1]["name"]]
            )

            workflow.add_step(
                Step(
                    name=step_name,
                    tool=step.get("tool")
                    or AsyncFunction(lambda **kwargs: {"result": "done"})
                    or AsyncFunction(lambda **kwargs: {"result": "done"}),
                    inputs=step.get("inputs", {}),
                    depends_on=deps,
                )
            )

        # Add false branch steps
        false_branch_names = []
        for idx, step in enumerate(if_false_steps):
            step_name = step["name"]
            false_branch_names.append(step_name)

            # First step depends on condition, others depend on previous
            deps = (
                [condition_step["name"]]
                if idx == 0
                else [if_false_steps[idx - 1]["name"]]
            )

            workflow.add_step(
                Step(
                    name=step_name,
                    tool=step.get("tool")
                    or AsyncFunction(lambda **kwargs: {"result": "done"})
                    or AsyncFunction(lambda **kwargs: {"result": "done"}),
                    inputs=step.get("inputs", {}),
                    depends_on=deps,
                )
            )

        # Add merge step if provided
        if merge_step:
            # Merge depends on the last step of both branches
            deps = []
            if true_branch_names:
                deps.append(true_branch_names[-1])
            if false_branch_names:
                deps.append(false_branch_names[-1])

            workflow.add_step(
                Step(
                    name=merge_step["name"],
                    tool=merge_step.get("tool")
                    or AsyncFunction(lambda **kwargs: {"merged": True})
                    or AsyncFunction(lambda **kwargs: {"merged": True}),
                    inputs=merge_step.get("inputs", {}),
                    depends_on=deps,
                )
            )

        return workflow

    @staticmethod
    def retry_loop(
        name: str,
        task: dict[str, Any],
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
        success_condition: Callable[[Any], bool] | None = None,
    ) -> Workflow:
        """Create a retry loop workflow.

        Args:
            name: Workflow name
            task: Task definition with 'name', 'agent'/'tool', and optional 'inputs'
            max_attempts: Maximum retry attempts
            backoff_seconds: Initial backoff time (doubles each retry)
            success_condition: Optional function to check if result is successful

        Returns:
            Configured workflow

        Example:
            workflow = WorkflowPatterns.retry_loop(
                "api_call_with_retry",
                task={"name": "call_api", "tool": api_client, "inputs": {"endpoint": "/data"}},
                max_attempts=5,
                backoff_seconds=2.0,
                success_condition=lambda result: result.get("status") == 200
            )
        """
        workflow = Workflow(
            name=name,
            description=f"Retry loop for {task['name']} (max {max_attempts} attempts)",
        )

        # Main task with retry configuration
        main_step = Step(
            name=task["name"],
            agent=task.get("agent"),
            tool=task.get("tool"),
            inputs=task.get("inputs", {}),
            retry_count=max_attempts - 1,  # retry_count is additional attempts
            depends_on=[],
        )

        # If we have a custom success condition, wrap the tool/agent
        if success_condition:
            original_executor = main_step.tool or main_step.agent
            wrapped = _create_conditional_wrapper(original_executor, success_condition)
            # Wrap with AsyncFunction to ensure it has arun method
            main_step.tool = AsyncFunction(wrapped)
            main_step.agent = None

        workflow.add_step(main_step)

        # Add a verification step
        workflow.add_step(
            Step(
                name=f"verify_{task['name']}",
                tool=AsyncFunction(_verify_retry_result),
                inputs={"max_attempts": max_attempts},
                depends_on=[task["name"]],
            )
        )

        return workflow

    @staticmethod
    def map_reduce(
        name: str,
        data_source: dict[str, Any],
        mapper: dict[str, Any],
        reducer: dict[str, Any],
        chunk_size: int | None = None,
    ) -> Workflow:
        """Create a map-reduce workflow pattern.

        Args:
            name: Workflow name
            data_source: Step to load/prepare data
            mapper: Step to map over data chunks
            reducer: Step to reduce results
            chunk_size: Optional size for data chunks

        Returns:
            Configured workflow

        Example:
            workflow = WorkflowPatterns.map_reduce(
                "analyze_logs",
                data_source={"name": "load_logs", "tool": log_loader},
                mapper={"name": "analyze_chunk", "tool": log_analyzer},
                reducer={"name": "aggregate_stats", "tool": stats_aggregator},
                chunk_size=1000
            )
        """
        workflow = Workflow(name=name, description=f"Map-reduce pattern: {name}")

        # Add data source step
        workflow.add_step(
            Step(
                name=data_source["name"],
                agent=data_source.get("agent"),
                tool=data_source.get("tool"),
                inputs=data_source.get("inputs", {}),
            )
        )

        # Add splitter step
        workflow.add_step(
            Step(
                name="split_data",
                tool=AsyncFunction(_create_data_splitter(chunk_size)),
                depends_on=[data_source["name"]],
            )
        )

        # Add mapper coordinator
        workflow.add_step(
            Step(
                name="map_coordinator",
                tool=AsyncFunction(_create_map_coordinator(mapper)),
                depends_on=["split_data"],
            )
        )

        # Add reducer step
        workflow.add_step(
            Step(
                name=reducer["name"],
                agent=reducer.get("agent"),
                tool=reducer.get("tool"),
                inputs=reducer.get("inputs", {}),
                depends_on=["map_coordinator"],
            )
        )

        return workflow

    @staticmethod
    def pipeline(
        name: str,
        steps: list[dict[str, Any]],
        error_handler: dict[str, Any] | None = None,
    ) -> Workflow:
        """Create a sequential pipeline workflow.

        Args:
            name: Workflow name
            steps: List of steps to execute in sequence
            error_handler: Optional error handling step

        Returns:
            Configured workflow

        Example:
            workflow = WorkflowPatterns.pipeline(
                "etl_pipeline",
                steps=[
                    {"name": "extract", "tool": data_extractor},
                    {"name": "transform", "tool": data_transformer},
                    {"name": "validate", "tool": data_validator},
                    {"name": "load", "tool": data_loader}
                ],
                error_handler={"name": "handle_error", "tool": error_handler}
            )
        """
        workflow = Workflow(name=name, description=f"Sequential pipeline: {name}")

        # Add steps in sequence
        for idx, step_def in enumerate(steps):
            deps = [] if idx == 0 else [steps[idx - 1]["name"]]

            workflow.add_step(
                Step(
                    name=step_def["name"],
                    agent=step_def.get("agent"),
                    tool=step_def.get("tool"),
                    inputs=step_def.get("inputs", {}),
                    depends_on=deps,
                    retry_count=step_def.get("retry_count", 0),
                )
            )

        # Add error handler if provided
        if error_handler:
            # Error handler depends on all steps (runs if any fail)
            workflow.add_step(
                Step(
                    name=error_handler["name"],
                    agent=error_handler.get("agent"),
                    tool=error_handler.get("tool"),
                    inputs=error_handler.get("inputs", {}),
                    depends_on=[s["name"] for s in steps],
                )
            )

        return workflow


# Helper functions for patterns


async def _aggregate_results(**kwargs) -> dict[str, Any]:
    """Aggregate results from parallel tasks."""
    results = {}
    errors = []

    for key, value in kwargs.items():
        if isinstance(value, Exception):
            errors.append({"task": key, "error": str(value)})
        else:
            results[key] = value

    return {
        "aggregated_at": datetime.now().isoformat(),
        "results": results,
        "errors": errors,
        "success_count": len(results),
        "error_count": len(errors),
    }


async def _verify_retry_result(max_attempts: int, **kwargs) -> dict[str, Any]:
    """Verify retry loop results."""
    # Get the task result from kwargs
    task_result = next(iter(kwargs.values())) if kwargs else None

    return {
        "verified": task_result is not None,
        "max_attempts": max_attempts,
        "result": task_result,
    }


def _create_conditional_wrapper(
    executor: Callable | Any, condition: Callable[[Any], bool]
) -> Callable:
    """Create a wrapper that checks success condition."""

    async def wrapper(**kwargs):
        # Handle different types of executors
        if asyncio.iscoroutinefunction(executor):
            result = await executor(**kwargs)
        elif hasattr(executor, "arun"):
            # Handle tools with arun method
            result = await executor.arun(**kwargs)
        elif callable(executor):
            # Handle regular callables
            result = executor(**kwargs)
            # If result is a coroutine, await it
            if asyncio.iscoroutine(result):
                result = await result
        else:
            raise TypeError(f"Executor {executor} is not callable")

        if not condition(result):
            raise Exception(f"Success condition not met: {result}")

        return result

    return wrapper


def _create_data_splitter(chunk_size: int | None) -> Callable:
    """Create a data splitter function."""

    async def splitter(**kwargs) -> dict[str, Any]:
        # Get data from previous step
        data = next(iter(kwargs.values())) if kwargs else []

        if not chunk_size:
            # Auto-determine chunk size
            total_size = len(data) if hasattr(data, "__len__") else 100
            optimal_chunks = min(10, total_size)  # Max 10 chunks
            actual_chunk_size = max(1, total_size // optimal_chunks)
        else:
            actual_chunk_size = chunk_size

        chunks = []
        if hasattr(data, "__getitem__"):
            # List-like data
            for i in range(0, len(data), actual_chunk_size):
                chunks.append(data[i : i + actual_chunk_size])
        else:
            # Convert to list if needed
            data_list = list(data)
            for i in range(0, len(data_list), actual_chunk_size):
                chunks.append(data_list[i : i + actual_chunk_size])

        return {
            "chunks": chunks,
            "chunk_count": len(chunks),
            "chunk_size": actual_chunk_size,
        }

    return splitter


def _create_map_coordinator(mapper: dict[str, Any]) -> Callable:
    """Create a map coordinator function."""

    async def coordinator(split_data: dict[str, Any], **kwargs) -> list[Any]:
        chunks = split_data.get("chunks", [])
        executor = mapper.get("tool") or mapper.get("agent")

        if not executor:
            raise ValueError("Mapper must have either 'tool' or 'agent'")

        # Process chunks in parallel
        tasks = []
        for chunk in chunks:
            if asyncio.iscoroutinefunction(executor):
                task = executor(data=chunk, **mapper.get("inputs", {}))
            else:
                task = asyncio.create_task(
                    asyncio.to_thread(executor, data=chunk, **mapper.get("inputs", {}))
                )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful_results = [r for r in results if not isinstance(r, Exception)]

        return successful_results

    return coordinator
