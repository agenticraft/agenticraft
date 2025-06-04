"""Comprehensive tests for types module to achieve >95% coverage."""

import json
from datetime import datetime
import time

import pytest

from agenticraft.core.types import (
    ToolCall, ToolResult, MessageRole, Message,
    CompletionResponse, ToolParameter, ToolDefinition
)


class TestToolCall:
    """Test ToolCall model."""
    
    def test_tool_call_creation(self):
        """Test creating a tool call."""
        tool_call = ToolCall(
            name="calculator",
            arguments={"x": 5, "y": 3}
        )
        
        assert tool_call.name == "calculator"
        assert tool_call.arguments == {"x": 5, "y": 3}
        assert isinstance(tool_call.id, str)
        assert len(tool_call.id) > 0
    
    def test_tool_call_with_custom_id(self):
        """Test tool call with custom ID."""
        tool_call = ToolCall(
            id="custom_id_123",
            name="search",
            arguments={"query": "test"}
        )
        
        assert tool_call.id == "custom_id_123"
    
    def test_validate_arguments_from_string(self):
        """Test arguments validation from JSON string."""
        tool_call = ToolCall(
            name="test",
            arguments='{"key": "value", "number": 42}'
        )
        
        assert tool_call.arguments == {"key": "value", "number": 42}
        assert isinstance(tool_call.arguments, dict)
    
    def test_validate_arguments_invalid_json(self):
        """Test arguments validation with invalid JSON."""
        tool_call = ToolCall(
            name="test",
            arguments="not a json string"
        )
        
        # Should wrap in input key
        assert tool_call.arguments == {"input": "not a json string"}
    
    def test_validate_arguments_already_dict(self):
        """Test arguments validation when already a dict."""
        args = {"x": 1, "y": 2}
        tool_call = ToolCall(
            name="test",
            arguments=args
        )
        
        assert tool_call.arguments == args


class TestToolResult:
    """Test ToolResult model."""
    
    def test_tool_result_success(self):
        """Test successful tool result."""
        result = ToolResult(
            tool_call_id="call_123",
            result={"answer": 42}
        )
        
        assert result.tool_call_id == "call_123"
        assert result.result == {"answer": 42}
        assert result.error is None
        assert result.success is True
    
    def test_tool_result_with_error(self):
        """Test tool result with error."""
        result = ToolResult(
            tool_call_id="call_456",
            result=None,
            error="Division by zero"
        )
        
        assert result.tool_call_id == "call_456"
        assert result.result is None
        assert result.error == "Division by zero"
        assert result.success is False
    
    def test_tool_result_various_types(self):
        """Test tool result with various result types."""
        # String result
        result1 = ToolResult(tool_call_id="1", result="string result")
        assert result1.result == "string result"
        assert result1.success is True
        
        # List result
        result2 = ToolResult(tool_call_id="2", result=[1, 2, 3])
        assert result2.result == [1, 2, 3]
        
        # None result with no error (still successful)
        result3 = ToolResult(tool_call_id="3", result=None)
        assert result3.result is None
        assert result3.error is None
        assert result3.success is True


class TestMessageRole:
    """Test MessageRole enum."""
    
    def test_message_roles(self):
        """Test all message role values."""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.TOOL == "tool"
    
    def test_message_role_string_conversion(self):
        """Test string conversion of roles."""
        assert str(MessageRole.SYSTEM) == "system"
        assert str(MessageRole.USER) == "user"
        assert str(MessageRole.ASSISTANT) == "assistant"
        assert str(MessageRole.TOOL) == "tool"
    
    def test_message_role_comparison(self):
        """Test role comparisons."""
        assert MessageRole.USER == MessageRole.USER
        assert MessageRole.USER != MessageRole.ASSISTANT
        # String enums in Python DO equal their string values
        assert MessageRole.SYSTEM == "system"  # This is True for string enums
        assert MessageRole.USER == "user"
        assert str(MessageRole.SYSTEM) == "system"


