"""Unit tests for tool module.

This module tests the tool functionality including:
- Tool decorator
- Tool registry
- Tool execution
- Tool definitions and schemas
"""

import asyncio
import inspect
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agenticraft.core.tool import (
    BaseTool,
    FunctionTool,
    tool,
    ToolRegistry,
)
from agenticraft.core.types import ToolDefinition, ToolParameter, ToolCall, ToolResult
from agenticraft.core.exceptions import ToolExecutionError, ToolNotFoundError, ToolValidationError


class TestToolDecorator:
    """Test the @tool decorator."""
    
    def test_simple_tool_decorator(self):
        """Test decorating a simple function."""
        @tool
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b
        
        assert isinstance(add_numbers, FunctionTool)
        assert add_numbers.name == "add_numbers"
        assert add_numbers.description == "Add two numbers together."
    
    def test_tool_decorator_with_name(self):
        """Test decorator with custom name."""
        @tool(name="calculator_add")
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b
        
        assert add.name == "calculator_add"
        assert add.description == "Add two numbers."
    
    def test_tool_decorator_with_description(self):
        """Test decorator with custom description."""
        @tool(description="Custom description for addition")
        def add(a: int, b: int) -> int:
            return a + b
        
        assert add.description == "Custom description for addition"
    
    def test_tool_decorator_preserves_function(self):
        """Test that decorator preserves original function."""
        @tool
        def multiply(x: float, y: float) -> float:
            """Multiply two numbers."""
            return x * y
        
        # Should still be callable
        result = multiply(3.0, 4.0)
        assert result == 12.0
    
    def test_async_tool_decorator(self):
        """Test decorating async functions."""
        @tool
        async def fetch_data(url: str) -> Dict:
            """Fetch data from URL."""
            await asyncio.sleep(0.1)
            return {"url": url, "data": "sample"}
        
        assert isinstance(fetch_data, FunctionTool)
        assert asyncio.iscoroutinefunction(fetch_data.func)
    
    def test_tool_decorator_without_parentheses(self):
        """Test decorator used without parentheses."""
        @tool
        def simple_tool(value: str) -> str:
            """A simple tool."""
            return value.upper()
        
        assert simple_tool.name == "simple_tool"
        assert simple_tool("hello") == "HELLO"
    
    def test_tool_decorator_with_complex_types(self):
        """Test decorator with complex type annotations."""
        @tool
        def process_list(
            items: List[str],
            options: Optional[Dict[str, bool]] = None
        ) -> Dict[str, List[str]]:
            """Process a list of items."""
            options = options or {}
            return {
                "original": items,
                "processed": [item.upper() for item in items]
            }
        
        definition = process_list.get_definition()
        assert len(definition.parameters) == 2
        assert definition.parameters[0].name == "items"
        assert definition.parameters[1].name == "options"
        assert not definition.parameters[1].required


