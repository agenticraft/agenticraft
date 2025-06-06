# Provider Switching Examples

Dynamic provider switching is a powerful AgentiCraft feature that lets you optimize for cost, performance, and availability.

## Basic Provider Switching

```python
from agenticraft import Agent

# Create an agent
agent = Agent(name="FlexBot", model="gpt-4")

# Use OpenAI for creative tasks
creative_response = agent.run("Write a creative story opening")
print(f"GPT-4: {creative_response}")

# Switch to Claude for analysis
agent.set_provider("anthropic", model="claude-3-opus-20240229")
analysis_response = agent.run("Analyze the themes in the previous story")
print(f"Claude: {analysis_response}")

# Switch to local Ollama for simple tasks
agent.set_provider("ollama", model="llama2")
summary_response = agent.run("Summarize in one sentence")
print(f"Llama2: {summary_response}")
```

## Cost Optimization

Use expensive models only when needed:

```python
from agenticraft import Agent

class SmartAgent:
    def __init__(self):
        self.agent = Agent(name="CostOptimizer", model="gpt-3.5-turbo")
        
    def run(self, prompt: str, complexity: str = "simple"):
        if complexity == "complex":
            # Use powerful model for complex tasks
            self.agent.set_provider("anthropic", model="claude-3-opus-20240229")
        elif complexity == "simple":
            # Use efficient model for simple tasks
            self.agent.set_provider("ollama", model="llama2")
        else:
            # Default to balanced option
            self.agent.set_provider("openai", model="gpt-3.5-turbo")
            
        return self.agent.run(prompt)

# Usage
smart = SmartAgent()
smart.run("Count to 10", complexity="simple")  # Uses Llama2
smart.run("Explain quantum computing", complexity="complex")  # Uses Claude
```

## Automatic Failover

Handle provider failures gracefully:

```python
from agenticraft import Agent, ProviderError
import time

class ResilientAgent:
    def __init__(self):
        self.agent = Agent(name="Resilient", model="gpt-4")
        self.providers = [
            ("openai", "gpt-4"),
            ("anthropic", "claude-3-opus-20240229"),
            ("ollama", "llama2")
        ]
        
    def run_with_failover(self, prompt: str):
        for provider, model in self.providers:
            try:
                self.agent.set_provider(provider, model)
                return self.agent.run(prompt)
            except ProviderError as e:
                print(f"Provider {provider} failed: {e}")
                continue
        raise Exception("All providers failed")

# Usage
resilient = ResilientAgent()
response = resilient.run_with_failover("Hello world")
```

## Performance-Based Switching

Switch providers based on response time:

```python
from agenticraft import Agent
import time

class PerformanceAgent:
    def __init__(self):
        self.agent = Agent(name="SpeedyBot", model="gpt-4")
        self.provider_stats = {}
        
    def run_with_timing(self, prompt: str):
        providers = [
            ("openai", "gpt-3.5-turbo"),
            ("anthropic", "claude-3-haiku-20240307"),
            ("ollama", "llama2")
        ]
        
        fastest_time = float('inf')
        fastest_provider = None
        fastest_response = None
        
        for provider, model in providers:
            try:
                self.agent.set_provider(provider, model)
                start = time.time()
                response = self.agent.run(prompt)
                elapsed = time.time() - start
                
                if elapsed < fastest_time:
                    fastest_time = elapsed
                    fastest_provider = (provider, model)
                    fastest_response = response
                    
                print(f"{provider}: {elapsed:.2f}s")
            except:
                continue
                
        # Use fastest provider for subsequent calls
        if fastest_provider:
            self.agent.set_provider(*fastest_provider)
            
        return fastest_response
```

## Task-Specific Providers

Different providers for different tasks:

```python
from agenticraft import Agent

class TaskRouter:
    def __init__(self):
        self.agent = Agent(name="TaskBot", model="gpt-4")
        
        # Define task-to-provider mapping
        self.task_providers = {
            "code": ("openai", "gpt-4"),
            "creative": ("anthropic", "claude-3-opus-20240229"),
            "chat": ("ollama", "llama2"),
            "analysis": ("anthropic", "claude-3-sonnet-20240229"),
            "translation": ("openai", "gpt-3.5-turbo")
        }
    
    def run_task(self, task_type: str, prompt: str):
        if task_type in self.task_providers:
            provider, model = self.task_providers[task_type]
            self.agent.set_provider(provider, model)
        
        return self.agent.run(prompt)

# Usage
router = TaskRouter()
router.run_task("code", "Write a Python function to sort a list")
router.run_task("creative", "Write a poem about the ocean")
router.run_task("chat", "How's the weather?")
```

