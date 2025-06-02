"""Tool system for AgentiCraft"""

from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
import inspect
import asyncio
from functools import wraps

import structlog

logger = structlog.get_logger()


@dataclass
class ToolConfig:
    """Configuration for a Tool"""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]


class Tool:
    """Base Tool class"""
    
    def __init__(self, name: str, description: str, func: Callable):
        """Initialize a Tool
        
        Args:
            name: Tool name
            description: Tool description
            func: Callable function
        """
        self.name = name
        self.description = description
        self.func = func
        self.config = self._build_config()
    
    def _build_config(self) -> ToolConfig:
        """Build tool configuration from function signature"""
        sig = inspect.signature(self.func)
        parameters = {
            param.name: {
                "type": str(param.annotation) if param.annotation != param.empty else "Any",
                "required": param.default == param.empty
            }
            for param in sig.parameters.values()
        }
        
        return ToolConfig(
            name=self.name,
            description=self.description,
            parameters=parameters,
            returns={"type": "Any"}
        )
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool result
        """
        logger.debug("tool_execution_started", tool=self.name, kwargs=kwargs)
        
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)
            
            logger.debug("tool_execution_completed", tool=self.name)
            return result
        except Exception as e:
            logger.error("tool_execution_failed", tool=self.name, error=str(e))
            raise
    
    @staticmethod
    def create(name: str, description: Optional[str] = None):
        """Decorator to create a tool from a function
        
        Args:
            name: Tool name
            description: Tool description
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Tool:
            desc = description or func.__doc__ or "No description"
            return Tool(name=name, description=desc, func=func)
        return decorator
    
    @classmethod
    def Calculator(cls) -> "Tool":
        """Built-in calculator tool"""
        def calculate(expression: str) -> float:
            """Safely evaluate mathematical expressions"""
            # Simple implementation - in production use a proper math parser
            try:
                # Only allow basic math operations
                allowed_chars = "0123456789+-*/()., "
                if all(c in allowed_chars for c in expression):
                    return eval(expression)
                else:
                    raise ValueError("Invalid characters in expression")
            except Exception as e:
                raise ValueError(f"Calculation error: {e}")
        
        return cls("calculator", "Perform mathematical calculations", calculate)
    
    @classmethod
    def WebSearch(cls) -> "Tool":
        """Built-in web search tool"""
        async def search(query: str, num_results: int = 5) -> Dict[str, Any]:
            """Search the web for information"""
            # Placeholder implementation
            return {
                "query": query,
                "results": [
                    {"title": f"Result {i+1}", "url": f"https://example.com/{i}"}
                    for i in range(num_results)
                ]
            }
        
        return cls("web_search", "Search the web for information", search)
    
    @classmethod
    def FileReader(cls) -> "Tool":
        """Built-in file reader tool"""
        async def read_file(path: str) -> str:
            """Read contents of a file"""
            try:
                with open(path, 'r') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Failed to read file: {e}")
        
        return cls("file_reader", "Read contents of a file", read_file)
