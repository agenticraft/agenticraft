"""Common types used throughout AgentiCraft.

This module defines shared type definitions, enums, and data structures
used across the AgentiCraft framework.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field, field_validator


class ToolCall(BaseModel):
    """Represents a call to a tool."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    arguments: Dict[str, Any]
    
    @field_validator('arguments', mode='before')
    @classmethod
    def validate_arguments(cls, v: Any) -> Dict[str, Any]:
        """Ensure arguments is a dictionary."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"input": v}
        return v


class ToolResult(BaseModel):
    """Result from a tool execution."""
    
    tool_call_id: str
    result: Any
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if the tool execution was successful."""
        return self.error is None


class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    
    def __str__(self) -> str:
        return self.value


class Message(BaseModel):
    """A message in a conversation.
    
    Attributes:
        role: The role of the message sender
        content: The message content
        tool_calls: Tool calls made in this message (for assistant messages)
        metadata: Additional metadata
        created_at: When the message was created
    """
    
    role: MessageRole
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM providers."""
        data = {
            "role": str(self.role),
            "content": self.content
        }
        
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
            
        # Some providers need specific metadata
        if self.role == MessageRole.TOOL and "tool_call_id" in self.metadata:
            data["tool_call_id"] = self.metadata["tool_call_id"]
            
        return data


class CompletionResponse(BaseModel):
    """Response from an LLM completion."""
    
    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None  # Model used for completion


class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


class ToolDefinition(BaseModel):
    """Definition of a tool for LLM providers."""
    
    name: str
    description: str
    parameters: List[ToolParameter]
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function schema."""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
