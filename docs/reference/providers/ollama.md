# Ollama Provider Reference

The Ollama provider enables running LLMs locally with complete privacy and no API costs.

## Configuration

### Prerequisites

Install Ollama:
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### Start Ollama Service

```bash
# Start Ollama (required before using AgentiCraft)
ollama serve

# Pull models you want to use
ollama pull llama2        # 7B model (3.8GB)
ollama pull llama2:13b    # 13B model (7.3GB)
ollama pull mistral       # Fast alternative
ollama pull codellama     # For code generation
```

### Environment Variables

```bash
export OLLAMA_HOST="http://localhost:11434"  # Default
```

### Initialization

```python
from agenticraft import Agent

# IMPORTANT: Always set appropriate timeout for Ollama
agent = Agent(
    name="LocalBot",
    provider="ollama",
    model="llama2",      # or "llama2:latest"
    timeout=120          # 2 minutes - essential for CPU inference!
)

# Custom host
agent = Agent(
    name="RemoteBot",
    provider="ollama",
    model="mistral",
    base_url="http://192.168.1.100:11434",
    timeout=180
)
```

## ⚠️ Critical: Timeout Configuration

**Ollama requires longer timeouts than cloud providers**, especially on CPU:

```python
# ❌ This will likely timeout on CPU
agent = Agent(provider="ollama", model="llama2")  # Default timeout too short

# ✅ Always set explicit timeout
agent = Agent(
    provider="ollama",
    model="llama2",
    timeout=120,  # Minimum 2 minutes recommended
    max_tokens=100  # Limit response length for faster generation
)
```

### Timeout Guidelines

| Scenario | Recommended Timeout | Notes |
|----------|-------------------|-------|
| First run (model loading) | 300s (5 min) | Model loads into memory |
| Simple queries | 60-120s | Short prompts, limited tokens |
| Complex queries | 180-300s | Longer responses |
| GPU available | 30-60s | Much faster than CPU |

## Supported Models

| Model | Size | Command | Use Case |
|-------|------|---------|----------|
| `llama2` | 3.8GB | `ollama pull llama2` | General purpose |
| `llama2:13b` | 7.3GB | `ollama pull llama2:13b` | Better quality |
| `llama2:70b` | 40GB | `ollama pull llama2:70b` | Best quality |
| `mistral` | 4.1GB | `ollama pull mistral` | Fast, efficient |
| `codellama` | 3.8GB | `ollama pull codellama` | Code generation |
| `phi` | 1.6GB | `ollama pull phi` | Tiny, very fast |

## Performance Characteristics

### Expected Generation Times (CPU)

```python
# First request (model loading)
# Llama2 7B: 15-30 seconds to load
# Then: 1-5 tokens/second generation

# Subsequent requests (model in memory)
# Simple prompt (10-50 tokens): 5-15 seconds
# Medium prompt (100-200 tokens): 20-60 seconds
# Long prompt (500+ tokens): 2-5 minutes

# With GPU acceleration
# 5-10x faster than CPU
```

## ⚠️ Common Issues and Solutions

### Issue: Timeouts during normal operation

**Problem**: Default timeout too short for local inference
```python
# This often fails with timeout
agent = Agent(provider="ollama", model="llama2")
response = await agent.arun("Explain quantum computing")  # Timeout!
```

**Solution**: Set appropriate timeout and limit response length
```python
agent = Agent(
    provider="ollama",
    model="llama2",
    timeout=180,      # 3 minutes
    max_tokens=100    # Limit response length
)
```

### Issue: First request very slow

**Problem**: Model needs to load into memory (15-30 seconds)

**Solution**: Warm up the model
```python
async def warm_up_model():
    """Load model into memory with simple query"""
    agent = Agent(provider="ollama", model="llama2", timeout=300)
    await agent.arun("Hi")  # Simple query to load model
    print("Model loaded and ready!")

# Run warmup before main tasks
await warm_up_model()
```

### Issue: Inconsistent performance

**Problem**: System resources, model state affect performance

