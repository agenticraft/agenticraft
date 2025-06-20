# Visual Workflow Builder Guide

The AgentiCraft Visual Builder provides a drag-and-drop interface for creating multi-agent workflows without writing code.

## Quick Start

### Running the Visual Builder

```bash
# From the AgentiCraft directory
python run_visual_builder.py
```

This will:
1. Start the FastAPI server on http://localhost:8000
2. Open your browser to the visual builder interface
3. Provide API documentation at http://localhost:8000/docs

### Interface Overview

The visual builder has four main areas:

1. **Templates Panel** (Left)
   - Pre-built hero workflow templates
   - Component palette for drag-and-drop

2. **Canvas** (Center)
   - Visual workflow design area
   - Drag components here
   - Connect components with ports

3. **Properties Panel** (Right)
   - Configure selected components
   - Set parameters and options

4. **Header Actions**
   - Save/Load workflows
   - Export to Python code

## Creating Workflows

### Method 1: Using Templates

1. Click a template card:
   - 🔬 **Research Team** - Multi-agent research workflow
   - 💬 **Customer Service** - Support desk workflow
   - 👨‍💻 **Code Review** - Automated code review

2. The template loads with pre-configured components
3. Modify as needed
4. Export to Python code

### Method 2: Building from Scratch

1. **Drag Components** from the palette:
   - 📥 **Input** - User input or data source
   - 🤖 **Agent** - Individual AI agent
   - 🔄 **Workflow** - Workflow coordinator
   - 📤 **Output** - Results or actions
   - ⚙️ **Config** - Workflow configuration

2. **Connect Components**:
   - Click output port (right side) of source
   - Click input port (left side) of target
   - Connection line appears

3. **Configure Components**:
   - Click component to select
   - Edit properties in right panel
   - Set names, roles, parameters

4. **Export to Python**:
   - Click "Export to Python" button
   - Copy or download generated code

## Component Types

### Input Components
- Capture user input
- Load data from files
- API endpoints

### Agent Components
- Individual AI agents with roles
- Examples: Researcher, Analyst, Writer
- Configure model and specialty

### Workflow Components
- Coordinate multiple agents
- Hero workflows (Research, Customer Service, Code Review)
- Custom coordination logic

### Output Components
- Display results
- Save to files
- Trigger actions

### Config Components
- Global workflow settings
- Model selection (GPT-4, Claude, etc.)
- Parameters (team size, depth, etc.)

## Hero Workflow Templates

### Research Team Template

```python
# Components:
- Input: Research Topic
- Config: Team settings (size, model, depth)
- Agents: Researchers, Analysts, Writers
- Workflow: Research Team coordinator
- Output: Research Report
```

**Configuration Options:**
- Team size: 3-10 agents
- Research depth: quick, standard, comprehensive
- Output format: markdown, PDF, HTML

### Customer Service Template

```python
# Components:
- Input: Customer Inquiry
- Config: Desk settings (routing, escalation)
- Agents: Support specialists by area
- Workflow: Service Desk router
- Output: Support Response
```

**Configuration Options:**
- Routing strategy: round-robin, skills-based, priority
- Escalation: enabled/disabled
- Response style: formal, friendly, technical

### Code Review Template

```python
# Components:
- Input: Code to Review
- Config: Review settings (depth, checks)
- Agents: Security, Performance, Quality reviewers
- Workflow: Review Pipeline coordinator
- Output: Review Report
```

**Configuration Options:**
- Review depth: quick, standard, comprehensive
- Security checks: enabled/disabled
- Performance analysis: enabled/disabled
- Language: python, javascript, java, etc.

## Programmatic Usage

### Creating Workflows in Python

```python
from agenticraft.tools.builder import WorkflowBuilder, VisualComponent, ComponentType, Position

# Create builder
builder = WorkflowBuilder()

# Add components
input_comp = VisualComponent(
    type=ComponentType.INPUT,
    name="User Query",
    position=Position(100, 200)
)
input_id = builder.add_component(input_comp)

agent = VisualComponent(
    type=ComponentType.AGENT,
    name="Assistant",
    position=Position(300, 200),
    config={"model": "gpt-4"}
)
agent_id = builder.add_component(agent)

# Connect components
builder.connect(input_id, agent_id)

# Export to Python
code = builder.export_to_python()
print(code)
```

### Using Templates Programmatically

```python
from agenticraft.tools.builder import HeroWorkflowTemplates

# Create from template
builder = HeroWorkflowTemplates.create_research_team_template()

# Modify if needed
# ... add components, change config ...

# Export
code = builder.export_to_python()

# Save
builder.save("my_research_workflow.json")
```

### Loading and Modifying Workflows

```python
# Load existing workflow
builder = WorkflowBuilder()
builder.load("saved_workflow.json")

# Add new component
new_agent = VisualComponent(
    type=ComponentType.AGENT,
    name="Fact Checker",
    position=Position(400, 300)
)
builder.add_component(new_agent)

# Save modified version
builder.save("enhanced_workflow.json")
```

## API Endpoints

The visual builder provides a REST API:

### Workflow Management
- `POST /api/workflows/create` - Create new workflow
- `GET /api/workflows/{id}` - Get workflow details
- `PUT /api/workflows/{id}` - Update workflow
- `POST /api/workflows/{id}/save` - Save to disk
- `POST /api/workflows/{id}/load/{filename}` - Load from disk

### Components
- `POST /api/workflows/{id}/components` - Add component
- `DELETE /api/workflows/{id}/components/{comp_id}` - Remove component
- `POST /api/workflows/{id}/connections` - Create connection

### Templates
- `GET /api/templates` - List available templates
- `POST /api/workflows/{id}/load-template/{template_id}` - Load template

### Export
- `POST /api/workflows/{id}/export` - Export to Python/JSON

## Best Practices

### 1. Start with Templates
- Use hero workflow templates as starting points
- Modify to fit your specific needs
- Learn patterns from generated code

### 2. Component Naming
- Use descriptive names for components
- Follow role-based naming (e.g., "Security Reviewer")
- Keep names concise but clear

### 3. Workflow Organization
- Group related agents visually
- Keep data flow left-to-right
- Use config components for global settings

### 4. Testing Workflows
- Export and test generated code
- Start with simple workflows
- Gradually add complexity

### 5. Saving and Version Control
- Save workflows as JSON files
- Version control workflow files
- Document workflow purpose and usage

## Troubleshooting

### Components Not Connecting
- Ensure clicking output port first, then input port
- Components must be different
- Check browser console for errors

### Export Not Working
- Ensure workflow has required components
- Config component needed for hero workflows
- Check API server is running

### Workflow Not Loading
- Check file exists in saved_workflows directory
- Ensure valid JSON format
- Verify workflow compatibility

## Examples

### Research Automation
```python
# Load research template
# Configure for market analysis
# Add specialized analyst agents
# Export and run for automated research
```

### Customer Support Bot
```python
# Load customer service template
# Add specialized support agents
# Configure escalation rules
# Export for 24/7 support bot
```

### Code Review Pipeline
```python
# Load code review template
# Configure for your language
# Add custom review checks
# Export for CI/CD integration
```

## Summary

The Visual Workflow Builder makes it easy to:
1. **Create** workflows visually without coding
2. **Configure** agents and parameters through UI
3. **Export** to production-ready Python code
4. **Share** workflows as JSON files
5. **Iterate** quickly on multi-agent designs

For advanced usage, combine visual design with programmatic customization to create powerful multi-agent applications.
