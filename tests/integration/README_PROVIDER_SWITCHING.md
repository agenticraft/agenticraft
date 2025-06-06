# Provider Switching Tests for AgentiCraft v0.1.1

## Overview

This directory contains integration tests for the provider switching functionality planned for AgentiCraft v0.1.1. The tests verify that agents can seamlessly switch between different LLM providers (OpenAI, Anthropic, Ollama) at runtime.

## Test Files

### 1. `test_provider_switching.py`
Comprehensive integration tests covering:
- Basic provider switching on existing agents
- Provider-specific feature preservation
- Configuration persistence across switches
- Tool and memory compatibility
- Concurrent agents with different providers
- Error handling and rollback scenarios
- Edge cases like switching during execution

### 2. `agent_set_provider_implementation.py`
Example implementation of the `set_provider` method that needs to be added to the Agent class in `agenticraft/core/agent.py`.

## Key Test Scenarios

### Basic Provider Switching
```python
agent = Agent(name="TestAgent", provider="openai")
agent.set_provider("anthropic", model="claude-3-opus-20240229")
agent.set_provider("ollama", model="llama2")
```

### Provider-Specific Features
- **OpenAI**: Tests response_format parameter
- **Anthropic**: Tests system message handling
- **Ollama**: Tests local model parameters (seed, etc.)

### Configuration Preservation
Tests ensure that when switching providers:
- Agent instructions remain unchanged
- Temperature and other parameters persist
- Tools remain registered and functional
- Memory history is preserved

### Error Handling
- Invalid provider names
- Missing API credentials
- Provider initialization failures
- Rollback on failed switches

## Running the Tests

```bash
# Run all provider switching tests
pytest tests/integration/test_provider_switching.py -v

# Run specific test class
pytest tests/integration/test_provider_switching.py::TestProviderSwitching -v

# Run with coverage
pytest tests/integration/test_provider_switching.py --cov=agenticraft.core.agent
```

## Implementation Requirements

For these tests to pass, the following needs to be implemented:

### 1. Add `set_provider` Method to Agent Class
The method should:
- Accept provider name and optional parameters
- Create new provider instance via ProviderFactory
- Update agent configuration
- Handle errors with rollback
- Log provider switches

### 2. Ensure Provider Compatibility
Each provider should:
- Implement the BaseProvider interface consistently
- Handle tool calls in a compatible format
- Support message history preservation

### 3. Update ProviderFactory (Optional)
While the current implementation works, it could be enhanced to:
- Accept explicit provider names
- Better handle provider-specific model naming
- Provide model compatibility checking

## Expected Test Results

When fully implemented, all tests should pass with:
- ✅ 19 test methods passing
- ✅ 100% coverage of provider switching logic
- ✅ No warnings about missing implementations

## Notes for v0.1.1 Release

1. **Documentation**: Update agent documentation to include provider switching examples
2. **Examples**: Add provider switching examples to the examples directory
3. **Performance**: Consider caching provider instances for frequently used configurations
4. **Async Safety**: Ensure provider switches don't interfere with ongoing async operations
5. **Provider Discovery**: Consider adding a method to list available providers dynamically

## Future Enhancements

- **Provider Profiles**: Save and load provider configurations
- **Automatic Fallback**: Switch to backup provider on failures
- **Cost Tracking**: Track usage costs across different providers
- **Performance Metrics**: Compare response times between providers
- **Model Migration**: Helpers to migrate prompts between provider-specific formats
