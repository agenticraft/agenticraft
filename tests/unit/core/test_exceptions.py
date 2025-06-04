"""Unit tests for exceptions module.

This module tests all custom exceptions in AgentiCraft.
"""

import pytest

from agenticraft.core.exceptions import (
    AgenticraftError,
    AgentError,
    ToolError,
    ToolExecutionError,
    ProviderError,
    ConfigurationError,
    MemoryError,
    WorkflowError,
    PluginError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""
    
    def test_base_exception(self):
        """Test base AgenticraftError."""
        error = AgenticraftError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)
    
    def test_all_exceptions_inherit_from_base(self):
        """Test all exceptions inherit from AgenticraftError."""
        exceptions = [
            AgentError("Agent error"),
            ToolError("Tool error"),
            ProviderError("Provider error"),
            ConfigurationError("Config error"),
            MemoryError("Memory error"),
            WorkflowError("Workflow error"),
            PluginError("Plugin error"),
            ValidationError("Validation error"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, AgenticraftError)
            assert isinstance(exc, Exception)


class TestAgentError:
    """Test AgentError exception."""
    
    def test_agent_error_creation(self):
        """Test creating AgentError."""
        error = AgentError("Agent failed to initialize")
        assert str(error) == "Agent failed to initialize"
    
    def test_agent_error_with_context(self):
        """Test AgentError with additional context."""
        try:
            raise AgentError("Agent execution failed", agent_id="agent-123")
        except AgentError as e:
            assert "Agent execution failed" in str(e)


class TestToolError:
    """Test tool-related exceptions."""
    
    def test_tool_error(self):
        """Test basic ToolError."""
        error = ToolError("Tool not found")
        assert str(error) == "Tool not found"
        assert isinstance(error, AgenticraftError)
    
    def test_tool_execution_error(self):
        """Test ToolExecutionError."""
        error = ToolExecutionError("Calculator tool failed", tool_name="calculator")
        assert "Calculator tool failed" in str(error)
        assert isinstance(error, ToolError)
    
    def test_tool_execution_error_with_details(self):
        """Test ToolExecutionError with detailed information."""
        error = ToolExecutionError(
            "Division by zero",
            tool_name="calculator",
            arguments={"a": 10, "b": 0}
        )
        assert "Division by zero" in str(error)


class TestProviderError:
    """Test ProviderError exception."""
    
    def test_provider_error(self):
        """Test ProviderError creation."""
        error = ProviderError("API key invalid")
        assert str(error) == "API key invalid"
    
    def test_provider_error_with_provider_name(self):
        """Test ProviderError with provider details."""
        error = ProviderError("Rate limit exceeded", provider="openai")
        assert "Rate limit exceeded" in str(error)


class TestConfigurationError:
    """Test ConfigurationError exception."""
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Missing required setting: API_KEY")
        assert "Missing required setting: API_KEY" in str(error)
    
    def test_configuration_error_with_field(self):
        """Test ConfigurationError with field information."""
        error = ConfigurationError(
            "Invalid value for temperature",
            field="temperature",
            value=3.0
        )
        assert "Invalid value for temperature" in str(error)


class TestMemoryError:
    """Test MemoryError exception."""
    
    def test_memory_error(self):
        """Test MemoryError creation."""
        error = MemoryError("Memory store not initialized")
        assert str(error) == "Memory store not initialized"
    
    def test_memory_error_with_store_type(self):
        """Test MemoryError with store details."""
        error = MemoryError(
            "Failed to connect to vector store",
            store_type="chromadb"
        )
        assert "Failed to connect to vector store" in str(error)


class TestWorkflowError:
    """Test WorkflowError exception."""
    
    def test_workflow_error(self):
        """Test WorkflowError."""
        error = WorkflowError("Circular dependency detected")
        assert str(error) == "Circular dependency detected"
    
    def test_workflow_error_with_step_info(self):
        """Test WorkflowError with step information."""
        error = WorkflowError(
            "Step timeout",
            workflow="data_pipeline",
            step="process_data"
        )
        assert "Step timeout" in str(error)


class TestPluginError:
    """Test PluginError exception."""
    
    def test_plugin_error(self):
        """Test PluginError."""
        error = PluginError("Plugin failed to load")
        assert str(error) == "Plugin failed to load"
    
    def test_plugin_error_with_plugin_name(self):
        """Test PluginError with plugin details."""
        error = PluginError(
            "Incompatible plugin version",
            plugin_name="weather_plugin",
            required_version="2.0",
            found_version="1.5"
        )
        assert "Incompatible plugin version" in str(error)


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input format")
        assert str(error) == "Invalid input format"
    
    def test_validation_error_with_details(self):
        """Test ValidationError with validation details."""
        error = ValidationError(
            "Schema validation failed",
            field="temperature",
            constraint="must be between 0 and 2",
            value=3.5
        )
        assert "Schema validation failed" in str(error)


class TestExceptionChaining:
    """Test exception chaining and context."""
    
    def test_exception_chaining(self):
        """Test chaining exceptions with cause."""
        try:
            try:
                # Simulate low-level error
                raise ValueError("Invalid JSON")
            except ValueError as e:
                # Wrap in domain exception
                raise ToolExecutionError(
                    "Failed to parse tool response",
                    tool_name="json_parser"
                ) from e
        except ToolExecutionError as e:
            assert "Failed to parse tool response" in str(e)
            assert e.__cause__ is not None
            assert "Invalid JSON" in str(e.__cause__)
    
    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        original_error = None
        wrapper_error = None
        
        try:
            try:
                1 / 0
            except ZeroDivisionError as e:
                original_error = e
                raise ProviderError("Math operation failed") from e
        except ProviderError as e:
            wrapper_error = e
        
        assert wrapper_error is not None
        assert wrapper_error.__cause__ is original_error
        assert isinstance(wrapper_error.__cause__, ZeroDivisionError)


class TestExceptionUsagePatterns:
    """Test common exception usage patterns."""
    
    def test_reraise_with_context(self):
        """Test reraising exceptions with additional context."""
        def process_data(data):
            try:
                return data["key"]
            except KeyError as e:
                raise ValidationError(
                    f"Required field 'key' missing in data: {list(data.keys())}"
                ) from e
        
        with pytest.raises(ValidationError) as exc_info:
            process_data({"other": "value"})
        
        assert "Required field 'key' missing" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, KeyError)
    
    def test_exception_error_codes(self):
        """Test exceptions with error codes."""
        # Custom exception with error code
        class CodedError(AgenticraftError):
            def __init__(self, message: str, code: str = None):
                super().__init__(message)
                self.code = code
        
        error = CodedError("Operation failed", code="E001")
        assert error.code == "E001"
        assert str(error) == "Operation failed"
    
    def test_exception_serialization(self):
        """Test that exceptions can be serialized for logging."""
        error = ToolExecutionError(
            "Tool failed",
            tool_name="calculator",
            arguments={"a": 1, "b": 2}
        )
        
        # Should be able to convert to string
        error_str = str(error)
        assert "Tool failed" in error_str
        
        # Should be able to get representation
        error_repr = repr(error)
        assert "ToolExecutionError" in error_repr
