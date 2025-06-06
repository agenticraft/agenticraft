# Changelog

All notable changes to AgentiCraft will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-06-11

### 🚀 Features

#### Dynamic Provider Switching
- Switch between LLM providers at runtime without recreating agents
- New `set_provider()` method for instant provider changes
- `get_provider_info()` to check current provider details
- `list_available_providers()` to discover available options
- Explicit provider selection via `provider` parameter

#### New LLM Providers
- **Anthropic Claude** - Access to Opus, Sonnet, and Haiku models
- **Ollama** - Run models locally (Llama2, Mistral, CodeLlama, and more)

#### Advanced Agent Types
- **ReasoningAgent** - Transparent thought process with explainable AI
- **WorkflowAgent** - Optimized for complex multi-step processes

### ⚡ Performance
- Provider switching overhead < 50ms
- Connection pooling for high-throughput scenarios
- Optimized provider initialization and caching

### 📚 Documentation
- Comprehensive feature guides
- Real-world examples and use cases
- Complete API reference
- Performance optimization guide

### 🔧 Developer Experience
- Improved error messages for provider issues
- Better type hints and IDE support
- Enhanced debugging capabilities

---

## [Upcoming]

### Planned Features
- Unified streaming interface across all providers
- Automatic model selection based on task complexity
- Built-in cost tracking and usage analytics
- Provider configuration profiles
- Enhanced tool calling standardization
