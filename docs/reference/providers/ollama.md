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
# Start Ollama
ollama serve

# Pull models you want to use
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

### Environment Variables

```bash
export OLLAMA_HOST="http://localhost:11434"  # Default
export OLLAMA_TIMEOUT="300"  # Timeout in seconds
```

### Initialization

```python
from agenticraft import Agent

# Explicit provider required for Ollama
agent = Agent(
    name="LocalBot",
    provider="ollama",
    model="llama2"
)

# Custom host
agent = Agent(
    name="RemoteBot",
    provider="ollama",
    model="mistral",
    base_url="http://192.168.1.100:11434"
)
```

## Supported Models

| Model | Size | Description | Best For |
|-------|------|-------------|----------|
| `llama2` | 7B | Meta's Llama 2 | General purpose |
| `llama2:13b` | 13B | Larger Llama 2 | Better quality |
| `llama2:70b` | 70B | Largest Llama 2 | Best quality |
| `mistral` | 7B | Mistral AI model | Fast, efficient |
| `mixtral` | 8x7B | MoE model | High quality |
| `codellama` | 7B | Code-focused | Programming tasks |
| `phi-2` | 2.7B | Microsoft's small model | Resource-constrained |
| `neural-chat` | 7B | Intel's fine-tuned | Conversational |
| `starling-lm` | 7B | Berkeley's model | Instruction following |

## Provider-Specific Features

### Model Management

```python
from agenticraft.providers.ollama import OllamaProvider

# List available models
provider = OllamaProvider()
models = provider.list_models()
for model in models:
    print(f"{model['name']}: {model['size']}")

# Pull a new model
provider.pull_model("llama2:13b")

# Delete a model
provider.delete_model("old-model")
```

### Custom Models

Load custom GGUF models:

```python
# Create custom modelfile
modelfile = """
FROM ./my-model.gguf
PARAMETER temperature 0.8
PARAMETER top_p 0.9
SYSTEM You are a helpful assistant.
"""

# Create model
provider.create_model("my-custom-model", modelfile)

# Use it
agent = Agent(
    name="CustomBot",
    provider="ollama",
    model="my-custom-model"
)
```

### Embedding Models

```python
# Use embedding models
agent = Agent(
    name="EmbeddingBot",
    provider="ollama",
    model="nomic-embed-text",
    task="embedding"
)

embeddings = agent.embed(["text1", "text2", "text3"])
```

### Streaming

```python
agent = Agent(
    name="StreamBot",
    provider="ollama",
    model="llama2",
    stream=True
)

# Stream responses
for chunk in agent.run_stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

## Configuration Options

```python
agent = Agent(
    name="ConfiguredOllama",
    provider="ollama",
    model="llama2",
    
    # Ollama-specific options
    temperature=0.8,        # 0.0-1.0
    top_p=0.9,             # Nucleus sampling
    top_k=40,              # Top-k sampling
    repeat_penalty=1.1,    # Penalize repetition
    seed=42,               # Reproducible outputs
    num_predict=2048,      # Max tokens to generate
    num_ctx=4096,          # Context window size
    num_batch=512,         # Batch size for prompt eval
    num_gpu=1,             # GPUs to use
    main_gpu=0,            # Main GPU
    low_vram=False,        # Low VRAM mode
    f16_kv=True,           # Use f16 for K,V cache
    vocab_only=False,      # Only load vocabulary
    use_mmap=True,         # Use memory mapping
    use_mlock=False,       # Lock model in memory
    
    # Connection settings
    timeout=300,           # Request timeout
    keep_alive="5m"        # Keep model loaded
)
```

## Performance Optimization

### GPU Acceleration

```python
# Use GPU acceleration
agent = Agent(
    name="GPUBot",
    provider="ollama",
    model="llama2",
    num_gpu=1  # Number of GPU layers
)

# Check GPU usage
info = agent.get_model_info()
print(f"GPU layers: {info.get('gpu_layers')}")
```

### Memory Management

```python
# Low memory configuration
agent = Agent(
    name="LowMemBot",
    provider="ollama",
    model="phi-2",  # Smaller model
    num_ctx=2048,   # Smaller context
    num_batch=256,  # Smaller batch
    low_vram=True   # Enable low VRAM mode
)
```

### Model Preloading

```python
# Keep model loaded in memory
agent = Agent(
    name="FastBot",
    provider="ollama",
    model="mistral",
    keep_alive="30m"  # Keep loaded for 30 minutes
)

