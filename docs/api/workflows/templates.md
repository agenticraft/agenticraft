# Workflow Templates API Reference

## Overview

Workflow Templates provide production-ready, customizable workflows for common business scenarios. Each template implements best practices and can be configured for specific needs.

## Class Reference

### WorkflowTemplates

```python
class WorkflowTemplates:
    """
    Collection of production-ready workflow templates.
    
    Static methods that generate complete workflows for
    research, content creation, data processing, and more.
    """
```

#### Template Methods

##### research_workflow()

```python
@staticmethod
def research_workflow(
    topic: str,
    sources: List[str] = ["web", "academic", "news"],
    depth: str = "comprehensive",
    output_format: str = "report",
    tools: Optional[Dict[str, BaseTool]] = None,
    max_sources: int = 10,
    quality_threshold: float = 0.7
) -> Workflow
```

Create a comprehensive research workflow.

**Parameters:**
- `topic`: Research topic
- `sources`: Information sources to use
- `depth`: Research depth ("quick", "standard", "comprehensive")
- `output_format`: Output format ("summary", "report", "presentation")
- `tools`: Custom tools for research
- `max_sources`: Maximum number of sources to analyze
- `quality_threshold`: Minimum quality score for sources

**Returns:**
- `Workflow`: Configured research workflow

**Example:**

```python
from agenticraft.workflows.templates import WorkflowTemplates

# Comprehensive research workflow
research = WorkflowTemplates.research_workflow(
    topic="AI Safety and Alignment",
    sources=["academic", "news", "blogs", "forums"],
    depth="comprehensive",
    output_format="report",
    max_sources=20,
    quality_threshold=0.8
)

# Quick research
quick_research = WorkflowTemplates.research_workflow(
    topic="Latest AI developments",
    sources=["news", "blogs"],
    depth="quick",
    output_format="summary"
)
```

**Generated Workflow Structure:**
```
1. Define Research Scope
2. Parallel Source Gathering
   - Academic papers
   - News articles
   - Blog posts
   - Forum discussions
3. Quality Filtering
4. Information Extraction
5. Fact Verification
6. Synthesis and Analysis
7. Report Generation
8. Citation Compilation
```

##### content_pipeline()

```python
@staticmethod
def content_pipeline(
    content_type: str,
    target_audience: str = "general",
    tone: str = "professional",
    length: str = "medium",
    seo_optimized: bool = False,
    stages: Optional[List[str]] = None,
    review_loops: int = 1
) -> Workflow
```

Create a content creation and publishing workflow.

**Parameters:**
- `content_type`: Type of content ("blog_post", "article", "social_media", "video_script")
- `target_audience`: Target audience description
- `tone`: Writing tone ("professional", "casual", "academic", "creative")
- `length`: Content length ("short", "medium", "long")
- `seo_optimized`: Include SEO optimization
- `stages`: Custom pipeline stages
- `review_loops`: Number of review iterations

**Returns:**
- `Workflow`: Configured content pipeline

**Example:**

```python
# Blog post pipeline
blog_pipeline = WorkflowTemplates.content_pipeline(
    content_type="blog_post",
    target_audience="developers",
    tone="technical",
    length="long",
    seo_optimized=True,
    review_loops=2
)

# Social media content
social_pipeline = WorkflowTemplates.content_pipeline(
    content_type="social_media",
    target_audience="general",
    tone="casual",
    length="short",
    stages=["ideation", "creation", "optimization", "scheduling"]
)
```

**Default Stages:**
```
1. Topic Research
2. Outline Creation
3. Content Drafting
4. Review and Edit
5. SEO Optimization (if enabled)
6. Final Review
7. Publishing Preparation
8. Distribution
```

##### data_processing()

```python
@staticmethod
def data_processing(
    input_format: str,
    output_format: str,
    transformations: List[str],
    validation_rules: Optional[Dict[str, Any]] = None,
    error_handling: str = "log_and_continue",
    batch_size: Optional[int] = None,
    parallel_processing: bool = True
) -> Workflow
```

Create a data processing pipeline.

**Parameters:**
- `input_format`: Input data format ("csv", "json", "xml", "database")
- `output_format`: Output data format
- `transformations`: List of transformations to apply
- `validation_rules`: Data validation rules
- `error_handling`: Error handling strategy
- `batch_size`: Process data in batches
- `parallel_processing`: Enable parallel processing

**Returns:**
- `Workflow`: Configured data processing workflow

**Example:**

```python
# ETL pipeline
etl = WorkflowTemplates.data_processing(
    input_format="csv",
    output_format="parquet",
    transformations=[
        "remove_duplicates",
        "clean_missing",
        "normalize_dates",
        "calculate_metrics",
        "aggregate_by_region"
    ],
    validation_rules={
        "required_columns": ["id", "date", "amount"],
        "date_format": "YYYY-MM-DD",
        "amount_range": (0, 1000000)
    },
    batch_size=10000,
    parallel_processing=True
)

# Real-time processing
streaming = WorkflowTemplates.data_processing(
    input_format="json_stream",
    output_format="database",
    transformations=["validate", "enrich", "store"],
    error_handling="dead_letter_queue"
)
```

