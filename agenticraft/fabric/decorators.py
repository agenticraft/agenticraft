"""
Fast-Agent Style Decorators for AgentiCraft.

This module provides decorator-based agent creation with natural tool access,
inspired by Google's ADK and modern Python patterns.
"""

import asyncio
import functools
import inspect
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, Tuple

import yaml

from agenticraft import Agent, ReasoningAgent, WorkflowAgent
from agenticraft.core import BaseTool, Workflow
from agenticraft.core.config import settings
from agenticraft.fabric.legacy import (
    UnifiedProtocolFabric,
    get_global_fabric,
    initialize_fabric
)

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for decorator-based agents."""
    name: str
    servers: List[str] = None
    tools: List[str] = None
    model: str = None
    provider: str = None
    reasoning_pattern: str = None
    temperature: float = None
    max_tokens: int = None
    sandbox_enabled: bool = False
    memory_enabled: bool = False
    metadata: Dict[str, Any] = None


class ToolProxy:
    """Proxy object for natural tool access (self.tools.tool_name)."""
    
    def __init__(self, agent: Agent, fabric: UnifiedProtocolFabric):
        self._agent = agent
        self._fabric = fabric
        self._tool_cache = {}
    
    def __getattr__(self, name: str) -> Callable:
        """Get tool by name with dot notation."""
        if name in self._tool_cache:
            return self._tool_cache[name]
        
        # Try to find tool in fabric
        tools = self._fabric.get_tools()
        for tool in tools:
            # Match by full name first
            if tool.name == name:
                # Create async wrapper
                async def tool_wrapper(**kwargs):
                    return await self._fabric.execute_tool(tool.name, **kwargs)
                
                self._tool_cache[name] = tool_wrapper
                return tool_wrapper
            
            # Match by name after colon
            if ":" in tool.name:
                after_colon = tool.name.split(":")[-1]
                if after_colon == name:
                    # Create async wrapper
                    async def tool_wrapper(**kwargs):
                        return await self._fabric.execute_tool(tool.name, **kwargs)
                    
                    self._tool_cache[name] = tool_wrapper
                    return tool_wrapper
                
                # Match by final part after dots
                if "." in after_colon:
                    final_part = after_colon.split(".")[-1]
                    if final_part == name:
                        # Create async wrapper
                        async def tool_wrapper(**kwargs):
                            return await self._fabric.execute_tool(tool.name, **kwargs)
                        
                        self._tool_cache[name] = tool_wrapper
                        return tool_wrapper
        
        raise AttributeError(f"Tool '{name}' not found")
    
    def __dir__(self) -> List[str]:
        """List available tools for autocomplete."""
        tools = self._fabric.get_tools()
        names = []
        for tool in tools:
            # Add full name
            names.append(tool.name)
            
            # Extract simple name after colon
            if ":" in tool.name:
                after_colon = tool.name.split(":")[-1]
                if after_colon != tool.name:
                    names.append(after_colon)
                
                # Also extract the final part after any dots
                if "." in after_colon:
                    final_part = after_colon.split(".")[-1]
                    if final_part not in names:
                        names.append(final_part)
            
        return names


class DecoratedAgent:
    """Wrapper for decorated agent functions."""
    
    def __init__(
        self,
        func: Callable,
        config: AgentConfig,
        agent_class: Type[Agent] = Agent
    ):
        self.func = func
        self.config = config
        self.agent_class = agent_class
        self._agent: Optional[Agent] = None
        self._fabric: Optional[UnifiedProtocolFabric] = None
        self._initialized = False
        
        # Preserve function metadata
        functools.update_wrapper(self, func)
        
        # Auto-register if name is provided
        if config.name:
            register_agent(self)
    
    async def _initialize(self):
        """Initialize the agent and fabric."""
        if self._initialized:
            return
        
        # Get or initialize fabric
        self._fabric = get_global_fabric()
        
        # Configure fabric with servers
        if self.config.servers:
            fabric_config = {}
            
            for server in self.config.servers:
                # Parse server URLs to determine protocol
                if "mcp" in server or server.startswith(("http://", "https://", "ws://")):
                    if "mcp" not in fabric_config:
                        fabric_config["mcp"] = {"servers": []}
                    fabric_config["mcp"]["servers"].append({"url": server})
                elif "a2a" in server:
                    if "a2a" not in fabric_config:
                        fabric_config["a2a"] = {}
                    fabric_config["a2a"]["url"] = server
                elif "acp" in server:
                    if "acp" not in fabric_config:
                        fabric_config["acp"] = {}
                    fabric_config["acp"]["url"] = server
                elif "did:anp" in server:
                    if "anp" not in fabric_config:
                        fabric_config["anp"] = {"did_method": "web"}
            
            await self._fabric.initialize(fabric_config)
        
        # Create agent with fabric tools
        agent_kwargs = {
            "name": self.config.name,
            "model": self.config.model or settings.default_model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "sandbox_enabled": self.config.sandbox_enabled,
        }
        
        # Add provider if specified
        if self.config.provider:
            agent_kwargs["provider"] = self.config.provider
        
        # Add reasoning pattern if using ReasoningAgent
        if self.config.reasoning_pattern and self.agent_class == ReasoningAgent:
            agent_kwargs["reasoning_pattern"] = self.config.reasoning_pattern
        
        # Create agent
        self._agent = await self._fabric.create_unified_agent(**agent_kwargs)
        
        # Add tool proxy
        self.tools = ToolProxy(self._agent, self._fabric)
        
        self._initialized = True
    
    async def __call__(self, *args, **kwargs):
        """Execute the decorated function."""
        await self._initialize()
        
        # Bind self (with tools) to the function
        bound_func = functools.partial(self.func, self)
        
        # Execute
        if asyncio.iscoroutinefunction(self.func):
            return await bound_func(*args, **kwargs)
        else:
            return bound_func(*args, **kwargs)
    
    async def arun(self, prompt: str, **kwargs) -> Any:
        """Run the agent with a prompt (compatibility method)."""
        await self._initialize()
        return await self._agent.arun(prompt, **kwargs)
    
    @property
    def agent(self) -> Agent:
        """Get the underlying agent instance."""
        if not self._initialized:
            raise RuntimeError("Agent not initialized. Call the decorated function first.")
        return self._agent


def agent(
    name: str,
    *,
    servers: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    reasoning: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    sandbox: bool = False,
    memory: bool = False,
    **metadata
) -> Callable:
    """
    Decorator to create an agent with natural tool access.
    
    Args:
        name: Agent name
        servers: List of MCP/A2A server URLs to connect to
        tools: List of specific tools to load (if not loading all from servers)
        model: LLM model to use
        provider: LLM provider (openai, anthropic, ollama)
        reasoning: Reasoning pattern (chain_of_thought, tree_of_thoughts, react)
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        sandbox: Enable sandboxed execution
        memory: Enable memory system
        **metadata: Additional metadata
    
    Example:
        @agent("researcher", servers=["http://localhost:3000/mcp"])
        async def research_agent(self, topic: str):
            # Natural tool access via self.tools
            results = await self.tools.web_search(query=topic)
            summary = await self.tools.summarize(text=results)
            return summary
    """
    def decorator(func: Callable) -> DecoratedAgent:
        # Determine agent class based on reasoning pattern
        agent_class = Agent
        if reasoning:
            agent_class = ReasoningAgent
        
        config = AgentConfig(
            name=name,
            servers=servers,
            tools=tools,
            model=model,
            provider=provider,
            reasoning_pattern=reasoning,
            temperature=temperature,
            max_tokens=max_tokens,
            sandbox_enabled=sandbox,
            memory_enabled=memory,
            metadata=metadata
        )
        
        return DecoratedAgent(func, config, agent_class)
    
    return decorator


def workflow(
    name: str,
    *,
    steps: Optional[List[str]] = None,
    parallel: bool = False,
    **metadata
) -> Callable:
    """
    Decorator to create a workflow.
    
    Args:
        name: Workflow name
        steps: List of step names (auto-detected if not provided)
        parallel: Whether steps can run in parallel
        **metadata: Additional metadata
    
    Example:
        @workflow("research_flow")
        class ResearchWorkflow:
            @step
            async def gather_data(self, topic: str):
                return await self.tools.search(topic)
            
            @step
            async def analyze(self, data: str):
                return await self.tools.analyze(data)
    """
    def decorator(cls: Type) -> Type:
        # Find all methods marked as steps
        step_methods = []
        for name, method in inspect.getmembers(cls):
            if hasattr(method, "_is_step"):
                step_methods.append((name, method))
        
        # Sort by step order if defined
        step_methods.sort(key=lambda x: getattr(x[1], "_step_order", 0))
        
        # Add workflow metadata
        cls._workflow_name = name
        cls._workflow_steps = step_methods
        cls._workflow_parallel = parallel
        cls._workflow_metadata = metadata
        
        # Add execution method
        async def execute_workflow(self, input_data: Any) -> Any:
            """Execute the workflow steps."""
            if parallel:
                # Run all steps in parallel
                tasks = []
                for step_name, step_method in step_methods:
                    tasks.append(step_method(self, input_data))
                results = await asyncio.gather(*tasks)
                return dict(zip([name for name, _ in step_methods], results))
            else:
                # Run steps sequentially
                result = input_data
                for step_name, step_method in step_methods:
                    result = await step_method(self, result)
                return result
        
        cls.execute = execute_workflow
        
        return cls
    
    return decorator


def step(order: int = 0):
    """Mark a method as a workflow step."""
    def decorator(func: Callable) -> Callable:
        func._is_step = True
        func._step_order = order
        return func
    return decorator


def chain(*agents: Union[str, DecoratedAgent, Callable]) -> Callable:
    """
    Chain multiple agents together.
    
    Args:
        *agents: Agent names, decorated agents, or agent functions to chain
    
    Example:
        @chain("researcher", "writer", "reviewer")
        async def research_pipeline(topic: str):
            return {"topic": topic, "timestamp": datetime.now()}
            
        # Or with direct agent references
        @chain(researcher, writer, reviewer)
        async def research_pipeline(topic: str):
            return topic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get initial input from the decorated function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Chain through each agent
            for agent_ref in agents:
                if isinstance(agent_ref, str):
                    # Look up agent by name from registry
                    agent_instance = get_agent(agent_ref)
                    if not agent_instance:
                        raise ValueError(f"Agent '{agent_ref}' not found in registry")
                    result = await agent_instance(result)
                    
                elif isinstance(agent_ref, DecoratedAgent):
                    # Use decorated agent directly
                    result = await agent_ref(result)
                    
                elif callable(agent_ref):
                    # Handle raw agent functions
                    if asyncio.iscoroutinefunction(agent_ref):
                        result = await agent_ref(result)
                    else:
                        result = agent_ref(result)
                        
                else:
                    raise ValueError(f"Invalid agent type: {type(agent_ref)}")
            
            return result
        
        # Store chain metadata
        wrapper._is_chain = True
        wrapper._chain_agents = agents
        
        return wrapper
    
    return decorator


