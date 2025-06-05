"""Example: Using Ollama provider with AgentiCraft.

This example demonstrates how to use the Ollama provider for running
local LLMs with AgentiCraft. Ollama enables running open-source models
like Llama 2, Mistral, and CodeLlama on your own hardware.

Requirements:
    1. Install Ollama: https://ollama.ai
    2. Start Ollama: ollama serve
    3. Pull a model: ollama pull llama2
    4. Install AgentiCraft: pip install agenticraft
"""

import asyncio
import os
from typing import List, Dict, Any

from agenticraft import Agent
from agenticraft.providers.ollama import OllamaProvider
from agenticraft.tools import Tool


# Example 1: Basic Usage
async def basic_example():
    """Basic example using Ollama provider."""
    print("=== Basic Ollama Example ===")
    
    # Create provider explicitly
    provider = OllamaProvider(
        base_url="http://localhost:11434",  # Default Ollama URL
        model="llama2"
    )
    
    # Create agent with provider
    agent = Agent("Local Assistant", provider=provider)
    
    # Simple query
    response = await agent.run("What are the benefits of running LLMs locally?")
    print(f"Response: {response}")


# Example 2: Using Different Models
async def model_selection_example():
    """Example showing different Ollama models."""
    print("\n=== Model Selection Example ===")
    
    # List available models first
    provider = OllamaProvider()
    try:
        models = await provider.list_models()
        print("Available models:")
        for model in models:
            print(f"  - {model['name']} ({model.get('size', 0) / 1e9:.1f}GB)")
    except Exception as e:
        print(f"Could not list models: {e}")
    
    # Using Llama 2 (general purpose)
    llama_agent = Agent(model="ollama/llama2")
    response = await llama_agent.run("Explain quantum computing in one sentence.")
    print(f"\nLlama 2: {response}")
    
    # Using CodeLlama (code generation)
    # Note: You need to pull this first: ollama pull codellama
    try:
        code_agent = Agent(model="ollama/codellama")
        response = await code_agent.run("Write a Python function to calculate factorial.")
        print(f"\nCodeLlama:\n{response}")
    except Exception as e:
        print(f"\nCodeLlama not available: {e}")
        print("Pull it with: ollama pull codellama")
    
    # Using Mistral (efficient and powerful)
    # Note: You need to pull this first: ollama pull mistral
    try:
        mistral_agent = Agent(model="ollama/mistral")
        response = await mistral_agent.run("What's the capital of France?")
        print(f"\nMistral: {response}")
    except Exception as e:
        print(f"\nMistral not available: {e}")
        print("Pull it with: ollama pull mistral")


# Example 3: Custom Server Configuration
async def custom_server_example():
    """Example with custom Ollama server configuration."""
    print("\n=== Custom Server Example ===")
    
    # Connect to Ollama on a different host/port
    provider = OllamaProvider(
        base_url="http://localhost:11434",  # Change if running elsewhere
        timeout=600  # Longer timeout for slower hardware
    )
    
    agent = Agent("Remote Ollama", provider=provider)
    
    try:
        response = await agent.run("Hello! Are you running locally?")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running with: ollama serve")


# Example 4: Performance Optimization
async def performance_example():
    """Example showing performance optimization techniques."""
    print("\n=== Performance Example ===")
    
    # Use smaller, faster models for quick responses
    fast_provider = OllamaProvider(
        model="phi",  # Microsoft's small but capable model
        timeout=30    # Shorter timeout for fast models
    )
    
    # Temperature and max_tokens affect performance
    agent = Agent("Fast Local", provider=fast_provider)
    
    try:
        response = await agent.run(
            "List 3 programming languages",
            temperature=0.1,  # Lower temperature = more deterministic
            max_tokens=50     # Limit response length
        )
        print(f"Fast response: {response}")
    except Exception as e:
        print(f"Phi model not available: {e}")
        print("Pull it with: ollama pull phi")


# Example 5: Long-Form Generation
async def long_form_example():
    """Example of long-form content generation."""
    print("\n=== Long-Form Generation Example ===")
    
    provider = OllamaProvider(
        model="llama2",
        timeout=600  # Longer timeout for long generations
    )
    
    agent = Agent("Story Writer", provider=provider)
    
    response = await agent.run(
        "Write a short story about a robot learning to paint (100 words max)",
        temperature=0.8,  # Higher temperature for creativity
        max_tokens=200    # Allow longer response
    )
    print(f"Story:\n{response}")


