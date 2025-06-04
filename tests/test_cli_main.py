"""Comprehensive tests for CLI main module."""

import os
import platform
from unittest.mock import Mock, patch
import pytest
import click
from click.testing import CliRunner

import sys
sys.path.insert(0, ".")
from agenticraft import __version__
from agenticraft.cli.main import cli, main


class TestCLIMain:
    """Test the main CLI interface."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_cli_basic(self, runner):
        """Test basic CLI invocation."""
        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert "AgentiCraft - The AI Agent Framework" in result.output
        assert "Build production-ready AI agents" in result.output
    
    def test_cli_help(self, runner):
        """Test CLI help output."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "AgentiCraft - The AI Agent Framework" in result.output
        assert "Options:" in result.output
        assert "Commands:" in result.output
        
        # Check that all commands are listed
        assert "new" in result.output
        assert "run" in result.output
        assert "templates" in result.output
        assert "plugin" in result.output
        assert "version" in result.output
        assert "info" in result.output
    
    def test_version_option(self, runner):
        """Test --version option."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert f"agenticraft, version {__version__}" in result.output
    
    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(cli, ['version'])
        assert result.exit_code == 0
        assert f"AgentiCraft {__version__}" in result.output
    
    def test_info_command(self, runner):
        """Test info command."""
        result = runner.invoke(cli, ['info'])
        assert result.exit_code == 0
        
        # Check version info
        assert f"AgentiCraft {__version__}" in result.output
        assert f"Python {platform.python_version()}" in result.output
        assert f"Platform: {platform.platform()}" in result.output
        assert "Installation:" in result.output
        
        # Check sections
        assert "Available Providers:" in result.output
        assert "Core Tools:" in result.output
        
        # Check core tools are listed
        assert "search" in result.output
        assert "calculator" in result.output
        assert "files" in result.output
        assert "http" in result.output
        assert "text" in result.output
    
    def test_info_command_with_providers(self, runner):
        """Test info command with providers available."""
        mock_providers = ["openai", "anthropic", "google"]
        
        with patch('agenticraft.providers.list_providers', return_value=mock_providers):
            result = runner.invoke(cli, ['info'])
            assert result.exit_code == 0
            
            for provider in mock_providers:
                assert provider in result.output
    
    def test_info_command_provider_error(self, runner):
        """Test info command when providers can't be loaded."""
        with patch('agenticraft.providers.list_providers', side_effect=Exception("Load error")):
            result = runner.invoke(cli, ['info'])
            assert result.exit_code == 0
            assert "Unable to load providers" in result.output
    
    def test_context_object(self, runner):
        """Test that context object is properly initialized."""
        @cli.command()
        @click.pass_context
        def test_cmd(ctx):
            """Test command to check context."""
            assert isinstance(ctx.obj, dict)
            click.echo("Context OK")
        
        result = runner.invoke(cli, ['test_cmd'])
        assert result.exit_code == 0
        assert "Context OK" in result.output
    
    def test_main_function(self):
        """Test main entry point."""
        with patch('agenticraft.cli.main.cli') as mock_cli:
            main()
            mock_cli.assert_called_once()
    
    def test_main_function_error_handling(self):
        """Test main function error handling."""
        with patch('agenticraft.cli.main.cli', side_effect=Exception("Test error")):
            with patch('click.echo') as mock_echo:
                with patch('sys.exit') as mock_exit:
                    main()
                    
                    # Check error was printed
                    mock_echo.assert_called_with("Error: Test error", err=True)
                    # Check exit was called with error code
                    mock_exit.assert_called_once_with(1)
    
    def test_command_groups_added(self, runner):
        """Test that all command groups are properly added."""
        # Get the CLI commands
        commands = cli.list_commands(None)
        
        # Check all expected commands are present
        expected_commands = ['info', 'new', 'plugin', 'run', 'templates', 'version']
        for cmd in expected_commands:
            assert cmd in commands
    
    def test_invalid_command(self, runner):
        """Test running an invalid command."""
        result = runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output
