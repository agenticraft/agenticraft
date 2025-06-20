"""
Example: Creating MCP Servers for Claude Desktop

This example shows how to create MCP servers that can be used with Claude Desktop.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add AgentiCraft to path
import sys
sys.path.insert(0, '/Users/zahere/Desktop/TLV/agenticraft')

from agenticraft.protocols import MCPServerBuilder
from agenticraft.core.agent import Agent
from agenticraft.tools.web import web_search, extract_text, get_page_metadata
from agenticraft.tools.calculator import calculator
from agenticraft.tools.file_ops import read_file, write_file, list_files


# Example 1: Simple AgentiCraft Tools Server
def create_agenticraft_tools_server():
    """Create an MCP server exposing AgentiCraft tools."""
    
    # Check if MCP SDK is available
    try:
        from mcp.server.fastmcp import FastMCP
        print("✅ MCP SDK is installed")
    except ImportError:
        print("⚠️  MCP SDK not installed. Install with: pip install 'mcp[cli]'")
        print("   Showing what would be created...\n")
        return None
    
    builder = MCPServerBuilder(
        "AgentiCraft Tools",
        "Access AgentiCraft's powerful tool suite through MCP"
    )
    
    # Add web search tool
    @builder.add_tool(description="Search the web for information")
    async def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search the web and return results."""
        # Use the actual web_search tool
        return await web_search(query, max_results)
    
    # Add text analysis tool
    @builder.add_tool(description="Extract and analyze text from URLs")
    async def analyze_url(url: str) -> Dict[str, Any]:
        """Extract and analyze text from a URL."""
        # Use the actual extract_text tool
        result = await extract_text(url, include_links=True)
        metadata = await get_page_metadata(url)
        
        return {
            "content": result,
            "metadata": metadata,
            "analysis": {
                "word_count": result.get("word_count", 0),
                "has_links": len(result.get("links", [])) > 0,
                "language": result.get("language", "unknown")
            }
        }
    
    # Add calculation tool
    @builder.add_tool(description="Perform mathematical calculations")
    async def calculate(expression: str) -> Dict[str, Any]:
        """Evaluate a mathematical expression."""
        # Use the actual calculator tool
        result = await calculator(expression)
        return {
            "expression": expression,
            "result": result,
            "type": type(result).__name__
        }
    
    # Add resources
    @builder.add_resource("tools://list")
    def list_tools() -> str:
        """List all available tools."""
        tools_info = {
            "web": ["search_web", "analyze_url"],
            "math": ["calculate"],
            "total": 3
        }
        return json.dumps(tools_info, indent=2)
    
    @builder.add_resource("config://agenticraft/version")
    def get_version() -> str:
        """Get AgentiCraft version information."""
        return json.dumps({
            "version": "1.0.0",
            "protocols": ["a2a", "mcp"],
            "features": ["tools", "agents", "workflows"]
        })
    
    # Add prompts
    @builder.add_prompt("research_task")
    def research_prompt(topic: str, depth: str = "moderate") -> str:
        """Generate a research task prompt."""
        return f"""Please conduct {depth} research on: {topic}

Requirements:
1. Use search_web to find relevant information
2. Use analyze_url to extract content from promising sources
3. Provide a structured summary with:
   - Key facts and findings
   - Important sources
   - Areas for further investigation
   
Depth level: {depth} (shallow/moderate/deep)
"""
    
    @builder.add_prompt("calculation_task")
    def calc_prompt(problem: str) -> str:
        """Generate a calculation task prompt."""
        return f"""Please solve this mathematical problem: {problem}

Requirements:
1. Break down the problem into steps
2. Use the calculate tool for each step
3. Show your work
4. Provide the final answer with explanation

Problem: {problem}
"""
    
    return builder


