# Workflow Visualization API Reference

## Overview

The Workflow Visualization API provides multiple formats for visualizing workflow structures, execution progress, and dependencies. Supports Mermaid diagrams, ASCII art, JSON, and interactive HTML.

## Class Reference

### WorkflowVisualizer

```python
class WorkflowVisualizer:
    """
    Generate visual representations of workflows in multiple formats.
    
    Supports static diagrams, progress overlays, and interactive visualizations.
    """
```

#### Methods

##### visualize()

```python
def visualize(
    workflow: Union[Workflow, List[Step], Dict],
    format: str = "mermaid",
    show_progress: bool = False,
    progress_data: Optional[Dict[str, StepProgress]] = None,
    theme: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> str
```

Generate visualization in the specified format.

**Parameters:**
- `workflow`: The workflow to visualize
- `format`: Output format ("mermaid", "ascii", "json", "html")
- `show_progress`: Include execution progress overlay
- `progress_data`: Progress information for each step
- `theme`: Visual theme (format-specific)
- `options`: Additional format-specific options

**Returns:**
- `str`: Visualization in the requested format

**Example:**

```python
from agenticraft.workflows import visualize_workflow

# Basic Mermaid diagram
mermaid = visualize_workflow(workflow, format="mermaid")

# With progress overlay
mermaid_progress = visualize_workflow(
    workflow,
    format="mermaid",
    show_progress=True,
    progress_data={
        "step1": StepProgress(status="completed", duration=1.2),
        "step2": StepProgress(status="running", duration=0.5),
        "step3": StepProgress(status="pending")
    }
)
```

##### to_mermaid()

```python
def to_mermaid(
    workflow: Workflow,
    theme: str = "default",
    direction: str = "TB",
    show_conditions: bool = True,
    show_tools: bool = True
) -> str
```

Generate Mermaid diagram representation.

**Parameters:**
- `workflow`: Workflow to visualize
- `theme`: Mermaid theme ("default", "dark", "forest", "neutral")
- `direction`: Graph direction ("TB", "LR", "BT", "RL")
- `show_conditions`: Display conditional logic
- `show_tools`: Show associated tools

**Returns:**
- `str`: Mermaid diagram syntax

**Example:**

```python
mermaid = visualizer.to_mermaid(
    workflow,
    theme="dark",
    direction="LR",
    show_conditions=True
)

# Output:
"""
graph LR
    start([Start])
    step1[Extract Data]
    step2[Transform Data]
    step3[Load Data]
    end([End])
    
    start --> step1
    step1 --> step2
    step2 --> step3
    step3 --> end
    
    classDef completed fill:#28a745,stroke:#1e7e34,color:#fff
    classDef running fill:#ffc107,stroke:#d39e00,color:#000
    classDef pending fill:#6c757d,stroke:#545b62,color:#fff
"""
```

##### to_ascii()

```python
def to_ascii(
    workflow: Workflow,
    width: int = 80,
    show_status: bool = True,
    box_style: str = "simple"
) -> str
```

Generate ASCII art representation for terminal display.

**Parameters:**
- `workflow`: Workflow to visualize
- `width`: Maximum width in characters
- `show_status`: Include execution status
- `box_style`: Box drawing style ("simple", "rounded", "double", "heavy")

**Returns:**
- `str`: ASCII art representation

**Example:**

```python
ascii = visualizer.to_ascii(workflow, width=60, box_style="rounded")

# Output:
"""
╭─────────────────────────────────────────────────────────╮
│                    Data Pipeline                         │
╰─────────────────────────────────────────────────────────╯
                           │
                           ▼
                    ╭──────────────╮
                    │ Extract Data │ ✓
                    ╰──────────────╯
                           │
                           ▼
                    ╭──────────────╮
                    │ Transform    │ ⟳
                    ╰──────────────╯
                           │
                           ▼
                    ╭──────────────╮
                    │ Load Data    │ ○
                    ╰──────────────╯
                           
Legend: ✓ Completed  ⟳ Running  ○ Pending  ✗ Failed
"""
```

##### to_json()

```python
def to_json(
    workflow: Workflow,
    include_metadata: bool = True,
    include_progress: bool = False,
    indent: int = 2
) -> str
```

Generate JSON representation for programmatic use.

**Parameters:**
- `workflow`: Workflow to convert
- `include_metadata`: Include step metadata
- `include_progress`: Include execution progress
- `indent`: JSON indentation level

