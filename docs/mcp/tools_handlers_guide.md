# Tool Wrappers, Handlers, and MCP Integration in AgentiCraft

## Overview

AgentiCraft provides multiple approaches for integrating tools into workflows:

1. **Direct Handlers** - Embed tool logic directly in workflow step handlers
2. **Tool Wrappers** - Wrap functions to make them workflow-compatible
3. **MCP Integration** - Expose and consume tools via Model Context Protocol

## Approach 1: Direct Handlers (workflow_with_handlers.py)

This approach embeds tool functionality directly in workflow steps, avoiding decorator issues.

### Example: Weather Analysis with Inline Handlers

```python
from agenticraft.agents import WorkflowAgent, Workflow

async def weather_workflow_with_handlers():
    agent = WorkflowAgent(
        name="WeatherAnalyzer",
        instructions="Analyze weather data step by step"
    )
    
    workflow = agent.create_workflow(
        name="weather_analysis",
        description="Analyze weather using integrated tool logic"
    )
    
    # Step 1: Fetch weather data (tool logic inline)
    def fetch_weather_data(agent, step, context):
        """Fetch weather for multiple cities."""
        cities = context.get("target_cities", ["New York", "London"])
        weather_db = {
            "New York": {"temp": 72, "humidity": 65, "conditions": "Partly cloudy"},
            "London": {"temp": 59, "humidity": 80, "conditions": "Rainy"}
        }
        
        fetched_data = []
        for city in cities:
            if city in weather_db:
                data = weather_db[city].copy()
                data["city"] = city
                fetched_data.append(data)
        
        context["weather_data"] = fetched_data
        return f"Fetched weather for {len(fetched_data)} cities"
    
    # Step 2: Analyze the data
    def analyze_weather(agent, step, context):
        """Analyze weather patterns."""
        weather_data = context.get("weather_data", [])
        
        temps = [d["temp"] for d in weather_data]
        avg_temp = sum(temps) / len(temps) if temps else 0
        
        analysis = {
            "avg_temperature": round(avg_temp, 1),
            "cities_analyzed": len(weather_data)
        }
        
        context["analysis"] = analysis
        return f"Average temperature: {analysis['avg_temperature']}°F"
    
    # Register handlers
    agent.register_handler("fetch", fetch_weather_data)
    agent.register_handler("analyze", analyze_weather)
    
    # Define workflow steps
    workflow.add_step(
        name="fetch_data",
        handler="fetch",
        action="Fetching weather data..."
    )
    
    workflow.add_step(
        name="analyze_data",
        handler="analyze",
        action="Analyzing weather patterns...",
        depends_on=["fetch_data"]
    )
    
    # Execute
    context = {"target_cities": ["New York", "London", "Tokyo"]}
    result = await agent.execute_workflow(workflow, context=context)
    return result
```

### Benefits of Direct Handlers:
- No decorator issues
- Full control over data flow
- Complex logic without framework limitations
- Direct access to workflow context

## Approach 2: Tool Wrappers (workflow_with_wrappers.py)

This approach creates a wrapper class to make regular functions workflow-compatible.

### The ToolWrapper Class

```python
class ToolWrapper:
    """Wrapper to make tools work with workflows."""
    
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
        self._results = {}
    
    async def execute(self, *args, **kwargs):
        """Execute the wrapped function."""
        try:
            result = self.func(*args, **kwargs)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def create_step_handler(self, step_name: str):
        """Create a handler for workflow steps."""
        async def handler(agent, step, context):
            # Get parameters from context
            params = context.get(f"{step_name}_params", {})
            result = await self.execute(**params)
            
            # Store result in context
            context[f"{step_name}_result"] = result
            
            return json.dumps(result) if isinstance(result, dict) else str(result)
        
        return handler
```

### Using Tool Wrappers in Workflows

```python
# Define regular Python functions
def fetch_weather_data(city: str) -> Dict[str, Any]:
    """Fetch weather data for a city."""
    weather_db = {
        "New York": {"temp": 72, "humidity": 65},
        "London": {"temp": 59, "humidity": 80}
    }
    return weather_db.get(city, {"temp": 70, "humidity": 60})

def analyze_weather_list(cities_data: list) -> Dict[str, Any]:
    """Analyze weather data from multiple cities."""
    temps = [d["temperature"] for d in cities_data]
    return {
        "avg_temperature": sum(temps) / len(temps),
        "city_count": len(cities_data)
    }

# Create workflow with wrappers
async def weather_workflow_with_wrappers():
    # Create tool wrappers
    weather_tool = ToolWrapper("fetch_weather", "Fetch weather data", fetch_weather_data)
    analyze_tool = ToolWrapper("analyze_weather", "Analyze weather", analyze_weather_list)
    
    # Create workflow agent
    agent = WorkflowAgent(name="WeatherBot")
    
    # Register handlers from wrappers
    agent.register_handler("fetch_nyc", weather_tool.create_step_handler("fetch_nyc"))
    agent.register_handler("analyze_data", analyze_tool.create_step_handler("analyze_data"))
    
    # Create workflow
    workflow = agent.create_workflow("weather_analysis")
    
    # Define context with parameters
    context = {
        "fetch_nyc_params": {"city": "New York"},
        "cities_data": []
    }
    
    # Add steps
    workflow.add_step(
        name="fetch_nyc",
        handler="fetch_nyc",
        action="Fetching NYC weather..."
    )
    
    workflow.add_step(
        name="analyze_data",
        handler="analyze_data",
        action="Analyzing weather data...",
        depends_on=["fetch_nyc"]
    )
    
    # Execute
    result = await agent.execute_workflow(workflow, context=context)
    return result
```

## Approach 3: MCP Integration

MCP provides a standardized way to expose and consume tools across systems.

### Creating MCP Tools for Workflows

```python
from agenticraft.protocols.mcp import MCPServer, MCPClient, mcp_tool

# Define MCP tools
@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "temperature": {"type": "number"},
            "humidity": {"type": "number"},
            "city": {"type": "string"}
        }
    }
)
async def fetch_weather_mcp(city: str) -> Dict[str, Any]:
    """Fetch weather data via MCP."""
    # Could call external API here
    await asyncio.sleep(0.1)  # Simulate API call
    return {
        "city": city,
        "temperature": 72,
        "humidity": 65
    }

# Create MCP server
server = MCPServer(name="Weather Service")
server.register_tool(fetch_weather_mcp)

# Start server
await server.start_websocket_server("localhost", 3000)
```

### Using MCP Tools in Workflows

```python
async def workflow_with_mcp_tools():
    # Connect to MCP server
    async with MCPClient("ws://localhost:3000") as mcp:
        # Create agent with MCP tools
        agent = WorkflowAgent(
            name="MCPWeatherBot",
            tools=mcp.get_tools()  # Get tools from MCP
        )
        
        # Create workflow that uses MCP tools
        workflow = agent.create_workflow("mcp_weather_analysis")
        
        # MCP tools can be used in step actions
        workflow.add_step(
            name="fetch_weather",
            action="Use fetch_weather_mcp tool to get weather for New York"
        )
        
        workflow.add_step(
            name="analyze",
            action="Analyze the fetched weather data",
            depends_on=["fetch_weather"]