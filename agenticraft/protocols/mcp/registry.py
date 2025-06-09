"""MCP tool registry for managing tool registrations.

This module provides a registry for MCP tools that can be shared
between clients and servers.
"""

import logging
from typing import Any

from ...core.exceptions import ToolError, ToolNotFoundError
from ...core.tool import BaseTool
from .types import MCPTool, MCPToolParameter

logger = logging.getLogger(__name__)


class MCPRegistry:
    """Registry for MCP tools.

    This registry manages MCP tool definitions and provides
    methods for tool discovery and validation.
    """

    def __init__(self):
        """Initialize the MCP registry."""
        self._tools: dict[str, MCPTool] = {}
        self._categories: dict[str, set[str]] = {}
        self._adapters: dict[str, BaseTool] = {}

    def register_mcp_tool(self, tool: MCPTool, category: str | None = None) -> None:
        """Register an MCP tool.

        Args:
            tool: MCP tool to register
            category: Optional category for organization
        """
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing MCP tool: {tool.name}")

        self._tools[tool.name] = tool

        if category:
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(tool.name)

        logger.info(f"Registered MCP tool: {tool.name}")

    def register_agenticraft_tool(
        self, tool: BaseTool, category: str | None = None
    ) -> None:
        """Register an AgentiCraft tool as MCP tool.

        Args:
            tool: AgentiCraft tool to register
            category: Optional category
        """
        # Convert to MCP tool
        mcp_tool = self._convert_to_mcp_tool(tool)
        self.register_mcp_tool(mcp_tool, category)

        # Store adapter
        self._adapters[tool.name] = tool

    def _convert_to_mcp_tool(self, tool: BaseTool) -> MCPTool:
        """Convert AgentiCraft tool to MCP tool."""
        definition = tool.get_definition()

        parameters = []
        for param in definition.parameters:
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
            name=definition.name,
            description=definition.description,
            parameters=parameters,
        )

    def get_tool(self, name: str) -> MCPTool:
        """Get an MCP tool by name.

        Args:
            name: Tool name

        Returns:
            MCP tool

        Raises:
            ToolNotFoundError: If tool not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]

    def get_adapter(self, name: str) -> BaseTool | None:
        """Get AgentiCraft adapter for a tool.

        Args:
            name: Tool name

        Returns:
            AgentiCraft tool adapter if available
        """
        return self._adapters.get(name)

    def list_tools(self, category: str | None = None) -> list[str]:
        """List tool names.

        Args:
            category: Optional category filter

        Returns:
            List of tool names
        """
        if category:
            return list(self._categories.get(category, set()))
        return list(self._tools.keys())

    def list_categories(self) -> list[str]:
        """List available categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def get_tools_by_category(self, category: str) -> list[MCPTool]:
        """Get all tools in a category.

        Args:
            category: Category name

        Returns:
            List of MCP tools
        """
        tool_names = self._categories.get(category, set())
        return [self._tools[name] for name in tool_names if name in self._tools]

    def search_tools(self, query: str) -> list[MCPTool]:
        """Search for tools by name or description.

        Args:
            query: Search query

        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        matches = []

        for tool in self._tools.values():
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
            ):
                matches.append(tool)

        return matches

    def validate_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Validate tool call arguments.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Raises:
            ToolNotFoundError: If tool not found
            ToolError: If arguments are invalid
        """
        tool = self.get_tool(tool_name)

        # Check required parameters
        required_params = {param.name for param in tool.parameters if param.required}
        provided_params = set(arguments.keys())

        missing = required_params - provided_params
        if missing:
            raise ToolError(f"Missing required parameters for {tool_name}: {missing}")

        # Check parameter types (basic validation)
        for param in tool.parameters:
            if param.name in arguments:
                value = arguments[param.name]

                # Check enum values
                if param.enum and value not in param.enum:
                    raise ToolError(
                        f"Invalid value for {param.name}: {value}. "
                        f"Must be one of: {param.enum}"
                    )

    def export_tools(self) -> dict[str, Any]:
        """Export all tools as JSON-serializable dict.

        Returns:
            Dictionary of tools
        """
        return {
            "tools": [tool.to_json_schema() for tool in self._tools.values()],
            "categories": {cat: list(tools) for cat, tools in self._categories.items()},
        }

    def import_tools(self, data: dict[str, Any]) -> None:
        """Import tools from exported data.

        Args:
            data: Exported tools data
        """
        # Clear existing
        self._tools.clear()
        self._categories.clear()

        # Import tools
        for tool_data in data.get("tools", []):
            tool = MCPTool(**tool_data)
            self._tools[tool.name] = tool

        # Import categories
        for category, tool_names in data.get("categories", {}).items():
            self._categories[category] = set(tool_names)

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()
        self._adapters.clear()

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if tool is registered."""
        return tool_name in self._tools


# Global registry instance
_global_registry = MCPRegistry()


def get_global_registry() -> MCPRegistry:
    """Get the global MCP registry instance.

    Returns:
        Global MCP registry
    """
    return _global_registry
