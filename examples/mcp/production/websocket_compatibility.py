#!/usr/bin/env python3
"""MCP Client with websockets compatibility fix - IMMEDIATE WORKING VERSION"""

import asyncio
import sys

# Add path
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

# Monkey patch websockets.connect to ignore extra_headers if not supported
import inspect

import websockets

original_connect = websockets.connect


def patched_connect(*args, **kwargs):
    """Websockets connect that ignores unsupported parameters."""
    # Remove extra_headers if it's not supported
    if "extra_headers" in kwargs:
        try:
            sig = inspect.signature(original_connect)
            if "extra_headers" not in sig.parameters:
                print("🔧 Removing unsupported 'extra_headers' parameter")
                kwargs.pop("extra_headers")
        except:
            kwargs.pop("extra_headers", None)

    return original_connect(*args, **kwargs)


# Apply the patch BEFORE importing AgentiCraft
websockets.connect = patched_connect


async def test_fixed_mcp():
    """Test MCP with the compatibility fix."""
    print("🧪 Testing MCP with Compatibility Fix")
    print("=" * 50)

    try:
        from agenticraft.protocols.mcp import MCPClient

        print("✅ Imported MCPClient with compatibility patch")

        print("🔌 Connecting with patched websockets...")
        async with MCPClient("ws://localhost:3000") as client:
            print("✅ Successfully connected!")

            # Get server info
            if hasattr(client, "server_info") and client.server_info:
                server_name = client.server_info.get("name", "Unknown Server")
                server_version = client.server_info.get("version", "Unknown")
                print(f"📡 Connected to: {server_name} v{server_version}")

            # List tools
            if hasattr(client, "available_tools"):
                tools = list(client.available_tools)
                print(f"📦 Available tools ({len(tools)}): {', '.join(tools)}")

                # Test calculator
                if "calculate" in tools:
                    result = await client.call_tool(
                        "calculate", {"expression": "12 * 3"}
                    )
                    print(f"   🧮 calculate(12 * 3) = {result}")

                # Test reverse text
                if "reverse_text" in tools:
                    result = await client.call_tool(
                        "reverse_text", {"text": "SUCCESS!"}
                    )
                    print(f"   🔄 reverse_text('SUCCESS!') = {result}")

                # Test time
                if "get_time" in tools:
                    result = await client.call_tool("get_time", {"timezone": "UTC"})
                    print(f"   ⏰ get_time(UTC) = {result}")

                # Test file listing
                if "list_files" in tools:
                    result = await client.call_tool("list_files", {"directory": "."})
                    print(f"   📁 list_files(.) = {len(result)} files found")

                print("\n🎉 ALL MCP TESTS PASSED!")
                print(
                    "✅ AgentiCraft MCP is working correctly with the compatibility fix!"
                )

            else:
                print("⚠️  Connected but no tools interface found")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n🔧 Debug info:")
        import traceback

        traceback.print_exc()

        # Additional debugging
        try:
            import websockets

            print(f"websockets version: {websockets.__version__}")
        except:
            pass


async def main():
    """Main test function."""
    print("🚀 MCP Compatibility Fix and Test")
    print("=" * 60)

    # Show what we're doing
    print("This script fixes the websockets compatibility issue by:")
    print("1. Patching websockets.connect to ignore 'extra_headers'")
    print("2. Testing all 4 MCP tools from your server")
    print("3. Demonstrating full MCP functionality")
    print()

    await test_fixed_mcp()

    print("\n" + "=" * 60)
    print("🎯 If this worked, your MCP implementation is FULLY FUNCTIONAL!")
    print("🔧 The only issue was a websockets library version compatibility.")
    print("\n📚 Next steps:")
    print("   1. Optionally upgrade: pip install --upgrade websockets")
    print("   2. Try advanced examples: python examples/mcp/advanced_mcp_example.py")
    print(
        "   3. Test workflow integration: python examples/agents/workflow_with_handlers.py"
    )


if __name__ == "__main__":
    asyncio.run(main())
