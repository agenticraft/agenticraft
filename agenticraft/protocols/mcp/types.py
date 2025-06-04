"""Type definitions for Model Context Protocol.

This module defines the data structures used in MCP communication,
including requests, responses, tools, and errors.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MCPMethod(str, Enum):
    """MCP protocol methods."""
    
    # Discovery
    LIST_TOOLS = "tools/list"
    DESCRIBE_TOOL = "tools/describe"
    
    # Execution
    CALL_TOOL = "tools/call"
    
    # Lifecycle
    INITIALIZE = "initialize"
    SHUTDOWN = "shutdown"
    
    # Server info
    GET_INFO = "server/info"
    GET_CAPABILITIES = "server/capabilities"


class MCPErrorCode(str, Enum):
    """MCP error codes."""
    
    PARSE_ERROR = "parse_error"
    INVALID_REQUEST = "invalid_request"
    METHOD_NOT_FOUND = "method_not_found"
    INVALID_PARAMS = "invalid_params"
    INTERNAL_ERROR = "internal_error"
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_EXECUTION_ERROR = "tool_execution_error"


class MCPCapability(str, Enum):
    """MCP server capabilities."""
    
    TOOLS = "tools"
    STREAMING = "streaming"
    CANCELLATION = "cancellation"
    PROGRESS = "progress"
    MULTI_TOOL = "multi_tool"


@dataclass
class MCPRequest:
    """MCP request message."""
    
    jsonrpc: str = "2.0"
    method: MCPMethod = MCPMethod.LIST_TOOLS
    params: Optional[Dict[str, Any]] = None
    id: Union[str, int] = field(default_factory=lambda: str(uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "jsonrpc": self.jsonrpc,
            "method": self.method.value,
            "id": self.id
        }
        if self.params is not None:
            data["params"] = self.params
        return data


@dataclass
class MCPResponse:
    """MCP response message."""
    
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    result: Optional[Any] = None
    error: Optional["MCPError"] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        
        if self.error is not None:
            data["error"] = self.error.to_dict()
        else:
            data["result"] = self.result
            
        return data
    
    @property
    def is_error(self) -> bool:
        """Check if response is an error."""
        return self.error is not None


@dataclass
class MCPError:
    """MCP error structure."""
    
    code: MCPErrorCode
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        error_dict = {
            "code": self.code.value,
            "message": self.message
        }
        if self.data is not None:
            error_dict["data"] = self.data
        return error_dict


class MCPToolParameter(BaseModel):
    """MCP tool parameter definition."""
    
    name: str
    type: str  # JSON Schema type
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: Dict[str, Any] = {
            "type": self.type
        }
        
        if self.description:
            schema["description"] = self.description
        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
            
        return schema


class MCPTool(BaseModel):
    """MCP tool definition."""
    
    name: str
    description: str
    parameters: List[MCPToolParameter] = Field(default_factory=list)
    returns: Optional[Dict[str, Any]] = None  # JSON Schema for return type
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format for tool definition."""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)
        
        schema = {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
        
        if self.returns:
            schema["returnSchema"] = self.returns
            
        if self.examples:
            schema["examples"] = self.examples
            
        return schema


@dataclass
class MCPServerInfo:
    """MCP server information."""
    
    name: str
    version: str
    description: Optional[str] = None
    capabilities: List[MCPCapability] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": [cap.value for cap in self.capabilities]
        }


@dataclass
class MCPToolCall:
    """MCP tool invocation."""
    
    tool: str
    arguments: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool": self.tool,
            "arguments": self.arguments,
            "id": self.id
        }


@dataclass
class MCPToolResult:
    """MCP tool execution result."""
    
    tool_call_id: str
    result: Any
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "tool_call_id": self.tool_call_id
        }
        
        if self.error:
            data["error"] = self.error
        else:
            data["result"] = self.result
            
        return data
    
    @property
    def is_error(self) -> bool:
        """Check if result is an error."""
        return self.error is not None


# Connection-related types
@dataclass
class MCPConnectionConfig:
    """Configuration for MCP connection."""
    
    url: str
    timeout: int = 30
    max_retries: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_websocket(self) -> bool:
        """Check if URL is WebSocket."""
        return self.url.startswith("ws://") or self.url.startswith("wss://")
    
    @property
    def is_http(self) -> bool:
        """Check if URL is HTTP."""
        return self.url.startswith("http://") or self.url.startswith("https://")
