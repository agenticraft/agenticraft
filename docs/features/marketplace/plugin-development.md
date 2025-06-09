# Plugin Development Guide

Comprehensive guide to creating, testing, and publishing AgentiCraft plugins.

## Overview

This guide covers the complete plugin development lifecycle:
1. Setting up your development environment
2. Creating a plugin from scratch
3. Testing and debugging
4. Publishing to the marketplace
5. Maintenance and updates

## Getting Started

### Prerequisites

```bash
# Install AgentiCraft with development dependencies
pip install agenticraft[dev]

# Install plugin development tools
pip install agenticraft-plugin-tools
```

### Plugin Generator

Use the CLI to generate a plugin skeleton:

```bash
# Interactive plugin creation
agenticraft plugin create

# Or with options
agenticraft plugin create \
  --name "my-awesome-tool" \
  --author "Your Name" \
  --description "Tool description" \
  --type "tool"
```

This creates:
```
my-awesome-tool/
├── plugin.yaml
├── README.md
├── LICENSE
├── setup.py
├── requirements.txt
├── src/
│   └── my_awesome_tool/
│       ├── __init__.py
│       ├── tool.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_tool.py
│   └── conftest.py
├── examples/
│   ├── basic_usage.py
│   └── advanced_usage.py
└── .github/
    └── workflows/
        └── test.yml
```

## Plugin Architecture

### Tool Implementation

```python
# src/my_awesome_tool/tool.py
from typing import Dict, Any, List, Optional
from agenticraft.tools import BaseTool, ToolResult
from agenticraft.tools.decorators import tool_method, requires_config

class MyAwesomeTool(BaseTool):
    """A powerful tool for AgentiCraft agents.
    
    This tool provides functionality for...
    """
    
    name = "my_awesome_tool"
    description = "Performs awesome operations"
    version = "1.0.0"
    
    # Configuration schema
    config_schema = {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "description": "API key for the service"
            },
            "timeout": {
                "type": "integer",
                "description": "Request timeout in seconds",
                "default": 30
            },
            "retry_count": {
                "type": "integer",
                "description": "Number of retries",
                "default": 3
            }
        },
        "required": ["api_key"]
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the tool.
        
        Args:
            config: Tool configuration
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        self.timeout = self.config.get("timeout", 30)
        self.retry_count = self.config.get("retry_count", 3)
        
        # Initialize any clients or resources
        self._client = None
        
    async def setup(self):
        """Async setup for the tool."""
        # Initialize async resources
        self._client = await self._create_client()
        
    async def teardown(self):
        """Cleanup resources."""
        if self._client:
            await self._client.close()
    
    @tool_method
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Main tool execution method.
        
        Args:
            query: The query to process
            **kwargs: Additional parameters
            
        Returns:
            ToolResult with the response
        """
        try:
            # Validate input
            if not query:
                return ToolResult(
                    success=False,
                    error="Query cannot be empty"
                )
            
            # Process the query
            result = await self._process_query(query, **kwargs)
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"query_length": len(query)}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"error_type": type(e).__name__}
            )
    
    @tool_method
    @requires_config("api_key")
    async def advanced_operation(self, data: Dict[str, Any]) -> ToolResult:
        """Perform an advanced operation requiring API key.
        
        Args:
            data: Input data
            
        Returns:
            ToolResult with processed data
        """
        # Implementation here
        pass
    
    async def _process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Internal query processing."""
        # Your implementation
        return {"result": f"Processed: {query}"}
    
    async def _create_client(self):
        """Create API client."""
        # Client initialization
        pass
    
    def get_capabilities(self) -> List[str]:
        """Return tool capabilities."""
        return [
            "process_text",
            "analyze_data",
            "generate_reports"
        ]
```

### Utility Functions

```python
# src/my_awesome_tool/utils.py
import re
from typing import List, Dict, Any
from functools import lru_cache

def validate_input(text: str) -> bool:
    """Validate input text.
    
    Args:
        text: Input to validate
        
    Returns:
        True if valid
    """
    if not text or len(text) > 10000:
        return False
    
    # Additional validation
    return True

@lru_cache(maxsize=128)
def parse_query(query: str) -> Dict[str, Any]:
    """Parse query into components.
    
    Args:
        query: Query string
        
    Returns:
        Parsed components
    """
    # Extract patterns
    patterns = {
        "command": r"^(\w+)\s+",
        "parameters": r"--(\w+)=([^\s]+)",
        "flags": r"-(\w)"
    }
    
    result = {"command": None, "parameters": {}, "flags": []}
    
    # Parse command
    command_match = re.match(patterns["command"], query)
    if command_match:
        result["command"] = command_match.group(1)
    
    # Parse parameters
    for match in re.finditer(patterns["parameters"], query):
        result["parameters"][match.group(1)] = match.group(2)
    
    # Parse flags
    for match in re.finditer(patterns["flags"], query):
        result["flags"].append(match.group(1))
    
    return result
```

