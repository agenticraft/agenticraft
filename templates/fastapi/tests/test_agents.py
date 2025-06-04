"""Tests for agent endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


class TestAgentEndpoints:
    """Test suite for agent endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Provide authentication headers."""
        return {"X-API-Key": "demo-key-123"}
    
    def test_list_agents(self, auth_headers):
        """Test listing available agents."""
        response = client.get("/agents/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 3
        
        # Check agent structure
        for agent in data["agents"]:
            assert "name" in agent
            assert "endpoint" in agent
            assert "description" in agent
    
    @patch("app.agents.simple_agent.run")
    async def test_simple_agent(self, mock_run, auth_headers):
        """Test simple agent endpoint."""
        # Mock agent response
        mock_result = AsyncMock()
        mock_result.answer = "Hello! I'm doing well, thank you for asking."
        mock_result.tools_used = []
        mock_result.metrics = {"tokens": 50}
        mock_run.return_value = mock_result
        
        response = client.post(
            "/agents/simple",
            headers=auth_headers,
            json={
                "prompt": "Hello, how are you?",
                "context": {"user_id": "test-user"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "result" in data
        assert data["result"] == "Hello! I'm doing well, thank you for asking."
        assert "metadata" in data
        assert data["metadata"]["agent_name"] == "API Assistant"
    
    @patch("app.agents.reasoning_agent.think_and_act")
    async def test_reasoning_agent(self, mock_think_and_act, auth_headers):
        """Test reasoning agent endpoint."""
        # Mock reasoning response
        mock_result = AsyncMock()
        mock_result.answer = "To plan a sustainable city, we need to consider..."
        mock_result.reasoning = AsyncMock()
        mock_result.reasoning.goal_analysis = "Understanding sustainable city planning"
        mock_result.reasoning.steps = [
            AsyncMock(
                number=1,
                description="Analyze current challenges",
                confidence=0.9,
                tools=["search"],
                outcome="Identified key sustainability factors"
            )
        ]
        mock_result.reasoning.synthesis = "A comprehensive approach is needed"
        mock_result.reasoning.confidence = 0.85
        mock_result.metrics = {"thinking_ms": 1500}
        
        mock_think_and_act.return_value = mock_result
        
        response = client.post(
            "/agents/reasoning",
            headers=auth_headers,
            json={
                "prompt": "Plan a sustainable city",
                "options": {"max_steps": 5}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "result" in data
        assert "reasoning" in data
        assert "thinking_time_ms" in data
        assert data["thinking_time_ms"] == 1500
        
        # Check reasoning structure
        reasoning = data["reasoning"]
        assert "goal_analysis" in reasoning
        assert "steps" in reasoning
        assert len(reasoning["steps"]) >= 1
        assert "final_synthesis" in reasoning
    
    def test_missing_auth(self):
        """Test endpoint without authentication."""
        response = client.post(
            "/agents/simple",
            json={"prompt": "Hello"}
        )
        assert response.status_code == 401
        assert "Missing API key" in response.json()["error"]
    
    def test_invalid_auth(self):
        """Test endpoint with invalid authentication."""
        response = client.post(
            "/agents/simple",
            headers={"X-API-Key": "invalid-key"},
            json={"prompt": "Hello"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["error"]
    
    def test_agent_health(self, auth_headers):
        """Test agent health endpoint."""
        response = client.get("/agents/health", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["simple_agent"] == "healthy"
        assert data["reasoning_agent"] == "healthy"
        assert data["workflow_agent"] == "healthy"
        assert "provider" in data
        assert "tools_available" in data
    
    @pytest.mark.parametrize("prompt", [
        "",
        " ",
        None,
    ])
    def test_invalid_prompt(self, prompt, auth_headers):
        """Test with invalid prompts."""
        response = client.post(
            "/agents/simple",
            headers=auth_headers,
            json={"prompt": prompt}
        )
        assert response.status_code == 422  # Validation error
    
    def test_rate_limiting(self, auth_headers):
        """Test rate limiting functionality."""
        # Make multiple requests
        for i in range(5):
            response = client.post(
                "/agents/simple",
                headers=auth_headers,
                json={"prompt": f"Test {i}"}
            )
            
            # Check rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
