# Changelog

All notable changes to AgentiCraft will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-06-04 (Initial Release)

### Added
- 🎯 Core Framework (<2000 lines of code)
  - Base `Agent` class with reasoning transparency
  - `@tool` decorator for easy tool creation
  - Simple workflow engine for multi-step processes
  - Plugin architecture for extensibility
  - Two memory types: `ConversationMemory` and `KnowledgeMemory`

- 🧠 Reasoning Transparency
  - Every agent exposes its thought process
  - Access reasoning via `response.reasoning`
  - Understand tool selection and execution order
  - Build trust through transparency

- 🔌 MCP Protocol Support
  - First-class Model Context Protocol implementation
  - MCP server and client
  - Tool registry with automatic discovery
  - WebSocket and HTTP transports

- 📊 Built-in Observability
  - OpenTelemetry integration from day one
  - Automatic tracing of agent operations
  - Metrics collection (tokens, latency, errors)
  - Ready for production monitoring

- 🛠️ Tools & Integrations
  - OpenAI provider (fully implemented)
  - Essential tools: calculator, file operations, web requests
  - Tool execution with error handling
  - Async-first design

- 📚 Documentation & Examples
  - Comprehensive quickstart guide
  - Philosophy and design principles
  - 15+ working examples
  - API reference (auto-generated)
  - Production templates (FastAPI, CLI)

- 🧪 Quality Assurance
  - 40+ test files
  - Unit and integration tests
  - GitHub Actions CI/CD
  - Pre-commit hooks

### Known Limitations
- Anthropic and Ollama providers planned for v0.1.1
- Streaming responses coming in v0.2.0
- Advanced memory strategies in development
- PyPI package coming soon (install from GitHub for now)

### Breaking Changes
- Initial release - all APIs should be considered beta

### Security
- No known security issues
- Sandboxed tool execution planned for v0.2.0

## [0.1.1] - 2025-06-11

### Added
- 🔄 **Dynamic Provider Switching**
  - Runtime provider switching with `agent.set_provider()`
  - Automatic provider detection from model names
  - Explicit provider specification in Agent configuration
  - Rollback support on provider switch failures
  - Provider information retrieval with `get_provider_info()`
  - List available providers with `list_available_providers()`

- 🤖 **New LLM Providers**
  - **Anthropic Provider** - Full support for Claude 3 models
    - Claude 3 Opus, Sonnet, and Haiku models
    - Streaming support with proper chunk handling
    - Tool calling with Anthropic's format
    - System message handling
    - 96.58% test coverage
  - **Ollama Provider** - Run open-source models locally
    - Support for Llama 2, Mistral, CodeLlama, Phi-2, Neural-chat, and more
    - Model management (list, pull, check availability)
    - Custom server configuration
    - Automatic model pulling when not available
    - 94.00% test coverage

- 🧠 **Advanced Agent Types**
  - **ReasoningAgent** - Transparent thought process exposure
    - Step-by-step reasoning traces
    - Thought process visibility
    - Decision tracking
    - 96.82% test coverage
  - **WorkflowAgent** - Optimized for multi-step workflows
    - Parallel step execution
    - Conditional branching
    - Retry mechanisms
    - Workflow state management
    - 94.43% test coverage

- 📦 **PyPI Package**
  - Official package: `pip install agenticraft`
  - Automated release pipeline
  - Version management

- 📚 **Enhanced Documentation**
  - Provider switching guide with examples
  - Migration guide from v0.1.0 to v0.1.1
  - Performance optimization guide
  - 15+ new example scripts
  - API reference updates

- 🧪 **Improved Testing**
  - 691 tests passing
  - >95% coverage for all new features
  - Integration tests for cross-provider compatibility
  - Performance benchmarks

### Changed
- Agent configuration now accepts `provider` parameter
- Improved error messages for provider-related issues
- Enhanced provider factory with better caching

### Fixed
- ReasoningAgent context argument handling
- WorkflowAgent condition evaluation logic
- WorkflowAgent retry mechanism
- Provider validation in tests
- Tool execution format consistency

### Performance
- Provider switching overhead: <50ms
- No memory leaks when switching providers
- Connection pooling for high-throughput scenarios

## [0.2.0-alpha] - 2025-06-16

### Added
- 🌊 **Streaming Support**
  - Native streaming for all providers (OpenAI, Anthropic, Ollama)
  - Real-time token-by-token responses with <100ms latency
  - Unified streaming interface across providers
  - Interrupt handling and partial response recovery
  - Visual streaming examples with progress indicators

- 🧠 **Advanced Reasoning Patterns**
  - Chain of Thought (CoT) - Step-by-step reasoning with confidence scores
  - Tree of Thoughts (ToT) - Explore multiple reasoning paths in parallel
  - ReAct Pattern - Reasoning combined with tool actions
  - Transparent reasoning traces for all patterns
  - Side-by-side pattern comparison examples

- 🔌 **Model Context Protocol (MCP)**
  - First-class MCP support for tool interoperability
  - WebSocket-based MCP client and server implementations
  - Seamless tool discovery and execution
  - Bridge between MCP tools and AgentiCraft agents
  - Compatible with Anthropic's MCP ecosystem

- 📊 **Production Telemetry**
  - OpenTelemetry integration with <1% performance overhead
  - Distributed tracing for multi-agent workflows
  - Prometheus metrics export
  - Jaeger and OTLP exporter support
  - Production-ready observability from day one

- 🔧 **Enhanced Workflows**
  - Visual workflow design with Mermaid diagrams
  - ASCII workflow visualization for terminals
  - Parallel step execution with dependency management
  - Workflow state persistence and resumption
  - Error handling and retry mechanisms

- 💾 **Advanced Memory Systems**
  - Vector memory with ChromaDB integration
  - Semantic search across conversation history
  - Knowledge graph memory for relationships
  - Hybrid memory combining vector and graph approaches
  - Memory persistence across sessions

- 🛍️ **Plugin Marketplace Foundation**
  - Plugin discovery and loading system
  - Standardized plugin interface
  - Tool sharing capabilities
  - Foundation for future marketplace UI

- 📚 **Documentation & Examples**
  - 50+ comprehensive examples covering all features
  - Streaming examples with visual progress
  - Reasoning pattern demonstrations
  - MCP integration guides
  - Production deployment templates
  - Interactive tutorials

### Changed
- Streaming API now uses async iterators exclusively
- ReasoningAgent replaces ChainOfThoughtAgent
- Memory interface standardized across all types
- Tool decorator signature updated for MCP compatibility

### Fixed
- Fixed OpenAI provider initialization without API key
- Fixed tracer context injection/extraction
- Resolved workflow step ordering issues
- Fixed memory search with special characters
- Corrected streaming interruption handling

### Performance
- Optimized provider initialization
- Reduced memory footprint for base agents
- Faster tool execution with caching
- Efficient streaming buffer management

## [Unreleased]

### [1.0.0] - Q4 2025
- Stable API guarantee
- Enterprise features
- Cloud deployment helpers
- GUI for agent building
- Comprehensive security audit

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to AgentiCraft.

## Reporting Issues

Found a bug? Please report it on our [issue tracker](https://github.com/agenticraft/agenticraft/issues).