**Solution**: Add delays between requests
```python
import asyncio

# Process multiple queries with delays
queries = ["Question 1", "Question 2", "Question 3"]
for query in queries:
    response = await agent.arun(query)
    print(response.content)
    await asyncio.sleep(2)  # Give Ollama time to stabilize
```

## Configuration Options

```python
# Optimized configuration for local inference
agent = Agent(
    name="OptimizedOllama",
    provider="ollama",
    model="llama2",
    
    # Essential settings
    timeout=180,           # 3 minutes - adjust based on your hardware
    max_tokens=150,        # Limit response length for speed
    
    # Ollama-specific options
    temperature=0.7,       # 0.0-1.0
    top_p=0.9,            # Nucleus sampling
    top_k=40,             # Top-k sampling  
    repeat_penalty=1.1,   # Penalize repetition
    seed=42,              # Reproducible outputs
    
    # Advanced options (if needed)
    num_ctx=2048,         # Context window (default: 2048)
    num_gpu=1,            # GPU layers (if available)
    num_thread=8,         # CPU threads
)
```

## Performance Optimization

### Quick Responses Configuration

```python
# Optimized for speed
fast_agent = Agent(
    provider="ollama",
    model="llama2",
    timeout=60,
    temperature=0.1,    # Lower = faster
    max_tokens=50,      # Short responses
    top_k=10           # Restrict vocabulary
)

# Use for simple queries
response = await fast_agent.arun("What is 2+2?")
```

### Quality Responses Configuration

```python
# Optimized for quality (slower)
quality_agent = Agent(
    provider="ollama",
    model="llama2:13b",  # Larger model
    timeout=300,         # 5 minutes
    temperature=0.7,
    max_tokens=500,
    num_ctx=4096        # Larger context
)
```

### Batch Processing

```python
async def batch_process(queries: list, delay: float = 2.0):
    """Process multiple queries with delays"""
    agent = Agent(
        provider="ollama",
        model="llama2",
        timeout=120,
        max_tokens=100
    )
    
    results = []
    for i, query in enumerate(queries):
        print(f"Processing {i+1}/{len(queries)}...")
        try:
            response = await agent.arun(query)
            results.append(response.content)
        except Exception as e:
            results.append(f"Error: {e}")
        
        # Delay between requests
        if i < len(queries) - 1:
            await asyncio.sleep(delay)
    
    return results
```

## Best Practices

1. **Always set explicit timeout**: Minimum 120 seconds for CPU
2. **Limit response length**: Use `max_tokens` to control generation time
3. **Warm up models**: First request loads model into memory
4. **Add delays**: Space out requests to prevent overwhelming Ollama
5. **Monitor resources**: Check CPU/RAM usage during inference
6. **Use appropriate models**: Smaller models for speed, larger for quality

## Complete Working Example

