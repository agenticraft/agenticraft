"""Comprehensive tests for exceptions module to achieve >95% coverage."""

import pytest

from agenticraft.core.exceptions import (
    AgenticraftError,
    AgentError,
    ConfigurationError,
    ProviderError,
    ProviderNotFoundError,
    ProviderAuthError,
    ProviderRateLimitError,
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolValidationError,
    MemoryError,
    MemoryStorageError,
    WorkflowError,
    StepExecutionError,
    ValidationError,
    PluginError
)


class TestAgenticraftError:
    """Test base AgenticraftError."""
    
    def test_base_error_creation(self):
        """Test creating base error."""
        error = AgenticraftError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)
    
    def test_base_error_with_details(self):
        """Test base error with additional details."""
        error = AgenticraftError("Error occurred", code=500, context="test")
        assert error.message == "Error occurred"
        assert error.details == {"code": 500, "context": "test"}
        assert error.details["code"] == 500
        assert error.details["context"] == "test"
        # Check that kwargs are also set as attributes
        assert error.code == 500
        assert error.context == "test"
    
    def test_base_error_empty_details(self):
        """Test base error with no details."""
        error = AgenticraftError("Simple error")
        assert error.details == {}


class TestAgentError:
    """Test AgentError."""
    
    def test_agent_error(self):
        """Test agent error creation."""
        error = AgentError("Agent failed")
        assert str(error) == "Agent failed"
        assert isinstance(error, AgenticraftError)
    
    def test_agent_error_with_details(self):
        """Test agent error with details."""
        error = AgentError("Agent initialization failed", agent_name="TestAgent")
        assert error.message == "Agent initialization failed"
        assert error.details["agent_name"] == "TestAgent"
        assert error.agent_name == "TestAgent"