class TestMessage:
    """Test Message model."""
    
    def test_message_creation_basic(self):
        """Test basic message creation."""
        msg = Message(
            role=MessageRole.USER,
            content="Hello, assistant!"
        )
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, assistant!"
        assert msg.tool_calls is None
        assert msg.metadata == {}
        assert isinstance(msg.created_at, datetime)
    
    def test_message_with_tool_calls(self):
        """Test message with tool calls."""
        tool_calls = [
            {"id": "1", "name": "search", "arguments": {"q": "test"}},
            {"id": "2", "name": "calculator", "arguments": {"expr": "2+2"}}
        ]
        
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="I'll help you with that.",
            tool_calls=tool_calls
        )
        
        assert msg.tool_calls == tool_calls
        assert len(msg.tool_calls) == 2
    
    def test_message_with_metadata(self):
        """Test message with metadata."""
        metadata = {
            "model": "gpt-4",
            "temperature": 0.7,
            "custom_field": "value"
        }
        
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Response",
            metadata=metadata
        )
        
        assert msg.metadata == metadata
        assert msg.metadata["model"] == "gpt-4"
    
    def test_message_to_dict_basic(self):
        """Test converting message to dict."""
        msg = Message(
            role=MessageRole.USER,
            content="Test message"
        )
        
        data = msg.to_dict()
        
        assert data == {
            "role": "user",
            "content": "Test message"
        }
    
    def test_message_to_dict_with_tool_calls(self):
        """Test converting message with tool calls to dict."""
        tool_calls = [{"id": "1", "name": "test"}]
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Using tools",
            tool_calls=tool_calls
        )
        
        data = msg.to_dict()
        
        assert data["role"] == "assistant"
        assert data["content"] == "Using tools"
        assert data["tool_calls"] == tool_calls
    
    def test_message_to_dict_tool_message(self):
        """Test converting tool message to dict."""
        msg = Message(
            role=MessageRole.TOOL,
            content="Tool result",
            metadata={"tool_call_id": "call_123"}
        )
        
        data = msg.to_dict()
        
        assert data["role"] == "tool"
        assert data["content"] == "Tool result"
        assert data["tool_call_id"] == "call_123"
    
    def test_message_to_dict_tool_without_id(self):
        """Test tool message without tool_call_id."""
        msg = Message(
            role=MessageRole.TOOL,
            content="Tool result",
            metadata={"other": "data"}
        )
        
        data = msg.to_dict()
        
        assert data["role"] == "tool"
        assert data["content"] == "Tool result"
        assert "tool_call_id" not in data


class TestCompletionResponse:
    """Test CompletionResponse model."""
    
    def test_completion_response_basic(self):
        """Test basic completion response."""
        response = CompletionResponse(
            content="This is the response"
        )
        
        assert response.content == "This is the response"
        assert response.tool_calls == []
        assert response.finish_reason is None
        assert response.metadata == {}
        assert response.usage is None
    
    def test_completion_response_full(self):
        """Test completion response with all fields."""
        tool_calls = [
            ToolCall(name="search", arguments={"q": "test"})
        ]
        
        response = CompletionResponse(
            content="Let me search for that",
            tool_calls=tool_calls,
            finish_reason="tool_calls",
            metadata={"model": "gpt-4"},
            usage={"prompt_tokens": 50, "completion_tokens": 20}
        )
        
        assert response.content == "Let me search for that"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "search"
        assert response.finish_reason == "tool_calls"
        assert response.metadata["model"] == "gpt-4"
        assert response.usage["prompt_tokens"] == 50


class TestToolParameter:
    """Test ToolParameter model."""
    
    def test_tool_parameter_required(self):
        """Test required tool parameter."""
        param = ToolParameter(
            name="query",
            type="string",
            description="Search query"
        )
        
        assert param.name == "query"
        assert param.type == "string"
        assert param.description == "Search query"
        assert param.required is True
        assert param.default is None
        assert param.enum is None
    
    def test_tool_parameter_optional(self):
        """Test optional tool parameter with default."""
        param = ToolParameter(
            name="limit",
            type="integer",
            description="Number of results",
            required=False,
            default=10
        )
        
        assert param.required is False
        assert param.default == 10
    
    def test_tool_parameter_with_enum(self):
        """Test tool parameter with enum values."""
        param = ToolParameter(
            name="format",
            type="string",
            description="Output format",
            enum=["json", "xml", "csv"]
        )
        
        assert param.enum == ["json", "xml", "csv"]


