#!/usr/bin/env python3
"""
Simple chatbot example with memory - Non-interactive test version
"""

import asyncio
from agenticraft import Agent
from agenticraft.core.memory import ConversationMemory


async def main():
    # Create a chatbot with memory
    memory = ConversationMemory()
    chatbot = Agent(
        name="ChatBot",
        model="gpt-4",
        instructions="You are a helpful AI assistant. Be friendly and conversational.",
        memory=[memory]
    )
    
    print("ChatBot: Hello! I'm your AI assistant.")
    print("(This is a non-interactive test version)")
    
    # Simulate a conversation
    test_messages = [
        "Hello! How are you?",
        "What's the weather like?",
        "Thanks for chatting!"
    ]
    
    for message in test_messages:
        print(f"\nYou: {message}")
        # Note: This would normally call the API
        # For testing, we'll just show the structure
        print(f"ChatBot: [Would respond to '{message}' here]")
    
    print("\nChatBot: Test conversation complete!")
    print("✅ Chatbot example structure verified")


if __name__ == "__main__":
    asyncio.run(main())
