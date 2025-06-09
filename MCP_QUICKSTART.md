# MCP (Model Context Protocol) Quick Start

The MCP implementation has been organized into the examples directory for better project structure.

## 📁 MCP Files Location

All MCP-related files are now in `examples/mcp/`:

- **Production Files**: `examples/mcp/production/`
  - `server.py` - Production MCP server
  - `client.py` - Production MCP client
  - `websocket_compatibility.py` - WebSocket compatibility reference

- **Demo Files**: `examples/mcp/demos/`
  - `basic_demo.py` - Basic MCP demonstration
  - `advanced_demo.py` - Advanced features demo

- **Documentation**: `docs/mcp/`
  - Integration guides and examples

## 🚀 Quick Start

```bash
# Start MCP server
python examples/mcp/production/server.py

# Test with client (in another terminal)
python examples/mcp/production/client.py
```

## 📚 More Information

- See `examples/mcp/README.md` for detailed examples
- See `examples/mcp/PRODUCTION_README.md` for production usage
- See `docs/mcp/` for comprehensive guides
