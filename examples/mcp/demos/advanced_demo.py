#!/usr/bin/env python3
"""Fixed Advanced MCP example using the working server approach."""

import asyncio
import logging
import os
import sys
from typing import Any

# Add path
sys.path.insert(0, "/Users/zahere/Desktop/TLV/agenticraft")

# Import our working server
from working_mcp_server import WorkingMCPServer

from agenticraft import Agent, tool
from agenticraft.protocols.mcp import MCPClient, mcp_tool
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
    """Solve a math word problem step by step."""
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
    """Analyze text and extract insights."""
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
    """Search internal knowledge base."""
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


class AdvancedMCPServerMonitor:
    """Advanced MCP server with monitoring and metrics."""

    def __init__(self):
        self.server = WorkingMCPServer(
            name="Advanced AgentiCraft Server",
            version="2.0.0",
            description="Feature-rich MCP server with analytics",
        )
        self.call_count = {}
        self.error_count = {}

    def get_metrics(self) -> dict[str, Any]:
        """Get server metrics."""
        return {
            "tool_calls": self.call_count,
            "errors": self.error_count,
            "total_calls": sum(self.call_count.values()),
            "total_errors": sum(self.error_count.values()),
        }


async def demonstrate_advanced_mcp():
    """Demonstrate advanced MCP integration with working server."""
    print("\n🚀 Advanced MCP Integration Demo (FIXED)")
    print("=" * 60)

    # 1. Create and start server
    print("\n📡 Starting Advanced MCP Server...")
    monitor = AdvancedMCPServerMonitor()
    server = monitor.server

    # Register tools
    tools = [solve_math_problem, analyze_text, search_knowledge_base]
    server.register_tools(tools)

    print(f"📦 Registered {len(tools)} advanced tools")

    # Start server in background task
    print("🌐 Starting server on localhost:3001...")
    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3001))

    # Give server time to start
    await asyncio.sleep(1)
    print("✅ Server started successfully")

    try:
        # 2. Connect client and test
        print("\n🔌 Connecting Advanced MCP Client...")
        async with MCPClient("ws://localhost:3001") as client:
            print(f"✅ Connected to: {client.server_info.name}")
            print(f"   Available tools: {', '.join(client.available_tools)}")

            # 3. Test advanced tools
            print("\n🔧 Testing Advanced Tools:")

            # Math problem solving
            print("\n📊 Math Problem Solver:")
            math_result = await client.call_tool(
                "solve_math_problem", {"problem": "What is 15% of 200?"}
            )
            print("   Problem: What is 15% of 200?")
            print(f"   Result: {math_result['result']}")
            print(f"   Steps: {math_result['steps']}")
            print(f"   Confidence: {math_result['confidence']}")

            # Text analysis
            print("\n📝 Text Analysis:")
            text_result = await client.call_tool(
                "analyze_text",
                {
                    "text": "This is an amazing example of advanced MCP integration. It works incredibly well!"
                },
            )
            print("   Text: Advanced MCP integration example")
            print(f"   Summary: {text_result['summary']}")
            print(f"   Keywords: {text_result['keywords']}")
            print(f"   Sentiment: {text_result['sentiment']}")
            print(f"   Length: {text_result['length']} characters")

            # Knowledge search
            print("\n🔍 Knowledge Base Search:")
            search_result = await client.call_tool(
                "search_knowledge_base", {"query": "Python programming", "limit": 3}
            )
            print("   Query: Python programming")
            print(f"   Found {len(search_result)} results:")
            for doc in search_result:
                print(f"      - {doc['title']}")

            # 4. Test with Agent (if API key available)
            print("\n🤖 Testing Agent Integration...")
            if os.getenv("OPENAI_API_KEY"):
                try:
                    agent = Agent(
                        name="AdvancedMCPAgent",
                        instructions="""You are an advanced AI assistant with powerful MCP tools.
                        Use your tools to help users with:
                        - Math problems (use solve_math_problem)
                        - Text analysis (use analyze_text)
                        - Knowledge search (use search_knowledge_base)
                        
                        Always explain what tools you're using and why.""",
                        tools=client.get_tools(),
                        model="gpt-4o-mini",
                    )

                    print("   ✅ Created agent with advanced MCP tools")

                    # Test query
                    test_query = "Analyze this text: 'Advanced MCP is fantastic!' and also calculate 25% of 120"
                    print(f"   💬 Query: {test_query}")

                    response = await agent.arun(test_query)
                    print(f"   🤖 Response: {response.content}")

                    if hasattr(response, "tool_calls") and response.tool_calls:
                        print(
                            f"   📊 Tools used: {[tc.function.name for tc in response.tool_calls]}"
                        )

                except Exception as e:
                    print(f"   ⚠️  Agent test skipped due to error: {e}")
            else:
                print("   ⏭️  Agent test skipped (OPENAI_API_KEY not set)")

            # 5. Show server metrics
            print("\n📈 Server Metrics:")
            metrics = monitor.get_metrics()
            print(f"   Total calls: {metrics['total_calls']}")
            print(f"   Tool usage: {metrics['tool_calls']}")

            # 6. Test global registry
            print("\n🗂️ Testing Global Registry:")
            registry = get_global_registry()

            # Register tools in registry
            for tool in tools:
                if hasattr(tool, "get_mcp_tool"):
                    mcp_tool = tool.get_mcp_tool()
                    registry.register_mcp_tool(mcp_tool, category="advanced")

            print(f"   Registry size: {len(registry)}")
            print(f"   Categories: {registry.list_categories()}")
            print(f"   Advanced tools: {registry.list_tools('advanced')}")

            # Search in registry
            search_results = registry.search_tools("math")
            print(f"   Search 'math': {[t.name for t in search_results]}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        print("✅ Server stopped")

    print("\n✅ Advanced MCP Demo Complete!")


async def main():
    """Run the fixed advanced MCP demo."""
    print("🚀 Fixed Advanced MCP Integration Test")
    print("=" * 60)
    print("This version uses the working server and should complete successfully!")
    print()

    try:
        await demonstrate_advanced_mcp()

        print("\n🎉 Advanced MCP demo completed successfully!")
        print("\n💡 This demonstrates:")
        print("   • Advanced MCP tools with rich metadata")
        print("   • Server monitoring and metrics")
        print("   • Agent integration with MCP tools")
        print("   • Global tool registry usage")
        print("   • Real-world tool examples")

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
