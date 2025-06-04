#!/usr/bin/env python3
"""
Simple chatbot example with memory
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
    
    print("ChatBot: Hello! I'm your AI assistant. Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'quit':
            print("ChatBot: Goodbye!")
            break
        
        response = await chatbot.arun(user_input)
        print(f"ChatBot: {response.content}")


if __name__ == "__main__":
    asyncio.run(main())
