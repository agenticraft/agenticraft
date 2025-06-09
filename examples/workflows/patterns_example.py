#!/usr/bin/env python3
"""Workflow patterns example.

This example demonstrates common workflow patterns:
- Parallel execution
- Conditional branching
- Retry loops
- Map-reduce operations
"""

import asyncio
from datetime import datetime
from typing import Any

from agenticraft import tool
from agenticraft.workflows import WorkflowPatterns, visualize_workflow


# Example tools for demonstration
@tool
async def fetch_data(source: str) -> dict[str, Any]:
    """Fetch data from a source."""
    await asyncio.sleep(0.5)  # Simulate API call
    return {"source": source, "records": 100, "status": "success"}


@tool
async def process_batch(data: list[Any]) -> dict[str, Any]:
    """Process a batch of data."""
    await asyncio.sleep(0.3)  # Simulate processing
    return {
        "processed": len(data),
        "results": [f"processed_{i}" for i in range(len(data))],
    }


@tool
async def quality_check(data: dict[str, Any]) -> dict[str, Any]:
    """Check data quality."""
    await asyncio.sleep(0.2)
    quality_score = 0.85  # Simulated score
    return {
        "quality_score": quality_score,
        "passed": quality_score > 0.8,
        "issues": [] if quality_score > 0.8 else ["Low quality detected"],
    }


@tool
async def send_notification(message: str, channel: str) -> dict[str, Any]:
    """Send notification."""
    await asyncio.sleep(0.1)
    return {
        "sent": True,
        "channel": channel,
        "message": message,
        "timestamp": "2024-01-15T10:30:00",
    }


