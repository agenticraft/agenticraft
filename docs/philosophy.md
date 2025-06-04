# Philosophy

AgentiCraft is built on strong principles that guide every design decision. Understanding our philosophy helps you get the most out of the framework.

## Core Principles

### 1. Simplicity First 🎯

> "Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away." - Antoine de Saint-Exupéry

Every feature in AgentiCraft must pass the simplicity test:
- Can it be explained in one sentence?
- Can a developer use it without reading docs?
- Does it solve a real problem?

If the answer to any of these is "no", it doesn't belong in core.

**Example**: Creating an agent
```python
# This is all you need
agent = Agent(name="assistant")
```

### 2. Transparent by Default 🧠

AI agents shouldn't be black boxes. Developers need to understand:
- What the agent is thinking
- Why it made certain decisions
- How it arrived at its response

**Example**: Reasoning visibility
```python
response = agent.run("Complex question")
print(response.reasoning)  # Always available
```

### 3. Production-Ready from Day One 📊

Demos are easy. Production is hard. AgentiCraft bridges this gap:
- Built-in observability
- Error handling that makes sense
- Templates for common use cases
- Performance considerations baked in

### 4. Developer Joy 💜

Writing agent code should be enjoyable:
- Intuitive APIs that feel natural
- Clear error messages that help, not frustrate
- Excellent documentation with real examples
- Fast feedback loops

### 5. Extensible, Not Bloated 🔧

The core stays small (<2000 lines), but the possibilities are endless:
- Plugin architecture for custom needs
- Standard interfaces for interoperability
- Community-driven ecosystem

## Design Decisions

### Why Not Graph-Based Workflows?

Many frameworks use complex graph structures for workflows. We chose simplicity:

```python
# AgentiCraft way - simple and clear
workflow.add_steps([
    Step("research", agent=researcher),
    Step("write", agent=writer, depends_on=["research"])
])

# Not the AgentiCraft way - unnecessary complexity
workflow.add_node("research", ResearchNode())
workflow.add_edge("research", "write", condition=lambda x: x.success)
```

Graphs are powerful but rarely necessary. Our step-based approach handles 95% of use cases with 10% of the complexity.

### Why Only Two Memory Types?

Other frameworks offer 5+ memory types:
- Short-term memory
- Long-term memory
- Episodic memory
- Semantic memory
- Procedural memory

We provide just two:
1. **ConversationMemory** - Recent interactions
2. **KnowledgeMemory** - Persistent facts

Why? Because that's all you need in practice. Additional complexity doesn't improve outcomes.

### Why Reasoning Patterns Matter

LLMs can reason, but they need structure. We provide patterns, not prompts:

```python
from agenticraft import Agent, ChainOfThought

agent = Agent(
    name="Analyst",
    reasoning_pattern=ChainOfThought()  # Structured thinking
)
```

This ensures consistent, high-quality reasoning across all agents.

## What We're NOT Building

Being clear about what we won't build is as important as what we will:

### ❌ NOT Another LangChain

LangChain is powerful but complex. We're building something different:
- Simpler APIs
- Smaller core
- Clearer abstractions
- Better developer experience

### ❌ NOT a Kitchen Sink

We resist the temptation to add every possible feature:
- No 20 different memory types
- No complex graph visualizations
- No unnecessary abstractions
- No features "just in case"

### ❌ NOT a Research Project

This is production software:
- Stability over novelty
- Reliability over impressiveness
- Documentation over demos
- Real use cases over paper citations

## Community Values

### Open Source, Open Community

- **Contributions welcome** - But simplicity is non-negotiable
- **Feedback valued** - Users shape the roadmap
- **Transparency default** - Development happens in the open

### Quality Over Quantity

- **Better 10 excellent tools than 100 mediocre ones**
- **Better clear docs than extensive ones**
- **Better stable API than feature-rich**

### Pragmatism Wins

- **Real-world usage drives decisions**
- **Production experience matters**
- **Developer time is valuable**

## The AgentiCraft Way

When building with AgentiCraft, ask yourself:

1. **Is this the simplest solution?**
2. **Can I understand what's happening?**
3. **Will this work in production?**
4. **Am I enjoying this?**

If you answer "yes" to all four, you're doing it the AgentiCraft way.

## Future Vision

As AgentiCraft grows, these principles remain constant:

- **Core stays small** - Complexity lives in plugins
- **APIs stay simple** - Power through composition
- **Reasoning stays transparent** - No black boxes
- **Production stays first** - Real-world focus

## Join Us

If these principles resonate with you:

- ⭐ [Star the project](https://github.com/agenticraft/agenticraft)
- 💬 [Join the discussion](https://discord.gg/agenticraft)
- 🛠️ [Contribute code](https://github.com/agenticraft/agenticraft/contribute)
- 📝 [Share your story](https://github.com/agenticraft/agenticraft/discussions)

Together, we're making AI agent development accessible to every developer.

---

*"Make it simple. Make it transparent. Make it work."* - The AgentiCraft Motto
