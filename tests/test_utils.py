"""
Test utilities and helpers for AgentiCraft tests.

Provides common testing utilities, assertion helpers, and test data generators.
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAgent:
    """A simple test agent for testing purposes."""
    
    def __init__(self, name: str = "test_agent"):
        self.name = name
        self.memory = []
        self.tools = {}
        self.reasoning_traces = []
    
    async def think(self, prompt: str) -> str:
        """Simulate thinking with reasoning traces."""
        self.reasoning_traces.append({
            "type": "thinking",
            "prompt": prompt,
            "timestamp": "2025-01-01T00:00:00Z"
        })
        return f"Thought about: {prompt}"
    
    async def act(self, action: str) -> Dict[str, Any]:
        """Simulate taking an action."""
        self.reasoning_traces.append({
            "type": "action",
            "action": action,
            "timestamp": "2025-01-01T00:00:01Z"
        })
        return {"action": action, "result": "success"}


def create_mock_tool(name: str = "test_tool", 
                    async_tool: bool = True) -> MagicMock:
    """
    Create a mock tool for testing.
    
    Args:
        name: Tool name
        async_tool: Whether the tool should be async
        
    Returns:
        Mock tool object
    """
    MockClass = AsyncMock if async_tool else MagicMock
    tool = MockClass()
    tool.name = name
    tool.description = f"A test tool named {name}"
    tool.parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Test input"}
        },
        "required": ["input"]
    }
    
    if async_tool:
        tool.execute.return_value = {"result": f"{name} executed"}
    else:
        tool.execute = MagicMock(return_value={"result": f"{name} executed"})
    
    return tool


def assert_reasoning_trace(trace: Dict[str, Any], 
                          expected_type: str,
                          expected_fields: List[str] = None):
    """
    Assert a reasoning trace has expected structure.
    
    Args:
        trace: The reasoning trace to check
        expected_type: Expected trace type
        expected_fields: Additional fields that should be present
    """
    assert trace["type"] == expected_type
    assert "timestamp" in trace
    
    if expected_fields:
        for field in expected_fields:
            assert field in trace, f"Missing field: {field}"


def create_test_workflow_spec() -> Dict[str, Any]:
    """Create a test workflow specification."""
    return {
        "name": "test_workflow",
        "steps": [
            {
                "id": "step1",
                "name": "First Step",
                "tool": "test_tool",
                "inputs": {"input": "test"},
                "depends_on": []
            },
            {
                "id": "step2", 
                "name": "Second Step",
                "tool": "test_tool_2",
                "inputs": {"input": "{step1.result}"},
                "depends_on": ["step1"]
            }
        ]
    }


async def async_return(value: Any):
    """Helper to return a value asynchronously."""
    return value


class MemoryStore:
    """Simple in-memory store for testing memory implementations."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
    
    async def get(self, key: str) -> Any:
        return self.data.get(key)
    
    async def set(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    async def delete(self, key: str) -> None:
        self.data.pop(key, None)
    
    async def clear(self) -> None:
        self.data.clear()
    
    async def keys(self) -> List[str]:
        return list(self.data.keys())


def compare_json(actual: Any, expected: Any, ignore_keys: List[str] = None):
    """
    Compare JSON-like structures, optionally ignoring certain keys.
    
    Args:
        actual: Actual value
        expected: Expected value  
        ignore_keys: Keys to ignore in comparison
    """
    ignore_keys = ignore_keys or []
    
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in expected:
            if key not in ignore_keys:
                assert key in actual, f"Missing key: {key}"
                compare_json(actual[key], expected[key], ignore_keys)
    elif isinstance(expected, list) and isinstance(actual, list):
        assert len(actual) == len(expected), "List lengths don't match"
        for i, (a, e) in enumerate(zip(actual, expected)):
            compare_json(a, e, ignore_keys)
    else:
        assert actual == expected, f"Values don't match: {actual} != {expected}"


# Test data generators
def generate_test_messages(count: int = 5) -> List[Dict[str, str]]:
    """Generate test conversation messages."""
    messages = []
    for i in range(count):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({
            "role": role,
            "content": f"Test message {i} from {role}"
        })
    return messages
