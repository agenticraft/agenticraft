# AgentiCraft Reasoning Examples

This directory contains comprehensive examples demonstrating AgentiCraft's advanced reasoning patterns: Chain of Thought, Tree of Thoughts, and ReAct.

## 🚀 Quick Start

```bash
# Interactive launcher - easiest way to start
python quickstart.py

# Or run the simple demo (no API required)
python reasoning_demo.py
```

## 📚 Example Files

### 1. **reasoning_demo.py** - No API Required
Perfect introduction to all three reasoning patterns. Shows how each pattern works conceptually without needing any API keys.

```bash
python reasoning_demo.py
```

### 2. **chain_of_thought.py** - Step-by-Step Reasoning
Demonstrates linear, sequential reasoning perfect for:
- Mathematical calculations
- Logical analysis
- Step-by-step problem solving
- Process optimization

```bash
python chain_of_thought.py
```

### 3. **tree_of_thoughts.py** - Exploratory Reasoning
Shows how to explore multiple solution paths for:
- Creative design problems
- Strategic planning
- Optimization challenges
- Multi-option comparisons

```bash
python tree_of_thoughts.py
```

### 4. **react.py** - Action-Oriented Reasoning
Combines thinking with action for:
- Research tasks
- System troubleshooting
- Data analysis
- Decision support

```bash
python react.py
```

### 5. **pattern_comparison.py** - Side-by-Side Comparison
Compares all three patterns on the same problems to help you understand when to use each one.

```bash
python pattern_comparison.py
```

### 6. **production_handlers.py** - Production-Ready Patterns
Real-world examples showing how to implement reasoning patterns in production systems:
- Customer support system
- Code review assistant
- Data analysis pipeline
- Strategic decision support

```bash
python production_handlers.py
```

### 7. **reasoning_transparency.py** - Understanding AI Thinking
Demonstrates how to access and visualize the agent's reasoning process:
- View step-by-step thought traces
- Understand tool usage decisions
- Debug reasoning failures
- Build trust through transparency
- Learn from AI problem-solving

```bash
python reasoning_transparency.py
```

### 8. **sustainability_reasoning_example.py** - Sustainability Analysis
Shows how reasoning patterns can be applied to sustainability and environmental challenges.

```bash
python sustainability_reasoning_example.py
```

## 🎯 Reasoning Patterns Overview

### Chain of Thought (CoT)
**Best for**: Problems with clear sequential steps
- ✓ Mathematical calculations
- ✓ Logical deductions
- ✓ Process analysis
- ✓ Step-by-step explanations

**How it works**: Breaks down complex problems into sequential steps, building confidence through each stage.

### Tree of Thoughts (ToT)
**Best for**: Problems with multiple valid approaches
- ✓ Creative design
- ✓ Strategic planning
- ✓ Optimization problems
- ✓ Exploring alternatives

**How it works**: Explores multiple solution paths simultaneously, evaluating and pruning to find the optimal approach.

### ReAct
**Best for**: Problems requiring external information or iteration
- ✓ Research tasks
- ✓ Troubleshooting
- ✓ Data gathering
- ✓ Validation and testing

**How it works**: Alternates between thinking and acting, using tools to gather information and refine solutions.

## 🔧 Setup Options

### Option 1: No Setup Required (Mock Mode)
All examples work without API keys! They use simulated responses to demonstrate the patterns.

```bash
python reasoning_demo.py  # Start here!
```

### Option 2: OpenAI
```bash
export OPENAI_API_KEY="your-key-here"
python chain_of_thought.py
```

### Option 3: Anthropic
```bash
export ANTHROPIC_API_KEY="your-key-here"
python tree_of_thoughts.py
```

### Option 4: Local Models (Ollama)
```bash
# Install and start Ollama
ollama pull llama2
ollama serve

# Run examples (no API key needed)
python react.py
```

## 📖 Pattern Selection Guide

| Problem Type | Recommended Pattern | Example Use Case |
|-------------|-------------------|------------------|
| Mathematical | Chain of Thought | Calculate ROI, solve equations |
| Creative | Tree of Thoughts | Design UI, create content |
| Research | ReAct | Find information, validate data |
| Analytical | Chain of Thought | Debug code, analyze metrics |
| Strategic | Tree of Thoughts | Business planning, optimization |
| Investigative | ReAct | Troubleshoot issues, gather facts |
| Business Decisions | Tree of Thoughts | Market entry, product strategy |
| Compliance | Chain of Thought | Step-by-step verification |
| Customer Support | Pattern varies | Depends on issue complexity |

## 💼 Real-World Business Applications

### Startup Decision Making
```python
# Using Tree of Thoughts for exploring startup ideas
explorer = ReasoningAgent(
    reasoning_pattern="tree_of_thoughts",
    pattern_config={"max_depth": 3, "beam_width": 4}
)
response = await explorer.think_and_act(
    "What's the best SaaS startup for the healthcare market?"
)
```

