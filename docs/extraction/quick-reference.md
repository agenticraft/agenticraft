# AgentiCraft Extraction Quick Reference

## 🎯 Hero Workflow Extraction Map

Quick reference for extracting components from Agentic Framework to AgentiCraft following the Hero Workflow approach.

## 📍 Week 1: Research Team Extraction

### Monday-Tuesday: Coordinator
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `/core/protocols/a2a/centralized/hierarchical.py` | `/agenticraft/agents/patterns/coordinator.py` | ~200 | Basic delegation, round-robin, result aggregation |

**Extract Commands:**
```bash
# Copy and simplify
cp /Users/zahere/Desktop/TLV/agentic-framework/core/protocols/a2a/centralized/hierarchical.py /tmp/
# Manual extraction focusing on:
# - HierarchicalCoordinator.__init__
# - delegate_task method (simplified)
# - aggregate_results method
# Remove: Roles, complex strategies, metrics
```

### Wednesday: Research Agents
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `/core/reasoning/specialized_agents/research/web_researcher.py` | `/agenticraft/agents/specialized/web_researcher.py` | ~100 | Search + summarization |
| `NEW` | `/agenticraft/agents/specialized/data_analyst.py` | ~100 | Simple synthesis |
| `/core/reasoning/specialized_agents/content/content_creator.py` | `/agenticraft/agents/specialized/technical_writer.py` | ~100 | Report formatting |

### Thursday: Research Team Workflow
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `NEW` | `/agenticraft/workflows/research_team.py` | ~150 | Hero workflow |

### Friday: Examples
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `NEW` | `/examples/quickstart/06_research_team.py` | ~50 | Quick start |
| `NEW` | `/examples/workflows/research_customization.py` | ~100 | Customization |
| `NEW` | `/examples/production/research_api.py` | ~150 | FastAPI integration |

## 📍 Week 2: Customer Service Extraction

### Tuesday-Wednesday: New Components
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `/core/protocols/a2a/hybrid/mesh_network.py` | `/agenticraft/agents/patterns/mesh.py` | ~300 | Basic routing, load balancing |
| `/core/human_loop/approval_system.py` | `/agenticraft/agents/patterns/escalation.py` | ~150 | Simple approval flow |
| `/core/protocols/mcp/auth.py` | `/agenticraft/protocols/mcp/auth/api_key.py` | ~50 | API key auth only |

### Thursday: Customer Service Workflow
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `NEW` | `/agenticraft/workflows/customer_service.py` | ~200 | Hero workflow |

## 📍 Week 3: Code Review Pipeline

### Monday-Tuesday: Production Infrastructure
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `/core/protocols/mcp/auth.py` | `/agenticraft/protocols/mcp/auth/jwt.py` | ~100 | JWT auth |
| `/core/protocols/mcp/auth.py` | `/agenticraft/protocols/mcp/auth/hmac.py` | ~100 | HMAC auth |
| `/core/protocols/mcp/auth.py` | `/agenticraft/protocols/mcp/auth/bearer.py` | ~50 | Bearer auth |
| `/templates/fastapi_production/deployment/` | `/agenticraft/templates/kubernetes/` | N/A | YAML files |
| `/enterprise/tools/observability_tool.py` | `/agenticraft/telemetry/observability/enhanced.py` | ~500 | Full observability |

### Wednesday-Thursday: Code Review
| From (Agentic) | To (AgentiCraft) | Lines | Focus |
|----------------|------------------|-------|-------|
| `/core/reasoning/specialized_agents/technical/code_reviewer.py` | `/agenticraft/agents/specialized/code_reviewer.py` | ~200 | Code analysis |
| `/core/utils/decorators.py` | `/agenticraft/utils/decorators.py` | ~150 | Retry, performance |
| `NEW` | `/agenticraft/workflows/code_review.py` | ~200 | Hero workflow |

## 🛠️ Extraction Scripts

### Basic Extraction Script
```bash
#!/bin/bash
# extract.sh - Basic extraction helper

AGENTIC_PATH="/Users/zahere/Desktop/TLV/agentic-framework"
AGENTICRAFT_PATH="/Users/zahere/Desktop/TLV/agenticraft"

# Function to extract specific classes/functions
extract_component() {
    local source=$1
    local dest=$2
    local component=$3
    
    echo "Extracting $component from $source to $dest"
    # Use sed/awk to extract specific components
    # Manual review required after extraction
}

# Week 1 extractions
extract_component \
    "$AGENTIC_PATH/core/protocols/a2a/centralized/hierarchical.py" \
    "$AGENTICRAFT_PATH/agenticraft/agents/patterns/coordinator.py" \
    "HierarchicalCoordinator"
```

