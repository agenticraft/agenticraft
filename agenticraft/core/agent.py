"""Base Agent class for AgentiCraft.

This module provides the core Agent class that all agents in AgentiCraft
are built upon. The Agent class handles LLM interactions, memory management,
and reasoning patterns.

Example:
    Basic agent creation and usage::

        from agenticraft import Agent

        agent = Agent(
            name="Assistant",
            instructions="You are a helpful AI assistant."
        )

        response = agent.run("Hello, how are you?")
        print(response.content)
        print(response.reasoning)

    For tool-like functionality, use WorkflowAgent with handlers::

        from agenticraft.agents import WorkflowAgent

        workflow_agent = WorkflowAgent(
            name="DataProcessor",
            instructions="Process data through workflows."
        )

        def process_handler(agent, step, context):
            data = context.get("data", [])
            result = len(data)
            context["result"] = result
            return f"Processed {result} items"

        workflow_agent.register_handler("process", process_handler)
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import settings
from .exceptions import AgentError, ProviderError
from .memory import BaseMemory, MemoryStore
from .provider import BaseProvider, ProviderFactory
from .reasoning import ReasoningTrace, SimpleReasoning
from .streaming import StreamChunk, StreamInterruptedError
from .tool import BaseTool, ToolRegistry
from .types import Message, MessageRole, ToolCall, ToolResult

# Security imports - optional to avoid breaking existing code
try:
    from ..security import SandboxManager, SecurityContext, SandboxType, SecureResult
    from ..security.exceptions import SecurityException
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    SecurityContext = None
    SandboxType = None
    SecureResult = None

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Response from an agent execution.

    Attributes:
        content: The main response content
        reasoning: The reasoning trace showing how the agent thought
        tool_calls: List of tools called during execution
        metadata: Additional metadata about the response
        agent_id: ID of the agent that generated this response
        created_at: Timestamp when response was created
    """

    content: str
    reasoning: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    agent_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class AgentConfig(BaseModel):
    """Configuration for an Agent.

    Attributes:
        name: The agent's name
        instructions: System instructions defining the agent's behavior
        provider: Explicit provider name (optional, auto-detected if not specified)
        model: LLM model to use (e.g., "gpt-4", "claude-3-opus")
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        tools: List of tools available to the agent
        memory: Memory configuration
        reasoning_pattern: Reasoning pattern to use
        api_key: API key for the LLM provider
        base_url: Optional base URL for the LLM provider
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        metadata: Additional metadata
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(default="Agent")
    instructions: str = Field(
        default="You are a helpful AI assistant.",
        description="System instructions defining agent behavior",
    )
    provider: str | None = Field(
        default=None,
        description="Explicit provider name (e.g., 'openai', 'anthropic', 'ollama'). If not specified, auto-detected from model name.",
    )
    model: str = Field(
        default_factory=lambda: settings.default_model, description="LLM model to use"
    )
    temperature: float = Field(
        default_factory=lambda: settings.default_temperature, ge=0.0, le=2.0
    )
    max_tokens: int | None = Field(
        default_factory=lambda: settings.default_max_tokens, gt=0
    )
    tools: list[Any] = Field(default_factory=list)
    memory: list[Any] = Field(default_factory=list)
    reasoning_pattern: Any | None = None
    api_key: str | None = Field(default=None, exclude=True)
    base_url: str | None = None
    timeout: int = Field(default_factory=lambda: settings.default_timeout, gt=0)
    max_retries: int = Field(default_factory=lambda: settings.default_max_retries, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Security settings
    sandbox_enabled: bool = Field(default=False, description="Enable sandboxed execution")
    sandbox_type: str | None = Field(default=None, description="Type of sandbox to use")
    memory_limit: int = Field(default=512, description="Memory limit in MB for sandboxed execution")
    cpu_limit: float = Field(default=50.0, description="CPU limit percentage for sandboxed execution")

    @field_validator("provider")
    def validate_provider(cls, provider: str | None) -> str | None:
        """Validate provider name if specified."""
        if provider is not None:
            valid_providers = ["openai", "anthropic", "ollama", "google"]
            if provider not in valid_providers:
                raise ValueError(
                    f"Invalid provider: {provider}. "
                    f"Valid providers are: {', '.join(valid_providers)}"
                )
        return provider

    @field_validator("tools")
    def validate_tools(cls, tools: list[Any]) -> list[Any]:
        """Validate tools are proper type."""
        from .tool import BaseTool

        for tool in tools:
            if not (isinstance(tool, BaseTool) or callable(tool)):
                raise ValueError(f"Invalid tool type: {type(tool)}")
        return tools

    @field_validator("memory")
    def validate_memory(cls, memory: list[Any]) -> list[Any]:
        """Validate memory instances."""

        for mem in memory:
            if not isinstance(mem, BaseMemory):
                raise ValueError(f"Invalid memory type: {type(mem)}")
        return memory


class Agent:
    """Base Agent class for AgentiCraft.

    The Agent class is the core abstraction in AgentiCraft. It combines
    an LLM provider, memory, and reasoning patterns to create
    an intelligent agent capable of complex tasks.

    For tool-like functionality, use WorkflowAgent with handlers instead
    of the deprecated add_tool method.

    Args:
        name: The agent's name
        instructions: System instructions for the agent
        model: LLM model to use
        **kwargs: Additional configuration options

    Example:
        Creating a simple agent::

            agent = Agent(
                name="MathTutor",
                instructions="You are a patient math tutor.",
                model="gpt-4"
            )

        For complex operations with tools, use WorkflowAgent::

            from agenticraft.agents import WorkflowAgent

            workflow_agent = WorkflowAgent(
                name="Calculator",
                instructions="You perform calculations."
            )

            # Register handlers instead of tools
            workflow_agent.register_handler("calc", calc_handler)
    """

    def __init__(
        self,
        name: str = "Agent",
        instructions: str = "You are a helpful AI assistant.",
        model: str = "gpt-4",
        **kwargs: Any,
    ):
        """Initialize an Agent."""
        # Create config
        self.config = AgentConfig(
            name=name, instructions=instructions, model=model, **kwargs
        )

        # Generate unique ID
        self.id = uuid4()

        # Initialize components
        self._provider: BaseProvider | None = None
        self._tool_registry = ToolRegistry()
        self._memory_store = MemoryStore()
        self._reasoning = self.config.reasoning_pattern or SimpleReasoning()

        # Register tools
        for tool in self.config.tools:
            self._tool_registry.register(tool)

        # Initialize memory
        for memory in self.config.memory:
            self._memory_store.add_memory(memory)

        # Message history
        self._messages: list[Message] = []
        
        # Security components
        self._sandbox_manager: SandboxManager | None = None
        self._security_context: SecurityContext | None = None
        
        # Initialize security if enabled
        if self.config.sandbox_enabled and SECURITY_AVAILABLE:
            self._init_security()

        logger.info(f"Initialized agent '{self.name}' with ID {self.id}")
    
    def _init_security(self) -> None:
        """Initialize security components."""
        from ..security import SandboxManager, SecurityContext, SandboxType
        
        # Initialize sandbox manager
        self._sandbox_manager = SandboxManager()
        
        # Create default security context
        self._security_context = SecurityContext(
            user_id="agent",
            permissions=["execute"],
            resource_limits={
                "memory_mb": self.config.memory_limit,
                "cpu_percent": self.config.cpu_limit,
                "timeout_seconds": self.config.timeout,
                "network_access": False,
                "filesystem_access": False
            }
        )

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self.config.name

    @property
    def provider(self) -> BaseProvider:
        """Get or create the LLM provider."""
        if self._provider is None:
            # Use explicit provider if specified in config
            if self.config.provider:
                self._provider = ProviderFactory.create(
                    model=self.config.model,
                    provider=self.config.provider,  # Pass explicit provider
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                )
            else:
                # Auto-detect from model name
                self._provider = ProviderFactory.create(
                    model=self.config.model,
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                )
        return self._provider

    def run(
        self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any
    ) -> AgentResponse:
        """Run the agent synchronously.

        Args:
            prompt: The user's prompt/question
            context: Optional context to provide to the agent
            **kwargs: Additional arguments passed to the LLM

        Returns:
            AgentResponse containing the result

        Example:
            Basic usage::

                response = agent.run("What's the weather?")
                print(response.content)

            With context::

                response = agent.run(
                    "Summarize this",
                    context={"document": "Long text..."}
                )
        """
        return asyncio.run(self.arun(prompt, context, **kwargs))

    async def arun(
        self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any
    ) -> AgentResponse:
        """Run the agent asynchronously.

        Args:
            prompt: The user's prompt/question
            context: Optional context to provide to the agent
            **kwargs: Additional arguments passed to the LLM

        Returns:
            AgentResponse containing the result
        """
        try:
            # Start reasoning
            reasoning_trace = self._reasoning.start_trace(prompt)

            # Add user message
            user_message = Message(
                role=MessageRole.USER,
                content=prompt,
                metadata={"context": context} if context else {},
            )
            self._messages.append(user_message)

            # Get memory context
            memory_context = await self._memory_store.get_context(
                query=prompt, max_items=10
            )

            # Build conversation
            messages = self._build_messages(memory_context, context)

            # Get available tools
            tools_schema = self._tool_registry.get_tools_schema()

            # Call LLM
            reasoning_trace.add_step(
                "calling_llm",
                {"model": self.config.model, "temperature": self.config.temperature},
            )

            response = await self.provider.complete(
                messages=messages,
                tools=tools_schema if tools_schema else None,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs,
            )

            # Process tool calls if any
            tool_results = []
            executed_tool_calls = []  # Track the tool calls we executed
            if response.tool_calls:
                executed_tool_calls = response.tool_calls  # Save for later
                tool_results = await self._execute_tools(
                    response.tool_calls, reasoning_trace
                )

                # If tools were called, we need another LLM call with results
                if tool_results:
                    tool_message = Message(
                        role=MessageRole.ASSISTANT,
                        content=response.content,
                        tool_calls=[
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": json.dumps(tc.arguments)
                                    if isinstance(tc.arguments, dict)
                                    else tc.arguments
                                }
                            }
                            for tc in response.tool_calls
                        ],
                    )
                    self._messages.append(tool_message)

                    # Add assistant message with tool calls to messages
                    messages.append(tool_message.to_dict())

                    # Add tool results
                    for result in tool_results:
                        result_message = Message(
                            role=MessageRole.TOOL,
                            content=json.dumps(result.result),
                            metadata={"tool_call_id": result.tool_call_id},
                        )
                        messages.append(result_message.to_dict())

                    # Get final response
                    response = await self.provider.complete(
                        messages=messages,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        **kwargs,
                    )

            # Add assistant message
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response.content,
                metadata=response.metadata,
            )
            self._messages.append(assistant_message)

            # Store in memory
            await self._memory_store.store(
                user_message=user_message, assistant_message=assistant_message
            )

            # Complete reasoning
            reasoning_trace.complete({"response": response.content})

            # Build response
            return AgentResponse(
                content=response.content,
                reasoning=self._reasoning.format_trace(reasoning_trace),
                tool_calls=[
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments
                    }
                    for tc in executed_tool_calls
                ],  # Use the saved tool calls
                metadata={
                    "model": self.config.model,
                    "reasoning_pattern": self._reasoning.__class__.__name__,
                    **response.metadata,
                },
                agent_id=self.id,
            )

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise AgentError(f"Agent execution failed: {e}") from e

    async def stream(
        self, prompt: str, context: dict[str, Any] | None = None, **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        """Stream the agent's response token by token.

        This method provides real-time streaming of responses, allowing for
        better user experience with long responses.

        Args:
            prompt: The user's prompt/question
            context: Optional context to provide to the agent
            **kwargs: Additional arguments passed to the LLM

        Yields:
            StreamChunk: Individual chunks of the response

        Raises:
            StreamInterruptedError: If the stream is interrupted
            ProviderError: If the provider doesn't support streaming

        Example:
            Basic streaming::

                async for chunk in agent.stream("Tell me a story"):
                    print(chunk.content, end="", flush=True)

            With interruption handling::

                try:
                    async for chunk in agent.stream("Long response"):
                        print(chunk.content, end="")
                        if some_condition:
                            break
                except StreamInterruptedError as e:
                    print(f"Stream interrupted: {e.partial_response}")
        """
        # Check if provider supports streaming
        if not hasattr(self.provider, "stream"):
            raise ProviderError(
                f"Provider {self.provider.__class__.__name__} does not support streaming. "
                f"Use run() or arun() instead."
            )

        try:
            # Start reasoning
            reasoning_trace = self._reasoning.start_trace(prompt)

            # Add user message
            user_message = Message(
                role=MessageRole.USER,
                content=prompt,
                metadata={"context": context} if context else {},
            )
            self._messages.append(user_message)

            # Get memory context
            memory_context = await self._memory_store.get_context(
                query=prompt, max_items=10
            )

            # Build conversation
            messages = self._build_messages(memory_context, context)

            # Get available tools
            tools_schema = self._tool_registry.get_tools_schema()

            # Track streaming
            reasoning_trace.add_step(
                "streaming_start",
                {
                    "model": self.config.model,
                    "temperature": self.config.temperature,
                    "streaming": True,
                },
            )

            # Stream from provider
            accumulated_content = ""
            accumulated_tool_calls = []

            async for chunk in self.provider.stream(
                messages=messages,
                tools=tools_schema if tools_schema else None,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs,
            ):
                # Yield content chunks
                if chunk.content:
                    accumulated_content += chunk.content
                    yield chunk

                # Handle final chunk with metadata
                if chunk.is_final and chunk.metadata:
                    # Extract tool calls if any
                    if "tool_calls" in chunk.metadata and chunk.metadata["tool_calls"]:
                        # Process tool calls
                        tool_calls = [
                            ToolCall(**tc) for tc in chunk.metadata["tool_calls"]
                        ]

                        # Execute tools
                        tool_results = await self._execute_tools(
                            tool_calls, reasoning_trace
                        )

                        if tool_results:
                            # Add tool message
                            tool_message = Message(
                                role=MessageRole.ASSISTANT,
                                content=accumulated_content,
                                tool_calls=[
                                    {
                                        "id": tc.id,
                                        "type": "function",
                                        "function": {
                                            "name": tc.name,
                                            "arguments": json.dumps(tc.arguments)
                                            if isinstance(tc.arguments, dict)
                                            else tc.arguments
                                        }
                                    }
                                    for tc in tool_calls
                                ],
                            )
                            self._messages.append(tool_message)

                            # Add assistant message with tool calls to messages
                            messages.append(tool_message.to_dict())

                            # Add tool results to messages
                            for result in tool_results:
                                result_message = Message(
                                    role=MessageRole.TOOL,
                                    content=json.dumps(result.result),
                                    metadata={"tool_call_id": result.tool_call_id},
                                )
                                messages.append(result_message.to_dict())

                            # Stream final response after tool execution
                            accumulated_content = ""
                            async for final_chunk in self.provider.stream(
                                messages=messages,
                                temperature=self.config.temperature,
                                max_tokens=self.config.max_tokens,
                                **kwargs,
                            ):
                                if final_chunk.content:
                                    accumulated_content += final_chunk.content
                                yield final_chunk

            # Add assistant message
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=accumulated_content,
                metadata={"streamed": True},
            )
            self._messages.append(assistant_message)

            # Store in memory
            await self._memory_store.store(
                user_message=user_message, assistant_message=assistant_message
            )

            # Complete reasoning
            reasoning_trace.complete(
                {"response": accumulated_content, "streamed": True}
            )

        except StreamInterruptedError:
            # Re-raise stream interruptions
            raise
        except Exception as e:
            logger.error(f"Agent streaming failed: {e}")
            raise AgentError(f"Agent streaming failed: {e}") from e

    def _build_messages(
        self,
        memory_context: list[Message],
        user_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Build the message list for the LLM."""
        messages = []

        # System message
        system_content = self.config.instructions
        if user_context:
            context_str = "\n".join(f"{k}: {v}" for k, v in user_context.items())
            system_content += f"\n\nContext:\n{context_str}"

        messages.append({"role": "system", "content": system_content})

        # Add memory context
        for msg in memory_context:
            messages.append(msg.to_dict())

        # Clean message history before building messages
        self._clean_message_history()
        
        # Add recent messages, filtering out incomplete tool call sequences
        recent_messages = self._messages[-10:]  # Last 10 messages
        
        # Process messages to ensure tool call/response pairs are complete
        i = 0
        while i < len(recent_messages):
            msg = recent_messages[i]
            msg_dict = msg.to_dict()
            
            # If this is an assistant message with tool calls
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                # Check if we have corresponding tool responses
                tool_call_ids = set()
                for tc in msg.tool_calls:
                    if isinstance(tc, dict) and "id" in tc:
                        tool_call_ids.add(tc["id"])
                
                # Look for tool responses in subsequent messages
                j = i + 1
                found_responses = set()
                while j < len(recent_messages) and recent_messages[j].role == MessageRole.TOOL:
                    tool_msg = recent_messages[j]
                    if "tool_call_id" in tool_msg.metadata:
                        found_responses.add(tool_msg.metadata["tool_call_id"])
                    j += 1
                
                # Only include this message if all tool calls have responses
                if tool_call_ids.issubset(found_responses):
                    messages.append(msg_dict)
                    # Add the tool response messages
                    for k in range(i + 1, j):
                        messages.append(recent_messages[k].to_dict())
                    i = j  # Skip to after tool responses
                else:
                    # Skip this message and its incomplete tool responses
                    i = j if j > i + 1 else i + 1
            else:
                # Regular message, just add it
                messages.append(msg_dict)
                i += 1

        return messages

    async def _execute_tools(
        self, tool_calls: list[ToolCall], reasoning_trace: ReasoningTrace
    ) -> list[ToolResult]:
        """Execute tool calls."""
        results = []

        for tool_call in tool_calls:
            reasoning_trace.add_step(
                "executing_tool",
                {"tool": tool_call.name, "arguments": tool_call.arguments},
            )

            try:
                result = await self._tool_registry.execute(
                    tool_call.name, **tool_call.arguments
                )

                results.append(ToolResult(tool_call_id=tool_call.id, result=result))

                reasoning_trace.add_step(
                    "tool_result", {"tool": tool_call.name, "result": result}
                )

            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                error_result = ToolResult(
                    tool_call_id=tool_call.id, result={"error": str(e)}, error=str(e)
                )
                results.append(error_result)

                reasoning_trace.add_step(
                    "tool_error", {"tool": tool_call.name, "error": str(e)}
                )

        return results

    def add_tool(self, tool: BaseTool | callable) -> None:
        """Add a tool to the agent dynamically.

        Note: This method is deprecated. Use WorkflowAgent with handlers instead.

        Args:
            tool: Tool instance or callable to add
        """
        import warnings

        warnings.warn(
            "add_tool is deprecated. Use WorkflowAgent with handlers for tool-like functionality.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._tool_registry.register(tool)
        self.config.tools.append(tool)

    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        self._memory_store.clear()
        self._messages.clear()
    
    async def execute_secure(
        self,
        operation: Any,
        *args,
        user_context: dict[str, Any] | None = None,
        **kwargs
    ) -> Any:
        """Execute an operation in a secure sandbox.
        
        Args:
            operation: The operation to execute (callable or code string)
            *args: Positional arguments for the operation
            user_context: Optional user context for security
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation or SecureResult if sandbox is enabled
            
        Raises:
            SecurityException: If security check fails
            RuntimeError: If sandbox is not available
        """
        if not self.config.sandbox_enabled or not SECURITY_AVAILABLE:
            # Fallback to direct execution
            if callable(operation):
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                else:
                    return operation(*args, **kwargs)
            else:
                raise ValueError("Non-sandboxed execution requires callable operation")
        
        if not self._sandbox_manager:
            raise RuntimeError("Sandbox manager not initialized")
        
        # Update security context with user context
        security_context = self._security_context
        if user_context and "user_id" in user_context:
            from ..security import SecurityContext
            security_context = SecurityContext(
                user_id=user_context["user_id"],
                permissions=user_context.get("permissions", ["execute"]),
                resource_limits=self._security_context.resource_limits,
                metadata=user_context
            )
        
        # Get appropriate sandbox
        if self.config.sandbox_type:
            from ..security import SandboxType
            sandbox_type = SandboxType(self.config.sandbox_type)
            sandbox = await self._sandbox_manager.get_sandbox(sandbox_type)
        else:
            # Use default sandbox type
            sandbox = await self._sandbox_manager.get_sandbox()
        
        # Execute in sandbox
        if isinstance(operation, str):
            # Code execution
            result = await sandbox.execute_code(operation, security_context)
        else:
            # Callable execution
            result = await sandbox.execute(operation, security_context, *args, **kwargs)
        
        if not result.success:
            raise SecurityException(f"Secure execution failed: {result.error}")
        
        return result.result
    
    async def execute_tool_secure(
        self,
        tool_name: str,
        user_context: dict[str, Any] | None = None,
        **kwargs
    ) -> Any:
        """Execute a tool in a secure sandbox.
        
        Args:
            tool_name: Name of the tool to execute
            user_context: Optional user context for security
            **kwargs: Arguments for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            SecurityException: If security check fails
        """
        # Get the tool
        tool = self._tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # For sandbox execution, check if we're using RestrictedPythonSandbox
        # which doesn't support callable execution
        if self.config.sandbox_enabled and SECURITY_AVAILABLE:
            from ..security import SandboxType
            
            # If using restricted sandbox, execute tool directly with security checks
            if not self.config.sandbox_type or self.config.sandbox_type == "restricted":
                # Log security event but execute outside sandbox
                # This is a limitation of RestrictedPythonSandbox
                logger.warning(
                    "RestrictedPythonSandbox doesn't support tool execution. "
                    "Executing with security context but outside sandbox."
                )
                return await tool.arun(**kwargs)
            else:
                # Other sandboxes can handle callables
                async def tool_wrapper():
                    return await tool.arun(**kwargs)
                
                return await self.execute_secure(
                    tool_wrapper,
                    user_context=user_context
                )
        else:
            # Direct execution without sandbox
            return await tool.arun(**kwargs)
    
    def _clean_message_history(self) -> None:
        """Clean message history to remove incomplete tool call sequences."""
        cleaned_messages = []
        i = 0
        
        while i < len(self._messages):
            msg = self._messages[i]
            
            # If this is an assistant message with tool calls
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                # Collect tool call IDs
                tool_call_ids = set()
                for tc in msg.tool_calls:
                    if isinstance(tc, dict) and "id" in tc:
                        tool_call_ids.add(tc["id"])
                
                # Look for corresponding tool responses
                j = i + 1
                tool_responses = []
                found_ids = set()
                
                while j < len(self._messages) and self._messages[j].role == MessageRole.TOOL:
                    tool_msg = self._messages[j]
                    if "tool_call_id" in tool_msg.metadata:
                        found_ids.add(tool_msg.metadata["tool_call_id"])
                        tool_responses.append(tool_msg)
                    j += 1
                
                # Only keep if all tool calls have responses
                if tool_call_ids.issubset(found_ids):
                    cleaned_messages.append(msg)
                    cleaned_messages.extend(tool_responses)
                
                i = j  # Skip to after tool responses
            else:
                # Keep regular messages
                cleaned_messages.append(msg)
                i += 1
        
        self._messages = cleaned_messages

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"Agent(name='{self.name}', "
            f"model='{self.config.model}', "
            f"tools={len(self.config.tools)})"
        )

    def set_provider(
        self,
        provider_name: str,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Switch the agent's LLM provider dynamically.

        This method allows switching between different LLM providers while
        preserving the agent's configuration, tools, memory, and state.

        Args:
            provider_name: Name of the provider ("openai", "anthropic", "ollama")
            model: Optional model override for the new provider
            api_key: Optional API key for the new provider
            base_url: Optional base URL (mainly for Ollama)
            **kwargs: Additional provider-specific parameters

        Raises:
            ProviderError: If the provider name is invalid or setup fails

        Example:
            >>> # Switch to Anthropic
            >>> agent.set_provider("anthropic", model="claude-3-opus-20240229")
            >>>
            >>> # Switch to local Ollama
            >>> agent.set_provider("ollama", model="llama2", base_url="http://localhost:11434")
            >>>
            >>> # Switch back to OpenAI with specific model
            >>> agent.set_provider("openai", model="gpt-3.5-turbo")

        Note:
            When switching providers, the agent will:
            - Preserve all configuration except model and API settings
            - Maintain tool registrations and functionality
            - Keep conversation memory intact
            - Continue with the same reasoning patterns
        """
        # Map of provider names to their default models
        provider_defaults = {
            "openai": "gpt-4",
            "anthropic": "claude-3-opus-20240229",
            "ollama": "llama2",
        }

        # Validate provider name
        if provider_name not in provider_defaults:
            raise ProviderError(
                f"Unknown provider: {provider_name}. "
                f"Valid providers are: {', '.join(provider_defaults.keys())}"
            )

        # Determine model to use
        if model is None:
            # If no model specified, use provider default
            model = provider_defaults[provider_name]
        else:
            # For Ollama, strip "ollama/" prefix if present
            if provider_name == "ollama" and model.startswith("ollama/"):
                model = model[7:]  # Remove "ollama/" prefix

        # Store current state for rollback
        old_provider = self._provider
        old_model = self.config.model
        old_api_key = self.config.api_key
        old_base_url = self.config.base_url

        try:
            # Update configuration
            self.config.model = model
            self.config.provider = provider_name
            if api_key is not None:
                self.config.api_key = api_key
            if base_url is not None:
                self.config.base_url = base_url

            # Clear current provider to force recreation
            self._provider = None

            # Access provider property to trigger creation with new settings
            new_provider = self.provider

            # Validate the new provider works
            new_provider.validate_auth()

            logger.info(
                f"Agent '{self.name}' switched to {provider_name} " f"(model: {model})"
            )

        except Exception as e:
            # Rollback on failure
            self._provider = old_provider
            self.config.model = old_model
            self.config.api_key = old_api_key
            self.config.base_url = old_base_url

            logger.error(f"Failed to switch provider: {e}")
            raise ProviderError(f"Failed to switch to {provider_name}: {e}") from e

    def get_provider_info(self) -> dict[str, Any]:
        """Get information about the current provider.

        Returns:
            Dict containing provider name, model, and capabilities

        Example:
            >>> info = agent.get_provider_info()
            >>> print(f"Using {info['provider']} with model {info['model']}")
        """
        provider = self.provider
        provider_name = provider.__class__.__name__.replace("Provider", "").lower()

        return {
            "provider": provider_name,
            "model": self.config.model,
            "supports_streaming": hasattr(provider, "stream")
            and hasattr(provider, "supports_streaming")
            and provider.supports_streaming(),
            "supports_tools": True,  # All providers support tools via adaptation
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

    def list_available_providers(self) -> list[str]:
        """List available LLM providers.

        Returns:
            List of provider names that can be used with set_provider

        Example:
            >>> providers = agent.list_available_providers()
            >>> print(f"Available providers: {', '.join(providers)}")
        """
        # Import here to avoid circular imports
        from .provider import ProviderFactory

        # Ensure providers are loaded
        ProviderFactory._lazy_load_providers()

        return list(ProviderFactory._providers.keys())