def parallel(*agents: Union[str, DecoratedAgent, Callable]) -> Callable:
    """
    Run multiple agents in parallel.
    
    Args:
        *agents: Agent names, decorated agents, or agent functions to run in parallel
    
    Example:
        @parallel("analyzer1", "analyzer2", "analyzer3")
        async def multi_analysis(data: str):
            return {"data": data, "timestamp": datetime.now()}
            
        # Returns: [result1, result2, result3]
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get input data from the decorated function
            if asyncio.iscoroutinefunction(func):
                input_data = await func(*args, **kwargs)
            else:
                input_data = func(*args, **kwargs)
            
            # Create tasks for parallel execution
            tasks = []
            for agent_ref in agents:
                if isinstance(agent_ref, str):
                    # Look up agent by name
                    agent_instance = get_agent(agent_ref)
                    if not agent_instance:
                        raise ValueError(f"Agent '{agent_ref}' not found in registry")
                    tasks.append(agent_instance(input_data))
                    
                elif isinstance(agent_ref, DecoratedAgent):
                    # Use decorated agent directly
                    tasks.append(agent_ref(input_data))
                    
                elif callable(agent_ref):
                    # Handle raw agent functions
                    if asyncio.iscoroutinefunction(agent_ref):
                        tasks.append(agent_ref(input_data))
                    else:
                        # Wrap sync function for gather
                        tasks.append(asyncio.create_task(
                            asyncio.to_thread(agent_ref, input_data)
                        ))
                        
                else:
                    raise ValueError(f"Invalid agent type: {type(agent_ref)}")
            
            # Execute all agents in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    agent_name = agents[i] if isinstance(agents[i], str) else f"Agent {i}"
                    logger.error(f"Error in {agent_name}: {result}")
            
            return results
        
        # Store parallel metadata
        wrapper._is_parallel = True
        wrapper._parallel_agents = agents
        
        return wrapper
    
    return decorator


def orchestrator(
    strategy: str = "consensus",
    **kwargs
) -> Callable:
    """
    Create an orchestrator that coordinates multiple agents.
    
    Args:
        strategy: Orchestration strategy ("consensus", "best_of", "weighted", "sequential")
        **kwargs: Strategy-specific parameters
    
    Example:
        @orchestrator(strategy="consensus", min_agreement=0.7)
        @parallel("expert1", "expert2", "expert3")
        async def expert_consensus(question: str):
            return question
            
        # The orchestrator will run agents in parallel and apply consensus
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the wrapped function (which might be @parallel or @chain)
            results = await func(*args, **kwargs)
            
            # Apply orchestration strategy
            if strategy == "consensus":
                return await _consensus_strategy(results, kwargs.get("min_agreement", 0.5))
            elif strategy == "best_of":
                return await _best_of_strategy(results, kwargs.get("metric", "confidence"))
            elif strategy == "weighted":
                return await _weighted_strategy(results, kwargs.get("weights"))
            elif strategy == "sequential":
                return await _sequential_strategy(results, kwargs.get("threshold"))
            else:
                raise ValueError(f"Unknown orchestration strategy: {strategy}")
        
        wrapper._is_orchestrator = True
        wrapper._orchestration_strategy = strategy
        
        return wrapper
    
    return decorator


