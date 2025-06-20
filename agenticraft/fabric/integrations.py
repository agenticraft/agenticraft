"""
Protocol Fabric Integrations.

This module provides integration bridges between the Protocol Fabric
and other AgentiCraft components.
"""

from typing import Dict, List, Any, Optional, AsyncIterator
import asyncio
from dataclasses import dataclass
import time

from agenticraft.fabric import UnifiedProtocolFabric, ProtocolType
from agenticraft.core.streaming import StreamChunk, StreamingProvider
from agenticraft.memory import MemoryStore, MemoryEntry, MemoryType
# Import reasoning components if available
try:
    from agenticraft.reasoning import ReasoningPattern, ReasoningStep
except ImportError:
    # Basic fallback classes
    from abc import ABC, abstractmethod
    from dataclasses import dataclass
    from typing import Any, Dict, List
    
    @dataclass
    class ReasoningStep:
        description: str
        result: Any = None
        error: str = None
        metadata: Dict[str, Any] = None
        timestamp: float = 0.0
    
    class ReasoningPattern(ABC):
        @abstractmethod
        async def reason(self, problem: str, context: Dict[str, Any] = None) -> Any:
            pass
from agenticraft.telemetry import get_tracer, get_meter, set_span_attributes
from agenticraft.security import SecurityContext, ISandbox


