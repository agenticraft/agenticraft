"""Tests for tool functionality."""

import asyncio
from typing import List

import pytest

from agenticraft import tool
from agenticraft.core.tool import (
    BaseTool,
    FunctionTool,
    ToolCall,
    ToolRegistry,
    ToolResult,
    Calculator,
)
from agenticraft.core.exceptions import (
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
)


class TestToolDecorator:
    """Test the @tool decorator."""
    
    def test_basic_tool_creation(self):
        """Test creating a basic tool."""
        @tool
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y
        
        assert isinstance(add, FunctionTool)
        assert add.name == "add"
        assert add.description == "Add two numbers."
        assert len(add.parameters) == 2
    
    def test_tool_with_overrides(self):
        """Test tool with custom name and description."""
        @tool(name="calculator", description="Performs calculations")
        def calc(expr: str) -> float:
            return eval(expr)
        
        assert calc.name == "calculator"
        assert calc.description == "Performs calculations"
    
    def test_tool_without_docstring(self):
        """Test tool without docstring."""
        @tool
        def no_doc():
            return "test"
        
        assert no_doc.description == "Function no_doc"
    
    def test_async_tool(self):
        """Test async tool creation."""
        @tool
        async def async_fetch(url: str) -> str:
            """Fetch data from URL."""
            await asyncio.sleep(0.01)
            return f"Data from {url}"
        
        assert async_fetch.is_async is True
        assert async_fetch.name == "async_fetch"
    
    def test_tool_parameter_parsing(self):
        """Test parameter parsing from function signature."""
        @tool
        def complex_func(
            required: str,
            optional: int = 42,
            another: bool = True
        ) -> str:
            """Complex function with various parameters."""
            return f"{required}-{optional}-{another}"
        
        params = {p.name: p for p in complex_func.parameters}
        
        assert len(params) == 3
        assert params["required"].required is True
        assert params["optional"].required is False
        assert params["optional"].default == 42
        assert params["another"].required is False
        assert params["another"].default is True


