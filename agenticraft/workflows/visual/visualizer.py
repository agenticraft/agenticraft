"""Workflow visualization module.

This module provides visualization capabilities for workflows including:
- Mermaid diagram generation for web/markdown rendering
- ASCII art for terminal display
- JSON export for programmatic consumption
- Progress overlay for real-time monitoring
"""

import json
from enum import Enum
from typing import Any, Union

from ...agents.workflow import StepStatus, WorkflowStep
from ...agents.workflow import Workflow as AgentWorkflow
from ...core.workflow import Workflow, WorkflowResult


class VisualizationFormat(str, Enum):
    """Supported visualization formats."""

    MERMAID = "mermaid"
    ASCII = "ascii"
    JSON = "json"
    HTML = "html"


class WorkflowVisualizer:
    """Visualize workflows in various formats.

    This class provides methods to convert workflow definitions
    and execution results into visual representations.
    """

    def __init__(self):
        """Initialize the visualizer."""
        self.theme = {
            "colors": {
                "pending": "#gray",
                "running": "#blue",
                "completed": "#green",
                "failed": "#red",
                "skipped": "#yellow",
            },
            "icons": {
                "pending": "⏸",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
            },
        }

    def visualize(
        self,
        workflow: Workflow | AgentWorkflow,
        format: VisualizationFormat = VisualizationFormat.MERMAID,
        include_progress: bool = False,
        result: Union[WorkflowResult, "WorkflowResult"] | None = None,
    ) -> str:
        """Visualize a workflow in the specified format.

        Args:
            workflow: Workflow to visualize
            format: Output format
            include_progress: Include execution progress
            result: Optional execution result for progress overlay

        Returns:
            Visualization string in the requested format
        """
        if format == VisualizationFormat.MERMAID:
            return self.to_mermaid(workflow, include_progress, result)
        elif format == VisualizationFormat.ASCII:
            return self.to_ascii(workflow, include_progress, result)
        elif format == VisualizationFormat.JSON:
            return self.to_json(workflow, include_progress, result)
        elif format == VisualizationFormat.HTML:
            return self.to_html(workflow, include_progress, result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def to_mermaid(
        self,
        workflow: Workflow | AgentWorkflow,
        include_progress: bool = False,
        result: Any | None = None,
    ) -> str:
        """Generate Mermaid diagram for workflow.

        Args:
            workflow: Workflow to visualize
            include_progress: Include execution status
            result: Optional execution result

        Returns:
            Mermaid diagram definition
        """
        lines = ["graph TD"]

        # Determine if it's core or agent workflow
        is_agent_workflow = isinstance(workflow, AgentWorkflow)

        if is_agent_workflow:
            # Agent workflow with WorkflowStep objects
            for step in workflow.steps:
                # Node definition with status styling
                node_class = self._get_mermaid_class(
                    step.status if include_progress else None
                )
                node_label = self._escape_mermaid(step.name)

                if include_progress and step.status != StepStatus.PENDING:
                    icon = self.theme["icons"].get(step.status, "")
                    node_label = f"{icon} {node_label}"

                lines.append(f"    {step.name}[{node_label}]:::{node_class}")

                # Add edges for dependencies
                for dep in step.depends_on:
                    lines.append(f"    {dep} --> {step.name}")

                # Add timing information if available
                if include_progress and step.duration:
                    lines.append(
                        f"    {step.name} -.- timer{step.name}[{step.duration:.1f}s]"
                    )
        else:
            # Core workflow with Step objects
            steps_dict = workflow._steps

            # Build status map from result if available
            status_map = {}
            if include_progress and result:
                for step_name, step_result in result.steps.items():
                    if hasattr(step_result, "success"):
                        status_map[step_name] = (
                            StepStatus.COMPLETED
                            if step_result.success
                            else StepStatus.FAILED
                        )

            for step_name, step in steps_dict.items():
                # Node definition
                status = status_map.get(step_name)
                node_class = self._get_mermaid_class(status)
                node_label = self._escape_mermaid(step_name)

                if include_progress and status:
                    icon = self.theme["icons"].get(status, "")
                    node_label = f"{icon} {node_label}"

                lines.append(f"    {step_name}[{node_label}]:::{node_class}")

                # Add edges for dependencies
                for dep in step.depends_on:
                    lines.append(f"    {dep} --> {step_name}")

                # Add timing if available
                if include_progress and result and step_name in result.steps:
                    step_result = result.steps[step_name]
                    if hasattr(step_result, "started_at") and hasattr(
                        step_result, "completed_at"
                    ):
                        if step_result.started_at and step_result.completed_at:
                            duration = (
                                step_result.completed_at - step_result.started_at
                            ).total_seconds()
                            lines.append(
                                f"    {step_name} -.- timer{step_name}[{duration:.1f}s]"
                            )

        # Add styling
        lines.extend(
            [
                "",
                "    classDef pending fill:#f9f9f9,stroke:#999,stroke-width:2px",
                "    classDef running fill:#3498db,stroke:#2980b9,stroke-width:3px,stroke-dasharray: 5 5",
                "    classDef completed fill:#27ae60,stroke:#229954,stroke-width:2px",
                "    classDef failed fill:#e74c3c,stroke:#c0392b,stroke-width:2px",
                "    classDef skipped fill:#f39c12,stroke:#d68910,stroke-width:2px",
                "    classDef default fill:#ecf0f1,stroke:#34495e,stroke-width:2px",
            ]
        )

        return "\n".join(lines)

    def to_ascii(
        self,
        workflow: Workflow | AgentWorkflow,
        include_progress: bool = False,
        result: Any | None = None,
    ) -> str:
        """Generate ASCII art visualization.

        Args:
            workflow: Workflow to visualize
            include_progress: Include execution status
            result: Optional execution result

        Returns:
            ASCII art representation
        """
        lines = []
        is_agent_workflow = isinstance(workflow, AgentWorkflow)

        # Title
        title = f"Workflow: {workflow.name}"
        lines.append("=" * len(title))
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")

        if is_agent_workflow:
            # Build dependency graph for agent workflow
            steps_by_level = self._organize_by_levels_agent(workflow)

            # Render each level
            for level, steps in enumerate(steps_by_level):
                if level > 0:
                    lines.append("    |")
                    lines.append("    v")

                # Render steps at this level
                step_strs = []
                for step in steps:
                    status_icon = ""
                    if include_progress:
                        status_icon = self.theme["icons"].get(step.status, "") + " "

                    step_str = f"[{status_icon}{step.name}]"
                    if step.duration and include_progress:
                        step_str += f" ({step.duration:.1f}s)"

                    step_strs.append(step_str)

                # Handle parallel steps
                if len(step_strs) > 1:
                    lines.append("    " + " -> ".join(step_strs) + " (parallel)")
                else:
                    lines.append("    " + step_strs[0])
        else:
            # Build dependency graph for core workflow
            steps_by_level = self._organize_by_levels_core(workflow)

            # Build status map
            status_map = {}
            duration_map = {}
            if include_progress and result:
                for step_name, step_result in result.steps.items():
                    if hasattr(step_result, "success"):
                        status_map[step_name] = (
                            StepStatus.COMPLETED
                            if step_result.success
                            else StepStatus.FAILED
                        )
                    if hasattr(step_result, "started_at") and hasattr(
                        step_result, "completed_at"
                    ):
                        if step_result.started_at and step_result.completed_at:
                            duration_map[step_name] = (
                                step_result.completed_at - step_result.started_at
                            ).total_seconds()

            # Render each level
            for level, step_names in enumerate(steps_by_level):
                if level > 0:
                    lines.append("    |")
                    lines.append("    v")

                # Render steps at this level
                step_strs = []
                for step_name in step_names:
                    status = status_map.get(step_name)
                    status_icon = ""
                    if include_progress and status:
                        status_icon = self.theme["icons"].get(status, "") + " "

                    step_str = f"[{status_icon}{step_name}]"
                    if step_name in duration_map:
                        step_str += f" ({duration_map[step_name]:.1f}s)"

                    step_strs.append(step_str)

                # Handle parallel steps
                if len(step_strs) > 1:
                    lines.append("    " + " -> ".join(step_strs) + " (parallel)")
                else:
                    lines.append("    " + step_strs[0])

        # Add summary if progress included
        if include_progress and result:
            lines.extend(["", "Summary:", "-" * 20])
            if hasattr(result, "status"):
                lines.append(f"Status: {result.status}")
            if hasattr(result, "duration"):
                lines.append(f"Total Duration: {result.duration:.1f}s")
            if hasattr(result, "successful"):
                lines.append(f"Success: {'Yes' if result.successful else 'No'}")

        return "\n".join(lines)

    def to_json(
        self,
        workflow: Workflow | AgentWorkflow,
        include_progress: bool = False,
        result: Any | None = None,
    ) -> str:
        """Export workflow as JSON.

        Args:
            workflow: Workflow to export
            include_progress: Include execution data
            result: Optional execution result

        Returns:
            JSON string representation
        """
        is_agent_workflow = isinstance(workflow, AgentWorkflow)

        data = {
            "id": workflow.id if hasattr(workflow, "id") else str(id(workflow)),
            "name": workflow.name,
            "description": (
                workflow.description if hasattr(workflow, "description") else ""
            ),
            "steps": [],
        }

        if is_agent_workflow:
            # Export agent workflow steps
            for step in workflow.steps:
                step_data = {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "depends_on": step.depends_on,
                    "parallel": step.parallel,
                    "timeout": step.timeout,
                }

                if include_progress:
                    step_data.update(
                        {
                            "status": step.status,
                            "duration": step.duration,
                            "error": step.error,
                            "result": self._serialize_result(step.result),
                        }
                    )

                data["steps"].append(step_data)
        else:
            # Export core workflow steps
            for step_name, step in workflow._steps.items():
                step_data = {
                    "name": step_name,
                    "depends_on": step.depends_on,
                    "timeout": step.timeout,
                    "retry_count": step.retry_count,
                }

                if include_progress and result and step_name in result.steps:
                    step_result = result.steps[step_name]
                    step_data.update(
                        {
                            "success": (
                                step_result.success
                                if hasattr(step_result, "success")
                                else None
                            ),
                            "error": (
                                step_result.error
                                if hasattr(step_result, "error")
                                else None
                            ),
                        }
                    )

                    # Calculate duration if timestamps available
                    if hasattr(step_result, "started_at") and hasattr(
                        step_result, "completed_at"
                    ):
                        if step_result.started_at and step_result.completed_at:
                            duration = (
                                step_result.completed_at - step_result.started_at
                            ).total_seconds()
                            step_data["duration"] = duration

                data["steps"].append(step_data)

        # Add execution summary if available
        if include_progress and result:
            data["execution"] = {
                "status": result.status if hasattr(result, "status") else "unknown",
                "duration": result.duration if hasattr(result, "duration") else None,
                "started_at": (
                    result.started_at.isoformat()
                    if hasattr(result, "started_at") and result.started_at
                    else None
                ),
                "completed_at": (
                    result.completed_at.isoformat()
                    if hasattr(result, "completed_at") and result.completed_at
                    else None
                ),
            }

        return json.dumps(data, indent=2, default=str)

    def to_html(
        self,
        workflow: Workflow | AgentWorkflow,
        include_progress: bool = False,
        result: Any | None = None,
    ) -> str:
        """Generate interactive HTML visualization.

        Args:
            workflow: Workflow to visualize
            include_progress: Include execution status
            result: Optional execution result

        Returns:
            HTML string with embedded Mermaid diagram
        """
        mermaid_diagram = self.to_mermaid(workflow, include_progress, result)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow: {workflow.name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .diagram {{
            margin: 20px 0;
            text-align: center;
            background-color: #fafafa;
            padding: 20px;
            border-radius: 4px;
        }}
        .metadata {{
            margin-top: 20px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 4px;
        }}
        .metadata h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .metadata p {{
            margin: 5px 0;
            color: #34495e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Workflow: {workflow.name}</h1>
        <div class="diagram">
            <div class="mermaid">
{mermaid_diagram}
            </div>
        </div>
        """

        # Add metadata section if progress included
        if include_progress and result:
            html += """
        <div class="metadata">
            <h3>Execution Summary</h3>
            """

            if hasattr(result, "status"):
                html += f"<p><strong>Status:</strong> {result.status}</p>"
            if hasattr(result, "duration"):
                html += (
                    f"<p><strong>Duration:</strong> {result.duration:.2f} seconds</p>"
                )
            if hasattr(result, "started_at") and result.started_at:
                html += f"<p><strong>Started:</strong> {result.started_at.strftime('%Y-%m-%d %H:%M:%S')}</p>"
            if hasattr(result, "completed_at") and result.completed_at:
                html += f"<p><strong>Completed:</strong> {result.completed_at.strftime('%Y-%m-%d %H:%M:%S')}</p>"

            html += """
        </div>
            """

        html += """
    </div>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            themeVariables: {
                primaryColor: '#3498db',
                primaryTextColor: '#fff',
                primaryBorderColor: '#2980b9',
                lineColor: '#34495e',
                secondaryColor: '#ecf0f1',
                tertiaryColor: '#fff'
            }
        });
    </script>
</body>
</html>"""

        return html

    def _get_mermaid_class(self, status: StepStatus | None) -> str:
        """Get Mermaid CSS class for status."""
        if status is None:
            return "default"
        return status.lower()

    def _escape_mermaid(self, text: str) -> str:
        """Escape text for Mermaid diagrams."""
        # Escape special characters
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        text = text.replace("\n", "<br/>")
        return text

    def _organize_by_levels_agent(
        self, workflow: AgentWorkflow
    ) -> list[list[WorkflowStep]]:
        """Organize agent workflow steps by dependency levels."""
        levels = []
        processed = set()

        while len(processed) < len(workflow.steps):
            current_level = []

            for step in workflow.steps:
                if step.name in processed:
                    continue

                # Check if all dependencies are processed
                if all(dep in processed for dep in step.depends_on):
                    current_level.append(step)

            if not current_level:
                # Prevent infinite loop
                break

            levels.append(current_level)
            for step in current_level:
                processed.add(step.name)

        return levels

    def _organize_by_levels_core(self, workflow: Workflow) -> list[list[str]]:
        """Organize core workflow steps by dependency levels."""
        levels = []
        processed = set()

        while len(processed) < len(workflow._steps):
            current_level = []

            for step_name, step in workflow._steps.items():
                if step_name in processed:
                    continue

                # Check if all dependencies are processed
                if all(dep in processed for dep in step.depends_on):
                    current_level.append(step_name)

            if not current_level:
                # Prevent infinite loop
                break

            levels.append(current_level)
            processed.update(current_level)

        return levels

    def _serialize_result(self, result: Any) -> Any:
        """Serialize step result for JSON export."""
        if result is None:
            return None
        elif isinstance(result, (str, int, float, bool, list)):
            return result
        elif isinstance(result, dict):
            return result
        elif hasattr(result, "dict"):
            return result.dict()
        elif hasattr(result, "__dict__"):
            return result.__dict__
        else:
            return str(result)


# Convenience functions
def visualize_workflow(
    workflow: Workflow | AgentWorkflow,
    format: str = "mermaid",
    include_progress: bool = False,
    result: Any | None = None,
) -> str:
    """Quick function to visualize a workflow.

    Args:
        workflow: Workflow to visualize
        format: Output format (mermaid, ascii, json, html)
        include_progress: Include execution progress
        result: Optional execution result

    Returns:
        Visualization string
    """
    visualizer = WorkflowVisualizer()
    return visualizer.visualize(
        workflow, VisualizationFormat(format), include_progress, result
    )


def save_workflow_visualization(
    workflow: Workflow | AgentWorkflow,
    filepath: str,
    format: str = "html",
    include_progress: bool = False,
    result: Any | None = None,
) -> None:
    """Save workflow visualization to file.

    Args:
        workflow: Workflow to visualize
        filepath: Path to save file
        format: Output format
        include_progress: Include execution progress
        result: Optional execution result
    """
    content = visualize_workflow(workflow, format, include_progress, result)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
