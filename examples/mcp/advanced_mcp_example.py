#!/usr/bin/env python3
"""Advanced MCP example demonstrating full capabilities.

This example shows:
- WebSocket and HTTP server modes
- Tool discovery and execution
- Integration with AgentiCraft agents
- Streaming responses with MCP tools
- Error handling and retries
"""

import asyncio
import json
import logging
from typing import Any

from agenticraft import Agent, tool
from agenticraft.protocols.mcp import MCPClient, MCPServer, mcp_tool
from agenticraft.protocols.mcp.registry import get_global_registry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define advanced MCP tools with metadata
@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "result": {"type": "number"},
            "steps": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    },
    examples=[
        {
            "input": {"problem": "What is 25% of 80?"},
            "output": {
                "result": 20,
                "steps": ["Convert 25% to decimal: 0.25", "Multiply: 0.25 × 80 = 20"],
                "confidence": 1.0,
            },
        }
    ],
)
async def solve_math_problem(problem: str) -> dict[str, Any]:
    """Solve a math word problem step by step.

    Args:
        problem: Math problem in natural language

    Returns:
        Solution with steps and confidence
    """
    # Simple implementation for demo
    steps = []
    result = 0
    confidence = 0.8

    if "%" in problem and "of" in problem:
        # Handle percentage problems
        import re

        numbers = re.findall(r"\d+", problem)
        if len(numbers) >= 2:
            percentage = float(numbers[0]) / 100
            value = float(numbers[1])
            result = percentage * value
            steps = [
                f"Convert {numbers[0]}% to decimal: {percentage}",
                f"Multiply: {percentage} × {value} = {result}",
            ]
            confidence = 0.95
    else:
        # Try to evaluate simple expressions
        try:
            # Extract numbers and operators
            import re

            expr = re.sub(r"[^\d+\-*/().\s]", "", problem)
            if expr.strip():
                result = eval(expr, {"__builtins__": {}}, {})
                steps = [f"Evaluate expression: {expr} = {result}"]
                confidence = 0.9
        except:
            steps = ["Unable to parse problem"]
            confidence = 0.1

    return {"result": result, "steps": steps, "confidence": confidence}


@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "sentiment": {
                "type": "string",
                "enum": ["positive", "negative", "neutral"],
            },
            "length": {"type": "integer"},
        },
    }
)
async def analyze_text(text: str, max_keywords: int = 5) -> dict[str, Any]:
    """Analyze text and extract insights.

    Args:
        text: Text to analyze
        max_keywords: Maximum keywords to extract

    Returns:
        Analysis results
    """
    # Simple implementation
    words = text.lower().split()

    # Extract keywords (most common non-stop words)
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 3:
            word_freq[word] = word_freq.get(word, 0) + 1

    keywords = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[
        :max_keywords
    ]

    # Simple sentiment
    positive_words = {"good", "great", "excellent", "amazing", "wonderful", "love"}
    negative_words = {"bad", "terrible", "awful", "hate", "horrible", "poor"}

    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)

    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Summary (first 50 chars)
    summary = text[:50] + "..." if len(text) > 50 else text

    return {
        "summary": summary,
        "keywords": keywords,
        "sentiment": sentiment,
        "length": len(text),
    }