async def _consensus_strategy(results: List[Any], min_agreement: float) -> Any:
    """Apply consensus strategy to results."""
    if not results:
        return None
    
    # For simple results, use majority voting
    if all(isinstance(r, (str, int, bool)) for r in results):
        from collections import Counter
        counter = Counter(results)
        most_common = counter.most_common(1)[0]
        agreement_ratio = most_common[1] / len(results)
        
        if agreement_ratio >= min_agreement:
            return most_common[0]
        else:
            return {
                "consensus": None,
                "agreement": agreement_ratio,
                "votes": dict(counter)
            }
    
    # For complex results, return all with metadata
    return {
        "consensus": "complex_results",
        "results": results,
        "count": len(results)
    }


async def _best_of_strategy(results: List[Any], metric: str) -> Any:
    """Select best result based on metric."""
    if not results:
        return None
    
    # If results have the metric attribute
    if all(hasattr(r, metric) for r in results):
        return max(results, key=lambda r: getattr(r, metric))
    
    # If results are dicts with metric key
    if all(isinstance(r, dict) and metric in r for r in results):
        return max(results, key=lambda r: r[metric])
    
    # Default to first result
    return results[0]


async def _weighted_strategy(results: List[Any], weights: Optional[List[float]]) -> Any:
    """Apply weighted combination of results."""
    if not results:
        return None
    
    if not weights:
        weights = [1.0 / len(results)] * len(results)
    
    # For numeric results, compute weighted average
    if all(isinstance(r, (int, float)) for r in results):
        return sum(r * w for r, w in zip(results, weights))
    
    # For other results, return with weights
    return {
        "weighted_results": list(zip(results, weights)),
        "strategy": "weighted"
    }


