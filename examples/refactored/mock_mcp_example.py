"""
Mock MCP Agent Example

This example demonstrates MCP agent functionality using a mock transport
that doesn't require a real server connection.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from agenticraft.fabric import UnifiedAgent
from agenticraft.protocols.mcp import MCPProtocol, MCPTool, MCPToolParameter
from agenticraft.core.transport import Transport, TransportConfig, Message, MessageType
from agenticraft.core.auth import AuthConfig

# Enable logging
logging.basicConfig(level=logging.INFO)


class MockTransport(Transport):
    """Mock transport for testing without a real server."""
    
    def __init__(self, config: TransportConfig):
        super().__init__(config)
        self._mock_tools = self._create_mock_tools()
        
    def _create_mock_tools(self):
        """Create some mock tools."""
        return [
            MCPTool(
                name="calculator",
                description="Simple calculator for basic math operations",
                parameters=[
                    MCPToolParameter(
                        name="operation",
                        type="string",
                        description="Math operation: add, subtract, multiply, divide",
                        enum=["add", "subtract", "multiply", "divide"]
                    ),
                    MCPToolParameter(
                        name="a",
                        type="number",
                        description="First number"
                    ),
                    MCPToolParameter(
                        name="b", 
                        type="number",
                        description="Second number"
                    )
                ]
            ),
            MCPTool(
                name="weather",
                description="Get weather information",
                parameters=[
                    MCPToolParameter(
                        name="city",
                        type="string",
                        description="City name"
                    )
                ]
            )
        ]
        
    async def connect(self) -> None:
        """Mock connection."""
        self._connected = True
        logging.info("Mock transport connected")
        
    async def disconnect(self) -> None:
        """Mock disconnection."""
        self._connected = False
        logging.info("Mock transport disconnected")
        
    async def send(self, message: Message) -> Optional[Message]:
        """Mock send that returns appropriate responses."""
        if not self._connected:
            raise ConnectionError("Not connected")
            
        # Parse the payload to determine response
        payload = message.payload
        method = payload.get("method", "")
        
        # Mock responses based on method
        if method == "initialize":
            result = {
                "protocolVersion": "1.0",
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                },
                "serverInfo": {
                    "name": "Mock MCP Server",
                    "version": "1.0.0"
                }
            }
        elif method == "tools/list":
            result = {
                "tools": [tool.to_json_schema() for tool in self._mock_tools]
            }
        elif method == "tools/call":
            result = self._handle_tool_call(payload.get("params", {}))
        else:
            result = {"error": f"Unknown method: {method}"}
            
        # Return mock response
        return Message(
            id=message.id,
            type=MessageType.RESPONSE,
            payload={
                "jsonrpc": "2.0",
                "id": message.id,
                "result": result
            }
        )
        
    def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mock tool calls."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if tool_name == "calculator":
            operation = arguments.get("operation")
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            
            result = None
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                result = a / b if b != 0 else "Error: Division by zero"
                
            return {
                "content": [{
                    "type": "text",
                    "text": f"Result: {result}"
                }]
            }
        elif tool_name == "weather":
            city = arguments.get("city", "Unknown")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Weather in {city}: Sunny, 72°F (mock data)"
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Unknown tool: {tool_name}"
                }]
            }
            
    async def receive(self) -> Message:
        """Mock receive (not used in this example)."""
        raise NotImplementedError("Mock transport doesn't support receive")


async def main():
    """Demonstrate MCP agent with mock transport."""
    
    # Create mock transport
    transport = MockTransport(TransportConfig(url="mock://localhost"))
    
    # Create MCP protocol
    protocol = MCPProtocol(transport=transport)
    
    # Create agent
    agent = UnifiedAgent(name="mock-example-agent")
    agent.add_protocol("mcp", protocol, transport, primary=True)
    
    try:
        # Start the agent
        await agent.start()
        print(f"\\nAgent '{agent.name}' started with mock transport")
        
        # Initialize the protocol
        init_result = await agent.call(
            method="initialize",
            params={}
        )
        print(f"\\nProtocol initialized: {init_result}")
        
        # List available tools
        tools_result = await agent.call(
            method="tools/list",
            params={}
        )
        print(f"\\nAvailable tools:")
        for tool in tools_result.get("tools", []):
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Test calculator tool
        print("\\n--- Testing Calculator Tool ---")
        
        # Addition
        result = await agent.call(
            method="tools/call",
            params={
                "name": "calculator",
                "arguments": {
                    "operation": "add",
                    "a": 5,
                    "b": 3
                }
            }
        )
        print(f"5 + 3 = {result['content'][0]['text']}")
        
        # Multiplication  
        result = await agent.call(
            method="tools/call",
            params={
                "name": "calculator",
                "arguments": {
                    "operation": "multiply",
                    "a": 7,
                    "b": 6
                }
            }
        )
        print(f"7 × 6 = {result['content'][0]['text']}")
        
        # Division
        result = await agent.call(
            method="tools/call",
            params={
                "name": "calculator",
                "arguments": {
                    "operation": "divide",
                    "a": 20,
                    "b": 4
                }
            }
        )
        print(f"20 ÷ 4 = {result['content'][0]['text']}")
        
        # Test weather tool
        print("\\n--- Testing Weather Tool ---")
        result = await agent.call(
            method="tools/call",
            params={
                "name": "weather",
                "arguments": {
                    "city": "San Francisco"
                }
            }
        )
        print(f"Weather check: {result['content'][0]['text']}")
        
        # Check agent health
        health = await agent.health_check()
        print(f"\\nAgent health: {health}")
        
    finally:
        await agent.stop()
        print(f"\\nAgent '{agent.name}' stopped")


if __name__ == "__main__":
    asyncio.run(main())
