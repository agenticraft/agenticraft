# Basic AgentiCraft Example

A minimal example showing how to use AgentiCraft agents.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. **Run the example:**
```bash
python main.py
```

## What's Included

- Simple agent with tools
- Reasoning agent example
- Basic tool usage (calculator and search)

## Running with CLI

You can also run this agent using the AgentiCraft CLI:

```bash
# Interactive mode
agenticraft run main.py --interactive

# Single prompt
agenticraft run main.py --prompt "What is 2+2?"
```

## Customization

Edit `main.py` to:
- Change the agent name
- Add more tools
- Modify the prompts
- Switch providers (OpenAI, Anthropic, Ollama)

## Next Steps

- Check out the [documentation](https://docs.agenticraft.ai)
- Explore more [examples](https://github.com/agenticraft/agenticraft/tree/main/examples)
- Try other templates: `agenticraft new my-api --template fastapi`