## Plugin Manifest

### Complete Manifest Example

```yaml
# plugin.yaml
name: my-awesome-tool
version: 1.0.0
description: A powerful tool for data processing and analysis
author: Your Name <your.email@example.com>
license: MIT

# Metadata
metadata:
  homepage: https://github.com/yourusername/my-awesome-tool
  repository: https://github.com/yourusername/my-awesome-tool
  documentation: https://my-awesome-tool.readthedocs.io
  changelog: https://github.com/yourusername/my-awesome-tool/blob/main/CHANGELOG.md
  
  # Categorization
  category: data-processing
  tags:
    - data
    - analysis
    - processing
    - api
    
  # Support
  issues: https://github.com/yourusername/my-awesome-tool/issues
  discussions: https://github.com/yourusername/my-awesome-tool/discussions

# Tools provided
tools:
  - name: MyAwesomeTool
    module: my_awesome_tool.tool
    class: MyAwesomeTool
    description: Main tool for data processing
    
    # Tool-specific configuration
    config_schema:
      type: object
      properties:
        api_key:
          type: string
          description: API key for the service
          env_var: MY_AWESOME_TOOL_API_KEY
        
        endpoint:
          type: string
          description: API endpoint
          default: https://api.example.com
          
        rate_limit:
          type: integer
          description: Requests per minute
          default: 60
          minimum: 1
          maximum: 1000
      
      required: [api_key]

# Dependencies
dependencies:
  # Core dependency
  agenticraft: ">=0.2.0,<1.0.0"
  
  # Required dependencies
  aiohttp: ">=3.8.0"
  pydantic: ">=2.0.0"
  
  # Optional dependencies
  optional:
    pandas: ">=1.5.0"  # For data processing
    numpy: ">=1.20.0"  # For numerical operations

# Development dependencies
dev_dependencies:
  pytest: ">=7.0.0"
  pytest-asyncio: ">=0.20.0"
  pytest-cov: ">=4.0.0"
  black: ">=22.0.0"
  ruff: ">=0.0.200"

# Python version requirement
python_requires: ">=3.8"

# Entry points for plugin discovery
entry_points:
  agenticraft.tools:
    - my_awesome_tool = my_awesome_tool.tool:MyAwesomeTool

# Additional files to include
include:
  - README.md
  - LICENSE
  - CHANGELOG.md
  - examples/**/*.py

# Scripts to run
scripts:
  post_install: "my_awesome_tool.setup:post_install"
  pre_uninstall: "my_awesome_tool.setup:pre_uninstall"
```

## Testing Your Plugin

### Unit Tests

```python
# tests/test_tool.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from my_awesome_tool.tool import MyAwesomeTool
from agenticraft.tools import ToolResult

class TestMyAwesomeTool:
    """Test suite for MyAwesomeTool."""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        config = {"api_key": "test-key"}
        return MyAwesomeTool(config)
    
    @pytest.fixture
    def mock_client(self):
        """Mock API client."""
        client = AsyncMock()
        client.request.return_value = {"status": "success"}
        return client
    
    @pytest.mark.asyncio
    async def test_execute_success(self, tool, mock_client):
        """Test successful execution."""
        # Patch the client
        with patch.object(tool, '_client', mock_client):
            result = await tool.execute("test query")
            
            assert result.success
            assert result.data
            assert "result" in result.data
    
    @pytest.mark.asyncio
    async def test_execute_empty_query(self, tool):
        """Test execution with empty query."""
        result = await tool.execute("")
        
        assert not result.success
        assert result.error == "Query cannot be empty"
    
    @pytest.mark.asyncio
    async def test_execute_with_error(self, tool, mock_client):
        """Test execution with API error."""
        # Make client raise exception
        mock_client.request.side_effect = Exception("API Error")
        
        with patch.object(tool, '_client', mock_client):
            result = await tool.execute("test query")
            
            assert not result.success
            assert "API Error" in result.error
    
    def test_configuration(self, tool):
        """Test tool configuration."""
        assert tool.api_key == "test-key"
        assert tool.timeout == 30
        assert tool.retry_count == 3
    
    def test_capabilities(self, tool):
        """Test tool capabilities."""
        capabilities = tool.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert "process_text" in capabilities
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
from agenticraft import Agent
from agenticraft.marketplace import load_plugin

@pytest.mark.integration
@pytest.mark.asyncio
async def test_plugin_with_agent():
    """Test plugin integration with agent."""
    # Load plugin
    plugin = load_plugin("my-awesome-tool", config={
        "api_key": "test-key"
    })
    
    # Create agent with plugin
    agent = Agent(name="TestAgent")
    agent.add_tool(plugin)
    
    # Test execution
    response = await agent.arun("Use my_awesome_tool to process this data")
    
    assert response
    assert "Processed" in response

@pytest.mark.integration
@pytest.mark.asyncio
async def test_plugin_lifecycle():
    """Test plugin lifecycle."""
    plugin = load_plugin("my-awesome-tool", config={
        "api_key": "test-key"
    })
    
    # Setup
    await plugin.setup()
    
    try:
        # Use plugin
        result = await plugin.execute("test")
        assert result.success
    finally:
        # Teardown
        await plugin.teardown()
```

