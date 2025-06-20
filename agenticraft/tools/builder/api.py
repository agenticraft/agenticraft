"""FastAPI backend for Visual Workflow Builder."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path

from .visual_builder import (
    WorkflowBuilder, 
    HeroWorkflowTemplates,
    HeroWorkflowType,
    ComponentType,
    VisualComponent,
    Position
)

app = FastAPI(title="AgentiCraft Visual Builder API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for active workflows (in production, use a database)
active_workflows: Dict[str, WorkflowBuilder] = {}

# Ensure directories exist
WORKFLOWS_DIR = Path("saved_workflows")
EXPORTS_DIR = Path("exported_code")
WORKFLOWS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Pydantic models for API
class ComponentCreate(BaseModel):
    """Request model for creating a component."""
    type: str
    name: str
    x: float
    y: float
    config: Dict[str, Any] = {}

class ConnectionCreate(BaseModel):
    """Request model for creating a connection."""
    source_id: str
    target_id: str

class WorkflowUpdate(BaseModel):
    """Request model for updating workflow."""
    workflow_type: Optional[str] = None

class ExportRequest(BaseModel):
    """Request model for export."""
    format: str = "python"  # python, json


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AgentiCraft Visual Builder API",
        "docs": "/docs",
        "builder": "/static/index.html"
    }

@app.post("/api/workflows/create")
async def create_workflow():
    """Create a new workflow."""
    workflow_id = str(len(active_workflows) + 1)
    active_workflows[workflow_id] = WorkflowBuilder()
    return {"workflow_id": workflow_id}

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow details."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    return {
        "workflow_id": workflow_id,
        "workflow_type": workflow.workflow_type.value if workflow.workflow_type else None,
        "components": [c.to_dict() for c in workflow.components.values()],
        "connections": [c.to_dict() for c in workflow.connections]
    }

@app.put("/api/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, update: WorkflowUpdate):
    """Update workflow settings."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    if update.workflow_type:
        workflow.workflow_type = HeroWorkflowType(update.workflow_type)
    
    return {"status": "updated"}

@app.post("/api/workflows/{workflow_id}/components")
async def add_component(workflow_id: str, component: ComponentCreate):
    """Add a component to the workflow."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    visual_component = VisualComponent(
        type=ComponentType(component.type),
        name=component.name,
        position=Position(component.x, component.y),
        config=component.config
    )
    
    component_id = workflow.add_component(visual_component)
    return {"component_id": component_id}

@app.delete("/api/workflows/{workflow_id}/components/{component_id}")
async def remove_component(workflow_id: str, component_id: str):
    """Remove a component from the workflow."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    workflow.remove_component(component_id)
    return {"status": "removed"}

@app.post("/api/workflows/{workflow_id}/connections")
async def add_connection(workflow_id: str, connection: ConnectionCreate):
    """Add a connection between components."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    connection_id = workflow.connect(connection.source_id, connection.target_id)
    return {"connection_id": connection_id}

@app.post("/api/workflows/{workflow_id}/export")
async def export_workflow(workflow_id: str, request: ExportRequest):
    """Export workflow to code or JSON."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    
    if request.format == "python":
        code = workflow.export_to_python()
        filename = f"workflow_{workflow_id}.py"
        filepath = EXPORTS_DIR / filename
        
        with open(filepath, 'w') as f:
            f.write(code)
            
        return {
            "format": "python",
            "code": code,
            "filename": filename,
            "download_url": f"/api/downloads/{filename}"
        }
    elif request.format == "json":
        filename = f"workflow_{workflow_id}.json"
        filepath = WORKFLOWS_DIR / filename
        workflow.save(str(filepath))
        
        return {
            "format": "json",
            "filename": filename,
            "download_url": f"/api/downloads/{filename}"
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")

@app.get("/api/templates")
async def list_templates():
    """List available workflow templates."""
    return {
        "templates": [
            {
                "id": "research_team",
                "name": "Research Team",
                "description": "Multi-agent research team for comprehensive analysis",
                "type": HeroWorkflowType.RESEARCH_TEAM.value
            },
            {
                "id": "customer_service",
                "name": "Customer Service Desk",
                "description": "Intelligent customer support system",
                "type": HeroWorkflowType.CUSTOMER_SERVICE.value
            },
            {
                "id": "code_review",
                "name": "Code Review Pipeline",
                "description": "Automated code review with multiple perspectives",
                "type": HeroWorkflowType.CODE_REVIEW.value
            }
        ]
    }

@app.post("/api/workflows/{workflow_id}/load-template/{template_id}")
async def load_template(workflow_id: str, template_id: str):
    """Load a template into the workflow."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create template
    if template_id == "research_team":
        template = HeroWorkflowTemplates.create_research_team_template()
    elif template_id == "customer_service":
        template = HeroWorkflowTemplates.create_customer_service_template()
    elif template_id == "code_review":
        template = HeroWorkflowTemplates.create_code_review_template()
    else:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Replace current workflow with template
    active_workflows[workflow_id] = template
    
    return {"status": "template_loaded"}

@app.get("/api/downloads/{filename}")
async def download_file(filename: str):
    """Download exported file."""
    # Check in both directories
    for directory in [EXPORTS_DIR, WORKFLOWS_DIR]:
        filepath = directory / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                content = f.read()
            
            return {
                "filename": filename,
                "content": content,
                "content_type": "text/plain" if filename.endswith('.py') else "application/json"
            }
    
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/workflows/{workflow_id}/save")
async def save_workflow(workflow_id: str, name: str = "workflow"):
    """Save workflow to disk."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = active_workflows[workflow_id]
    filename = f"{name}_{workflow_id}.json"
    filepath = WORKFLOWS_DIR / filename
    
    workflow.save(str(filepath))
    
    return {
        "status": "saved",
        "filename": filename
    }

@app.get("/api/saved-workflows")
async def list_saved_workflows():
    """List saved workflows."""
    workflows = []
    for filepath in WORKFLOWS_DIR.glob("*.json"):
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        workflows.append({
            "filename": filepath.name,
            "workflow_type": data.get("workflow_type"),
            "components_count": len(data.get("components", [])),
            "connections_count": len(data.get("connections", []))
        })
    
    return {"workflows": workflows}

@app.post("/api/workflows/{workflow_id}/load/{filename}")
async def load_workflow(workflow_id: str, filename: str):
    """Load a saved workflow."""
    filepath = WORKFLOWS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Workflow file not found")
    
    workflow = WorkflowBuilder()
    workflow.load(str(filepath))
    
    active_workflows[workflow_id] = workflow
    
    return {"status": "loaded"}

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_workflows": len(active_workflows),
        "saved_workflows": len(list(WORKFLOWS_DIR.glob("*.json")))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
