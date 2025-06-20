"""
Protocol types and interfaces for the unified fabric.

This module contains shared types used across the fabric layer.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from agenticraft.core.exceptions import ToolError


class ProtocolType(Enum):
    """Supported protocol types."""
    A2A = "a2a"       # Google's Agent-to-Agent Protocol
    MCP = "mcp"       # Anthropic's Model Context Protocol
    ACP = "acp"       # IBM's Agent Communication Protocol
    ANP = "anp"       # Agent Network Protocol (Decentralized)
    NATIVE = "native" # AgentiCraft native


@dataclass
class ProtocolCapability:
    """Represents a capability exposed by a protocol."""
    name: str
    description: str
    protocol: ProtocolType
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedTool:
    """Unified tool representation across all protocols."""
    name: str
    description: str
    protocol: ProtocolType
    original_tool: Any  # Original protocol-specific tool
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool through its native protocol."""
        if hasattr(self.original_tool, 'arun'):
            return await self.original_tool.arun(**kwargs)
        elif hasattr(self.original_tool, 'execute'):
            return await self.original_tool.execute(**kwargs)
        else:
            raise ToolError(f"Tool {self.name} has no executable method")


class IProtocolAdapter(ABC):
    """Interface for protocol adapters."""
    
    @property
    @abstractmethod
    def protocol_type(self) -> ProtocolType:
        """Get the protocol type."""
        pass
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to the protocol server/service."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the protocol."""
        pass
    
    @abstractmethod
    async def discover_tools(self) -> List[UnifiedTool]:
        """Discover available tools from the protocol."""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool through the protocol."""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get protocol capabilities."""
        pass
    
    def supports_feature(self, feature: str) -> bool:
        """Check if adapter supports a specific feature."""
        # Default implementation - subclasses can override
        return False
