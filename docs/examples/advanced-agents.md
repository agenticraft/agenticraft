# Advanced Agent Examples

Explore the power of ReasoningAgent and WorkflowAgent with practical examples.

## ReasoningAgent Examples

### Problem Solving with Transparency

```python
from agenticraft import ReasoningAgent

# Create a reasoning agent
agent = ReasoningAgent(
    name="ProblemSolver",
    model="gpt-4",
    reasoning_style="chain_of_thought"
)

# Solve a complex problem
problem = """
A company's revenue is declining by 15% quarterly. 
Employee satisfaction is at 45%. 
Customer churn increased by 30%. 
What should the CEO prioritize?
"""

response = agent.run(problem)

# Display reasoning process
print("=== REASONING PROCESS ===")
for i, step in enumerate(response.reasoning, 1):
    print(f"\nStep {i}: {step}")

print(f"\n=== RECOMMENDATION ===")
print(response.content)

print(f"\n=== CONFIDENCE ===")
print(f"Confidence level: {response.confidence:.2%}")
```

### Multi-Perspective Analysis

```python
from agenticraft import ReasoningAgent

agent = ReasoningAgent(
    name="Analyst",
    model="gpt-4",
    reasoning_style="tree_of_thought",
    explore_branches=3
)

# Analyze from multiple angles
query = "Should we launch our product in Europe or Asia first?"

response = agent.run(query)

# Show different perspectives explored
print("=== PERSPECTIVES CONSIDERED ===")
for branch in response.reasoning_branches:
    print(f"\n{branch.perspective}:")
    print(f"  Pros: {branch.pros}")
    print(f"  Cons: {branch.cons}")
    print(f"  Score: {branch.score}")
```

### Decision Making with Criteria

```python
from agenticraft import ReasoningAgent

agent = ReasoningAgent(
    name="DecisionMaker",
    model="gpt-4"
)

decision = agent.run("""
    Evaluate these job offers:
    1. Startup: $120k, equity, high risk
    2. Big Tech: $150k, stable, less growth
    3. Remote: $130k, flexibility, isolation
    
    Criteria: Career growth, work-life balance, financial security
""")

# Structured decision output
print("Decision Matrix:")
print(decision.structured_output)
```

## WorkflowAgent Examples

### Data Processing Pipeline

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(
    name="DataProcessor",
    model="gpt-4"
)

# Define a data processing workflow
data_workflow = [
    Step("validate", "Validate input data format and completeness"),
    Step("clean", "Remove duplicates and fix inconsistencies"),
    Step("transform", "Convert data to analysis format"),
    Step("analyze", "Perform statistical analysis"),
    Step("visualize", "Create charts and graphs"),
    Step("report", "Generate executive summary")
]

# Run the workflow
result = agent.run_workflow(
    "Process Q4 sales data from all regions",
    workflow=data_workflow
)

# Monitor progress
for step_name, step_result in result.steps.items():
    print(f"\n{step_name.upper()}")
    print(f"  Status: {step_result.status}")
    print(f"  Duration: {step_result.duration:.2f}s")
    print(f"  Output: {step_result.output[:100]}...")
```

### Content Creation Workflow

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(
    name="ContentCreator",
    model="gpt-4"
)

blog_workflow = [
    Step("research", "Research the topic and gather sources"),
    Step("outline", "Create a detailed outline"),
    Step("draft", "Write the first draft"),
    Step("edit", "Edit for clarity and flow"),
    Step("optimize", "Optimize for SEO"),
    Step("format", "Format with headers and sections")
]

result = agent.run_workflow(
    "Create a blog post about AI safety best practices",
    workflow=blog_workflow
)

# Get the final content
final_content = result.steps["format"].output
print(final_content)
```

### Parallel Processing Example

```python
from agenticraft import WorkflowAgent, Step

agent = WorkflowAgent(
    name="ParallelProcessor",
    model="gpt-4"
)

# Steps that can run in parallel
analysis_workflow = [
    # These three run in parallel
    Step("analyze_customers", "Analyze customer data"),
    Step("analyze_products", "Analyze product performance"),
    Step("analyze_market", "Analyze market trends"),
    
    # This depends on all three above
    Step("synthesize", "Combine all analyses",
         depends_on=["analyze_customers", "analyze_products", "analyze_market"]),
    
    Step("recommend", "Generate recommendations",
         depends_on=["synthesize"])
]

result = agent.run_workflow(
    "Perform comprehensive business analysis",
    workflow=analysis_workflow,
    parallel=True  # Enable parallel execution
)
```

## Combining Both Agent Types

### Research Assistant with Reasoning

```python
from agenticraft import ReasoningAgent, WorkflowAgent, Step

# Use ReasoningAgent for analysis
reasoner = ReasoningAgent(name="Analyst", model="gpt-4")

# Use WorkflowAgent for process
workflow_agent = WorkflowAgent(name="Researcher", model="gpt-4")

# Research workflow that uses reasoning
research_workflow = [
    Step("gather", "Gather information on the topic"),
    Step("analyze", "Deep analysis with reasoning"),
    Step("synthesize", "Synthesize findings"),
    Step("conclude", "Draw conclusions")
]

# Custom step handler for reasoning
async def analyze_with_reasoning(context):
    data = context["gather_output"]
    reasoning_result = reasoner.run(f"Analyze this data: {data}")
    return {
        "analysis": reasoning_result.content,
        "reasoning": reasoning_result.reasoning,
        "confidence": reasoning_result.confidence
    }

# Attach custom handler
workflow_agent.set_step_handler("analyze", analyze_with_reasoning)

# Run the research
result = workflow_agent.run_workflow(
    "Research the impact of remote work on productivity",
    workflow=research_workflow
)
```

