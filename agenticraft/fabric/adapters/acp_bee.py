"""
IBM ACP (Agent Communication Protocol) Adapter using Bee Framework patterns.

Since there's no official Python SDK for IBM ACP, this adapter implements
the protocol based on IBM's Bee framework patterns:
https://github.com/i-am-bee/beeai-framework
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
from ..protocol_types import IProtocolAdapter, ProtocolType, UnifiedTool, ProtocolCapability

# Import ToolInfo or define if needed
from dataclasses import dataclass as base_dataclass, field

@base_dataclass 
class ToolInfo:
    """Information about a tool."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class MessageType(Enum):
    """IBM ACP message types based on Bee framework."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"


@dataclass
class ACPMessage:
    """IBM ACP message structure."""
    id: str
    type: MessageType
    sender: str
    receiver: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class ACPBeeAdapter(IProtocolAdapter):
    """
    Adapter for IBM Agent Communication Protocol using Bee framework patterns.
    
    This implementation is based on IBM's Bee framework since there's no
    official Python SDK yet. It follows IBM's ACP specifications for:
    - RESTful communication
    - Session management
    - MIME multipart messages
    - Tool orchestration
    - Agent collaboration
    
    Reference:
    - https://www.ibm.com/think/topics/agent-communication-protocol
    - https://github.com/i-am-bee/beeai-framework
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url: Optional[str] = None
        self.agent_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self._message_handlers: Dict[MessageType, Any] = {}
        self._tools_cache: Dict[str, Dict[str, Any]] = {}
    
    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.ACP
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Connect to IBM ACP service following Bee patterns."""
        self.base_url = config.get("url", "http://localhost:9000")
        self.agent_id = config.get("agent_id", "agenticraft-agent")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={
                "Content-Type": "application/json",
                "X-Agent-ID": self.agent_id,
                "X-Agent-Type": "AgentiCraft"
            }
        )
        
        # Initialize session following Bee framework pattern
        session_data = {
            "agent": {
                "id": self.agent_id,
                "name": config.get("name", "AgentiCraft ACP Agent"),
                "capabilities": config.get("capabilities", ["tool-execution"]),
                "version": "1.0.0"
            },
            "config": {
                "timeout": config.get("timeout", 30),
                "max_retries": config.get("max_retries", 3)
            }
        }
        
        # Create session
        async with self.session.post(
            f"{self.base_url}/sessions",
            json=session_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.session_id = data.get("session_id")
                # Update headers with session ID
                self.session.headers.update({
                    "X-Session-ID": self.session_id
                })
            else:
                raise ConnectionError(
                    f"Failed to create ACP session: {response.status}"
                )
        
        # Discover available tools
        await self._discover_remote_tools()
    
    async def disconnect(self) -> None:
        """Disconnect from ACP service."""
        if self.session and self.session_id:
            try:
                # Close session
                await self.session.delete(
                    f"{self.base_url}/sessions/{self.session_id}"
                )
            except Exception:
                pass  # Ignore errors during cleanup
            
            await self.session.close()
            self.session = None
            self.session_id = None
    
    async def _discover_remote_tools(self) -> None:
        """Discover tools following Bee framework patterns."""
        async with self.session.get(
            f"{self.base_url}/tools"
        ) as response:
            if response.status == 200:
                tools = await response.json()
                for tool in tools.get("tools", []):
                    self._tools_cache[tool["name"]] = tool
    
    async def discover_tools(self) -> List[ToolInfo]:
        """Get available tools through ACP."""
        tools = []
        
        for tool_name, tool_data in self._tools_cache.items():
            tools.append(ToolInfo(
                name=tool_name,
                description=tool_data.get("description", ""),
                parameters=tool_data.get("input_schema", {})
            ))
        
        return tools
    
    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute tool following IBM ACP patterns."""
        if tool_name not in self._tools_cache:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Create tool execution message following Bee patterns
        message = ACPMessage(
            id=self._generate_message_id(),
            type=MessageType.TOOL_CALL,
            sender=self.agent_id,
            receiver="system",  # System handles tool routing
            content={
                "tool": tool_name,
                "arguments": arguments or {},
                "context": {
                    "session_id": self.session_id,
                    "timestamp": self._get_timestamp()
                }
            }
        )
        
        # Send tool execution request
        async with self.session.post(
            f"{self.base_url}/messages",
            json=self._message_to_dict(message)
        ) as response:
            if response.status == 200:
                result = await response.json()
                
                # Handle async execution pattern (Bee framework)
                if result.get("status") == "pending":
                    # Poll for result
                    execution_id = result.get("execution_id")
                    return await self._poll_for_result(execution_id)
                else:
                    # Immediate result
                    return result.get("result")
            else:
                error_data = await response.text()
                raise RuntimeError(
                    f"Tool execution failed: {response.status} - {error_data}"
                )
    
    async def _poll_for_result(
        self, 
        execution_id: str, 
        max_attempts: int = 30,
        interval: float = 1.0
    ) -> Any:
        """Poll for async execution result (Bee pattern)."""
        for attempt in range(max_attempts):
            async with self.session.get(
                f"{self.base_url}/executions/{execution_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get("status")
                    
                    if status == "completed":
                        return data.get("result")
                    elif status == "failed":
                        raise RuntimeError(
                            f"Execution failed: {data.get('error')}"
                        )
                    
                    # Still pending, wait
                    await asyncio.sleep(interval)
                else:
                    raise RuntimeError(
                        f"Failed to get execution status: {response.status}"
                    )
        
        raise TimeoutError(f"Execution {execution_id} timed out")
    
    async def send_message(
        self, 
        receiver: str, 
        content: Dict[str, Any],
        message_type: MessageType = MessageType.REQUEST
    ) -> Optional[Dict[str, Any]]:
        """Send message to another agent (IBM ACP feature)."""
        message = ACPMessage(
            id=self._generate_message_id(),
            type=message_type,
            sender=self.agent_id,
            receiver=receiver,
            content=content,
            metadata={
                "session_id": self.session_id,
                "timestamp": self._get_timestamp()
            }
        )
        
        async with self.session.post(
            f"{self.base_url}/messages",
            json=self._message_to_dict(message)
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise RuntimeError(
                    f"Failed to send message: {response.status}"
                )
    
    async def create_workflow(
        self, 
        workflow_definition: Dict[str, Any]
    ) -> str:
        """Create a workflow (Bee framework feature)."""
        async with self.session.post(
            f"{self.base_url}/workflows",
            json=workflow_definition
        ) as response:
            if response.status == 201:
                data = await response.json()
                return data.get("workflow_id")
            else:
                raise RuntimeError(
                    f"Failed to create workflow: {response.status}"
                )
    
    async def execute_workflow(
        self, 
        workflow_id: str, 
        inputs: Dict[str, Any]
    ) -> Any:
        """Execute a workflow (Bee framework feature)."""
        async with self.session.post(
            f"{self.base_url}/workflows/{workflow_id}/execute",
            json={"inputs": inputs}
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                # Handle async workflow execution
                if data.get("status") == "pending":
                    execution_id = data.get("execution_id")
                    return await self._poll_for_result(execution_id)
                else:
                    return data.get("result")
            else:
                raise RuntimeError(
                    f"Failed to execute workflow: {response.status}"
                )
    
    def _message_to_dict(self, message: ACPMessage) -> Dict[str, Any]:
        """Convert ACPMessage to dictionary."""
        return {
            "id": message.id,
            "type": message.type.value,
            "sender": message.sender,
            "receiver": message.receiver,
            "content": message.content,
            "metadata": message.metadata or {}
        }
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    async def get_capabilities(self) -> List[ProtocolCapability]:
        """Get ACP capabilities."""
        capabilities = []
        
        if self.session_id:
            capabilities.append(ProtocolCapability(
                name="tools",
                description="Tool discovery and execution via ACP",
                protocol=ProtocolType.ACP
            ))
            
            capabilities.append(ProtocolCapability(
                name="messaging",
                description="Agent-to-agent messaging",
                protocol=ProtocolType.ACP
            ))
            
            capabilities.append(ProtocolCapability(
                name="workflows",
                description="Workflow creation and execution (Bee framework)",
                protocol=ProtocolType.ACP
            ))
            
            capabilities.append(ProtocolCapability(
                name="sessions",
                description="Session management",
                protocol=ProtocolType.ACP,
                metadata={"session_id": self.session_id}
            ))
            
            capabilities.append(ProtocolCapability(
                name="async_execution",
                description="Asynchronous tool and workflow execution",
                protocol=ProtocolType.ACP
            ))
            
            if self._tools_cache:
                capabilities.append(ProtocolCapability(
                    name="tool_discovery",
                    description="Dynamic tool discovery",
                    protocol=ProtocolType.ACP,
                    metadata={"tool_count": len(self._tools_cache)}
                ))
        
        return capabilities
    
    def supports_feature(self, feature: str) -> bool:
        """Check if adapter supports a specific feature."""
        return feature in {
            'tools', 'messaging', 'workflows', 'sessions',
            'async_execution', 'multipart_messages'
        }


class ACPEnhancedAdapter(ACPBeeAdapter):
    """
    Enhanced ACP adapter with additional enterprise features.
    
    Adds support for:
    - Message queuing
    - Retry logic
    - Circuit breaker pattern
    - Metrics collection
    """
    
    def __init__(self):
        super().__init__()
        self._metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "tools_executed": 0,
            "errors": 0
        }
        self._circuit_breaker_open = False
        self._consecutive_failures = 0
    
    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute tool with circuit breaker and metrics."""
        if self._circuit_breaker_open:
            raise RuntimeError("Circuit breaker is open - service unavailable")
        
        try:
            result = await super().execute_tool(tool_name, arguments)
            self._metrics["tools_executed"] += 1
            self._consecutive_failures = 0  # Reset on success
            return result
        except Exception as e:
            self._metrics["errors"] += 1
            self._consecutive_failures += 1
            
            # Open circuit breaker after 5 consecutive failures
            if self._consecutive_failures >= 5:
                self._circuit_breaker_open = True
                # Schedule circuit breaker reset
                asyncio.create_task(self._reset_circuit_breaker())
            
            raise
    
    async def _reset_circuit_breaker(self):
        """Reset circuit breaker after cooldown period."""
        await asyncio.sleep(30)  # 30 second cooldown
        self._circuit_breaker_open = False
        self._consecutive_failures = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        return self._metrics.copy()
