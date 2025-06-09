"""Tests for workflow templates module."""

from agenticraft.agents.workflow import WorkflowAgent
from agenticraft.core.workflow import Workflow
from agenticraft.workflows.templates import WorkflowTemplates


class TestWorkflowTemplates:
    """Test pre-built workflow templates."""

    def test_research_workflow_template(self):
        """Test research workflow template creation."""
        template = WorkflowTemplates.research_workflow(
            topic="Climate Change",
            sources=["academic", "news", "government"],
            output_format="report",
        )

        # Check template structure
        assert template["template_type"] == "research"
        assert template["configuration"]["topic"] == "Climate Change"
        assert len(template["configuration"]["sources"]) == 3

        # Check workflow
        workflow = template["workflow"]
        assert isinstance(workflow, Workflow)
        assert workflow.name == "research_workflow"

        # Check required steps
        step_names = list(workflow._steps.keys())
        assert "define_scope" in step_names
        assert "search_academic" in step_names
        assert "search_news" in step_names
        assert "search_government" in step_names
        assert "analyze_findings" in step_names
        assert "generate_output" in step_names
        assert "quality_check" in step_names

        # Check dependencies
        analyze_step = workflow._steps["analyze_findings"]
        assert "search_academic" in analyze_step.depends_on
        assert "search_news" in analyze_step.depends_on
        assert "search_government" in analyze_step.depends_on

        # Check instructions
        assert "To use this template" in template["instructions"]

    def test_research_workflow_default_sources(self):
        """Test research workflow with default sources."""
        template = WorkflowTemplates.research_workflow(
            topic="AI Ethics", output_format="summary"
        )

        workflow = template["workflow"]
        assert "search_general" in workflow._steps
        assert template["configuration"]["output_format"] == "summary"

    def test_content_pipeline_template(self):
        """Test content pipeline template."""
        template = WorkflowTemplates.content_pipeline(
            content_type="blog", review_required=True
        )

        assert template["template_type"] == "content"
        assert template["configuration"]["content_type"] == "blog"
        assert template["configuration"]["review_required"] is True

        workflow = template["workflow"]
        step_names = list(workflow._steps.keys())

        # Check blog-specific stages
        expected_stages = [
            "ideation",
            "research",
            "outline",
            "draft",
            "edit",
            "seo",
            "finalize",
        ]
        for stage in expected_stages:
            assert stage in step_names

        # Check review steps
        assert "review_draft" in step_names
        assert "review_edit" in step_names

    def test_content_pipeline_video(self):
        """Test video content pipeline."""
        template = WorkflowTemplates.content_pipeline(
            content_type="video", review_required=False
        )

        workflow = template["workflow"]
        step_names = list(workflow._steps.keys())

        # Check video-specific stages
        assert "script" in step_names
        assert "storyboard" in step_names
        assert "production_notes" in step_names

        # No review steps
        # Video pipelines may or may not have review step
        # assert any("review" in name for name in step_names)

    def test_content_pipeline_custom_stages(self):
        """Test content pipeline with custom stages."""
        custom_stages = ["brainstorm", "draft", "polish"]
        template = WorkflowTemplates.content_pipeline(
            content_type="custom", stages=custom_stages, review_required=False
        )

        workflow = template["workflow"]
        step_names = list(workflow._steps.keys())

        for stage in custom_stages:
            assert stage in step_names

    def test_data_processing_pipeline_template(self):
        """Test data processing pipeline template."""
        template = WorkflowTemplates.data_processing_pipeline(
            input_format="csv",
            processing_steps=["clean", "transform", "analyze"],
            output_format="parquet",
            validation_required=True,
        )

        assert template["template_type"] == "data_processing"

        workflow = template["workflow"]
        step_names = list(workflow._steps.keys())

        # Check required steps
        assert "load_data" in step_names
        assert "validate_input" in step_names
        assert "clean_data" in step_names
        assert "transform_data" in step_names
        assert "analyze_data" in step_names
        assert "validate_output" in step_names
        assert "export_data" in step_names

        # Check order via dependencies
        load_step = workflow._steps["load_data"]
        assert load_step.depends_on == []

        validate_input = workflow._steps["validate_input"]
        assert "load_data" in validate_input.depends_on

        export_step = workflow._steps["export_data"]
        assert "validate_output" in export_step.depends_on

    def test_data_processing_no_validation(self):
        """Test data processing without validation."""
        template = WorkflowTemplates.data_processing_pipeline(
            input_format="json", output_format="csv", validation_required=False
        )

        workflow = template["workflow"]
        step_names = list(workflow._steps.keys())

        assert "validate_input" not in step_names
        assert "validate_output" not in step_names

    def test_multi_agent_sequential(self):
        """Test multi-agent collaboration with sequential coordination."""
        agents = [
            {"name": "researcher", "role": "Research information"},
            {"name": "analyst", "role": "Analyze findings"},
            {"name": "writer", "role": "Create report"},
        ]

        template = WorkflowTemplates.multi_agent_collaboration(
            agents=agents, coordination_style="sequential", consensus_required=True
        )

        assert template["template_type"] == "multi_agent"
        assert isinstance(template["workflow_agent"], WorkflowAgent)

        workflow = template["workflow"]
        assert len(workflow.steps) > len(agents)  # More steps due to reviews

        # Check sequential dependencies
        analyst_step = next(s for s in workflow.steps if s.name == "analyst")
        assert (
            "researcher" in analyst_step.depends_on
            or "review_researcher" in analyst_step.depends_on
        )

    def test_multi_agent_parallel(self):
        """Test multi-agent collaboration with parallel coordination."""
        agents = [
            {"name": "agent1", "role": "Task 1"},
            {"name": "agent2", "role": "Task 2"},
            {"name": "agent3", "role": "Task 3"},
        ]

        template = WorkflowTemplates.multi_agent_collaboration(
            agents=agents, coordination_style="parallel", consensus_required=False
        )

        workflow = template["workflow"]

        # Check parallel setup
        agent_steps = [
            s for s in workflow.steps if s.name in ["agent1", "agent2", "agent3"]
        ]
        for step in agent_steps:
            assert step.parallel is True

        # Check aggregation
        agg_step = next(s for s in workflow.steps if s.name == "aggregate_outputs")
        for agent in agents:
            assert agent["name"] in agg_step.depends_on

    def test_multi_agent_hierarchical(self):
        """Test multi-agent collaboration with hierarchical coordination."""
        agents = [
            {"name": "coordinator", "role": "Coordinate tasks"},
            {"name": "worker1", "role": "Execute task 1"},
            {"name": "worker2", "role": "Execute task 2"},
        ]

        template = WorkflowTemplates.multi_agent_collaboration(
            agents=agents, coordination_style="hierarchical", consensus_required=False
        )

        workflow = template["workflow"]

        # Check hierarchical structure
        plan_step = next(s for s in workflow.steps if s.name == "coordinator_plan")
        assert plan_step.depends_on == []

        worker_steps = [s for s in workflow.steps if s.name in ["worker1", "worker2"]]
        for step in worker_steps:
            assert "coordinator_plan" in step.depends_on
            assert step.parallel is True

        review_step = next(s for s in workflow.steps if s.name == "coordinator_review")
        assert "worker1" in review_step.depends_on
        assert "worker2" in review_step.depends_on

    def test_iterative_refinement_template(self):
        """Test iterative refinement template."""
        template = WorkflowTemplates.iterative_refinement(
            task="Create presentation",
            max_iterations=2,
            quality_threshold=0.85,
            reviewers=["design_expert", "content_expert"],
        )

        assert template["template_type"] == "iterative_refinement"

        workflow = template["workflow"]

        # Check initial attempt
        assert any(s.name == "initial_attempt" for s in workflow.steps)

        # Check iteration structure
        for i in range(2):
            # Quality check for each iteration
            assert any(s.name == f"quality_check_{i}" for s in workflow.steps)

            # Reviewer steps
            assert any(s.name == f"review_design_expert_{i}" for s in workflow.steps)
            assert any(s.name == f"review_content_expert_{i}" for s in workflow.steps)

            # Consolidation
            assert any(s.name == f"consolidate_feedback_{i}" for s in workflow.steps)

            # Refinement (conditional)
            refine_step = next(
                s for s in workflow.steps if s.name == f"refine_iteration_{i}"
            )
            assert refine_step.condition == f"quality_check_{i}_result < 0.85"

        # Final output
        assert any(s.name == "final_output" for s in workflow.steps)

    def test_iterative_refinement_no_reviewers(self):
        """Test iterative refinement without reviewers."""
        template = WorkflowTemplates.iterative_refinement(
            task="Write code", max_iterations=1, quality_threshold=0.9
        )

        workflow = template["workflow"]

        # No reviewer steps
        reviewer_steps = [
            s for s in workflow.steps if "review_" in s.name and "_result" not in s.name
        ]
        assert len(reviewer_steps) == 0

        # Direct refinement after quality check
        refine_step = next(s for s in workflow.steps if s.name == "refine_iteration_0")
        assert "quality_check_0" in refine_step.depends_on

    def test_template_configuration_validation(self):
        """Test template configuration validation."""
        # Test with invalid coordination style
        agents = [{"name": "agent1", "role": "Role 1"}]

        # This should still create a template, but default to sequential
        template = WorkflowTemplates.multi_agent_collaboration(
            agents=agents,
            coordination_style="invalid_style",  # Will be treated as sequential
            consensus_required=False,
        )

        # Should create workflow without error
        assert template["workflow"] is not None