@tool
async def search_knowledge_base(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Search internal knowledge base.

    Args:
        query: Search query
        limit: Maximum results

    Returns:
        List of matching documents
    """
    # Mock knowledge base
    knowledge_base = [
        {
            "id": "1",
            "title": "Python Basics",
            "content": "Python is a high-level programming language...",
        },
        {
            "id": "2",
            "title": "Async Programming",
            "content": "Asynchronous programming allows concurrent execution...",
        },
        {
            "id": "3",
            "title": "Machine Learning",
            "content": "ML is a subset of AI that enables learning from data...",
        },
        {
            "id": "4",
            "title": "Web Development",
            "content": "Modern web development involves frontend and backend...",
        },
        {
            "id": "5",
            "title": "Data Science",
            "content": "Data science combines statistics and programming...",
        },
    ]

    # Simple search
    results = []
    query_lower = query.lower()
    for doc in knowledge_base:
        if query_lower in doc["title"].lower() or query_lower in doc["content"].lower():
            results.append(doc)
            if len(results) >= limit:
                break

    await asyncio.sleep(0.1)  # Simulate network delay
    return results


class AdvancedMCPServer:
    """Advanced MCP server with monitoring and metrics."""

    def __init__(self):
        self.server = MCPServer(
            name="Advanced AgentiCraft Server",
            version="2.0.0",
            description="Feature-rich MCP server with analytics",
        )
        self.call_count = {}
        self.error_count = {}

        # Wrap handle_request to add monitoring
        original_handle = self.server.handle_request
        self.server.handle_request = self._monitored_handle_request(original_handle)

    def _monitored_handle_request(self, original_handle):
        """Wrap request handler with monitoring."""

        async def wrapper(request):
            tool_name = None
            if request.method.value == "tools/call":
                tool_name = request.params.get("tool", "unknown")
                self.call_count[tool_name] = self.call_count.get(tool_name, 0) + 1

            try:
                response = await original_handle(request)
                return response
            except Exception:
                if tool_name:
                    self.error_count[tool_name] = self.error_count.get(tool_name, 0) + 1
                raise

        return wrapper

    def get_metrics(self) -> dict[str, Any]:
        """Get server metrics."""
        return {
            "tool_calls": self.call_count,
            "errors": self.error_count,
            "total_calls": sum(self.call_count.values()),
            "total_errors": sum(self.error_count.values()),
        }


async def demonstrate_mcp_integration():
    """Demonstrate full MCP integration."""
    print("\n🚀 Advanced MCP Integration Demo")
    print("=" * 60)

    # 1. Create and start server
    print("\n📡 Starting MCP Server...")
    advanced_server = AdvancedMCPServer()
    server = advanced_server.server

    # Register tools
    tools = [solve_math_problem, analyze_text, search_knowledge_base]
    server.register_tools(tools)

    # Start server in background
    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3001))
    await asyncio.sleep(1)  # Give server time to start

    try:
        # 2. Connect client and discover tools
        print("\n🔌 Connecting MCP Client...")
        async with MCPClient("ws://localhost:3001") as client:
            print(f"✅ Connected to: {client.server_info.name}")
            print(f"   Available tools: {', '.join(client.available_tools)}")

            # 3. Use tools directly
            print("\n🔧 Direct Tool Usage:")

            # Math problem
            math_result = await client.call_tool(
                "solve_math_problem", {"problem": "What is 30% of 150?"}
            )
            print(f"\n📊 Math Result: {json.dumps(math_result, indent=2)}")

            # Text analysis
            text_result = await client.call_tool(
                "analyze_text",
                {
                    "text": "This is an amazing example of MCP integration. It works great!"
                },
            )
            print(f"\n📝 Text Analysis: {json.dumps(text_result, indent=2)}")

            # 4. Create agent with MCP tools
            print("\n🤖 Creating Agent with MCP Tools...")
            agent = Agent(
                name="MCPPoweredAssistant",
                instructions="""You are an AI assistant powered by MCP tools.
                Use your tools to help users with:
                - Math problems (use solve_math_problem)
                - Text analysis (use analyze_text)
                - Knowledge search (use search_knowledge_base)
                
                Always explain what tools you're using and why.""",
                tools=client.get_tools(),
                model="gpt-4o-mini",  # Use appropriate model
            )

            # 5. Test agent with various queries
            test_queries = [
                "Calculate 15% tip on a $85 restaurant bill",
                "Analyze this text: 'The quick brown fox jumps over the lazy dog. This pangram is excellent for testing.'",
                "Search for information about Python programming",
            ]

            print("\n💬 Testing Agent:")
            for query in test_queries:
                print(f"\n👤 User: {query}")
                response = await agent.arun(query)
                print(f"🤖 Assistant: {response.content}")

                if response.tool_calls:
                    print("   📊 Tools used:")
                    for tool_call in response.tool_calls:
                        print(f"      - {tool_call.function.name}")

            # 6. Test streaming with MCP tools
            print("\n🌊 Testing Streaming with MCP Tools:")
            query = "First, calculate 25% of 200, then analyze the sentence 'MCP integration is working perfectly!'"
            print(f"👤 User: {query}")
            print("🤖 Assistant: ", end="", flush=True)

            full_response = ""
            async for chunk in agent.stream(query):
                if chunk.delta:
                    print(chunk.delta, end="", flush=True)
                    full_response += chunk.delta
            print()  # New line after streaming

            # 7. Show server metrics
            print("\n📈 Server Metrics:")
            metrics = advanced_server.get_metrics()
            print(json.dumps(metrics, indent=2))

            # 8. Test the global registry
            print("\n🗂️ Testing Global Registry:")
            registry = get_global_registry()

            # Register tools in registry
            for tool in tools:
                if hasattr(tool, "get_mcp_tool"):
                    mcp_tool = tool.get_mcp_tool()
                    registry.register_mcp_tool(mcp_tool, category="demo")

            print(f"   Registry size: {len(registry)}")
            print(f"   Categories: {registry.list_categories()}")
            print(f"   Demo tools: {registry.list_tools('demo')}")

            # Search in registry
            search_results = registry.search_tools("math")
            print(f"   Search 'math': {[t.name for t in search_results]}")

    finally:
        # Clean up
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    print("\n✅ Advanced MCP Demo Complete!")


async def test_error_handling():
    """Test MCP error handling and recovery."""
    print("\n🧪 Testing Error Handling")
    print("=" * 40)

    # Test connection failures
    print("\n1️⃣ Testing connection failure:")
    try:
        client = MCPClient("ws://localhost:9999")  # Non-existent server
        await client.connect()
    except Exception as e:
        print(f"   ✅ Caught expected error: {type(e).__name__}: {e}")

    # Test tool not found
    print("\n2️⃣ Testing tool not found:")
    server = MCPServer()
    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3002))
    await asyncio.sleep(0.5)

    try:
        async with MCPClient("ws://localhost:3002") as client:
            try:
                await client.call_tool("nonexistent_tool", {})
            except Exception as e:
                print(f"   ✅ Caught expected error: {type(e).__name__}: {e}")
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    print("\n✅ Error handling tests complete!")


async def main():
    """Run all advanced MCP examples."""
    try:
        # Check for required dependencies
        try:
            import websockets
        except ImportError:
            print("❌ This example requires websockets")
            print("   Install with: pip install websockets")
            return

        # Run demonstrations
        await demonstrate_mcp_integration()
        await test_error_handling()

        print("\n🎉 All examples completed successfully!")

    except KeyboardInterrupt:
        print("\n👋 Examples interrupted")
    except Exception as e:
        print(f"\n❌ Example error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
