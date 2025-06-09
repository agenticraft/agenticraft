# MCP (Model Context Protocol) Files

## Production Files

### Core Implementation
- **`mcp_server_production.py`** - Production-ready MCP server with WebSocket support
- **`mcp_client_production.py`** - Production-ready MCP client with compatibility fixes
- **`mcp_websocket_compatibility.py`** - WebSocket compatibility reference implementation

### Demo Files
- **`mcp_basic_demo.py`** - Basic MCP demonstration
- **`mcp_advanced_demo.py`** - Advanced MCP features demonstration

### Tools
- **`tools/mcp_review_tool.py`** - MCP implementation review and testing tool

## Quick Start

1. **Start the MCP Server:**
   ```bash
   python mcp_server_production.py
   ```

2. **Test with Client:**
   ```bash
   python mcp_client_production.py
   ```

3. **Review Implementation:**
   ```bash
   # From the AgentiCraft root directory:
   python tools/mcp_review_tool.py
   ```

## Available Tools

The production server exposes 4 tools:
- `calculate` - Evaluate mathematical expressions
- `reverse_text` - Reverse text with metadata
- `get_time` - Get current time in specified timezone
- `list_files` - List files in allowed directories

## Integration with AgentiCraft

See the documentation in `docs/mcp/` for detailed integration guides:
- `tools_handlers_guide.md` - Integration approaches
- `practical_guide.md` - Practical usage examples
- `examples_summary.md` - Complete examples overview

## Example Usage

```python
from agenticraft.protocols.mcp import MCPClient
from agenticraft import Agent

async with MCPClient("ws://localhost:3000") as client:
    # Use tools directly
    result = await client.call_tool("calculate", {"expression": "10 + 5"})
    
    # Or with an agent
    agent = Agent(name="Assistant", tools=client.get_tools())
    response = await agent.say("Calculate 10 + 5")
```