# Example 2: Agent-based MCP Server
def create_agent_mcp_server():
    """Create an MCP server from an AgentiCraft agent."""
    
    # Check if MCP SDK is available
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("⚠️  MCP SDK not installed.")
        return None
    
    # Create a research agent
    agent = Agent(
        name="ResearchAssistant",
        model="gpt-4",
        tools=[web_search, extract_text, get_page_metadata],
        system_prompt="""You are a research assistant with access to web search 
        and text extraction tools. Help users find and analyze information."""
    )
    
    builder = MCPServerBuilder(
        "Research Assistant Agent",
        "An AI-powered research assistant accessible through MCP"
    )
    
    # Convert agent to MCP server
    builder.from_agent(agent)
    
    # Add agent-specific tools
    @builder.add_tool(description="Ask the research assistant")
    async def ask_assistant(
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Ask the research assistant any question."""
        response = await agent.execute(question, context=context)
        return response
    
    @builder.add_tool(description="Research a topic in depth")
    async def research_topic(
        topic: str,
        max_sources: int = 5,
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """Research a topic comprehensively."""
        prompt = f"""Research the topic: {topic}
        
        Find up to {max_sources} sources and {'provide analysis' if include_analysis else 'list findings'}.
        """
        
        result = await agent.execute(prompt)
        
        return {
            "topic": topic,
            "findings": result,
            "sources_consulted": max_sources,
            "analysis_included": include_analysis
        }
    
    # Add conversation memory resource
    @builder.add_resource("conversation-history")
    def get_conversation_history() -> str:
        """Get the conversation history."""
        # In a real implementation, this would track actual conversations
        return json.dumps({
            "message": "Conversation history would be tracked here",
            "sessions": 0
        })
    
    return builder


# Example 3: File Operations MCP Server
def create_file_ops_mcp_server():
    """Create an MCP server for file operations."""
    
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("⚠️  MCP SDK not installed.")
        return None
    
    builder = MCPServerBuilder(
        "AgentiCraft File Operations",
        "Safe file operations through MCP"
    )
    
    # Add file operation tools
    @builder.add_tool(description="Read a file")
    async def read_file_content(path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read content from a file."""
        content = await read_file(path, encoding)
        return {
            "path": path,
            "content": content,
            "encoding": encoding,
            "size": len(content)
        }
    
    @builder.add_tool(description="Write to a file")
    async def write_file_content(
        path: str,
        content: str,
        mode: str = "w",
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """Write content to a file."""
        result = await write_file(path, content, mode, encoding)
        return {
            "path": path,
            "success": result.get("success", False),
            "size": len(content),
            "mode": mode
        }
    
    @builder.add_tool(description="List files in directory")
    async def list_directory(
        path: str = ".",
        pattern: str = "*",
        recursive: bool = False
    ) -> List[str]:
        """List files in a directory."""
        files = await list_files(path, pattern, recursive)
        return files
    
    # Add resources
    @builder.add_resource("files://stats")
    def get_file_stats() -> str:
        """Get file operation statistics."""
        return json.dumps({
            "operations": {
                "reads": 0,
                "writes": 0,
                "lists": 0
            },
            "status": "ready"
        })
    
    # Add file operation prompts
    @builder.add_prompt("file_task")
    def file_task_prompt(task: str, path: str) -> str:
        """Generate a file operation task prompt."""
        return f"""Please help with this file task: {task}

Target path: {path}

Available operations:
- read_file_content: Read file contents
- write_file_content: Write or append to files
- list_directory: List files in directories

Please complete the task safely and provide clear feedback.
"""
    
    return builder


def save_server_configs():
    """Save MCP server configurations for Claude Desktop."""
    
    print("📦 Creating MCP Server Configurations")
    print("=" * 60)
    
    servers = []
    
    # Try to create each server
    print("\n1. AgentiCraft Tools Server")
    tools_server = create_agenticraft_tools_server()
    if tools_server:
        servers.append(("agenticraft-tools", tools_server))
        print("   ✅ Created successfully")
    
    print("\n2. Research Assistant Server")
    agent_server = create_agent_mcp_server()
    if agent_server:
        servers.append(("research-assistant", agent_server))
        print("   ✅ Created successfully")
    
    print("\n3. File Operations Server")
    file_server = create_file_ops_mcp_server()
    if file_server:
        servers.append(("file-operations", file_server))
        print("   ✅ Created successfully")
    
    if not servers:
        print("\n⚠️  No servers created. Please install MCP SDK:")
        print("   pip install 'mcp[cli]'")
        return
    
    # Create configs directory
    config_dir = Path("mcp_configs")
    config_dir.mkdir(exist_ok=True)
    
    # Claude Desktop config
    claude_config = {
        "mcpServers": {}
    }
    
    for name, builder in servers:
        # Save individual server script
        server_file = config_dir / f"{name.replace('-', '_')}_server.py"
        
        with open(server_file, 'w') as f:
            f.write(f'''#!/usr/bin/env python3
"""
MCP Server: {builder.name}
{builder.description}

This is a template for the MCP server.
To implement, add the actual tool implementations.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{builder.name}")

# Add your tool implementations here
# Example:
# @mcp.tool()
# async def my_tool(param: str) -> str:
#     return f"Result: {{param}}"

if __name__ == "__main__":
    # For stdio transport (Claude Desktop)
    mcp.run()
''')
        
        # Add to Claude config
        claude_config["mcpServers"][name] = {
            "command": "python",
            "args": [str(server_file.absolute())],
            "name": builder.name,
            "description": builder.description
        }
    
    # Save Claude Desktop config
    claude_config_file = config_dir / "claude_desktop_config.json"
    with open(claude_config_file, 'w') as f:
        json.dump(claude_config, f, indent=2)
    
    print(f"\n✅ MCP server configurations saved to {config_dir}/")
    print(f"\n📝 To use with Claude Desktop:")
    print(f"1. Copy the contents of {claude_config_file}")
    print(f"2. Add to ~/Library/Application Support/Claude/claude_desktop_config.json")
    print(f"3. Restart Claude Desktop")
    
    return config_dir


def main():
    """Create and demonstrate MCP servers."""
    print("🚀 Creating MCP Servers for Claude Desktop")
    print("=" * 60)
    
    # Check if MCP SDK is available
    try:
        from mcp.server.fastmcp import FastMCP
        print("✅ MCP SDK is installed")
    except ImportError:
        print("⚠️  MCP SDK not installed")
        print("\n📦 To install:")
        print("   pip install 'mcp[cli]'")
        print("\n📚 This demo will show what would be created.")
    
    # Save configurations
    print()
    config_dir = save_server_configs()
    
    print("\n🎯 Quick Start:")
    print("1. Install MCP SDK: pip install 'mcp[cli]'")
    if config_dir:
        print(f"2. Test a server: mcp dev {config_dir}/agenticraft_tools_server.py")
        print("3. Add to Claude Desktop using the generated config")
    
    print("\n✅ MCP server setup complete!")


if __name__ == "__main__":
    main()