### Cost-Optimized Complex Tasks

```python
from agenticraft import ReasoningAgent, WorkflowAgent

# Expensive reasoning agent
reasoning_agent = ReasoningAgent(
    name="DeepThinker",
    provider="anthropic",
    model="claude-3-opus-20240229"
)

# Cheaper workflow agent
workflow_agent = WorkflowAgent(
    name="Worker",
    provider="ollama",
    model="llama2"
)

# Use reasoning for complex parts only
def smart_process(task):
    # Simple steps with cheap model
    workflow = [
        Step("preprocess", "Prepare data"),
        Step("basic_analysis", "Basic analysis")
    ]
    
    basic_result = workflow_agent.run_workflow(task, workflow)
    
    # Complex reasoning with expensive model
    if basic_result.requires_deep_analysis:
        reasoning_result = reasoning_agent.run(
            f"Analyze: {basic_result.summary}"
        )
        return reasoning_result
    
    return basic_result
```

## Best Practices

1. **Choose the Right Agent**:
   - ReasoningAgent for transparency and explainability
   - WorkflowAgent for structured multi-step processes
   - Combine both for complex systems

2. **Optimize Resource Usage**:
   - Use expensive models only for complex reasoning
   - Switch to cheaper models for simple tasks
   - Cache intermediate results

3. **Design Clear Workflows**:
   - Each step should have a single purpose
   - Use dependencies to control flow
   - Enable parallel execution where possible

4. **Monitor and Debug**:
   - Track step durations
   - Log reasoning traces
   - Set confidence thresholds

## Complete Example: AI Teaching Assistant

```python
#!/usr/bin/env python3
"""
AI Teaching Assistant using both ReasoningAgent and WorkflowAgent
"""

from agenticraft import ReasoningAgent, WorkflowAgent, Step

class TeachingAssistant:
    def __init__(self):
        # Reasoning agent for explanations
        self.explainer = ReasoningAgent(
            name="Explainer",
            model="gpt-4",
            reasoning_style="chain_of_thought"
        )
        
        # Workflow agent for lesson planning
        self.planner = WorkflowAgent(
            name="LessonPlanner",
            model="gpt-3.5-turbo"
        )
    
    def explain_concept(self, concept: str, student_level: str):
        """Explain a concept with reasoning."""
        prompt = f"""
        Explain {concept} to a {student_level} student.
        Show your reasoning for the explanation approach.
        """
        
        response = self.explainer.run(prompt)
        
        return {
            "explanation": response.content,
            "reasoning": response.reasoning,
            "confidence": response.confidence,
            "assumptions": response.assumptions
        }
    
    def create_lesson_plan(self, topic: str, duration: str):
        """Create a structured lesson plan."""
        lesson_workflow = [
            Step("objectives", "Define learning objectives"),
            Step("prerequisites", "Identify prerequisites"),
            Step("content", "Structure main content"),
            Step("activities", "Design interactive activities"),
            Step("assessment", "Create assessment methods"),
            Step("resources", "List additional resources")
        ]
        
        result = self.planner.run_workflow(
            f"Create a {duration} lesson plan for {topic}",
            workflow=lesson_workflow
        )
        
        return result
    
    def adaptive_teaching(self, question: str, student_response: str):
        """Adapt teaching based on student understanding."""
        # Analyze student response with reasoning
        analysis = self.explainer.run(
            f"Student asked: {question}\n"
            f"Student answered: {student_response}\n"
            "Analyze their understanding level."
        )
        
        # Create adaptive response workflow
        if analysis.confidence < 0.6:
            # Student seems confused
            workflow = [
                Step("simplify", "Simplify the explanation"),
                Step("example", "Provide concrete example"),
                Step("check", "Check understanding")
            ]
        else:
            # Student understands basics
            workflow = [
                Step("deepen", "Deepen the explanation"),
                Step("connect", "Connect to related concepts"),
                Step("challenge", "Provide challenge question")
            ]
        
        response = self.planner.run_workflow(
            f"Respond to student based on analysis",
            workflow=workflow
        )
        
        return response

# Usage
assistant = TeachingAssistant()

# Explain a concept
explanation = assistant.explain_concept(
    "recursion", 
    "beginner programmer"
)

print("EXPLANATION:")
print(explanation["explanation"])
print("\nTEACHING APPROACH:")
for step in explanation["reasoning"]:
    print(f"- {step}")

# Create lesson plan
lesson = assistant.create_lesson_plan(
    "Introduction to Machine Learning",
    "2 hours"
)

print("\nLESSON PLAN:")
for step_name, result in lesson.steps.items():
    print(f"\n{step_name.upper()}:")
    print(result.output)
```

## Next Steps

- [Try the examples yourself](hello-world.md)
- [Learn about provider switching](provider-switching.md)
- [Explore real-world applications](real-world.md)
