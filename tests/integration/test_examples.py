"""Integration tests for AgentiCraft examples.

These tests ensure that all examples run correctly end-to-end.
"""

import asyncio
import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestExamples:
    """Test all example scripts work correctly."""
    
    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM responses for consistent testing."""
        return {
            "hello": "Hello! I'm AgentiCraft Agent. How can I help you today?",
            "chatbot": "I understand you're asking about testing. Here's my response.",
            "research": "Based on my research, here are the findings...",
            "tool": "I'll help you with that calculation: 2 + 2 = 4"
        }
    
    def test_01_hello_world(self, mock_llm_response):
        """Test the hello world example runs correctly."""
        # The hello world example doesn't actually call the LLM
        # so we don't need to mock anything
        
        # Import and run the example
        import importlib.util
        spec = importlib.util.spec_from_file_location("hello_world", "examples/01_hello_world.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        main = module.main
        
        # Should run without errors
        main()
    
    @pytest.mark.skip(reason="Example uses ChatAgent which doesn't exist yet")
    @pytest.mark.asyncio
    async def test_02_simple_chatbot(self, mock_llm_response, capsys):
        """Test the simple chatbot example."""
        # This example uses ChatAgent which is not yet implemented
        pass
    
    @pytest.mark.skip(reason="Provider mocking needs refactoring")
    @pytest.mark.asyncio
    async def test_02_tools(self, mock_llm_response):
        """Test the tools example."""
        pass
    
    def test_03_configuration(self):
        """Test the configuration example."""
        # Set required environment variables
        os.environ['AGENTICRAFT_LLM_PROVIDER'] = 'openai'
        os.environ['AGENTICRAFT_API_KEY'] = 'test-key'
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("configuration", "examples/03_configuration.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            main = module.main
            
            # Should demonstrate configuration
            main()
        finally:
            # Clean up
            os.environ.pop('AGENTICRAFT_LLM_PROVIDER', None)
            os.environ.pop('AGENTICRAFT_API_KEY', None)
    
    @pytest.mark.skip(reason="Provider mocking needs refactoring")
    @pytest.mark.asyncio
    async def test_04_workflow_research(self, mock_llm_response):
        """Test the research workflow example."""
        pass
    
    @pytest.mark.skip(reason="Provider mocking needs refactoring")
    @pytest.mark.asyncio
    async def test_05_tools_showcase(self, mock_llm_response):
        """Test the tools showcase example."""
        pass


class TestMCPExamples:
    """Test MCP protocol examples."""
    
    @pytest.mark.asyncio
    async def test_mcp_basic_example(self):
        """Test basic MCP example."""
        # Mock MCP server
        with patch('agenticraft.protocols.mcp.client.MCPClient.connect') as mock_connect:
            mock_connect.return_value = AsyncMock()
            
            # Check if example exists
            mcp_example = Path("examples/mcp/basic_mcp.py")
            if mcp_example.exists():
                # Import and test
                spec = importlib.util.spec_from_file_location("basic_mcp", mcp_example)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'main'):
                    await module.main()


class TestPluginExamples:
    """Test plugin examples."""
    
    def test_plugin_basic_example(self):
        """Test basic plugin example."""
        # Check if example exists
        plugin_example = Path("examples/plugins/custom_plugin.py")
        if plugin_example.exists():
            # Import and test
            spec = importlib.util.spec_from_file_location("custom_plugin", plugin_example)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Verify plugin structure
            assert hasattr(module, 'CustomPlugin')


class TestExampleUtils:
    """Test utility functions for examples."""
    
    def test_all_examples_have_main(self):
        """Ensure all example files have a main function."""
        examples_dir = Path("examples").resolve()
        
        for py_file in examples_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            with open(py_file, 'r') as f:
                content = f.read()
                
            # Check for main function
            assert "def main" in content or "async def main" in content, \
                f"{py_file.name} should have a main function"
            
            # Check for docstring
            assert '"""' in content or "'''" in content, \
                f"{py_file.name} should have a docstring"
    
    def test_examples_are_executable(self):
        """Check that examples have proper shebang and are executable."""
        examples_dir = Path("examples").resolve()
        
        for py_file in examples_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            with open(py_file, 'r') as f:
                first_line = f.readline().strip()
                
            # Check for shebang
            assert first_line.startswith("#!"), \
                f"{py_file.name} should start with shebang (#!/usr/bin/env python3)"


# importlib.util already imported at the top


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
