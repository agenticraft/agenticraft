# AgentiCraft Providers

This directory contains LLM provider implementations for AgentiCraft. Each provider offers a consistent interface while supporting provider-specific features.

## 📦 Available Providers

### OpenAI Provider (`openai.py`)
**Status**: ✅ Complete  
**Models**: GPT-4, GPT-3.5, GPT-4 Turbo, and all OpenAI models  
**Features**:
- Full tool/function calling support
- JSON mode (GPT-4 Turbo)
- Custom endpoints (Azure OpenAI, etc.)
- Streaming support (coming in v0.2.0)

**Configuration**:
```python
# Via environment variable
export OPENAI_API_KEY="sk-..."

# Or in code
agent = Agent(model="gpt-4", api_key="sk-...")
```

### Anthropic Provider (`anthropic.py`)
**Status**: ✅ Complete  
**Models**: Claude 3 (Opus, Sonnet, Haiku)  
**Features**:
- Native tool calling
- System message handling
- 200K+ token context window
- Streaming support (coming in v0.2.0)

**Configuration**:
```python
# Via environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Or in code
agent = Agent(model="claude-3-opus-20240229", api_key="sk-ant-...")
```

### Ollama Provider (`ollama.py`)
**Status**: ✅ Complete  
**Models**: Llama 2, Mistral, CodeLlama, Phi, and any Ollama-supported model  
**Features**:
- Local model execution
- Model management (list, pull)
- No API key required
- Custom server configuration
- Tool simulation via prompts

**Configuration**:
```python
# Default local setup
agent = Agent(model="ollama/llama2")

# Custom server
agent = Agent(
    model="ollama/mistral",
    base_url="http://192.168.1.100:11434"
)
```

## 🚀 Usage Examples

### Basic Usage
```python
from agenticraft import Agent

# OpenAI
openai_agent = Agent(model="gpt-4")

# Anthropic
claude_agent = Agent(model="claude-3-sonnet-20240229")

# Ollama (local)
local_agent = Agent(model="ollama/llama2")

# All work the same way!
response = await agent.arun("Hello, how are you?")
print(response.content)
```

### Provider-Specific Features
```python
# OpenAI JSON mode
response = await openai_agent.run(
    "Generate a user profile",
    response_format={"type": "json_object"}
)

# Anthropic with system message
claude_agent = Agent(
    model="claude-3-opus-20240229",
    instructions="You are a helpful assistant who speaks like Shakespeare."
)

# Ollama model management
from agenticraft.providers.ollama import OllamaProvider
provider = OllamaProvider()
models = await provider.list_models()
await provider.pull_model("codellama")
```

## 🏗️ Architecture

### Provider Selection
The `ProviderFactory` automatically selects the appropriate provider based on the model name:

```python
# Automatic detection
Agent(model="gpt-4")           # → OpenAIProvider
Agent(model="claude-3-opus")   # → AnthropicProvider  
Agent(model="ollama/llama2")   # → OllamaProvider

# Explicit provider specification
Agent(model="openai:gpt-4")    # Force OpenAI provider
```

### Lazy Loading
Providers are loaded only when needed to reduce import time and dependencies:

```python
# Providers are imported only when first used
agent = Agent(model="gpt-4")  # OpenAI provider loaded here
```

## 🔧 Adding a New Provider

To add support for a new LLM provider:

### 1. Create Provider Implementation
Create `providers/your_provider.py`:

```python
"""Your provider implementation for AgentiCraft."""

import os
from typing import Any, Dict, List, Optional, Union

from ..core.config import settings
from ..core.exceptions import ProviderError, ProviderAuthError
from ..core.provider import BaseProvider
from ..core.types import CompletionResponse, Message, ToolCall, ToolDefinition


class YourProvider(BaseProvider):
    """Provider for Your LLM service."""
    
    def __init__(self, **kwargs):
        """Initialize Your provider."""
        # Get API key from kwargs, settings, or environment
        api_key = (
            kwargs.get("api_key") or 
            settings.your_api_key or 
            os.getenv("YOUR_API_KEY")
        )
        if not api_key:
            raise ProviderAuthError("your_provider")
        
        kwargs["api_key"] = api_key
        kwargs.setdefault("base_url", settings.your_base_url)
        
        # Store model if provided
        self.model = kwargs.pop('model', 'your-default-model')
        
        super().__init__(**kwargs)
        
        self._client = None
    
    @property
    def client(self):
        """Get or create Your client."""
        if self._client is None:
            try:
                from your_sdk import YourClient
                self._client = YourClient(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout,
                    max_retries=self.max_retries
                )
            except ImportError:
                raise ProviderError("Your provider requires 'your-sdk' package")
        return self._client
    
    async def complete(
        self,
        messages: Union[List[Message], List[Dict[str, Any]]],
        model: Optional[str] = None,
        tools: Optional[Union[List[ToolDefinition], List[Dict[str, Any]]]] = None,
        tool_choice: Optional[Any] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> CompletionResponse:
        """Get completion from Your LLM."""
        try:
            # Implementation details
            # 1. Format messages
            # 2. Handle tools if supported
            # 3. Make API call
            # 4. Parse response
            # 5. Return CompletionResponse
            pass
        except Exception as e:
            raise ProviderError(f"Your completion failed: {e}") from e
    
    def validate_auth(self) -> None:
        """Validate authentication credentials."""
        if not self.api_key:
            raise ProviderAuthError("your_provider")
```

