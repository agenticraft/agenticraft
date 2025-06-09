#!/usr/bin/env python3
"""Runner script for streaming examples."""

import os
import subprocess
import sys
from pathlib import Path


def check_api_keys():
    """Check if API keys are set."""
    keys = {
        "OpenAI": "OPENAI_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
    }

    found_keys = []
    for name, env_var in keys.items():
        if os.getenv(env_var):
            found_keys.append(name)

    return found_keys


def run_example(example_file: str):
    """Run a specific example."""
    example_path = Path(__file__).parent / example_file

    if not example_path.exists():
        print(f"❌ Example file not found: {example_file}")
        return

    print(f"\n🚀 Running {example_file}...")
    print("=" * 60)

    try:
        subprocess.run([sys.executable, str(example_path)], check=True)
    except subprocess.CalledProcessError:
        print("\n❌ Example failed to run")
    except KeyboardInterrupt:
        print("\n👋 Example interrupted")


def main():
    """Main runner function."""
    print("🌊 AgentiCraft Streaming Examples Runner")
    print("=" * 60)

    # Check API keys
    found_keys = check_api_keys()

    if found_keys:
        print(f"✅ Found API keys for: {', '.join(found_keys)}")
    else:
        print("⚠️  No API keys found")
        print("   You can still run mock examples!")

    # Show menu
    print("\nAvailable examples:")
    print("1. Simple Streaming Demo (no API key required)")
    print("2. Workflow Streaming Demo (no API key required)")
    print("3. Basic Streaming (requires API key)")
    print("4. Advanced Streaming with Handlers (requires API key)")
    print("5. Practical Streaming (requires API key)")
    print("6. Visual Streaming (requires API key)")
    print("7. Multi-Provider Streaming (requires API key)")
    print("8. Run all examples")
    print("0. Exit")

    while True:
        try:
            choice = input("\nSelect an example (0-8): ").strip()

            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                run_example("simple_streaming_demo.py")
            elif choice == "2":
                run_example("workflow_streaming_demo.py")
            elif choice == "3":
                if not found_keys:
                    print("⚠️  This example requires an API key!")
                    print(
                        "   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable"
                    )
                else:
                    run_example("basic_streaming.py")
            elif choice == "4":
                if not found_keys:
                    print("⚠️  This example requires an API key!")
                    print(
                        "   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable"
                    )
                else:
                    run_example("advanced_streaming_handlers.py")
            elif choice == "5":
                if not found_keys:
                    print("⚠️  This example requires an API key!")
                    print(
                        "   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable"
                    )
                else:
                    run_example("practical_streaming.py")
            elif choice == "6":
                if not found_keys:
                    print("⚠️  This example requires an API key!")
                    print(
                        "   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable"
                    )
                else:
                    run_example("visual_streaming.py")
            elif choice == "7":
                if not found_keys:
                    print("⚠️  This example requires an API key!")
                    print(
                        "   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable"
                    )
                else:
                    run_example("multi_provider_stream.py")
            elif choice == "8":
                print("\n🎯 Running all examples...")
                # Run no-API-key examples first
                run_example("simple_streaming_demo.py")
                run_example("workflow_streaming_demo.py")

                if found_keys:
                    # Run API-key-required examples
                    run_example("basic_streaming.py")
                    run_example("streaming_with_handlers.py")
                    run_example("advanced_streaming_handlers.py")
                    run_example("practical_streaming.py")
                    run_example("visual_streaming.py")
                    run_example("multi_provider_stream.py")
                else:
                    print("\n⚠️  Skipping API examples (no API key found)")
            else:
                print("❌ Invalid choice. Please select 0-8.")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n📚 For more information, see README.md")


if __name__ == "__main__":
    # Change to script directory
    os.chdir(Path(__file__).parent)

    main()
