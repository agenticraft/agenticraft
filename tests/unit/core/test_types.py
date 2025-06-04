"""Unit tests for types module.

This module tests all the type definitions and data models.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import pytest
from pydantic import ValidationError

from agenticraft.core.types import (
    MessageRole,
    Message,
    ToolCall,
    ToolResult,
    ToolDefinition,
    ToolParameter,
    CompletionResponse,
)


class TestMessageRole:
    """Test MessageRole enum."""
    
    def test_message_roles(self):
        """Test all message role values."""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.TOOL == "tool"
    
    def test_message_role_values(self):
        """Test getting enum values."""
        roles = [role.value for role in MessageRole]
        assert "system" in roles
        assert "user" in roles
        assert "assistant" in roles
        assert "tool" in roles


class TestMessage:
    """Test Message model."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(
            role=MessageRole.USER,
            content="Hello, assistant!"
        )
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, assistant!"
        assert msg.metadata == {}
        assert msg.tool_calls is None
        assert isinstance(msg.created_at, datetime)
    
    def test_message_with_metadata(self):
        """Test message with metadata."""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="I can help with that.",
            metadata={"confidence": 0.95, "topic": "general"}
        )
        
        assert msg.metadata["confidence"] == 0.95
        assert msg.metadata["topic"] == "general"
    
    def test_message_with_tool_calls(self):
        """Test message with tool calls."""
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": '{"expression": "2 + 2"}'
                }
            }
        ]
        
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Let me calculate that for you.",
            tool_calls=tool_calls
        )
        
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["function"]["name"] == "calculator"
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = Message(
            role=MessageRole.USER,
            content="Test message",
            metadata={"key": "value"}
        )
        
        msg_dict = msg.to_dict()
        
        assert msg_dict["role"] == "user"
        assert msg_dict["content"] == "Test message"
        # Metadata is not included in to_dict by default
    
    def test_message_to_dict_with_tool_calls(self):
        """Test converting message with tool calls to dict."""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Using tool",
            tool_calls=[
                {"id": "1", "type": "function", "function": {"name": "tool", "arguments": "{}"}}
            ]
        )
        
        msg_dict = msg.to_dict()
        
        assert "tool_calls" in msg_dict
        assert len(msg_dict["tool_calls"]) == 1
    
    def test_message_validation(self):
        """Test message validation."""
        # Invalid role
        with pytest.raises(ValidationError):
            Message(role="invalid", content="Test")
        
        # Missing content
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER)


class TestToolCall:
    """Test ToolCall model."""
    
    def test_tool_call_creation(self):
        """Test creating a tool call."""
        tool_call = ToolCall(
            id="call_123",
            name="search",
            arguments={"query": "Python tutorials"}
        )
        
        assert tool_call.id == "call_123"
        assert tool_call.name == "search"
        assert tool_call.arguments["query"] == "Python tutorials"
    
    def test_tool_call_auto_id(self):
        """Test tool call with auto-generated ID."""
        # Arguments can be passed as string and will be parsed
        tool_call = ToolCall(
            name="calculator",
            arguments='{"a": 5, "b": 3}'
        )
        
        assert tool_call.arguments == {"a": 5, "b": 3}
    
    def test_tool_call_string_arguments(self):
        """Test tool call with string arguments."""
        tool_call = ToolCall(
            name="search",
            arguments='{"query": "test"}'
        )
        
        # Should parse JSON string to dict
        assert tool_call.arguments["query"] == "test"
    
    def test_tool_call_invalid_json_arguments(self):
        """Test tool call with invalid JSON."""
        tool_call = ToolCall(
            name="search",
            arguments="plain text query"
        )
        
        # Should wrap in input key
        assert tool_call.arguments == {"input": "plain text query"}


class TestToolResult:
    """Test ToolResult model."""
    
    def test_tool_result_success(self):
        """Test successful tool result."""
        result = ToolResult(
            tool_call_id="call_123",
            result={"temperature": 72, "condition": "sunny"}
        )
        
        assert result.tool_call_id == "call_123"
        assert result.result["temperature"] == 72
        assert result.error is None
    
    def test_tool_result_with_error(self):
        """Test tool result with error."""
        result = ToolResult(
            tool_call_id="call_456",
            result=None,
            error="API rate limit exceeded"
        )
        
        assert result.tool_call_id == "call_456"
        assert result.result is None
        assert result.error == "API rate limit exceeded"
    
    def test_tool_result_json_serializable(self):
        """Test that tool result is JSON serializable."""
        result = ToolResult(
            tool_call_id="call_789",
            result={"data": [1, 2, 3], "status": "ok"}
        )
        
        # Should be able to JSON serialize
        json_str = json.dumps(result.model_dump())
        parsed = json.loads(json_str)
        
        assert parsed["tool_call_id"] == "call_789"
        assert parsed["result"]["data"] == [1, 2, 3]


