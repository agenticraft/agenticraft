#!/usr/bin/env python3
"""Test WebSocket transport for MCP protocol.

This script tests the WebSocket transport layer to ensure
proper communication between MCP clients and servers.
"""

import asyncio
import logging
from typing import Any

from agenticraft import tool
from agenticraft.protocols.mcp import MCPClient, MCPServer

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Test tools
@tool
def echo(message: str) -> str:
    """Echo back the message."""
    return f"Echo: {message}"


@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@tool
async def async_delay(seconds: float, message: str = "Done") -> str:
    """Async tool that delays before returning."""
    await asyncio.sleep(seconds)
    return f"{message} after {seconds}s delay"


async def test_websocket_transport():
    """Test WebSocket transport functionality."""
    print("\n🧪 WebSocket Transport Test")
    print("=" * 50)

    # Check if websockets is available
    try:
        import websockets

        print("✅ websockets library available")
    except ImportError:
        print("❌ websockets library not found")
        print("   Install with: pip install websockets")
        return False

    # Create server
    server = MCPServer(
        name="WebSocket Test Server",
        version="1.0.0",
        description="Testing WebSocket transport",
    )

    # Register test tools
    server.register_tools([echo, add_numbers, async_delay])
    print("📦 Registered 3 test tools")

    # Start server
    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3003))
    print("🚀 Started WebSocket server on ws://localhost:3003")

    # Give server time to start
    await asyncio.sleep(0.5)

    success = True

    try:
        # Test 1: Basic connection
        print("\n1️⃣ Testing basic connection...")
        async with MCPClient("ws://localhost:3003") as client:
            print(f"   ✅ Connected to {client.server_info.name}")
            assert client.server_info is not None
            assert len(client.available_tools) == 3
            print(f"   ✅ Discovered {len(client.available_tools)} tools")

        # Test 2: Tool execution
        print("\n2️⃣ Testing tool execution...")
        async with MCPClient("ws://localhost:3003") as client:
            # Test echo
            result = await client.call_tool("echo", {"message": "Hello MCP!"})
            print(f"   Echo result: {result}")
            assert result == "Echo: Hello MCP!"
            print("   ✅ Echo tool works")

            # Test add_numbers
            result = await client.call_tool("add_numbers", {"a": 10, "b": 32})
            print(f"   Add result: {result}")
            assert result == 42
            print("   ✅ Add tool works")

            # Test async tool
            result = await client.call_tool(
                "async_delay", {"seconds": 0.5, "message": "Async complete"}
            )
            print(f"   Async result: {result}")
            assert "Async complete" in result
            print("   ✅ Async tool works")

        # Test 3: Multiple concurrent connections
        print("\n3️⃣ Testing concurrent connections...")

        async def client_task(client_id: int) -> dict[str, Any]:
            """Run client operations."""
            async with MCPClient("ws://localhost:3003") as client:
                results = {}

                # Each client makes different calls
                if client_id % 2 == 0:
                    results["echo"] = await client.call_tool(
                        "echo", {"message": f"Client {client_id}"}
                    )
                else:
                    results["add"] = await client.call_tool(
                        "add_numbers", {"a": client_id, "b": client_id * 2}
                    )

                return results

        # Run 5 concurrent clients
        tasks = [client_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        print(f"   ✅ All {len(results)} clients completed successfully")
        for i, result in enumerate(results):
            print(f"      Client {i}: {result}")

        # Test 4: Error handling
        print("\n4️⃣ Testing error handling...")
        async with MCPClient("ws://localhost:3003") as client:
            # Test invalid tool
            try:
                await client.call_tool("nonexistent", {})
                print("   ❌ Should have raised error")
                success = False
            except Exception as e:
                print(f"   ✅ Caught expected error: {e}")

            # Test invalid parameters
            try:
                await client.call_tool("add_numbers", {"x": 1})  # Wrong params
                print("   ❌ Should have raised error")
                success = False
            except Exception as e:
                print(f"   ✅ Caught expected error: {e}")

        # Test 5: Connection recovery
        print("\n5️⃣ Testing connection recovery...")
        client = MCPClient("ws://localhost:3003")
        await client.connect()

        # Make a call
        result = await client.call_tool("echo", {"message": "Before disconnect"})
        print(f"   Initial call: {result}")

        # Simulate disconnect and reconnect
        if client._ws:
            await client._ws.close()
            client._ws = None

        # Try to reconnect
        await client.disconnect()
        await client.connect()

        # Make another call
        result = await client.call_tool("echo", {"message": "After reconnect"})
        print(f"   After reconnect: {result}")
        print("   ✅ Recovery successful")

        await client.disconnect()

        # Test 6: Large payload
        print("\n6️⃣ Testing large payloads...")
        async with MCPClient("ws://localhost:3003") as client:
            large_message = "x" * 10000  # 10KB message
            result = await client.call_tool("echo", {"message": large_message})
            assert len(result) > 10000
            print(f"   ✅ Successfully handled {len(result)} byte response")

        print("\n✅ All WebSocket transport tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        success = False

    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        print("\n🛑 Server stopped")

    return success


async def test_performance():
    """Test WebSocket performance."""
    print("\n⚡ Performance Test")
    print("=" * 50)

    server = MCPServer()
    server.register_tool(echo)

    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3004))
    await asyncio.sleep(0.5)

    try:
        async with MCPClient("ws://localhost:3004") as client:
            # Warm up
            await client.call_tool("echo", {"message": "warmup"})

            # Time 100 calls
            import time

            start = time.time()

            for i in range(100):
                await client.call_tool("echo", {"message": f"msg{i}"})

            elapsed = time.time() - start
            calls_per_second = 100 / elapsed

            print(f"   Completed 100 calls in {elapsed:.2f}s")
            print(f"   Performance: {calls_per_second:.1f} calls/second")
            print(f"   Average latency: {elapsed/100*1000:.1f}ms per call")

            if calls_per_second > 50:
                print("   ✅ Performance is good!")
            else:
                print("   ⚠️  Performance could be improved")

    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


async def main():
    """Run all WebSocket transport tests."""
    print("🔌 MCP WebSocket Transport Test Suite")
    print("=" * 60)

    # Run tests
    success = await test_websocket_transport()

    if success:
        await test_performance()
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
