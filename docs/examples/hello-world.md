# Hello World

Welcome to AgentiCraft! Let's start with the simplest possible agent.

## Your First Agent

```python
from agenticraft import Agent

# Create an agent
agent = Agent(name="HelloBot", model="gpt-4")

# Run it!
response = agent.run("Say hello to AgentiCraft!")
print(response)
```

Output:
```
Hello AgentiCraft! 🚀 I'm excited to be your AI assistant powered by this amazing framework!
```

## Basic Chat

Build a simple interactive chatbot:

```python
from agenticraft import Agent

# Create a conversational agent
agent = Agent(
    name="ChatBot",
    model="gpt-4",
    memory_enabled=True  # Remember conversation context
)

print("ChatBot: Hello! I'm your AI assistant. Type 'quit' to exit.")

while True:
    user_input = input("You: ")
    if user_input.lower() == 'quit':
        break
    
    response = agent.run(user_input)
    print(f"ChatBot: {response}")
```

## Adding Personality

```python
from agenticraft import Agent

# Create an agent with personality
agent = Agent(
    name="FriendlyBot",
    model="gpt-4",
    system_prompt="You are a friendly, helpful assistant who loves using emojis and being encouraging!"
)

response = agent.run("I'm learning Python")
print(response)
# Output: That's fantastic! 🎉 Python is an amazing language to learn! 🐍 ...
```

## Using Different Providers

```python
from agenticraft import Agent

# Try different providers
providers = [
    ("openai", "gpt-4"),
    ("anthropic", "claude-3-opus-20240229"),
    ("ollama", "llama2")
]

prompt = "Write a haiku about coding"

for provider, model in providers:
    try:
        agent = Agent(name=f"{provider}-poet", provider=provider, model=model)
        response = agent.run(prompt)
        print(f"\n{provider.upper()} ({model}):")
        print(response)
    except Exception as e:
        print(f"Skipping {provider}: {e}")
```

## Next Steps

Now that you've created your first agent:
- [Add tools to your agent](../concepts/tools.md)
- [Try provider switching](provider-switching.md)
- [Explore advanced agents](advanced-agents.md)

## Complete Example

Here's a complete example you can save and run:

```python
#!/usr/bin/env python3
\"\"\"
hello_world.py - Your first AgentiCraft agent
\"\"\"

from agenticraft import Agent

def main():
    # Create an agent
    agent = Agent(
        name="HelloBot",
        model="gpt-4",
        temperature=0.7
    )
    
    # Test various prompts
    prompts = [
        "Introduce yourself",
        "What's 2+2?",
        "Tell me a joke",
        "Explain AgentiCraft in one sentence"
    ]
    
    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        response = agent.run(prompt)
        print(f"Response: {response}")

if __name__ == "__main__":
    main()
```

Save this as `hello_world.py` and run:
```bash
python hello_world.py
```

Happy coding with AgentiCraft! 🚀
