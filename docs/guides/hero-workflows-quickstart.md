# AgentiCraft Hero Workflows - Quick Start Guide

Now that all hero workflows are fixed and working, here's how to use them:

## 1. ResearchTeam - Multi-Agent Research

```python
from agenticraft.workflows import ResearchTeam

# Create a research team (uses default model: gpt-4)
team = ResearchTeam()

# Or specify a different model
team = ResearchTeam(model="gpt-3.5-turbo")

# Conduct research
report = await team.research(
    topic="AI frameworks comparison",
    depth="comprehensive",  # "quick", "standard", or "comprehensive"
    audience="technical"    # "general", "technical", or "executive"
)

print(report["executive_summary"])
print(report["key_findings"])
```

## 2. CustomerServiceDesk - Multi-Tier Support

```python
from agenticraft.workflows import CustomerServiceDesk

# Create service desk
desk = CustomerServiceDesk()

# Handle customer inquiry
response = await desk.handle(
    customer_id="cust_123",
    inquiry="I need help with my billing",
    priority=7  # 1-10 scale
)

print(response["response"])
print(f"Handled by: {response['agent']}")
print(f"Escalated: {response['escalated']}")
```

## 3. CodeReviewPipeline - Automated Code Review

```python
from agenticraft.workflows import CodeReviewPipeline

# Create pipeline
pipeline = CodeReviewPipeline(mode="standard")  # "quick", "standard", or "thorough"

# Review code
review = await pipeline.review(
    code="""
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
""",
    language="python"
)

print(f"Score: {review['consensus']['average_score']}/100")
print(f"Issues found: {len(review['aggregated']['all_issues'])}")
```

## 4. MemoryResearchTeam - Research with Memory

```python
from agenticraft.workflows import MemoryResearchTeam

# Create team with memory
team = MemoryResearchTeam(memory_enabled=True)
await team.initialize()

# First research
report1 = await team.research("Python web frameworks")

# Continue with memory of previous research
report2 = await team.research(
    "Continue our analysis focusing on async frameworks",
    continue_previous=True
)

# Check research history
history = await team.get_research_history()

# Don't forget to shutdown
await team.shutdown()
```

## Configuration Options

All workflows accept these common parameters:

```python
workflow = WorkflowClass(
    name="CustomName",           # Custom workflow name
    model="gpt-4",              # LLM model (default: "gpt-4")
    provider=None,              # LLM provider (auto-detected from model)
    **kwargs                    # Additional workflow-specific options
)
```

## Model Configuration

The default model is set in AgentiCraft settings:
- Default: "gpt-4" 
- Can be overridden per workflow
- Supported models: Any OpenAI, Anthropic, or Ollama model

To change the global default:
```python
from agenticraft.core.config import settings
settings.default_model = "gpt-3.5-turbo"
```

## Environment Setup

Set your API keys:
```bash
export AGENTICRAFT_OPENAI_API_KEY="your-key"
export AGENTICRAFT_ANTHROPIC_API_KEY="your-key"
```

Or use a `.env` file:
```
AGENTICRAFT_OPENAI_API_KEY=your-key
AGENTICRAFT_ANTHROPIC_API_KEY=your-key
AGENTICRAFT_DEFAULT_MODEL=gpt-4
```

## Next Steps

1. Run `python test_workflows_fixed.py` to verify everything works
2. Check out the examples in `/examples/quickstart/`
3. Read the full documentation for each workflow
4. Start building your own multi-agent applications!