```python
import asyncio
import time
from agenticraft import Agent

class LocalAssistant:
    def __init__(self):
        # Check if Ollama is running
        self._check_ollama()
        
        # Create agents for different purposes
        self.fast_agent = Agent(
            name="FastLocal",
            provider="ollama",
            model="llama2",
            timeout=90,
            temperature=0.1,
            max_tokens=50
        )
        
        self.balanced_agent = Agent(
            name="BalancedLocal",
            provider="ollama",
            model="llama2",
            timeout=180,
            temperature=0.7,
            max_tokens=200
        )
        
        # Warm up models
        print("Warming up models...")
        asyncio.run(self._warmup())
    
    def _check_ollama(self):
        """Verify Ollama is accessible"""
        import httpx
        try:
            response = httpx.get("http://localhost:11434/api/tags")
            print("✅ Ollama is running")
        except:
            raise Exception(
                "❌ Ollama not running. Start with: ollama serve"
            )
    
    async def _warmup(self):
        """Load models into memory"""
        try:
            await self.fast_agent.arun("Hi")
            print("✅ Models loaded")
        except Exception as e:
            print(f"⚠️  Warmup failed: {e}")
    
    async def quick_answer(self, question: str) -> str:
        """Fast responses for simple questions"""
        start = time.time()
        try:
            response = await self.fast_agent.arun(question)
            elapsed = time.time() - start
            print(f"⏱️  Response time: {elapsed:.1f}s")
            return response.content
        except Exception as e:
            return f"Error: {e}"
    
    async def detailed_response(self, prompt: str) -> str:
        """Detailed responses (slower)"""
        start = time.time()
        try:
            response = await self.balanced_agent.arun(prompt)
            elapsed = time.time() - start
            print(f"⏱️  Response time: {elapsed:.1f}s")
            return response.content
        except Exception as e:
            return f"Error: {e}"
    
    async def batch_queries(self, queries: list) -> list:
        """Process multiple queries efficiently"""
        results = []
        
        for i, query in enumerate(queries):
            print(f"\nProcessing {i+1}/{len(queries)}: {query[:50]}...")
            
            # Use fast agent for simple queries
            if len(query) < 50 and "?" in query:
                result = await self.quick_answer(query)
            else:
                result = await self.detailed_response(query)
            
            results.append(result)
            
            # Delay between requests
            if i < len(queries) - 1:
                await asyncio.sleep(2)
        
        return results

# Usage example
async def main():
    print("🦙 Local LLM Assistant")
    print("=" * 50)
    
    # Initialize assistant
    assistant = LocalAssistant()
    
    # Quick questions
    print("\n📌 Quick Answers:")
    quick_q = [
        "What is 2+2?",
        "Capital of France?",
        "Define CPU"
    ]
    
    for q in quick_q:
        answer = await assistant.quick_answer(q)
        print(f"Q: {q}")
        print(f"A: {answer}\n")
        await asyncio.sleep(1)
    
    # Detailed response
    print("\n📌 Detailed Response:")
    detailed = await assistant.detailed_response(
        "Explain the benefits of running AI models locally"
    )
    print(f"Response: {detailed[:200]}...")
    
    # Batch processing
    print("\n📌 Batch Processing:")
    batch = [
        "What is RAM?",
        "Explain how neural networks work",
        "List 3 programming languages"
    ]
    results = await assistant.batch_queries(batch)
    
    for q, r in zip(batch, results):
        print(f"\nQ: {q}")
        print(f"A: {r[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting Guide

### Debugging Timeout Issues

```python
async def debug_ollama():
    """Diagnose Ollama performance issues"""
    import httpx
    
    print("🔍 Ollama Diagnostics")
    print("=" * 40)
    
    # Check connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])
            print(f"✅ Connected. Models: {len(models)}")
            for model in models:
                print(f"   - {model['name']} ({model['size'] / 1e9:.1f}GB)")
    except:
        print("❌ Cannot connect to Ollama")
        return
    
    # Test performance
    timeouts = [30, 60, 120, 180]
    for timeout in timeouts:
        print(f"\n⏱️  Testing {timeout}s timeout...")
        agent = Agent(
            provider="ollama",
            model="llama2",
            timeout=timeout,
            max_tokens=10
        )
        
        try:
            start = time.time()
            await agent.arun("Say hello")
            elapsed = time.time() - start
            print(f"   ✅ Success in {elapsed:.1f}s")
        except Exception as e:
            print(f"   ❌ Failed: {type(e).__name__}")

# Run diagnostics if having issues
await debug_ollama()
```

## Hardware Recommendations

| Model Size | Minimum RAM | Recommended RAM | GPU Recommended |
|------------|-------------|-----------------|-----------------|
| 2-3B (phi) | 4GB | 8GB | No |
| 7B (llama2) | 8GB | 16GB | Yes |
| 13B | 16GB | 32GB | Yes |
| 70B | 64GB | 128GB | Required |

## See Also

- [Agent API](../agent.md) - Core agent functionality
- [WorkflowAgent Guide](../../concepts/workflows.md) - Tool usage patterns
- [Performance Tuning](../../guides/performance-tuning.md) - Optimization tips
- [Ollama Docs](https://github.com/ollama/ollama) - Official Ollama documentation