**Returns:**
- `str`: JSON string representation

**Example:**

```python
json_data = visualizer.to_json(
    workflow,
    include_metadata=True,
    include_progress=True
)

# Output:
{
  "name": "data_pipeline",
  "description": "Process customer data",
  "steps": [
    {
      "id": "extract",
      "name": "Extract Data",
      "type": "task",
      "dependencies": [],
      "metadata": {
        "tool": "csv_reader",
        "timeout": 300
      },
      "progress": {
        "status": "completed",
        "duration": 1.23,
        "started_at": "2025-06-13T10:00:00Z",
        "completed_at": "2025-06-13T10:00:01.23Z"
      }
    }
  ],
  "edges": [
    {"from": "start", "to": "extract"},
    {"from": "extract", "to": "transform"}
  ]
}
```

##### to_html()

```python
def to_html(
    workflow: Workflow,
    title: Optional[str] = None,
    interactive: bool = True,
    embed_styles: bool = True,
    include_controls: bool = True
) -> str
```

Generate standalone HTML with interactive visualization.

**Parameters:**
- `workflow`: Workflow to visualize
- `title`: Page title
- `interactive`: Enable zoom, pan, click interactions
- `embed_styles`: Include CSS inline
- `include_controls`: Add playback controls for execution

**Returns:**
- `str`: Complete HTML document

**Example:**

```python
html = visualizer.to_html(
    workflow,
    title="Data Processing Pipeline",
    interactive=True,
    include_controls=True
)

# Generates interactive HTML with:
# - Zoomable workflow diagram
# - Click for step details
# - Execution playback controls
# - Progress animation
```

### StepProgress

```python
@dataclass
class StepProgress:
    """Progress information for a workflow step."""
    
    status: StepStatus
    duration: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output_preview: Optional[str] = None
    retry_count: int = 0
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | StepStatus | Current step status |
| `duration` | Optional[float] | Execution time in seconds |
| `started_at` | Optional[datetime] | Start timestamp |
| `completed_at` | Optional[datetime] | Completion timestamp |
| `error` | Optional[str] | Error message if failed |
| `output_preview` | Optional[str] | Preview of step output |
| `retry_count` | int | Number of retry attempts |

### StepStatus

```python
class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
```

## Visualization Options

### Mermaid Options

```python
mermaid_options = {
    "theme": "dark",              # Theme: default, dark, forest, neutral
    "direction": "TB",            # Direction: TB, LR, BT, RL
    "node_spacing": 50,           # Space between nodes
    "rank_spacing": 50,           # Space between ranks
    "curve": "basis",             # Edge curve style
    "show_labels": True,          # Show step labels
    "show_conditions": True,      # Show conditional logic
    "show_tools": True,           # Show tool associations
    "highlight_critical": True,   # Highlight critical path
    "progress_animation": True    # Animate progress
}
```

### ASCII Options

```python
ascii_options = {
    "width": 80,                  # Maximum width
    "box_style": "rounded",       # Box style: simple, rounded, double, heavy
    "show_legends": True,         # Include legend
    "compact": False,             # Compact layout
    "color": True,                # Use ANSI colors (terminal)
    "progress_bar": True,         # Show progress bars
    "tree_style": "lines"         # Tree style: lines, ascii, unicode
}
```

### JSON Options

```python
json_options = {
    "include_metadata": True,     # Include all metadata
    "include_progress": True,     # Include progress data
    "include_stats": True,        # Include statistics
    "flatten": False,             # Flatten nested structure
    "timestamps_iso": True,       # ISO format for timestamps
    "compact": False              # Compact JSON output
}
```

### HTML Options

```python
html_options = {
    "width": "100%",              # Canvas width
    "height": "600px",            # Canvas height
    "zoom_controls": True,        # Include zoom buttons
    "minimap": True,              # Include minimap
    "fullscreen": True,           # Fullscreen button
    "export_buttons": True,       # Export as image/svg
    "theme": "light",             # Theme: light, dark, auto
    "animations": True,           # Enable animations
    "tooltips": True              # Show tooltips on hover
}
```

## Advanced Usage

### Custom Themes

```python
# Define custom Mermaid theme
custom_theme = {
    "primaryColor": "#1f2937",
    "primaryTextColor": "#f3f4f6",
    "primaryBorderColor": "#4b5563",
    "lineColor": "#6b7280",
    "secondaryColor": "#374151",
    "tertiaryColor": "#111827",
    "background": "#ffffff",
    "mainBkg": "#1f2937",
    "secondBkg": "#374151",
    "tertiaryBkg": "#111827",
    "primaryBorderColor": "#4b5563",
    "lineColor": "#6b7280",
    "fontFamily": "Inter, sans-serif"
}