class TestToolParameter:
    """Test ToolParameter model."""
    
    def test_tool_parameter_basic(self):
        """Test basic tool parameter."""
        param = ToolParameter(
            name="temperature",
            type="number",
            description="Temperature in Celsius",
            required=True
        )
        
        assert param.name == "temperature"
        assert param.type == "number"
        assert param.description == "Temperature in Celsius"
        assert param.required is True
        assert param.default is None
        assert param.enum is None
    
    def test_tool_parameter_with_default(self):
        """Test tool parameter with default value."""
        param = ToolParameter(
            name="format",
            type="string",
            description="Output format",
            required=False,
            default="json"
        )
        
        assert param.required is False
        assert param.default == "json"
    
    def test_tool_parameter_with_enum(self):
        """Test tool parameter with enum values."""
        param = ToolParameter(
            name="unit",
            type="string",
            description="Temperature unit",
            required=True,
            enum=["celsius", "fahrenheit", "kelvin"]
        )
        
        assert param.enum == ["celsius", "fahrenheit", "kelvin"]



class TestToolDefinition:
    """Test ToolDefinition model."""
    
    def test_tool_definition_basic(self):
        """Test basic tool definition."""
        tool_def = ToolDefinition(
            name="calculator",
            description="Perform mathematical calculations",
            parameters=[]
        )
        
        assert tool_def.name == "calculator"
        assert tool_def.description == "Perform mathematical calculations"
        assert tool_def.parameters == []
    
    def test_tool_definition_with_parameters(self):
        """Test tool definition with parameters."""
        params = [
            ToolParameter(
                name="expression",
                type="string",
                description="Math expression to evaluate",
                required=True
            ),
            ToolParameter(
                name="precision",
                type="integer",
                description="Decimal places",
                required=False,
                default=2
            )
        ]
        
        tool_def = ToolDefinition(
            name="calculator",
            description="Calculate math expressions",
            parameters=params
        )
        
        assert len(tool_def.parameters) == 2
        assert tool_def.parameters[0].name == "expression"
        assert tool_def.parameters[1].default == 2
    
    def test_tool_definition_to_openai_schema(self):
        """Test converting to OpenAI function schema."""
        tool_def = ToolDefinition(
            name="weather",
            description="Get weather information",
            parameters=[
                ToolParameter(
                    name="location",
                    type="string",
                    description="City name",
                    required=True
                ),
                ToolParameter(
                    name="units",
                    type="string",
                    description="Temperature units",
                    required=False,
                    default="celsius",
                    enum=["celsius", "fahrenheit"]
                )
            ]
        )
        
        schema = tool_def.to_openai_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "weather"
        assert schema["function"]["description"] == "Get weather information"
        assert "parameters" in schema["function"]
        
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "location" in params["properties"]
        assert "units" in params["properties"]
        assert params["required"] == ["location"]


class TestCompletionResponse:
    """Test CompletionResponse model."""
    
    def test_completion_response_basic(self):
        """Test basic completion response."""
        response = CompletionResponse(
            content="Hello, how can I help you?"
        )
        
        assert response.content == "Hello, how can I help you?"
        assert response.tool_calls == []
        assert response.finish_reason is None
        assert response.metadata == {}
        assert response.usage is None
    
    def test_completion_response_with_tool_calls(self):
        """Test completion response with tool calls."""
        tool_calls = [
            ToolCall(name="search", arguments={"query": "weather"}),
            ToolCall(name="calculator", arguments={"expression": "2+2"})
        ]
        
        response = CompletionResponse(
            content="I'll search for that and calculate.",
            tool_calls=tool_calls
        )
        
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "search"
        assert response.tool_calls[1].name == "calculator"
    
    def test_completion_response_with_metadata(self):
        """Test completion response with metadata."""
        response = CompletionResponse(
            content="Response text",
            finish_reason="stop",
            metadata={"model": "gpt-4", "temperature": 0.7},
            usage={"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}
        )
        
        assert response.finish_reason == "stop"
        assert response.metadata["model"] == "gpt-4"
        assert response.usage["total_tokens"] == 70

