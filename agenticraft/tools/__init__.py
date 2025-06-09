"""Built-in tools for AgentiCraft.

This module provides a collection of ready-to-use tools that agents
can leverage for various tasks.

Available tool categories:
- Calculator: Mathematical operations
- File Operations: File reading, writing, and manipulation
- Web: Search and web content extraction

Example:
    Using built-in tools with an agent::

        from agenticraft import Agent
        from agenticraft.tools import simple_calculate, web_search, read_file

        agent = Agent(
            name="researcher",
            tools=[simple_calculate, web_search, read_file]
        )

        response = await agent.arun(
            "Search for Python tutorials and calculate 15% of 1200"
        )
"""

# Calculator tools
from .calculator import scientific_calculate, simple_calculate

# File operation tools
from .file_ops import (
    file_info,
    list_files,
    read_file,
    read_json,
    write_file,
    write_json,
)

# Web tools
from .web import check_url, extract_text, get_page_metadata, web_search

# Export all tools
__all__ = [
    # Calculator
    "simple_calculate",
    "scientific_calculate",
    # File operations
    "read_file",
    "write_file",
    "list_files",
    "read_json",
    "write_json",
    "file_info",
    # Web
    "web_search",
    "extract_text",
    "get_page_metadata",
    "check_url",
]

# Tool collections for convenience
CALCULATOR_TOOLS = [simple_calculate, scientific_calculate]
FILE_TOOLS = [read_file, write_file, list_files, read_json, write_json, file_info]
WEB_TOOLS = [web_search, extract_text, get_page_metadata, check_url]
ALL_TOOLS = CALCULATOR_TOOLS + FILE_TOOLS + WEB_TOOLS