# Example 6: Code Generation with CodeLlama
async def code_generation_example():
    """Example of code generation using CodeLlama."""
    print("\n=== Code Generation Example ===")
    
    try:
        provider = OllamaProvider(model="codellama")
        agent = Agent(
            "Code Generator",
            provider=provider,
            system_prompt="You are an expert programmer. Write clean, efficient, well-commented code."
        )
        
        response = await agent.run("""
        Write a Python class for a simple todo list with methods to:
        - Add a task
        - Mark task as complete
        - List all tasks
        - Remove a task
        """)
        print(f"Generated Code:\n{response}")
    except Exception as e:
        print(f"CodeLlama not available: {e}")
        print("Install with: ollama pull codellama")


# Example 7: Multi-Turn Conversation
async def conversation_example():
    """Example of maintaining conversation context."""
    print("\n=== Conversation Example ===")
    
    provider = OllamaProvider(model="llama2")
    agent = Agent("Conversationalist", provider=provider)
    
    # Simulate a conversation about a topic
    messages = [
        "I'm interested in learning about space exploration.",
        "What was the first satellite launched into space?",
        "When was it launched?",
        "What country launched it?"
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        response = await agent.run(message)
        print(f"Assistant: {response}")


# Example 8: Error Handling and Fallbacks
async def error_handling_example():
    """Example of proper error handling with Ollama."""
    print("\n=== Error Handling Example ===")
    
    # Try to use a model that might not be available
    provider = OllamaProvider(model="gpt2")  # This likely isn't pulled
    agent = Agent("Test Agent", provider=provider)
    
    try:
        response = await agent.run("Hello!")
        print(f"Success: {response}")
    except Exception as e:
        print(f"Error with gpt2: {e}")
        
        # Fallback to a model that should be available
        print("\nFalling back to llama2...")
        fallback_agent = Agent(model="ollama/llama2")
        try:
            response = await fallback_agent.run("Hello!")
            print(f"Fallback success: {response}")
        except Exception as e:
            print(f"Ollama not running? Error: {e}")
            print("Start Ollama with: ollama serve")


# Example 9: Tool Usage Simulation
async def tool_simulation_example():
    """Example simulating tool usage with Ollama.
    
    Note: Ollama doesn't have native tool support yet, but we can
    simulate it with prompt engineering.
    """
    print("\n=== Tool Simulation Example ===")
    
    provider = OllamaProvider(model="llama2")
    agent = Agent(
        "Tool User",
        provider=provider,
        system_prompt="""You have access to these tools:
        - calculator: Performs mathematical calculations
        - weather: Gets current weather for a location
        
        To use a tool, respond with:
        TOOL_CALL: {"name": "tool_name", "arguments": {...}}
        
        Then provide your response based on the tool result."""
    )
    
    response = await agent.run("What's 25 * 4?")
    print(f"Response: {response}")
    
    # In a real implementation, you'd parse TOOL_CALL from the response
    # and execute the appropriate tool


# Example 10: Model Management
async def model_management_example():
    """Example of managing Ollama models."""
    print("\n=== Model Management Example ===")
    
    provider = OllamaProvider()
    
    # List current models
    try:
        models = await provider.list_models()
        print(f"Currently installed: {len(models)} models")
        
        # Check if specific model is available
        model_names = [m['name'] for m in models]
        if 'llama2' not in model_names:
            print("\nLlama2 not found. Pulling it...")
            # Uncomment to actually pull:
            # await provider.pull_model("llama2")
            print("(Simulated pull - uncomment to actually download)")
        else:
            print("Llama2 is available!")
            
    except Exception as e:
        print(f"Error accessing Ollama: {e}")


async def main():
    """Run all examples."""
    print("🤖 AgentiCraft Ollama Provider Examples")
    print("=" * 50)
    print("\n⚠️  Prerequisites:")
    print("1. Install Ollama: https://ollama.ai")
    print("2. Start Ollama: ollama serve")
    print("3. Pull a model: ollama pull llama2")
    print("\nPress Ctrl+C to skip slow examples\n")
    
    # Check if Ollama is running
    provider = OllamaProvider()
    try:
        provider.validate_auth()
        print("✅ Ollama is running!")
    except Exception as e:
        print(f"❌ Ollama not accessible: {e}")
        print("Please start Ollama with: ollama serve")
        return
    
    # Run examples
    examples = [
        basic_example,
        model_selection_example,
        custom_server_example,
        performance_example,
        long_form_example,
        code_generation_example,
        conversation_example,
        error_handling_example,
        tool_simulation_example,
        model_management_example
    ]
    
    for example in examples:
        try:
            await example()
            print("\n" + "-" * 50)
        except KeyboardInterrupt:
            print("\n⏭️  Skipping to next example...")
            continue
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(main())
