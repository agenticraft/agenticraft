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

### 📝 Documentation Updates (2025-06-08)
- **Provider Documentation Overhaul**
  - Added critical warnings about parameter configuration limitations
  - Documented Anthropic model specification requirements
  - Comprehensive Ollama timeout configuration guide
  - Working examples for all providers tested and verified
  - Troubleshooting sections with specific error solutions
  - Performance expectations and hardware recommendations
- **Configuration Guide Updates**
  - Clear DO/DON'T patterns for each provider
  - Timeout configuration matrix
  - Error prevention strategies
  - Best practices based on real-world testing

---

## [0.2.0] - 2025-06-12 (In Development)

#### Enhanced Workflows
- **Workflow Visualization** - Multiple formats (Mermaid, ASCII, JSON, HTML)
  - Real-time progress overlay
  - Interactive HTML with zoom/pan
  - Export capabilities
- **Workflow Patterns** - Pre-built patterns for common scenarios
  - Parallel execution with concurrency control
  - Conditional branching with if/else logic
  - Retry loops with exponential backoff
  - Map-reduce for data processing
  - Sequential pipelines with error handling
- **Workflow Templates** - Production-ready templates
  - Research workflows with multiple sources
  - Content creation pipelines
  - Data processing ETL pipelines
  - Multi-agent collaboration workflows
- **Enhanced WorkflowAgent**
  - Visual planning with AI assistance
  - Checkpoint/resume capability
  - Real-time progress streaming
  - Dynamic workflow modification
  - Automatic parallelization

#### Advanced Reasoning Patterns
- **Chain of Thought (CoT)** - Step-by-step reasoning with confidence tracking
  - Automatic alternative generation for low-confidence steps
  - Problem complexity assessment
  - Structured thought decomposition
- **Tree of Thoughts (ToT)** - Multi-path exploration and evaluation
  - Configurable beam width and exploration depth
  - Branch scoring and pruning
  - Visual tree representation
- **ReAct Pattern** - Combines reasoning with tool actions
  - Thought → Action → Observation cycles
  - Progress reflection and self-correction
  - Integrated tool execution

#### Pattern Selection
- Automatic pattern selection based on query analysis
- Manual pattern override support
- Pattern-specific configuration options
- Seamless integration with ReasoningAgent

### ⚡ Performance
- CoT: ~50ms for simple problems, ~150ms for complex
- ToT: ~200ms for simple, ~500ms for complex (with exploration)
- ReAct: ~100ms baseline + tool execution time
- Confidence tracking adds <5% overhead

### 📚 Documentation
- Comprehensive API reference for all patterns
- Integration guide with real-world examples
- Migration guide from basic reasoning
- Quick reference for pattern selection
- Performance optimization strategies

### 🔧 Developer Experience
- Rich reasoning step structure with metadata
- Pattern-specific debugging information
- Visualization support for reasoning trees
- Async/await support throughout

---

## [Upcoming]

### Planned Features
- Unified streaming interface across all providers
- MCP (Model Context Protocol) integration
- Enhanced workflow engine with visual builder
- OpenTelemetry integration for observability
- Advanced memory systems (vector and graph)
- Tool marketplace foundation