class TestToolDefinition:
    """Test ToolDefinition model."""
    
    def test_tool_definition_basic(self):
        """Test basic tool definition."""
        params = [
            ToolParameter(name="x", type="number", description="First number"),
            ToolParameter(name="y", type="number", description="Second number")
        ]
        
        tool_def = ToolDefinition(
            name="add",
            description="Add two numbers",
            parameters=params
        )
        
        assert tool_def.name == "add"
        assert tool_def.description == "Add two numbers"
        assert len(tool_def.parameters) == 2
    
    def test_to_openai_schema_basic(self):
        """Test converting to OpenAI function schema."""
        params = [
            ToolParameter(name="query", type="string", description="Search query")
        ]
        
        tool_def = ToolDefinition(
            name="search",
            description="Search the web",
            parameters=params
        )
        
        schema = tool_def.to_openai_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "search"
        assert schema["function"]["description"] == "Search the web"
        assert schema["function"]["parameters"]["type"] == "object"
        assert schema["function"]["parameters"]["properties"]["query"]["type"] == "string"
        assert schema["function"]["parameters"]["properties"]["query"]["description"] == "Search query"
        assert schema["function"]["parameters"]["required"] == ["query"]
    
    def test_to_openai_schema_complex(self):
        """Test converting complex tool to OpenAI schema."""
        params = [
            ToolParameter(
                name="text",
                type="string",
                description="Text to analyze",
                required=True
            ),
            ToolParameter(
                name="language",
                type="string",
                description="Language code",
                required=False,
                default="en",
                enum=["en", "es", "fr", "de"]
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="Maximum summary length",
                required=False,
                default=100
            )
        ]
        
        tool_def = ToolDefinition(
            name="summarize",
            description="Summarize text",
            parameters=params
        )
        
        schema = tool_def.to_openai_schema()
        
        # Check structure
        assert schema["type"] == "function"
        func = schema["function"]
        assert func["name"] == "summarize"
        
        # Check parameters
        props = func["parameters"]["properties"]
        assert "text" in props
        assert "language" in props
        assert "max_length" in props
        
        # Check required
        assert func["parameters"]["required"] == ["text"]
        
        # Check enum
        assert props["language"]["enum"] == ["en", "es", "fr", "de"]
        
        # Check defaults
        assert props["language"]["default"] == "en"
        assert props["max_length"]["default"] == 100
    
    def test_to_openai_schema_no_params(self):
        """Test tool with no parameters."""
        tool_def = ToolDefinition(
            name="get_time",
            description="Get current time",
            parameters=[]
        )
        
        schema = tool_def.to_openai_schema()
        
        assert schema["function"]["parameters"]["properties"] == {}
        assert schema["function"]["parameters"]["required"] == []


class TestTypesIntegration:
    """Integration tests for types working together."""
    
    def test_tool_flow(self):
        """Test complete tool flow with types."""
        # Define a tool
        params = [
            ToolParameter(name="city", type="string", description="City name")
        ]
        tool_def = ToolDefinition(
            name="get_weather",
            description="Get weather for a city",
            parameters=params
        )
        
        # Create a tool call
        tool_call = ToolCall(
            id="call_weather_123",
            name=tool_def.name,
            arguments={"city": "London"}
        )
        
        # Create a message with tool call
        message = Message(
            role=MessageRole.ASSISTANT,
            content="I'll check the weather for you.",
            tool_calls=[tool_call.model_dump()]
        )
        
        # Create tool result
        tool_result = ToolResult(
            tool_call_id=tool_call.id,
            result={"temperature": 15, "conditions": "cloudy"}
        )
        
        # Create tool response message
        tool_message = Message(
            role=MessageRole.TOOL,
            content=json.dumps(tool_result.result),
            metadata={"tool_call_id": tool_result.tool_call_id}
        )
        
        # Verify the flow
        assert message.tool_calls[0]["id"] == tool_call.id
        assert tool_result.success is True
        assert tool_message.to_dict()["tool_call_id"] == tool_call.id
    
    def test_completion_with_tools(self):
        """Test completion response with tool calls."""
        # Create tool calls
        calls = [
            ToolCall(name="search", arguments={"q": "weather"}),
            ToolCall(name="calculator", arguments={"expr": "15 * 1.8 + 32"})
        ]
        
        # Create completion response
        response = CompletionResponse(
            content="Let me search for weather and convert the temperature.",
            tool_calls=calls,
            finish_reason="tool_calls",
            usage={"prompt_tokens": 30, "completion_tokens": 15}
        )
        
        # Verify
        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "search"
        assert response.tool_calls[1].arguments["expr"] == "15 * 1.8 + 32"
        assert response.finish_reason == "tool_calls"
