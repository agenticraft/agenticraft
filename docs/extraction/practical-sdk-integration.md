# Practical SDK Integration: Step-by-Step Implementation

## Quick Start: Installing and Using Official SDKs

### Step 1: Install the SDKs

```bash
# Install official SDKs
pip install a2a-python
pip install mcp
pip install agentconnect

# Install in AgentiCraft
cd /Users/zahere/Desktop/TLV/agenticraft
pip install -e ".[sdk]"  # Add sdk extras to setup.py
```

### Step 2: Create SDK-Based Agent Example

**File: `/agenticraft/examples/sdk_agent.py`**
```python
"""Complete example using all three official SDKs with AgentiCraft."""

import asyncio
from typing import Dict, Any, List

# Official SDKs
from a2a import Agent as A2AAgent, AgentCard, Registry
from mcp import Server, Tool, Resource, Prompt
from agentconnect import AgentConnect, DIDDocument

# AgentiCraft
from agenticraft.agents import Agent

class MultiProtocolAgent:
    """Agent that supports all three protocols using official SDKs."""
    
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        
        # Initialize protocol components
        self.a2a_agent = None
        self.mcp_server = None
        self.anp_agent = None
        
    async def initialize(self):
        """Initialize all protocol endpoints."""
        
        # 1. Initialize A2A Agent
        await self._init_a2a()
        
        # 2. Initialize MCP Server
        await self._init_mcp()
        
        # 3. Initialize ANP Agent
        await self._init_anp()
        
    async def _init_a2a(self):
        """Initialize Google A2A agent."""
        
        # Create agent card
        card = AgentCard(
            name=self.name,
            description=f"Multi-protocol agent: {self.name}",
            capabilities=self.capabilities,
            vendor="AgentiCraft",
            version="1.0.0"
        )
        
        # Create A2A agent
        self.a2a_agent = A2AAgent(card=card)
        
        # Register task handlers
        @self.a2a_agent.on("task")
        async def handle_task(task: Dict[str, Any]) -> Any:
            """Handle incoming A2A tasks."""
            task_type = task.get("type", "general")
            
            if task_type == "weather":
                return await self.get_weather(task.get("city", "New York"))
            elif task_type == "analysis":
                return await self.analyze_data(task.get("data", {}))
            else:
                return {"error": "Unknown task type"}
                
        # Start A2A agent
        await self.a2a_agent.start(port=8001)
        
    async def _init_mcp(self):
        """Initialize MCP server with all primitives."""
        
        # Create MCP server
        self.mcp_server = Server(
            name=f"{self.name}_mcp",
            version="1.0.0"
        )
        
        # Register tools
        @self.mcp_server.tool()
        async def get_weather(city: str = "New York") -> Dict[str, Any]:
            """Get weather for a city."""
            return {
                "city": city,
                "temperature": 72,
                "conditions": "Sunny",
                "humidity": 45
            }
            
        @self.mcp_server.tool()
        async def analyze_sentiment(text: str) -> Dict[str, Any]:
            """Analyze sentiment of text."""
            # Simplified sentiment analysis
            positive_words = ["good", "great", "excellent", "happy"]
            negative_words = ["bad", "terrible", "sad", "angry"]
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
                
            return {
                "text": text,
                "sentiment": sentiment,
                "confidence": 0.85
            }
            
        # Register resources
        @self.mcp_server.resource("weather://current/*")
        async def current_weather_resource(uri: str) -> Dict[str, Any]:
            """Provide current weather data as resource."""
            city = uri.split("/")[-1]
            return {
                "type": "weather.current",
                "city": city,
                "data": await get_weather(city)
            }
            
        # Register prompts
        @self.mcp_server.prompt("weather_report")
        async def weather_report_prompt(city: str, unit: str = "F") -> str:
            """Generate weather report prompt."""
            weather = await get_weather(city)
            return f"""
            Weather Report for {city}:
            Temperature: {weather['temperature']}°{unit}
            Conditions: {weather['conditions']}
            Humidity: {weather['humidity']}%
            """
            
        # Start MCP server
        await self.mcp_server.start(port=3001)
        
    async def _init_anp(self):
        """Initialize ANP agent with DID."""
        
        # Create DID document
        did_doc = DIDDocument(
            id=f"did:anp:{self.name}",
            authentication=[{
                "id": f"did:anp:{self.name}#keys-1",
                "type": "Ed25519VerificationKey2020",
                "controller": f"did:anp:{self.name}"
            }],
            service=[{
                "id": f"did:anp:{self.name}#agent-service",
                "type": "AgentService",
                "serviceEndpoint": {
                    "a2a": f"http://localhost:8001",
                    "mcp": f"http://localhost:3001"
                },
                "capabilities": self.capabilities
            }]
        )
        
        # Connect to ANP network
        self.anp_agent = AgentConnect()
        await self.anp_agent.register(did_doc)
        
        # Set up discovery responses
        @self.anp_agent.on("discovery")
        async def handle_discovery(query: Dict[str, Any]) -> Dict[str, Any]:
            """Handle ANP discovery requests."""
            return {
                "did": did_doc.id,
                "name": self.name,
                "capabilities": self.capabilities,
                "endpoints": {
                    "a2a": f"http://localhost:8001",
                    "mcp": f"http://localhost:3001"
                }
            }
            
    # Business logic methods
    async def get_weather(self, city: str) -> Dict[str, Any]:
        """Get weather data (shared across protocols)."""
        # In real implementation, this would call a weather API
        weather_data = {
            "New York": {"temp": 72, "conditions": "Sunny", "humidity": 45},
            "London": {"temp": 59, "conditions": "Cloudy", "humidity": 78},
            "Tokyo": {"temp": 68, "conditions": "Clear", "humidity": 62}
        }
        
        data = weather_data.get(city, {"temp": 70, "conditions": "Unknown", "humidity": 50})
        return {
            "city": city,
            "temperature": data["temp"],
            "conditions": data["conditions"],
            "humidity": data["humidity"],
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
    async def analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze provided data."""
        return {
            "input": data,
            "analysis": {
                "data_points": len(data),
                "summary": "Analysis complete",
                "insights": ["Pattern detected", "Anomaly found"]
            }
        }

class AgentiCraftSDKWrapper:
    """Wrapper to integrate SDK agents with AgentiCraft."""
    
    def __init__(self):
        self.agents: Dict[str, MultiProtocolAgent] = {}
        self.fabric_registry = {}
        
    async def create_agent(self, 
                          agenticraft_agent: Agent) -> MultiProtocolAgent:
        """Create multi-protocol agent from AgentiCraft agent."""
        
        # Extract capabilities
        capabilities = []
        if hasattr(agenticraft_agent, 'tools'):
            capabilities.extend([f"tool:{name}" for name in agenticraft_agent.tools])
        if hasattr(agenticraft_agent, 'capabilities'):
            capabilities.extend(agenticraft_agent.capabilities)
            
        # Create multi-protocol agent
        mp_agent = MultiProtocolAgent(
            name=agenticraft_agent.name,
            capabilities=capabilities
        )
        
        # Override methods to use AgentiCraft logic
        if hasattr(agenticraft_agent, 'execute'):
            mp_agent.analyze_data = agenticraft_agent.execute
            
        # Initialize all protocols
        await mp_agent.initialize()
        
        # Store reference
        self.agents[agenticraft_agent.name] = mp_agent
        
        return mp_agent
        
    async def discover_agents(self, capability: str) -> List[Dict[str, Any]]:
        """Discover agents across all protocols."""
        discovered = []
        
        # A2A discovery
        a2a_registry = Registry()
        a2a_agents = await a2a_registry.search(capability=capability)
        for agent in a2a_agents:
            discovered.append({
                "protocol": "a2a",
                "name": agent.card.name,
                "endpoint": agent.endpoint,
                "capabilities": agent.card.capabilities
            })
            
        # ANP discovery
        anp = AgentConnect()
        anp_agents = await anp.discover(capability=capability)
        for agent in anp_agents:
            discovered.append({
                "protocol": "anp",
                "did": agent.did,
                "name": agent.name,
                "endpoints": agent.endpoints,
                "capabilities": agent.capabilities
            })
            
        return discovered

# Example usage
async def main():
    """Demonstrate SDK integration."""
    
    print("=== AgentiCraft SDK Integration Demo ===\n")
    
    # Create wrapper
    wrapper = AgentiCraftSDKWrapper()
    
    # Create a traditional AgentiCraft agent
    from agenticraft.agents import Agent
    
    weather_agent = Agent(
        name="weather_service",
        instructions="Provide weather information and analysis"
    )
    
    # Add some tools
    async def get_forecast(days: int = 7) -> List[Dict]:
        return [{"day": i, "temp": 70 + i} for i in range(days)]
        
    weather_agent.tools = {"get_forecast": get_forecast}
    weather_agent.capabilities = ["weather", "forecast", "analysis"]
    
    # Convert to multi-protocol agent
    mp_agent = await wrapper.create_agent(weather_agent)
    
    print(f"✅ Agent '{weather_agent.name}' registered on all protocols:")
    print(f"   - A2A: http://localhost:8001")
    print(f"   - MCP: http://localhost:3001")
    print(f"   - ANP: did:anp:{weather_agent.name}")
    
    # Test A2A execution
    print("\n📡 Testing A2A Protocol:")
    # In real scenario, this would come from external A2A client
    a2a_task = {
        "type": "weather",
        "city": "New York"
    }
    result = await mp_agent.a2a_agent.handle_task(a2a_task)
    print(f"   Result: {result}")
    
    # Test MCP tool execution
    print("\n🔧 Testing MCP Protocol:")
    tools = mp_agent.mcp_server.list_tools()
    print(f"   Available tools: {[t.name for t in tools]}")
    weather_tool = next(t for t in tools if t.name == "get_weather")
    result = await weather_tool.call(city="London")
    print(f"   Result: {result}")
    
    # Test ANP discovery
    print("\n🔍 Testing ANP Discovery:")
    discovered = await wrapper.discover_agents("weather")
    print(f"   Found {len(discovered)} agents with 'weather' capability")
    
    print("\n✨ SDK Integration Complete!")

if __name__ == "__main__":
    # Run example
    asyncio.run(main())
```

