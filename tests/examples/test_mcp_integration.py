#!/usr/bin/env python3
"""Comprehensive MCP integration test.

This script verifies that all MCP components are working correctly
together, including types, server, client, adapters, and registry.
"""

import asyncio
from typing import Any

from agenticraft import tool
from agenticraft.protocols.mcp import (
    MCPClient,
    MCPServer,
    get_global_registry,
    mcp_tool,
    wrap_function_as_mcp_tool,
)
from agenticraft.protocols.mcp.types import (
    MCPMethod,
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPToolParameter,
)


# Test tools with various features
@mcp_tool(
    returns={"type": "string"},
    examples=[{"input": {"text": "hello"}, "output": "HELLO"}],
)
def uppercase_tool(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()


@tool
async def async_calculator(operation: str, a: float, b: float) -> float:
    """Perform async calculation."""
    await asyncio.sleep(0.1)  # Simulate async work

    ops = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float("inf"),
    }

    return ops.get(operation, lambda x, y: 0)(a, b)


def plain_function(name: str, age: int = 25) -> dict[str, Any]:
    """A plain Python function to wrap."""
    return {"name": name, "age": age, "adult": age >= 18}


async def run_integration_tests():
    """Run comprehensive MCP integration tests."""
    print("🧪 MCP Integration Test Suite")
    print("=" * 60)

    test_results = {"passed": 0, "failed": 0, "errors": []}

    # Test 1: Type System
    print("\n1️⃣ Testing Type System...")
    try:
        # Create request
        request = MCPRequest(method=MCPMethod.LIST_TOOLS, params={"category": "test"})
        assert request.jsonrpc == "2.0"
        assert request.method == MCPMethod.LIST_TOOLS
        print("   ✅ Request creation works")

        # Create response
        response = MCPResponse(id=request.id, result={"tools": []})
        assert not response.is_error
        print("   ✅ Response creation works")

        # Create MCP tool
        mcp_tool_obj = MCPTool(
            name="test_tool",
            description="Test tool",
            parameters=[MCPToolParameter(name="param1", type="string", required=True)],
        )
        schema = mcp_tool_obj.to_json_schema()
        assert schema["name"] == "test_tool"
        assert "inputSchema" in schema
        print("   ✅ MCP tool types work")

        test_results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Type system test failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Type system: {e}")

    # Test 2: Server and Client Communication
    print("\n2️⃣ Testing Server/Client Communication...")
    server = MCPServer(name="Integration Test Server", version="1.0.0")

    # Register various tools
    server.register_tool(uppercase_tool)
    server.register_tool(async_calculator)

    # Start server
    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3006))
    await asyncio.sleep(0.5)

    try:
        async with MCPClient("ws://localhost:3006") as client:
            # Test connection
            assert client.server_info is not None
            assert client.server_info.name == "Integration Test Server"
            print("   ✅ Client connects successfully")

            # Test tool discovery
            tools = client.available_tools
            assert "uppercase_tool" in tools
            assert "async_calculator" in tools
            print(f"   ✅ Discovered {len(tools)} tools")

            # Test tool execution
            result = await client.call_tool("uppercase_tool", {"text": "test"})
            assert result == "TEST"
            print("   ✅ Sync tool execution works")

            # Test async tool
            result = await client.call_tool(
                "async_calculator", {"operation": "multiply", "a": 6, "b": 7}
            )
            assert result == 42
            print("   ✅ Async tool execution works")

            test_results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Server/Client test failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Server/Client: {e}")
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    # Test 3: Tool Adapters
    print("\n3️⃣ Testing Tool Adapters...")
    try:
        # Wrap plain function
        wrapped = wrap_function_as_mcp_tool(
            plain_function,
            name="person_info",
            description="Get person information",
            returns={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "adult": {"type": "boolean"},
                },
            },
        )

        # Test wrapped function
        result = await wrapped.arun(name="Alice", age=30)
        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["adult"] is True
        print("   ✅ Function wrapper works")

        # Get MCP tool representation
        mcp_representation = wrapped.get_mcp_tool()
        assert mcp_representation.name == "person_info"
        assert len(mcp_representation.parameters) == 2
        print("   ✅ MCP tool conversion works")

        test_results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Adapter test failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Adapters: {e}")

    # Test 4: Registry
    print("\n4️⃣ Testing Registry...")
    try:
        # Get global registry
        registry = get_global_registry()
        registry.clear()  # Start fresh

        # Register tools
        registry.register_agenticraft_tool(uppercase_tool, category="text")
        registry.register_agenticraft_tool(async_calculator, category="math")

        # Test registry operations
        assert len(registry) == 2
        assert "text" in registry.list_categories()
        assert "math" in registry.list_categories()
        print("   ✅ Tool registration works")

        # Test search
        results = registry.search_tools("calc")
        assert len(results) == 1
        assert results[0].name == "async_calculator"
        print("   ✅ Tool search works")

        # Test validation
        registry.validate_tool_call("uppercase_tool", {"text": "hello"})
        print("   ✅ Validation works")

        # Test export/import
        exported = registry.export_tools()
        assert "tools" in exported
        assert "categories" in exported

        # Clear and reimport
        registry.clear()
        registry.import_tools(exported)
        assert len(registry) == 2
        print("   ✅ Export/Import works")

        test_results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Registry test failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Registry: {e}")

    # Test 5: Error Handling
    print("\n5️⃣ Testing Error Handling...")
    server2 = MCPServer()
    server2.register_tool(uppercase_tool)

    server_task2 = asyncio.create_task(
        server2.start_websocket_server("localhost", 3007)
    )
    await asyncio.sleep(0.5)

    try:
        async with MCPClient("ws://localhost:3007") as client:
            # Test tool not found
            try:
                await client.call_tool("nonexistent", {})
                print("   ❌ Should have raised ToolNotFoundError")
                test_results["failed"] += 1
            except Exception:
                print("   ✅ Tool not found error works")

            # Test invalid parameters
            try:
                await client.call_tool("uppercase_tool", {})  # Missing required param
                print("   ❌ Should have raised error for missing params")
                test_results["failed"] += 1
            except Exception:
                print("   ✅ Parameter validation works")

            test_results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Error handling: {e}")
    finally:
        server_task2.cancel()
        try:
            await server_task2
        except asyncio.CancelledError:
            pass

    # Test 6: Integration with AgentiCraft Tools
    print("\n6️⃣ Testing AgentiCraft Integration...")
    try:
        from agenticraft import Agent

        # Create a server with mixed tools
        server3 = MCPServer()

        # Regular AgentiCraft tool
        @tool
        def agenticraft_tool(value: int) -> int:
            """Double a value."""
            return value * 2

        server3.register_tools([uppercase_tool, agenticraft_tool])

        server_task3 = asyncio.create_task(
            server3.start_websocket_server("localhost", 3008)
        )
        await asyncio.sleep(0.5)

        async with MCPClient("ws://localhost:3008") as client:
            # Create agent with MCP tools
            agent = Agent(
                name="TestAgent",
                instructions="You are a test agent with MCP tools.",
                tools=client.get_tools(),
            )

            # Test that agent can use the tools
            response = await agent.arun("Convert 'hello world' to uppercase")
            assert "HELLO WORLD" in response.content
            print("   ✅ Agent can use MCP tools")

            test_results["passed"] += 1
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Integration: {e}")
    finally:
        server_task3.cancel()
        try:
            await server_task3
        except asyncio.CancelledError:
            pass

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   ✅ Passed: {test_results['passed']}")
    print(f"   ❌ Failed: {test_results['failed']}")
    print(f"   Total: {test_results['passed'] + test_results['failed']}")

    if test_results["errors"]:
        print("\n❌ Errors:")
        for error in test_results["errors"]:
            print(f"   - {error}")

    if test_results["failed"] == 0:
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print("\n⚠️  Some tests failed")
        return False


async def main():
    """Run the integration test suite."""
    try:
        # Check dependencies
        try:
            import websockets
        except ImportError:
            print("❌ Tests require websockets")
            print("   Install with: pip install websockets")
            return

        success = await run_integration_tests()

        if success:
            print("\n✅ MCP implementation is working correctly!")
        else:
            print("\n❌ MCP implementation has issues")

    except KeyboardInterrupt:
        print("\n👋 Tests interrupted")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