async def _sequential_strategy(results: List[Any], threshold: Optional[float]) -> Any:
    """Process results sequentially until threshold is met."""
    # This is more relevant for @chain, but included for completeness
    if not results:
        return None
    
    # Return last result (chain endpoint)
    return results[-1] if isinstance(results, list) else results


class AgentRegistry:
    """Registry for decorated agents."""
    
    def __init__(self):
        self._agents: Dict[str, DecoratedAgent] = {}
    
    def register(self, agent: DecoratedAgent):
        """Register an agent."""
        self._agents[agent.config.name] = agent
        logger.debug(f"Registered agent: {agent.config.name}")
    
    def get(self, name: str) -> Optional[DecoratedAgent]:
        """Get agent by name."""
        return self._agents.get(name)
    
    def list(self) -> List[str]:
        """List registered agent names."""
        return list(self._agents.keys())
    
    def clear(self):
        """Clear all registered agents."""
        self._agents.clear()


# Global registry
_agent_registry = AgentRegistry()


def register_agent(agent: DecoratedAgent):
    """Register an agent in the global registry."""
    _agent_registry.register(agent)


def get_agent(name: str) -> Optional[DecoratedAgent]:
    """Get agent from the global registry."""
    return _agent_registry.get(name)


def list_agents() -> List[str]:
    """List all registered agent names."""
    return _agent_registry.list()


def clear_agents():
    """Clear all registered agents."""
    _agent_registry.clear()


# Configuration loading
def load_agent_config(config_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Load agent configuration from YAML file.
    
    Example agenticraft.yaml:
        agents:
          researcher:
            servers:
              - http://localhost:3000/mcp
              - ws://localhost:8080/a2a
            model: gpt-4
            temperature: 0.7
            
          writer:
            servers:
              - http://localhost:3001/mcp
            model: claude-3
            reasoning: chain_of_thought
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    return config


def from_config(config_file: Union[str, Path]) -> Callable:
    """
    Create agents from configuration file.
    
    Args:
        config_file: Path to agenticraft.yaml
    
    Example:
        @from_config("agenticraft.yaml")
        class MyAgents:
            @agent("researcher")  # Uses config from file
            async def research(self, topic: str):
                return await self.tools.search(topic)
    """
    config = load_agent_config(config_file)
    
    def decorator(cls: Type) -> Type:
        # Apply configuration to all agents in class
        for name, method in inspect.getmembers(cls):
            if isinstance(method, DecoratedAgent):
                # Override config from file
                agent_config = config.get("agents", {}).get(method.config.name, {})
                for key, value in agent_config.items():
                    if hasattr(method.config, key):
                        setattr(method.config, key, value)
        
        return cls
    
    return decorator