### 2. Update Provider Exports
Add to `providers/__init__.py`:

```python
from .your_provider import YourProvider

__all__ = [
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "YourProvider",  # Add this
]
```

### 3. Register in ProviderFactory
Update `core/provider.py` in the `_lazy_load_providers` method:

```python
@classmethod
def _lazy_load_providers(cls) -> None:
    """Lazily load provider implementations."""
    if not cls._providers:
        from ..providers.openai import OpenAIProvider
        from ..providers.anthropic import AnthropicProvider
        from ..providers.ollama import OllamaProvider
        from ..providers.your_provider import YourProvider  # Add this
        
        cls._providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "ollama": OllamaProvider,
            "your_provider": YourProvider,  # Add this
        }
```

Also update the model detection logic in `ProviderFactory.create()`:

```python
elif model.startswith("your-model-prefix"):
    provider_name = "your_provider"
```

### 4. Create Tests
Create `tests/unit/providers/test_your_provider.py` with comprehensive tests:
- Initialization tests
- Authentication validation
- Completion tests (with and without tools)
- Error handling
- Edge cases

### 5. Create Examples
Create `examples/providers/your_provider_example.py` showing:
- Basic usage
- Model selection
- Tool calling (if supported)
- Provider-specific features
- Error handling

### 6. Update Documentation
- Add to this README
- Update main README.md
- Add to CHANGELOG.md

## 📋 Provider Requirements

All providers must:
1. Inherit from `BaseProvider`
2. Implement `complete()` method
3. Implement `validate_auth()` method
4. Handle errors gracefully
5. Support both `Message` objects and dict messages
6. Return proper `CompletionResponse` objects
7. Support optional tool calling (or document limitations)

## 🧪 Testing Providers

Each provider has comprehensive tests:

```bash
# Test individual provider
pytest tests/unit/providers/test_openai.py -v
pytest tests/unit/providers/test_anthropic.py -v
pytest tests/unit/providers/test_ollama.py -v

# Test all providers
pytest tests/unit/providers/ -v

# Run provider examples
python examples/providers/openai_example.py
python examples/providers/anthropic_example.py
python examples/providers/ollama_example.py
python examples/providers/provider_switching.py
```

## 🔒 Security Considerations

1. **API Keys**: Never commit API keys. Use environment variables or secure vaults.
2. **Base URLs**: Be cautious with custom endpoints. Validate SSL certificates.
3. **Local Models**: Ollama runs locally, ensuring data privacy.
4. **Error Messages**: Providers should not leak sensitive information in errors.

## 📈 Performance Tips

1. **Model Selection**: 
   - Use smaller models for simple tasks (GPT-3.5, Claude Haiku)
   - Reserve larger models for complex reasoning (GPT-4, Claude Opus)

2. **Caching**: Consider implementing response caching for repeated queries

3. **Timeouts**: Adjust timeouts based on model and query complexity:
   ```python
   # Fast model, short timeout
   agent = Agent(model="gpt-3.5-turbo", timeout=30)
   
   # Large model, longer timeout
   agent = Agent(model="gpt-4", timeout=120)
   
   # Local model, very long timeout for first run
   agent = Agent(model="ollama/llama2", timeout=600)
   ```

4. **Batch Processing**: Group similar requests when possible

## 🤝 Contributing

When contributing a new provider:
1. Follow the existing code patterns
2. Keep it simple (~150-300 lines)
3. Add comprehensive tests (aim for >95% coverage)
4. Document provider-specific features
5. Include practical examples
6. Update all relevant documentation

## 📝 License

All provider implementations are part of AgentiCraft and follow the Apache 2.0 license.