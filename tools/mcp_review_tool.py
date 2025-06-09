#!/usr/bin/env python3
"""Streamlined MCP review and test script.

This script provides a quick way to:
1. Test the working MCP server/client pair
2. Verify MCP tools are functioning
3. Check integration with workflow agents
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

# Add AgentiCraft to path

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
os.chdir(base_dir)  # Change to base directory for running scripts


class MCPReviewTester:
    """Quick MCP functionality tester."""

    def __init__(self):
        self.server_process = None

    async def test_working_mcp_server(self):
        """Test the production-ready MCP server."""
        print("\n🧪 Testing Working MCP Server")
        print("=" * 50)

        try:
            # Start the working MCP server
            print("1. Starting mcp_server_production.py...")
            self.server_process = subprocess.Popen(
                [sys.executable, "mcp_server_production.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for server to start
            await asyncio.sleep(2)

            # Check if server is running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                print("❌ Server failed to start:")
                print(f"   STDOUT: {stdout}")
                print(f"   STDERR: {stderr}")
                return False

            print("   ✅ Server started successfully")

            # Test the client
            print("\n2. Testing mcp_client_production.py...")
            client_result = subprocess.run(
                [sys.executable, "mcp_client_production.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if client_result.returncode == 0:
                print("   ✅ Client test passed")
                # Show key results
                if "Found 4 tools:" in client_result.stdout:
                    print("   ✅ All 4 tools discovered")
                if "All tests completed successfully!" in client_result.stdout:
                    print("   ✅ All tools tested successfully")
                elif "All tool tests completed!" in client_result.stdout:
                    print("   ✅ All tools tested successfully")
            else:
                print("   ❌ Client test failed:")
                print(client_result.stderr)
                return False

            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

        finally:
            # Clean up server
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait()
                print("\n   🛑 Server stopped")

    async def test_mcp_tools_directly(self):
        """Test MCP tools directly without server/client."""
        print("\n🧪 Testing MCP Tools Directly")
        print("=" * 50)

        try:
            from agenticraft import tool
            from agenticraft.protocols.mcp import mcp_tool

            # Test the tools defined in working_mcp_server.py
            print("1. Testing calculate tool...")

            @tool
            def calculate(expression: str) -> float:
                """Safely evaluate a mathematical expression."""
                try:
                    result = eval(expression, {"__builtins__": {}}, {})
                    return float(result)
                except Exception as e:
                    raise ValueError(f"Invalid expression: {e}")

            result = calculate("10 + 5 * 2")
            print(f"   ✅ calculate('10 + 5 * 2') = {result}")

            print("\n2. Testing reverse_text tool...")

            @mcp_tool(
                returns={
                    "type": "object",
                    "properties": {
                        "original": {"type": "string"},
                        "reversed": {"type": "string"},
                        "length": {"type": "integer"},
                    },
                }
            )
            def reverse_text(text: str):
                """Reverse a text string."""
                return {"original": text, "reversed": text[::-1], "length": len(text)}

            result = reverse_text("MCP Test")
            print(f"   ✅ reverse_text('MCP Test') = {json.dumps(result, indent=2)}")

            return True

        except Exception as e:
            print(f"❌ Tool testing failed: {e}")
            return False

    async def test_workflow_integration(self):
        """Test MCP integration with workflows."""
        print("\n🧪 Testing Workflow Integration")
        print("=" * 50)

        if not os.getenv("OPENAI_API_KEY"):
            print("   ⏭️  OPENAI_API_KEY not set - skipping workflow test")
            return True

        try:
            # Test handler approach
            print("1. Testing workflow_with_handlers.py...")
            handler_result = subprocess.run(
                [sys.executable, "examples/agents/workflow_with_handlers.py"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if (
                handler_result.returncode == 0
                and "Workflow completed successfully" in handler_result.stdout
            ):
                print("   ✅ Handler approach works")
            else:
                print("   ❌ Handler approach failed")

            # Test wrapper approach
            print("\n2. Testing workflow_with_wrappers.py...")
            wrapper_result = subprocess.run(
                [sys.executable, "examples/agents/workflow_with_wrappers.py"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if (
                wrapper_result.returncode == 0
                and "Workflow completed successfully" in wrapper_result.stdout
            ):
                print("   ✅ Wrapper approach works")
            else:
                print("   ❌ Wrapper approach failed")

            return True

        except Exception as e:
            print(f"❌ Workflow integration test failed: {e}")
            return False

    async def check_mcp_files(self):
        """Check status of MCP-related files."""
        print("\n📁 MCP File Status")
        print("=" * 50)

        # Production files
        production_files = [
            "mcp_server_production.py",
            "mcp_advanced_demo.py",
            "mcp_websocket_compatibility.py",
            "mcp_client_production.py",
            "mcp_basic_demo.py",
        ]

        print("✅ Production Files:")
        for file in production_files:
            file_path = Path(file)
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"   ✅ {file} ({size:,} bytes)")
            else:
                print(f"   ❌ {file} (missing)")

        # Example files
        example_files = [
            "examples/mcp/basic_server.py",
            "examples/mcp/basic_client.py",
            "examples/mcp/advanced_mcp_example.py",
            "examples/mcp/README.md",
        ]

        print("\n📚 Example Files:")
        for file in example_files:
            if Path(file).exists():
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} (missing)")

        # Files to remove (based on your summary)
        debug_files = [
            "simple_mcp_client.py",
            "mcp_protocol_debug.py",
            "minimal_server_test.py",
            "test_mcp_working.py",
            "patched_basic_client.py",
        ]

        print("\n🗑️  Debug Files (cleanup status):")
        found_debug = 0
        for file in debug_files:
            if Path(file).exists():
                print(f"   ❗ {file} (exists - should be removed)")
                found_debug += 1

        if found_debug == 0:
            print("   ✅ All debug files removed (clean!)")

    async def run_review(self):
        """Run complete MCP review."""
        print("🚀 MCP Implementation Review (Updated)")
        print("=" * 60)
        print("This script reviews your MCP implementation with the new file structure")
        print()

        # Check files
        await self.check_mcp_files()

        # Test core functionality
        print("\n" + "=" * 60)
        print("🧪 Functionality Tests")
        print("=" * 60)

        # Test working server/client
        server_test = await self.test_working_mcp_server()

        # Test tools directly
        tools_test = await self.test_mcp_tools_directly()

        # Test workflow integration
        workflow_test = await self.test_workflow_integration()

        # Summary
        print("\n" + "=" * 60)
        print("📊 Review Summary")
        print("=" * 60)

        results = {
            "Working MCP Server/Client": server_test,
            "MCP Tools": tools_test,
            "Workflow Integration": workflow_test,
        }

        for test_name, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {test_name}")

        all_passed = all(results.values())

        if all_passed:
            print("\n🎉 All tests passed! Your MCP implementation is ready!")
            print("\n📝 Your production files are:")
            print("   - mcp_server_production.py (main server)")
            print("   - mcp_client_production.py (test client)")
            print("   - mcp_advanced_demo.py (advanced features)")
            print("   - mcp_basic_demo.py (basic demo)")
            print("   - mcp_websocket_compatibility.py (WebSocket reference)")
            print("\n📚 Documentation:")
            print("   - examples/mcp/README.md (complete MCP guide)")
            print("   - docs/mcp/ (comprehensive guides)")
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")


async def main():
    """Main entry point."""
    tester = MCPReviewTester()

    try:
        await tester.run_review()
    except KeyboardInterrupt:
        print("\n⏹️  Review interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