### Testing Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from typing import Generator

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_api_response():
    """Mock API response."""
    return {
        "status": "success",
        "data": {
            "result": "processed",
            "timestamp": "2025-06-15T10:00:00Z"
        }
    }

@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "api_key": "test-key",
        "endpoint": "https://test.example.com",
        "timeout": 10
    }
```

## Advanced Features

### Async Context Manager

```python
class ContextualTool(BaseTool):
    """Tool that works as context manager."""
    
    async def __aenter__(self):
        """Enter context."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        await self.teardown()
        
    async def process_batch(self, items: List[str]) -> List[ToolResult]:
        """Process items in batch."""
        async with self:
            results = []
            for item in items:
                result = await self.execute(item)
                results.append(result)
            return results
```

### Streaming Support

```python
from typing import AsyncIterator
from agenticraft.tools import StreamingTool, StreamChunk

class StreamingDataTool(StreamingTool):
    """Tool with streaming support."""
    
    async def stream_execute(
        self,
        query: str,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Execute with streaming response."""
        # Simulate streaming data
        chunks = await self._get_data_chunks(query)
        
        for i, chunk in enumerate(chunks):
            yield StreamChunk(
                content=chunk,
                metadata={"chunk_index": i, "total": len(chunks)},
                is_final=i == len(chunks) - 1
            )
    
    async def _get_data_chunks(self, query: str) -> List[str]:
        """Get data in chunks."""
        # Implementation
        return ["chunk1", "chunk2", "chunk3"]
```

### Caching

```python
from functools import lru_cache
from agenticraft.tools.cache import async_lru_cache

class CachedTool(BaseTool):
    """Tool with caching capabilities."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self._cache_size = self.config.get("cache_size", 100)
    
    @async_lru_cache(maxsize=128)
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute with caching."""
        # Expensive operation
        result = await self._expensive_operation(query)
        
        return ToolResult(
            success=True,
            data=result,
            metadata={"cached": False}
        )
    
    def clear_cache(self):
        """Clear the cache."""
        self.execute.cache_clear()
```

### Multi-Tool Plugin

```python
# Plugin that provides multiple tools
class DataProcessorTool(BaseTool):
    name = "data_processor"
    description = "Process various data formats"

class DataAnalyzerTool(BaseTool):
    name = "data_analyzer"
    description = "Analyze processed data"

class DataVisualizerTool(BaseTool):
    name = "data_visualizer"
    description = "Create visualizations"

# Register all tools in manifest
"""
tools:
  - name: DataProcessorTool
    module: my_plugin.tools
    class: DataProcessorTool
    
  - name: DataAnalyzerTool
    module: my_plugin.tools
    class: DataAnalyzerTool
    
  - name: DataVisualizerTool
    module: my_plugin.tools
    class: DataVisualizerTool
"""
```

## Publishing Your Plugin

### Pre-publish Checklist

```python
# scripts/pre_publish.py
import subprocess
import sys
from pathlib import Path

