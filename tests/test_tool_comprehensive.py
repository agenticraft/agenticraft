"""Comprehensive tests for tool module to achieve >95% coverage."""

import asyncio
import inspect
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch

import pytest

from agenticraft.core.tool import (
    BaseTool, FunctionTool, ToolRegistry, tool, Calculator
)
from agenticraft.core.types import ToolDefinition, ToolParameter, ToolCall, ToolResult
from agenticraft.core.exceptions import ToolExecutionError, ToolNotFoundError, ToolValidationError


class TestBaseTool:
    """Test BaseTool abstract class."""
    
    def test_cannot_instantiate_base_tool(self):
        """Test BaseTool cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseTool()
    
    def test_base_tool_implementation(self):
        """Test implementing BaseTool."""
        class TestTool(BaseTool):
            def __init__(self):
                super().__init__(name="test_tool", description="A test tool")
            
            async def arun(self, **kwargs) -> Any:
                return {"result": "success", "args": kwargs}
            
            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name=self.name,
                    description=self.description,
                    parameters=[]
                )
        
        tool = TestTool()
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        
        # Test sync execution
        result = tool.run(arg1="value1")
        assert result == {"result": "success", "args": {"arg1": "value1"}}
        
        # Test async execution
        result = asyncio.run(tool.arun(arg2="value2"))
        assert result == {"result": "success", "args": {"arg2": "value2"}}
        
        # Test callable
        result = asyncio.run(tool(arg3="value3"))
        assert result == {"result": "success", "args": {"arg3": "value3"}}
        
        # Test definition
        definition = tool.get_definition()
        assert definition.name == "test_tool"
        assert definition.description == "A test tool"
        assert definition.parameters == []


class TestFunctionTool:
    """Test FunctionTool implementation."""
    
    def test_function_tool_sync(self):
        """Test FunctionTool with synchronous function."""
        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y
        
        tool = FunctionTool(add)
        
        assert tool.name == "add"
        assert tool.description == "Add two numbers."
        assert tool.func == add
        assert tool.is_async is False
        
        # Test execution
        result = tool.run(x=5, y=3)
        assert result == 8
        
        # Test async execution of sync function
        result = asyncio.run(tool.arun(x=10, y=20))
        assert result == 30
    
    def test_function_tool_async(self):
        """Test FunctionTool with asynchronous function."""
        async def fetch_data(url: str) -> dict:
            """Fetch data from URL."""
            await asyncio.sleep(0.01)  # Simulate async operation
            return {"url": url, "data": "fetched"}
        
        tool = FunctionTool(fetch_data)
        
        assert tool.name == "fetch_data"
        assert tool.description == "Fetch data from URL."
        assert tool.is_async is True
        
        # Test async execution
        result = asyncio.run(tool.arun(url="https://example.com"))
        assert result == {"url": "https://example.com", "data": "fetched"}
        
        # Test sync execution of async function
        result = tool.run(url="https://test.com")
        assert result == {"url": "https://test.com", "data": "fetched"}
    
    def test_function_tool_custom_name_description(self):
        """Test FunctionTool with custom name and description."""
        def process():
            return "processed"
        
        tool = FunctionTool(
            process,
            name="custom_processor",
            description="Custom processing tool"
        )
        
        assert tool.name == "custom_processor"
        assert tool.description == "Custom processing tool"
    
    def test_function_tool_no_docstring(self):
        """Test FunctionTool with function without docstring."""
        def no_docs(x):
            return x * 2
        
        tool = FunctionTool(no_docs)
        
        assert tool.name == "no_docs"
        assert tool.description == f"Function {no_docs.__name__}"  # Default description
    
    def test_function_tool_get_definition(self):
        """Test converting FunctionTool to ToolDefinition."""
        def calculate(
            operation: str,
            x: float,
            y: float = 10.0,
            precision: Optional[int] = None
        ) -> float:
            """Perform a calculation."""
            if operation == "+":
                result = x + y
            elif operation == "-":
                result = x - y
            elif operation == "*":
                result = x * y
            elif operation == "/":
                result = x / y
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            if precision is not None:
                result = round(result, precision)
            return result
        
        tool = FunctionTool(calculate)
        definition = tool.get_definition()
        
        assert definition.name == "calculate"
        assert "Perform a calculation" in definition.description
        assert len(definition.parameters) == 4
        
        # Check parameters
        params_by_name = {p.name: p for p in definition.parameters}
        
        assert params_by_name["operation"].type == "string"
        assert params_by_name["operation"].required is True
        
        assert params_by_name["x"].type == "number"
        assert params_by_name["x"].required is True
        
        assert params_by_name["y"].type == "number"
        assert params_by_name["y"].required is False
        assert params_by_name["y"].default == 10.0
        
        assert params_by_name["precision"].type == "integer"
        assert params_by_name["precision"].required is False
        assert params_by_name["precision"].default is None
    
    def test_function_tool_type_mapping(self):
        """Test type mapping in FunctionTool."""
        def test_types(
            text: str,
            number: int,
            decimal: float,
            flag: bool,
            items: List[str],
            data: Dict[str, Any],
            optional: Optional[int] = None,
            any_type: Any = "default"
        ):
            """Test various types."""
            pass
        
        tool = FunctionTool(test_types)
        definition = tool.get_definition()
        
        params_by_name = {p.name: p for p in definition.parameters}
        
        assert params_by_name["text"].type == "string"
        assert params_by_name["number"].type == "integer"
        assert params_by_name["decimal"].type == "number"
        assert params_by_name["flag"].type == "boolean"
        assert params_by_name["items"].type == "array"
        assert params_by_name["data"].type == "object"
        assert params_by_name["optional"].type == "integer"
        assert params_by_name["any_type"].type == "string"  # Default for Any
    
    def test_function_tool_error_handling(self):
        """Test error handling in FunctionTool."""
        def failing_tool():
            raise ValueError("Tool failed")
        
        tool = FunctionTool(failing_tool)
        
        with pytest.raises(ToolExecutionError) as exc_info:
            tool.run()
        
        assert exc_info.value.tool_name == "failing_tool"
        assert "Tool failed" in str(exc_info.value.error)
        
        with pytest.raises(ToolExecutionError):
            asyncio.run(tool.arun())
    
    def test_function_tool_validation(self):
        """Test argument validation in FunctionTool."""
        def strict_tool(required: str, optional: int = 5):
            return f"{required}-{optional}"
        
        tool = FunctionTool(strict_tool)
        
        # Valid call
        result = tool.run(required="test", optional=10)
        assert result == "test-10"
        
        # Missing required parameter
        with pytest.raises(ToolValidationError) as exc_info:
            tool.run(optional=10)
        
        assert "Missing required parameter: required" in str(exc_info.value)
        
        # Unknown parameter
        with pytest.raises(ToolValidationError) as exc_info:
            tool.run(required="test", unknown="param")
        
        assert "Unknown parameter: unknown" in str(exc_info.value)
    
    def test_function_tool_no_annotations(self):
        """Test FunctionTool with no type annotations."""
        def untyped_func(a, b, c=10):
            """Untyped function."""
            return a + b + c
        
        tool = FunctionTool(untyped_func)
        definition = tool.get_definition()
        
        # All parameters should default to string type
        for param in definition.parameters:
            assert param.type == "string"
        
        # Check required/optional
        params_by_name = {p.name: p for p in definition.parameters}
        assert params_by_name["a"].required is True
        assert params_by_name["b"].required is True
        assert params_by_name["c"].required is False
        assert params_by_name["c"].default == 10


class TestToolDecorator:
    """Test @tool decorator."""
    
    def test_tool_decorator_basic(self):
        """Test basic @tool decorator."""
        @tool
        def my_tool(x: int) -> int:
            """Double a number."""
            return x * 2
        
        assert isinstance(my_tool, FunctionTool)
        assert my_tool.name == "my_tool"
        assert my_tool.description == "Double a number."
        
        # Can still call it
        result = my_tool.run(x=21)
        assert result == 42
    
    def test_tool_decorator_async(self):
        """Test @tool decorator on async function."""
        @tool
        async def async_tool(text: str) -> str:
            """Process text asynchronously."""
            await asyncio.sleep(0.01)
            return text.upper()
        
        assert isinstance(async_tool, FunctionTool)
        assert async_tool.is_async is True
        
        result = asyncio.run(async_tool.arun(text="hello"))
        assert result == "HELLO"
    
    def test_tool_decorator_with_params(self):
        """Test @tool decorator with parameters."""
        @tool(name="custom_name", description="Custom description")
        def another_tool():
            return "result"
        
        assert another_tool.name == "custom_name"
        assert another_tool.description == "Custom description"
    
    def test_tool_decorator_callable_syntax(self):
        """Test @tool() syntax."""
        @tool()
        def empty_parens():
            """Tool with empty decorator parens."""
            return "works"
        
        assert empty_parens.name == "empty_parens"
        assert empty_parens.description == "Tool with empty decorator parens."
    
    def test_tool_decorator_preserves_function(self):
        """Test that decorators preserve function properties."""
        def original_func(x: int, y: int = 5) -> int:
            """Original function."""
            return x + y
        
        decorated = tool(original_func)
        
        # Should preserve function properties
        assert decorated.func.__name__ == "original_func"
        assert decorated.func.__doc__ == "Original function."
        
        # Can get original function signature
        sig = inspect.signature(decorated.func)
        assert len(sig.parameters) == 2
        assert sig.parameters["y"].default == 5


class TestToolRegistry:
    """Test ToolRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create a tool registry."""
        return ToolRegistry()
    
    def test_register_function(self, registry):
        """Test registering a function."""
        def test_func():
            return "test"
        
        registry.register(test_func)
        
        assert "test_func" in registry._tools
        tool = registry.get("test_func")
        assert isinstance(tool, FunctionTool)
        assert tool.name == "test_func"
    
    def test_register_function_tool(self, registry):
        """Test registering a FunctionTool."""
        def func():
            return "result"
        
        func_tool = FunctionTool(func, name="custom_tool")
        registry.register(func_tool)
        
        assert "custom_tool" in registry._tools
        assert registry.get("custom_tool") == func_tool
    
    def test_register_base_tool(self, registry):
        """Test registering a BaseTool subclass."""
        class CustomTool(BaseTool):
            def __init__(self):
                super().__init__(name="custom", description="Custom tool")
            
            async def arun(self, **kwargs):
                return {"custom": True}
            
            def get_definition(self):
                return ToolDefinition(name=self.name, description=self.description, parameters=[])
        
        tool = CustomTool()
        registry.register(tool)
        
        assert "custom" in registry._tools
        assert registry.get("custom") == tool
    
    def test_register_invalid_tool(self, registry):
        """Test registering invalid tool types."""
        with pytest.raises(ValueError, match="Invalid tool type"):
            registry.register("not a tool")
        
        with pytest.raises(ValueError, match="Invalid tool type"):
            registry.register(42)
        
        with pytest.raises(ValueError, match="Invalid tool type"):
            registry.register(None)
    
    def test_register_duplicate_tool(self, registry):
        """Test registering duplicate tool names."""
        def tool1():
            return 1
        
        def tool2():
            return 2
        
        registry.register(tool1, name="duplicate")
        registry.register(tool2, name="duplicate")
        
        # Should overwrite
        tool = registry.get("duplicate")
        result = asyncio.run(registry.execute("duplicate"))
        assert result == 2
    
    def test_get_existing_tool(self, registry):
        """Test getting an existing tool."""
        def my_tool():
            return "found"
        
        registry.register(my_tool)
        
        tool = registry.get("my_tool")
        assert tool is not None
        assert tool.run() == "found"
    
    def test_get_nonexistent_tool(self, registry):
        """Test getting a non-existent tool."""
        with pytest.raises(ToolNotFoundError, match="Tool 'nonexistent' not found in registry"):
            registry.get("nonexistent")
    
    def test_list_tools(self, registry):
        """Test listing all tools."""
        def tool1():
            return 1
        def tool2():
            return 2
        def tool3():
            return 3
        
        registry.register(tool1)
        registry.register(tool2)
        registry.register(tool3)
        
        tools = registry.list_tools()
        assert len(tools) == 3
        assert set(tools) == {"tool1", "tool2", "tool3"}
    
    def test_list_tools_empty(self, registry):
        """Test listing tools when registry is empty."""
        tools = registry.list_tools()
        assert tools == []
    
    @pytest.mark.asyncio
    async def test_execute_sync_tool(self, registry):
        """Test executing a synchronous tool."""
        def add(x: int, y: int) -> int:
            return x + y
        
        registry.register(add)
        
        result = await registry.execute("add", x=5, y=3)
        assert result == 8
    
    @pytest.mark.asyncio
    async def test_execute_async_tool(self, registry):
        """Test executing an asynchronous tool."""
        async def async_process(data: str) -> str:
            await asyncio.sleep(0.01)
            return data.upper()
        
        registry.register(async_process)
        
        result = await registry.execute("async_process", data="hello")
        assert result == "HELLO"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, registry):
        """Test executing a non-existent tool."""
        with pytest.raises(ToolNotFoundError, match="Tool 'missing' not found in registry"):
            await registry.execute("missing", arg="value")
    
    @pytest.mark.asyncio
    async def test_execute_tool_error(self, registry):
        """Test executing a tool that raises an error."""
        def failing_tool():
            raise RuntimeError("Tool error")
        
        registry.register(failing_tool)
        
        with pytest.raises(ToolExecutionError) as exc_info:
            await registry.execute("failing_tool")
        
        error = exc_info.value
        assert error.tool_name == "failing_tool"
        assert "Tool error" in str(error.error)
    
    def test_get_tools_schema(self, registry):
        """Test getting tools schema."""
        def tool1(x: int) -> int:
            """First tool."""
            return x
        
        def tool2(text: str) -> str:
            """Second tool."""
            return text
        
        registry.register(tool1)
        registry.register(tool2)
        
        schema = registry.get_tools_schema()
        
        assert len(schema) == 2
        
        # Check it returns OpenAI-compatible schema
        for tool_schema in schema:
            assert tool_schema["type"] == "function"
            assert "function" in tool_schema
            assert "name" in tool_schema["function"]
            assert "description" in tool_schema["function"]
            assert "parameters" in tool_schema["function"]
    
    def test_get_tools_schema_empty(self, registry):
        """Test getting schema when no tools registered."""
        schema = registry.get_tools_schema()
        assert schema == []
    
    def test_clear(self, registry):
        """Test clearing all tools."""
        registry.register(lambda: 1, name="tool1")
        registry.register(lambda: 2, name="tool2")
        
        assert len(registry.list_tools()) == 2
        
        registry.clear()
        
        assert len(registry.list_tools()) == 0
        assert registry._tools == {}


class TestCalculatorTool:
    """Test the built-in Calculator tool."""
    
    def test_calculator_basic(self):
        """Test basic calculator functionality."""
        calc = Calculator()
        
        assert calc.name == "calculator"
        assert "calculator" in calc.description.lower()
        
        # Test basic operations
        result = asyncio.run(calc.arun(expression="2 + 2"))
        assert result == 4.0
        
        result = asyncio.run(calc.arun(expression="10 - 3"))
        assert result == 7.0
        
        result = asyncio.run(calc.arun(expression="4 * 5"))
        assert result == 20.0
        
        result = asyncio.run(calc.arun(expression="15 / 3"))
        assert result == 5.0
    
    def test_calculator_complex(self):
        """Test complex expressions."""
        calc = Calculator()
        
        # Order of operations
        result = asyncio.run(calc.arun(expression="2 + 3 * 4"))
        assert result == 14.0
        
        # Parentheses
        result = asyncio.run(calc.arun(expression="(2 + 3) * 4"))
        assert result == 20.0
        
        # Floating point
        result = asyncio.run(calc.arun(expression="10.5 + 0.5"))
        assert result == 11.0
    
    def test_calculator_error(self):
        """Test calculator error handling."""
        calc = Calculator()
        
        # Invalid expression
        with pytest.raises(ToolExecutionError) as exc_info:
            asyncio.run(calc.arun(expression="2 + + 3"))
        
        assert exc_info.value.tool_name == "calculator"
        assert "Invalid expression" in str(exc_info.value)
        
        # Dangerous operations should be blocked
        with pytest.raises(ToolExecutionError):
            asyncio.run(calc.arun(expression="__import__('os').system('ls')"))
    
    def test_calculator_definition(self):
        """Test calculator tool definition."""
        calc = Calculator()
        definition = calc.get_definition()
        
        assert definition.name == "calculator"
        assert len(definition.parameters) == 1
        
        param = definition.parameters[0]
        assert param.name == "expression"
        assert param.type == "string"
        assert param.required is True


class TestToolIntegration:
    """Integration tests for tools."""
    
    def test_complete_tool_flow(self):
        """Test complete tool flow from definition to execution."""
        # Define a tool using decorator
        @tool
        def search_web(query: str, max_results: int = 10) -> List[Dict[str, str]]:
            """Search the web for information.
            
            Args:
                query: Search query
                max_results: Maximum results to return
            """
            return [
                {"title": f"Result {i}", "url": f"https://example.com/{i}"}
                for i in range(min(max_results, 3))
            ]
        
        # Create registry and register
        registry = ToolRegistry()
        registry.register(search_web)
        
        # Get tool definition
        tool = registry.get("search_web")
        definition = tool.get_definition()
        
        # Verify definition
        assert definition.name == "search_web"
        assert "Search the web" in definition.description
        assert len(definition.parameters) == 2
        
        # Get schema for LLM
        schema = registry.get_tools_schema()
        assert len(schema) == 1
        
        tool_schema = schema[0]
        assert tool_schema["function"]["name"] == "search_web"
        assert "query" in tool_schema["function"]["parameters"]["properties"]
        assert tool_schema["function"]["parameters"]["required"] == ["query"]
        
        # Execute tool
        result = asyncio.run(registry.execute("search_web", query="python", max_results=2))
        assert len(result) == 2
        assert result[0]["title"] == "Result 0"
    
    def test_tool_result_types(self):
        """Test ToolCall and ToolResult types."""
        # Test ToolCall
        tool_call = ToolCall(
            name="test_tool",
            arguments={"x": 5, "y": 10}
        )
        
        assert tool_call.id  # Should have auto-generated ID
        assert tool_call.name == "test_tool"
        assert tool_call.arguments == {"x": 5, "y": 10}
        
        # Test ToolCall with JSON string arguments
        tool_call2 = ToolCall(
            name="test_tool",
            arguments='{"x": 5, "y": 10}'
        )
        assert tool_call2.arguments == {"x": 5, "y": 10}  # Should parse JSON
        
        # Test ToolCall with invalid JSON
        tool_call3 = ToolCall(
            name="test_tool",
            arguments="not json"
        )
        assert tool_call3.arguments == {"input": "not json"}  # Should wrap as input
        
        # Test ToolResult
        result = ToolResult(
            tool_call_id=tool_call.id,
            result={"sum": 15}
        )
        
        assert result.tool_call_id == tool_call.id
        assert result.result == {"sum": 15}
        assert result.error is None
        assert result.success is True
        
        # Test ToolResult with error
        error_result = ToolResult(
            tool_call_id=tool_call.id,
            result=None,
            error="Division by zero"
        )
        
        assert error_result.success is False
        assert error_result.error == "Division by zero"
    
    def test_multiple_registries(self):
        """Test multiple independent registries."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        
        def tool1():
            return "from registry 1"
        
        def tool2():
            return "from registry 2"
        
        registry1.register(tool1, name="shared_name")
        registry2.register(tool2, name="shared_name")
        
        # Registries should be independent
        result1 = asyncio.run(registry1.execute("shared_name"))
        result2 = asyncio.run(registry2.execute("shared_name"))
        
        assert result1 == "from registry 1"
        assert result2 == "from registry 2"
        
        # Different tool lists
        assert registry1.list_tools() == ["shared_name"]
        assert registry2.list_tools() == ["shared_name"]