### Market Research
```python
# Using ReAct for data-driven decisions
researcher = ReasoningAgent(
    reasoning_pattern="react",
    tools=[MarketDataTool(), CostCalculatorTool()]
)
response = await researcher.think_and_act(
    "Analyze the sustainable fashion market opportunity"
)
```

### Problem Diagnosis
```python
# Using Chain of Thought for systematic analysis
analyst = ReasoningAgent(
    reasoning_pattern="chain_of_thought",
    pattern_config={"min_confidence": 0.8}
)
response = await analyst.think_and_act(
    "Why did our conversion rate drop 30% last month?"
)
```

## 🏭 Production Usage

For production applications, see `production_handlers.py` which demonstrates:
- Clean handler pattern (no decorator issues)
- Automatic pattern selection
- Error handling and fallbacks
- Performance tracking
- Extensible architecture

### Key Production Patterns

1. **Handler Pattern** (Recommended)
```python
def my_handler(agent, step, context):
    # Tool logic here
    result = perform_operation(context.get("input"))
    context["output"] = result
    return f"Completed: {result}"

agent.register_handler("my_tool", my_handler)
```

2. **Pattern Selection Logic**
```python
def select_pattern(problem: str) -> str:
    problem_lower = problem.lower()
    if any(word in problem_lower for word in ["calculate", "compute", "step"]):
        return "chain_of_thought"
    elif any(word in problem_lower for word in ["design", "create", "options"]):
        return "tree_of_thoughts"
    elif any(word in problem_lower for word in ["find", "search", "research"]):
        return "react"
    return "chain_of_thought"  # default
```

3. **Error Handling**
```python
try:
    response = await agent.think_and_act(problem, timeout=30)
except TimeoutError:
    # Fall back to simpler pattern
    response = await simple_agent.think_and_act(problem)
```

## 🧪 Testing Your Setup

```bash
# Test all examples
python quickstart.py
# Then choose 'test'

# Or check your environment
python -c "import agenticraft; print('✅ AgentiCraft installed')"
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test specific pattern
python -c "
from agenticraft.agents.reasoning import ReasoningAgent
agent = ReasoningAgent(reasoning_pattern='chain_of_thought')
print('✅ Reasoning patterns available')
"
```

## 💡 Tips and Best Practices

1. **Start Simple**: Begin with `reasoning_demo.py` to understand the patterns
2. **Compare Patterns**: Use `pattern_comparison.py` to see differences
3. **Mock First**: Test with mock mode before using API keys
4. **Production Ready**: Study `production_handlers.py` for real-world usage
5. **Combine Patterns**: Consider hybrid approaches for complex problems
6. **Monitor Performance**: Track pattern effectiveness over time
7. **Handle Timeouts**: Set appropriate timeouts for each pattern
8. **Cache Results**: For expensive reasoning operations

## ⚠️ Common Pitfalls and Solutions

### Tool Integration Issues
**Problem**: `@tool` decorator causing issues with WorkflowAgent  
**Solution**: Use the handler pattern shown in `production_handlers.py`

### Pattern Selection
**Problem**: Using wrong pattern for the task  
**Solution**: Start with `pattern_comparison.py` to understand strengths

### Performance
**Problem**: Tree of Thoughts taking too long  
**Solution**: Reduce `max_depth` and `beam_width` parameters

### API Timeouts
**Problem**: Complex reasoning hitting API timeouts  
**Solution**: Break into smaller sub-problems or increase timeout

## 🐛 Troubleshooting

### "AgentiCraft not installed"
```bash
cd /path/to/agenticraft
pip install -e .
```

### "No API keys found"
- Examples work without API keys (mock mode)
- Or set up keys using `python quickstart.py` → 'setup'

### "Import errors"
- Ensure you're in the right directory
- Check Python version (3.8+ required)

### "Provider not available"
- Check API key is set correctly
- For Ollama: ensure `ollama serve` is running
- Try mock mode first

## 📊 Performance Considerations

| Pattern | Typical Time | Token Usage | Best For |
|---------|-------------|-------------|----------|
| Chain of Thought | 0.5-2s | Low-Medium | Quick analysis |
| Tree of Thoughts | 2-10s | High | Complex decisions |
| ReAct | Variable | Medium-High | Data gathering |

## 📚 Learn More

- **Conceptual Overview**: Start with `reasoning_demo.py`
- **Deep Dive**: Each example file has detailed inline documentation
- **Production Patterns**: See `production_handlers.py`
- **Pattern Selection**: Check `pattern_comparison.py`
- **API Documentation**: See `/docs/api/reasoning/`
- **Feature Guide**: See `/docs/features/reasoning_patterns.md`

## 🎉 Next Steps

1. Run `python quickstart.py` for interactive exploration
2. Try each pattern on your own problems
3. Experiment with different providers (OpenAI, Anthropic, Ollama)
4. Build your own reasoning applications!
5. Share your experiences and contribute examples!

Happy reasoning! 🧠✨
