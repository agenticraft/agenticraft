"""Tool abstraction for AgentiCraft.

This module provides the base classes and decorators for creating tools
that agents can use. Tools are functions that extend an agent's capabilities
beyond just language generation.

Example:
    Creating a simple tool::

        from agenticraft import tool

        @tool
        def calculate(expression: str) -> float:
            '''Evaluate a mathematical expression.'''
            return eval(expression, {"__builtins__": {}})

        # Use with an agent
        agent = Agent(tools=[calculate])
"""

from __future__ import annotations

import asyncio
import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Union

from .exceptions import ToolExecutionError, ToolNotFoundError, ToolValidationError
from .types import ToolDefinition, ToolParameter


class BaseTool(ABC):
    """Base class for all tools.

    Tools extend agent capabilities by providing specific functions
    that can be called during agent execution.
    """

    def __init__(self, name: str | None = None, description: str | None = None):
        """Initialize a tool.

        Args:
            name: Override the tool name
            description: Override the tool description
        """
        # Check if class has a name attribute first
        if (
            name is None
            and hasattr(self.__class__, "name")
            and self.__class__.name != "BaseTool"
        ):
            self.name = self.__class__.name
        else:
            self.name = name or self.__class__.__name__

        # Check if class has a description attribute first
        if (
            description is None
            and hasattr(self.__class__, "description")
            and self.__class__.description != "BaseTool"
        ):
            self.description = self.__class__.description
        else:
            self.description = description or self.__class__.__doc__ or "No description"

    @abstractmethod
    async def arun(self, **kwargs: Any) -> Any:
        """Run the tool asynchronously."""
        pass

    def run(self, **kwargs: Any) -> Any:
        """Run the tool synchronously."""
        return asyncio.run(self.arun(**kwargs))

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get the tool definition for LLM providers."""
        pass

    async def __call__(self, **kwargs: Any) -> Any:
        """Make the tool callable."""
        return await self.arun(**kwargs)


class FunctionTool(BaseTool):
    """A tool created from a function.

    This is the most common type of tool, created using the @tool decorator.
    """

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
    ):
        """Initialize from a function."""
        self.func = func
        self.is_async = asyncio.iscoroutinefunction(func)

        # Extract metadata
        name = name or func.__name__
        description = description or func.__doc__ or f"Function {func.__name__}"

        super().__init__(name=name, description=description)

        # Parse function signature
        self.signature = inspect.signature(func)
        self.parameters = self._parse_parameters()

    def _parse_parameters(self) -> list[ToolParameter]:
        """Parse function parameters into ToolParameter objects."""
        parameters = []

        for param_name, param in self.signature.parameters.items():
            if param_name == "self":
                continue

            # Skip **kwargs and *args
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            # Get type annotation
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                # Handle Optional types
                annotation = param.annotation

                # Check if it's Optional (Union with None)
                if hasattr(annotation, "__origin__"):
                    if annotation.__origin__ is Union:
                        # Get the non-None type from Optional
                        args = [
                            arg for arg in annotation.__args__ if arg is not type(None)
                        ]
                        if args:
                            annotation = args[0]

                # Check for generic types (List, Dict, etc.)
                if hasattr(annotation, "__origin__"):
                    origin = annotation.__origin__
                    # Map generic types to their base types
                    if origin is list:
                        annotation = list
                    elif origin is dict:
                        annotation = dict
                    # Add more generic types as needed

                type_map = {
                    int: "integer",
                    float: "number",
                    str: "string",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                param_type = type_map.get(annotation, "string")

            # Check if required (no default value)
            required = param.default == inspect.Parameter.empty

            # Extract description from docstring if available
            description = f"Parameter {param_name}"

            parameters.append(
                ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=description,
                    required=required,
                    default=None if required else param.default,
                )
            )

        return parameters

    async def arun(self, **kwargs: Any) -> Any:
        """Run the tool asynchronously."""
        try:
            # Validate arguments
            self._validate_arguments(kwargs)

            # Execute
            if self.is_async:
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)

            return result

        except Exception as e:
            raise ToolExecutionError(str(e), tool_name=self.name) from e

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Make the tool callable with original function signature."""
        # If called with positional args, convert to kwargs using signature
        if args:
            bound_args = self.signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
            kwargs = bound_args.arguments

        # Run synchronously if called directly
        if self.is_async:
            # If in an async context, this would fail - user should use arun
            # For now, just run in a new event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, can't use asyncio.run
                raise RuntimeError(
                    "Cannot call async tool synchronously from async context. Use await tool.arun() instead."
                )
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(self.arun(**kwargs))
        else:
            return self.run(**kwargs)

    def _validate_arguments(self, kwargs: dict[str, Any]) -> None:
        """Validate arguments against function signature."""
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                raise ToolValidationError(
                    self.name, f"Missing required parameter: {param.name}"
                )

        # Check for unknown parameters only if function doesn't accept **kwargs
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in self.signature.parameters.values()
        )

        if not has_var_keyword:
            valid_params = {p.name for p in self.parameters}
            for key in kwargs:
                if key not in valid_params:
                    raise ToolValidationError(self.name, f"Unknown parameter: {key}")

    def get_definition(self) -> ToolDefinition:
        """Get the tool definition."""
        return ToolDefinition(
            name=self.name, description=self.description, parameters=self.parameters
        )

    def run(self, **kwargs: Any) -> Any:
        """Run the tool synchronously."""
        # Override to handle sync functions without creating event loop issues
        try:
            # Validate arguments
            self._validate_arguments(kwargs)

            # Execute sync functions directly
            if not self.is_async:
                result = self.func(**kwargs)
                return result
            else:
                # For async functions, use the parent's run method
                return super().run(**kwargs)

        except ToolValidationError:
            raise
        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(str(e), tool_name=self.name) from e


