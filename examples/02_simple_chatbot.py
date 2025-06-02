"""
Simple chatbot example with memory
"""

import asyncio
from agenticraft import ChatAgent


async def main():
    # Create a chatbot with memory
    chatbot = ChatAgent(name="ChatBot", memory=True)
    
    print("ChatBot: Hello! I'm your AI assistant. Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'quit':
            print("ChatBot: Goodbye!")
            break
        
        response = await chatbot.chat(user_input)
        print(f"ChatBot: {response}")


if __name__ == "__main__":
    asyncio.run(main())