### Step 3: Production Integration Pattern

**File: `/agenticraft/fabric/sdk_production.py`**
```python
"""Production-ready SDK integration for AgentiCraft."""

import asyncio
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import SDKs with error handling
try:
    from a2a import Agent as A2AAgent, Client as A2AClient
    HAS_A2A = True
except ImportError:
    logger.warning("a2a-python not installed")
    HAS_A2A = False

try:
    from mcp import Server as MCPServer, Client as MCPClient
    HAS_MCP = True
except ImportError:
    logger.warning("mcp not installed")
    HAS_MCP = False

try:
    from agentconnect import AgentConnect
    HAS_ANP = True
except ImportError:
    logger.warning("agentconnect not installed")
    HAS_ANP = False

class ProductionSDKFabric:
    """Production-ready protocol fabric using official SDKs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.protocols = {}
        
        # Health tracking
        self.protocol_health = {
            'a2a': {'available': HAS_A2A, 'healthy': False},
            'mcp': {'available': HAS_MCP, 'healthy': False},
            'anp': {'available': HAS_ANP, 'healthy': False}
        }
        
    async def initialize(self):
        """Initialize available protocols with error handling."""
        
        # Initialize A2A if available
        if HAS_A2A:
            try:
                self.protocols['a2a'] = {
                    'client': A2AClient(),
                    'agents': {}
                }
                await self.protocols['a2a']['client'].connect()
                self.protocol_health['a2a']['healthy'] = True
                logger.info("✅ A2A protocol initialized")
            except Exception as e:
                logger.error(f"❌ A2A initialization failed: {e}")
                
        # Initialize MCP if available
        if HAS_MCP:
            try:
                self.protocols['mcp'] = {
                    'servers': {},
                    'client': MCPClient()
                }
                self.protocol_health['mcp']['healthy'] = True
                logger.info("✅ MCP protocol initialized")
            except Exception as e:
                logger.error(f"❌ MCP initialization failed: {e}")
                
        # Initialize ANP if available
        if HAS_ANP:
            try:
                self.protocols['anp'] = AgentConnect()
                await self.protocols['anp'].connect()
                self.protocol_health['anp']['healthy'] = True
                logger.info("✅ ANP protocol initialized")
            except Exception as e:
                logger.error(f"❌ ANP initialization failed: {e}")
                
    def get_available_protocols(self) -> List[str]:
        """Get list of available and healthy protocols."""
        return [
            protocol 
            for protocol, health in self.protocol_health.items()
            if health['available'] and health['healthy']
        ]
        
    async def execute_with_fallback(self,
                                  task: str,
                                  preferred_protocol: str = "a2a",
                                  **kwargs) -> Any:
        """Execute with automatic fallback to available protocols."""
        
        # Try preferred protocol first
        if preferred_protocol in self.get_available_protocols():
            try:
                return await self._execute_on_protocol(
                    task, preferred_protocol, **kwargs
                )
            except Exception as e:
                logger.warning(f"Preferred protocol {preferred_protocol} failed: {e}")
                
        # Fallback to other protocols
        for protocol in self.get_available_protocols():
            if protocol != preferred_protocol:
                try:
                    logger.info(f"Falling back to {protocol}")
                    return await self._execute_on_protocol(
                        task, protocol, **kwargs
                    )
                except Exception as e:
                    logger.warning(f"Fallback protocol {protocol} failed: {e}")
                    
        raise RuntimeError("All protocols failed")
        
    async def _execute_on_protocol(self, task: str, protocol: str, **kwargs) -> Any:
        """Execute task on specific protocol."""
        
        if protocol == "a2a" and 'a2a' in self.protocols:
            return await self._execute_a2a(task, **kwargs)
        elif protocol == "mcp" and 'mcp' in self.protocols:
            return await self._execute_mcp(task, **kwargs)
        elif protocol == "anp" and 'anp' in self.protocols:
            return await self._execute_anp(task, **kwargs)
        else:
            raise ValueError(f"Protocol {protocol} not available")

# Usage example
async def production_example():
    """Example of production SDK usage."""
    
    fabric = ProductionSDKFabric()
    await fabric.initialize()
    
    print(f"Available protocols: {fabric.get_available_protocols()}")
    
    # Execute with automatic fallback
    try:
        result = await fabric.execute_with_fallback(
            task="Get weather for NYC",
            preferred_protocol="a2a",
            city="New York"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(production_example())
```

## Key Recommendations

### 1. **Use Official SDKs**
- They ensure compatibility with the broader ecosystem
- Automatic updates when protocols evolve
- Better documentation and community support

### 2. **Keep AgentiCraft's Innovations**
- Mesh networking and consensus can be built on top of SDKs
- Use SDKs for protocol compliance, AgentiCraft for agent intelligence

### 3. **Gradual Migration**
- Start with new agents using SDKs
- Migrate existing agents incrementally
- Maintain backward compatibility during transition

### 4. **Focus on Agent Capabilities**
- Let SDKs handle protocol complexity
- Focus AgentiCraft development on agent intelligence
- Build unique features on top of standard protocols

This approach gives you the best of both worlds: full ecosystem compatibility with the freedom to innovate on agent capabilities.