class TestFunctionTool:
    """Test FunctionTool class functionality."""
    
    def test_tool_creation(self):
        """Test creating a Tool instance."""
        def sample_func(x: int) -> int:
            """Double a number."""
            return x * 2
        
        tool_instance = FunctionTool(
            func=sample_func,
            name="doubler",
            description="Doubles the input"
        )
        
        assert tool_instance.name == "doubler"
        assert tool_instance.description == "Doubles the input"
        assert tool_instance.func == sample_func
        # Test execution
        assert tool_instance.run(x=3) == 6
    
    def test_tool_run_sync(self):
        """Test running a synchronous tool."""
        @tool
        def concat_strings(a: str, b: str) -> str:
            """Concatenate two strings."""
            return a + b
        
        result = concat_strings.run(a="Hello", b=" World")
        assert result == "Hello World"
    
    @pytest.mark.asyncio
    async def test_tool_arun_sync(self):
        """Test async run of synchronous tool."""
        @tool
        def square(n: int) -> int:
            """Square a number."""
            return n * n
        
        result = await square.arun(n=5)
        assert result == 25
    
    @pytest.mark.asyncio
    async def test_tool_arun_async(self):
        """Test running an async tool."""
        @tool
        async def async_process(data: str) -> str:
            """Process data asynchronously."""
            await asyncio.sleep(0.01)
            return data.upper()
        
        result = await async_process.arun(data="test")
        assert result == "TEST"
    
    def test_tool_get_definition(self):
        """Test getting tool definition."""
        @tool(name="math_add", description="Add numbers")
        def add(x: float, y: float, round_result: bool = False) -> float:
            """Add two numbers with optional rounding."""
            result = x + y
            return round(result) if round_result else result
        
        definition = add.get_definition()
        
        assert isinstance(definition, ToolDefinition)
        assert definition.name == "math_add"
        assert definition.description == "Add numbers"
        assert len(definition.parameters) == 3
        
        # Check parameters
        param_names = [p.name for p in definition.parameters]
        assert "x" in param_names
        assert "y" in param_names
        assert "round_result" in param_names
        
        # Check required vs optional
        round_param = next(p for p in definition.parameters if p.name == "round_result")
        assert not round_param.required
        assert round_param.default is False
    
    def test_tool_parse_parameters(self):
        """Test parameter parsing from function signature."""
        @tool
        def complex_tool(
            required_str: str,
            required_int: int,
            optional_str: str = "default",
            optional_list: List[str] = None,
            optional_dict: Dict[str, int] = None
        ) -> Dict:
            """Tool with various parameter types."""
            return {}
        
        definition = complex_tool.get_definition()
        params = {p.name: p for p in definition.parameters}
        
        # Check required parameters
        assert params["required_str"].required
        assert params["required_str"].type == "string"
        assert params["required_int"].required
        assert params["required_int"].type == "integer"
        
        # Check optional parameters
        assert not params["optional_str"].required
        assert params["optional_str"].default == "default"
        assert not params["optional_list"].required
        assert params["optional_list"].type == "array"
    
    def test_tool_error_handling(self):
        """Test tool error handling."""
        @tool
        def failing_tool(should_fail: bool = True) -> str:
            """A tool that can fail."""
            if should_fail:
                raise ValueError("Tool failed as requested")
            return "Success"
        
        # Should raise ToolExecutionError
        with pytest.raises(ToolExecutionError) as exc_info:
            failing_tool.run(should_fail=True)
        
        assert "Tool failed as requested" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None
    
    def test_tool_with_no_parameters(self):
        """Test tool with no parameters."""
        @tool
        def get_timestamp() -> str:
            """Get current timestamp."""
            import datetime
            return datetime.datetime.now().isoformat()
        
        definition = get_timestamp.get_definition()
        assert len(definition.parameters) == 0
        
        result = get_timestamp.run()
        assert isinstance(result, str)
    
    def test_tool_callable_directly(self):
        """Test that tools remain callable."""
        @tool
        def echo(message: str) -> str:
            """Echo the message."""
            return message
        
        # Should work as regular function
        assert echo("test") == "test"
        
        # Should work as tool
        assert echo.run(message="test") == "test"


class TestBaseTool:
    """Test BaseTool abstract class."""
    
    def test_base_tool_cannot_be_instantiated(self):
        """Test that BaseTool is abstract."""
        with pytest.raises(TypeError):
            BaseTool()
    
    def test_custom_tool_implementation(self):
        """Test creating custom tool class."""
        class WeatherTool(BaseTool):
            name = "weather"
            description = "Get weather information"
            
            async def arun(self, location: str) -> Dict:
                # Mock implementation
                return {
                    "location": location,
                    "temperature": 72,
                    "condition": "sunny"
                }
            
            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name=self.name,
                    description=self.description,
                    parameters=[
                        ToolParameter(
                            name="location",
                            type="string",
                            description="City name",
                            required=True
                        )
                    ]
                )
        
        tool = WeatherTool()
        assert tool.name == "weather"
        
        # Test async execution
        result = asyncio.run(tool.arun(location="New York"))
        assert result["location"] == "New York"
        assert result["temperature"] == 72