class TestFunctionTool:
    """Test FunctionTool class."""
    
    def test_sync_execution(self):
        """Test synchronous tool execution."""
        def add(x: int, y: int) -> int:
            return x + y
        
        tool = FunctionTool(add)
        result = tool.run(x=5, y=3)
        
        assert result == 8
    
    @pytest.mark.asyncio
    async def test_async_execution(self):
        """Test asynchronous tool execution."""
        async def async_add(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y
        
        tool = FunctionTool(async_add)
        result = await tool.arun(x=5, y=3)
        
        assert result == 8
    
    def test_argument_validation(self):
        """Test tool argument validation."""
        @tool
        def strict_func(required: str, number: int) -> str:
            return f"{required}-{number}"
        
        # Missing required argument
        with pytest.raises(ToolValidationError, match="Missing required parameter"):
            strict_func.run(number=42)
        
        # Unknown parameter
        with pytest.raises(ToolValidationError, match="Unknown parameter"):
            strict_func.run(required="test", number=42, unknown="bad")
    
    def test_execution_error(self):
        """Test tool execution error handling."""
        @tool
        def error_tool():
            raise ValueError("Something went wrong")
        
        with pytest.raises(ToolExecutionError, match="Something went wrong"):
            error_tool.run()
    
    def test_tool_definition(self):
        """Test tool definition generation."""
        @tool
        def sample_tool(text: str, count: int = 1) -> str:
            """Repeat text multiple times."""
            return text * count
        
        definition = sample_tool.get_definition()
        
        assert definition.name == "sample_tool"
        assert definition.description == "Repeat text multiple times."
        assert len(definition.parameters) == 2
        
        # Check OpenAI schema conversion
        schema = definition.to_openai_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "sample_tool"
        assert "text" in schema["function"]["parameters"]["properties"]
        assert "count" in schema["function"]["parameters"]["properties"]
        assert schema["function"]["parameters"]["required"] == ["text"]


class TestToolCall:
    """Test ToolCall model."""
    
    def test_tool_call_creation(self):
        """Test creating a tool call."""
        tc = ToolCall(
            name="test_tool",
            arguments={"x": 1, "y": 2}
        )
        
        assert tc.name == "test_tool"
        assert tc.arguments == {"x": 1, "y": 2}
        assert tc.id is not None
    
    def test_tool_call_string_arguments(self):
        """Test tool call with string arguments (from LLM)."""
        tc = ToolCall(
            name="test_tool",
            arguments='{"x": 1, "y": 2}'
        )
        
        assert tc.arguments == {"x": 1, "y": 2}
    
    def test_tool_call_invalid_json(self):
        """Test tool call with invalid JSON arguments."""
        tc = ToolCall(
            name="test_tool",
            arguments="not json"
        )
        
        # Should convert to input key
        assert tc.arguments == {"input": "not json"}


class TestToolResult:
    """Test ToolResult model."""
    
    def test_successful_result(self):
        """Test successful tool result."""
        result = ToolResult(
            tool_call_id="call_123",
            result={"data": "success"}
        )
        
        assert result.success is True
        assert result.error is None
        assert result.result == {"data": "success"}
    
    def test_error_result(self):
        """Test error tool result."""
        result = ToolResult(
            tool_call_id="call_456",
            result={"error": "Failed"},
            error="Tool execution failed"
        )
        
        assert result.success is False
        assert result.error == "Tool execution failed"


class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    def test_register_tool(self):
        """Test registering tools."""
        registry = ToolRegistry()
        
        @tool
        def my_tool():
            return "test"
        
        registry.register(my_tool)
        
        assert "my_tool" in registry.list_tools()
        assert registry.get("my_tool") == my_tool
    
    def test_register_callable(self):
        """Test registering plain callable."""
        registry = ToolRegistry()
        
        def plain_func():
            return "plain"
        
        registry.register(plain_func)
        
        assert "plain_func" in registry.list_tools()
        tool_instance = registry.get("plain_func")
        assert isinstance(tool_instance, FunctionTool)
    
    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        
        with pytest.raises(ToolNotFoundError, match="Tool 'missing' not found"):
            registry.get("missing")
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing tool through registry."""
        registry = ToolRegistry()
        
        @tool
        def multiply(x: int, y: int) -> int:
            return x * y
        
        registry.register(multiply)
        
        result = await registry.execute("multiply", x=6, y=7)
        assert result == 42
    
    def test_get_tools_schema(self):
        """Test getting schema for all tools."""
        registry = ToolRegistry()
        
        @tool
        def tool1():
            """First tool."""
            return "1"
        
        @tool
        def tool2():
            """Second tool."""
            return "2"
        
        registry.register(tool1)
        registry.register(tool2)
        
        schemas = registry.get_tools_schema()
        
        assert len(schemas) == 2
        assert any(s["function"]["name"] == "tool1" for s in schemas)
        assert any(s["function"]["name"] == "tool2" for s in schemas)
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ToolRegistry()
        
        @tool
        def test_tool():
            return "test"
        
        registry.register(test_tool)
        assert len(registry.list_tools()) == 1
        
        registry.clear()
        assert len(registry.list_tools()) == 0


class TestBuiltinTools:
    """Test built-in tools."""
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self):
        """Test the Calculator tool."""
        calc = Calculator()
        
        assert calc.name == "calculator"
        assert "math" in calc.description.lower()
        
        # Test valid expressions
        result = await calc.arun(expression="2 + 2")
        assert result == 4.0
        
        result = await calc.arun(expression="10 * 5")
        assert result == 50.0
        
        result = await calc.arun(expression="(10 + 5) * 2")
        assert result == 30.0
        
        # Test invalid expression
        with pytest.raises(ToolExecutionError, match="Invalid expression"):
            await calc.arun(expression="invalid")
    
    def test_calculator_definition(self):
        """Test Calculator tool definition."""
        calc = Calculator()
        definition = calc.get_definition()
        
        assert definition.name == "calculator"
        assert len(definition.parameters) == 1
        assert definition.parameters[0].name == "expression"
        assert definition.parameters[0].required is True
