# 5-Minute Quickstart

Get your first AI agent running in less than 5 minutes. No complex setup, no configuration files, just Python.

## Installation

```bash
pip install agenticraft
```

That's it. No additional dependencies to manually install.

## Your First Agent

### Step 1: Set Your API Key

```bash
export OPENAI_API_KEY="your-key-here"
```

Or create a `.env` file:
```bash
OPENAI_API_KEY=your-key-here
```

### Step 2: Create Your Agent

Create a file called `hello_agent.py`:

```python
from agenticraft import Agent

# Create a simple agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful AI assistant."
)

# Run the agent
response = agent.run("Tell me a fun fact about Python")
print(response.content)
```

### Step 3: Run It

```bash
python hello_agent.py
```

**Congratulations!** 🎉 You've just created your first AI agent.

## Adding Tools

Let's make your agent more capable by adding tools:

```python
from agenticraft import Agent, tool

# Define a simple tool
@tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    return eval(expression, {"__builtins__": {}}, {})

@tool
def get_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%I:%M %p")

# Create an agent with tools
agent = Agent(
    name="SmartAssistant",
    instructions="You are a helpful assistant with calculation and time abilities.",
    tools=[calculate, get_time]
)

# The agent will automatically use tools when needed
response = agent.run("What's 15% of 847? Also, what time is it?")
print(response.content)
```

## Understanding Agent Reasoning

One of AgentiCraft's core features is transparent reasoning:

```python
response = agent.run("Help me plan a birthday party for 20 people")

# See what the agent is thinking
print("=== Agent's Reasoning ===")
print(response.reasoning)

print("\n=== Final Response ===")
print(response.content)
```

## Creating a Simple Workflow

Chain multiple agents together:

```python
from agenticraft import Agent, Workflow, Step

# Create specialized agents
researcher = Agent(
    name="Researcher",
    instructions="You research topics thoroughly and provide detailed information."
)

writer = Agent(
    name="Writer", 
    instructions="You write engaging content based on research."
)

# Create a workflow
workflow = Workflow(name="content_creation")

# Add steps - no complex graphs needed!
workflow.add_steps([
    Step("research", agent=researcher, inputs=["topic"]),
    Step("write", agent=writer, depends_on=["research"])
])

# Run the workflow
result = await workflow.run(topic="The future of AI agents")
print(result["write"])
```

## Memory for Conversational Agents

Make your agents remember context:

```python
from agenticraft import Agent, ConversationMemory

agent = Agent(
    name="ChatBot",
    instructions="You are a friendly conversational AI.",
    memory=[ConversationMemory(max_turns=10)]
)

# First interaction
response1 = agent.run("My name is Alice")
print(response1.content)

# The agent remembers!
response2 = agent.run("What's my name?")
print(response2.content)  # Will correctly recall "Alice"
```

## Using Different LLM Providers

AgentiCraft supports multiple providers:

```python
# OpenAI (default)
agent = Agent(name="GPT4", model="gpt-4")

# Anthropic Claude
agent = Agent(name="Claude", model="claude-3-opus", api_key="anthropic-key")

# Google Gemini
agent = Agent(name="Gemini", model="gemini-pro", api_key="google-key")

# Local Ollama
agent = Agent(name="Local", model="ollama/llama2", base_url="http://localhost:11434")
```

## Next Steps

You've learned the basics! Here's what to explore next:

### Learn More
- [Core Concepts](concepts/agents.md) - Understand how agents work
- [Building Tools](concepts/tools.md) - Create powerful agent capabilities  
- [Designing Workflows](concepts/workflows.md) - Build complex systems

### See Examples
- [Hello World](examples/hello-world.md) - Simple agent examples
- [Provider Switching](examples/provider-switching.md) - Dynamic provider usage
- [Advanced Agents](examples/advanced-agents.md) - ReasoningAgent and WorkflowAgent

### Production Ready
- [Performance Tuning](guides/performance-tuning.md) - Optimize your agents
- [Best Practices](features/provider_switching.md) - Use providers effectively

## Quick Tips

!!! tip "Environment Variables"
    Create a `.env` file in your project root to manage API keys:
    ```
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    ```

!!! tip "Async Support"
    All agent operations support async/await:
    ```python
    response = await agent.arun("Your prompt")
    ```

!!! tip "Error Handling"
    AgentiCraft provides clear error messages:
    ```python
    try:
        response = agent.run("Do something")
    except AgentError as e:
        print(f"Agent error: {e}")
    ```

## Getting Help

- 💬 [Join our Discord](https://discord.gg/agenticraft)
- 🐛 [Report issues on GitHub](https://github.com/agenticraft/agenticraft/issues)
- 📚 [Read the full documentation](index.md)

---

**Ready for more?** Check out our [comprehensive examples](examples/index.md) or dive into the [API reference](reference/index.md).