async def main():
    """Run workflow pattern examples."""
    print("🔄 AgentiCraft Workflow Patterns Example")
    print("=" * 50)

    # 1. Parallel Tasks Pattern
    print("\n1️⃣ Parallel Tasks Pattern")
    print("-" * 40)

    parallel_workflow = WorkflowPatterns.parallel_tasks(
        name="data_ingestion",
        tasks=[
            {"name": "fetch_api", "tool": fetch_data, "inputs": {"source": "api"}},
            {"name": "fetch_db", "tool": fetch_data, "inputs": {"source": "database"}},
            {"name": "fetch_file", "tool": fetch_data, "inputs": {"source": "file"}},
        ],
        max_concurrent=2,  # Limit to 2 concurrent tasks
    )

    print("Visualization:")
    print(visualize_workflow(parallel_workflow, format="ascii"))

    # Execute workflow
    print("\nExecuting parallel workflow...")
    result = await parallel_workflow.run()
    print(f"✅ Completed in {result.completed_at - result.started_at}")

    # 2. Conditional Branch Pattern
    print("\n2️⃣ Conditional Branch Pattern")
    print("-" * 40)

    conditional_workflow = WorkflowPatterns.conditional_branch(
        name="quality_assurance",
        condition_step={"name": "check_quality", "tool": quality_check},
        if_true_steps=[
            {
                "name": "approve",
                "tool": lambda **kwargs: {
                    "approved": True,
                    "message": "Quality passed",
                },
            },
            {
                "name": "deploy",
                "tool": lambda **kwargs: {"deployed": True, "version": "1.0"},
            },
        ],
        if_false_steps=[
            {
                "name": "flag_issues",
                "tool": lambda **kwargs: {"flagged": True, "issues": ["Low quality"]},
            },
            {
                "name": "notify_team",
                "tool": send_notification,
                "inputs": {"message": "QA Alert", "channel": "qa-team"},
            },
        ],
        merge_step={
            "name": "log_outcome",
            "tool": lambda **kwargs: {
                "logged": True,
                "timestamp": datetime.now().isoformat(),
            },
        },
    )

    print("Visualization:")
    print(visualize_workflow(conditional_workflow, format="ascii"))

    # 3. Retry Loop Pattern
    print("\n3️⃣ Retry Loop Pattern")
    print("-" * 40)

    # Simulate an unreliable API with a closure to track attempts
    def create_unreliable_api():
        attempt_count = 0

        @tool
        async def unreliable_api(endpoint: str) -> dict[str, Any]:
            """Simulate unreliable API that fails sometimes."""
            nonlocal attempt_count
            attempt_count += 1

            # Fail first 2 attempts
            if attempt_count < 3:
                raise Exception(f"API timeout (attempt {attempt_count})")

            return {"status": 200, "data": "Success after retries!"}

        return unreliable_api

    unreliable_api = create_unreliable_api()

    retry_workflow = WorkflowPatterns.retry_loop(
        name="api_retry",
        task={
            "name": "call_api",
            "tool": unreliable_api,
            "inputs": {"endpoint": "/data"},
        },
        max_attempts=5,
        backoff_seconds=1.0,
        success_condition=lambda result: result.get("status") == 200,
    )

    print("Visualization:")
    print(visualize_workflow(retry_workflow, format="ascii"))

    print("\nExecuting retry workflow...")
    result = await retry_workflow.run()
    if "call_api" in result.steps and result.steps["call_api"].success:
        print(f"✅ Succeeded after retries: {result.steps['call_api'].output}")
    else:
        print("❌ API call failed after all retries")

    # 4. Map-Reduce Pattern
    print("\n4️⃣ Map-Reduce Pattern")
    print("-" * 40)

    # Create mock data loader
    @tool
    async def load_dataset() -> list[list[int]]:
        """Load dataset for processing."""
        # Generate mock data
        return [[i + j for j in range(10)] for i in range(0, 100, 10)]

    # Create analyzer
    @tool
    async def analyze_chunk(data: list[int]) -> dict[str, float]:
        """Analyze a chunk of data."""
        await asyncio.sleep(0.1)  # Simulate processing
        return {
            "count": len(data),
            "sum": sum(data),
            "average": sum(data) / len(data) if data else 0,
            "max": max(data) if data else 0,
            "min": min(data) if data else 0,
        }

    # Create aggregator
    @tool
    async def aggregate_stats(*results: list[dict[str, float]]) -> dict[str, float]:
        """Aggregate statistics from all chunks."""
        # Flatten results (they come as a list)
        all_results = (
            results[0] if results and isinstance(results[0], list) else list(results)
        )

        if not all_results:
            return {}

        total_count = sum(r["count"] for r in all_results)
        total_sum = sum(r["sum"] for r in all_results)

        return {
            "total_records": total_count,
            "total_sum": total_sum,
            "overall_average": total_sum / total_count if total_count > 0 else 0,
            "global_max": max(r["max"] for r in all_results),
            "global_min": min(r["min"] for r in all_results),
            "chunks_processed": len(all_results),
        }

    mapreduce_workflow = WorkflowPatterns.map_reduce(
        name="data_analysis",
        data_source={"name": "load_data", "tool": load_dataset},
        mapper={"name": "analyze", "tool": analyze_chunk},
        reducer={"name": "aggregate", "tool": aggregate_stats},
        chunk_size=10,
    )

    print("Visualization:")
    print(visualize_workflow(mapreduce_workflow, format="ascii"))

    print("\nExecuting map-reduce workflow...")
    result = await mapreduce_workflow.run()

    # Get the aggregated results
    if "aggregate" in result.steps and result.steps["aggregate"].success:
        aggregate_result = result.steps["aggregate"].output
        print("✅ Map-Reduce Results:")
        print(f"   Total records: {aggregate_result['total_records']}")
        print(f"   Overall average: {aggregate_result['overall_average']:.2f}")
        print(
            f"   Global min/max: {aggregate_result['global_min']}/{aggregate_result['global_max']}"
        )
        print(f"   Chunks processed: {aggregate_result['chunks_processed']}")
    else:
        print("❌ Map-reduce aggregation failed")

    # 5. Pipeline Pattern
    print("\n5️⃣ Sequential Pipeline Pattern")
    print("-" * 40)

    # Create pipeline tools
    @tool
    async def validate_input(**kwargs) -> dict[str, Any]:
        """Validate input data."""
        data = kwargs.get("data", "")
        is_valid = len(data) > 0 and data.isalnum()
        return {"valid": is_valid, "data": data}

    @tool
    async def transform_data(**kwargs) -> str:
        """Transform validated data."""
        # Get validate result
        validate = kwargs.get("validate", {})
        valid = validate.get("valid", False) if isinstance(validate, dict) else False
        data = (
            validate.get("data", "")
            if isinstance(validate, dict)
            else kwargs.get("data", "")
        )

        if not valid:
            raise ValueError("Invalid data cannot be transformed")
        return data.upper()

    @tool
    async def save_output(**kwargs) -> dict[str, Any]:
        """Save transformed data."""
        # Get transform result
        transform = kwargs.get("transform", "")
        transformed_data = transform if isinstance(transform, str) else str(transform)
        return {"saved": True, "location": f"/output/{transformed_data}.txt"}

    pipeline_workflow = WorkflowPatterns.pipeline(
        name="etl_pipeline",
        steps=[
            {
                "name": "validate",
                "tool": validate_input,
                "inputs": {"data": "hello123"},
            },
            {"name": "transform", "tool": transform_data},
            {"name": "save", "tool": save_output},
        ],
    )

    print("Visualization:")
    print(visualize_workflow(pipeline_workflow, format="ascii"))

    print("\nExecuting pipeline workflow...")
    result = await pipeline_workflow.run()
    if "save" in result.steps and result.steps["save"].success:
        save_result = result.steps["save"].output
        print(f"✅ Pipeline complete: {save_result}")
    else:
        print("❌ Pipeline did not complete successfully")

    print("\n🎉 All workflow patterns demonstrated successfully!")


if __name__ == "__main__":
    asyncio.run(main())
