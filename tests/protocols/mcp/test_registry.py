"""Tests for MCP registry implementation."""

import pytest

from agenticraft import tool
from agenticraft.core.exceptions import ToolNotFoundError, ToolError
from agenticraft.protocols.mcp import MCPRegistry
from agenticraft.protocols.mcp.types import MCPTool, MCPToolParameter


class TestMCPRegistry:
    """Test MCP registry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create test registry."""
        return MCPRegistry()
    
    @pytest.fixture
    def sample_mcp_tool(self):
        """Create sample MCP tool."""
        return MCPTool(
            name="calculator",
            description="Math calculator",
            parameters=[
                MCPToolParameter(
                    name="expression",
                    type="string",
                    required=True
                )
            ]
        )
    
    @pytest.fixture
    def sample_agenticraft_tool(self):
        """Create sample AgentiCraft tool."""
        @tool
        def search(query: str) -> str:
            """Search for information."""
            return f"Results for: {query}"
        return search
    
    def test_register_mcp_tool(self, registry, sample_mcp_tool):
        """Test registering MCP tool."""
        registry.register_mcp_tool(sample_mcp_tool)
        
        assert "calculator" in registry
        assert len(registry) == 1
        
        # Get tool back
        tool = registry.get_tool("calculator")
        assert tool.name == "calculator"
        assert tool.description == "Math calculator"
    
    def test_register_mcp_tool_with_category(self, registry, sample_mcp_tool):
        """Test registering MCP tool with category."""
        registry.register_mcp_tool(sample_mcp_tool, category="math")
        
        assert "math" in registry.list_categories()
        assert "calculator" in registry.list_tools(category="math")
    
    def test_register_agenticraft_tool(self, registry, sample_agenticraft_tool):
        """Test registering AgentiCraft tool."""
        registry.register_agenticraft_tool(sample_agenticraft_tool)
        
        assert "search" in registry
        
        # Get as MCP tool
        mcp_tool = registry.get_tool("search")
        assert mcp_tool.name == "search"
        assert mcp_tool.description == "Search for information."
        
        # Get adapter
        adapter = registry.get_adapter("search")
        assert adapter is not None
        assert adapter.name == "search"
    
    def test_get_nonexistent_tool(self, registry):
        """Test getting non-existent tool."""
        with pytest.raises(ToolNotFoundError):
            registry.get_tool("nonexistent")
    
    def test_list_tools(self, registry, sample_mcp_tool):
        """Test listing tools."""
        # Empty registry
        assert registry.list_tools() == []
        
        # Add tools
        registry.register_mcp_tool(sample_mcp_tool)
        registry.register_mcp_tool(
            MCPTool(name="search", description="Search tool"),
            category="web"
        )
        
        # List all
        tools = registry.list_tools()
        assert len(tools) == 2
        assert "calculator" in tools
        assert "search" in tools
        
        # List by category
        assert registry.list_tools(category="web") == ["search"]
        assert registry.list_tools(category="math") == []
    
    def test_get_tools_by_category(self, registry):
        """Test getting tools by category."""
        # Add tools in categories
        tool1 = MCPTool(name="add", description="Add numbers")
        tool2 = MCPTool(name="multiply", description="Multiply numbers")
        tool3 = MCPTool(name="search", description="Web search")
        
        registry.register_mcp_tool(tool1, category="math")
        registry.register_mcp_tool(tool2, category="math")
        registry.register_mcp_tool(tool3, category="web")
        
        # Get math tools
        math_tools = registry.get_tools_by_category("math")
        assert len(math_tools) == 2
        assert all(t.name in ["add", "multiply"] for t in math_tools)
        
        # Get web tools
        web_tools = registry.get_tools_by_category("web")
        assert len(web_tools) == 1
        assert web_tools[0].name == "search"
    
    def test_search_tools(self, registry):
        """Test searching tools."""
        # Add various tools
        tools = [
            MCPTool(name="calculator", description="Math calculator"),
            MCPTool(name="web_search", description="Search the web"),
            MCPTool(name="file_search", description="Search files"),
            MCPTool(name="weather", description="Get weather info"),
        ]
        
        for t in tools:
            registry.register_mcp_tool(t)
        
        # Search by name
        results = registry.search_tools("search")
        assert len(results) == 2
        names = [r.name for r in results]
        assert "web_search" in names
        assert "file_search" in names
        
        # Search by description
        results = registry.search_tools("math")
        assert len(results) == 1
        assert results[0].name == "calculator"
        
        # Case insensitive
        results = registry.search_tools("WEATHER")
        assert len(results) == 1
        assert results[0].name == "weather"
    
    def test_validate_tool_call(self, registry, sample_mcp_tool):
        """Test validating tool calls."""
        registry.register_mcp_tool(sample_mcp_tool)
        
        # Valid call
        registry.validate_tool_call(
            "calculator",
            {"expression": "2 + 2"}
        )
        
        # Missing required parameter
        with pytest.raises(ToolError, match="Missing required parameters"):
            registry.validate_tool_call("calculator", {})
        
        # Tool not found
        with pytest.raises(ToolNotFoundError):
            registry.validate_tool_call("nonexistent", {})
    
    def test_validate_enum_parameter(self, registry):
        """Test validating enum parameters."""
        tool = MCPTool(
            name="converter",
            description="Unit converter",
            parameters=[
                MCPToolParameter(
                    name="unit",
                    type="string",
                    enum=["meters", "feet", "inches"],
                    required=True
                )
            ]
        )
        registry.register_mcp_tool(tool)
        
        # Valid enum value
        registry.validate_tool_call(
            "converter",
            {"unit": "meters"}
        )
        
        # Invalid enum value
        with pytest.raises(ToolError, match="Must be one of"):
            registry.validate_tool_call(
                "converter",
                {"unit": "kilometers"}
            )
    
    def test_export_import_tools(self, registry):
        """Test exporting and importing tools."""
        # Add tools with categories
        tool1 = MCPTool(name="calc", description="Calculator")
        tool2 = MCPTool(name="search", description="Search")
        
        registry.register_mcp_tool(tool1, category="math")
        registry.register_mcp_tool(tool2, category="web")
        
        # Export
        exported = registry.export_tools()
        assert len(exported["tools"]) == 2
        assert "math" in exported["categories"]
        assert "calc" in exported["categories"]["math"]
        
        # Create new registry and import
        new_registry = MCPRegistry()
        new_registry.import_tools(exported)
        
        assert len(new_registry) == 2
        assert "calc" in new_registry
        assert "search" in new_registry
        assert "calc" in new_registry.list_tools(category="math")
    
    def test_clear_registry(self, registry, sample_mcp_tool):
        """Test clearing registry."""
        registry.register_mcp_tool(sample_mcp_tool)
        assert len(registry) == 1
        
        registry.clear()
        assert len(registry) == 0
        assert registry.list_tools() == []
        assert registry.list_categories() == []
    
    def test_overwrite_tool(self, registry):
        """Test overwriting existing tool."""
        # Register initial tool
        tool1 = MCPTool(name="test", description="Version 1")
        registry.register_mcp_tool(tool1)
        
        # Overwrite with new version
        tool2 = MCPTool(name="test", description="Version 2")
        registry.register_mcp_tool(tool2)
        
        # Should have new version
        tool = registry.get_tool("test")
        assert tool.description == "Version 2"
        assert len(registry) == 1


def test_global_registry():
    """Test global registry singleton."""
    from agenticraft.protocols.mcp.registry import get_global_registry
    
    registry1 = get_global_registry()
    registry2 = get_global_registry()
    
    assert registry1 is registry2  # Same instance