class TestConfigurationError:
    """Test ConfigurationError."""
    
    def test_configuration_error(self):
        """Test configuration error creation."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, AgenticraftError)
    
    def test_configuration_error_with_field(self):
        """Test configuration error with field details."""
        error = ConfigurationError(
            "Invalid API key",
            field="api_key",
            value=None
        )
        assert error.message == "Invalid API key"
        assert error.details["field"] == "api_key"


class TestProviderErrors:
    """Test provider-related errors."""
    
    def test_provider_error(self):
        """Test provider error creation."""
        error = ProviderError("Provider not available")
        assert str(error) == "Provider not available"
        assert isinstance(error, AgenticraftError)
    
    def test_provider_not_found_error(self):
        """Test provider not found error."""
        error = ProviderNotFoundError("gpt-5")
        assert "No provider found for model 'gpt-5'" in str(error)
        assert "openai, anthropic, google, ollama" in str(error)
        assert error.model == "gpt-5"
    
    def test_provider_auth_error(self):
        """Test provider authentication error."""
        error = ProviderAuthError("openai")
        assert "Authentication failed for openai" in str(error)
        assert "check your API key" in str(error)
        assert error.provider == "openai"
    
    def test_provider_rate_limit_error(self):
        """Test provider rate limit error."""
        error = ProviderRateLimitError("anthropic", retry_after=60)
        assert "Rate limit exceeded for anthropic" in str(error)
        assert "Retry after 60 seconds" in str(error)
        assert error.provider == "anthropic"
        assert error.retry_after == 60
    
    def test_provider_rate_limit_no_retry(self):
        """Test provider rate limit error without retry_after."""
        error = ProviderRateLimitError("openai")
        assert "Rate limit exceeded for openai" in str(error)
        assert "Retry after" not in str(error)
        assert error.retry_after is None


class TestToolErrors:
    """Test tool-related errors."""
    
    def test_tool_error(self):
        """Test base tool error."""
        error = ToolError("Tool error occurred")
        assert str(error) == "Tool error occurred"
        assert isinstance(error, AgenticraftError)
    
    def test_tool_not_found_error(self):
        """Test tool not found error."""
        error = ToolNotFoundError("calculator")
        assert str(error) == "Tool 'calculator' not found in registry"
        assert isinstance(error, ToolError)
        assert error.tool_name == "calculator"
    
    def test_tool_execution_error(self):
        """Test tool execution error."""
        error = ToolExecutionError(
            message="Connection timeout",
            tool_name="web_search"
        )
        assert "Connection timeout" in str(error)
        assert isinstance(error, ToolError)
        assert error.tool_name == "web_search"
    
    def test_tool_validation_error(self):
        """Test tool validation error."""
        error = ToolValidationError(
            tool_name="calculator",
            error="Invalid expression"
        )
        assert "Tool 'calculator' validation failed: Invalid expression" in str(error)
        assert isinstance(error, ToolError)
        assert error.tool_name == "calculator"
        assert error.error == "Invalid expression"


class TestMemoryErrors:
    """Test memory-related errors."""
    
    def test_memory_error(self):
        """Test memory error creation."""
        error = MemoryError("Memory operation failed")
        assert str(error) == "Memory operation failed"
        assert isinstance(error, AgenticraftError)
    
    def test_memory_storage_error(self):
        """Test memory storage error."""
        error = MemoryStorageError("Failed to save memory")
        assert str(error) == "Failed to save memory"
        assert isinstance(error, MemoryError)
    
    def test_memory_error_with_details(self):
        """Test memory error with details."""
        error = MemoryError(
            "Failed to persist memory",
            memory_type="knowledge",
            operation="save",
            path="/tmp/memory.json"
        )
        assert error.details["memory_type"] == "knowledge"
        assert error.details["operation"] == "save"


class TestWorkflowErrors:
    """Test workflow-related errors."""
    
    def test_workflow_error(self):
        """Test workflow error creation."""
        error = WorkflowError("Workflow execution failed")
        assert str(error) == "Workflow execution failed"
        assert isinstance(error, AgenticraftError)
    
    def test_step_execution_error(self):
        """Test step execution error."""
        error = StepExecutionError("data_transform", "Invalid input format")
        assert "Step 'data_transform' failed: Invalid input format" in str(error)
        assert isinstance(error, WorkflowError)
        assert error.step_name == "data_transform"
        assert error.error == "Invalid input format"
    
    def test_workflow_error_with_details(self):
        """Test workflow error with step information."""
        error = WorkflowError(
            "Step failed",
            workflow="data_pipeline",
            step="transform",
            step_number=3,
            total_steps=5
        )
        assert error.details["step"] == "transform"
        assert error.details["step_number"] == 3


class TestValidationError:
    """Test ValidationError."""
    
    def test_validation_error(self):
        """Test validation error creation."""
        error = ValidationError("Invalid input data")
        assert str(error) == "Invalid input data"
        assert isinstance(error, AgenticraftError)
    
    def test_validation_error_with_details(self):
        """Test validation error with field-specific errors."""
        error = ValidationError(
            "Validation failed",
            fields=["name", "email"],
            values={"name": "", "email": "invalid"}
        )
        assert error.details["fields"] == ["name", "email"]
        assert error.details["values"]["email"] == "invalid"


class TestExceptionInheritance:
    """Test exception inheritance relationships."""
    
    def test_all_inherit_from_base(self):
        """Test all exceptions inherit from AgenticraftError."""
        exceptions = [
            AgentError("test"),
            ConfigurationError("test"),
            ProviderError("test"),
            ProviderNotFoundError("test_model"),
            ProviderAuthError("test_provider"),
            ProviderRateLimitError("test_provider"),
            ToolError("test"),
            ToolNotFoundError("test_tool"),
            ToolExecutionError("error", tool_name="test_tool"),
            ToolValidationError("test_tool", "error"),
            MemoryError("test"),
            MemoryStorageError("test"),
            WorkflowError("test"),
            StepExecutionError("test_step", "error"),
            ValidationError("test"),
            PluginError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, AgenticraftError)
            assert isinstance(exc, Exception)
    
    def test_tool_error_hierarchy(self):
        """Test tool error inheritance."""
        not_found = ToolNotFoundError("tool")
        execution = ToolExecutionError("error", tool_name="tool")
        validation = ToolValidationError("tool", "error")
        
        assert isinstance(not_found, ToolError)
        assert isinstance(execution, ToolError)
        assert isinstance(validation, ToolError)
        assert isinstance(not_found, AgenticraftError)
        assert isinstance(execution, AgenticraftError)
        assert isinstance(validation, AgenticraftError)
    
    def test_provider_error_hierarchy(self):
        """Test provider error inheritance."""
        not_found = ProviderNotFoundError("model")
        auth = ProviderAuthError("provider")
        rate_limit = ProviderRateLimitError("provider")
        
        assert isinstance(not_found, ProviderError)
        assert isinstance(auth, ProviderError)
        assert isinstance(rate_limit, ProviderError)
        assert isinstance(not_found, AgenticraftError)
        assert isinstance(auth, AgenticraftError)
        assert isinstance(rate_limit, AgenticraftError)
    
    def test_memory_error_hierarchy(self):
        """Test memory error inheritance."""
        storage = MemoryStorageError("test")
        
        assert isinstance(storage, MemoryError)
        assert isinstance(storage, AgenticraftError)
    
    def test_workflow_error_hierarchy(self):
        """Test workflow error inheritance."""
        step = StepExecutionError("step", "error")
        
        assert isinstance(step, WorkflowError)
        assert isinstance(step, AgenticraftError)


class TestExceptionUsage:
    """Test practical usage of exceptions."""
    
    def test_catching_specific_errors(self):
        """Test catching specific error types."""
        def may_fail():
            raise ToolNotFoundError("calculator")
        
        with pytest.raises(ToolNotFoundError) as exc_info:
            may_fail()
        
        assert exc_info.value.tool_name == "calculator"
        assert "calculator" in str(exc_info.value)
    
    def test_catching_parent_errors(self):
        """Test catching parent error types."""
        def may_fail():
            raise ToolExecutionError("Network error", tool_name="search")
        
        # Should be caught by ToolError
        with pytest.raises(ToolError):
            may_fail()
        
        # Should also be caught by AgenticraftError
        with pytest.raises(AgenticraftError):
            may_fail()
    
    def test_error_chaining(self):
        """Test error chaining with cause."""
        original = ValueError("Invalid input")
        
        try:
            raise original
        except ValueError as e:
            raised_error = ToolExecutionError(str(e), tool_name="calculator")
            
        assert "Invalid input" in str(raised_error)
    
    def test_provider_auth_flow(self):
        """Test provider authentication error flow."""
        def authenticate(api_key):
            if not api_key:
                raise ProviderAuthError("openai")
            return True
        
        with pytest.raises(ProviderAuthError) as exc_info:
            authenticate(None)
        
        error = exc_info.value
        assert error.provider == "openai"
        assert "API key" in str(error)
    
    def test_workflow_step_failure(self):
        """Test workflow step execution failure."""
        def execute_step(name, data):
            if not data:
                raise StepExecutionError(name, "No input data provided")
            return data
        
        with pytest.raises(StepExecutionError) as exc_info:
            execute_step("transform", None)
        
        error = exc_info.value
        assert error.step_name == "transform"
        assert error.error == "No input data provided"
        assert "transform" in str(error)


class TestPluginError:
    """Test PluginError."""
    
    def test_plugin_error(self):
        """Test plugin error creation."""
        error = PluginError("Plugin failed to load")
        assert str(error) == "Plugin failed to load"
        assert isinstance(error, AgenticraftError)
    
    def test_plugin_error_with_details(self):
        """Test plugin error with details."""
        error = PluginError(
            "Plugin version mismatch",
            plugin_name="weather",
            required_version="2.0",
            found_version="1.5"
        )
        assert error.details["plugin_name"] == "weather"
        assert error.details["required_version"] == "2.0"
        assert error.plugin_name == "weather"
        assert error.required_version == "2.0"
        assert error.found_version == "1.5"
