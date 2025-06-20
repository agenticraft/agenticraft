# AgentiCraft Model Parameter Fixes - Summary

## Issue Fixed
All hero workflows (ResearchTeam, CustomerServiceDesk, CodeReviewPipeline) were failing because they were passing `model=None` when creating agents, which violated pydantic validation requiring a valid string.

## Solution Applied
Added logic to use the default model from settings when no model is specified:

```python
# Use default model from settings if not specified
from agenticraft.core.config import settings
model = self.model or settings.default_model
```

## Files Updated

### 1. CodeReviewPipeline (`/agenticraft/workflows/code_review.py`)
- Fixed `_setup_agents()` method to use settings default model
- Updated all CodeReviewer agent creations to use the resolved model
- Added telemetry stub functions to avoid import errors

### 2. ResearchTeam (`/agenticraft/workflows/research_team.py`)
- Fixed `_setup_team()` method to use settings default model
- Updated WebResearcher, DataAnalyst, and TechnicalWriter creations
- Updated SimpleCoordinator creation

### 3. CustomerServiceDesk (`/agenticraft/workflows/customer_service.py`)
- Fixed `_setup_agents()` method to use settings default model
- Updated all service agent creations
- Updated coordinator agent creation

### 4. MemoryResearchTeam (`/agenticraft/workflows/memory_research_team.py`)
- Fixed `_setup_team()` method to use settings default model
- Updated all agent creations (researchers, analysts, writers)
- Updated SimpleCoordinator creation

### 5. Core Configuration (`/agenticraft/core/__init__.py` and `/agenticraft/core/workflow.py`)
- Added WorkflowConfig class to workflow.py
- Exported WorkflowConfig from core module
- Updated Workflow class to accept WorkflowConfig

## Default Model
The default model is set to "gpt-4" in the settings (`/agenticraft/core/config.py`):
```python
default_model: str = Field(default="gpt-4", description="Default LLM model")
```

## Testing
All hero workflows should now create successfully without specifying a model:
```python
# These now work:
pipeline = CodeReviewPipeline()  # Uses default "gpt-4"
team = ResearchTeam()           # Uses default "gpt-4"
desk = CustomerServiceDesk()    # Uses default "gpt-4"

# Can still override:
pipeline = CodeReviewPipeline(model="gpt-3.5-turbo")
```

## Next Steps
1. Implement the provider factory (`get_provider` function)
2. Implement telemetry module properly
3. Add tests for all hero workflows
4. Document the model configuration options
