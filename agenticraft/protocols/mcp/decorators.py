"""MCP-specific decorators for AgentiCraft.

This module provides decorators for adding MCP-specific metadata
to AgentiCraft tools.
"""

from collections.abc import Callable
from typing import Any

from ...core.tool import tool as base_tool


def mcp_tool(
    *args,
    name: str | None = None,
    description: str | None = None,
    returns: dict[str, Any] | None = None,
    examples: list[dict[str, Any]] | None = None,
    **kwargs,
) -> Callable:
    """Decorator for creating MCP tools with additional metadata.

    This is an enhanced version of the @tool decorator that allows
    specifying MCP-specific metadata like return schemas and examples.

    Args:
        name: Override tool name
        description: Override tool description
        returns: JSON schema for return value
        examples: List of input/output examples
        **kwargs: Additional metadata

    Example:
        @mcp_tool(
            returns={"type": "object", "properties": {"result": {"type": "string"}}},
            examples=[{"input": {"text": "hello"}, "output": {"result": "HELLO"}}]
        )
        def uppercase(text: str) -> Dict[str, str]:
            return {"result": text.upper()}
    """

    def decorator(func: Callable) -> Any:
        # Create tool using base decorator
        tool_instance = base_tool(name=name, description=description)(func)

        # Add MCP-specific metadata
        if returns is not None:
            tool_instance._mcp_returns = returns
        if examples is not None:
            tool_instance._mcp_examples = examples

        # Add any additional metadata
        for key, value in kwargs.items():
            setattr(tool_instance, f"_mcp_{key}", value)

        return tool_instance

    # Handle both @mcp_tool and @mcp_tool() syntax
    if (
        len(args) == 1
        and callable(args[0])
        and not any([name, description, returns, examples, kwargs])
    ):
        # Direct decoration: @mcp_tool
        func = args[0]
        return decorator(func)
    else:
        # With parameters: @mcp_tool(...)
        return decorator
