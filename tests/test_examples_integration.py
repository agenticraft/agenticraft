"""Integration tests for AgentiCraft examples."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

# Add examples to path
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))


class TestBasicExamples:
    """Test basic examples."""
    
    @pytest.mark.asyncio
    async def test_hello_world_example(self):
        """Test the hello world example."""
        with patch("agenticraft.core.provider.AsyncOpenAI") as mock_openai:
            # Mock OpenAI response
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            mock_response = AsyncMock()
            mock_response.choices = [
                AsyncMock(
                    message=AsyncMock(content="Hello! I'm doing great, thank you for asking!", tool_calls=None),
                    finish_reason="stop"
                )
            ]
            mock_response.usage = AsyncMock(prompt_tokens=10, completion_tokens=20)
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            # Import and run example
            from basic.hello_world import main
            
            # Capture output
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
            
            output = f.getvalue()
            assert "Assistant:" in output
            assert "doing great" in output.lower()
    
    @pytest.mark.asyncio
    async def test_simple_agent_example(self):
        """Test the simple agent example."""
        with patch("agenticraft.core.provider.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = AsyncMock()
            mock_response.choices = [
                AsyncMock(
                    message=AsyncMock(content="Paris is the capital of France.", tool_calls=None),
                    finish_reason="stop"
                )
            ]
            mock_response.usage = None
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            from basic.simple_agent import main
            
            # Run with patched input
            with patch("builtins.input", return_value="What is the capital of France?"):
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    main()
                
                output = f.getvalue()
                assert "Paris" in output
                assert "France" in output


class TestToolExamples:
    """Test tool examples."""
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self):
        """Test calculator tool example."""
        with patch("agenticraft.core.provider.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Mock tool call response
            mock_tool_call = AsyncMock()
            mock_tool_call.id = "call_123"
            mock_tool_call.function = AsyncMock(
                name="calculate",
                arguments='{"expression": "25 * 4 + 10"}'
            )
            
            # First response requests tool
            mock_response1 = AsyncMock()
            mock_response1.choices = [
                AsyncMock(
                    message=AsyncMock(
                        content="I'll calculate that for you.",
                        tool_calls=[mock_tool_call]
                    ),
                    finish_reason="tool_calls"
                )
            ]
            
            # Second response with result
            mock_response2 = AsyncMock()
            mock_response2.choices = [
                AsyncMock(
                    message=AsyncMock(
                        content="25 * 4 + 10 = 110",
                        tool_calls=None
                    ),
                    finish_reason="stop"
                )
            ]
            
            mock_client.chat.completions.create = AsyncMock(
                side_effect=[mock_response1, mock_response2]
            )
            
            from tools.calculator_tool import CalculatorAgent, main
            
            # Test the agent directly
            agent = CalculatorAgent()
            response = await agent.arun("What is 25 * 4 + 10?")
            
            assert "110" in response.content
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["name"] == "calculate"
    
    def test_custom_tools(self):
        """Test custom tools example."""
        from tools.custom_tools import get_weather, search_web, send_email
        
        # Test weather tool
        result = get_weather("London")
        assert "London" in result
        assert "°C" in result
        
        # Test search tool  
        results = search_web("Python programming")
        assert len(results) == 3
        assert all("Python" in r["title"] for r in results)
        
        # Test email tool
        result = send_email(
            to="test@example.com",
            subject="Test",
            body="Test email"
        )
        assert result["status"] == "sent"
        assert result["to"] == "test@example.com"


class TestWorkflowExamples:
    """Test workflow examples."""
    
    @pytest.mark.asyncio
    async def test_simple_workflow(self):
        """Test simple workflow example."""
        from workflows.simple_workflow import create_data_pipeline, main
        
        # Test workflow creation
        workflow = create_data_pipeline()
        assert workflow.name == "data_processing_pipeline"
        assert len(workflow.steps) == 4
        
        # Test workflow execution
        from agenticraft.core.workflow import WorkflowEngine
        
        engine = WorkflowEngine()
        
        # Register step implementations
        async def load_data(ctx):
            ctx.set("raw_data", [1, 2, 3, 4, 5])
            return {"count": 5}
        
        async def validate_data(ctx):
            data = ctx.get("raw_data", [])
            ctx.set("valid_data", [d for d in data if d > 0])
            return {"valid_count": len(data)}
        
        async def transform_data(ctx):
            data = ctx.get("valid_data", [])
            ctx.set("transformed_data", [d * 2 for d in data])
            return {"transformed": True}
        
        async def save_results(ctx):
            data = ctx.get("transformed_data", [])
            return {"saved": len(data), "sum": sum(data)}
        
        engine.register_step("load_data", load_data)
        engine.register_step("validate_data", validate_data)
        engine.register_step("transform_data", transform_data)
        engine.register_step("save_results", save_results)
        
        # Execute workflow
        context = await engine.execute(workflow)
        
        # Check results
        assert len(context.results) == 4
        final_result = context.get_result("save_results")
        assert final_result.output["saved"] == 5
        assert final_result.output["sum"] == 30  # (1+2+3+4+5) * 2


class TestReasoningExamples:
    """Test reasoning examples."""
    
    @pytest.mark.asyncio
    async def test_chain_of_thought(self):
        """Test chain of thought reasoning example."""
        with patch("agenticraft.core.provider.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = AsyncMock()
            mock_response.choices = [
                AsyncMock(
                    message=AsyncMock(
                        content="To solve 234 * 567, I need to multiply step by step...",
                        tool_calls=None
                    ),
                    finish_reason="stop"
                )
            ]
            mock_response.usage = None
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            from reasoning.chain_of_thought import main
            
            # Create agent
            import sys
sys.path.insert(0, ".")
from agenticraft import Agent
            from agenticraft.core.reasoning import ChainOfThought
            
            agent = Agent(
                name="ReasoningAgent",
                reasoning_pattern=ChainOfThought()
            )
            
            response = await agent.arun("What is 234 * 567?")
            
            # Check reasoning is included
            assert response.reasoning is not None
            assert "Chain of Thought:" in response.reasoning
            assert "234 * 567" in response.reasoning


class TestMemoryExamples:
    """Test memory examples."""
    
    @pytest.mark.asyncio
    async def test_conversation_memory(self):
        """Test conversation memory example."""
        from memory.conversation_memory import main
        import sys
sys.path.insert(0, ".")
from agenticraft import Agent
        from agenticraft.core.memory import ConversationMemory
        
        # Create agent with memory
        memory = ConversationMemory(max_turns=5)
        agent = Agent(
            name="MemoryBot",
            instructions="You are a helpful assistant with memory of our conversation.",
            memory=[memory]
        )
        
        # Mock the provider
        with patch.object(agent, '_provider') as mock_provider:
            mock_provider.complete = AsyncMock()
            
            # First response
            mock_provider.complete.return_value = AsyncMock(
                content="Hello! Nice to meet you. How can I help?",
                tool_calls=[],
                finish_reason="stop"
            )
            
            await agent.arun("Hello, my name is Alice")
            
            # Check memory stored the message
            messages = memory.get_messages()
            assert len(messages) == 2  # User + Assistant
            assert messages[0].content == "Hello, my name is Alice"
            
            # Second response should remember
            mock_provider.complete.return_value = AsyncMock(
                content="Hello again, Alice! How can I help you today?",
                tool_calls=[],
                finish_reason="stop"
            )
            
            await agent.arun("Do you remember my name?")
            
            # Check conversation history
            messages = memory.get_messages()
            assert len(messages) == 4
            assert any("Alice" in msg.content for msg in messages)


class TestPluginExamples:
    """Test plugin examples."""
    
    def test_logging_plugin(self):
        """Test logging plugin example."""
        from plugins.logging_plugin import LoggingPlugin
        from agenticraft.core.plugin import PluginRegistry
        
        # Reset registry
        PluginRegistry._instance = None
        
        # Create and register plugin
        plugin = LoggingPlugin()
        registry = PluginRegistry()
        registry.register(plugin)
        registry.initialize("logging", {"log_file": "test.log"})
        
        # Test metadata
        metadata = plugin.metadata()
        assert metadata.name == "logging"
        assert metadata.version == "1.0.0"
        
        # Test hooks
        from unittest.mock import Mock
        
        # Trigger hooks
        mock_agent = Mock(name="TestAgent")
        registry.trigger_hook("on_agent_created", agent=mock_agent)
        
        mock_tool = Mock(name="TestTool")
        registry.trigger_hook("on_tool_executed", tool=mock_tool, result="Success")
        
        # Plugin should have logged events
        assert hasattr(plugin, 'log_file')
    
    def test_simple_plugin(self):
        """Test simple plugin example."""
        from plugins.simple_plugin import MetricsPlugin
        
        plugin = MetricsPlugin()
        plugin.initialize({})
        
        # Test tracking
        from unittest.mock import Mock
        
        mock_agent = Mock()
        plugin.on_agent_created(mock_agent)
        plugin.on_agent_run(mock_agent, "Test prompt")
        plugin.on_agent_run(mock_agent, "Another prompt")
        
        # Check metrics
        metrics = plugin.get_metrics()
        assert metrics["agents_created"] == 1
        assert metrics["total_runs"] == 2
        assert metrics["total_prompt_length"] == len("Test prompt") + len("Another prompt")


class TestMCPExamples:
    """Test MCP examples."""
    
    @pytest.mark.asyncio
    async def test_mcp_client(self):
        """Test MCP client example."""
        from unittest.mock import AsyncMock, MagicMock
        
        with patch("websockets.connect") as mock_connect:
            # Mock WebSocket
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock()
            mock_ws.send = AsyncMock()
            mock_ws.close = AsyncMock()
            
            # Mock connection
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None
            
            # Mock server responses
            mock_ws.recv.side_effect = [
                '{"id": 1, "result": {"tools": [{"name": "test_tool", "description": "Test"}]}}',
                '{"id": 2, "result": {"result": "Tool executed"}}'
            ]
            
            from mcp.basic_client import main
            
            # Should complete without error
            # Note: In real test, we'd check specific behavior
    
    @pytest.mark.asyncio
    async def test_mcp_server(self):
        """Test MCP server example."""
        from mcp.basic_server import WeatherTool, create_server
        
        # Test weather tool
        tool = WeatherTool()
        result = await tool.execute(city="London")
        
        assert "weather" in result
        assert "London" in result["weather"]
        assert "temperature" in result
        
        # Test server creation
        server = create_server()
        assert server is not None
        assert hasattr(server, 'register_tool')


def test_all_examples_importable():
    """Test that all example modules can be imported."""
    example_dirs = ["basic", "tools", "workflows", "reasoning", "memory", "plugins", "mcp"]
    
    for dir_name in example_dirs:
        example_dir = Path(__file__).parent.parent / "examples" / dir_name
        if not example_dir.exists():
            continue
            
        for py_file in example_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
                
            module_name = f"{dir_name}.{py_file.stem}"
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
