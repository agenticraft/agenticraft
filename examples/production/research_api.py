"""Research Team Production API Example.

This example shows how to deploy ResearchTeam as a production API service
using FastAPI, with proper error handling, caching, and monitoring.
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from agenticraft.workflows import ResearchTeam

# Load environment variables
load_dotenv()


# Request/Response models
class ResearchDepth(str, Enum):
    """Research depth options."""
    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class AudienceType(str, Enum):
    """Target audience types."""
    GENERAL = "general"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


class ResearchRequest(BaseModel):
    """Research request model."""
    topic: str = Field(..., description="The topic to research")
    depth: ResearchDepth = Field(
        ResearchDepth.STANDARD,
        description="Depth of research"
    )
    audience: AudienceType = Field(
        AudienceType.GENERAL,
        description="Target audience"
    )
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Specific areas to focus on",
        max_items=5
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context"
    )
    team_size: Optional[int] = Field(
        5,
        description="Research team size (3-10)",
        ge=3,
        le=10
    )


class ResearchResponse(BaseModel):
    """Research response model."""
    request_id: str
    topic: str
    executive_summary: str
    key_findings: List[str]
    recommendations: List[str]
    report_sections: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime


class ResearchStatus(BaseModel):
    """Research job status."""
    request_id: str
    status: str
    progress: Optional[str]
    result: Optional[ResearchResponse]
    error: Optional[str]


# Create FastAPI app
app = FastAPI(
    title="ResearchTeam API",
    description="Multi-agent research as a service",
    version="1.0.0"
)

# Global research team instance (reused for efficiency)
research_team = None

# Simple in-memory storage for async jobs
research_jobs: Dict[str, ResearchStatus] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the research team on startup."""
    global research_team
    print("Initializing ResearchTeam...")
    research_team = ResearchTeam(
        size=5,
        name="ProductionTeam"
    )
    print("ResearchTeam ready!")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "ResearchTeam API",
        "version": "1.0.0",
        "endpoints": {
            "POST /research": "Submit research request",
            "POST /research/async": "Submit async research request",
            "GET /research/status/{request_id}": "Check async job status",
            "GET /team/status": "Get team status",
            "POST /team/adjust": "Adjust team composition"
        }
    }


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Conduct research synchronously (waits for completion)."""
    try:
        # Adjust team size if requested
        if request.team_size != research_team.team_size:
            diff = request.team_size - research_team.team_size
            await research_team.adjust_team(
                add_researchers=diff // 2,
                add_analysts=diff - (diff // 2)
            )
        
        # Conduct research
        start_time = time.time()
        result = await research_team.research(
            topic=request.topic,
            depth=request.depth.value,
            audience=request.audience.value,
            focus_areas=request.focus_areas,
            context=request.context
        )
        
        # Create response
        response = ResearchResponse(
            request_id=f"req_{int(time.time() * 1000)}",
            topic=request.topic,
            executive_summary=result["executive_summary"],
            key_findings=result["key_findings"],
            recommendations=result["recommendations"],
            report_sections=list(result["sections"].keys()),
            metadata={
                **result["metadata"],
                "api_latency": time.time() - start_time
            },
            timestamp=datetime.utcnow()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_research_job(request_id: str, request: ResearchRequest):
    """Run research job in background."""
    try:
        # Update status
        research_jobs[request_id].status = "running"
        research_jobs[request_id].progress = "Initializing research team..."
        
        # Conduct research
        result = await research_team.research(
            topic=request.topic,
            depth=request.depth.value,
            audience=request.audience.value,
            focus_areas=request.focus_areas,
            context=request.context
        )
        
        # Create response
        response = ResearchResponse(
            request_id=request_id,
            topic=request.topic,
            executive_summary=result["executive_summary"],
            key_findings=result["key_findings"],
            recommendations=result["recommendations"],
            report_sections=list(result["sections"].keys()),
            metadata=result["metadata"],
            timestamp=datetime.utcnow()
        )
        
        # Update job status
        research_jobs[request_id].status = "completed"
        research_jobs[request_id].result = response
        
    except Exception as e:
        # Update job with error
        research_jobs[request_id].status = "failed"
        research_jobs[request_id].error = str(e)


@app.post("/research/async")
async def research_async(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """Submit research request asynchronously."""
    # Generate request ID
    request_id = f"req_{int(time.time() * 1000)}"
    
    # Create job entry
    research_jobs[request_id] = ResearchStatus(
        request_id=request_id,
        status="pending",
        progress="Request queued",
        result=None,
        error=None
    )
    
    # Add to background tasks
    background_tasks.add_task(run_research_job, request_id, request)
    
    return {
        "request_id": request_id,
        "status": "accepted",
        "message": "Research job submitted",
        "check_status_at": f"/research/status/{request_id}"
    }


@app.get("/research/status/{request_id}", response_model=ResearchStatus)
async def get_research_status(request_id: str):
    """Get status of async research job."""
    if request_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Research job not found")
    
    return research_jobs[request_id]


@app.get("/team/status")
async def get_team_status():
    """Get current team status."""
    return await research_team.get_team_status()


@app.post("/team/adjust")
async def adjust_team(
    add_researchers: int = 0,
    add_analysts: int = 0,
    add_writers: int = 0
):
    """Adjust team composition."""
    try:
        new_composition = await research_team.adjust_team(
            add_researchers=add_researchers,
            add_analysts=add_analysts,
            add_writers=add_writers
        )
        
        return {
            "status": "adjusted",
            "new_composition": new_composition,
            "team_status": await research_team.get_team_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/research/stream")
async def research_stream(topic: str):
    """Stream research progress (SSE endpoint)."""
    async def generate():
        # Send updates as research progresses
        yield f"data: Starting research on '{topic}'\n\n"
        
        # In production, this would stream real progress
        steps = [
            "Initializing research team...",
            "Conducting web research...",
            "Analyzing findings...",
            "Generating report...",
            "Finalizing recommendations..."
        ]
        
        for step in steps:
            yield f"data: {step}\n\n"
            # In real implementation, await actual progress
        
        yield f"data: Research complete!\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "team_initialized": research_team is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get API metrics."""
    total_jobs = len(research_jobs)
    completed = sum(1 for j in research_jobs.values() if j.status == "completed")
    failed = sum(1 for j in research_jobs.values() if j.status == "failed")
    running = sum(1 for j in research_jobs.values() if j.status == "running")
    
    return {
        "total_research_jobs": total_jobs,
        "completed": completed,
        "failed": failed,
        "running": running,
        "team_status": await research_team.get_team_status() if research_team else None
    }


if __name__ == "__main__":
    # Check for API key
    if not any(os.getenv(key) for key in [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"
    ]):
        print("❌ Error: No API key found!")
        print("Please set an API key in your .env file")
    else:
        print("🚀 Starting ResearchTeam API...")
        print("📝 API docs available at: http://localhost:8000/docs")
        
        # Run the API
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
