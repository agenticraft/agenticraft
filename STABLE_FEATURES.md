# AgentiCraft Stable Features

This document lists the production-ready features in AgentiCraft v0.2.0-alpha that are stable and recommended for use.

## ✅ Stable Core Features

### 1. Basic Agent Creation
```python
from agenticraft import Agent

agent = Agent(
    name="Assistant",
    instructions="You are a helpful AI assistant."
)
response = await agent.arun("Hello!")
```
**Status**: ✅ Stable | Well-tested | Production-ready

### 2. Tool System
```python
from agenticraft import tool

@tool
def calculate(expression: str) -> float:
    """Calculate a mathematical expression."""
    return eval(expression)

agent = Agent(name="Calculator", tools=[calculate])
```
**Status**: ✅ Stable | Extensive testing | Clear API

### 3. Provider Support
- **OpenAI** (GPT-3.5, GPT-4): ✅ Stable
- **Anthropic** (Claude): ✅ Stable
- **Ollama** (Local models): ✅ Stable

```python
# Provider switching
agent.set_provider("anthropic", model="claude-3-opus-20240229")
```
**Status**: ✅ Stable | All providers tested

### 4. Basic Workflows
```python
from agenticraft import Workflow, Step

workflow = Workflow(name="DataPipeline")
workflow.add_step(Step("fetch", fetch_data))
workflow.add_step(Step("process", process_data))
workflow.add_step(Step("save", save_data))
```
**Status**: ✅ Stable | Core functionality solid

### 5. Streaming Responses
```python
async for chunk in agent.stream("Tell me a story"):
    print(chunk.content, end="")
```
**Status**: ✅ Stable | Works with all providers

## ⚠️ Beta Features (Use with Caution)

### 1. Reasoning Patterns
- Chain of Thought: ⚠️ Beta
- Tree of Thoughts: ⚠️ Beta
- ReAct: ⚠️ Beta

### 2. Memory Systems
- Vector Memory: ⚠️ Beta
- Conversation Memory: ⚠️ Beta

### 3. Basic Telemetry
- OpenTelemetry integration: ⚠️ Beta
- Metrics collection: ⚠️ Beta

## 🚧 Experimental Features (Not for Production)

### 1. Protocol Support
- MCP (Model Context Protocol): 🚧 Experimental
- A2A (Agent-to-Agent): 🚧 Experimental
- Protocol Fabric: 🚧 Experimental

### 2. Security Features
- Sandboxing: 🚧 Experimental
- RBAC: 🚧 Experimental

### 3. Advanced Features
- Multi-agent orchestration: 🚧 Experimental
- Plugin marketplace: 🚧 Experimental
- Mesh networking: 🚧 Experimental

## 📋 Feature Stability Matrix

| Feature | Stability | Tests | Docs | Production Use |
|---------|-----------|-------|------|----------------|
| Basic Agents | ✅ Stable | ✅ | ✅ | ✅ Recommended |
| Tools | ✅ Stable | ✅ | ✅ | ✅ Recommended |
| Provider Switching | ✅ Stable | ✅ | ✅ | ✅ Recommended |
| Workflows | ✅ Stable | ✅ | ✅ | ✅ Recommended |
| Streaming | ✅ Stable | ✅ | ✅ | ✅ Recommended |
| Reasoning | ⚠️ Beta | ⚠️ | ⚠️ | ⚠️ Test First |
| Memory | ⚠️ Beta | ⚠️ | ⚠️ | ⚠️ Test First |
| Telemetry | ⚠️ Beta | ⚠️ | ✅ | ⚠️ Test First |
| Protocols | 🚧 Experimental | 🚧 | 🚧 | ❌ Not Ready |
| Security | 🚧 Experimental | 🚧 | 🚧 | ❌ Not Ready |

## 🎯 Recommended Usage

### For Production Applications
Stick to stable features:
```python
from agenticraft import Agent, tool

# ✅ This is stable and production-ready
agent = Agent(
    name="ProductionBot",
    model="gpt-4",
    temperature=0.7
)

@tool
def safe_operation(data: str) -> str:
    return f"Processed: {data}"

agent.tools.append(safe_operation)
response = await agent.arun("Process this data")
```

### For Experimentation
Enable experimental features explicitly:
```python
# 🚧 Experimental - not for production
from agenticraft.experimental import enable_features
enable_features("protocols", "security")

from agenticraft.experimental.protocols import MCPClient
```

## 📅 Stability Roadmap

### v0.2.0 (Current)
- Core features stable
- Beta features in testing
- Experimental features available

### v0.3.0 (Q1 2025)
- Reasoning patterns → Stable
- Memory systems → Stable
- Basic telemetry → Stable

### v1.0.0 (Target: Q2 2025)
- All current beta features → Stable
- Selected experimental features → Beta
- Production deployments supported

---

*Last Updated: November 2024*
*Refer to this document when choosing features for your application*
