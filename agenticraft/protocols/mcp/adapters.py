"""Adapters for converting between AgentiCraft and MCP formats.

This module provides adapters to seamlessly use MCP tools in AgentiCraft
and expose AgentiCraft tools via MCP.
"""

from collections.abc import Callable
from typing import Any

from ...core.tool import BaseTool, tool
from ...core.types import ToolDefinition, ToolParameter
from .types import MCPTool, MCPToolParameter


def mcp_tool_to_agenticraft(mcp_tool: MCPTool) -> ToolDefinition:
    """Convert MCP tool to AgentiCraft tool definition.

    Args:
        mcp_tool: MCP tool to convert

    Returns:
        AgentiCraft tool definition
    """
    parameters = []

    for param in mcp_tool.parameters:
        tool_param = ToolParameter(
            name=param.name,
            type=param.type,
            description=param.description or f"Parameter {param.name}",
            required=param.required,
            default=param.default,
            enum=param.enum,
        )
        parameters.append(tool_param)

    return ToolDefinition(
        name=mcp_tool.name, description=mcp_tool.description, parameters=parameters
    )


def agenticraft_tool_to_mcp(tool_def: ToolDefinition) -> MCPTool:
    """Convert AgentiCraft tool definition to MCP tool.

    Args:
        tool_def: AgentiCraft tool definition

    Returns:
        MCP tool
    """
    parameters = []

    for param in tool_def.parameters:
        mcp_param = MCPToolParameter(
            name=param.name,
            type=param.type,
            description=param.description,
            required=param.required,
            default=param.default,
            enum=param.enum,
        )
        parameters.append(mcp_param)

    return MCPTool(
        name=tool_def.name, description=tool_def.description, parameters=parameters
    )


def mcp_tool(
    name: str | Callable | None = None,
    description: str | None = None,
    returns: dict[str, Any] | None = None,
    examples: list[dict[str, Any]] | None = None,
):
    """Decorator for MCP-compatible tools.

    This decorator creates tools that include MCP-specific metadata
    like return schemas and examples.

    Args:
        name: Tool name override (or function if used without parentheses)
        description: Tool description override
        returns: JSON Schema for return type
        examples: Example inputs and outputs

    Example:
        Using the MCP tool decorator::

            @mcp_tool(
                name="weather",
                returns={"type": "object", "properties": {...}},
                examples=[{"input": {"city": "NYC"}, "output": {...}}]
            )
            def get_weather(city: str) -> dict:
                '''Get weather for a city.'''
                return {"temp": 72, "conditions": "sunny"}

            # Or without parentheses:
            @mcp_tool
            def simple_tool(x: int) -> int:
                '''Double a number.'''
                return x * 2
    """

    def decorator(func):
        # Create base tool
        base_tool = tool(
            name=name if isinstance(name, str) else None, description=description
        )(func)

        # Add MCP metadata
        base_tool._mcp_returns = returns
        base_tool._mcp_examples = examples

        # Override get_definition to include MCP data
        original_get_definition = base_tool.get_definition

        def get_definition_with_mcp():
            definition = original_get_definition()

            # Convert to MCP tool to include extra fields
            mcp_tool_obj = agenticraft_tool_to_mcp(definition)
            mcp_tool_obj.returns = returns
            mcp_tool_obj.examples = examples or []

            return definition

        base_tool.get_definition = get_definition_with_mcp

        # Add method to get MCP tool directly
        def get_mcp_tool():
            definition = original_get_definition()
            mcp_tool_obj = agenticraft_tool_to_mcp(definition)
            mcp_tool_obj.returns = returns
            mcp_tool_obj.examples = examples or []
            return mcp_tool_obj

        base_tool.get_mcp_tool = get_mcp_tool

        return base_tool

    # Handle both @mcp_tool and @mcp_tool() syntax
    if callable(name):
        func = name
        name = None
        return decorator(func)

    return decorator


class MCPToolWrapper(BaseTool):
    """Wrapper to use any Python function as an MCP tool.

    This wrapper allows exposing arbitrary Python functions via MCP
    without modifying the original function.
    """

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
        parameters: list[MCPToolParameter] | None = None,
        returns: dict[str, Any] | None = None,
        examples: list[dict[str, Any]] | None = None,
    ):
        """Initialize the wrapper.

        Args:
            func: Function to wrap
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            parameters: Explicit parameter definitions
            returns: Return type schema
            examples: Example inputs/outputs
        """

        # Extract metadata
        self.func = func
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Function {func.__name__}"

        super().__init__(name=tool_name, description=tool_desc)

        # Parse or use provided parameters
        if parameters:
            self.parameters = parameters
        else:
            self.parameters = self._parse_function_parameters(func)

        self.returns = returns
        self.examples = examples or []

    def _parse_function_parameters(self, func: Callable) -> list[MCPToolParameter]:
        """Parse function signature to extract parameters."""
        import inspect

        sig = inspect.signature(func)
        parameters = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Determine type
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                type_map = {
                    int: "integer",
                    float: "number",
                    str: "string",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                param_type = type_map.get(param.annotation, "string")

            # Check if required
            required = param.default == inspect.Parameter.empty

            parameters.append(
                MCPToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter {param_name}",
                    required=required,
                    default=None if required else param.default,
                )
            )

        return parameters

    async def arun(self, **kwargs: Any) -> Any:
        """Execute the wrapped function."""
        import asyncio

        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            return self.func(**kwargs)

    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        parameters = []

        for param in self.parameters:
            tool_param = ToolParameter(
                name=param.name,
                type=param.type,
                description=param.description or f"Parameter {param.name}",
                required=param.required,
                default=param.default,
                enum=param.enum,
            )
            parameters.append(tool_param)

        return ToolDefinition(
            name=self.name, description=self.description, parameters=parameters
        )

    def get_mcp_tool(self) -> MCPTool:
        """Get as MCP tool."""
        return MCPTool(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            returns=self.returns,
            examples=self.examples,
        )


def wrap_function_as_mcp_tool(func: Callable, **kwargs: Any) -> MCPToolWrapper:
    """Wrap a function as an MCP tool.

    Args:
        func: Function to wrap
        **kwargs: Additional configuration

    Returns:
        MCP tool wrapper
    """
    return MCPToolWrapper(func, **kwargs)