# Streaming Integration
class ProtocolStreamingProvider(StreamingProvider):
    """
    Streaming provider that works with protocol tools.
    
    Enables streaming responses from any protocol that supports it.
    """
    
    def __init__(self, fabric: UnifiedProtocolFabric):
        self.fabric = fabric
        self.supported_protocols = {
            ProtocolType.MCP: True,      # MCP supports streaming
            ProtocolType.A2A: False,     # A2A doesn't yet
            ProtocolType.ACP: True,      # ACP with async support
            ProtocolType.ANP: False      # ANP is request/response
        }
    
    async def stream(
        self, 
        protocol: str,
        tool_name: str,
        **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        """Stream from a protocol tool if supported."""
        protocol_type = ProtocolType(protocol)
        
        if not self.supports_streaming_for(protocol_type):
            # Simulate streaming for non-streaming protocols
            result = await self.fabric.execute_tool(protocol, tool_name, **kwargs)
            for i, char in enumerate(str(result)):
                yield StreamChunk(
                    content=char,
                    metadata={
                        'protocol': protocol,
                        'tool': tool_name,
                        'simulated': True
                    }
                )
                await asyncio.sleep(0.01)  # Simulate delay
        else:
            # Use native streaming
            adapter = self.fabric.get_adapter(protocol)
            if hasattr(adapter, 'stream_tool'):
                async for chunk in adapter.stream_tool(tool_name, **kwargs):
                    yield StreamChunk(
                        content=chunk,
                        metadata={
                            'protocol': protocol,
                            'tool': tool_name
                        }
                    )
    
    def supports_streaming(self) -> bool:
        """Check if any protocol supports streaming."""
        return any(self.supported_protocols.values())
    
    def supports_streaming_for(self, protocol: ProtocolType) -> bool:
        """Check if specific protocol supports streaming."""
        return self.supported_protocols.get(protocol, False)


# Memory Integration
class ProtocolAwareMemoryStore(MemoryStore):
    """
    Memory store that preserves protocol context.
    
    Features:
    - Protocol-tagged memories
    - Cross-protocol memory sharing
    - Tool context preservation
    """
    
    def __init__(self, base_store: MemoryStore, fabric: UnifiedProtocolFabric):
        self.base_store = base_store
        self.fabric = fabric
    
    async def store_with_protocol(
        self,
        entry: MemoryEntry,
        protocol: str,
        tool_name: Optional[str] = None
    ) -> str:
        """Store memory with protocol context."""
        # Enhance metadata with protocol info
        entry.metadata['protocol'] = protocol
        if tool_name:
            entry.metadata['tool'] = tool_name
        
        # Add available tools for context
        try:
            tools = await self.fabric.get_protocol_tools(protocol)
            entry.metadata['available_tools'] = [t.name for t in tools]
        except:
            pass
        
        return await self.base_store.store(entry)
    
    async def share_across_protocols(
        self,
        entry_id: str,
        source_protocol: str,
        target_protocols: List[str]
    ) -> Dict[str, str]:
        """Share memory across protocol boundaries."""
        # Retrieve original entry
        original = await self.base_store.retrieve_by_id(entry_id)
        if not original:
            raise ValueError(f"Memory {entry_id} not found")
        
        shared_ids = {}
        
        for target in target_protocols:
            # Create adapted entry for target protocol
            adapted = MemoryEntry(
                key=f"{original.key}_from_{source_protocol}",
                value=original.value,
                memory_type=original.memory_type,
                metadata={
                    **original.metadata,
                    'shared_from': source_protocol,
                    'shared_to': target,
                    'original_id': entry_id
                }
            )
            
            # Store in target context
            shared_id = await self.store_with_protocol(adapted, target)
            shared_ids[target] = shared_id
        
        return shared_ids
    
    # Delegate standard operations to base store
    async def store(self, entry: MemoryEntry) -> str:
        return await self.base_store.store(entry)
    
    async def retrieve(self, query) -> List[Any]:
        return await self.base_store.retrieve(query)
    
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        return await self.base_store.update(entry_id, updates)
    
    async def delete(self, entry_id: str) -> bool:
        return await self.base_store.delete(entry_id)
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        return await self.base_store.clear(memory_type)
    
    async def get_stats(self) -> Dict[str, Any]:
        stats = await self.base_store.get_stats()
        
        # Add protocol-specific stats
        protocol_counts = {}
        for entry in await self.base_store.get_all():
            protocol = entry.metadata.get('protocol', 'native')
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        stats['by_protocol'] = protocol_counts
        return stats


# Reasoning Integration
class ProtocolAwareReasoningPattern(ReasoningPattern):
    """
    Reasoning pattern that leverages multiple protocols.
    
    Features:
    - Protocol-specific reasoning steps
    - Cross-protocol evidence gathering
    - Protocol confidence scoring
    """
    
    def __init__(self, fabric: UnifiedProtocolFabric):
        super().__init__()
        self.fabric = fabric
        self.protocol_steps = []
    
    async def reason_with_protocol(
        self,
        step: str,
        protocol: str,
        tool_name: str,
        **kwargs
    ) -> ReasoningStep:
        """Execute reasoning step using specific protocol."""
        # Record step
        reasoning_step = ReasoningStep(
            description=f"{step} (via {protocol})",
            timestamp=time.time()
        )
        
        try:
            # Execute via protocol
            result = await self.fabric.execute_tool(protocol, tool_name, **kwargs)
            reasoning_step.result = result
            reasoning_step.metadata = {
                'protocol': protocol,
                'tool': tool_name,
                'success': True
            }
        except Exception as e:
            reasoning_step.error = str(e)
            reasoning_step.metadata = {
                'protocol': protocol,
                'tool': tool_name,
                'success': False
            }
        
        self.protocol_steps.append(reasoning_step)
        return reasoning_step
    
    async def gather_multi_protocol_evidence(
        self,
        query: str,
        protocols: List[str]
    ) -> Dict[str, Any]:
        """Gather evidence from multiple protocols in parallel."""
        tasks = []
        
        for protocol in protocols:
            # Determine appropriate tool for protocol
            tool = self._select_tool_for_protocol(protocol, "research")
            if tool:
                tasks.append(
                    self.reason_with_protocol(
                        f"Gathering evidence from {protocol}",
                        protocol,
                        tool,
                        query=query
                    )
                )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        evidence = {}
        for i, result in enumerate(results):
            protocol = protocols[i]
            if isinstance(result, Exception):
                evidence[protocol] = {"error": str(result)}
            else:
                evidence[protocol] = result.result
        
        return evidence
    
    def _select_tool_for_protocol(self, protocol: str, purpose: str) -> Optional[str]:
        """Select appropriate tool based on protocol and purpose."""
        tool_mapping = {
            'mcp': {
                'research': 'web_search',
                'analyze': 'data_analysis',
                'summarize': 'summarizer'
            },
            'a2a': {
                'research': 'expert_consult',
                'analyze': 'expert_analyze',
                'summarize': 'expert_summary'
            },
            'acp': {
                'research': 'workflow_search',
                'analyze': 'workflow_analyze',
                'summarize': 'workflow_report'
            },
            'anp': {
                'research': 'distributed_search',
                'analyze': 'distributed_compute',
                'summarize': 'distributed_aggregate'
            }
        }
        
        return tool_mapping.get(protocol, {}).get(purpose)
    
    def calculate_protocol_confidence(self) -> Dict[str, float]:
        """Calculate confidence score per protocol."""
        confidence = {}
        
        for step in self.protocol_steps:
            protocol = step.metadata.get('protocol', 'unknown')
            success = step.metadata.get('success', False)
            
            if protocol not in confidence:
                confidence[protocol] = []
            
            confidence[protocol].append(1.0 if success else 0.0)
        
        # Average confidence per protocol
        return {
            protocol: sum(scores) / len(scores)
            for protocol, scores in confidence.items()
            if scores
        }


# Telemetry Integration
class ProtocolTelemetry:
    """
    Protocol-aware telemetry collection.
    
    Features:
    - Protocol-specific metrics
    - Cross-protocol tracing
    - Performance comparison
    """
    
    def __init__(self, fabric: UnifiedProtocolFabric):
        self.fabric = fabric
        self.tracer = get_tracer(__name__)
        self.meter = get_meter(__name__)
        
        # Create protocol-specific metrics
        self.protocol_latency = self.meter.create_histogram(
            "protocol.latency",
            description="Protocol execution latency",
            unit="ms"
        )
        
        self.protocol_errors = self.meter.create_counter(
            "protocol.errors",
            description="Protocol execution errors"
        )
        
        self.protocol_calls = self.meter.create_counter(
            "protocol.calls",
            description="Protocol tool calls"
        )
    
    async def trace_protocol_execution(
        self,
        protocol: str,
        tool_name: str,
        **kwargs
    ) -> Any:
        """Execute with protocol telemetry."""
        with self.tracer.start_as_current_span(
            f"protocol.{protocol}.{tool_name}"
        ) as span:
            # Set span attributes
            set_span_attributes(span, {
                "protocol.type": protocol,
                "tool.name": tool_name,
                "tool.args": str(kwargs)
            })
            
            # Record call
            self.protocol_calls.add(
                1,
                {"protocol": protocol, "tool": tool_name}
            )
            
            # Execute with timing
            start_time = time.time()
            try:
                result = await self.fabric.execute_tool(
                    protocol, tool_name, **kwargs
                )
                
                # Record latency
                latency = (time.time() - start_time) * 1000
                self.protocol_latency.record(
                    latency,
                    {"protocol": protocol, "tool": tool_name, "status": "success"}
                )
                
                span.set_attribute("protocol.success", True)
                return result
                
            except Exception as e:
                # Record error
                self.protocol_errors.add(
                    1,
                    {"protocol": protocol, "tool": tool_name, "error": type(e).__name__}
                )
                
                span.set_attribute("protocol.success", False)
                span.record_exception(e)
                raise
    
    def get_protocol_stats(self) -> Dict[str, Any]:
        """Get protocol performance statistics."""
        # This would aggregate metrics from the meter
        # For now, return placeholder
        return {
            "total_calls": "Use metrics backend",
            "average_latency": "Use metrics backend",
            "error_rate": "Use metrics backend"
        }


# Security Integration
class ProtocolSecuritySandbox(ISandbox):
    """
    Security sandbox for protocol operations.
    
    Features:
    - Protocol-level access control
    - Resource isolation per protocol
    - Audit logging
    """
    
    def __init__(
        self,
        fabric: UnifiedProtocolFabric,
        security_context: SecurityContext
    ):
        self.fabric = fabric
        self.context = security_context
        self.allowed_protocols = set()
        self.audit_log = []
    
    def allow_protocol(self, protocol: str):
        """Allow access to a specific protocol."""
        self.allowed_protocols.add(protocol)
    
    async def execute_sandboxed(
        self,
        protocol: str,
        tool_name: str,
        **kwargs
    ) -> Any:
        """Execute protocol tool in sandbox."""
        # Check protocol access
        if protocol not in self.allowed_protocols:
            self._audit("access_denied", protocol, tool_name)
            raise PermissionError(f"Protocol {protocol} not allowed")
        
        # Check specific tool permissions
        if not self._check_tool_permission(protocol, tool_name):
            self._audit("tool_denied", protocol, tool_name)
            raise PermissionError(f"Tool {tool_name} not allowed")
        
        # Execute with resource limits
        try:
            self._audit("execution_start", protocol, tool_name)
            
            # Would apply resource limits here
            result = await asyncio.wait_for(
                self.fabric.execute_tool(protocol, tool_name, **kwargs),
                timeout=self.context.timeout or 30.0
            )
            
            self._audit("execution_success", protocol, tool_name)
            return result
            
        except asyncio.TimeoutError:
            self._audit("execution_timeout", protocol, tool_name)
            raise
        except Exception as e:
            self._audit("execution_error", protocol, tool_name, str(e))
            raise
    
    def _check_tool_permission(self, protocol: str, tool: str) -> bool:
        """Check if tool is allowed based on security context."""
        # Implement fine-grained tool permissions
        if self.context.role == "admin":
            return True
        
        # Define allowed tools per role
        role_permissions = {
            "researcher": {
                "mcp": ["web_search", "summarize"],
                "a2a": ["expert_consult"],
                "acp": ["workflow_search"],
                "anp": ["distributed_search"]
            },
            "analyst": {
                "mcp": ["web_search", "data_analysis"],
                "a2a": ["expert_analyze"],
                "acp": ["workflow_analyze"],
                "anp": ["distributed_compute"]
            }
        }
        
        allowed_tools = role_permissions.get(
            self.context.role, {}
        ).get(protocol, [])
        
        return tool in allowed_tools
    
    def _audit(self, event: str, protocol: str, tool: str, details: str = ""):
        """Record audit event."""
        self.audit_log.append({
            "timestamp": time.time(),
            "event": event,
            "protocol": protocol,
            "tool": tool,
            "user": self.context.user_id,
            "role": self.context.role,
            "details": details
        })
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        return self.audit_log.copy()


# Plugin Integration
@dataclass
class ProtocolPlugin:
    """
    Plugin that can register tools to specific protocols.
    """
    name: str
    version: str
    tools: Dict[str, List[Any]]  # protocol -> tools
    
    def register_to_fabric(self, fabric: UnifiedProtocolFabric):
        """Register plugin tools to appropriate protocols."""
        for protocol, tools in self.tools.items():
            for tool in tools:
                # Register tool to protocol namespace
                fabric.register_native_tool(tool, namespace=protocol)


# Convenience functions for integration
def integrate_streaming(fabric: UnifiedProtocolFabric) -> ProtocolStreamingProvider:
    """Create protocol-aware streaming provider."""
    return ProtocolStreamingProvider(fabric)


def integrate_memory(
    fabric: UnifiedProtocolFabric,
    base_store: MemoryStore
) -> ProtocolAwareMemoryStore:
    """Create protocol-aware memory store."""
    return ProtocolAwareMemoryStore(base_store, fabric)


def integrate_reasoning(fabric: UnifiedProtocolFabric) -> ProtocolAwareReasoningPattern:
    """Create protocol-aware reasoning pattern."""
    return ProtocolAwareReasoningPattern(fabric)


def integrate_telemetry(fabric: UnifiedProtocolFabric) -> ProtocolTelemetry:
    """Create protocol telemetry collector."""
    return ProtocolTelemetry(fabric)


def integrate_security(
    fabric: UnifiedProtocolFabric,
    context: SecurityContext
) -> ProtocolSecuritySandbox:
    """Create protocol security sandbox."""
    return ProtocolSecuritySandbox(fabric, context)