class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    def test_registry_creation(self):
        """Test creating tool registry."""
        registry = ToolRegistry()
        assert len(registry.list_tools()) == 0
    
    def test_register_tool_instance(self):
        """Test registering a tool instance."""
        registry = ToolRegistry()
        
        @tool
        def sample_tool(x: int) -> int:
            """Sample tool."""
            return x * 2
        
        registry.register(sample_tool)
        
        assert "sample_tool" in registry.list_tools()
        assert registry.get("sample_tool") == sample_tool
    
    def test_register_tool_function(self):
        """Test registering a plain function."""
        registry = ToolRegistry()
        
        def plain_function(text: str) -> str:
            """Convert to uppercase."""
            return text.upper()
        
        registry.register(plain_function)
        
        assert "plain_function" in registry.list_tools()
        registered = registry.get("plain_function")
        assert isinstance(registered, FunctionTool)
        assert registered.name == "plain_function"
    
    def test_register_with_custom_tool_name(self):
        """Test registering tool with custom name."""
        registry = ToolRegistry()
        
        @tool(name="custom_name")
        def original_name() -> str:
            """Tool function."""
            return "result"
        
        registry.register(original_name)
        
        assert "custom_name" in registry.list_tools()
        assert "original_name" not in registry.list_tools()
    
    def test_register_duplicate_name(self):
        """Test registering duplicate names."""
        registry = ToolRegistry()
        
        def first():
            return "first"
        def second():
            return "second"
        
        tool1 = tool(first)
        tool2 = tool(second)
        
        # Both tools have different names based on their functions
        registry.register(tool1)
        registry.register(tool2)
        
        assert "first" in registry.list_tools()
        assert "second" in registry.list_tools()
    
    def test_get_tool(self):
        """Test getting tool from registry."""
        registry = ToolRegistry()
        
        @tool
        def my_tool() -> str:
            return "result"
        
        registry.register(my_tool)
        
        retrieved = registry.get("my_tool")
        assert retrieved == my_tool
        
        # Non-existent tool
        with pytest.raises(ToolNotFoundError):
            registry.get("nonexistent")
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        
        @tool(name="tool1")
        def t1():
            return "1"
        
        @tool(name="tool2")
        def t2():
            return "2"
        
        @tool(name="tool3")
        def t3():
            return "3"
        
        registry.register(t1)
        registry.register(t2)
        registry.register(t3)
        
        tool_names = registry.list_tools()
        assert len(tool_names) == 3
        assert "tool1" in tool_names
        assert "tool2" in tool_names
        assert "tool3" in tool_names
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing tool through registry."""
        registry = ToolRegistry()
        
        @tool
        def calculator(operation: str, a: float, b: float) -> float:
            """Perform calculation."""
            if operation == "add":
                return a + b
            elif operation == "multiply":
                return a * b
            else:
                raise ValueError(f"Unknown operation: {operation}")
        
        registry.register(calculator)
        
        # Execute tool
        result = await registry.execute(
            "calculator",
            operation="add",
            a=10,
            b=5
        )
        
        assert result == 15
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing non-existent tool."""
        registry = ToolRegistry()
        
        with pytest.raises(ToolNotFoundError, match="Tool 'nonexistent' not found"):
            await registry.execute("nonexistent", arg="value")
    
    def test_get_tools_schema(self):
        """Test getting schema for all tools."""
        registry = ToolRegistry()
        
        @tool
        def search(query: str, limit: int = 10) -> List[str]:
            """Search for information."""
            return []
        
        @tool
        def calculate(expression: str) -> float:
            """Calculate math expression."""
            return 0.0
        
        registry.register(search)
        registry.register(calculate)
        
        schemas = registry.get_tools_schema()
        
        assert len(schemas) == 2
        
        # Check schemas are valid OpenAI format
        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ToolRegistry()
        
        @tool
        def temp_tool() -> str:
            return "temp"
        
        registry.register(temp_tool)
        assert "temp_tool" in registry.list_tools()
        
        registry.clear()
        assert len(registry.list_tools()) == 0
