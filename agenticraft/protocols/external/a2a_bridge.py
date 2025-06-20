"""
A2A Bridge - Connect AgentiCraft agents to Google's A2A ecosystem.

This module provides:
1. Agent Card generation for A2A discovery
2. HTTP/REST endpoints for A2A communication
3. JSON-RPC support
4. Seamless integration between internal and external agents
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

from agenticraft.protocols.a2a.base import Protocol, ProtocolMessage, MessageType
from agenticraft.protocols.a2a import MeshNetwork
from agenticraft.core.agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class A2AAgentCard:
    """Agent Card for A2A discovery following Google's specification."""
    name: str
    description: str
    capabilities: List[str]
    endpoints: Dict[str, str]
    version: str = "1.0"
    authentication: List[str] = field(default_factory=lambda: ["none"])
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to A2A-compliant JSON format."""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "endpoints": self.endpoints,
            "version": self.version,
            "authentication": self.authentication,
            "metadata": self.metadata
        }


class A2ATaskRequest(BaseModel):
    """A2A task request format."""
    id: str = None
    task: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data):
        if 'id' not in data or data['id'] is None:
            data['id'] = str(uuid4())
        super().__init__(**data)


class A2ATaskResponse(BaseModel):
    """A2A task response format."""
    id: str
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class A2AServer:
    """
    A2A-compliant server that exposes AgentiCraft agents to external systems.
    
    Features:
    - Agent Card endpoint for discovery
    - Task submission and execution
    - Status polling and SSE streaming
    - JSON-RPC support
    """
    
    def __init__(self, agent: Agent, base_url: str, port: int = 8080):
        self.agent = agent
        self.base_url = base_url
        self.port = port
        self.app = FastAPI(title=f"{agent.name} A2A Server")
        
        # Task tracking
        self.tasks: Dict[str, A2ATaskResponse] = {}
        self.task_futures: Dict[str, asyncio.Future] = {}
        
        # Generate agent card
        self.agent_card = self._create_agent_card()
        
        # Setup routes
        self._setup_routes()
    
    def _create_agent_card(self) -> A2AAgentCard:
        """Create A2A agent card from AgentiCraft agent."""
        capabilities = []
        
        # Extract capabilities from agent
        if hasattr(self.agent, 'tools'):
            capabilities.extend([f"tool:{tool}" for tool in self.agent.tools.keys()])
        if hasattr(self.agent, 'capabilities'):
            capabilities.extend(self.agent.capabilities)
        
        return A2AAgentCard(
            name=self.agent.name,
            description=getattr(self.agent, 'description', f'AgentiCraft agent: {self.agent.name}'),
            capabilities=capabilities,
            endpoints={
                "base_url": f"{self.base_url}:{self.port}",
                "agent_card": "/agent-card",
                "tasks": "/tasks",
                "jsonrpc": "/jsonrpc"
            }
        )
    
    def _setup_routes(self):
        """Setup A2A-compliant HTTP endpoints."""
        
        @self.app.get("/agent-card")
        async def get_agent_card():
            """Return agent capabilities and metadata."""
            return self.agent_card.to_dict()
        
        @self.app.post("/tasks")
        async def submit_task(request: A2ATaskRequest):
            """Submit a task for execution."""
            # Create response
            response = A2ATaskResponse(
                id=request.id,
                status="pending"
            )
            self.tasks[request.id] = response
            
            # Execute task asynchronously
            future = asyncio.create_task(self._execute_task(request))
            self.task_futures[request.id] = future
            
            return response.dict()
        
        @self.app.get("/tasks/{task_id}")
        async def get_task_status(task_id: str):
            """Get task status (polling)."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            return self.tasks[task_id].dict()
        
        @self.app.get("/tasks/{task_id}/stream")
        async def stream_task_updates(task_id: str):
            """Stream task updates via SSE."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            async def event_stream():
                while True:
                    task = self.tasks[task_id]
                    yield f"data: {json.dumps(task.dict())}\n\n"
                    
                    if task.status in ["completed", "failed"]:
                        break
                    
                    await asyncio.sleep(0.5)
            
            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream"
            )
        
        @self.app.post("/jsonrpc")
        async def handle_jsonrpc(request: Request):
            """Handle JSON-RPC requests."""
            body = await request.json()
            
            # Validate JSON-RPC format
            if "jsonrpc" not in body or body["jsonrpc"] != "2.0":
                return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}}
            
            method = body.get("method")
            params = body.get("params", {})
            req_id = body.get("id")
            
            try:
                if method == "executeTask":
                    task_req = A2ATaskRequest(task=params)
                    result = await self._execute_task_sync(task_req)
                    return {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": req_id
                    }
                elif method == "getCapabilities":
                    return {
                        "jsonrpc": "2.0",
                        "result": self.agent_card.to_dict(),
                        "id": req_id
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": "Method not found"},
                        "id": req_id
                    }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": str(e)},
                    "id": req_id
                }
    
    async def _execute_task(self, request: A2ATaskRequest):
        """Execute task asynchronously."""
        task_response = self.tasks[request.id]
        
        try:
            # Update status
            task_response.status = "running"
            
            # Execute through agent
            result = await self.agent.execute(
                request.task.get("description", ""),
                context=request.context
            )
            
            # Update response
            task_response.status = "completed"
            task_response.result = result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task_response.status = "failed"
            task_response.error = str(e)
    
    async def _execute_task_sync(self, request: A2ATaskRequest) -> Any:
        """Execute task synchronously for JSON-RPC."""
        return await self.agent.execute(
            request.task.get("description", ""),
            context=request.context
        )
    
    def run(self):
        """Run the A2A server."""
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)


class A2ABridge:
    """
    Bridge between AgentiCraft's internal A2A and Google's external A2A.
    
    This allows:
    1. Exposing internal agents as A2A servers
    2. Connecting to external A2A agents
    3. Protocol translation and routing
    """
    
    def __init__(self, internal_protocol: Protocol):
        self.internal_protocol = internal_protocol
        self.external_clients: Dict[str, httpx.AsyncClient] = {}
        self.exposed_servers: Dict[str, A2AServer] = {}
    
    async def expose_agent(self, agent: Agent, port: int) -> A2AServer:
        """Expose an AgentiCraft agent as an A2A server."""
        base_url = f"http://localhost"
        server = A2AServer(agent, base_url, port)
        
        # Store reference
        self.exposed_servers[agent.name] = server
        
        # Register in internal protocol
        if isinstance(self.internal_protocol, MeshNetwork):
            self.internal_protocol.register_capability(f"a2a:{agent.name}")
        
        return server
    
    async def connect_external_agent(self, agent_url: str) -> Dict[str, Any]:
        """Connect to an external A2A agent."""
        client = httpx.AsyncClient()
        self.external_clients[agent_url] = client
        
        # Fetch agent card
        response = await client.get(f"{agent_url}/agent-card")
        agent_card = response.json()
        
        # Register capabilities in internal protocol
        if isinstance(self.internal_protocol, MeshNetwork):
            for capability in agent_card.get("capabilities", []):
                self.internal_protocol.register_capability(
                    f"external:{agent_card['name']}:{capability}"
                )
        
        return agent_card
    
    async def route_task(self, task: str, capability: str) -> Any:
        """Route task to appropriate agent (internal or external)."""
        # Check if it's an external capability
        if capability.startswith("external:"):
            parts = capability.split(":", 2)
            agent_name = parts[1]
            actual_capability = parts[2] if len(parts) > 2 else ""
            
            # Find external agent
            for url, client in self.external_clients.items():
                # Submit task to external agent
                task_request = {
                    "task": {
                        "description": task,
                        "capability": actual_capability
                    }
                }
                
                response = await client.post(
                    f"{url}/tasks",
                    json=task_request
                )
                task_data = response.json()
                
                # Poll for result
                while task_data["status"] in ["pending", "running"]:
                    await asyncio.sleep(1)
                    status_response = await client.get(
                        f"{url}/tasks/{task_data['id']}"
                    )
                    task_data = status_response.json()
                
                if task_data["status"] == "completed":
                    return task_data["result"]
                else:
                    raise RuntimeError(f"Task failed: {task_data.get('error')}")
        
        else:
            # Route internally
            return await self.internal_protocol.execute_distributed(
                task=task,
                capability_required=capability,
                strategy="auto"
            )
    
    async def create_hybrid_workflow(self, name: str) -> 'HybridA2AWorkflow':
        """Create a workflow that can use both internal and external agents."""
        from agenticraft.workflows.a2a_integration import A2AWorkflow
        
        class HybridA2AWorkflow(A2AWorkflow):
            def __init__(self, bridge: A2ABridge):
                super().__init__(name, coordination_mode="hybrid")
                self.bridge = bridge
            
            async def execute_with_external(
                self,
                task: str,
                prefer_external: bool = False
            ) -> Any:
                # Get all capabilities (internal + external)
                all_capabilities = set()
                
                # Internal capabilities
                for node in self.protocol.nodes.values():
                    all_capabilities.update(node.capabilities)
                
                # External capabilities
                all_capabilities.update([
                    cap for cap in self.protocol.nodes[self.protocol.node_id].capabilities
                    if cap.startswith("external:")
                ])
                
                # Select capability based on preference
                if prefer_external:
                    external_caps = [c for c in all_capabilities if c.startswith("external:")]
                    if external_caps:
                        return await self.bridge.route_task(task, external_caps[0])
                
                # Default to internal
                internal_caps = [c for c in all_capabilities if not c.startswith("external:")]
                if internal_caps:
                    return await self.bridge.route_task(task, internal_caps[0])
                
                raise RuntimeError("No capable agents found")
        
        return HybridA2AWorkflow(self)
