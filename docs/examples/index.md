# Examples

Learn by example with practical AgentiCraft demonstrations.

## Quick Start Examples

### [Hello World](hello-world.md)
The simplest possible agent - perfect for getting started.

### [Basic Chat](hello-world.md#basic-chat)
Build a conversational AI in minutes.

## Feature Showcases

### [Provider Switching](provider-switching.md)
- Runtime provider changes
- Cost optimization strategies
- Automatic failover

### [Advanced Agents](advanced-agents.md)
- ReasoningAgent with transparent thinking
- WorkflowAgent for complex processes
- Combining agent types

## Real-World Applications

### [Customer Support Bot](real-world.md#customer-support)
Multi-provider support agent with knowledge base integration.

### [Data Analysis Pipeline](real-world.md#data-analysis)
Workflow agent that processes data through multiple stages.

### [Content Generator](real-world.md#content-generator)
ReasoningAgent that creates high-quality content with citations.

## Code Snippets

### Dynamic Model Selection
```python
# Use expensive model for complex tasks
if task.complexity > 0.7:
    agent.set_provider("anthropic", model="claude-3-opus-20240229")
else:
    agent.set_provider("ollama", model="llama2")
```

### Error Recovery
```python
try:
    response = agent.run(prompt)
except ProviderError:
    # Automatic failover
    agent.set_provider("ollama", model="llama2")
    response = agent.run(prompt)
```

### Tool Integration
```python
@tool
def search(query: str) -> str:
    """Search the web."""
    # Implementation
    
agent = Agent("SearchBot", tools=[search])
```

## Running the Examples

1. Clone the repository:
   ```bash
   git clone https://github.com/agenticraft/agenticraft
   cd agenticraft/examples
   ```

2. Install dependencies:
   ```bash
   pip install agenticraft
   ```

3. Set up API keys:
   ```bash
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   ```

4. Run examples:
   ```bash
   python hello_world.py
   python provider_switching/basic.py
   ```

## Contributing Examples

Have a cool use case? We'd love to see it! Share your examples on [GitHub](https://github.com/agenticraft/agenticraft).