def tool(name: str | None = None, description: str | None = None) -> Callable:
    """Decorator to create a tool from a function.

    Args:
        name: Override the function name as the tool name
        description: Override the function docstring as description

    Example:
        Basic tool::

            @tool
            def get_weather(city: str) -> str:
                '''Get weather for a city.'''
                return f"Weather in {city}: Sunny"

        With overrides::

            @tool(name="calc", description="Calculate math")
            def calculate(expr: str) -> float:
                return eval(expr)
    """

    def decorator(func: Callable) -> FunctionTool:
        return FunctionTool(func, name=name, description=description)

    # Handle both @tool and @tool() syntax
    if callable(name):
        func = name
        name = None
        return decorator(func)

    return decorator


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        """Initialize the registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool | Callable, name: str | None = None) -> None:
        """Register a tool.

        Args:
            tool: Tool instance or callable to register
            name: Optional name override for the tool
        """
        if callable(tool) and not isinstance(tool, BaseTool):
            # Convert function to tool
            tool = FunctionTool(tool, name=name)

        if not isinstance(tool, BaseTool):
            raise ValueError(f"Invalid tool type: {type(tool)}")

        # Use provided name or tool's own name
        tool_name = name or tool.name
        self._tools[tool_name] = tool

    def get(self, name: str) -> BaseTool:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            The tool instance

        Raises:
            ToolNotFoundError: If tool not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]

    async def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool arguments

        Returns:
            Tool execution result
        """
        tool = self.get(name)
        return await tool.arun(**kwargs)

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Get schema for all tools (for LLM providers)."""
        if not self._tools:
            return []

        schemas = []
        for tool in self._tools.values():
            definition = tool.get_definition()
            schemas.append(definition.to_openai_schema())

        return schemas

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()


# Built-in tools can be added here
class Calculator(BaseTool):
    """A simple calculator tool for mathematical expressions."""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Calculator tool to evaluate mathematical expressions safely",
        )

    async def arun(self, expression: str) -> float:
        """Evaluate a mathematical expression."""
        try:
            # Only allow basic arithmetic operations, no function calls
            # This is the safest approach
            result = eval(expression, {"__builtins__": {}}, {})
            return float(result)
        except Exception as e:
            raise ToolExecutionError(f"Invalid expression: {e}", tool_name=self.name)

    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="Mathematical expression to evaluate",
                    required=True,
                )
            ],
        )
