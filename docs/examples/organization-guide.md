# AgentiCraft Examples Organization Guide

## Overview

This guide helps you organize and test the AgentiCraft v0.2.0 examples, keeping only the most valuable and up-to-date ones.

## 🌟 High-Value Examples to Keep

### Core Examples
1. **`quickstart_5min.py`** - Perfect 5-minute introduction
2. **`demo_working_features.py`** - Quick validation of all v0.2.0 features
3. **`quick_feature_test.py`** - Rapid functionality check

### Feature-Specific Examples

#### Streaming (New in v0.2.0)
- `streaming/basic_streaming.py` - Foundation of streaming
- `streaming/multi_provider_stream.py` - Provider compatibility
- `streaming/practical_streaming.py` - Real-world applications
- `streaming/visual_streaming.py` - UI integration

#### Reasoning Patterns (New in v0.2.0)
- `reasoning/chain_of_thought_example.py` - Step-by-step reasoning
- `reasoning/tree_of_thoughts_example.py` - Exploring multiple paths
- `reasoning/react_example.py` - Thought-Action-Observation loops
- `reasoning/pattern_comparison.py` - When to use each pattern

#### Workflows (Enhanced in v0.2.0)
- `workflows/visualization_example.py` - Mermaid/ASCII visualization
- `workflows/patterns_example.py` - Parallel, conditional, retry patterns
- `workflows/templates_example.py` - Ready-to-use workflow templates
- `workflows/simple_workflow.py` - Basic workflow concepts

#### Memory Systems (New in v0.2.0)
- `memory/vector_memory_clean.py` - ChromaDB integration
- `memory/knowledge_graph_clean.py` - Graph-based memory

#### MCP Protocol (New in v0.2.0)
- Keep entire `mcp/` directory - Critical for tool standardization

#### Other Valuable Examples
- `agents/combined_agents_example.py` - Multi-agent coordination
- `05_tools_showcase.py` - Comprehensive tool integration
- `telemetry/` - Production observability examples
- `marketplace/` - Plugin system examples

## 🗑️ Examples to Remove

### Outdated/Basic
- `01_hello_world.py` - Too basic for v0.2.0
- `02_simple_chatbot.py` - Superseded by advanced examples
- `02_simple_chatbot_test.py` - Test file, not an example

### Redundant Workflow Files
Consolidate these into one example:
- `workflows/enhanced_agent_example_complete.py`
- `workflows/enhanced_agent_example_fixed.py` 
- `workflows/enhanced_agent_example_patched.py`
- `workflows/run_enhanced_example_fixed.py`
- `workflows/workflow_agent_patch.py`

### Test/Mock Files
- `streaming/mock_streaming.py` - Just for testing

## 🧪 Testing Strategy

### Quick Test
Run the automated test script:
```bash
python examples/test_examples.py
```

This will:
1. Check all dependencies
2. Test priority examples in order
3. Report any failures
4. Suggest cleanup actions

### Manual Testing Order
1. **Core Features** (5 min)
   ```bash
   python examples/quickstart_5min.py
   python examples/demo_working_features.py
   ```

2. **New v0.2.0 Features** (15 min)
   ```bash
   # Streaming
   python examples/streaming/basic_streaming.py
   
   # Reasoning
   python examples/reasoning/chain_of_thought_example.py
   
   # Memory
   python examples/memory/vector_memory_example.py
   
   # MCP
   python examples/mcp/basic_example.py
   ```

3. **Advanced Features** (10 min)
   ```bash
   # Workflows
   python examples/workflows/visualization_example.py
   
   # Multi-agent
   python examples/agents/combined_agents_example.py
   ```

## 📋 Checklist

### Before Testing
- [ ] Install AgentiCraft: `pip install agenticraft`
- [ ] Set API key: `export OPENAI_API_KEY='your-key'`
- [ ] Install optional deps: `python examples/install_optional_deps.py`

### Testing Priority
- [ ] Core examples work
- [ ] Streaming examples run
- [ ] Reasoning patterns execute
- [ ] Memory examples store/retrieve
- [ ] Workflow visualization generates diagrams
- [ ] MCP server starts

### Cleanup
- [ ] Remove outdated examples
- [ ] Consolidate redundant files
- [ ] Update example README files

## 🎯 Value Criteria

Examples are kept based on:
1. **Educational Value** - Clearly demonstrates a concept
2. **Feature Coverage** - Shows v0.2.0 capabilities
3. **Practical Use** - Solves real problems
4. **Code Quality** - Well-written and documented
5. **Uniqueness** - Not duplicated elsewhere

## 📁 Final Structure

After cleanup, your examples directory should have:
```
examples/
├── quickstart_5min.py          # Start here!
├── demo_working_features.py    # Feature overview
├── test_examples.py           # Test runner
├── streaming/                 # 4-5 examples
├── reasoning/                 # 4-5 examples  
├── workflows/                 # 4-5 examples
├── memory/                    # 2 examples
├── mcp/                       # All examples
├── agents/                    # 2-3 examples
├── telemetry/                 # Keep all
├── marketplace/               # Keep all
└── providers/                 # Provider-specific
```

Total: ~40 high-quality examples (down from 50+)

## 🚀 Next Steps

1. Run `test_examples.py` to validate examples
2. Remove redundant files
3. Try the examples that interest you most
4. Build something amazing with AgentiCraft v0.2.0!