### Simplification Checklist
For each extraction:
- [ ] Remove abstract base classes
- [ ] Convert to simple inheritance
- [ ] Add reasoning transparency
- [ ] Remove complex configuration
- [ ] Use smart defaults
- [ ] Integrate with AgentiCraft patterns

## 📊 Component Size Targets

| Component | Target Lines | Max Complexity |
|-----------|--------------|----------------|
| Coordinator | 200 | 1 class, 5 methods |
| Specialized Agent | 100 | 1 class, 3 methods |
| Hero Workflow | 150-200 | 1 class, 5 methods |
| Auth Method | 50-100 | 1 class, 4 methods |
| Pattern | 150-300 | 2 classes max |

## 🔄 Integration Patterns

### Pattern 1: Agent Integration
```python
# Agentic Framework pattern
class SpecializedAgent(BaseAgent, MemoryMixin, ToolMixin):
    def __init__(self, config: ComplexConfig):
        super().__init__(config)

# AgentiCraft pattern (simplified)
class SpecializedAgent(Agent):
    def __init__(self, name: str):
        super().__init__(name)
```

### Pattern 2: Workflow Integration
```python
# AgentiCraft workflow pattern
from agenticraft.core import Workflow

class HeroWorkflow(Workflow):
    def __init__(self):
        super().__init__("hero_name")
        self._setup()
    
    async def main_action(self, input: str) -> Result:
        # Simple, powerful API
        pass
```

### Pattern 3: Tool Integration
```python
# Use existing AgentiCraft tools
from agenticraft.tools import Tool

class ExtractedTool(Tool):
    def __init__(self):
        super().__init__(
            name="extracted_tool",
            description="Simple description"
        )
```

## 📝 Documentation Templates

### Hero Workflow Doc Template
```markdown
# [Hero Name] Workflow

## Quick Start
\```python
from agenticraft.workflows import HeroWorkflow
workflow = HeroWorkflow()
result = await workflow.action("input")
\```

## How It Works
[Explain the magic]

## Customization
[Show how to extend]

## Examples
[3 practical examples]
```

### Extracted Component Doc Template
```markdown
# [Component Name]

## Purpose
[Why this was extracted]

## Usage
\```python
[Simple example]
\```

## Integration
[How it fits with AgentiCraft]

## Original Source
Extracted from: `agentic-framework/path/to/file.py`
Simplified from: [X lines] to [Y lines]
```

## ✅ Weekly Deliverables Checklist

### Week 1 Deliverables
- [ ] SimpleCoordinator class (200 lines)
- [ ] 3 specialized agents (300 lines total)
- [ ] ResearchTeam workflow (150 lines)
- [ ] 3 examples (300 lines total)
- [ ] Documentation for Research Team
- [ ] Tests for all components

### Week 2 Deliverables  
- [ ] Mesh networking pattern (300 lines)
- [ ] Escalation pattern (150 lines)
- [ ] API key auth (50 lines)
- [ ] CustomerServiceDesk workflow (200 lines)
- [ ] 3 examples (300 lines total)
- [ ] Documentation for Customer Service

### Week 3 Deliverables
- [ ] Complete auth system (250 lines)
- [ ] K8s templates (YAML files)
- [ ] Enhanced observability (500 lines)
- [ ] Code reviewer agent (200 lines)
- [ ] CodeReviewPipeline workflow (200 lines)
- [ ] Production deployment guide

## 🚀 Launch Checklist

For each hero workflow launch:
- [ ] Code complete and tested
- [ ] Examples working
- [ ] Documentation ready
- [ ] Demo video recorded
- [ ] Blog post written
- [ ] Social media ready
- [ ] Community notified
- [ ] Metrics tracking enabled

## 🎯 Remember

1. **Heroes first** - Build what users want
2. **Extract minimally** - Only what heroes need
3. **Simplify ruthlessly** - Every line must justify itself
4. **Integrate seamlessly** - Feel native to AgentiCraft
5. **Document clearly** - Examples are documentation

**The hero workflows ARE the product!**