"""Customer Service Desk Production API Example.

This example shows how to deploy CustomerServiceDesk as a production API service
using FastAPI, with WebSocket support for real-time updates, escalation management,
and comprehensive monitoring.
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from agenticraft.workflows import CustomerServiceDesk
from agenticraft.agents.patterns import EscalationPriority

# Load environment variables
load_dotenv()


# Request/Response models
class Priority(int, Enum):
    """Customer priority levels."""
    LOW = 3
    MEDIUM = 5
    HIGH = 7
    URGENT = 9
    CRITICAL = 10


class CustomerInquiry(BaseModel):
    """Customer inquiry model."""
    customer_id: str = Field(..., description="Customer identifier")
    inquiry: str = Field(..., description="Customer's question or issue")
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context (order ID, account info, etc.)"
    )
    priority: Priority = Field(
        Priority.MEDIUM,
        description="Priority level"
    )


class ServiceResponse(BaseModel):
    """Service response model."""
    request_id: str
    customer_id: str
    response: str
    agent: str
    escalated: bool
    resolution_time: float
    resolution_path: List[Dict[str, Any]]
    status: str
    timestamp: datetime


class EscalationRequest(BaseModel):
    """Escalation handling request."""
    request_id: str
    approved: bool
    comments: Optional[str] = Field(None, description="Review comments")


class DeskConfiguration(BaseModel):
    """Service desk configuration."""
    tiers: List[str] = Field(
        default=["L1", "L2", "Expert"],
        description="Support tier names"
    )
    agents_per_tier: List[int] = Field(
        default=[3, 2, 1],
        description="Number of agents per tier"
    )


# Create FastAPI app
app = FastAPI(
    title="CustomerServiceDesk API",
    description="Multi-tier customer service with intelligent routing and escalation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service desk instance
service_desk: Optional[CustomerServiceDesk] = None

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []

# Escalation reviewers (would be from database in production)
human_reviewers = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the service desk on startup."""
    global service_desk
    print("Initializing CustomerServiceDesk...")
    
    service_desk = CustomerServiceDesk(
        name="ProductionServiceDesk",
        enable_auth=True
    )
    
    # Add some production API keys
    service_desk.add_api_key(
        "prod-api-key-123",
        "production_client",
        "Production Client",
        {"customer_service", "escalation"}
    )
    
    service_desk.add_api_key(
        "premium-api-key-456",
        "premium_client",
        "Premium Client",
        {"customer_service", "escalation", "priority", "admin"}
    )
    
    # Add human reviewers
    service_desk.add_human_reviewer(
        "reviewer_1",
        "Alice Johnson",
        max_concurrent=5,
        specialties={"billing", "refunds"}
    )
    
    service_desk.add_human_reviewer(
        "reviewer_2",
        "Bob Smith",
        max_concurrent=5,
        specialties={"technical", "bugs"}
    )
    
    print("CustomerServiceDesk ready!")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "CustomerServiceDesk API",
        "version": "1.0.0",
        "endpoints": {
            "POST /support/inquiry": "Submit customer inquiry",
            "GET /support/status": "Get service desk status",
            "GET /support/history/{customer_id}": "Get customer history",
            "GET /escalations/pending": "Get pending escalations",
            "POST /escalations/review": "Review escalation",
            "WS /ws": "WebSocket for real-time updates"
        }
    }


