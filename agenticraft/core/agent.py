"""Base Agent class for AgentiCraft.

This module provides the core Agent class that all agents in AgentiCraft
are built upon. The Agent class handles LLM interactions, tool execution,
memory management, and reasoning patterns.

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
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import settings
from .exceptions import AgentError, ToolExecutionError
from .memory import BaseMemory, MemoryStore
from .provider import BaseProvider, ProviderFactory
from .reasoning import BaseReasoning, ReasoningTrace, SimpleReasoning
from .tool import BaseTool, ToolRegistry
from .types import Message, MessageRole, ToolCall, ToolResult

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
    reasoning: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.now)


class AgentConfig(BaseModel):
    """Configuration for an Agent.
    
    Attributes:
        name: The agent's name
        instructions: System instructions defining the agent's behavior
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
        description="System instructions defining agent behavior"
    )
    model: str = Field(default_factory=lambda: settings.default_model, description="LLM model to use")
    temperature: float = Field(default_factory=lambda: settings.default_temperature, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default_factory=lambda: settings.default_max_tokens, gt=0)
    tools: List[Any] = Field(default_factory=list)
    memory: List[Any] = Field(default_factory=list)
    reasoning_pattern: Optional[Any] = None
    api_key: Optional[str] = Field(default=None, exclude=True)
    base_url: Optional[str] = None
    timeout: int = Field(default_factory=lambda: settings.default_timeout, gt=0)
    max_retries: int = Field(default_factory=lambda: settings.default_max_retries, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('tools')
    def validate_tools(cls, tools: List[Any]) -> List[Any]:
        """Validate tools are proper type."""
        from .tool import BaseTool
        for tool in tools:
            if not (isinstance(tool, BaseTool) or callable(tool)):
                raise ValueError(f"Invalid tool type: {type(tool)}")
        return tools
    
    @field_validator('memory')
    def validate_memory(cls, memory: List[Any]) -> List[Any]:
        """Validate memory instances."""
        from .memory import BaseMemory
        for mem in memory:
            if not isinstance(mem, BaseMemory):
                raise ValueError(f"Invalid memory type: {type(mem)}")
        return memory


class Agent:
    """Base Agent class for AgentiCraft.
    
    The Agent class is the core abstraction in AgentiCraft. It combines
    an LLM provider, tools, memory, and reasoning patterns to create
    an intelligent agent capable of complex tasks.
    
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
            
        Creating an agent with tools::
        
            from agenticraft import tool
            
            @tool
            def calculate(expr: str) -> float:
                return eval(expr)
                
            agent = Agent(
                name="Calculator",
                tools=[calculate]
            )
    """
    
    def __init__(
        self,
        name: str = "Agent",
        instructions: str = "You are a helpful AI assistant.",
        model: str = "gpt-4",
        **kwargs: Any
    ):
        """Initialize an Agent."""
        # Create config
        self.config = AgentConfig(
            name=name,
            instructions=instructions,
            model=model,
            **kwargs
        )
        
        # Generate unique ID
        self.id = uuid4()
        
        # Initialize components
        self._provider: Optional[BaseProvider] = None
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
        self._messages: List[Message] = []
        
        logger.info(f"Initialized agent '{self.name}' with ID {self.id}")
    
    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self.config.name
    
    @property
    def provider(self) -> BaseProvider:
        """Get or create the LLM provider."""
        if self._provider is None:
            self._provider = ProviderFactory.create(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries
            )
        return self._provider
    
    def run(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
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
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
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
                metadata={"context": context} if context else {}
            )
            self._messages.append(user_message)
            
            # Get memory context
            memory_context = await self._memory_store.get_context(
                query=prompt,
                max_items=10
            )
            
            # Build conversation
            messages = self._build_messages(memory_context, context)
            
            # Get available tools
            tools_schema = self._tool_registry.get_tools_schema()
            
            # Call LLM
            reasoning_trace.add_step("calling_llm", {
                "model": self.config.model,
                "temperature": self.config.temperature
            })
            
            response = await self.provider.complete(
                messages=messages,
                tools=tools_schema if tools_schema else None,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs
            )
            
            # Process tool calls if any
            tool_results = []
            executed_tool_calls = []  # Track the tool calls we executed
            if response.tool_calls:
                executed_tool_calls = response.tool_calls  # Save for later
                tool_results = await self._execute_tools(
                    response.tool_calls,
                    reasoning_trace
                )
                
                # If tools were called, we need another LLM call with results
                if tool_results:
                    tool_message = Message(
                        role=MessageRole.ASSISTANT,
                        content=response.content,
                        tool_calls=[tc.model_dump() for tc in response.tool_calls]
                    )
                    self._messages.append(tool_message)
                    
                    # Add tool results
                    for result in tool_results:
                        result_message = Message(
                            role=MessageRole.TOOL,
                            content=json.dumps(result.result),
                            metadata={"tool_call_id": result.tool_call_id}
                        )
                        messages.append(result_message)
                    
                    # Get final response
                    response = await self.provider.complete(
                        messages=messages,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        **kwargs
                    )
            
            # Add assistant message
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response.content,
                metadata=response.metadata
            )
            self._messages.append(assistant_message)
            
            # Store in memory
            await self._memory_store.store(
                user_message=user_message,
                assistant_message=assistant_message
            )
            
            # Complete reasoning
            reasoning_trace.complete({"response": response.content})
            
            # Build response
            return AgentResponse(
                content=response.content,
                reasoning=self._reasoning.format_trace(reasoning_trace),
                tool_calls=[tc.model_dump() for tc in executed_tool_calls],  # Use the saved tool calls
                metadata={
                    "model": self.config.model,
                    "reasoning_pattern": self._reasoning.__class__.__name__,
                    **response.metadata
                },
                agent_id=self.id
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise AgentError(f"Agent execution failed: {e}") from e
    
    def _build_messages(
        self,
        memory_context: List[Message],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Build the message list for the LLM."""
        messages = []
        
        # System message
        system_content = self.config.instructions
        if user_context:
            context_str = "\n".join(
                f"{k}: {v}" for k, v in user_context.items()
            )
            system_content += f"\n\nContext:\n{context_str}"
            
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add memory context
        for msg in memory_context:
            messages.append(msg.to_dict())
        
        # Add recent messages
        for msg in self._messages[-10:]:  # Last 10 messages
            messages.append(msg.to_dict())
            
        return messages
    
    async def _execute_tools(
        self,
        tool_calls: List[ToolCall],
        reasoning_trace: ReasoningTrace
    ) -> List[ToolResult]:
        """Execute tool calls."""
        results = []
        
        for tool_call in tool_calls:
            reasoning_trace.add_step("executing_tool", {
                "tool": tool_call.name,
                "arguments": tool_call.arguments
            })
            
            try:
                result = await self._tool_registry.execute(
                    tool_call.name,
                    **tool_call.arguments
                )
                
                results.append(ToolResult(
                    tool_call_id=tool_call.id,
                    result=result
                ))
                
                reasoning_trace.add_step("tool_result", {
                    "tool": tool_call.name,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                error_result = ToolResult(
                    tool_call_id=tool_call.id,
                    result={"error": str(e)},
                    error=str(e)
                )
                results.append(error_result)
                
                reasoning_trace.add_step("tool_error", {
                    "tool": tool_call.name,
                    "error": str(e)
                })
        
        return results
    
    def add_tool(self, tool: Union[BaseTool, callable]) -> None:
        """Add a tool to the agent dynamically.
        
        Args:
            tool: Tool instance or callable to add
            
        Example:
            Adding a tool after creation::
            
                @tool
                def search(query: str) -> str:
                    return f"Results for {query}"
                    
                agent.add_tool(search)
        """
        self._tool_registry.register(tool)
        self.config.tools.append(tool)
    
    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        self._memory_store.clear()
        self._messages.clear()
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"Agent(name='{self.name}', "
            f"model='{self.config.model}', "
            f"tools={len(self.config.tools)})"
        )
