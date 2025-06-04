"""
Shared pytest fixtures and configuration for AgentiCraft tests.

This module provides common fixtures and utilities used across all tests.
"""

import asyncio
from typing import AsyncGenerator, Generator
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from pydantic import BaseModel

# Import CompletionResponse with error handling
try:
    from agenticraft.core.types import CompletionResponse
except Exception:
    # If import fails due to settings initialization, create a mock
    from pydantic import BaseModel
    from typing import Dict, List, Any, Optional
    
    class CompletionResponse(BaseModel):
        content: str
        tool_calls: List[Any] = []
        finish_reason: Optional[str] = None
        metadata: Dict[str, Any] = {}
        usage: Optional[Dict[str, int]] = None

# Configure asyncio for tests
pytest_asyncio.fixture_scope = "function"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing agents without API calls."""
    provider = AsyncMock()
    provider.complete.return_value = MagicMock(
        content="Test response",
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )
    provider.stream.return_value = AsyncMock()
    return provider


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    class TestConfig(BaseModel):
        api_key: str = "test-key"
        model: str = "test-model"
        temperature: float = 0.7
        max_tokens: int = 1000

    return TestConfig()


@pytest.fixture
def mock_openai_key(monkeypatch):
    """Mock OpenAI API key for tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    return "test-key-123"


@pytest.fixture
def mock_provider():
    """Mock LLM provider that returns predefined responses."""
    provider = AsyncMock()
    provider.complete = AsyncMock()
    
    # Default response
    default_response = CompletionResponse(
        content="This is a test response",
        tool_calls=[],
        finish_reason="stop",
        usage={"prompt_tokens": 10, "completion_tokens": 20},
        metadata={}
    )
    
    provider.complete.return_value = default_response
    return provider


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for file operations."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest_asyncio.fixture
async def async_mock_tool():
    """Mock async tool for testing."""
    tool = AsyncMock()
    tool.name = "test_tool"
    tool.description = "A test tool"
    tool.execute.return_value = {"result": "success"}
    return tool


@pytest.fixture
def mock_telemetry():
    """Mock telemetry for testing observability."""
    telemetry = MagicMock()
    telemetry.span.return_value.__enter__ = MagicMock()
    telemetry.span.return_value.__exit__ = MagicMock()
    return telemetry


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singletons between tests."""
    # Add any singleton resets here as we implement them
    yield


@pytest.fixture
def clean_settings():
    """Clean up settings and environment variables between tests."""
    # Store original environment variables
    original_env = {}
    env_prefix = "AGENTICRAFT_"
    
    # Save current AGENTICRAFT_* environment variables
    for key in list(os.environ.keys()):
        if key.startswith(env_prefix):
            original_env[key] = os.environ.get(key)
            del os.environ[key]
    
    # Reset settings singleton if it exists
    from agenticraft.core.config import reload_settings
    
    yield
    
    # Clean up any AGENTICRAFT_* variables set during test
    for key in list(os.environ.keys()):
        if key.startswith(env_prefix):
            del os.environ[key]
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
    
    # Force reload settings to clean state
    reload_settings()


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def capture_reasoning():
    """Fixture to capture reasoning traces during tests."""
    traces = []
    
    class ReasoningCapture:
        def add(self, step: str, details: dict = None):
            traces.append({"step": step, "details": details or {}})
        
        def get_traces(self):
            return traces.copy()
        
        def clear(self):
            traces.clear()
    
    return ReasoningCapture()


# Markers for different test types
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "mcp: MCP protocol tests")


def pytest_collection_modifyitems(config, items):
    """Modify collected items to exclude tool instances."""
    # Filter out items that are tool instances mistakenly collected
    from agenticraft.core.tool import BaseTool, FunctionTool
    
    filtered_items = []
    for item in items:
        # Skip if the item is a tool instance
        if hasattr(item, 'obj') and isinstance(item.obj, (BaseTool, FunctionTool)):
            continue
        filtered_items.append(item)
    
    items[:] = filtered_items
