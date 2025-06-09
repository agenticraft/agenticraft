"""Practical streaming use cases for AgentiCraft.

This example demonstrates real-world applications of streaming:
- Interactive chat interface
- Document processing with progress
- Multi-step task execution
- Error recovery during streaming
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from agenticraft import Agent
from agenticraft.core.streaming import (
    create_mock_stream,
)


@dataclass
class ChatMessage:
    """Simple chat message structure."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = None
    streaming: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class StreamingChatInterface:
    """A simple streaming chat interface."""

    def __init__(self, agent_name: str = "ChatBot", use_mock: bool = True):
        """Initialize the chat interface."""
        self.messages: list[ChatMessage] = []
        self.use_mock = use_mock

        if not use_mock:
            self.agent = Agent(
                name=agent_name,
                instructions="You are a helpful chat assistant. Keep responses concise and friendly.",
                model="gpt-4",
            )
        else:
            self.agent = None

    def display_message(self, message: ChatMessage):
        """Display a chat message."""
        role_symbol = "👤" if message.role == "user" else "🤖"
        role_color = (
            "\033[34m" if message.role == "user" else "\033[32m"
        )  # Blue for user, green for assistant
        reset_color = "\033[0m"

        timestamp = message.timestamp.strftime("%H:%M:%S")
        print(
            f"\n{role_color}{role_symbol} {message.role.title()} [{timestamp}]:{reset_color}"
        )

        if message.streaming:
            return  # Content will be streamed
        else:
            print(message.content)

    async def stream_response(self, prompt: str) -> str:
        """Stream a response from the agent."""
        # Create assistant message
        assistant_msg = ChatMessage(role="assistant", content="", streaming=True)
        self.messages.append(assistant_msg)
        self.display_message(assistant_msg)

        collected_response = ""

        try:
            if self.use_mock:
                # Generate mock response based on prompt
                if "hello" in prompt.lower():
                    response = "Hello! How can I help you today? I'm here to assist with any questions or tasks you might have."
                elif "time" in prompt.lower():
                    response = f"The current time is {datetime.now().strftime('%H:%M:%S')}. Is there anything else you'd like to know?"
                elif "help" in prompt.lower():
                    response = "I can help you with:\n• Answering questions\n• Explaining concepts\n• Writing assistance\n• Problem solving\nWhat would you like help with?"
                else:
                    response = f"I understand you're asking about '{prompt}'. Let me think about that and provide you with a helpful response. This is a mock response for demonstration purposes."

                # Stream the mock response
                async for chunk in create_mock_stream(
                    response, chunk_size=3, delay=0.03
                ):
                    print(chunk.content, end="", flush=True)
                    collected_response += chunk.content
            else:
                # Stream real response
                async for chunk in self.agent.stream(prompt):
                    print(chunk.content, end="", flush=True)
                    collected_response += chunk.content

            # Update message content
            assistant_msg.content = collected_response
            assistant_msg.streaming = False
            print()  # New line after streaming

            return collected_response

        except Exception as e:
            error_msg = f"\n❌ Error: {e}"
            print(error_msg)
            assistant_msg.content = error_msg
            assistant_msg.streaming = False
            return error_msg

    async def chat_loop(self):
        """Run the interactive chat loop."""
        print("💬 Streaming Chat Interface")
        print("=" * 60)
        print("Type 'quit' to exit, 'history' to see chat history")
        print("Streaming:", "Mock Mode" if self.use_mock else "Real API Mode")
        print("=" * 60)

        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()

                if user_input.lower() == "quit":
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == "history":
                    self.show_history()
                    continue
                elif not user_input:
                    continue

                # Add user message
                user_msg = ChatMessage(role="user", content=user_input)
                self.messages.append(user_msg)

                # Stream assistant response
                await self.stream_response(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def show_history(self):
        """Display chat history."""
        print("\n📜 Chat History")
        print("-" * 60)
        for msg in self.messages:
            self.display_message(msg)


class DocumentProcessor:
    """Process documents with streaming progress updates."""

    def __init__(self):
        self.sections_processed = 0
        self.total_sections = 0

    async def process_document(self, sections: list[str], processor_func=None):
        """Process document sections with streaming progress."""
        print("\n📄 Document Processing with Streaming Progress")
        print("=" * 60)

        self.total_sections = len(sections)
        results = []

        for i, section in enumerate(sections):
            self.sections_processed = i

            # Update progress
            progress = (i / self.total_sections) * 100
            print(
                f"\n[{progress:5.1f}%] Processing section {i+1}/{self.total_sections}"
            )
            print("-" * 40)

            # Simulate processing with streaming output
            if processor_func:
                result = await processor_func(section)
            else:
                # Default mock processing
                processing_steps = [
                    f"📖 Reading section: {section[:30]}...",
                    "🔍 Analyzing content...",
                    "🧠 Extracting key points...",
                    "✍️  Generating summary...",
                    "✅ Section complete!",
                ]

                result = ""
                for step in processing_steps:
                    async for chunk in create_mock_stream(
                        step + "\n", chunk_size=5, delay=0.02
                    ):
                        print(chunk.content, end="", flush=True)
                        result += chunk.content
                    await asyncio.sleep(0.1)

            results.append(result)

        print("\n[100.0%] Document processing complete!")
        print(f"✅ Processed {self.total_sections} sections")
        return results


class MultiStepTaskExecutor:
    """Execute multi-step tasks with streaming updates."""

    def __init__(self, agent: Agent | None = None):
        self.agent = agent
        self.steps_completed = []
        self.current_step = None

    async def execute_task(self, task_name: str, steps: list[dict[str, Any]]):
        """Execute a multi-step task with streaming progress."""
        print(f"\n🎯 Executing Task: {task_name}")
        print("=" * 60)

        total_steps = len(steps)

        for i, step in enumerate(steps):
            self.current_step = step["name"]
            print(f"\n📍 Step {i+1}/{total_steps}: {step['name']}")
            print("-" * 40)

            try:
                # Execute step with streaming output
                if "prompt" in step and self.agent:
                    # Real agent execution
                    result = ""
                    async for chunk in self.agent.stream(step["prompt"]):
                        print(chunk.content, end="", flush=True)
                        result += chunk.content
                    print()
                else:
                    # Mock execution
                    result = await self._mock_execute_step(step)

                self.steps_completed.append(
                    {"step": step["name"], "result": result, "status": "success"}
                )

                # Progress update
                progress = ((i + 1) / total_steps) * 100
                print(f"\n✅ Step complete! Overall progress: {progress:.1f}%")

            except Exception as e:
                print(f"\n❌ Step failed: {e}")
                self.steps_completed.append(
                    {"step": step["name"], "result": str(e), "status": "failed"}
                )

                if step.get("critical", False):
                    print("🛑 Critical step failed, stopping task execution")
                    break

            # Delay between steps
            if i < total_steps - 1:
                await asyncio.sleep(0.5)

        # Summary
        print("\n" + "=" * 60)
        print("📊 Task Summary:")
        success_count = sum(1 for s in self.steps_completed if s["status"] == "success")
        print(f"✅ Successful steps: {success_count}/{total_steps}")

        if success_count < total_steps:
            print(f"❌ Failed steps: {total_steps - success_count}")

        return self.steps_completed

    async def _mock_execute_step(self, step: dict[str, Any]) -> str:
        """Mock execution of a step."""
        action = step.get("action", "Processing")
        duration = step.get("duration", 2.0)

        # Simulate step execution with streaming output
        output = f"{action}...\n"

        # Stream some mock progress
        for i in range(3):
            progress_text = f"  → Progress: {(i+1)*33}%...\n"
            async for chunk in create_mock_stream(
                progress_text, chunk_size=3, delay=0.02
            ):
                print(chunk.content, end="", flush=True)
            await asyncio.sleep(duration / 3)

        complete_text = f"  → {action} completed successfully!\n"
        async for chunk in create_mock_stream(complete_text, chunk_size=5, delay=0.02):
            print(chunk.content, end="", flush=True)

        return output + "Success"


async def chat_example():
    """Run the streaming chat example."""
    chat = StreamingChatInterface(use_mock=True)
    await chat.chat_loop()


async def document_processing_example():
    """Run the document processing example."""
    processor = DocumentProcessor()

    # Sample document sections
    sections = [
        "Introduction: This document explains the benefits of streaming in AI applications...",
        "Chapter 1: Real-time User Experience - Streaming allows users to see responses as they are generated...",
        "Chapter 2: Technical Implementation - The streaming architecture involves chunking responses...",
        "Chapter 3: Best Practices - When implementing streaming, consider chunk size and latency...",
        "Conclusion: Streaming is an essential feature for modern AI applications...",
    ]

    results = await processor.process_document(sections)

    print(f"\n📊 Processed {len(results)} sections")


async def multi_step_task_example():
    """Run the multi-step task execution example."""
    executor = MultiStepTaskExecutor()

    # Define a multi-step task
    task_steps = [
        {
            "name": "Data Collection",
            "action": "Gathering data from various sources",
            "duration": 1.5,
        },
        {
            "name": "Data Validation",
            "action": "Validating and cleaning collected data",
            "duration": 1.0,
            "critical": True,
        },
        {
            "name": "Analysis",
            "action": "Performing statistical analysis",
            "duration": 2.0,
        },
        {
            "name": "Report Generation",
            "action": "Creating comprehensive report",
            "duration": 1.5,
        },
        {"name": "Quality Check", "action": "Final quality assurance", "duration": 1.0},
    ]

    results = await executor.execute_task("Data Analysis Pipeline", task_steps)

    print("\n📋 Detailed Results:")
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['step']}: {result['status']}")


async def main():
    """Run practical streaming examples."""
    print("🚀 Practical Streaming Use Cases")
    print("=" * 60)

    examples = [
        ("Streaming Chat Interface", chat_example),
        ("Document Processing", document_processing_example),
        ("Multi-Step Task Execution", multi_step_task_example),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. Exit")

    while True:
        try:
            choice = input("\nSelect an example (0-3): ").strip()

            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                await examples[0][1]()
            elif choice == "2":
                await examples[1][1]()
            elif choice == "3":
                await examples[2][1]()
            else:
                print("❌ Invalid choice")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