**Pipeline Structure:**
```
1. Data Ingestion
2. Format Validation
3. Parallel Transformation
   - Clean data
   - Apply business rules
   - Calculate derived fields
4. Quality Checks
5. Output Generation
6. Delivery/Storage
```

##### multi_agent_collaboration()

```python
@staticmethod
def multi_agent_collaboration(
    task: str,
    agents: List[Dict[str, Any]],
    coordination_style: str = "orchestrated",
    communication_pattern: str = "hub_spoke",
    decision_making: str = "consensus",
    timeout: Optional[float] = None
) -> Workflow
```

Create a multi-agent collaboration workflow.

**Parameters:**
- `task`: Collaborative task description
- `agents`: List of agent configurations
- `coordination_style`: How agents coordinate ("orchestrated", "choreographed", "hybrid")
- `communication_pattern`: Communication pattern ("hub_spoke", "mesh", "chain")
- `decision_making`: Decision strategy ("consensus", "voting", "hierarchical")
- `timeout`: Overall timeout for collaboration

**Returns:**
- `Workflow`: Configured multi-agent workflow

**Example:**

```python
# Research team collaboration
research_team = WorkflowTemplates.multi_agent_collaboration(
    task="Comprehensive market analysis",
    agents=[
        {"name": "data_analyst", "role": "Analyze quantitative data"},
        {"name": "market_researcher", "role": "Research competitors"},
        {"name": "strategist", "role": "Develop recommendations"},
        {"name": "coordinator", "role": "Synthesize findings"}
    ],
    coordination_style="orchestrated",
    communication_pattern="hub_spoke",
    decision_making="consensus"
)

# Creative team
creative_team = WorkflowTemplates.multi_agent_collaboration(
    task="Design new product campaign",
    agents=[
        {"name": "copywriter", "role": "Create messaging"},
        {"name": "designer", "role": "Design visuals"},
        {"name": "strategist", "role": "Define strategy"},
        {"name": "reviewer", "role": "Quality control"}
    ],
    communication_pattern="mesh",
    decision_making="voting"
)
```

##### customer_service()

```python
@staticmethod
def customer_service(
    channels: List[str] = ["email", "chat"],
    escalation_levels: int = 3,
    knowledge_base: Optional[str] = None,
    sentiment_analysis: bool = True,
    auto_responses: bool = True,
    sla_config: Optional[Dict[str, int]] = None
) -> Workflow
```

Create a customer service workflow.

**Parameters:**
- `channels`: Support channels to handle
- `escalation_levels`: Number of escalation levels
- `knowledge_base`: Knowledge base identifier
- `sentiment_analysis`: Enable sentiment analysis
- `auto_responses`: Enable automatic responses
- `sla_config`: Service level agreement configuration

**Returns:**
- `Workflow`: Configured customer service workflow

**Example:**

```python
# Omnichannel support
support = WorkflowTemplates.customer_service(
    channels=["email", "chat", "phone", "social"],
    escalation_levels=3,
    knowledge_base="support_kb_v2",
    sentiment_analysis=True,
    sla_config={
        "response_time": 3600,  # 1 hour
        "resolution_time": 86400  # 24 hours
    }
)
```

##### code_review()

```python
@staticmethod
def code_review(
    review_types: List[str] = ["style", "security", "performance"],
    languages: List[str] = ["python", "javascript"],
    tools: Optional[Dict[str, Any]] = None,
    auto_fix: bool = False,
    threshold: float = 0.8
) -> Workflow
```

Create a code review workflow.

**Parameters:**
- `review_types`: Types of review to perform
- `languages`: Programming languages to support
- `tools`: Code analysis tools
- `auto_fix`: Enable automatic fixes
- `threshold`: Quality threshold

**Returns:**
- `Workflow`: Configured code review workflow

## Template Customization

### Extending Templates

```python
# Get base template
base_research = WorkflowTemplates.research_workflow(
    topic="AI Ethics",
    sources=["academic"]
)

# Customize by adding steps
custom_research = base_research.add_steps([
    Step("peer_review", "Get peer review of findings"),
    Step("publish", "Publish to repository")
])

# Modify existing steps
custom_research.modify_step(
    "synthesis",
    new_description="Synthesize with ethical framework"
)
```

### Template Composition

```python
# Combine multiple templates
class CompositeTemplates:
    @staticmethod
    def research_and_content(topic: str) -> Workflow:
        """Research topic then create content."""
        
        # Research phase
        research = WorkflowTemplates.research_workflow(
            topic=topic,
            output_format="summary"
        )
        
        # Content phase
        content = WorkflowTemplates.content_pipeline(
            content_type="blog_post",
            stages=["outline", "draft", "edit", "publish"]
        )
        
        # Combine workflows
        return Workflow.combine(
            name="research_to_content",
            workflows=[research, content],
            connection_type="sequential"
        )
```

