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

## [Upcoming]

### [0.1.1] - Week of 2025-06-11
- Complete Anthropic provider implementation
- Complete Ollama provider for local models
- PyPI package release
- Documentation website (docs.agenticraft.ai)
- Bug fixes from community feedback

### [0.2.0] - July 2025
- Streaming response support
- Advanced reasoning patterns
- Tool marketplace (beta)
- Performance optimizations
- Enhanced error messages

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