mermaid = visualize_workflow(
    workflow,
    format="mermaid",
    theme=custom_theme
)
```

### Progress Animation

```python
# Create animated progress visualization
async def animate_workflow_progress(workflow, execution_id):
    visualizer = WorkflowVisualizer()
    
    async for progress_update in monitor_execution(execution_id):
        # Update visualization with current progress
        visual = visualizer.visualize(
            workflow,
            format="html",
            show_progress=True,
            progress_data=progress_update,
            options={
                "animations": True,
                "update_interval": 100  # milliseconds
            }
        )
        
        # Stream to client
        yield visual
```

### Export Capabilities

```python
# Export workflow visualization
from agenticraft.workflows.visual import export_visualization

# Export as PNG
png_data = export_visualization(
    workflow,
    format="png",
    width=1920,
    height=1080,
    dpi=300
)

# Export as SVG
svg_data = export_visualization(
    workflow,
    format="svg",
    embed_fonts=True
)

# Export as PDF
pdf_data = export_visualization(
    workflow,
    format="pdf",
    page_size="A4",
    orientation="landscape"
)
```

### Integration with Jupyter

```python
# Display in Jupyter notebooks
from IPython.display import display, HTML, SVG

# Display Mermaid diagram
from agenticraft.workflows.visual import jupyter_display

jupyter_display(workflow, format="mermaid")

# Or manually
html = visualizer.to_html(workflow, options={"height": "400px"})
display(HTML(html))
```

## Performance Considerations

### Rendering Performance

| Format | Simple Workflow | Complex Workflow | Memory Usage |
|--------|----------------|------------------|--------------|
| Mermaid | ~10ms | ~50ms | Low |
| ASCII | ~5ms | ~20ms | Minimal |
| JSON | ~2ms | ~10ms | Low |
| HTML | ~20ms | ~100ms | Medium |

### Optimization Tips

1. **Cache Visualizations**: Store rendered output for static workflows
2. **Lazy Loading**: For HTML, load step details on demand
3. **Incremental Updates**: Update only changed portions
4. **Simplify Complex Workflows**: Use subgraphs for very large workflows

```python
# Caching example
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_visualization(workflow_hash, format):
    return visualize_workflow(workflow, format=format)

# Incremental updates
visualizer = WorkflowVisualizer()
visualizer.update_step_progress("step1", StepProgress(status="completed"))
updated_visual = visualizer.get_current_visualization()
```

## Error Handling

```python
try:
    visualization = visualize_workflow(workflow, format="mermaid")
except VisualizationError as e:
    if e.error_type == "circular_dependency":
        print(f"Circular dependency detected: {e.details}")
    elif e.error_type == "invalid_format":
        print(f"Unsupported format: {e.format}")
    else:
        print(f"Visualization error: {e}")
```

## Examples

### Complete Visualization Pipeline

```python
from agenticraft.workflows import visualize_workflow
from agenticraft.workflows.visual import WorkflowVisualizer

# Create visualizer instance
visualizer = WorkflowVisualizer()

# Generate multiple formats
formats = {
    "mermaid": visualizer.to_mermaid(workflow),
    "ascii": visualizer.to_ascii(workflow),
    "json": visualizer.to_json(workflow),
    "html": visualizer.to_html(workflow)
}

# Save visualizations
for format_name, content in formats.items():
    with open(f"workflow.{format_name}", "w") as f:
        f.write(content)

# Display with progress
progress_viz = visualizer.visualize(
    workflow,
    format="mermaid",
    show_progress=True,
    progress_data=execution_result.progress
)
print(progress_viz)
```

## See Also

- [Workflow Patterns](patterns.md) - Pre-built workflow patterns
- [Workflow Templates](templates.md) - Ready-to-use templates
- [WorkflowAgent](workflow_agent.md) - Execution and management
- [Examples](../../examples/workflows/visualization_example.py) - Working examples
