"""Example: Using the Visual Workflow Builder Programmatically

This example shows how to create workflows programmatically using the
visual builder API and export them to Python code.
"""

import asyncio
from agenticraft.tools.builder import (
    WorkflowBuilder, 
    HeroWorkflowTemplates,
    ComponentType,
    VisualComponent,
    Position
)

def example_research_team():
    """Create a research team workflow programmatically."""
    print("🔬 Creating Research Team Workflow")
    print("-" * 40)
    
    # Use template
    builder = HeroWorkflowTemplates.create_research_team_template()
    
    # Export to Python
    code = builder.export_to_python()
    print("Generated Python Code:")
    print(code)
    
    # Save to file
    builder.save("research_team_workflow.json")
    print("\n✅ Workflow saved to research_team_workflow.json")

def example_custom_workflow():
    """Create a custom workflow from scratch."""
    print("\n🛠️ Creating Custom Workflow")
    print("-" * 40)
    
    builder = WorkflowBuilder()
    
    # Add input
    input_comp = VisualComponent(
        type=ComponentType.INPUT,
        name="User Query",
        position=Position(100, 200),
        config={"placeholder": "Enter your question"}
    )
    input_id = builder.add_component(input_comp)
    
    # Add agents
    analyst = VisualComponent(
        type=ComponentType.AGENT,
        name="Data Analyst",
        position=Position(300, 150),
        config={"role": "analyst", "model": "gpt-4"}
    )
    analyst_id = builder.add_component(analyst)
    
    writer = VisualComponent(
        type=ComponentType.AGENT,
        name="Report Writer",
        position=Position(300, 250),
        config={"role": "writer", "style": "professional"}
    )
    writer_id = builder.add_component(writer)
    
    # Add workflow coordinator
    workflow = VisualComponent(
        type=ComponentType.WORKFLOW,
        name="Analysis Pipeline",
        position=Position(500, 200),
        config={"type": "custom"}
    )
    workflow_id = builder.add_component(workflow)
    
    # Add output
    output = VisualComponent(
        type=ComponentType.OUTPUT,
        name="Analysis Report",
        position=Position(700, 200),
        config={"format": "markdown"}
    )
    output_id = builder.add_component(output)
    
    # Connect components
    builder.connect(input_id, workflow_id)
    builder.connect(analyst_id, workflow_id)
    builder.connect(writer_id, workflow_id)
    builder.connect(workflow_id, output_id)
    
    # Export
    code = builder.export_to_python()
    print("Generated Python Code:")
    print(code)
    
    # Save
    builder.save("custom_analysis_workflow.json")
    print("\n✅ Custom workflow saved")

def example_load_and_modify():
    """Load a saved workflow and modify it."""
    print("\n📂 Loading and Modifying Workflow")
    print("-" * 40)
    
    # Create a simple workflow first
    builder = HeroWorkflowTemplates.create_customer_service_template()
    builder.save("customer_service_base.json")
    
    # Load it
    modified_builder = WorkflowBuilder()
    modified_builder.load("customer_service_base.json")
    
    # Add a new component
    escalation = VisualComponent(
        type=ComponentType.AGENT,
        name="Escalation Manager",
        position=Position(500, 400),
        config={"role": "manager", "threshold": "high_priority"}
    )
    modified_builder.add_component(escalation)
    
    # Save modified version
    modified_builder.save("customer_service_enhanced.json")
    print("✅ Enhanced workflow saved with escalation manager")

def main():
    """Run all examples."""
    print("🎨 Visual Workflow Builder Examples")
    print("=" * 50)
    
    # Example 1: Use templates
    example_research_team()
    
    # Example 2: Build from scratch
    example_custom_workflow()
    
    # Example 3: Load and modify
    example_load_and_modify()
    
    print("\n✨ All examples completed!")
    print("\nTo use the visual interface, run:")
    print("  python run_visual_builder.py")

if __name__ == "__main__":
    main()
