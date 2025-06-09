"""Tests for MCP types and data structures."""

import pytest

from agenticraft.protocols.mcp.types import (
    MCPCapability,
    MCPConnectionConfig,
    MCPError,
    MCPErrorCode,
    MCPMethod,
    MCPRequest,
    MCPResponse,
    MCPServerInfo,
    MCPTool,
    MCPToolCall,
    MCPToolParameter,
    MCPToolResult,
)


class TestMCPTypes:
    """Test MCP type definitions."""

    def test_mcp_request_creation(self):
        """Test creating MCP requests."""
        # Basic request
        request = MCPRequest(method=MCPMethod.LIST_TOOLS)
        assert request.jsonrpc == "2.0"
        assert request.method == MCPMethod.LIST_TOOLS
        assert request.params is None
        assert request.id is not None

        # Request with params
        request = MCPRequest(
            method=MCPMethod.CALL_TOOL,
            params={"tool": "calculate", "arguments": {"expression": "2+2"}},
            id="test-123",
        )
        assert request.params == {
            "tool": "calculate",
            "arguments": {"expression": "2+2"},
        }
        assert request.id == "test-123"

    def test_mcp_request_to_dict(self):
        """Test converting request to dictionary."""
        request = MCPRequest(
            method=MCPMethod.LIST_TOOLS, params={"category": "math"}, id=123
        )

        data = request.to_dict()
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "tools/list"
        assert data["params"] == {"category": "math"}
        assert data["id"] == 123

    def test_mcp_response_creation(self):
        """Test creating MCP responses."""
        # Success response
        response = MCPResponse(id="test-123", result={"tools": ["calculate", "search"]})
        assert response.jsonrpc == "2.0"
        assert response.id == "test-123"
        assert response.result == {"tools": ["calculate", "search"]}
        assert not response.is_error

        # Error response
        error = MCPError(code=MCPErrorCode.METHOD_NOT_FOUND, message="Unknown method")
        response = MCPResponse(id="test-123", error=error)
        assert response.is_error
        assert response.error.code == MCPErrorCode.METHOD_NOT_FOUND

    def test_mcp_tool_parameter(self):
        """Test MCP tool parameter."""
        param = MCPToolParameter(
            name="expression",
            type="string",
            description="Math expression to evaluate",
            required=True,
        )

        schema = param.to_json_schema()
        assert schema["type"] == "string"
        assert schema["description"] == "Math expression to evaluate"
        assert "default" not in schema

        # With enum
        param = MCPToolParameter(
            name="operation",
            type="string",
            enum=["add", "subtract", "multiply"],
            default="add",
        )
        schema = param.to_json_schema()
        assert schema["enum"] == ["add", "subtract", "multiply"]
        assert schema["default"] == "add"

    def test_mcp_tool(self):
        """Test MCP tool definition."""
        tool = MCPTool(
            name="calculate",
            description="Evaluate mathematical expressions",
            parameters=[
                MCPToolParameter(name="expression", type="string", required=True)
            ],
        )

        schema = tool.to_json_schema()
        assert schema["name"] == "calculate"
        assert schema["description"] == "Evaluate mathematical expressions"
        assert "inputSchema" in schema
        assert schema["inputSchema"]["type"] == "object"
        assert "expression" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["required"] == ["expression"]

    def test_mcp_server_info(self):
        """Test MCP server info."""
        info = MCPServerInfo(
            name="Test Server",
            version="1.0.0",
            description="A test server",
            capabilities=[MCPCapability.TOOLS, MCPCapability.STREAMING],
        )

        data = info.to_dict()
        assert data["name"] == "Test Server"
        assert data["version"] == "1.0.0"
        assert data["capabilities"] == ["tools", "streaming"]

    def test_mcp_tool_call(self):
        """Test MCP tool call."""
        call = MCPToolCall(tool="calculate", arguments={"expression": "2 + 2"})

        assert call.tool == "calculate"
        assert call.arguments == {"expression": "2 + 2"}
        assert call.id is not None

        data = call.to_dict()
        assert data["tool"] == "calculate"
        assert data["arguments"] == {"expression": "2 + 2"}
        assert data["id"] == call.id

    def test_mcp_tool_result(self):
        """Test MCP tool result."""
        # Success result
        result = MCPToolResult(tool_call_id="call-123", result=4)
        assert not result.is_error
        assert result.result == 4

        # Error result
        result = MCPToolResult(
            tool_call_id="call-123", result=None, error="Division by zero"
        )
        assert result.is_error
        assert result.error == "Division by zero"

    def test_mcp_connection_config(self):
        """Test MCP connection configuration."""
        # WebSocket config
        config = MCPConnectionConfig(url="ws://localhost:3000")
        assert config.is_websocket
        assert not config.is_http
        assert config.timeout == 30
        assert config.max_retries == 3

        # HTTP config
        config = MCPConnectionConfig(
            url="https://api.example.com",
            timeout=60,
            headers={"Authorization": "Bearer token"},
        )
        assert config.is_http
        assert not config.is_websocket
        assert config.timeout == 60
        assert config.headers["Authorization"] == "Bearer token"


@pytest.mark.parametrize(
    "method,expected",
    [
        (MCPMethod.LIST_TOOLS, "tools/list"),
        (MCPMethod.DESCRIBE_TOOL, "tools/describe"),
        (MCPMethod.CALL_TOOL, "tools/call"),
        (MCPMethod.INITIALIZE, "initialize"),
        (MCPMethod.SHUTDOWN, "shutdown"),
        (MCPMethod.GET_INFO, "server/info"),
        (MCPMethod.GET_CAPABILITIES, "server/capabilities"),
    ],
)
def test_mcp_method_values(method, expected):
    """Test MCP method enum values."""
    assert method.value == expected


@pytest.mark.parametrize(
    "code,expected",
    [
        (MCPErrorCode.PARSE_ERROR, "parse_error"),
        (MCPErrorCode.INVALID_REQUEST, "invalid_request"),
        (MCPErrorCode.METHOD_NOT_FOUND, "method_not_found"),
        (MCPErrorCode.INVALID_PARAMS, "invalid_params"),
        (MCPErrorCode.INTERNAL_ERROR, "internal_error"),
        (MCPErrorCode.TOOL_NOT_FOUND, "tool_not_found"),
        (MCPErrorCode.TOOL_EXECUTION_ERROR, "tool_execution_error"),
    ],
)
def test_mcp_error_code_values(code, expected):
    """Test MCP error code enum values."""
    assert code.value == expected


@pytest.mark.parametrize(
    "capability,expected",
    [
        (MCPCapability.TOOLS, "tools"),
        (MCPCapability.STREAMING, "streaming"),
        (MCPCapability.CANCELLATION, "cancellation"),
        (MCPCapability.PROGRESS, "progress"),
        (MCPCapability.MULTI_TOOL, "multi_tool"),
    ],
)
def test_mcp_capability_values(capability, expected):
    """Test MCP capability enum values."""
    assert capability.value == expected