def run_checks():
    """Run pre-publish checks."""
    checks = [
        ("Running tests", "pytest tests/"),
        ("Checking code style", "black --check src/"),
        ("Running linter", "ruff check src/"),
        ("Checking manifest", "agenticraft plugin validate"),
        ("Building package", "python setup.py sdist bdist_wheel")
    ]
    
    for description, command in checks:
        print(f"\n{description}...")
        result = subprocess.run(command.split(), capture_output=True)
        
        if result.returncode != 0:
            print(f"❌ {description} failed!")
            print(result.stderr.decode())
            return False
    
    print("\n✅ All checks passed!")
    return True

if __name__ == "__main__":
    if not run_checks():
        sys.exit(1)
```

### Publishing Process

```bash
# 1. Update version
agenticraft plugin version patch  # or minor/major

# 2. Run checks
python scripts/pre_publish.py

# 3. Create git tag
git tag v1.0.0
git push origin v1.0.0

# 4. Publish to marketplace
agenticraft plugin publish --token YOUR_TOKEN

# Or publish to PyPI
python -m build
python -m twine upload dist/*
```

### Post-publish

```python
# Verify installation
pip install my-awesome-tool

# Test in clean environment
python -c "from agenticraft.marketplace import load_plugin; print(load_plugin('my-awesome-tool'))"
```

## Maintenance

### Version Updates

```python
# scripts/update_version.py
import re
from pathlib import Path

def update_version(new_version: str):
    """Update version in all files."""
    files_to_update = [
        ("plugin.yaml", r"version: .+", f"version: {new_version}"),
        ("setup.py", r"version=['\"].+['\"]", f'version="{new_version}"'),
        ("src/my_awesome_tool/__init__.py", r"__version__ = ['\"].+['\"]", f'__version__ = "{new_version}"'),
    ]
    
    for filename, pattern, replacement in files_to_update:
        path = Path(filename)
        if path.exists():
            content = path.read_text()
            updated = re.sub(pattern, replacement, content)
            path.write_text(updated)
            print(f"Updated {filename}")
```

### Deprecation

```python
import warnings
from functools import wraps

def deprecated(reason: str, version: str):
    """Mark function as deprecated."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated as of version {version}. {reason}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

class MyTool(BaseTool):
    @deprecated("Use execute() instead", "2.0.0")
    async def old_method(self):
        """Deprecated method."""
        pass
```

## Best Practices

### 1. Error Handling

Always provide meaningful error messages:

```python
class RobustTool(BaseTool):
    async def execute(self, query: str) -> ToolResult:
        try:
            # Validate
            validation_error = self._validate_query(query)
            if validation_error:
                return ToolResult(
                    success=False,
                    error=validation_error,
                    error_code="VALIDATION_ERROR"
                )
            
            # Process
            result = await self._process(query)
            
            return ToolResult(success=True, data=result)
            
        except ConnectionError as e:
            return ToolResult(
                success=False,
                error=f"Connection failed: {e}",
                error_code="CONNECTION_ERROR",
                retry_after=60
            )
        except Exception as e:
            logger.exception("Unexpected error")
            return ToolResult(
                success=False,
                error="An unexpected error occurred",
                error_code="INTERNAL_ERROR"
            )
```

### 2. Documentation

Document everything:

```python
class WellDocumentedTool(BaseTool):
    """A well-documented tool for AgentiCraft.
    
    This tool provides comprehensive functionality for data processing
    with support for multiple formats and real-time streaming.
    
    Configuration:
        api_key (str): API key for authentication
        timeout (int): Request timeout in seconds (default: 30)
        retry_count (int): Number of retries (default: 3)
    
    Example:
        ```python
        tool = WellDocumentedTool({"api_key": "your-key"})
        result = await tool.execute("process this data")
        ```
    
    Note:
        Requires Python 3.8+ and AgentiCraft 0.2.0+
    """
```

### 3. Performance

Optimize for performance:

```python
class PerformantTool(BaseTool):
    def __init__(self, config=None):
        super().__init__(config)
        
        # Connection pooling
        self._session = None
        self._connection_pool = None
        
        # Caching
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def setup(self):
        """Initialize resources."""
        # Create connection pool
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30
            )
        )
    
    async def execute_batch(self, queries: List[str]) -> List[ToolResult]:
        """Process multiple queries efficiently."""
        # Use asyncio.gather for parallel processing
        tasks = [self.execute(query) for query in queries]
        return await asyncio.gather(*tasks)
```

## Next Steps

- [Testing Guide](testing-guide.md) - Comprehensive testing strategies
- [Publishing Guide](publishing-guide.md) - Detailed publishing process
- [API Reference](api-reference.md) - Complete API documentation
- [Examples](../../examples/marketplace/) - Working examples