## Provider Information

Check current provider and available options:

```python
from agenticraft import Agent

agent = Agent(name="InfoBot", model="gpt-4")

# Get current provider info
info = agent.get_provider_info()
print(f"Current provider: {info['provider']}")
print(f"Current model: {info['model']}")

# List all available providers
providers = agent.list_available_providers()
print(f"Available providers: {providers}")

# Switch and verify
agent.set_provider("anthropic", model="claude-3-opus-20240229")
new_info = agent.get_provider_info()
print(f"Switched to: {new_info['provider']} - {new_info['model']}")
```

## Complete Example: Smart Assistant

```python
#!/usr/bin/env python3
\"\"\"
Smart assistant that optimizes provider usage
\"\"\"

from agenticraft import Agent, ProviderError
import time

class SmartAssistant:
    def __init__(self):
        self.agent = Agent(name="SmartAssistant", model="gpt-3.5-turbo")
        self.usage_cost = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.001,
            "claude-3-opus-20240229": 0.025,
            "claude-3-sonnet-20240229": 0.003,
            "llama2": 0.0  # Free local model
        }
        
    def estimate_complexity(self, prompt: str) -> float:
        \"\"\"Estimate prompt complexity (0-1).\"\"\"
        factors = {
            "explain": 0.3,
            "analyze": 0.4,
            "create": 0.3,
            "simple": -0.2,
            "complex": 0.3,
            "detailed": 0.2
        }
        
        complexity = 0.5  # Base complexity
        prompt_lower = prompt.lower()
        
        for keyword, weight in factors.items():
            if keyword in prompt_lower:
                complexity += weight
                
        return max(0, min(1, complexity))
    
    def select_provider(self, prompt: str, max_cost: float = 0.01):
        \"\"\"Select optimal provider based on task and budget.\"\"\"
        complexity = self.estimate_complexity(prompt)
        
        if complexity > 0.7 and max_cost >= 0.025:
            return ("anthropic", "claude-3-opus-20240229")
        elif complexity > 0.5 and max_cost >= 0.003:
            return ("openai", "gpt-4")
        elif complexity > 0.3:
            return ("openai", "gpt-3.5-turbo")
        else:
            return ("ollama", "llama2")
    
    def run(self, prompt: str, max_cost: float = 0.01):
        provider, model = self.select_provider(prompt, max_cost)
        
        try:
            self.agent.set_provider(provider, model)
            response = self.agent.run(prompt)
            cost = self.usage_cost.get(model, 0)
            
            return {
                "response": response,
                "provider": provider,
                "model": model,
                "estimated_cost": cost
            }
        except ProviderError:
            # Fallback to local model
            self.agent.set_provider("ollama", model="llama2")
            return {
                "response": self.agent.run(prompt),
                "provider": "ollama",
                "model": "llama2",
                "estimated_cost": 0
            }

# Usage
assistant = SmartAssistant()

prompts = [
    "What's 2+2?",
    "Explain the theory of relativity",
    "Write a complex business strategy",
    "Translate 'hello' to Spanish"
]

for prompt in prompts:
    result = assistant.run(prompt)
    print(f"\nPrompt: {prompt}")
    print(f"Provider: {result['provider']} ({result['model']})")
    print(f"Cost: ${result['estimated_cost']}")
    print(f"Response: {result['response'][:100]}...")
```

## Best Practices

1. **Cache provider instances** when switching frequently
2. **Handle provider-specific errors** gracefully
3. **Monitor costs** when using expensive models
4. **Test failover scenarios** in development
5. **Log provider switches** for debugging

## Next Steps

- [Explore advanced agents](advanced-agents.md)
- [Learn about performance tuning](../guides/performance-tuning.md)
- [Build real-world applications](real-world.md)
