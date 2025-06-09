"""Tests for MCP adapters."""

from typing import Any

import pytest

from agenticraft.core.types import ToolDefinition, ToolParameter
from agenticraft.protocols.mcp.adapters import (
    MCPToolWrapper,
    agenticraft_tool_to_mcp,
    mcp_tool,
    mcp_tool_to_agenticraft,
    wrap_function_as_mcp_tool,
)
from agenticraft.protocols.mcp.types import MCPTool, MCPToolParameter


class TestMCPAdapters:
    """Test MCP adapter functions."""

    def test_mcp_tool_to_agenticraft(self):
        """Test converting MCP tool to AgentiCraft format."""
        # Create MCP tool
        mcp_tool_obj = MCPTool(
            name="weather",
            description="Get weather information",
            parameters=[
                MCPToolParameter(
                    name="city", type="string", description="City name", required=True
                ),
                MCPToolParameter(
                    name="units",
                    type="string",
                    description="Temperature units",
                    enum=["celsius", "fahrenheit"],
                    default="celsius",
                ),
            ],
        )

        # Convert
        tool_def = mcp_tool_to_agenticraft(mcp_tool_obj)

        assert tool_def.name == "weather"
        assert tool_def.description == "Get weather information"
        assert len(tool_def.parameters) == 2

        # Check parameters
        city_param = tool_def.parameters[0]
        assert city_param.name == "city"
        assert city_param.type == "string"
        assert city_param.required is True

        units_param = tool_def.parameters[1]
        assert units_param.name == "units"
        assert units_param.enum == ["celsius", "fahrenheit"]
        assert units_param.default == "celsius"

    def test_agenticraft_tool_to_mcp(self):
        """Test converting AgentiCraft tool to MCP format."""
        # Create AgentiCraft tool definition
        tool_def = ToolDefinition(
            name="calculate",
            description="Perform calculations",
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="Math expression",
                    required=True,
                ),
                ToolParameter(
                    name="precision",
                    type="integer",
                    description="Decimal precision",
                    required=False,
                    default=2,
                ),
            ],
        )

        # Convert
        mcp_tool_obj = agenticraft_tool_to_mcp(tool_def)

        assert mcp_tool_obj.name == "calculate"
        assert mcp_tool_obj.description == "Perform calculations"
        assert len(mcp_tool_obj.parameters) == 2

        # Check parameters
        expr_param = mcp_tool_obj.parameters[0]
        assert expr_param.name == "expression"
        assert expr_param.type == "string"
        assert expr_param.required is True

        precision_param = mcp_tool_obj.parameters[1]
        assert precision_param.name == "precision"
        assert precision_param.type == "integer"
        assert precision_param.default == 2

    def test_mcp_tool_decorator(self):
        """Test MCP tool decorator."""

        @mcp_tool(
            name="custom_weather",
            returns={
                "type": "object",
                "properties": {
                    "temperature": {"type": "number"},
                    "conditions": {"type": "string"},
                },
            },
            examples=[
                {
                    "input": {"city": "New York"},
                    "output": {"temperature": 72, "conditions": "sunny"},
                }
            ],
        )
        def get_weather(city: str) -> dict[str, Any]:
            """Get weather for a city."""
            return {"temperature": 72, "conditions": "sunny"}

        # Check it's a tool
        assert hasattr(get_weather, "name")
        assert get_weather.name == "custom_weather"

        # Check MCP metadata
        assert hasattr(get_weather, "_mcp_returns")
        assert hasattr(get_weather, "_mcp_examples")

        # Get MCP tool
        mcp_tool_obj = get_weather.get_mcp_tool()
        assert mcp_tool_obj.name == "custom_weather"
        assert mcp_tool_obj.returns is not None
        assert len(mcp_tool_obj.examples) == 1

    def test_mcp_tool_decorator_simple(self):
        """Test MCP tool decorator without extra metadata."""

        @mcp_tool
        def simple_tool(x: int) -> int:
            """Double a number."""
            return x * 2

        assert simple_tool.name == "simple_tool"
        assert simple_tool.description == "Double a number."

        # Should still work as regular tool
        result = simple_tool.run(x=5)
        assert result == 10

    def test_wrap_function_as_mcp_tool(self):
        """Test wrapping function as MCP tool."""

        def calculate_area(width: float, height: float) -> float:
            """Calculate rectangle area."""
            return width * height

        # Wrap with custom metadata
        wrapped = wrap_function_as_mcp_tool(
            calculate_area,
            name="rect_area",
            returns={"type": "number", "description": "Area in square units"},
            examples=[{"input": {"width": 5, "height": 3}, "output": 15}],
        )

        assert wrapped.name == "rect_area"
        assert wrapped.description == "Calculate rectangle area."

        # Check MCP tool
        mcp_tool_obj = wrapped.get_mcp_tool()
        assert mcp_tool_obj.returns is not None
        assert len(mcp_tool_obj.examples) == 1

        # Test execution
        result = wrapped.run(width=5, height=3)
        assert result == 15

    @pytest.mark.asyncio
    async def test_mcp_tool_wrapper_async(self):
        """Test MCP tool wrapper with async function."""

        async def async_search(query: str) -> str:
            """Async search function."""
            return f"Results for: {query}"

        wrapper = MCPToolWrapper(
            async_search,
            parameters=[MCPToolParameter(name="query", type="string", required=True)],
        )

        # Test async execution
        result = await wrapper.arun(query="test")
        assert result == "Results for: test"

    def test_mcp_tool_wrapper_parameter_parsing(self):
        """Test automatic parameter parsing."""

        def typed_function(
            name: str, age: int, active: bool = True, tags: list = None
        ) -> dict:
            """Function with typed parameters."""
            return {"name": name, "age": age, "active": active, "tags": tags or []}

        wrapper = MCPToolWrapper(typed_function)

        # Check parsed parameters
        assert len(wrapper.parameters) == 4

        name_param = wrapper.parameters[0]
        assert name_param.name == "name"
        assert name_param.type == "string"
        assert name_param.required is True

        age_param = wrapper.parameters[1]
        assert age_param.name == "age"
        assert age_param.type == "integer"
        assert age_param.required is True

        active_param = wrapper.parameters[2]
        assert active_param.name == "active"
        assert active_param.type == "boolean"
        assert active_param.required is False
        assert active_param.default is True

        tags_param = wrapper.parameters[3]
        assert tags_param.name == "tags"
        assert tags_param.type == "array"
        assert tags_param.required is False

    def test_mcp_tool_wrapper_definition(self):
        """Test getting tool definition from wrapper."""

        def simple_func(text: str) -> str:
            return text.upper()

        wrapper = MCPToolWrapper(
            simple_func, name="uppercase", description="Convert text to uppercase"
        )

        # Get AgentiCraft definition
        definition = wrapper.get_definition()
        assert definition.name == "uppercase"
        assert definition.description == "Convert text to uppercase"
        assert len(definition.parameters) == 1
        assert definition.parameters[0].name == "text"
