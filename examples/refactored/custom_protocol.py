"""
Custom Protocol Example - Refactored Architecture

This example demonstrates creating a custom protocol and integrating
it with the AgentiCraft fabric using the new architecture.
"""
import asyncio
import logging
from typing import Any, Optional, Dict
from dataclasses import dataclass

from agenticraft.protocols.base import Protocol, ProtocolConfig
from agenticraft.core.transport import Transport, Message, MessageType
from agenticraft.fabric import AgentBuilder
from agenticraft.fabric.adapters import ProtocolAdapter, register_adapter

# Enable logging
logging.basicConfig(level=logging.INFO)


# Custom protocol implementation
class EchoProtocol(Protocol):
    """Simple echo protocol for demonstration."""
    
    def __init__(self, echo_prefix: str = "ECHO:", **kwargs):
        config = ProtocolConfig(
            name="echo",
            version="1.0",
            metadata={"prefix": echo_prefix}
        )
        super().__init__(config, **kwargs)
        self.echo_prefix = echo_prefix
        self._echo_count = 0
        
    async def start(self) -> None:
        """Start the echo protocol."""
        if self._running:
            return
            
        if self.transport:
            await self.transport.connect()
            self.transport.on_message(self._handle_message)
            
        self._running = True
        logging.info("Echo protocol started")
        
    async def stop(self) -> None:
        """Stop the echo protocol."""
        if not self._running:
            return
            
        if self.transport:
            await self.transport.disconnect()
            
        self._running = False
        logging.info("Echo protocol stopped")
        
    async def send(
        self,
        message: Any,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Send a message and get echo response."""
        self._echo_count += 1
        
        # Create echo response
        echo_response = {
            "original": message,
            "echo": f"{self.echo_prefix} {message}",
            "count": self._echo_count,
            "target": target
        }
        
        # If we have transport, send through it
        if self.transport:
            msg = Message(
                id=str(self._echo_count),
                type=MessageType.REQUEST,
                payload=echo_response
            )
            
            response = await self.transport.send(msg)
            if response:
                return response.payload
                
        return echo_response
        
    async def receive(self, timeout: Optional[float] = None) -> Any:
        """Receive a message."""
        if self.transport:
            msg = await self.transport.receive()
            return msg.payload
        return None
        
    async def _handle_message(self, message: Message) -> None:
        """Handle incoming message."""
        # Echo it back with modifications
        echo_payload = {
            "received": message.payload,
            "echoed_at": asyncio.get_event_loop().time(),
            "echo_count": self._echo_count
        }
        
        response = Message(
            id=message.id,
            type=MessageType.RESPONSE,
            payload=echo_payload
        )
        
        await self.transport.send(response)


# Custom adapter for the echo protocol
class EchoAdapter(ProtocolAdapter):
    """Adapter for echo protocol."""
    
    async def _initialize_protocol(self, config: Dict[str, Any]) -> None:
        """Initialize echo protocol."""
        # Custom initialization
        prefix = config.get("echo_prefix", "ECHO:")
        if hasattr(self.protocol, 'echo_prefix'):
            self.protocol.echo_prefix = prefix
            
        await self.protocol.start()
        
    async def send_message(
        self,
        message: Any,
        target: Optional[str] = None
    ) -> Any:
        """Send message via echo protocol."""
        return await self.protocol.send(message, target)
        
    async def receive_message(self) -> Any:
        """Receive message from echo protocol."""
        return await self.protocol.receive()
        
    def get_protocol_name(self) -> str:
        """Get protocol name."""
        return "echo"
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Get echo protocol capabilities."""
        return {
            "echo": True,
            "prefix": self.protocol.echo_prefix,
            "count": self.protocol._echo_count
        }
        
    # Echo-specific methods
    async def echo_with_delay(self, message: str, delay: float) -> str:
        """Echo with delay."""
        await asyncio.sleep(delay)
        return await self.protocol.send(message)
        
    def get_echo_stats(self) -> Dict[str, int]:
        """Get echo statistics."""
        return {
            "total_echoes": self.protocol._echo_count,
            "prefix_length": len(self.protocol.echo_prefix)
        }


async def main():
    """Demonstrate custom protocol integration."""
    
    # Register custom adapter
    register_adapter("echo", EchoAdapter)
    
    # Create agent with custom protocol using builder
    agent = await (AgentBuilder("custom-agent")
        # Add standard MCP protocol
        .with_mcp("http://localhost:8080")
        # Add custom echo protocol
        .with_custom_protocol(
            protocol_id="echo",
            protocol=EchoProtocol(echo_prefix="CUSTOM_ECHO:"),
            transport=None  # No transport for this example
        )
        # Build and start
        .build_and_start())
    
    try:
        print(f"Agent with custom protocol started")
        print(f"Available protocols: {agent.list_protocols()}")
        
        # Use echo protocol
        print("\nTesting echo protocol:")
        
        # Simple echo
        result = await agent.send(
            "Hello, custom protocol!",
            protocol="echo"
        )
        print(f"Echo result: {result}")
        
        # Echo with metadata
        result = await agent.send(
            {"message": "Complex object", "timestamp": asyncio.get_event_loop().time()},
            protocol="echo"
        )
        print(f"Complex echo: {result}")
        
        # Get echo adapter for advanced features
        echo_adapter = agent.get_protocol("echo")
        if hasattr(echo_adapter, 'get_echo_stats'):
            stats = echo_adapter.get_echo_stats()
            print(f"\nEcho statistics: {stats}")
        
        # Use both protocols together
        print("\nCombining protocols:")
        
        # Get data from MCP
        mcp_data = await agent.call(
            method="tools/list",
            protocol="mcp"
        )
        
        # Echo the MCP data
        echoed_data = await agent.send(
            mcp_data,
            protocol="echo"
        )
        print(f"Echoed MCP data: {echoed_data}")
        
        # Health check shows both protocols
        health = await agent.health_check()
        print(f"\nHealth check:")
        for proto, status in health["protocols"].items():
            print(f"- {proto}: {status}")
            
    finally:
        await agent.stop()
        print("\nCustom protocol agent stopped")


# Advanced: Protocol composition
class CompositeProtocol(Protocol):
    """Protocol that combines multiple sub-protocols."""
    
    def __init__(self, protocols: Dict[str, Protocol], **kwargs):
        config = ProtocolConfig(name="composite", version="1.0")
        super().__init__(config, **kwargs)
        self.protocols = protocols
        
    async def start(self) -> None:
        """Start all sub-protocols."""
        for proto in self.protocols.values():
            await proto.start()
        self._running = True
        
    async def stop(self) -> None:
        """Stop all sub-protocols."""
        for proto in self.protocols.values():
            await proto.stop()
        self._running = False
        
    async def send(
        self,
        message: Any,
        target: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Route message to appropriate sub-protocol."""
        # Route based on message type
        if isinstance(message, dict) and "protocol" in message:
            proto_name = message["protocol"]
            if proto_name in self.protocols:
                return await self.protocols[proto_name].send(
                    message.get("payload", message),
                    target,
                    timeout
                )
                
        # Default: broadcast to all protocols
        results = {}
        for name, proto in self.protocols.items():
            results[name] = await proto.send(message, target, timeout)
        return results
        
    async def receive(self, timeout: Optional[float] = None) -> Any:
        """Receive from any sub-protocol."""
        # Simple implementation: return first message
        for proto in self.protocols.values():
            try:
                return await asyncio.wait_for(proto.receive(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
        return None


if __name__ == "__main__":
    asyncio.run(main())
