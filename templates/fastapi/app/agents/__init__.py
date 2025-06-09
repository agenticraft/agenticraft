"""Agent endpoints for the API."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agenticraft import Agent, ReasoningAgent, WorkflowAgent
from agenticraft.providers import get_provider
from agenticraft.tools.core import calculator_tool, search_tool


# Request/Response models
class AgentRequest(BaseModel):
    """Base request model for agent interactions."""

    prompt: str = Field(..., description="The prompt for the agent")
    context: dict[str, Any] | None = Field(None, description="Additional context")
    options: dict[str, Any] | None = Field(None, description="Agent-specific options")


class AgentResponse(BaseModel):
    """Base response model for agent interactions."""

    result: str = Field(..., description="The agent's response")
    metadata: dict[str, Any] | None = Field(None, description="Response metadata")


class ReasoningResponse(AgentResponse):
    """Response model with reasoning trace."""

    reasoning: dict[str, Any] = Field(..., description="The agent's reasoning trace")
    thinking_time_ms: int = Field(
        ..., description="Time spent thinking in milliseconds"
    )


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    final_result: str = Field(..., description="Final workflow result")
    steps: list[dict[str, Any]] = Field(..., description="Workflow steps executed")
    total_time_ms: int = Field(..., description="Total execution time in milliseconds")


# Create router
router = APIRouter()

# Initialize provider (you can make this configurable)
provider = get_provider("openai")  # or "anthropic", "ollama", etc.


# Simple agent endpoint
simple_agent = Agent("API Assistant", provider=provider)
simple_agent.add_tool(search_tool)
simple_agent.add_tool(calculator_tool)


@router.post("/simple", response_model=AgentResponse)
async def simple_agent_endpoint(request: AgentRequest):
    """
    Simple agent endpoint for basic conversations.

    This agent has access to search and calculator tools.
    """
    try:
        result = await simple_agent.run(
            request.prompt, context=request.context, **(request.options or {})
        )

        return AgentResponse(
            result=result.answer,
            metadata={
                "agent_name": simple_agent.name,
                "tools_used": [tool.name for tool in result.tools_used],
                "token_count": result.metrics.get("tokens", 0),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Reasoning agent endpoint
reasoning_agent = ReasoningAgent("Reasoning Assistant", provider=provider)
reasoning_agent.add_tool(search_tool)
reasoning_agent.add_tool(calculator_tool)


@router.post("/reasoning", response_model=ReasoningResponse)
async def reasoning_agent_endpoint(request: AgentRequest):
    """
    Reasoning agent endpoint that exposes thinking process.

    This agent provides full transparency into its reasoning.
    """
    try:
        result = await reasoning_agent.think_and_act(
            request.prompt, context=request.context, **(request.options or {})
        )

        # Extract reasoning trace
        reasoning_trace = {
            "goal_analysis": result.reasoning.goal_analysis,
            "steps": [
                {
                    "number": step.number,
                    "description": step.description,
                    "confidence": step.confidence,
                    "tools_used": step.tools,
                    "outcome": step.outcome,
                }
                for step in result.reasoning.steps
            ],
            "final_synthesis": result.reasoning.synthesis,
        }

        return ReasoningResponse(
            result=result.answer,
            reasoning=reasoning_trace,
            thinking_time_ms=result.metrics.thinking_ms,
            metadata={
                "agent_name": reasoning_agent.name,
                "total_steps": len(result.reasoning.steps),
                "confidence_score": result.reasoning.confidence,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Workflow endpoint
@router.post("/workflow", response_model=WorkflowResponse)
async def workflow_endpoint(request: AgentRequest):
    """
    Execute a multi-step workflow.

    This demonstrates how to use WorkflowAgent for complex tasks.
    """
    try:
        # Create workflow agent for the specific task
        workflow_agent = WorkflowAgent(
            "Workflow Executor",
            provider=provider,
            workflow_config=request.options.get("workflow_config", {}),
        )

        # Execute workflow
        result = await workflow_agent.execute_workflow(
            request.prompt, context=request.context
        )

        # Format steps for response
        steps = [
            {
                "name": step.name,
                "status": step.status,
                "duration_ms": step.duration_ms,
                "output": (
                    step.output[:200] + "..." if len(step.output) > 200 else step.output
                ),
            }
            for step in result.steps
        ]

        return WorkflowResponse(
            final_result=result.final_output,
            steps=steps,
            total_time_ms=result.total_duration_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# List available agents
@router.get("/")
async def list_agents():
    """List all available agent endpoints."""
    return {
        "agents": [
            {
                "name": "simple",
                "endpoint": "/agents/simple",
                "description": "Basic conversational agent with tools",
                "tools": ["search", "calculator"],
            },
            {
                "name": "reasoning",
                "endpoint": "/agents/reasoning",
                "description": "Agent that exposes its thinking process",
                "tools": ["search", "calculator"],
                "features": ["reasoning_trace", "confidence_scores"],
            },
            {
                "name": "workflow",
                "endpoint": "/agents/workflow",
                "description": "Multi-step workflow executor",
                "features": ["step_tracking", "parallel_execution"],
            },
        ]
    }


# Agent health check
@router.get("/health")
async def agent_health():
    """Check health of agent endpoints."""
    health_status = {
        "simple_agent": "healthy",
        "reasoning_agent": "healthy",
        "workflow_agent": "healthy",
        "provider": provider.__class__.__name__,
        "tools_available": ["search", "calculator"],
    }

    # You could add actual health checks here
    # For example, testing if the provider is accessible

    return health_status
