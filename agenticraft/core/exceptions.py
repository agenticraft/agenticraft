"""Custom exceptions for AgentiCraft.

This module defines all custom exceptions used throughout the AgentiCraft
framework. Each exception is designed to provide clear, actionable error
messages to developers.

Example:
    Handling AgentiCraft exceptions::

        from agenticraft import Agent, AgentError

        try:
            agent = Agent()
            response = agent.run("Do something")
        except AgentError as e:
            print(f"Agent error: {e}")
        except ToolExecutionError as e:
            print(f"Tool failed: {e.tool_name} - {e}")
"""


class AgenticraftError(Exception):
    """Base exception for all AgentiCraft errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.message = message
        self.details = kwargs
        # Store any additional context as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


class AgentError(AgenticraftError):
    """Raised when an agent operation fails."""

    pass


class ToolError(AgenticraftError):
    """Base exception for tool-related errors."""

    pass


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found."""

    def __init__(self, tool_name: str):
        super().__init__(f"Tool '{tool_name}' not found in registry")
        self.tool_name = tool_name


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    def __init__(self, message: str, tool_name: str, **kwargs):
        super().__init__(message, tool_name=tool_name, **kwargs)
        self.tool_name = tool_name


class ToolValidationError(ToolError):
    """Raised when tool arguments are invalid."""

    def __init__(self, tool_name: str, error: str):
        super().__init__(f"Tool '{tool_name}' validation failed: {error}")
        self.tool_name = tool_name
        self.error = error


class ProviderError(AgenticraftError):
    """Base exception for LLM provider errors."""

    pass


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not found."""

    def __init__(self, model: str):
        super().__init__(
            f"No provider found for model '{model}'. "
            f"Supported providers: openai, anthropic, google, ollama"
        )
        self.model = model


class ProviderAuthError(ProviderError):
    """Raised when provider authentication fails."""

    def __init__(self, provider: str):
        super().__init__(
            f"Authentication failed for {provider}. " f"Please check your API key."
        )
        self.provider = provider


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""

    def __init__(self, provider: str, retry_after: int = None):
        message = f"Rate limit exceeded for {provider}"
        if retry_after:
            message += f". Retry after {retry_after} seconds."
        super().__init__(message)
        self.provider = provider
        self.retry_after = retry_after


class MemoryError(AgenticraftError):
    """Base exception for memory-related errors."""

    pass


class MemoryStorageError(MemoryError):
    """Raised when memory storage operations fail."""

    pass


class WorkflowError(AgenticraftError):
    """Base exception for workflow-related errors."""

    pass


class StepExecutionError(WorkflowError):
    """Raised when a workflow step fails."""

    def __init__(self, step_name: str, error: str):
        super().__init__(f"Step '{step_name}' failed: {error}")
        self.step_name = step_name
        self.error = error


class ConfigurationError(AgenticraftError):
    """Raised when configuration is invalid."""

    pass


class ValidationError(AgenticraftError):
    """Raised when validation fails."""

    pass


class PluginError(AgenticraftError):
    """Base exception for plugin-related errors."""

    pass