@app.post("/support/inquiry", response_model=ServiceResponse)
async def handle_inquiry(
    inquiry: CustomerInquiry,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """Handle a customer service inquiry."""
    try:
        # Process inquiry
        start_time = time.time()
        
        result = await service_desk.handle(
            customer_id=inquiry.customer_id,
            inquiry=inquiry.inquiry,
            context=inquiry.context,
            priority=inquiry.priority.value,
            api_key=x_api_key
        )
        
        # Check for errors
        if "error" in result:
            raise HTTPException(
                status_code=401 if result.get("status") == "unauthorized" else 500,
                detail=result["error"]
            )
        
        # Create response
        response = ServiceResponse(
            request_id=result["request_id"],
            customer_id=inquiry.customer_id,
            response=result["response"],
            agent=result["agent"],
            escalated=result["escalated"],
            resolution_time=result["resolution_time"],
            resolution_path=result["resolution_path"],
            status=result["status"],
            timestamp=datetime.utcnow()
        )
        
        # Notify WebSocket clients
        await broadcast_update({
            "type": "inquiry_handled",
            "data": response.dict()
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/support/status")
async def get_desk_status(
    x_api_key: str = Header(..., description="API key for authentication")
):
    """Get current service desk status."""
    # Verify API key (simplified - in production, check permissions)
    if not service_desk.auth.authenticate(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        status = await service_desk.get_desk_status()
        
        # Add timestamp
        status["timestamp"] = datetime.utcnow().isoformat()
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/support/history/{customer_id}")
async def get_customer_history(
    customer_id: str,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """Get customer interaction history."""
    # Verify API key
    if not service_desk.auth.authenticate(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get history from service desk
    history = service_desk.customer_sessions.get(customer_id, [])
    
    return {
        "customer_id": customer_id,
        "interaction_count": len(history),
        "history": history[-10:]  # Last 10 interactions
    }


@app.get("/escalations/pending")
async def get_pending_escalations(
    reviewer_id: Optional[str] = None,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """Get pending escalation requests."""
    # Verify API key and check escalation permission
    if not service_desk.auth.authenticate(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not service_desk.auth.check_permission(x_api_key, "escalation"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Get pending escalations
        escalations = service_desk.escalation_manager.get_pending_escalations(
            reviewer_id=reviewer_id
        )
        
        # Format for API response
        return {
            "count": len(escalations),
            "escalations": [
                {
                    "request_id": esc.request_id,
                    "title": esc.title,
                    "description": esc.description,
                    "priority": esc.priority.value,
                    "requester": esc.requester_name,
                    "created_at": esc.created_at.isoformat(),
                    "expires_at": esc.expires_at.isoformat() if esc.expires_at else None,
                    "assigned_to": esc.assigned_to
                }
                for esc in escalations
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/escalations/review")
async def review_escalation(
    review: EscalationRequest,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """Review and resolve an escalation."""
    # Verify API key and permissions
    client_info = service_desk.auth.get_client_info(x_api_key)
    if not client_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not service_desk.auth.check_permission(x_api_key, "escalation"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Process escalation review
        success = await service_desk.escalation_manager.process_approval(
            request_id=review.request_id,
            reviewer_id=client_info.get("client_id", "unknown"),
            approved=review.approved,
            comments=review.comments
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to process escalation"
            )
        
        # Notify via WebSocket
        await broadcast_update({
            "type": "escalation_resolved",
            "data": {
                "request_id": review.request_id,
                "approved": review.approved,
                "reviewer": client_info.get("client_name", "Unknown")
            }
        })
        
        return {
            "status": "processed",
            "request_id": review.request_id,
            "decision": "approved" if review.approved else "rejected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/support/configure")
async def configure_desk(
    config: DeskConfiguration,
    x_api_key: str = Header(..., description="API key for authentication")
):
    """Reconfigure the service desk (admin only)."""
    # Check admin permission
    if not service_desk.auth.check_permission(x_api_key, "admin"):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    # In production, this would reconfigure the desk
    # For demo, just return the configuration
    return {
        "status": "configuration_updated",
        "config": config.dict()
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time service desk updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial status
        status = await service_desk.get_desk_status()
        await websocket.send_json({
            "type": "status_update",
            "data": status
        })
        
        # Keep connection alive
        while True:
            # Wait for messages (or timeout for ping)
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle ping
                if message == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send periodic status update
                status = await service_desk.get_desk_status()
                await websocket.send_json({
                    "type": "status_update",
                    "data": status
                })
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception:
        active_connections.remove(websocket)


async def broadcast_update(message: dict):
    """Broadcast update to all WebSocket clients."""
    disconnected = []
    
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CustomerServiceDesk",
        "desk_initialized": service_desk is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get service metrics."""
    if not service_desk:
        return {"error": "Service desk not initialized"}
    
    status = await service_desk.get_desk_status()
    
    return {
        "service_metrics": {
            "total_inquiries": status["total_handled"],
            "escalation_rate": status["escalation_rate"],
            "avg_resolution_time": status["avg_resolution_time"],
            "active_connections": len(active_connections)
        },
        "desk_metrics": status["mesh_status"],
        "escalation_metrics": status["escalation_stats"]
    }


if __name__ == "__main__":
    # Check for API key
    if not any(os.getenv(key) for key in [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"
    ]):
        print("❌ Error: No API key found!")
        print("Please set an API key in your .env file")
    else:
        print("🚀 Starting CustomerServiceDesk API...")
        print("📝 API docs available at: http://localhost:8000/docs")
        print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
        
        # Run the API
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
