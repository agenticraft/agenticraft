"""
Core functionality for AgentiCraft.

This module provides the core abstractions and base classes
that are used throughout the AgentiCraft framework.
"""

# Import existing core components
from .agent import Agent
from .config import Config
from .memory import Memory
from .plugin import Plugin
from .provider import Provider
from .reasoning import ReasoningEngine
from .streaming import StreamingResponse
from .telemetry import Telemetry
from .tool import Tool, BaseTool, ToolDefinition, ToolParameter
from .workflow import Workflow, WorkflowConfig

# Import specific exceptions (no star imports)
from .exceptions import (
    AgenticraftError,
    AgentError,
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolValidationError,
    ProviderError,
    ProviderNotFoundError,
    ProviderAuthError,
    ProviderRateLimitError,
    MemoryError,
    MemoryStorageError,
    WorkflowError,
    StepExecutionError,
    ConfigurationError,
    ValidationError,
    PluginError,
    CoreError,
    TransportError,
    ConnectionError,
    TimeoutError,
    AuthError,
    AuthenticationError,
    AuthorizationError,
    RegistryError,
    ServiceNotFoundError,
    ServiceAlreadyExistsError,
    PatternError,
    SerializationError,
)

# Import specific types (no star imports)
from .types import (
    ToolCall,
    ToolResult,
    MessageRole,
    Message,
    CompletionResponse,
    ToolParameter as ToolParameterType,  # Avoid name conflict
    ToolDefinition as ToolDefinitionType,  # Avoid name conflict
)

# Import new core abstractions
from . import transport
from . import auth
from . import registry
from . import patterns
from . import serialization

__all__ = [
    # Existing components
    "Agent",
    "Config",
    "Memory",
    "Plugin", 
    "Provider",
    "ReasoningEngine",
    "StreamingResponse",
    "Telemetry",
    "Tool",
    "BaseTool",
    "ToolDefinition",
    "ToolParameter",
    "Workflow",
    "WorkflowConfig",
    
    # New abstractions
    "transport",
    "auth",
    "registry", 
    "patterns",
    "serialization",
    
    # Exceptions
    "AgenticraftError",
    "AgentError",
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolValidationError",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "MemoryError",
    "MemoryStorageError",
    "WorkflowError",
    "StepExecutionError",
    "ConfigurationError",
    "ValidationError",
    "PluginError",
    "CoreError",
    "TransportError",
    "ConnectionError",
    "TimeoutError",
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "RegistryError",
    "ServiceNotFoundError",
    "ServiceAlreadyExistsError",
    "PatternError",
    "SerializationError",
    
    # Types
    "ToolCall",
    "ToolResult",
    "MessageRole",
    "Message",
    "CompletionResponse",
]