### Dynamic Template Generation

```python
class DynamicTemplateGenerator:
    """Generate templates based on requirements."""
    
    @staticmethod
    def generate_from_requirements(
        requirements: Dict[str, Any]
    ) -> Workflow:
        """Generate workflow from requirements."""
        
        # Analyze requirements
        complexity = requirements.get("complexity", "medium")
        domain = requirements.get("domain", "general")
        constraints = requirements.get("constraints", {})
        
        # Select base template
        if domain == "research":
            base = WorkflowTemplates.research_workflow(...)
        elif domain == "content":
            base = WorkflowTemplates.content_pipeline(...)
        else:
            base = WorkflowTemplates.data_processing(...)
        
        # Apply constraints
        if constraints.get("time_limit"):
            base.set_timeout(constraints["time_limit"])
        
        if constraints.get("parallel_execution"):
            base.enable_parallelism()
        
        return base
```

## Configuration Presets

### Industry-Specific Presets

```python
class IndustryPresets:
    """Pre-configured templates for specific industries."""
    
    @staticmethod
    def healthcare_data_processing() -> Workflow:
        """HIPAA-compliant data processing."""
        return WorkflowTemplates.data_processing(
            input_format="hl7",
            output_format="fhir",
            transformations=[
                "validate_phi",
                "deidentify",
                "standardize_codes",
                "quality_metrics"
            ],
            validation_rules={
                "hipaa_compliant": True,
                "encryption": "AES-256"
            }
        )
    
    @staticmethod
    def financial_reporting() -> Workflow:
        """Financial reporting workflow."""
        return WorkflowTemplates.data_processing(
            input_format="database",
            output_format="report",
            transformations=[
                "reconciliation",
                "regulatory_checks",
                "risk_calculations",
                "report_generation"
            ],
            validation_rules={
                "sox_compliant": True,
                "audit_trail": True
            }
        )
```

### Scale Presets

```python
# Small scale
small_scale = {
    "batch_size": 100,
    "parallel_processing": False,
    "timeout": 300,
    "resources": "minimal"
}

# Enterprise scale
enterprise_scale = {
    "batch_size": 10000,
    "parallel_processing": True,
    "timeout": 3600,
    "resources": "auto_scale",
    "checkpointing": True,
    "monitoring": True
}
```

## Performance Optimization

### Template Performance Profiles

| Template | Typical Duration | Resource Usage | Scalability |
|----------|-----------------|----------------|-------------|
| Research Workflow | 5-30 min | Medium | Horizontal |
| Content Pipeline | 10-60 min | Low | Vertical |
| Data Processing | Variable | High | Both |
| Multi-Agent | 15-45 min | High | Horizontal |

### Optimization Strategies

```python
# Optimize research workflow
optimized_research = WorkflowTemplates.research_workflow(
    topic="Quick research",
    sources=["web"],  # Limit sources
    depth="quick",  # Reduce depth
    max_sources=5,  # Limit sources
    parallel_source_fetching=True  # Parallel fetching
)

# Optimize data processing
optimized_data = WorkflowTemplates.data_processing(
    input_format="parquet",  # Efficient format
    output_format="parquet",
    transformations=["essential_only"],
    batch_size=50000,  # Large batches
    parallel_processing=True,
    cache_intermediate=True  # Cache results
)
```

## Monitoring and Metrics

### Built-in Metrics

```python
# Execute with metrics collection
result = await agent.run_workflow(
    "Execute template",
    template_workflow,
    collect_metrics=True
)

# Access metrics
metrics = result.metrics
print(f"Total duration: {metrics.total_duration}")
print(f"Steps completed: {metrics.steps_completed}")
print(f"Resource usage: {metrics.resource_usage}")
print(f"Error rate: {metrics.error_rate}")
```

### Custom Metrics

```python
# Add custom metrics to templates
template = WorkflowTemplates.research_workflow(
    topic="AI Safety",
    custom_metrics={
        "sources_analyzed": Counter(),
        "facts_extracted": Counter(),
        "confidence_scores": Histogram()
    }
)
```

## Error Recovery

### Template-Specific Recovery

```python
# Research workflow with recovery
research = WorkflowTemplates.research_workflow(
    topic="Complex topic",
    error_recovery={
        "source_unavailable": "use_cache",
        "parsing_error": "try_alternative_parser",
        "synthesis_failure": "fallback_to_summary"
    }
)

# Data processing with recovery
data_pipeline = WorkflowTemplates.data_processing(
    input_format="csv",
    output_format="database",
    error_recovery={
        "validation_error": "quarantine_record",
        "transformation_error": "log_and_skip",
        "database_error": "retry_with_backoff"
    }
)
```

## See Also

- [Workflow Patterns](patterns.md) - Building blocks for templates
- [Workflow Visualization](visualization.md) - Visualizing templates
- [WorkflowAgent](workflow_agent.md) - Template execution
- [Examples](../../examples/workflows/templates_example.py) - Template examples
