#!/usr/bin/env python3
"""Test the WebSocket handler fix"""

import asyncio
import sys
import os

# Add the project path
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

# Set up basic logging
import logging
logging.basicConfig(level=logging.INFO)


async def test_websocket_fix():
    """Test the WebSocket handler fix."""
    from agenticraft import tool
    from agenticraft.protocols.mcp import MCPServer, MCPClient
    
    print("🧪 Testing WebSocket Handler Fix")
    print("=" * 50)
    
    # Create a simple test tool
    @tool
    def test_tool(message: str) -> str:
        """Test tool that echoes a message."""
        return f"Test response: {message}"
    
    # Create server
    server = MCPServer(
        name="Test Server",
        version="1.0.0",
        description="Testing WebSocket handler fix"
    )
    
    # Register tool
    server.register_tool(test_tool)
    print("✅ Server created and tool registered")
    
    # Start server
    server_task = asyncio.create_task(
        server.start_websocket_server("localhost", 3005)
    )
    print("🚀 Starting server on ws://localhost:3005")
    
    # Give server time to start
    await asyncio.sleep(0.5)
    
    try:
        # Test connection
        print("\n📡 Testing connection...")
        async with MCPClient("ws://localhost:3005") as client:
            print(f"✅ Connected to {client.server_info.name}")
            
            # Test tool call
            print("\n🔧 Testing tool call...")
            result = await client.call_tool("test_tool", {"message": "Hello, WebSocket!"})
            print(f"✅ Tool response: {result}")
            
            if result == "Test response: Hello, WebSocket!":
                print("\n🎉 SUCCESS! WebSocket handler fix is working correctly!")
                return True
            else:
                print(f"\n❌ Unexpected response: {result}")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        print("\n🛑 Server stopped")


async def main():
    """Run the test."""
    success = await test_websocket_fix()
    
    if success:
        print("\n✅ The WebSocket handler issue has been fixed!")
        print("You can now run your full test suite.")
    else:
        print("\n❌ The fix didn't work as expected.")
        print("Additional debugging may be needed.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