# Preload model
agent.preload()
```

## Privacy Features

### Fully Offline Operation

```python
class PrivateAssistant:
    def __init__(self):
        # Ensure Ollama is running locally
        self.agent = Agent(
            name="PrivateBot",
            provider="ollama",
            model="llama2",
            base_url="http://localhost:11434"
        )
        
        # Verify no external connections
        self.agent.verify_local_only = True
    
    def process_sensitive_data(self, data: str):
        """Process data with complete privacy."""
        # Data never leaves your machine
        return self.agent.run(f"Analyze this confidential data: {data}")
```

### Custom Privacy Models

```python
# Create a privacy-focused model
modelfile = """
FROM llama2
PARAMETER temperature 0.7
SYSTEM You are a privacy-focused assistant. Never ask for or store personal information.
"""

provider = OllamaProvider()
provider.create_model("privacy-llama", modelfile)
```

## Best Practices

1. **Model Selection**: Choose model size based on available resources
2. **Resource Management**: Monitor CPU/GPU usage and memory
3. **Context Length**: Adjust context size to fit your hardware
4. **Batch Processing**: Use appropriate batch sizes for your system
5. **Model Caching**: Keep frequently used models loaded

## Complete Example

```python
import psutil
from agenticraft import Agent, tool
from typing import Dict

class LocalAssistant:
    def __init__(self):
        # Check system resources
        self._check_resources()
        
        # Select model based on available resources
        model = self._select_model()
        
        self.agent = Agent(
            name="LocalAssistant",
            provider="ollama",
            model=model,
            temperature=0.7,
            num_ctx=4096,
            num_gpu=1 if self._has_gpu() else 0,
            tools=self._create_tools()
        )
    
    def _check_resources(self):
        """Check available system resources."""
        ram = psutil.virtual_memory().total / (1024**3)  # GB
        print(f"Available RAM: {ram:.1f} GB")
        
        try:
            import torch
            if torch.cuda.is_available():
                print(f"GPU available: {torch.cuda.get_device_name()}")
        except ImportError:
            print("No GPU detected")
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _select_model(self) -> str:
        """Select model based on resources."""
        ram = psutil.virtual_memory().total / (1024**3)
        
        if ram >= 32:
            return "llama2:13b"  # 13B model
        elif ram >= 16:
            return "llama2"      # 7B model
        else:
            return "phi-2"       # 2.7B model
    
    def _create_tools(self):
        @tool
        def system_info() -> str:
            """Get current system information."""
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            return f"CPU: {cpu}%, RAM: {ram}%"
        
        @tool
        def read_local_file(path: str) -> str:
            """Read a local file."""
            try:
                with open(path, 'r') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        
        return [system_info, read_local_file]
    
    def chat(self, message: str) -> str:
        """Process a chat message locally."""
        response = self.agent.run(message)
        return response.content
    
    def analyze_file(self, file_path: str, analysis_type: str = "summary"):
        """Analyze a local file privately."""
        prompt = f"""
        Please {analysis_type} the following file content:
        
        {self.agent.run(f"Read file: {file_path}").content}
        
        Provide a detailed {analysis_type}.
        """
        
        return self.agent.run(prompt).content
    
    def switch_model(self, model: str):
        """Switch to a different local model."""
        try:
            # Test if model is available
            test_agent = Agent(
                name="Test",
                provider="ollama",
                model=model
            )
            test_agent.run("test")
            
            # Switch main agent
            self.agent.model = model
            print(f"Switched to {model}")
        except Exception as e:
            print(f"Model {model} not available: {e}")
            print("Run: ollama pull {model}")

# Usage
assistant = LocalAssistant()

# Private conversation
response = assistant.chat("Help me analyze my personal finances")
print(response)

# Analyze local files
analysis = assistant.analyze_file(
    "/path/to/document.txt",
    analysis_type="detailed summary"
)

# Switch models based on task
assistant.switch_model("codellama")  # For coding tasks
code = assistant.chat("Write a Python function to sort a list")
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Ensure Ollama is running
   ollama serve
   ```

2. **Model Not Found**
   ```bash
   # Pull the model first
   ollama pull llama2
   ```

3. **Out of Memory**
   - Use smaller models (phi-2, tinyllama)
   - Reduce context size
   - Enable low_vram mode

4. **Slow Generation**
   - Enable GPU acceleration
   - Use smaller models
   - Reduce context window

## Model Recommendations

| Use Case | Recommended Model | Min RAM |
|----------|------------------|---------|
| General chat | llama2 (7B) | 8GB |
| Code generation | codellama | 8GB |
| Fast responses | mistral | 8GB |
| Resource-constrained | phi-2 | 4GB |
| High quality | llama2:13b | 16GB |
| Best quality | llama2:70b | 64GB |

## See Also

- [Agent API](../agent.md) - Core agent functionality
- [Provider Switching](../../features/provider_switching.md) - Dynamic provider changes
- [Ollama Docs](https://github.com/ollama/ollama) - Official Ollama documentation
