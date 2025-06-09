"""Pre-built workflow templates for common scenarios.

This module provides ready-to-use workflow templates for:
- Research workflows
- Content pipelines
- Data processing
- Multi-agent collaboration
"""

from typing import Any

from ..agents.workflow import WorkflowAgent
from ..core.tool import tool
from ..core.workflow import Step, Workflow


# Placeholder tool for templates
@tool
def placeholder_tool(**kwargs) -> str:
    """Placeholder tool for workflow templates.

    This should be replaced with actual tools when using the template.
    """
    return f"Placeholder result for {kwargs.get('prompt', 'task')}"


class WorkflowTemplates:
    """Collection of pre-built workflow templates."""

    @staticmethod
    def research_workflow(
        topic: str, sources: list[str] | None = None, output_format: str = "report"
    ) -> dict[str, Any]:
        """Create a research workflow template.

        Args:
            topic: Research topic
            sources: Optional list of sources to search
            output_format: Output format (report, summary, presentation)

        Returns:
            Dictionary with workflow and configuration

        Example:
            template = WorkflowTemplates.research_workflow(
                topic="AI Ethics",
                sources=["academic", "news", "blogs"],
                output_format="report"
            )

            workflow = template["workflow"]
            result = await workflow.run(topic=topic)
        """
        workflow = Workflow(
            name="research_workflow", description=f"Research workflow for: {topic}"
        )

        # Step 1: Define research scope
        workflow.add_step(
            Step(
                name="define_scope",
                tool=placeholder_tool,  # Should be replaced by user
                inputs={
                    "topic": topic,
                    "sources": sources or ["general"],
                    "prompt": "Define the research scope and key questions for the topic",
                },
            )
        )

        # Step 2: Gather information (parallel)
        source_steps = []
        for idx, source in enumerate(sources or ["general"]):
            step_name = f"search_{source}"
            workflow.add_step(
                Step(
                    name=step_name,
                    tool=placeholder_tool,  # Should be replaced by user
                    inputs={
                        "source": source,
                        "scope": "$define_scope",
                        "prompt": f"Search {source} sources for information",
                    },
                    depends_on=["define_scope"],
                )
            )
            source_steps.append(step_name)

        # Step 3: Analyze and synthesize
        workflow.add_step(
            Step(
                name="analyze_findings",
                tool=placeholder_tool,  # Should be replaced by user
                inputs={"prompt": "Analyze and synthesize the research findings"},
                depends_on=source_steps,
            )
        )

        # Step 4: Generate output
        output_prompts = {
            "report": "Generate a comprehensive research report with citations",
            "summary": "Create an executive summary of key findings",
            "presentation": "Create presentation slides with main points",
        }

        workflow.add_step(
            Step(
                name="generate_output",
                tool=placeholder_tool,  # Should be replaced by user
                inputs={
                    "format": output_format,
                    "prompt": output_prompts.get(
                        output_format, "Generate research output"
                    ),
                },
                depends_on=["analyze_findings"],
            )
        )

        # Step 5: Quality check
        workflow.add_step(
            Step(
                name="quality_check",
                tool=placeholder_tool,  # Should be replaced by user
                inputs={
                    "prompt": "Review output for accuracy, completeness, and citations"
                },
                depends_on=["generate_output"],
            )
        )

        return {
            "workflow": workflow,
            "template_type": "research",
            "configuration": {
                "topic": topic,
                "sources": sources,
                "output_format": output_format,
            },
            "required_tools": {
                "define_scope": "Tool for defining research scope",
                **{
                    f"search_{source}": f"Tool for searching {source}"
                    for source in (sources or ["general"])
                },
            },
            "instructions": (
                "To use this template:\n"
                "1. Set appropriate tools/agents for each step\n"
                "2. Configure tool inputs as needed\n"
                "3. Run the workflow with initial parameters\n"
                "4. Review and iterate on results"
            ),
        }

    @staticmethod
    def content_pipeline(
        content_type: str = "blog",
        stages: list[str] | None = None,
        review_required: bool = True,
    ) -> dict[str, Any]:
        """Create a content creation pipeline template.

        Args:
            content_type: Type of content (blog, video, social, email)
            stages: Optional custom stages (default: ideation, outline, draft, edit, finalize)
            review_required: Whether to include review steps

        Returns:
            Dictionary with workflow and configuration
        """
        default_stages = {
            "blog": [
                "ideation",
                "research",
                "outline",
                "draft",
                "edit",
                "seo",
                "finalize",
            ],
            "video": ["ideation", "script", "storyboard", "production_notes", "review"],
            "social": ["ideation", "draft", "visuals", "hashtags", "schedule"],
            "email": ["audience", "subject", "draft", "personalize", "test"],
        }

        stages = stages or default_stages.get(
            content_type, ["ideation", "draft", "edit", "finalize"]
        )

        workflow = Workflow(
            name="content_pipeline", description=f"Content pipeline for {content_type}"
        )

        # Add stages sequentially
        for idx, stage in enumerate(stages):
            deps = [] if idx == 0 else [stages[idx - 1]]

            # Add review step after certain stages if required
            if review_required and stage in ["draft", "edit"]:
                workflow.add_step(
                    Step(
                        name=stage,
                        tool=placeholder_tool,
                        inputs={
                            "stage": stage,
                            "content_type": content_type,
                            "prompt": f"Execute {stage} stage for {content_type} content",
                        },
                        depends_on=deps,
                    )
                )

                # Add review step
                workflow.add_step(
                    Step(
                        name=f"review_{stage}",
                        tool=placeholder_tool,
                        inputs={"prompt": f"Review and provide feedback on {stage}"},
                        depends_on=[stage],
                    )
                )

                # Next stage depends on review
                if idx < len(stages) - 1:
                    stages[idx + 1] = stages[
                        idx + 1
                    ]  # Update reference for next iteration
            else:
                workflow.add_step(
                    Step(
                        name=stage,
                        tool=placeholder_tool,
                        inputs={
                            "stage": stage,
                            "content_type": content_type,
                            "prompt": f"Execute {stage} stage for {content_type} content",
                        },
                        depends_on=(
                            deps
                            if not (
                                review_required
                                and idx > 0
                                and stages[idx - 1] in ["draft", "edit"]
                            )
                            else [f"review_{stages[idx-1]}"]
                        ),
                    )
                )

        return {
            "workflow": workflow,
            "template_type": "content",
            "configuration": {
                "content_type": content_type,
                "stages": stages,
                "review_required": review_required,
            },
        }

    @staticmethod
    def data_processing_pipeline(
        input_format: str = "csv",
        processing_steps: list[str] | None = None,
        output_format: str = "json",
        validation_required: bool = True,
    ) -> dict[str, Any]:
        """Create a data processing pipeline template.

        Args:
            input_format: Input data format
            processing_steps: Custom processing steps
            output_format: Output data format
            validation_required: Whether to include validation

        Returns:
            Dictionary with workflow and configuration
        """
        default_steps = ["load", "validate", "clean", "transform", "enrich", "export"]
        processing_steps = processing_steps or default_steps

        workflow = Workflow(
            name="data_processing",
            description=f"Process {input_format} to {output_format}",
        )

        # Always start with load
        workflow.add_step(
            Step(
                name="load_data",
                tool=placeholder_tool,
                inputs={
                    "format": input_format,
                    "prompt": f"Load data from {input_format} format",
                },
            )
        )

        last_step = "load_data"

        # Add validation if required
        if validation_required:
            workflow.add_step(
                Step(
                    name="validate_input",
                    tool=placeholder_tool,
                    inputs={"prompt": "Validate data schema and integrity"},
                    depends_on=[last_step],
                )
            )
            last_step = "validate_input"

        # Add processing steps
        for step in processing_steps:
            if step not in [
                "load",
                "export",
            ]:  # Skip load (already added) and export (added later)
                workflow.add_step(
                    Step(
                        name=f"{step}_data",
                        tool=placeholder_tool,
                        inputs={
                            "operation": step,
                            "prompt": f"Apply {step} operation to data",
                        },
                        depends_on=[last_step],
                    )
                )
                last_step = f"{step}_data"

        # Add final validation if required
        if validation_required:
            workflow.add_step(
                Step(
                    name="validate_output",
                    tool=placeholder_tool,
                    inputs={"prompt": "Validate processed data before export"},
                    depends_on=[last_step],
                )
            )
            last_step = "validate_output"

        # Export step
        workflow.add_step(
            Step(
                name="export_data",
                tool=placeholder_tool,
                inputs={
                    "format": output_format,
                    "prompt": f"Export data to {output_format} format",
                },
                depends_on=[last_step],
            )
        )

        return {
            "workflow": workflow,
            "template_type": "data_processing",
            "configuration": {
                "input_format": input_format,
                "processing_steps": processing_steps,
                "output_format": output_format,
                "validation_required": validation_required,
            },
        }

    @staticmethod
    def multi_agent_collaboration(
        agents: list[dict[str, str]],
        coordination_style: str = "sequential",
        consensus_required: bool = False,
    ) -> dict[str, Any]:
        """Create a multi-agent collaboration template.

        Args:
            agents: List of agent definitions with 'name' and 'role'
            coordination_style: How agents coordinate (sequential, parallel, hierarchical)
            consensus_required: Whether consensus is needed

        Returns:
            Dictionary with workflow and configuration

        Example:
            template = WorkflowTemplates.multi_agent_collaboration(
                agents=[
                    {"name": "researcher", "role": "Research and gather information"},
                    {"name": "analyst", "role": "Analyze and synthesize findings"},
                    {"name": "writer", "role": "Create final output"}
                ],
                coordination_style="sequential",
                consensus_required=True
            )
        """
        workflow_agent = WorkflowAgent(
            name="CollaborationCoordinator",
            instructions="Coordinate multiple agents to achieve the goal",
        )

        workflow = workflow_agent.create_workflow(
            "multi_agent_collab", f"Multi-agent collaboration with {len(agents)} agents"
        )

        if coordination_style == "sequential":
            # Agents work in sequence
            for idx, agent_def in enumerate(agents):
                deps = [] if idx == 0 else [agents[idx - 1]["name"]]

                workflow.add_step(
                    name=agent_def["name"],
                    action=f"Agent {agent_def['name']}: {agent_def['role']}",
                    depends_on=deps,
                )

                # Add review step if consensus required
                if consensus_required and idx < len(agents) - 1:
                    workflow.add_step(
                        name=f"review_{agent_def['name']}",
                        action=f"All agents review output from {agent_def['name']}",
                        depends_on=[agent_def["name"]],
                    )

                    # Next agent depends on review
                    if idx < len(agents) - 1:
                        agents[idx + 1]["deps"] = [f"review_{agent_def['name']}"]

        elif coordination_style == "parallel":
            # All agents work in parallel
            agent_names = []
            for agent_def in agents:
                workflow.add_step(
                    name=agent_def["name"],
                    action=f"Agent {agent_def['name']}: {agent_def['role']}",
                    parallel=True,
                )
                agent_names.append(agent_def["name"])

            # Add aggregation step
            workflow.add_step(
                name="aggregate_outputs",
                action="Combine outputs from all agents",
                depends_on=agent_names,
            )

            # Add consensus if required
            if consensus_required:
                workflow.add_step(
                    name="reach_consensus",
                    action="All agents review and reach consensus",
                    depends_on=["aggregate_outputs"],
                )

        elif coordination_style == "hierarchical":
            # First agent coordinates others
            coordinator = agents[0]
            workers = agents[1:]

            # Coordinator plans
            workflow.add_step(
                name=f"{coordinator['name']}_plan",
                action=f"Coordinator {coordinator['name']}: Create plan and assign tasks",
            )

            # Workers execute in parallel
            worker_names = []
            for worker in workers:
                workflow.add_step(
                    name=worker["name"],
                    action=f"Worker {worker['name']}: {worker['role']}",
                    depends_on=[f"{coordinator['name']}_plan"],
                    parallel=True,
                )
                worker_names.append(worker["name"])

            # Coordinator reviews
            workflow.add_step(
                name=f"{coordinator['name']}_review",
                action=f"Coordinator {coordinator['name']}: Review and finalize",
                depends_on=worker_names,
            )

        return {
            "workflow": workflow,
            "workflow_agent": workflow_agent,
            "template_type": "multi_agent",
            "configuration": {
                "agents": agents,
                "coordination_style": coordination_style,
                "consensus_required": consensus_required,
            },
        }

    @staticmethod
    def iterative_refinement(
        task: str,
        max_iterations: int = 3,
        quality_threshold: float = 0.8,
        reviewers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an iterative refinement workflow template.

        Args:
            task: Task to refine
            max_iterations: Maximum refinement iterations
            quality_threshold: Quality score needed to complete
            reviewers: Optional list of reviewer roles

        Returns:
            Dictionary with workflow and configuration
        """
        workflow_agent = WorkflowAgent(
            name="RefinementCoordinator",
            instructions=f"Iteratively refine {task} until quality threshold is met",
        )

        workflow = workflow_agent.create_workflow(
            "iterative_refinement", f"Refine {task} through iterations"
        )

        # Initial attempt
        workflow.add_step(
            name="initial_attempt", action=f"Create initial version of {task}"
        )

        # Iteration loop (unrolled for simplicity)
        for i in range(max_iterations):
            prev_step = "initial_attempt" if i == 0 else f"refine_iteration_{i-1}"

            # Quality check
            workflow.add_step(
                name=f"quality_check_{i}",
                action=f"Evaluate quality of current version (iteration {i+1})",
                depends_on=[prev_step],
            )

            # Review step if reviewers specified
            if reviewers:
                review_deps = [f"quality_check_{i}"]
                for reviewer in reviewers:
                    workflow.add_step(
                        name=f"review_{reviewer}_{i}",
                        action=f"{reviewer} reviews and provides feedback",
                        depends_on=[f"quality_check_{i}"],
                        parallel=True,
                    )
                    review_deps.append(f"review_{reviewer}_{i}")

                # Consolidate feedback
                workflow.add_step(
                    name=f"consolidate_feedback_{i}",
                    action="Consolidate all reviewer feedback",
                    depends_on=review_deps,
                )

                refine_deps = [f"consolidate_feedback_{i}"]
            else:
                refine_deps = [f"quality_check_{i}"]

            # Refinement step (conditional on quality)
            workflow.add_step(
                name=f"refine_iteration_{i}",
                action=f"Refine based on feedback (iteration {i+1})",
                depends_on=refine_deps,
                condition=f"quality_check_{i}_result < {quality_threshold}",
            )

        # Final output
        final_deps = [f"quality_check_{max_iterations-1}"]
        if max_iterations > 0:
            final_deps.append(f"refine_iteration_{max_iterations-1}")

        workflow.add_step(
            name="final_output",
            action="Prepare final refined output",
            depends_on=final_deps,
        )

        return {
            "workflow": workflow,
            "workflow_agent": workflow_agent,
            "template_type": "iterative_refinement",
            "configuration": {
                "task": task,
                "max_iterations": max_iterations,
                "quality_threshold": quality_threshold,
                "reviewers": reviewers,
            },
        }
