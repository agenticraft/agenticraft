"""Comprehensive tests for CLI run command."""

import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import pytest
from click.testing import CliRunner
import yaml

from agenticraft.cli.commands.run import (
    run, _run_python_agent, _run_yaml_agent, _run_interactive
)


class TestRunCommand:
    """Test the run command for executing agents."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_agent_py(self, tmp_path):
        """Create a temporary Python agent file."""
        agent_file = tmp_path / "test_agent.py"
        agent_file.write_text("""
from agenticraft import Agent

agent = Agent(name="TestAgent")
""")
        return agent_file
    
    @pytest.fixture
    def temp_agent_yaml(self, tmp_path):
        """Create a temporary YAML agent config."""
        config_file = tmp_path / "agent.yaml"
        config = {
            "agent": {
                "name": "YAMLAgent",
                "type": "simple",
                "provider": "openai",
                "tools": ["calculator"],
                "default_prompt": "Hello from YAML"
            }
        }
        config_file.write_text(yaml.dump(config))
        return config_file
    
    def test_run_unsupported_file(self, runner, tmp_path):
        """Test error with unsupported file type."""
        bad_file = tmp_path / "agent.txt"
        bad_file.write_text("not an agent")
        
        result = runner.invoke(run, [str(bad_file)])
        
        assert result.exit_code != 0
        assert "Error: Unsupported file type: .txt" in result.output
        assert "Supported types: .py, .yaml, .yml" in result.output
    
    def test_run_missing_file(self, runner):
        """Test error with missing file."""
        result = runner.invoke(run, ["nonexistent.py"])
        
        assert result.exit_code != 0
        assert "does not exist" in result.output or "Error" in result.output
    
    def test_run_python_agent_no_prompt(self, runner, temp_agent_py):
        """Test error when running Python agent without prompt in non-interactive mode."""
        # Mock the module loading but let the prompt validation run
        mock_agent = Mock()
        mock_module = MagicMock()
        mock_module.agent = mock_agent
        
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        
        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            with patch('importlib.util.module_from_spec', return_value=mock_module):
                # This should fail because no prompt is provided
                result = runner.invoke(run, [str(temp_agent_py)])
                
                assert result.exit_code != 0
                assert "Error: --prompt required for non-interactive mode" in result.output
    
    def test_run_python_agent_with_prompt(self, runner, temp_agent_py):
        """Test running Python agent with prompt."""
        mock_agent = Mock()
        mock_result = Mock(content="Test response")
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        with patch('importlib.util.spec_from_file_location') as mock_spec:
            # Mock the module loading
            mock_module = MagicMock()
            mock_module.agent = mock_agent
            
            mock_spec_obj = MagicMock()
            mock_spec_obj.loader = MagicMock()
            mock_spec.return_value = mock_spec_obj
            
            with patch('importlib.util.module_from_spec', return_value=mock_module):
                result = runner.invoke(run, [str(temp_agent_py), '--prompt', 'Hello'])
                
                assert result.exit_code == 0
                assert "Agent: Test response" in result.output
    
    def test_run_python_agent_interactive(self, runner, temp_agent_py):
        """Test running Python agent in interactive mode."""
        mock_agent = Mock()
        mock_agent.name = "TestAgent"  # Set the name attribute explicitly
        
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        
        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            with patch('importlib.util.module_from_spec') as mock_module:
                mock_module.return_value.agent = mock_agent
                
                with patch('agenticraft.cli.commands.run._run_interactive') as mock_interactive:
                    result = runner.invoke(run, [str(temp_agent_py), '--interactive'])
                    
                    assert result.exit_code == 0
                    mock_interactive.assert_called_once_with(mock_agent)
    
    def test_run_yaml_agent(self, runner, temp_agent_yaml):
        """Test running YAML-configured agent."""
        mock_agent = Mock()
        mock_result = Mock(content="YAML response")
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        with patch('agenticraft.Agent', return_value=mock_agent):
            with patch('agenticraft.providers.get_provider'):
                result = runner.invoke(run, [str(temp_agent_yaml)])
                
                assert result.exit_code == 0
                assert "Agent: " in result.output
    
    def test_run_yaml_agent_with_provider_override(self, runner, temp_agent_yaml):
        """Test running YAML agent with provider override."""
        mock_agent = Mock()
        mock_result = Mock(content="Response")
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        with patch('agenticraft.Agent', return_value=mock_agent):
            with patch('agenticraft.providers.get_provider') as mock_get_provider:
                result = runner.invoke(run, [str(temp_agent_yaml), '--provider', 'anthropic'])
                
                assert result.exit_code == 0
                # Should use the overridden provider
                mock_get_provider.assert_called_with('anthropic')
    
    def test_run_yaml_reasoning_agent(self, runner, tmp_path):
        """Test running a reasoning agent from YAML."""
        config_file = tmp_path / "reasoning.yaml"
        config = {
            "agent": {
                "name": "ReasoningBot",
                "type": "reasoning",
                "provider": "openai"
            }
        }
        config_file.write_text(yaml.dump(config))
        
        mock_agent = Mock()
        mock_result = Mock(content="Reasoned response", reasoning=Mock(synthesis="My reasoning"))
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        with patch('agenticraft.ReasoningAgent', return_value=mock_agent):
            with patch('agenticraft.providers.get_provider'):
                result = runner.invoke(run, [str(config_file), '--prompt', 'Think'])
                
                assert result.exit_code == 0
                assert "Reasoning: My reasoning" in result.output


class TestRunCommandHelpers:
    """Test helper functions for the run command."""
    
    def test_run_python_agent_load_error(self):
        """Test error handling when Python file can't be loaded."""
        file_path = Path("bad_agent.py")
        
        with patch('importlib.util.spec_from_file_location', return_value=None):
            with pytest.raises(click.Abort):
                with patch('click.echo') as mock_echo:
                    _run_python_agent(file_path, None, False, None, None)
                    mock_echo.assert_called_with(f"Error: Failed to load {file_path}", err=True)
    
    def test_run_python_agent_exec_error(self):
        """Test error handling when Python module execution fails."""
        file_path = Path("error_agent.py")
        
        mock_spec = MagicMock()
        mock_spec.loader.exec_module.side_effect = Exception("Syntax error")
        
        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            with patch('importlib.util.module_from_spec'):
                with pytest.raises(click.Abort):
                    with patch('click.echo') as mock_echo:
                        _run_python_agent(file_path, None, False, None, None)
                        mock_echo.assert_called_with("Error loading agent: Syntax error", err=True)
    
    def test_run_python_agent_no_agent_found(self):
        """Test error when no agent is found in Python file."""
        file_path = Path("no_agent.py")
        
        # Create a module with no agent-related attributes
        mock_module = Mock(spec=['__dict__'])
        mock_module.__dict__ = {}  # Empty module
        
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        
        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            with patch('importlib.util.module_from_spec', return_value=mock_module):
                with pytest.raises(click.Abort):
                    with patch('click.echo') as mock_echo:
                        _run_python_agent(file_path, None, False, None, None)
                        assert any("No agent found" in str(call) for call in mock_echo.call_args_list)
    
    def test_run_python_agent_factory_function(self):
        """Test loading agent from factory function."""
        file_path = Path("factory_agent.py")
        
        mock_agent = Mock()
        
        # Create a simple module class that only has create_agent
        class MockModule:
            create_agent = Mock(return_value=mock_agent)
        
        mock_module = MockModule()
        
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        
        # Clean up sys.modules after test
        original_agent_module = sys.modules.get('agent_module')
        
        try:
            with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
                with patch('importlib.util.module_from_spec', return_value=mock_module):
                    with patch('agenticraft.cli.commands.run._run_interactive') as mock_interactive:
                        _run_python_agent(file_path, None, True, None, None)
                        
                        # Should call the factory function
                        mock_module.create_agent.assert_called_once()
                        # Should run interactive mode with the created agent
                        mock_interactive.assert_called_once_with(mock_agent)
        finally:
            # Clean up sys.modules
            if original_agent_module is None and 'agent_module' in sys.modules:
                del sys.modules['agent_module']
            elif original_agent_module is not None:
                sys.modules['agent_module'] = original_agent_module
    
    def test_run_yaml_agent_with_tools(self):
        """Test loading YAML agent with tools."""
        file_path = Path("agent_with_tools.yaml")
        config = {
            "agent": {
                "name": "ToolAgent",
                "tools": ["calculator", "search"]
            }
        }
        
        mock_agent = Mock()
        mock_agent.add_tool = Mock()
        # Mock the async run method
        mock_result = Mock(content="Test result")
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(config))):
            with patch('agenticraft.Agent', return_value=mock_agent):
                with patch('agenticraft.providers.get_provider'):
                    with patch('agenticraft.tools.simple_calculate') as mock_calc:
                        with patch('agenticraft.tools.web_search') as mock_search:
                            _run_yaml_agent(file_path, "test", False, None)
                            
                            # Should add both tools
                            assert mock_agent.add_tool.call_count == 2
                            mock_agent.add_tool.assert_any_call(mock_calc)
                            mock_agent.add_tool.assert_any_call(mock_search)
    
    def test_run_interactive(self):
        """Test interactive mode."""
        mock_agent = Mock()
        mock_agent.name = "TestBot"  # Set the name attribute explicitly
        mock_result = Mock(content="Interactive response")
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        # Simulate user input: one message then quit
        with patch('click.prompt', side_effect=["Hello bot", "quit"]):
            with patch('click.echo') as mock_echo:
                with patch('click.confirm', return_value=False):  # Mock confirm to avoid stdin issues
                    _run_interactive(mock_agent)
                    
                    # Check output
                    echo_args = [call.args[0] if call.args else "" for call in mock_echo.call_args_list]
                    
                    # Check all expected outputs
                    assert any("TestBot (Interactive Mode)" in arg for arg in echo_args)
                    assert any("TestBot: Interactive response" in arg for arg in echo_args)
                    assert any("Goodbye!" in arg for arg in echo_args)
    
    def test_run_interactive_with_reasoning(self):
        """Test interactive mode with reasoning display."""
        mock_agent = Mock()
        mock_agent.name = "ReasoningBot"  # Set the name attribute explicitly
        mock_reasoning = Mock(synthesis="This is my reasoning")
        mock_result = Mock(content="Reasoned answer", reasoning=mock_reasoning)
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        # Simulate user input and reasoning confirmation
        with patch('click.prompt', side_effect=["Explain something", "exit"]):
            with patch('click.confirm', return_value=True):  # Yes to show reasoning
                with patch('click.echo') as mock_echo:
                    _run_interactive(mock_agent)
                    
                    # Check reasoning was displayed
                    echo_args = [call.args[0] if call.args else "" for call in mock_echo.call_args_list]
                    assert any("This is my reasoning" in arg for arg in echo_args)
    
    def test_run_interactive_keyboard_interrupt(self):
        """Test handling keyboard interrupt in interactive mode."""
        mock_agent = Mock()
        mock_agent.name = "TestBot"  # Set the name attribute explicitly
        
        with patch('click.prompt', side_effect=KeyboardInterrupt()):
            with patch('click.echo') as mock_echo:
                _run_interactive(mock_agent)
                
                # Should handle gracefully
                echo_args = [call.args[0] if call.args else "" for call in mock_echo.call_args_list]
                assert any("Goodbye!" in arg for arg in echo_args)
    
    def test_run_interactive_error_handling(self):
        """Test error handling in interactive mode."""
        mock_agent = Mock()
        mock_agent.name = "ErrorBot"  # Set the name attribute explicitly
        mock_agent.run = AsyncMock(side_effect=Exception("Agent error"))
        
        # Simulate user input then quit after error
        with patch('click.prompt', side_effect=["Cause error", "quit"]):
            with patch('click.echo') as mock_echo:
                _run_interactive(mock_agent)
                
                # Should show error but continue
                echo_args = [str(call.args[0]) if call.args else "" for call in mock_echo.call_args_list]
                # Also check kwargs for err=True calls
                echo_err_args = [str(call.args[0]) if call.args and call.kwargs.get('err') else "" for call in mock_echo.call_args_list]
                assert any("Error: Agent error" in arg for arg in echo_args + echo_err_args)


# Helper to mock file opening
from unittest.mock import mock_open
import click